# Anki Study Agent

## Quick Start

### Local Development

1. Clone the repo

```bash
git clone https://github.com/asinthelol/Anki-Agent.git
cd Anki-Agent
```

2. Set up the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

3. Add your Anthropic API key

```bash
echo ANTHROPIC_API_KEY=sk-ant-your-key-here > .env
```

4. Run the CLI (Anki must be open with the AnkiConnect add-on installed)

```bash
python -m app.cli
```

## How To Use

1. Launch the CLI and ask about your deck or study performance
2. The agent reads your Anki collection. e.g. decks & cards
3. Approve or reject each write action (creating cards/decks, suspending, rescheduling) before it runs
4. Switch models mid-conversation with `/model`, or start fresh with `/new`
5. Close the CLI. Launching again resumes your conversation.

## Features

- Uses Claude to create study plans via AnkiConnect data
- Read tools for decks, cards, review history, leeches, struggling cards, and tags
- Write tools (create/move/suspend/reschedule cards, create reversed-card decks) with action confirmation
- Interactive terminal client with model switching, server-side conversation compaction, and persistence across restarts

## Coming Soon

- Web Application

## Built With

- **CLI**: Python (stdlib REPL + colorama)
- **Agent**: Python, Anthropic SDK
- **Data source**: AnkiConnect (localhost:8765)
- **Backend (planned)**: FastAPI
- **Frontend (planned)**: Next.js

## License

I don't care what you do with it, just don't say you made this.

---

### by asinthelol
