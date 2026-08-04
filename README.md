# BridgeAI 

### Making complex information simple, accessible, and understandable.

## Inspiration

Important information is often hidden behind complicated language.

Legal documents, medical instructions, government notices, and technical information can become difficult for many people to understand.

BridgeAI was created to help people access information by transforming complex content into simple, human-friendly explanations.

---

## What it does

BridgeAI uses Generative AI to simplify complicated information based on the user's needs.

Users can:
- Paste complex text
- Upload a PDF or image
- Select their target audience
- Receive a simplified explanation
- Understand key points and important actions

### Research Study

BridgeAI also includes a built-in research flow to evaluate whether AI simplification actually improves human comprehension. Participants:

1. Enter their first name and age
2. Read a randomly assigned passage (one of 5 subjects: **Medicine, Legal, Academic, Finance, Science/Technology**)
3. Take an initial comprehension quiz + rate their confidence
4. View an AI-simplified version of the same passage
5. Take a second comprehension quiz + rate their confidence again
6. Submit feedback on their experience

All responses are stored in a local SQLite database for analysis.

### Future versions will support:
- OCR extraction for scanned documents
- Accessibility-focused formatting (screen reader optimization, dyslexia-friendly fonts)
- Additional passage subjects and difficulty levels
- Exportable research analytics dashboard

---

## How it works

**Main tool:**
1. User enters complicated information (text, PDF, or image)
2. User selects their audience
3. BridgeAI creates a custom prompt
4. Gemini AI generates an accessible explanation
5. The simplified output is displayed

**Research flow:**
1. Participant provides basic info and is randomly assigned a passage + A/B group
2. Participant reads the passage and answers pre-simplification questions
3. BridgeAI simplifies the same passage using Gemini
4. Participant answers post-simplification questions
5. Participant submits feedback
6. All results are saved to the database

---

## Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask
- SQLite

### AI
- Google Gemini API

### Tools
- Git
- GitHub

---

## Features

 AI-powered simplification
 Audience-based explanations
 PDF and image upload support
 5-subject research study with pre/post comprehension quizzes
 Accessibility-focused design
 Modern glassmorphism interface

---

## Installation

Clone the repository:

```bash
git clone https://github.com/raevn45/BridgeAI-Research
cd BridgeAI-Research
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
SECRET_KEY=any_random_string_here
```

Generate a strong `SECRET_KEY` with `python -c "import secrets; print(secrets.token_hex(32))"`.
If it is not set, the app generates a random key at startup and existing sessions are dropped on restart.

Optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Interface the dev server binds to |
| `PORT` | `5000` | Dev server port |
| `FLASK_DEBUG` | `0` | Set to `1` for the debugger (never in production) |
| `SESSION_COOKIE_SECURE` | `1` | Set to `0` only when testing over plain HTTP |

Run the app locally:

```bash
SESSION_COOKIE_SECURE=0 python app.py
```

Visit `http://localhost:5000` in your browser.

---

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

With a coverage report:

```bash
pytest --cov=app --cov=bridgeai --cov=database --cov=passages --cov-report=term-missing
```

Tests stub out Gemini API calls and use a temporary SQLite database, so no API key or network access is required.

---

## Deployment

BridgeAI is deployed on Replit, which offers:
- Easy cloud hosting and instant setup
- Webview integration for seamless testing
- Direct environment secret management for API keys

To deploy:
1. Import the repository into your Replit workspace
2. Configure your `GEMINI_API_KEY` and `SECRET_KEY` in the Replit Secrets / Environment Variables panel
3. Ensure your `.replit` file uses the Gunicorn production server configuration
4. Click **Publish** or **Deploy** in your deployment panel

[https://bridge-ai-research--raevn.replit.app](https://bridge-ai-research--raevn.replit.app)

---
## Accessing Research Data

Participant responses are stored in `research.db` (SQLite) at the project root. The database
contains participant data and is gitignored — never commit it.

**On PythonAnywhere:**
- Use the **Files** tab to download `research.db` directly
- Or open a **Bash console** and run:
  ```bash
  sqlite3 research.db
  SELECT * FROM participants;
  ```

**Locally:**
- Download `research.db` and open it with a free tool like [DB Browser for SQLite](https://sqlitebrowser.org/) to view, filter, and export results as CSV

---

## License

This project is for educational and research purposes.
