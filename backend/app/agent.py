"""
Claude tool-use loop for generating (and optionally acting on) an Anki study plan.

Read tools execute automatically. Write tools pause the loop and wait for
resolve_pending() to be called with the user's approve/reject decision for each
one. Conversations are kept in memory, keyed by id.
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

import anthropic

from . import tools

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """
You are an Anki study coach. You have read tools to inspect a user's deck,
card, and review data, and write tools to act on a plan (move cards, suspend
them, reschedule them, create reversed-card decks). Use the read tools to
understand performance by deck and tag -- accuracy, leeches, forgetting curves
-- before proposing a plan. Explain what a write tool call will do and why
before making it; the user approves or rejects each one before it runs.
""".strip()

client = anthropic.Anthropic()


@dataclass
class Conversation:
    id: str
    messages: list = field(default_factory=list)
    pending: list = field(default_factory=list)  # [{tool_use_id, name, input}]
    status: str = "in_progress"  # "in_progress" | "awaiting_confirmation" | "done"
    final_text: str | None = None


_conversations: dict[str, Conversation] = {}


def start_conversation(user_message: str) -> Conversation:
    """
    Begin a new conversation with an initial user message and run the loop.
    """
    conversation = Conversation(id=str(uuid.uuid4()))
    conversation.messages.append({"role": "user", "content": user_message})
    _conversations[conversation.id] = conversation
    _run_loop(conversation)
    return conversation


def resolve_pending(conversation_id: str, decisions: dict[str, bool]) -> Conversation:
    """
    Resolve some or all pending write-tool calls for a paused conversation.
    `decisions` maps tool_use_id -> approved (True) or rejected (False).
    """
    conversation = _conversations[conversation_id]
    if conversation.status != "awaiting_confirmation":
        raise ValueError(f"conversation {conversation_id} has no pending confirmations")

    still_pending = []
    tool_results = []
    for call in conversation.pending:
        tool_use_id = call["tool_use_id"]
        if tool_use_id not in decisions:
            still_pending.append(call)
            continue

        if decisions[tool_use_id]:
            try:
                result = tools.dispatch(call["name"], call["input"])
                tool_results.append(_tool_result_block(tool_use_id, result))
            except Exception as e:
                tool_results.append(_tool_result_block(tool_use_id, str(e), is_error=True))
        else:
            tool_results.append(
                _tool_result_block(tool_use_id, "User declined this action.", is_error=True)
            )

    conversation.pending = still_pending
    if tool_results:
        conversation.messages.append({"role": "user", "content": tool_results})

    if conversation.pending:
        # still waiting on other decisions from this same turn
        return conversation

    conversation.status = "in_progress"
    _run_loop(conversation)
    return conversation


def _run_loop(conversation: Conversation) -> None:
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "disabled"},
            tools=tools.CLAUDE_TOOLS,
            messages=conversation.messages,
        )
        conversation.messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            conversation.status = "done"
            conversation.final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            return

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        tool_results = []
        pending = []

        for block in tool_use_blocks:
            if tools.requires_confirmation(block.name):
                pending.append({"tool_use_id": block.id, "name": block.name, "input": block.input})
            else:
                try:
                    result = tools.dispatch(block.name, block.input)
                    tool_results.append(_tool_result_block(block.id, result))
                except Exception as e:
                    tool_results.append(_tool_result_block(block.id, str(e), is_error=True))

        if tool_results:
            conversation.messages.append({"role": "user", "content": tool_results})

        if pending:
            conversation.pending = pending
            conversation.status = "awaiting_confirmation"
            return

        # every tool call this turn was a read thus loop again automatically


def _tool_result_block(tool_use_id: str, content: Any, is_error: bool = False) -> dict:
    text = content if isinstance(content, str) else json.dumps(content, default=str)
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": text,
        "is_error": is_error,
    }
