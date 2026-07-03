# Mining Study Hub

A Flask web app for Diploma in Mining Engineering students: PDF library, notes,
question bank, unified search, an AI study assistant, student accounts, and an
admin approval panel.

## Setup

1. **Install Python 3.12+** if you don't have it.

2. **Create a virtual environment and install dependencies:**
   ```bash
   cd mining-study-hub
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set:
   - `SECRET_KEY` — any random string
   - `ANTHROPIC_API_KEY` — your Anthropic API key (for the AI Assistant page).
     Get one at https://console.anthropic.com/settings/keys
   - `ANTHROPIC_MODEL` — defaults to `claude-sonnet-5`, change if needed

4. **Initialize the database** (creates tables + starter subjects):
   ```bash
   python init_db.py
   ```

5. **Run the app:**
   ```bash
   python app.py
   ```
   Visit http://127.0.0.1:5000

6. **Register your first account** at `/register` — it automatically becomes
   an admin account. Use it to add more subjects at `/admin/subjects` and
   approve/reject content submitted by other students at `/admin`.

## How content approval works

By default, uploaded PDFs, notes, and questions are auto-approved (`approved=True`
in `models.py`) so the app is usable immediately. If you want every submission to
require admin approval first, change `approved = db.Column(db.Boolean, default=True)`
to `default=False` in `models.py` for `PDF`, `Note`, and `Question`, then re-run
`init_db.py`. New submissions will then show up under **Admin → Pending** until
approved.

## Project structure

```
mining-study-hub/
├── app.py              # App factory + entry point
├── config.py           # Configuration from environment variables
├── extensions.py       # Shared Flask extensions (db, login, csrf)
├── models.py            # SQLAlchemy models
├── init_db.py           # One-time DB setup + starter subjects
├── requirements.txt
├── .env.example
├── routes/               # Blueprints: auth, main, pdfs, notes, questions, search, ai, admin
├── templates/            # Jinja2 templates
├── static/css/style.css  # Design system (rock-strata theme)
├── static/js/main.js     # AI assistant chat logic
└── uploads/pdfs/          # Uploaded PDF files land here
```

## Search

Search (`/search`) currently does a `LIKE`-based match across PDF titles, note
titles/content, and question text/answers. This is simple and reliable for a
student-scale library. If the library grows large, swap it for SQLite's FTS5
full-text search extension for faster, ranked results.

## AI Assistant

The AI Assistant page (`/ai`) calls the Anthropic API directly using your
`ANTHROPIC_API_KEY`. It's pre-loaded with mining-specific system instructions
so it gives exam-appropriate answers (explanations, N-mark answers, MCQs, viva
questions). If the key isn't set, the page shows a clear message instead of
crashing.

## Known limitations / next steps

- No file-type/virus scanning on uploads beyond extension check — fine for
  a small trusted user base, add stricter checks before wider deployment.
- Search is substring-based, not ranked — see note above.
- No password reset flow yet (would need email sending configured).
- Deploy to Render/Railway/PythonAnywhere for a public URL — set the same
  environment variables there and use a persistent disk for `uploads/` and
  `database.db` (or move to PostgreSQL for production).
