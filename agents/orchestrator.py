import json
import logging

from beeai_framework.errors import FrameworkError
from beeai_framework.workflows import Workflow

from agents.factories import create_granite_agent, create_claude_agent, ALL_TOOLS
from agents.models import PipelineState

logger = logging.getLogger(__name__)

INTENT_LIST = (
    "dining_query, bus_query, parking_query, event_query, class_query, "
    "library_query, recsports_query, building_query, calendar_query, "
    "directory_query, athletics_query, merchant_query, foodtruck_query, "
    "studentorg_query, canvas_query, grubhub_order, buckeyelink_query, "
    "chitchat, unknown"
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


def _build_workflow() -> Workflow:
    """Build the dual-model orchestration workflow."""
    wf = Workflow(PipelineState)

    async def granite_intake(state: PipelineState):
        """Granite classifies intent and extracts parameters."""
        agent = create_granite_agent()
        prompt = (
            "Classify the following user message into exactly one intent.\n"
            f"Valid intents: {INTENT_LIST}\n\n"
            "Respond with JSON only, no other text:\n"
            '{"intent": "<intent>", "params": {<extracted parameters>}, "is_simple": <true if chitchat/greeting that needs no tools>}\n\n'
            f"User message: {state.user_text}"
        )
        try:
            response = await agent.run(prompt)
            parsed = _parse_json(response.result.text)
            state.intent = parsed.get("intent", "unknown")
            state.extracted_params = parsed.get("params", {})
            state.is_simple = parsed.get("is_simple", False)
            logger.info(
                "Granite classified intent=%s is_simple=%s params=%s",
                state.intent, state.is_simple, state.extracted_params,
            )
        except FrameworkError as e:
            logger.error("Granite intake error: %s", e.explain())
            state.intent = "unknown"
            state.is_simple = False

    async def claude_plan_execute(state: PipelineState):
        """Claude Opus plans tool usage, executes tools, and synthesizes results."""
        if state.is_simple:
            return

        agent = create_claude_agent()
        prompt = (
            f"User intent: {state.intent}\n"
            f"Extracted parameters: {json.dumps(state.extracted_params)}\n"
            f"User message: {state.user_text}\n\n"
            "Select and call the appropriate tools to fulfill this request, "
            "then synthesize the results into a clear, helpful response."
        )
        try:
            response = await agent.run(prompt)
            state.draft_response = response.result.text
        except FrameworkError as e:
            logger.error("Claude execution error: %s", e.explain())
            state.draft_response = ""
        except Exception:
            logger.exception("Unexpected error in Claude execution")
            state.draft_response = ""

    async def granite_format(state: PipelineState):
        """Granite formats the final response for SMS delivery."""
        agent = create_granite_agent()

        if state.is_simple:
            try:
                response = await agent.run(state.user_text)
                state.final_response = response.result.text[:1500]
            except FrameworkError as e:
                logger.error("Granite simple response error: %s", e.explain())
                state.final_response = "Hey! How can I help you today?"
            return Workflow.END

        if not state.draft_response:
            state.final_response = "Sorry, I couldn't process that. Could you try rephrasing?"
            return Workflow.END

        prompt = (
            "Reformat the following response for SMS delivery.\n"
            "Keep under 1500 characters. Use line breaks and bullet points for readability.\n"
            "Do not add information — only format what's given.\n\n"
            f"{state.draft_response}"
        )
        try:
            response = await agent.run(prompt)
            state.final_response = response.result.text[:1500]
        except FrameworkError as e:
            logger.error("Granite format error: %s", e.explain())
            state.final_response = state.draft_response[:1500]

        return Workflow.END

    wf.add_step("granite_intake", granite_intake)
    wf.add_step("claude_plan_execute", claude_plan_execute)
    wf.add_step("granite_format", granite_format)

    return wf


_workflow = _build_workflow()


async def run_pipeline(text: str, from_number: str) -> str:
    """Run the dual-model orchestration pipeline. Returns SMS-ready text."""
    debug = True  # TODO: remove after debugging

    state = PipelineState(user_text=text, from_number=from_number)
    try:
        run = await _workflow.run(state).observe(lambda event: None)
        return run.state.final_response
    except FrameworkError as e:
        logger.error("Pipeline framework error: %s", e.explain())
        if debug:
            return f"[DEBUG] Pipeline error: {e.explain()[:500]}"
    except Exception as e:
        logger.exception("Unexpected pipeline error")
        if debug:
            return f"[DEBUG] Pipeline exception: {type(e).__name__}: {e}"[:600]

    # Last-resort fallback: try Granite alone with tools
    try:
        agent = create_granite_agent(tools=ALL_TOOLS)
        response = await agent.run(text)
        return response.result.text[:1500]
    except Exception as e:
        logger.exception("Fallback agent also failed")
        if debug:
            return f"[DEBUG] Fallback also failed: {type(e).__name__}: {e}"[:600]
        return "Sorry, I'm having technical difficulties. Please try again in a moment."
