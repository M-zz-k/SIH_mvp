# Data & Evidence Module — MetroScan AI

**Owner:** Data & Evidence Engineer
**Owns:** PostgreSQL schema, evidence image storage, SHA-256 hashing, PDF/DOCX report generation.

This module is the "system of record" for MetroScan AI. Every other module —
Frontend, Backend/API, OCR, and Rule Engine — reads from or writes to the
tables and helpers defined here. Nobody on the team should write their own
DB connection, their own file upload code, or their own PDF generator —
they should import from this module instead.

---

## 1. What's in this folder

```
data-evidence-module/
├── .env.example          ← template — copy to .env and fill in real credentials
├── .env                   ← YOU create this (never commit it — it's in .gitignore)
├── .gitignore
├── requirements.txt
├── database.py            ← DB engine + session
├── models.py               ← the 6 tables (schema)
├── hashing.py              ← SHA-256 "tamper-proof seal"
├── storage.py              ← upload/download evidence to Supabase bucket
├── reports.py              ← builds PDF + DOCX inspection reports
├── test_connection.py      ← run first — checks DB + storage are reachable
├── smoke_test.py           ← run second — proves the full pipeline works end-to-end
└── assets/
    └── fonts/
        ├── DejaVuSans.ttf       ← needed so ₹ renders correctly in PDFs
        └── DejaVuSans-Bold.ttf
```

---

## 2. One-time setup (do this once per machine)

