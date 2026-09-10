# METROSCAN AI

**Compliance-checking platform for packaged commodities under India's Legal Metrology (Packaged Commodities) Rules, 2011.**

Officers upload product label photos (single or bulk). The system runs OCR, extracts mandatory declarations, validates them against rules, checks font sizes, and returns a tiered compliance verdict with tamper-proof evidence.

---

## 🚀 Quick Start (Get running in < 10 minutes)

### 1. Clone & Setup

```bash
git clone <repo-url> && cd SIH_mvp
cp .env.example .env
```

### 2. Start PostgreSQL (requires Docker)

```bash
docker-compose up -d
```

> This spins up Postgres at `localhost:5432` with user `metroscan` / password `metroscan`.
> If you don't have Docker, install Postgres manually and create a DB named `metroscan`.

### 3. Backend (FastAPI)

```bash
# Create virtual environment (one time)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Run the API server
cd backend
uvicorn main:app --reload --port 8000
```

API will be at **http://localhost:8000** — try http://localhost:8000/docs for Swagger UI.

### 4. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

App will be at **http://localhost:5173** — frontend proxies `/api/*` to the backend.

---

## 📁 Repository Structure

```
SIH_mvp/
├── shared/                  # 🔒 SHARED DATA CONTRACT — read by everyone
│   ├── models.py            # Pydantic models (the schema)
│   └── mock_data.json       # 3 realistic mock inspection results
│
├── frontend/                # 👤 Person 1 — Frontend/Dashboard Lead
│   └── src/
│       ├── pages/           # Login, Upload, Results, Repository pages
│       ├── data/            # Copy of mock_data.json for offline UI dev
│       └── App.jsx          # Router & navigation
│
├── backend/                 # 👤 Person 2 — Backend/API Lead
│   └── main.py              # FastAPI app with route stubs
│
├── ocr_extraction/          # 👤 Person 3 — OCR & Extraction Engineer
│   └── extract.py           # extract_declarations(image_path) → Declarations
│
├── rule_engine/             # 👤 Person 4 — Rule Engine & Font Heuristic
│   └── validate.py          # validate(declarations) → ComplianceResult
│
├── data_evidence/           # 👤 Person 5 — Data & Evidence Engineer
│   ├── evidence.py          # hash_image(), generate_pdf(), DB helpers
│   └── db_models.py         # SQLAlchemy ORM (placeholder)
│
├── docs/                    # Architecture diagrams & references
│   └── ARCHITECTURE.md
│
├── requirements.txt         # Python dependencies (all pre-listed)
├── docker-compose.yml       # PostgreSQL only
├── .env.example             # Environment variable template
└── README.md                # ← You are here
```

---

## 👥 Team Assignments & Branch Convention

| Person | Role                          | Branch             | Works in           | Start file                        |
|--------|-------------------------------|---------------------|--------------------|-----------------------------------|
| 1      | Frontend / Dashboard Lead     | `feature/frontend`  | `/frontend/`       | `frontend/src/pages/UploadPage.jsx` |
| 2      | Backend / API Lead            | `feature/backend`   | `/backend/`        | `backend/main.py`                 |
| 3      | OCR & Extraction Engineer     | `feature/ocr`       | `/ocr_extraction/` | `ocr_extraction/extract.py`       |
| 4      | Rule Engine & Font Heuristic  | `feature/rules`     | `/rule_engine/`    | `rule_engine/validate.py`         |
| 5      | Data & Evidence Engineer      | `feature/evidence`  | `/data_evidence/`  | `data_evidence/evidence.py`       |
| 6      | Integration / QA Lead         | `main`              | Everywhere (read)  | `backend/main.py` + `README.md`   |

**Rule: Each person only modifies files in their assigned directory.** This eliminates merge conflicts. If you need a schema change, announce it to the team first.

### Creating your branch

```bash
git checkout -b feature/<your-area>   # e.g., feature/ocr
# Work in your directory, commit, push
git push -u origin feature/<your-area>
```

---

## 🔗 Shared Data Contract

**File: [`shared/models.py`](shared/models.py)**

This is the single source of truth for data shapes. Every module imports from here:

```python
from shared.models import InspectionResult, Declarations, ComplianceResult
```

### ⚠️ Schema Change Policy

**DO NOT change `shared/models.py` without telling the entire team.** Every module depends on these exact shapes. If you need a new field:

1. Announce in the team chat
2. Get agreement from affected people
3. Make the change with a default value (backward compatible)
4. Everyone pulls the change

### Key Types

| Type              | Produced by | Consumed by      | Description                            |
|-------------------|-------------|------------------|----------------------------------------|
| `Declarations`    | Person 3    | Person 4         | OCR-extracted fields (MRP, qty, etc.)  |
| `ComplianceResult`| Person 4    | Person 2, 5      | Compliance verdicts + font check + tier|
| `EvidenceRecord`  | Person 5    | Person 2         | SHA-256 hash + timestamp + PDF path    |
| `InspectionResult`| Person 2    | Person 1 (API)   | Everything combined — the API response |

---

## 🔄 Integration Order (Pipeline)

```
Upload Image
    │
    ▼
┌──────────────────┐
│  OCR Extraction   │  Person 3: extract_declarations(image) → Declarations
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Rule Engine      │  Person 4: validate(declarations) → ComplianceResult
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Data & Evidence  │  Person 5: hash_image() + generate_pdf() → EvidenceRecord
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Backend API      │  Person 2: Orchestrates above, returns InspectionResult
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Frontend         │  Person 1: Renders InspectionResult from API
└──────────────────┘
```

**Key rule: The frontend ONLY talks to the backend API.** It never imports from `ocr_extraction`, `rule_engine`, or `data_evidence` directly.

---

## 🧪 Testing the Pipeline (Person 6 — QA Lead)

Even before any real implementation, you can test the full pipeline:

```bash
# Backend returns mock data shaped correctly
curl http://localhost:8000/results/insp-001-abc

# Upload a test image (returns mock analysis)
curl -X POST http://localhost:8000/upload/single -F "file=@test_image.jpg"

# Search (returns all mock results)
curl "http://localhost:8000/results/search/query?q=tata"
```

The frontend at http://localhost:5173 renders all mock data visually from the first commit.

---

## 🏗️ Environment Variables

Copy `.env.example` to `.env` and update values:

| Variable              | Default                                              | Description                     |
|-----------------------|------------------------------------------------------|---------------------------------|
| `DATABASE_URL`        | `postgresql://metroscan:metroscan@localhost:5432/metroscan` | PostgreSQL connection string |
| `JWT_SECRET`          | (change this)                                        | Secret for signing JWTs         |
| `STORAGE_PATH`        | `./uploads`                                          | Where uploaded images are saved |
| `REPORTS_PATH`        | `./reports`                                          | Where generated PDFs are saved  |
| `VITE_API_URL`        | `http://localhost:8000`                              | Backend URL for frontend        |
