# BridgeAI

AI-powered tool that simplifies complex text (legal, medical, academic, financial, technical) for different audiences. Includes a built-in research study flow to measure comprehension improvement.

## Stack

- **Backend:** Python 3.12, Flask, SQLite
- **AI:** Google Gemini API (`google-genai`)
- **Frontend:** HTML/CSS/JS (Jinja2 templates, glassmorphism design)

## Running the app

The workflow **Start application** runs `python app.py` on port 5000.

```bash
python app.py
```

Environment variables / secrets needed:
- `GEMINI_API_KEY` — Google Gemini API key (set in Replit Secrets)
- `SECRET_KEY` — Flask session secret (set in Replit Secrets — keeps sessions stable across restarts)
- `HOST` — set to `0.0.0.0` in shared env (already configured)

## Project structure

| Path | Purpose |
|------|---------|
| `app.py` | Flask routes and app setup |
| `bridgeai.py` | Gemini API client and simplification logic |
| `database.py` | SQLite init and research data storage |
| `passages.py` | Research study passages (5 subjects) |
| `templates/` | Jinja2 HTML templates |
| `static/` | CSS and JS assets |
| `tests/` | pytest test suite (stubs Gemini, uses temp DB) |

## Running tests

```bash
pytest
# with coverage:
pytest --cov=app --cov=bridgeai --cov=database --cov=passages --cov-report=term-missing
```

## Research data

Participant responses are stored in `research.db` (SQLite, gitignored). Open with DB Browser for SQLite or query directly:

```bash
sqlite3 research.db "SELECT * FROM participants;"
```

## User preferences
