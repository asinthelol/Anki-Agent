"""
Interactive terminal for the Anki study agent.

Run with `python -m app.cli` from `backend/`. Talks to agent.py in-process --
no FastAPI server needed.
"""

from dotenv import load_dotenv

load_dotenv()

import itertools
import shutil
import sys
import threading
import time

import anthropic
import colorama

from . import agent, tools

colorama.just_fix_windows_console()

_RESET = "\033[0m"
_BOLD = "\033[1m"
_ORANGE = "\033[38;5;208m"
_RED = "\033[31m"
_USER_HIGHLIGHT = "\033[48;5;238m\033[38;5;208m"  # orange text on dark gray background


def _clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _print_banner(model: str) -> None:
    """
    A boxed header showing the app name, active model, and available commands.
    """
    title = " Anki Study Agent "
    model_line = f" Model: {model}"
    commands_line = " Commands: /new (reset)  /model [name] (switch)  /quit (exit)"

    interior_width = max(len(model_line), len(commands_line), len(title) + 4)
    term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    interior_width = min(interior_width, max(term_width - 2, len(title) + 4))

    left_pad = (interior_width - len(title)) // 2
    right_pad = interior_width - len(title) - left_pad

    def content_row(text: str) -> str:
        return f"{_ORANGE}│{_RESET}{text.ljust(interior_width)[:interior_width]}{_ORANGE}│{_RESET}"

    print(f"{_ORANGE}┌{'─' * left_pad}{_RESET}{_BOLD}{title}{_RESET}{_ORANGE}{'─' * right_pad}┐{_RESET}")
    print(content_row(model_line))
    print(f"{_ORANGE}├{'─' * interior_width}┤{_RESET}")
    print(content_row(commands_line))
    print(f"{_ORANGE}└{'─' * interior_width}┘{_RESET}")
    print()


def _print_user_message(text: str) -> None:
    """Redraw the just-typed line highlighted"""
    sys.stdout.write("\033[1A\033[2K")
    print(f"{_USER_HIGHLIGHT} {text} {_RESET}")


class _Spinner:
    """
    Rotating-character 'Thinking' indicator for the duration of a blocking call.
    """

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
        print(f"Available: {', '.join(agent.AVAILABLE_MODELS)}\n")
        return current_model

    valid = set(agent.AVAILABLE_MODELS) | set(agent.AVAILABLE_MODELS.values())
    if arg not in valid:
        print(f'{_RED}Model "{arg}" is not an available option.{_RESET}\n')
        return current_model

    new_model = agent.AVAILABLE_MODELS.get(arg, arg)
    _clear_screen()
    _print_banner(new_model)
    return new_model


def main() -> None:
    conversation: agent.Conversation | None = None
    current_model = agent.DEFAULT_MODEL
    _clear_screen()
    _print_banner(current_model)

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

        _print_user_message(user_input)

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
