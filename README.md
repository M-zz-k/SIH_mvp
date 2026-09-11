# METROSCAN AI — Backend (Dev2 / Backend-API lead)

FastAPI backend for the METROSCAN AI compliance platform. Handles auth,
request orchestration, and wires together OCR/extraction, the rule engine,
and evidence/storage — each owned by a different teammate.

## Quickstart

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive Swagger UI (test every
endpoint from the browser — no frontend needed yet).

Run tests:
```bash
pytest
```

## How this avoids merge conflicts

Everyone works in their **own file** and imports a **shared contract**:

| Who | Owns | Never touches |
|---|---|---|
| **Dev2 (me)** | `app/api/routes/*.py`, `app/services/pipeline.py`, `app/core/*`, `app/main.py`, `app/models/schemas.py` (contract owner) | other devs' interface files |
| Dev3 (OCR) | inside `app/services/extraction_interface.py` only | routes, main.py |
| Dev4 (rules) | inside `app/services/rule_engine_interface.py` only | routes, main.py |
| Dev5 (evidence/PDF) | inside `app/services/storage_interface.py` only | routes, main.py |
| Dev1 (frontend) | separate repo/folder, calls this API over HTTP | this repo |

Each `*_interface.py` file has a **mock implementation already working** —
the whole pipeline runs end-to-end today with fake data. Dev3/4/5 each pull
this repo, replace only the body of their one function (signature stays
identical), and push. Because nobody edits the same file as anyone else,
there's nothing to merge-conflict on.

If a teammate needs a new field in the data contract, they add it to
`app/models/schemas.py` and message the group first — that file is the one
shared surface, so treat changes to it like a mini design review.

## API surface

- `POST /auth/register` — public self-registration; **always creates an `inspector` role**
- `POST /auth/login` — returns a JWT; role is embedded in the token
- `POST /auth/promote` — **admin-only** (403 for inspector/supervisor); body: `{"email": "...", "new_role": "supervisor"|"admin"}`; promotes an existing user's role
- `POST /scan` — single-image capture (in-store mode)
- `POST /bulk` — multi-image bulk upload; response includes `failed_filenames: string[]` so the frontend can show a per-file retry list
- `GET /bulk/{job_id}`, `GET /bulk/{job_id}/results`
- `GET /results?q=&tier=&date_from=&date_to=` — searchable repository
- `GET /results/{id}` — full inspection detail
- `POST /results/{id}/report?format=pdf` — export
- `GET /dashboard/stats` — supervisor/admin-only analytics (returns 403 for inspector tokens)

### Changed response shapes (vs. original)

| Endpoint | Field | Change |
|---|---|---|
| `POST /bulk` | `failed_filenames` | **New** — `string[]` of filenames that errored; empty list on full success |
| `POST /auth/register` | `role` | Always `"inspector"` now; was previously controllable via query param |
| `POST /auth/promote` | *(new endpoint)* | Admin-only; body `{email, new_role}`; returns `UserOut` |

> **Teammate note (schemas.py change):** `BulkJobStatus` gained an optional `failed_filenames: list[str] = []` field.
> Dev1 (frontend) and anyone deserialising this shape should accept the new field — it defaults to `[]` so existing clients won't break.
> Dev3/4/5's interface files are unaffected.

## Swapping SQLite → Postgres

Default is local SQLite (`metroscan.db`) so this runs with zero setup. Once
Dev5's Postgres schema is ready, just set `DATABASE_URL` in `.env` to the
Postgres connection string — no code changes needed, SQLAlchemy handles it.
