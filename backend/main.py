"""
METROSCAN AI — Backend API (FastAPI) — Person 2's workspace
=============================================================

This is the main API server. It orchestrates the pipeline:
  Upload → OCR Extraction → Rule Engine → Evidence → Response

All routes return data matching the shared.models.InspectionResult schema.
Currently, every route calls stub functions that return mock data, so the
full pipeline "works" end-to-end from Day 1 — the frontend can call every
endpoint and get properly shaped responses.

Run with:
  cd backend
  uvicorn main:app --reload --port 8000
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import List, Optional

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.models import (
    InspectionResult,
    Declarations,
    ComplianceResult,
    EvidenceRecord,
)

# Import module stubs — each person replaces internals, signatures stay stable
from ocr_extraction.extract import extract_declarations
from rule_engine.validate import validate
from data_evidence.evidence import (
    create_evidence_record,
    generate_pdf,
    save_inspection,
    get_inspection,
    search_inspections,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="METROSCAN AI",
    description="Compliance-checking API for Legal Metrology (Packaged Commodities) Rules, 2011",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load mock data for fallback responses
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "shared", "mock_data.json")
with open(MOCK_DATA_PATH, "r", encoding="utf-8") as f:
    MOCK_RESULTS: List[dict] = json.load(f)


# ---------------------------------------------------------------------------
# Auth models — Person 2 implements real JWT auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Health check."""
    return {"status": "ok", "service": "METROSCAN AI", "version": "0.1.0"}


@app.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate an officer and return a JWT.

    # TODO(Person 2 — Backend Lead): Implement real auth:
    #   1. Verify credentials against DB (or hardcoded list for MVP)
    #   2. Generate JWT with PyJWT using JWT_SECRET from env
    #   3. Return token with expiry
    """

    # ---------- MOCK — accept any credentials ----------
    return LoginResponse(
        access_token="mock-jwt-token-replace-me",
        token_type="bearer",
    )


@app.post("/upload/single")
async def upload_single(file: UploadFile = File(...)):
    """Upload a single product label image and run the full pipeline.

    Pipeline: save image → OCR extract → validate rules → hash evidence → generate PDF

    # TODO(Person 2 — Backend Lead): Implement real orchestration:
    #   1. Save uploaded file to STORAGE_PATH
    #   2. Call extract_declarations(saved_path) — Person 3's module
    #   3. Call validate(declarations) — Person 4's module
    #   4. Call create_evidence_record(saved_path, pdf_path) — Person 5's module
    #   5. Call generate_pdf(result) — Person 5's module
    #   6. Call save_inspection(result) — Person 5's module
    #   7. Return InspectionResult
    """

    # ---------- MOCK — run stubs in the correct order ----------
    image_path = f"uploads/{file.filename}"
    inspection_id = str(uuid.uuid4())[:12]

    # Step 1: OCR extraction (Person 3)
    declarations = extract_declarations(image_path)

    # Step 2: Rule validation (Person 4)
    compliance_result = validate(declarations)

    # Step 3: Evidence (Person 5)
    evidence = create_evidence_record(image_path, f"reports/{inspection_id}.pdf")

    # Assemble final result
    result = InspectionResult(
        id=inspection_id,
        product_name=file.filename or "Uploaded Product",
        created_at=datetime.utcnow(),
        declarations=declarations,
        compliance_result=compliance_result,
        evidence=evidence,
    )

    return result.model_dump()


@app.post("/upload/bulk")
async def upload_bulk(files: List[UploadFile] = File(...)):
    """Upload multiple product label images (bulk inspection).

    # TODO(Person 2 — Backend Lead): Implement:
    #   1. Accept multiple files or a CSV of image URLs
    #   2. Process each through the same pipeline as /upload/single
    #   3. Return a list of InspectionResults
    #   4. Consider async processing for large batches
    """

    # ---------- MOCK — return mock data for each file ----------
    results = []
    for i, file in enumerate(files):
        mock = MOCK_RESULTS[i % len(MOCK_RESULTS)].copy()
        mock["id"] = str(uuid.uuid4())[:12]
        mock["product_name"] = file.filename or f"Product {i+1}"
        results.append(mock)

    return {"results": results, "total": len(results)}


@app.get("/results/{inspection_id}")
async def get_result(inspection_id: str):
    """Retrieve a single inspection result by ID.

    # TODO(Person 2 — Backend Lead): Wire to Person 5's get_inspection().
    """

    # Try real DB first
    result = get_inspection(inspection_id)
    if result:
        return result

    # Fallback to mock data
    for mock in MOCK_RESULTS:
        if mock["id"] == inspection_id:
            return mock

    # Default: return first mock with overridden ID
    fallback = MOCK_RESULTS[0].copy()
    fallback["id"] = inspection_id
    return fallback


@app.get("/results/search/query")
async def search_results(
    q: str = Query("", description="Search by product name"),
    tier: str = Query("", description="Filter by tier"),
    limit: int = Query(50, description="Max results"),
):
    """Search inspection results by product name or tier.

    # TODO(Person 2 — Backend Lead): Wire to Person 5's search_inspections().
    """

    # Try real DB first
    db_results = search_inspections(query=q, tier=tier, limit=limit)
    if db_results:
        return {"results": db_results, "total": len(db_results)}

    # Fallback to mock data with simple filtering
    filtered = MOCK_RESULTS
    if q:
        filtered = [r for r in filtered if q.lower() in r.get("product_name", "").lower()]
    if tier:
        filtered = [
            r for r in filtered
            if r.get("compliance_result", {}).get("tier", "") == tier
        ]

    return {"results": filtered[:limit], "total": len(filtered)}
