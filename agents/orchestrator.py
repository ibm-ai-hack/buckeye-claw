import json
import logging

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.workflows import Workflow

from agents.factories import create_granite_agent, create_claude_agent, create_grubhub_agent, create_email_agent, ALL_TOOLS
from agents.models import PipelineState
from backend.integrations.campus.utils import now_eastern
from agents.tracer import RunTracer, _tracer_var, get_tracer
from auth.client import get_client
from auth.users import get_user
from memory.db import MemoryDB
from memory.module import MemoryModule

logger = logging.getLogger(__name__)

_memory: MemoryModule | None = None


def init_memory() -> None:
    """Initialize the MemoryModule singleton. Call once at startup after load_dotenv()."""
    global _memory
    supabase = get_client()
    db = MemoryDB(supabase)
    llm = ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")
    _memory = MemoryModule(llm=llm, db=db)
    logger.info("MemoryModule initialized")

INTENT_LIST = (
    "dining_query, bus_query, parking_query, event_query, class_query, "
    "library_query, recsports_query, building_query, calendar_query, "
    "directory_query, athletics_query, merchant_query, foodtruck_query, "
    "studentorg_query, canvas_query, grubhub_order, buckeyelink_query, "
    "email_query, chitchat, unknown"
)


def _parse_json(text: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for start_marker in ("```json", "```"):
        if start_marker in text:
            start = text.index(start_marker) + len(start_marker)
            end = text.index("```", start)
            try:
                return json.loads(text[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        try:
            return json.loads(text[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def _build_intake_prompt(memory_context: str, last_reply: str, user_text: str) -> str:
    """Build the intent-classification prompt for the claude_intake step."""
    memory_block = f"Known user context: {memory_context}\n\n" if memory_context else ""
    prior_block = f"Last message you sent to this user: {last_reply}\n\n" if last_reply else ""
    return (
        f"{memory_block}"
        f"{prior_block}"
        "Classify the following user message into exactly one intent.\n"
        f"Valid intents: {INTENT_LIST}\n\n"
        "Respond with JSON only, no other text:\n"
        '{"intent": "<intent>", "params": {<extracted parameters>}, "is_simple": <true if chitchat/greeting that needs no tools>}\n\n'
        f"User message: {user_text}"
    )


def _build_workflow() -> Workflow:
    """Build the dual-model orchestration workflow."""
    wf = Workflow(PipelineState)

    async def claude_intake(state: PipelineState):
        """Claude 4.6 classifies intent and extracts parameters."""
        tracer = get_tracer()
        if tracer:
            tracer.step_start("claude_intake")

        llm = ChatModel.from_name("anthropic:claude-sonnet-4-6")
        agent = RequirementAgent(llm=llm, memory=UnconstrainedMemory())
        prompt = _build_intake_prompt(state.memory_context, state.last_reply, state.user_text)
        try:
            response = await agent.run(prompt)
            parsed = _parse_json(response.last_message.text)
            state.intent = parsed.get("intent", "unknown")
            state.extracted_params = parsed.get("params", {})
            state.is_simple = parsed.get("is_simple", False)
            logger.info(
                "Claude classified intent=%s is_simple=%s params=%s",
                state.intent, state.is_simple, state.extracted_params,
            )
            if tracer:
                tracer.emit(
                    "intent_classified",
                    step="claude_intake",
                    metadata={
                        "intent": state.intent,
                        "is_simple": state.is_simple,
                        "params": state.extracted_params,
                    },
                )
        except FrameworkError as e:
            logger.error("Claude intake error: %s", e.explain())
            state.intent = "unknown"
            state.is_simple = False
            if tracer:
                tracer.emit("error", step="claude_intake", metadata={"error": e.explain()[:500]})
        finally:
            if tracer:
                tracer.step_end("claude_intake")

    async def claude_plan_execute(state: PipelineState):
        """Route to a specialized agent or Claude Opus for tool execution."""
        if state.is_simple:
            return

        tracer = get_tracer()
        if tracer:
            tracer.step_start("claude_plan_execute")

        logger.info("Agent step starting for intent=%s", state.intent)

        memory_block = (
            f"[User context from memory: {state.memory_context}]\n"
            if state.memory_context else ""
        )

        # Grubhub access restricted to approved accounts
        GRUBHUB_ALLOWED_USERS = {"61a0bbff-fd23-4fb4-8108-5eda6ec290a6"}  # shetty.118@osu.edu

        if state.intent == "grubhub_order" and state.user_id not in GRUBHUB_ALLOWED_USERS:
            state.draft_response = (
                "Grubhub ordering isn't available for your account yet. "
                "Stay tuned — we're rolling it out soon!"
            )
            logger.info("Grubhub access denied for user_id=%s", state.user_id)
            return

        if state.intent == "grubhub_order":
            agent = create_grubhub_agent()
            prompt = (
                f"{memory_block}"
                f"[caller: {state.from_number}]\n"
                f"User message: {state.user_text}\n"
                f"Extracted parameters: {json.dumps(state.extracted_params)}\n\n"
                "Help this user with their Grubhub food order."
            )
        elif state.intent == "email_query":
            agent = create_email_agent()
            prompt = (
                f"{memory_block}"
                f"[caller: {state.from_number}]\n"
                f"User message: {state.user_text}\n"
                f"Extracted parameters: {json.dumps(state.extracted_params)}\n\n"
                "Help this user with their BuckeyeMail request."
            )
        else:
            agent = create_claude_agent()
            prompt = (
                f"[Current date/time: {now_eastern()}]\n"
                f"{memory_block}"
                f"User intent: {state.intent}\n"
                f"Extracted parameters: {json.dumps(state.extracted_params)}\n"
                f"User message: {state.user_text}\n\n"
                "Select and call the appropriate tools to fulfill this request, "
                "then synthesize the results into a clear, helpful response."
            )
        try:
            response = await agent.run(prompt)
            state.draft_response = response.last_message.text

            # Post-process tool calls from the agent run
            if tracer and hasattr(response, "state") and hasattr(response.state, "steps"):
                for step in response.state.steps:
                    if hasattr(step, "tool_name"):
                        tool_args = None
                        tool_result = None
                        try:
                            tool_args = step.tool_input if hasattr(step, "tool_input") else None
                        except Exception:
                            pass
                        try:
                            tool_result = str(step.tool_output)[:2000] if hasattr(step, "tool_output") else None
                        except Exception:
                            pass
                        tracer.emit(
                            "tool_invoked",
                            step="claude_plan_execute",
                            tool_name=step.tool_name,
                            tool_args={"input": tool_args} if tool_args else None,
                        )
                        tracer.emit(
                            "tool_resolved",
                            step="claude_plan_execute",
                            tool_name=step.tool_name,
                            tool_result={"output": tool_result} if tool_result else None,
                        )
        except FrameworkError as e:
            logger.error("Claude execution error: %s", e.explain())
            state.draft_response = f"[DEBUG] Claude error: {e.explain()[:400]}"
            if tracer:
                tracer.emit("error", step="claude_plan_execute", metadata={"error": e.explain()[:500]})
        except Exception as e:
            logger.exception("Unexpected error in Claude execution")
            state.draft_response = f"[DEBUG] Claude exception: {type(e).__name__}: {e}"[:500]
            if tracer:
                tracer.emit("error", step="claude_plan_execute", metadata={"error": f"{type(e).__name__}: {e}"[:500]})
        finally:
            if tracer:
                tracer.step_end("claude_plan_execute")

    async def granite_format(state: PipelineState):
        """Granite formats the final response for SMS delivery."""
        tracer = get_tracer()
        if tracer:
            tracer.step_start("granite_format")

        agent = create_granite_agent()

        if state.is_simple:
            try:
                response = await agent.run(
                    f"[Current date/time: {now_eastern()}]\n\n{state.user_text}"
                )
                state.final_response = response.last_message.text[:1500]
            except FrameworkError as e:
                logger.error("Granite simple response error: %s", e.explain())
                state.final_response = "Hey! How can I help you today?"
            if tracer:
                tracer.step_end("granite_format")
            return Workflow.END

        if not state.draft_response:
            state.final_response = "Sorry, I couldn't process that. Could you try rephrasing?"
            if tracer:
                tracer.step_end("granite_format")
            return Workflow.END

        prompt = (
            "Rewrite the following as a short text message from a chill, helpful friend.\n"
            "Rules: no markdown (no **, ##, or * bullets), no emojis, plain text only, use dashes for lists, keep under 800 characters.\n"
            "Sound natural and personable but not over the top. Keep it concise — no long explanations. Do not add information — only reformat what's given.\n\n"
            f"{state.draft_response}"
        )
        try:
            response = await agent.run(prompt)
            state.final_response = response.last_message.text[:1500]
        except FrameworkError as e:
            logger.error("Granite format error: %s", e.explain())
            state.final_response = state.draft_response[:1500]

        if tracer:
            tracer.step_end("granite_format")
        return Workflow.END

    wf.add_step("claude_intake", claude_intake)
    wf.add_step("claude_plan_execute", claude_plan_execute)
    wf.add_step("granite_format", granite_format)

    return wf


_workflow = _build_workflow()


async def run_pipeline(text: str, from_number: str) -> str:
    """Run the dual-model orchestration pipeline. Returns SMS-ready text."""
    debug = True  # TODO: remove after debugging

    # --- Tracing: create run and set context var ---
    tracer = RunTracer.create(phone=from_number, user_message=text)
    _tracer_var.set(tracer)
    tracer.record_message("user", text)

    # --- Memory: resolve user, fetch context ---
    user_id = ""
    memory_context = ""
    last_reply = ""
    if _memory is not None:
        try:
            supabase = get_client()
            resolved = get_user(supabase, from_number)
            if not resolved:
                logger.info("[MEMORY] No profile found for %s; skipping memory", from_number)
            else:
                user_id = resolved

                # Fetch last reply for follow-up detection
                lr = (
                    supabase.table("profiles")
                    .select("last_reply")
                    .eq("id", user_id)
                    .maybe_single()
                    .execute()
                )
                if lr and lr.data:
                    last_reply = lr.data.get("last_reply") or ""
                logger.debug("[MEMORY] Resolved %s → user_id=%s", from_number, user_id)

                # Fetch stored task history for this user (recent tasks across all categories)
                all_tasks = (
                    supabase.table("memory_tasks")
                    .select("task, category, created_at")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(10)
                    .execute()
                )
                if all_tasks.data:
                    logger.info("[MEMORY] Recent task history for user %s:", user_id)
                    for t in all_tasks.data:
                        logger.info("  [%s] %s  (%s)", t["category"], t["task"], t["created_at"])
                else:
                    logger.info("[MEMORY] No task history for user %s (new user)", user_id)

                # Fetch all stored facts for debug comparison
                all_facts = _memory.db.get_all_facts(user_id)
                if all_facts:
                    logger.info("[MEMORY] Stored facts for user %s:", user_id)
                    for f in all_facts:
                        logger.info("  %s = %s", f["key"], f["value"])
                else:
                    logger.info("[MEMORY] No stored facts for user %s", user_id)

                # Fetch scheduled jobs
                all_jobs = _memory.db.get_jobs(user_id)
                if all_jobs:
                    logger.info("[MEMORY] Scheduled jobs for user %s:", user_id)
                    for j in all_jobs:
                        logger.info("  %s (%s) — occurrences: %s", j["task_name"], j.get("schedule", "none"), j.get("occurrence_count", 0))

                # Now get the semantic context (top-k relevant facts via pgvector)
                memory_context = await _memory.get_context(user_id, text)
                logger.info("[MEMORY] Current task: %r", text)
                logger.info("[MEMORY] Injected context (%d chars): %s", len(memory_context), memory_context or "(empty)")
        except Exception:
            logger.exception("Memory context fetch failed; continuing without it")

    state = PipelineState(
        user_text=text,
        from_number=from_number,
        user_id=user_id,
        memory_context=memory_context,
        last_reply=last_reply,
    )

    response_text = None
    try:
        run = await _workflow.run(state).observe(lambda event: None)
        response_text = run.state.final_response
    except FrameworkError as e:
        logger.error("Pipeline framework error: %s", e.explain())
        tracer.fail(e.explain()[:500])
        if debug:
            response_text = f"[DEBUG] Pipeline error: {e.explain()[:500]}"
    except Exception as e:
        logger.exception("Unexpected pipeline error")
        tracer.fail(f"{type(e).__name__}: {e}"[:500])
        if debug:
            response_text = f"[DEBUG] Pipeline exception: {type(e).__name__}: {e}"[:600]

    # --- Memory: background update (fire and forget) ---
    if _memory is not None and user_id:
        logger.info("[MEMORY] Firing background update for user %s with task: %r", user_id, text)
        _memory.update_background(user_id, text)

    if response_text:
        tracer.record_message("agent", response_text)
        tracer.complete(response_text, intent=state.intent or None)
        return response_text

    # Last-resort fallback: try Granite alone with tools
    try:
        agent = create_granite_agent(tools=ALL_TOOLS)
        response = await agent.run(text)
        fallback_text = response.last_message.text[:1500]
        tracer.record_message("agent", fallback_text)
        tracer.complete(fallback_text, intent="fallback")
        return fallback_text
    except Exception as e:
        logger.exception("Fallback agent also failed")
        tracer.fail(f"Fallback also failed: {type(e).__name__}: {e}"[:500])
        if debug:
            return f"[DEBUG] Fallback also failed: {type(e).__name__}: {e}"[:600]
        return "Sorry, I'm having technical difficulties. Please try again in a moment."
