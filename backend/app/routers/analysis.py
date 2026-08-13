"""HTTP endpoints for running the study-plan agent and confirming its proposed actions."""

from fastapi import APIRouter, HTTPException

from .. import agent, tools
from ..schemas import AnalyzeRequest, AnalyzeResponse, ConfirmRequest, PendingAction

router = APIRouter(prefix="/analyze", tags=["analysis"])


def _to_response(conversation: agent.Conversation) -> AnalyzeResponse:
    pending_actions = None
    if conversation.status == "awaiting_confirmation":
        pending_actions = [
            PendingAction(
                tool_use_id=call["tool_use_id"],
                name=call["name"],
                description=tools.TOOL_DESCRIPTIONS[call["name"]],
                input=call["input"],
            )
            for call in conversation.pending
        ]

    return AnalyzeResponse(
        conversation_id=conversation.id,
        status=conversation.status,
        plan=conversation.final_text,
        pending_actions=pending_actions,
    )


@router.post("", response_model=AnalyzeResponse)
def start_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    conversation = agent.start_conversation(request.message)
    return _to_response(conversation)


@router.post("/{conversation_id}/confirm", response_model=AnalyzeResponse)
def confirm_actions(conversation_id: str, request: ConfirmRequest) -> AnalyzeResponse:
    try:
        conversation = agent.resolve_pending(conversation_id, request.decisions)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _to_response(conversation)
