"""
Wrapper for AnkiConnect API (localhost:8765).

Each function here maps to one or a few AnkiConnect actions and returns
data shaped for either a Claude tool call or a dashboard endpoint.
"""

from typing import Any

import httpx

ANKICONNECT_URL = "http://localhost:8765"


def invoke(action: str, **params) -> Any:
    """
    POST an AnkiConnect request, unwrap `result`, raise on `error`.
    """
    response = httpx.post(
        ANKICONNECT_URL,
        json={"action": action, "params": params, "version": 6,},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error") is not None:
        raise RuntimeError(f"AnkiConnect error on '{action}': {payload['error']}")
    return payload["result"]


# --- Decks -------------------------------------------------------------

def get_deck_names() -> list[str]:
    """
    Retrieves all deck names in the collection.
    """
    return invoke("deckNames")


def get_deck_stats(deck_names: list[str]) -> dict:
    """
    Retrieves per-deck counts: new / learning / review / total cards.
    """
    return invoke("getDeckStats", decks=deck_names)


def get_deck_config(deck_name: str) -> dict:
    """
    Retrieves deck options: new-cards-per-day limit, review limit, etc.
    """
    return invoke("getDeckConfig", deck=deck_name)


# --- Cards ---------------------------------------------------------------

def get_cards_in_deck(deck_name: str) -> list[int]:
    """
    Retrieves card IDs belonging to a deck (via findCards).
    """
    return invoke("findCards", query=f'deck:"{deck_name}"')


def get_cards_info(card_ids: list[int]) -> list[dict]:
    """
    Retrieves per-card metadata: interval, ease factor, due, queue/type, lapses, reps.
    """
    return invoke("cardsInfo", cards=card_ids)


def get_new_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards never studied (`deck:X is:new`).
    """
    return invoke("findCards", query=f'deck:"{deck_name}" is:new')


def get_seen_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards studied at least once (`deck:X -is:new`).
    """
    return invoke("findCards", query=f'deck:"{deck_name}" -is:new')


def get_suspended_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards currently suspended (`deck:X is:suspended`).
    """
    return invoke("findCards", query=f'deck:"{deck_name}" is:suspended')


def get_due_cards(deck_name: str) -> list[int]:
    """
    Retrieves cards due for review right now (`deck:X is:due`).
    """
    return invoke("findCards", query=f'deck:"{deck_name}" is:due')


# --- Review history / performance --------------------------------------

def get_review_history(card_ids: list[int]) -> dict:
    """
    Retrieves full revlog per card: timestamp, ease button pressed, interval, time taken.
    """
    return invoke("getReviewsOfCards", cards=card_ids)


def get_reviews_by_day(num_days: int) -> dict:
    """
    Retrieves review counts per day: feeds a study heatmap / streak view.
    """
    # [[date_str, count], ...] for every day with reviews, newest first.
    all_days: list[list] = invoke("getNumCardsReviewedByDay")
    recent_days = all_days[:num_days] if num_days else all_days
    return {date: count for date, count in recent_days}


def get_struggling_cards(
    deck_name: str,
    min_lapses: int = 4,
    max_factor: int = 2000,
) -> list[dict]:
    """
    Retrieves cards with low ease factor, high lapse count, or the 'leech' tag.
    """
    card_ids = get_cards_in_deck(deck_name)
    if not card_ids:
        return []

    cards = get_cards_info(card_ids)
    return [
        card
        for card in cards
        if card["lapses"] >= min_lapses
        or (card["factor"] > 0 and card["factor"] < max_factor)
    ]


def get_leeches(deck_name: str) -> list[dict]:
    """
    Retrieves cards Anki has auto-tagged as leeches.
    """
    card_ids = invoke("findCards", query=f'deck:"{deck_name}" tag:leech')
    if not card_ids:
        return []
    return get_cards_info(card_ids)


# --- Tags ----------------------------------------------------------------

def get_tags() -> list[str]:
    """
    Retrieves all tags in the collection.
    """
    return invoke("getTags")


def get_cards_by_tag(tag: str) -> list[int]:
    """
    Retrieves card IDs carrying a given tag.
    """
    return invoke("findCards", query=f"tag:{tag}")


# --- Acting on the plan (creating decks / cards, rescheduling) ----------

def create_deck(deck_name: str) -> int:
    """
    Create a new deck (or return the existing deck's id).
    """
    return invoke("createDeck", deck=deck_name)


def move_cards_to_deck(card_ids: list[int], deck_name: str) -> None:
    """
    Move cards into a deck e.g. pull leeches/struggling cards out for focused review.
    """
    invoke("changeDeck", cards=card_ids, deck=deck_name)


def create_struggling_deck(deck_name: str, card_ids: list[int]) -> None:
    """
    Create (or reuse) a deck and move the given struggling/leech cards into it.
    """
    create_deck(deck_name)
    move_cards_to_deck(card_ids, deck_name)


def create_card(
    deck_name: str,
    model_name: str,
    fields: dict[str, str],
    tags: list[str] | None = None,
) -> int:
    """
    Create a new note/card in a deck.
    """
    return invoke(
        "addNote",
        note={
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "options": {"allowDuplicate": False},
            "tags": tags or [],
        },
    )


def create_cards(
    deck_name: str,
    model_name: str,
    fields_list: list[dict[str, str]],
    tags: list[str] | None = None,
) -> list[int | None]:
    """
    Create multiple notes/cards in a deck in one call. Returns one id per note
    (None for any that failed, e.g. as a duplicate).
    """
    notes = [
        {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "options": {"allowDuplicate": False},
            "tags": tags or [],
        }
        for fields in fields_list
    ]
    return invoke("addNotes", notes=notes)


def create_reversed_cards(
    card_ids: list[int],
    new_deck_name: str,
    front_field: str = "Front",
    back_field: str = "Back",
) -> None:
    """
    Clone notes with front/back fields swapped into a new deck.
    """
    if not card_ids:
        return

    create_deck(new_deck_name)

    cards = get_cards_info(card_ids)
    note_ids = list({card["note"] for card in cards})
    notes = invoke("notesInfo", notes=note_ids)

    for note in notes:
        fields = note["fields"]
        if front_field not in fields or back_field not in fields:
            continue

        new_fields = {name: data["value"] for name, data in fields.items()}
        new_fields[front_field] = fields[back_field]["value"]
        new_fields[back_field] = fields[front_field]["value"]

        invoke(
            "addNote",
            note={
                "deckName": new_deck_name,
                "modelName": note["modelName"],
                "fields": new_fields,
                "options": {"allowDuplicate": True},
                "tags": note.get("tags", []),
            },
        )


def suspend_cards(card_ids: list[int]) -> None:
    """
    Suspend cards so they stop coming up in review.
    """
    invoke("suspend", cards=card_ids)


def unsuspend_cards(card_ids: list[int]) -> None:
    """
    Unsuspend previously-suspended cards.
    """
    invoke("unsuspend", cards=card_ids)


def set_due_date(card_ids: list[int], days: str) -> None:
    """
    Reschedule cards' due date e.g. front-load struggling cards sooner.
    """
    invoke("setDueDate", cards=card_ids, days=days)
