from pydantic import BaseModel


class PipelineState(BaseModel):
    """State passed through the BeeAI Workflow orchestrator steps."""

    # Input
    user_text: str
    from_number: str

    # Memory — resolved before workflow starts
    user_id: str = ""
    memory_context: str = ""
    last_reply: str = ""  # Last message the agent sent to this user (for follow-up detection)

    # Integration tokens — fetched before workflow starts
    canvas_token: str = ""

    # After Granite intake
    intent: str = ""
    extracted_params: dict = {}
    is_simple: bool = False

    # After Claude planning/execution
    draft_response: str = ""

    # After Granite formatting
    final_response: str = ""