1. **Get the credentials** from whoever owns the Supabase project (or from
   Supabase → Settings → Database / API / Storage if it's your own project):
   - Database connection string
   - Project URL + anon key
   - S3 access key ID + secret (Settings → Storage → S3 Connection — this is
     different from the anon key)

2. **Create your `.env`:**
   ```
   cp .env.example .env
   ```
   Open `.env` and paste in the real values from step 1.
   ⚠️ If your DB password contains special characters like `@`, `#`, `%`,
   URL-encode them in the connection string or the connection will fail
   with a "could not translate host name" error.

3. **Create and activate a virtual environment:**
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   ```

4. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

5. **Confirm everything is reachable:**
   ```
   python test_connection.py
   ```
   You must see two ✅ lines (Database, Storage) before doing anything else.
   If either fails, re-check the matching value in `.env`.

6. **Create the tables** (only needs to be done once per database):
   ```
   python -c "from database import init_db; init_db()"
   ```
   No output = success. Verify in Supabase → Table Editor — you should see
   6 tables: `user`, `inspection`, `evidenceimage`, `extractedfield`,
   `ruleviolation`, `report`.

7. **Prove the whole pipeline works:**
   ```
   python smoke_test.py
   ```
   This creates a fake user → inspection → evidence image → extracted
   fields → rule violation → PDF report, exactly the way real data will
   flow through the system. You should see 6 numbered lines ending in
   `✅ Full pipeline works`.

---

## 3. What each file actually does

### `database.py`
Creates one shared database engine for the whole app, and gives everyone
a `get_session()` context manager to safely read/write. Also has
`init_db()`, which creates all 6 tables from `models.py` if they don't
already exist.

```python
from database import get_session
from models import Inspection

with get_session() as session:
    session.add(Inspection(...))
    session.commit()
```

### `models.py`
The schema — one Python class per table, using SQLModel. This is the
single source of truth for what an "Inspection" or "EvidenceImage" looks
like. Everyone should import table classes directly from here rather
than redefining fields elsewhere.

```
User ──< Inspection ──< EvidenceImage
                    ──< ExtractedField
                    ──< RuleViolation
                    ──< Report
```
One `Inspection` row = one scan run (a bulk batch item or a single guided
scan). Everything else links back to it via `inspection_id`.

| Table | What it represents |
|---|---|
| `User` | An inspector/supervisor/admin logging into the system |
| `Inspection` | One scan run — bulk listing or single label |
| `EvidenceImage` | An uploaded label/listing photo + its SHA-256 hash |
| `ExtractedField` | One OCR'd field (MRP, quantity, manufacturer, etc.) |
| `RuleViolation` | One flagged rule breach, tied to a specific rule code |
| `Report` | A generated PDF/DOCX report + its own hash |

### `hashing.py`
SHA-256 hashing — the "tamper-proof seal" mentioned across the pitch deck.
**Rule for the whole team:** hash evidence bytes *before* uploading them,
and save that hash on the row (`EvidenceImage.file_hash` or
`Report.evidence_hash`). Anyone can later re-hash a downloaded file and
compare it to prove it wasn't altered.

```python
from hashing import hash_bytes
file_hash = hash_bytes(image_bytes)
```

### `storage.py`
Uploads/downloads evidence images and reports to the Supabase bucket
(`evidence-images`) using the S3-compatible API. **Nobody should write
evidence images to local disk — always go through this file.**

```python
from storage import upload_bytes, build_key
key = build_key(inspection_id, "label.jpg", prefix="evidence")
upload_bytes(image_bytes, key, content_type="image/jpeg")
```

### `reports.py`
Builds the actual PDF (ReportLab) and DOCX (python-docx) inspection
reports that get shown to officers and sellers. Bundles a Unicode font
(`assets/fonts/DejaVuSans.ttf`) so currency symbols like ₹ render
correctly — ReportLab's default font can't display them.

```python
from reports import build_pdf_report
pdf_bytes = build_pdf_report(inspection_data)  # see reports.py for the expected dict shape
```

### `test_connection.py`
Run this first, always. Confirms the DB and the storage bucket are both
reachable before you try to build or debug anything else on top of them.

### `smoke_test.py`
Run this second. Walks a fake record through the *entire* module —
user → inspection → evidence upload → hash → extracted fields → rule
violation → generated PDF report → upload — so you can prove the whole
thing works in one shot instead of testing six things separately.
Safe to re-run any time; it reuses the same test user and just adds a
fresh inspection each run.

---

## 4. How other teammates should use this module

- **Backend/API lead:** import `get_session()` from `database.py` and the
  table classes from `models.py` to read/write inspection data from your
  FastAPI endpoints.
- **OCR engineer:** after extracting fields, save them as `ExtractedField`
  rows via `get_session()`. Save the raw label image via `storage.py` +
  `hashing.py` as an `EvidenceImage` row — never write it to local disk.
- **Rule engine developer:** save each flagged breach as a `RuleViolation`
  row, using a real `rule_code` (e.g. `LM-PCR-2011-R6`) so it's auditable.
- **Frontend/dashboard lead:** query through the Backend/API layer, not
  directly against Supabase — Row Level Security is enabled with no
  policies, so only the `postgres`-role backend connection can read/write.
- **Everyone:** never bypass `storage.py` or `hashing.py` — every piece of
  evidence needs a matching hash for the "tamper-proof" claim in the pitch
  to actually be true.

---

## 5. Resetting test data

To wipe smoke-test rows before a real run or a demo, run this in
Supabase → SQL Editor:

```sql
TRUNCATE TABLE
  public.report,
  public.ruleviolation,
  public.extractedfield,
  public.evidenceimage,
  public.inspection,
  public."user"
RESTART IDENTITY CASCADE;
```

Then manually delete the corresponding files in **Storage → evidence-images**
(the `evidence/` and `reports/` folders) — SQL doesn't touch stored files.

---

## 6. Known things worth knowing

- **Row Level Security (RLS)** is enabled on all 6 tables with no policies,
  meaning only the `postgres` connection (used by `database.py`) can
  read/write. This is intentional and safe as long as everyone accesses
  the DB through this module / the backend API, not directly via the
  Supabase client from the frontend.
- **Currency symbols (₹):** PDF generation uses a bundled DejaVu Sans font
  specifically so ₹ doesn't render as a black box. If you ever see garbled
  symbols in a generated PDF, check that `assets/fonts/` was copied
  alongside `reports.py`.
- **Migrations:** for hackathon speed we're using `init_db()`
  (create-if-not-exists, no history). If the schema needs to change after
  teammates are already relying on it, switch to Alembic instead of
  editing `models.py` and rerunning `init_db()` blind — see the original
  handoff notes for the Alembic commands.
