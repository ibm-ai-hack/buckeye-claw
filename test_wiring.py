"""Quick manual test to verify memory module is wired into the pipeline.

Requires SUPABASE_URL, SUPABASE_API_KEY, VOYAGE_API_KEY, and WATSONX_* env vars.
Run: uv run python test_wiring.py
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

PHONE = "+15550001234"


async def main():
    from agents.orchestrator import init_memory, _memory
    from auth.client import get_client
    from auth.users import get_or_create_user

    # Step 1: Verify init_memory works
    print("\n=== Step 1: init_memory() ===")
    init_memory()
    from agents.orchestrator import _memory
    assert _memory is not None, "MemoryModule not initialized!"
    print("PASS: MemoryModule initialized")

    # Step 2: Verify user resolution
    print("\n=== Step 2: get_or_create_user() ===")
    supabase = get_client()
    user_id = get_or_create_user(supabase, PHONE)
    print(f"PASS: Resolved {PHONE} → {user_id}")

    # Step 3: Verify get_context works (empty for new user)
    print("\n=== Step 3: get_context() (should be empty for new user) ===")
    context = await _memory.get_context(user_id, "what's for dinner?")
    print(f"PASS: Context = {context!r} ({len(context)} chars)")

    # Step 4: Verify update_background fires without error
    print("\n=== Step 4: update_background() ===")
    _memory.update_background(user_id, "I'm a CSE major and I'm vegan")
    print("PASS: update_background fired (daemon thread)")

    # Give the background thread time to finish
    print("Waiting 10s for background thread to complete...")
    await asyncio.sleep(10)

    # Step 5: Verify facts were stored by checking context again
    print("\n=== Step 5: get_context() after update ===")
    context = await _memory.get_context(user_id, "what's for dinner?")
    print(f"Context = {context!r} ({len(context)} chars)")
    if context:
        print("PASS: Memory context is populated after update!")
    else:
        print("WARN: Context still empty — check WATSONX/VOYAGE credentials and logs above")

    # Cleanup: remove test profile (cascade deletes memory rows)
    print("\n=== Cleanup ===")
    supabase.table("profiles").delete().eq("id", user_id).execute()
    print(f"Deleted test profile {user_id}")

    print("\n=== All checks complete ===")


if __name__ == "__main__":
    asyncio.run(main())
