"""RunTracer — lightweight tracing for the orchestration pipeline.

Every pipeline run creates a RunTracer that writes to Supabase tables
(agent_runs, agent_events, messages) so the frontend can subscribe via
Realtime.  All DB writes are fire-and-forget with swallowed exceptions
so tracing never crashes the pipeline.
"""

from __future__ import annotations

import contextvars
import logging
import time
import uuid
from typing import Any

from auth.client import get_client

logger = logging.getLogger(__name__)

_tracer_var: contextvars.ContextVar["RunTracer | None"] = contextvars.ContextVar(
    "run_tracer", default=None
)


def get_tracer() -> "RunTracer | None":
    return _tracer_var.get()


class RunTracer:
    """Traces a single pipeline run into Supabase."""

    def __init__(self, run_id: str, phone: str) -> None:
        self.run_id = run_id
        self.phone = phone
        self._supabase = get_client()
        self._step_starts: dict[str, float] = {}

    # ── Factory ────────────────────────────────────────────

    @classmethod
    def create(cls, phone: str, user_message: str) -> "RunTracer":
        """Insert an agent_runs row and return a tracer bound to it."""
        run_id = str(uuid.uuid4())
        tracer = cls(run_id=run_id, phone=phone)
        try:
            tracer._supabase.table("agent_runs").insert(
                {
                    "id": run_id,
                    "phone": phone,
                    "status": "running",
                    "user_message": user_message,
                }
            ).execute()
        except Exception:
            logger.exception("tracer: failed to create agent_run %s", run_id)
        return tracer

    # ── Events ─────────────────────────────────────────────

    def emit(
        self,
        event_type: str,
        *,
        step: str | None = None,
        tool_name: str | None = None,
        tool_args: Any = None,
        tool_result: Any = None,
        duration_ms: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Insert a single agent_events row (fire-and-forget)."""
        try:
            row: dict[str, Any] = {
                "run_id": self.run_id,
                "event_type": event_type,
            }
            if step is not None:
                row["step"] = step
            if tool_name is not None:
                row["tool_name"] = tool_name
            if tool_args is not None:
                row["tool_args"] = tool_args
            if tool_result is not None:
                row["tool_result"] = tool_result
            if duration_ms is not None:
                row["duration_ms"] = duration_ms
            if metadata is not None:
                row["metadata"] = metadata
            self._supabase.table("agent_events").insert(row).execute()
        except Exception:
            logger.exception("tracer: failed to emit event %s", event_type)

    # ── Step timing helpers ────────────────────────────────

    def step_start(self, step: str) -> None:
        self._step_starts[step] = time.monotonic()
        self.emit("step_start", step=step)

    def step_end(self, step: str) -> None:
        start = self._step_starts.pop(step, None)
        duration_ms = int((time.monotonic() - start) * 1000) if start else None
        self.emit("step_end", step=step, duration_ms=duration_ms)

    # ── Messages ───────────────────────────────────────────

    def record_message(self, role: str, text: str) -> None:
        """Insert a row into the messages table."""
        try:
            self._supabase.table("messages").insert(
                {
                    "phone": self.phone,
                    "role": role,
                    "text": text,
                    "run_id": self.run_id,
                }
            ).execute()
        except Exception:
            logger.exception("tracer: failed to record message")

    # ── Finalization ───────────────────────────────────────

    def complete(self, final_response: str, intent: str | None = None) -> None:
        """Mark the run as completed."""
        try:
            update: dict[str, Any] = {
                "status": "completed",
                "final_response": final_response,
                "finished_at": "now()",
            }
            if intent:
                update["intent"] = intent
            self._supabase.table("agent_runs").update(update).eq(
                "id", self.run_id
            ).execute()
        except Exception:
            logger.exception("tracer: failed to complete run %s", self.run_id)

    def fail(self, error: str) -> None:
        """Mark the run as errored."""
        try:
            self._supabase.table("agent_runs").update(
                {
                    "status": "error",
                    "error": error[:2000],
                    "finished_at": "now()",
                }
            ).eq("id", self.run_id).execute()
        except Exception:
            logger.exception("tracer: failed to mark run %s as error", self.run_id)
