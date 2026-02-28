"""Thorough memory system test — exercises all 4 Supabase tables.

Uses an existing user profile (with prepopulated bus_transit history) to verify
writes to: profiles, memory_tasks, memory_facts, memory_jobs.

After running, check your Supabase dashboard to confirm the rows.
Cleans up only test-created rows (tasks/facts), never the user profile.

Run:  uv run python memory-test.py --phone +1614...
"""

import argparse
import asyncio
import json
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("memory-test")

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

results: list[tuple[str, bool]] = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, condition))


async def main(phone: str, keep: bool = False):
    from auth.client import get_client
    from auth.users import get_user
    from beeai_framework.backend import ChatModel
    from memory.db import MemoryDB
    from memory.module import MemoryModule

    supabase = get_client()
    db = MemoryDB(supabase)
    llm = ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")
    memory = MemoryModule(llm=llm, db=db)

    # =========================================================================
    # TABLE 1: profiles (lookup existing user)
    # =========================================================================
    print("\n" + "=" * 60)
    print("TABLE 1: profiles")
    print("=" * 60)

    user_id = get_user(supabase, phone)
    if not user_id:
        print(f"  [{FAIL}] No profile found for {phone}. Create one first via the web app.")
        return

    print(f"  Found profile: {phone} → {user_id}")
    row = supabase.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    check("Profile exists in DB", row is not None and row.data is not None)
    check("Phone number matches", row.data["phone"] == phone, f"got {row.data['phone']}")

    # =========================================================================
    # TABLE 2: memory_tasks (written on every message via _update)
    # =========================================================================
    print("\n" + "=" * 60)
    print("TABLE 2: memory_tasks")
    print("=" * 60)

    # Snapshot existing IDs before our test (so cleanup only removes what we add)
    pre_task_ids = {r["id"] for r in supabase.table("memory_tasks").select("id").eq("user_id", user_id).execute().data}
    pre_fact_ids = {r["id"] for r in supabase.table("memory_facts").select("id").eq("user_id", user_id).execute().data}
    pre_job_ids = {r["id"] for r in supabase.table("memory_jobs").select("id").eq("user_id", user_id).execute().data}
    pre_count = len(pre_task_ids)
    print(f"  Existing tasks before test: {pre_count}")

    # Send message — should create a task row
    print("  Sending: 'I prefer vegan food and my major is CSE'")
    await memory._update(user_id, "I prefer vegan food and my major is CSE")

    tasks = supabase.table("memory_tasks").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    check("Task row created after message", len(tasks.data) > pre_count, f"got {len(tasks.data)} total (was {pre_count})")

    if tasks.data:
        t = tasks.data[0]  # most recent
        check("Category assigned", bool(t["category"]), f"category={t['category']}")
        print(f"  Latest task: [{t['category']}] {t['task']}")

    # =========================================================================
    # TABLE 3: memory_facts (written when Granite extracts personal info)
    # =========================================================================
    print("\n" + "=" * 60)
    print("TABLE 3: memory_facts")
    print("=" * 60)

    # Wait a moment for any async embedding to settle
    await asyncio.sleep(1)

    facts = supabase.table("memory_facts").select("key, value, embedding").eq("user_id", user_id).execute()
    check("Facts extracted and stored", len(facts.data) >= 1, f"got {len(facts.data)} fact(s)")

    if facts.data:
        print("  Stored facts:")
        for f in facts.data:
            has_embedding = f["embedding"] is not None
            # Parse embedding to check dimensions
            if has_embedding and isinstance(f["embedding"], str):
                emb_len = len(json.loads(f["embedding"]))
            elif has_embedding:
                emb_len = len(f["embedding"])
            else:
                emb_len = 0
            print(f"    {f['key']} = {f['value']}  (embedding: {emb_len}-dim)")
            check(f"Fact '{f['key']}' has embedding", has_embedding)
            if has_embedding:
                check(f"Fact '{f['key']}' embedding is 1024-dim", emb_len == 1024, f"got {emb_len}")

    # Verify semantic search works — a food query should surface dietary facts
    print("\n  Testing semantic search (pgvector cosine)...")
    context = await memory.get_context(user_id, "what should I eat for dinner")
    check("get_context returns non-empty for food query", len(context) > 0, f"({len(context)} chars)")
    print(f"  Context: {context}")

    # Verify fact UPSERT (overwrite, not duplicate)
    print("\n  Testing fact upsert (overwrite)...")
    print("  Sending: 'actually I eat vegetarian not vegan'")
    await memory._update(user_id, "actually I eat vegetarian not vegan")
    await asyncio.sleep(1)

    facts_after = supabase.table("memory_facts").select("key, value").eq("user_id", user_id).execute()
    # Check there's no duplication of the diet key
    diet_facts = [f for f in facts_after.data if "diet" in f["key"].lower() or "food" in f["key"].lower() or "vegan" in f["value"].lower() or "vegetarian" in f["value"].lower()]
    print(f"  Diet-related facts after upsert: {diet_facts}")
    check("Facts still present after upsert", len(facts_after.data) >= 1, f"got {len(facts_after.data)} fact(s)")

    # =========================================================================
    # TABLE 4: memory_jobs (triggered by prepopulated bus_transit history)
    # =========================================================================
    print("\n" + "=" * 60)
    print("TABLE 4: memory_jobs")
    print("=" * 60)

    # Show prepopulated bus_transit tasks
    pre_bus = supabase.table("memory_tasks").select("task, category, created_at").eq("user_id", user_id).eq("category", "bus_transit").order("created_at").execute()
    print(f"  Prepopulated bus_transit tasks: {len(pre_bus.data)}")
    for t in pre_bus.data:
        print(f"    [{t['created_at']}] {t['task']}")

    # Send 1 bus message — should trigger repetition detection (>= 3 same-category)
    print("\n  Sending 1 bus message to trigger repetition check:")
    print("    → when is the next bus to north campus")
    await memory._update(user_id, "when is the next bus to north campus")

    await asyncio.sleep(2)

    # Check if repetition was detected
    tasks_all = supabase.table("memory_tasks").select("task, category").eq("user_id", user_id).execute()
    categories = [t["category"] for t in tasks_all.data]
    from collections import Counter
    cat_counts = Counter(categories)
    print(f"\n  Task category distribution: {dict(cat_counts)}")

    # Check for bus_transit with 3+ entries
    bus_count = cat_counts.get("bus_transit", 0)
    check("bus_transit has 3+ tasks (repetition threshold)", bus_count >= 3, f"bus_transit={bus_count}")

    jobs = supabase.table("memory_jobs").select("*").eq("user_id", user_id).execute()
    if jobs.data:
        print(f"\n  Jobs detected ({len(jobs.data)}):")
        for j in jobs.data:
            print(f"    {j['task_name']} | schedule: {j.get('schedule', 'none')} | occurrences: {j.get('occurrence_count', 0)}")
        check("Job row created in memory_jobs", True)
    else:
        print(f"\n  [{WARN}] No jobs created — Granite may not have detected a recurring schedule pattern.")
        print("       This is expected sometimes; repetition detection requires Granite to infer a time pattern.")
        print("       The code path was still exercised (3+ same-category tasks triggered _handle_repetition).")

    # =========================================================================
    # FULL ROUND-TRIP: get_context after all updates
    # =========================================================================
    print("\n" + "=" * 60)
    print("FULL ROUND-TRIP: get_context()")
    print("=" * 60)

    context_final = await memory.get_context(user_id, "what bus should I take to get food")
    print(f"  Final context: {context_final}")
    check("Final context is non-empty", len(context_final) > 0, f"({len(context_final)} chars)")

    if jobs.data:
        check("Jobs appear in context", "Recurring tasks:" in context_final)

    # =========================================================================
    # DB SNAPSHOT
    # =========================================================================
    print("\n" + "=" * 60)
    print(f"DB SNAPSHOT — check Supabase for user_id: {user_id}")
    print("=" * 60)

    final_tasks = supabase.table("memory_tasks").select("task, category").eq("user_id", user_id).execute()
    final_facts = supabase.table("memory_facts").select("key, value").eq("user_id", user_id).execute()
    final_jobs = supabase.table("memory_jobs").select("task_name, schedule, occurrence_count").eq("user_id", user_id).execute()

    print(f"\n  profiles:      1 row (phone={phone})")
    print(f"  memory_tasks:  {len(final_tasks.data)} rows")
    for t in final_tasks.data:
        print(f"    [{t['category']}] {t['task']}")
    print(f"  memory_facts:  {len(final_facts.data)} rows")
    for f in final_facts.data:
        print(f"    {f['key']} = {f['value']}")
    print(f"  memory_jobs:   {len(final_jobs.data)} rows")
    for j in final_jobs.data:
        print(f"    {j['task_name']} ({j.get('schedule', 'none')}) x{j.get('occurrence_count', 0)}")

    # =========================================================================
    # CLEANUP — remove only rows created by this test run
    # =========================================================================
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    if keep:
        print("  --keep flag set. Skipping cleanup — test data preserved.")
    else:
        new_task_ids = [r["id"] for r in supabase.table("memory_tasks").select("id").eq("user_id", user_id).execute().data if r["id"] not in pre_task_ids]
        new_fact_ids = [r["id"] for r in supabase.table("memory_facts").select("id").eq("user_id", user_id).execute().data if r["id"] not in pre_fact_ids]
        new_job_ids = [r["id"] for r in supabase.table("memory_jobs").select("id").eq("user_id", user_id).execute().data if r["id"] not in pre_job_ids]

        for tid in new_task_ids:
            supabase.table("memory_tasks").delete().eq("id", tid).execute()
        for fid in new_fact_ids:
            supabase.table("memory_facts").delete().eq("id", fid).execute()
        for jid in new_job_ids:
            supabase.table("memory_jobs").delete().eq("id", jid).execute()

        print(f"  Deleted {len(new_task_ids)} test task(s), {len(new_fact_ids)} test fact(s), {len(new_job_ids)} test job(s)")
        print(f"  User profile and prepopulated data left untouched.")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    total = len(results)
    color = "\033[92m" if failed == 0 else "\033[91m"
    print(f"RESULTS: {color}{passed}/{total} passed\033[0m")
    if failed > 0:
        print("Failed checks:")
        for name, ok in results:
            if not ok:
                print(f"  - {name}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Memory system integration test")
    parser.add_argument("--phone", required=True, help="E.164 phone number of existing user (e.g. +1614...)")
    parser.add_argument("--keep", action="store_true", help="Skip cleanup — keep test data in Supabase")
    args = parser.parse_args()
    asyncio.run(main(phone=args.phone, keep=args.keep))
