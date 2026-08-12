"""
Tool schemas exposed to Claude, and dispatch from tool name -> ankiconnect function.

Every tool is tagged `requires_confirmation`. Reads run freely; writes (anything
that creates, moves, suspends, or reschedules cards) must be confirmed by the
user before agent.py calls dispatch() for them.
"""

from . import ankiconnect

# Each entry: Claude-facing schema (name/description/input_schema) plus our own
# requires_confirmation flag. CLAUDE_TOOLS below strips the flag before the list
# goes to the API.
TOOL_SPECS = [
    # --- Reads: decks --------------------------------------------------
    {
        "name": "get_deck_names",
        "description": "List all deck names in the collection.",
        "input_schema": {"type": "object", "properties": {}},
        "requires_confirmation": False,
    },
    {
        "name": "get_deck_stats",
        "description": "Get per-deck counts: new / learning / review / total cards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deck_names": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["deck_names"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_deck_config",
        "description": "Get a deck's options: new-cards-per-day limit, review limit, etc.",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    # --- Reads: cards ----------------------------------------------------
    {
        "name": "get_cards_in_deck",
        "description": "Get all card IDs belonging to a deck.",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_cards_info",
        "description": "Get per-card metadata (interval, ease factor, due, queue/type, lapses, reps) for a list of card IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["card_ids"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_new_cards",
        "description": "Get cards in a deck that have never been studied.",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_seen_cards",
        "description": "Get cards in a deck that have been studied at least once.",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_suspended_cards",
        "description": "Get cards in a deck that are currently suspended.",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_due_cards",
        "description": "Get cards in a deck that are due for review right now.",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    # --- Reads: review history / performance ------------------------------
    {
        "name": "get_review_history",
        "description": "Get the full revlog (timestamp, ease pressed, interval, time taken) for a list of card IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["card_ids"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_reviews_by_day",
        "description": "Get review counts per day for the last N days, for a study heatmap / streak view.",
        "input_schema": {
            "type": "object",
            "properties": {"num_days": {"type": "integer"}},
            "required": ["num_days"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_struggling_cards",
        "description": "Get cards in a deck with a high lapse count or low ease factor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deck_name": {"type": "string"},
                "min_lapses": {"type": "integer", "description": "Default 4."},
                "max_factor": {"type": "integer", "description": "Default 2000."},
            },
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    {
        "name": "get_leeches",
        "description": "Get cards in a deck that Anki has auto-tagged as leeches.",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": False,
    },
    # --- Reads: tags -------------------------------------------------------
    {
        "name": "get_tags",
        "description": "List all tags in the collection.",
        "input_schema": {"type": "object", "properties": {}},
        "requires_confirmation": False,
    },
    {
        "name": "get_cards_by_tag",
        "description": "Get all card IDs carrying a given tag.",
        "input_schema": {
            "type": "object",
            "properties": {"tag": {"type": "string"}},
            "required": ["tag"],
        },
        "requires_confirmation": False,
    },
    # --- Writes: acting on the plan ----------------------------------------
    {
        "name": "create_deck",
        "description": "Create a new deck (or return the existing deck's id).",
        "input_schema": {
            "type": "object",
            "properties": {"deck_name": {"type": "string"}},
            "required": ["deck_name"],
        },
        "requires_confirmation": True,
    },
    {
        "name": "move_cards_to_deck",
        "description": "Move cards into a deck, e.g. pull leeches/struggling cards out for focused review.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_ids": {"type": "array", "items": {"type": "integer"}},
                "deck_name": {"type": "string"},
            },
            "required": ["card_ids", "deck_name"],
        },
        "requires_confirmation": True,
    },
    {
        "name": "create_struggling_deck",
        "description": "Create (or reuse) a deck and move the given struggling/leech cards into it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deck_name": {"type": "string"},
                "card_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["deck_name", "card_ids"],
        },
        "requires_confirmation": True,
    },
    {
        "name": "create_reversed_cards",
        "description": "Clone notes with front/back fields swapped into a new deck, for reverse-recall practice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_ids": {"type": "array", "items": {"type": "integer"}},
                "new_deck_name": {"type": "string"},
                "front_field": {"type": "string", "description": "Default 'Front'."},
                "back_field": {"type": "string", "description": "Default 'Back'."},
            },
            "required": ["card_ids", "new_deck_name"],
        },
        "requires_confirmation": True,
    },
    {
        "name": "suspend_cards",
        "description": "Suspend cards so they stop coming up in review.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["card_ids"],
        },
        "requires_confirmation": True,
    },
    {
        "name": "unsuspend_cards",
        "description": "Unsuspend previously-suspended cards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["card_ids"],
        },
        "requires_confirmation": True,
    },
    {
        "name": "set_due_date",
        "description": "Reschedule cards' due date, e.g. front-load struggling cards sooner.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_ids": {"type": "array", "items": {"type": "integer"}},
                "days": {
                    "type": "string",
                    "description": "AnkiConnect due-date spec, e.g. '0' for today or '1-3' for a random day in a range.",
                },
            },
            "required": ["card_ids", "days"],
        },
        "requires_confirmation": True,
    },
]

# What actually gets sent to the Claude API - no requires_confirmation field.
CLAUDE_TOOLS: list[dict] = [
    {"name": spec["name"], "description": spec["description"], "input_schema": spec["input_schema"]}
    for spec in TOOL_SPECS
]

_CONFIRMATION_REQUIRED: dict[str, bool] = {spec["name"]: spec["requires_confirmation"] for spec in TOOL_SPECS}

_DISPATCH_TABLE = {spec["name"]: getattr(ankiconnect, spec["name"]) for spec in TOOL_SPECS}


def requires_confirmation(tool_name: str) -> bool:
    """Whether agent.py must pause and get user approval before running this tool."""
    return _CONFIRMATION_REQUIRED[tool_name]


def dispatch(tool_name: str, tool_input: dict):
    """Call the ankiconnect function matching `tool_name` with `tool_input` as kwargs."""
    return _DISPATCH_TABLE[tool_name](**tool_input)
