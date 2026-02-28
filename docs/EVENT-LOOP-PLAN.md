# BuckeyeBot Event Loop Architecture — Implementation Plan

## Context

BuckeyeBot currently has a **single-model architecture**: user texts in → Granite handles everything (classification + tool selection + response) → reply sent via SMS. There's no separation between fast classification and complex reasoning.

This plan builds a **dual-model agent orchestration pipeline** (Granite as fast router, Claude Opus 4.6 as planner/executor) and integrates it with the existing SMS infrastructure via BeeAI Workflow.

---

## New File Structure

```
buckeye-claw/
  main.py                      # MODIFY — asyncio event loop with Flask in thread
  agent.py                     # MODIFY — split into granite/claude agent factories
  orchestrator.py              # NEW — BeeAI Workflow (dual-model pipeline)
  models.py                    # NEW — Pydantic models (PipelineState)
  messaging/
    webhook.py                 # MODIFY — use shared asyncio event loop
    (client.py, sender.py, events.py, verify.py, chat_store.py — unchanged)
```

---

## Step 1: Pydantic Models — `models.py`

Pipeline state passed through the BeeAI Workflow steps:

- **`PipelineState`** — user_text, from_number, intent, extracted_params, is_simple, draft_response, final_response

---

## Step 2: Refactor `agent.py` — Dual Agent Factories

Split `create_agent()` into two factories. Keep `ALL_TOOLS` list unchanged.

```python
def create_granite_agent(tools=None) -> RequirementAgent:
    """Fast/cheap classifier + formatter. No tools by default."""
    llm = ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")
    return RequirementAgent(llm=llm, tools=tools or [], memory=UnconstrainedMemory(), ...)

def create_claude_agent() -> RequirementAgent:
    """Complex reasoning + tool selection. Gets ALL_TOOLS."""
    llm = ChatModel.from_name("anthropic:claude-opus-4-6")
    return RequirementAgent(llm=llm, tools=ALL_TOOLS, memory=UnconstrainedMemory(), ...)
```

- Both use `UnconstrainedMemory()` — each workflow run is stateless (memory will be plugged in externally later).
- Claude gets all 48 tools for autonomous tool selection and execution.

---

## Step 3: Orchestrator — `orchestrator.py`

BeeAI `Workflow` with 3 core steps implementing the dual-model pipeline:

### Pipeline Flow
```
SMS in → [1] granite_intake → [2] claude_plan_execute → [3] granite_format → SMS out
```

### Step Details

**Step 1 — `granite_intake`**: Granite classifies intent into one of: `dining_query`, `bus_query`, `parking_query`, `event_query`, `class_query`, `library_query`, `recsports_query`, `building_query`, `calendar_query`, `directory_query`, `athletics_query`, `merchant_query`, `foodtruck_query`, `studentorg_query`, `canvas_query`, `grubhub_order`, `buckeyelink_query`, `chitchat`, `unknown`. Extracts params and sets `is_simple=True` for greetings/chitchat that don't need tools.

**Step 2 — `claude_plan_execute`**:
- If `is_simple`: skip (Granite handles in step 3)
- Otherwise: Claude receives intent + params + user message, selects and calls tools autonomously via BeeAI's built-in tool loop, synthesizes results into a draft response

**Step 3 — `granite_format`**: Granite reformats Claude's draft for SMS (under 1500 chars, line breaks, bullet points). For simple intents, Granite generates the full response directly.

### Exported Function
```python
async def run_pipeline(text: str, from_number: str) -> str
```
This replaces the current `agent.run(text)` call in the message handler.

### Error Handling
- Granite intake failure → fall through to Claude with `intent="unknown"`
- Claude timeout/error → Granite-only fallback response
- Tool failure → already handled per-tool; Claude synthesizes error message
- All agent calls wrapped in `try/except FrameworkError` per BeeAI conventions

---

## Step 4: Modify `messaging/webhook.py`

One change:

### Shared Event Loop
Replace per-thread `asyncio.new_event_loop()` in `_process_event` with `asyncio.run_coroutine_threadsafe(coro, main_loop)` so webhook background threads share the main asyncio loop. Store the main loop reference via a `set_main_loop()` function called from `main.py`.

This ensures all agent processing runs on a single event loop, which is required for BeeAI agents and will be required when the scheduler is added later.

---

## Step 5: Restructure `main.py` — Unified Event Loop

Replace the synchronous `app.run()` with an asyncio main loop:

```python
async def async_main():
    # 1. Load chat store from .linq_chats.json
    # 2. Register orchestrator.run_pipeline as the agent handler
    # 3. Set main event loop reference for webhook.py
    # 4. Run Flask in a daemon thread (app.run in thread)
    # 5. Keep asyncio loop alive

def main():
    asyncio.run(async_main())
```

Flask runs in a background thread; the main thread owns the asyncio event loop where all agent processing happens.

---

## Step 6: Dependencies

Add to `pyproject.toml` dependencies:
```
"beeai-framework[watsonx,anthropic]"   # add anthropic extra (currently only watsonx)
```

Add to `.env.example`:
```
ANTHROPIC_API_KEY=                       # Required for Claude Opus 4.6 planner
```

---

## Implementation Order

| # | Task | Files |
|---|------|-------|
| 1 | Pydantic models | `models.py` |
| 2 | Refactor agent factories | `agent.py` |
| 3 | Build orchestrator workflow | `orchestrator.py` |
| 4 | Modify webhook for shared event loop | `messaging/webhook.py` |
| 5 | Wire up main.py | `main.py` |
| 6 | Update dependencies + env | `pyproject.toml`, `.env.example` |

---

## Verification Plan

1. **Test orchestrator in isolation**: Call `run_pipeline("what dining halls are open?", "+1234567890")` — verify Granite classifies, Claude calls `get_dining_locations`, Granite formats response under 1500 chars
2. **Test simple bypass**: Call `run_pipeline("hello!", "+1234567890")` — verify it skips Claude and Granite responds directly
3. **End-to-end SMS test**: Text the Linq number, verify full round-trip with typing indicators, read receipts, and dual-model response
