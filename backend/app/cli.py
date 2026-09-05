"""
Interactive terminal for the Anki study agent.

Run with `python -m app.cli` from `backend/`. Talks to agent.py in-process --
no FastAPI server needed.
"""

from dotenv import load_dotenv

load_dotenv()

import itertools
import sys
import threading
import time

import anthropic

from . import agent, tools


class _Spinner:
    """Rotating-character 'Thinking' indicator for the duration of a blocking call."""

    _FRAMES = "|/-\\"

    def __init__(self, message: str = "Thinking..."):
        self._message = message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        for frame in itertools.cycle(self._FRAMES):
            if self._stop_event.is_set():
                break
            sys.stdout.write(f"\r{frame} {self._message}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self._message) + 2) + "\r")
        sys.stdout.flush()

    def __enter__(self) -> "_Spinner":
        self._thread.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._stop_event.set()
        self._thread.join()


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
        with _Spinner():
            conversation = agent.resolve_pending(conversation.id, decisions)
    print(conversation.final_text or "(no response)")
    print()
    return conversation


def _handle_model_command(arg: str, current_model: str) -> str:
    if not arg:
        print(f"\nCurrent model: {current_model}")
        print(f"Available: {', '.join(agent.AVAILABLE_MODELS)} (or any full model id)\n")
        return current_model

    new_model = agent.AVAILABLE_MODELS.get(arg, arg)
    print(f"\nSwitched to {new_model}.\n")
    return new_model


def main() -> None:
    print("Anki Study Agent CLI | type a message, /new to reset, /model [name] to switch models, /quit to exit.\n")
    conversation: agent.Conversation | None = None
    current_model = agent.DEFAULT_MODEL
    print(f"Model: {current_model}\n")

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
        if user_input == "/model" or user_input.startswith("/model "):
            arg = user_input[len("/model"):].strip()
            current_model = _handle_model_command(arg, current_model)
            continue

        try:
            with _Spinner():
                if conversation is None:
                    conversation = agent.start_conversation(user_input, model=current_model)
                else:
                    conversation = agent.send_message(conversation.id, user_input, model=current_model)
            conversation = _handle(conversation)
        except anthropic.AuthenticationError:
            print("\nAnthropic rejected the API key. Please check ANTHROPIC_API_KEY in backend/.env.\n")
        except anthropic.APIConnectionError:
            print("\nCouldn't reach the Anthropic API. Please check your network connection.\n")


if __name__ == "__main__":
    main()
