"""Models for the analysis endpoints."""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    decisions: dict[str, bool]  # tool_use_id -> approve (True) / reject (False)


class PendingAction(BaseModel):
    tool_use_id: str
    name: str
    description: str
    input: dict


class AnalyzeResponse(BaseModel):
    conversation_id: str
    status: str  # "awaiting_confirmation" | "done"
    plan: str | None = None
    pending_actions: list[PendingAction] | None = None
