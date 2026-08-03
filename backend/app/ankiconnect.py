"""
Wrapper for AnkiConnect API (localhost:8765).

Each function here maps to one or a few AnkiConnect actions and returns
data shaped for either a Claude tool call or a dashboard endpoint.
"""

import httpx

ANKICONNECT_URL = "http://localhost:8765"


def invoke(action: str, **params) -> dict:
    """
    POST an AnkiConnect request, unwrap `result`, raise on `error`.
    """
    pass


# --- Decks -------------------------------------------------------------

def get_deck_names() -> list[str]:
    """
    Retrieves all deck names in the collection.
    """
    pass


def get_deck_stats(deck_names: list[str]) -> dict:
    """
    Retrieves per-deck counts: new / learning / review / total cards.
    """
    pass


def get_deck_config(deck_name: str) -> dict:
    """
    Retrieves deck options: new-cards-per-day limit, review limit, etc.
    """
    pass


# --- Cards ---------------------------------------------------------------

def get_cards_in_deck(deck_name: str) -> list[int]:
    """
    Retrieves card IDs belonging to a deck (via findCards).
    """
    pass


def get_cards_info(card_ids: list[int]) -> list[dict]:
    """
    Retrieves per-card metadata: interval, ease factor, due, queue/type, lapses, reps.
    """
    pass


def get_new_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards never studied (`deck:X is:new`).
    """
    pass


def get_seen_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards studied at least once (`deck:X -is:new`).
    """
    pass


def get_suspended_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards currently suspended (`deck:X is:suspended`).
    """
    pass


def get_due_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards due for review right now (`deck:X is:due`).
    """
    pass


# --- Review history / performance --------------------------------------

def get_review_history(card_ids: list[int]) -> dict:
    """
    Retrieves full revlog per card: timestamp, ease button pressed, interval, time taken.
    """
    pass


def get_reviews_by_day(num_days: int) -> dict:
    """
    Retrieves review counts per day: feeds a study heatmap / streak view.
    """
    pass


def get_struggling_cards(deck_name: str) -> list[dict]:
    """
    Retrieves cards with low ease factor, high lapse count, or the 'leech' tag.
    """
    pass


def get_leeches(deck_name: str) -> list[dict]:
    """
    Retrieves cards Anki has auto-tagged as leeches.
    """
    pass


# --- Tags ----------------------------------------------------------------

def get_tags() -> list[str]:
    """
    Retrieves all tags in the collection.
    """
    pass


def get_cards_by_tag(tag: str) -> list[int]:
    """
    Retrieves card IDs carrying a given tag.
    """
    pass


# --- Acting on the plan (creating decks / cards, rescheduling) ----------

def create_deck(deck_name: str) -> int:
    """
    Create a new deck (or return the existing deck's id).
    """
    pass


def move_cards_to_deck(card_ids: list[int], deck_name: str) -> None:
    """
    Move cards into a deck e.g. pull leeches/struggling cards out for focused review.
    """
    pass


def create_struggling_deck(deck_name: str, card_ids: list[int]) -> None:
    """C
    reate (or reuse) a deck and move the given struggling/leech cards into it.
    """
    pass


def create_reversed_cards(card_ids: list[int], new_deck_name: str) -> None:
    """
    Clone notes with front/back fields swapped into a new deck.
    """
    pass


def suspend_cards(card_ids: list[int]) -> None:
    """
    Suspend cards so they stop coming up in review.
    """
    pass


def unsuspend_cards(card_ids: list[int]) -> None:
    """
    Unsuspend previously-suspended cards.
    """
    pass


def set_due_date(card_ids: list[int], days: str) -> None:
    """
    Reschedule cards' due date e.g. front-load struggling cards sooner.
    """
    pass
