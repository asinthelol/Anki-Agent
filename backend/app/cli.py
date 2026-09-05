"""
Interactive terminal for the Anki study agent.

Run with `python -m app.cli` from `backend/`. Talks to agent.py in-process --
no FastAPI server needed.
"""

from dotenv import load_dotenv

load_dotenv()

import anthropic

from . import agent, tools


def _prompt_decisions(pending: list[dict]) -> dict[str, bool]:
    print("\nThe agent wants to take these actions:")
    decisions = {}
    for call in pending:
        description = tools.TOOL_DESCRIPTIONS[call["name"]]
        print(f"\n  {call['name']}: {description}")
        print(f"    input: {call['input']}")
        answer = input("  Approve? [y/N] ").strip().lower()
        decisions[call["tool_use_id"]] = answer == "y"
    print()
    return decisions


def _handle(conversation: agent.Conversation) -> agent.Conversation:
    while conversation.status == "awaiting_confirmation":
        decisions = _prompt_decisions(conversation.pending)
        conversation = agent.resolve_pending(conversation.id, decisions)
    print(conversation.final_text or "(no response)")
    print()
    return conversation


def main() -> None:
    print("Anki Study Agent CLI | type a message, /new to reset, /quit to exit.\n")
    conversation: agent.Conversation | None = None

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input == "/quit":
            break
        if user_input == "/new":
            conversation = None
            print("Started a new conversation.\n")
            continue

        try:
            if conversation is None:
                conversation = agent.start_conversation(user_input)
            else:
                conversation = agent.send_message(conversation.id, user_input)
            conversation = _handle(conversation)
        except anthropic.AuthenticationError:
            print("\nAnthropic rejected the API key. Please check ANTHROPIC_API_KEY in backend/.env.\n")
        except anthropic.APIConnectionError:
            print("\nCouldn't reach the Anthropic API. Please check your network connection.\n")


if __name__ == "__main__":
    main()
