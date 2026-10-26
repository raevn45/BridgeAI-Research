# BridgeAI: one website, two connected experiences

BridgeAI combines the AI simplification tool and the BridgeAI Research study in **one Flask application, one repository, and one Vercel deployment**.

## What lives here

- **Home page** at `/`: shared entry point and navigation.
- **BridgeAI simplifier** at `/app`: paste complex text or upload a PDF/image, choose an audience, and get a clearer explanation.
- **Research study** at `/research`: participant consent, passage, comprehension quizzes, AI-simplified passage, follow-up quiz, confidence ratings, and feedback. The flow is also available through the `/study/...` routes.

The older standalone `raevn45/BridgeAI` repository contains an earlier version of the same simplification tool. This repository is the canonical combined deployment so the tool and study share one homepage, navigation, backend, and deployment configuration instead of maintaining duplicate Flask apps.

## Stack

- Python and Flask
- Google Gemini API
- HTML, CSS, JavaScript
- SQLite for local development; managed PostgreSQL for Vercel
- Vercel for deployment

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Create a `.env` file:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=replace_with_a_long_random_secret
SESSION_COOKIE_SECURE=0
```

Run the app:

```bash
python app.py
```

Open `http://127.0.0.1:5000`. `SESSION_COOKIE_SECURE=0` is only for local HTTP development. Keep it enabled in production HTTPS.

## Deploy the combined site to Vercel

Import **only** `raevn45/BridgeAI-Research` into Vercel and use the repository root as the project root. The Flask entry point is `app.py`; frontend files used in production live under `public/assets/research/`.

Set these environment variables in Vercel for the Production environment (and Preview if you want preview deployments to work):

| Variable | Required | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | Yes | Gemini API access for simplification |
| `SECRET_KEY` | Yes | Stable, strong Flask session signing key |
| `DATABASE_URL` | Yes | Connection URL for managed PostgreSQL |
| `ADMIN_EXPORT_TOKEN` | Recommended | Bearer token required for the private participant-data export endpoint |
| `SESSION_COOKIE_SECURE` | Yes in production | Set to `1` for HTTPS |

**Do not deploy the research flow until `DATABASE_URL` points to a persistent managed PostgreSQL database.** Vercel's function filesystem is not durable storage. Do not rely on a SQLite file for participant responses in production.

### Participant data warning

The old SQLite database is not automatically copied into PostgreSQL by deployment. Back it up and plan a separate, verified migration if existing study responses must be preserved. Do not commit `research.db` or participant data to GitHub.

### Static assets

Vercel serves files under `public/` directly. The Flask route for `/assets/<path>` is a local-development fallback, so the same templates work both locally and on Vercel.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The GitHub Actions test workflow is intended to run the test suite on pushes and pull requests. A green workflow and a live Vercel preview still need to be confirmed before treating the deployment as production-ready.

## Research integrity

The research flow stores participant submissions and is separate from the public simplification tool. Keep the study consent language, data handling, and export access appropriate for the actual research protocol.
