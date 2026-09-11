"""
================================================================================
SHARED DATA CONTRACT — read this before writing any integration code.
================================================================================
This file is the single source of truth for the JSON shape that flows between
every module. It's the thing that lets 6 people build in parallel without
merge conflicts:

  Dev3 (OCR/extraction) -> returns an ExtractionResult
  Dev4 (rule engine)     -> takes an ExtractionResult, returns a RuleEngineResult
  Dev5 (evidence/PDF)    -> takes a full InspectionResult, returns evidence + report
  Dev1 (frontend)        -> renders whatever comes back from GET /results/*
  Dev2 (me, backend)     -> orchestrates all of the above, owns this file

RULE: if you need a new field, add it here first and message the group —
don't invent a parallel shape in your own module. Everyone imports from here.
================================================================================
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VerdictTier(str, Enum):
    """Every declaration AND the label overall resolves to one of these.
    Never a raw pass/fail — see project spec, item 5 (Tiered output)."""
    LIKELY_COMPLIANT = "likely_compliant"
    NEEDS_REVIEW = "needs_officer_review"
    LIKELY_VIOLATION = "likely_violation"


class UserRole(str, Enum):
    INSPECTOR = "inspector"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class ScanMode(str, Enum):
    SINGLE = "single_scan"
    BULK = "bulk"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class UserOut(BaseModel):
    id: int
    email: str
    role: UserRole


# ---------------------------------------------------------------------------
# Extraction contract  (Dev3 plugs in here)
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    """Pixel coordinates on the ORIGINAL uploaded image. Origin = top-left."""
    x: int
    y: int
    width: int
    height: int


class ExtractedField(BaseModel):
    field_name: str  # e.g. "mrp", "net_quantity", "manufacturer", "date_of_packing",
                      # "consumer_care", "country_of_origin"
    raw_text: Optional[str] = None
    parsed_value: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None


class ExtractionResult(BaseModel):
    """What Dev3's OCR/extraction module must return for one label image."""
    image_id: str
    ocr_engine: str = "paddleocr"
    fields: list[ExtractedField]
    largest_text_bbox: Optional[BoundingBox] = None  # brand-name-sized text,
                                                        # used by Dev4's font heuristic
    raw_ocr_text: Optional[str] = None  # full page text, useful for debugging


# ---------------------------------------------------------------------------
# Rule engine contract  (Dev4 plugs in here)
# ---------------------------------------------------------------------------

class RuleViolation(BaseModel):
    rule_id: str          # e.g. "LMR2011-8(a)-net-quantity-present"
    field_name: str
    description: str
    citation: str         # actual provision reference, e.g. "Rule 6(1)(a)"
    tier: VerdictTier


class FontHeuristicResult(BaseModel):
    field_name: str
    declaration_height_px: int
    reference_height_px: int  # largest_text_bbox height
    ratio: float
    tier: VerdictTier


class RuleEngineResult(BaseModel):
    """What Dev4's rule engine module must return for one ExtractionResult."""
    image_id: str
    rule_set_version: str
    field_verdicts: dict[str, VerdictTier]  # field_name -> tier
    violations: list[RuleViolation]
    font_heuristics: list[FontHeuristicResult] = []
    overall_tier: VerdictTier


# ---------------------------------------------------------------------------
# Evidence / reporting contract  (Dev5 plugs in here)
# ---------------------------------------------------------------------------

class EvidenceRecord(BaseModel):
    image_id: str
    sha256_hash: str
    annotated_image_path: Optional[str] = None  # image with bounding boxes drawn
    stored_at: datetime


class ReportRequest(BaseModel):
    inspection_id: int
    format: str = Field(pattern="^(pdf|docx|csv)$", default="pdf")


class ReportResponse(BaseModel):
    inspection_id: int
    file_path: str
    format: str


# ---------------------------------------------------------------------------
# Full inspection (what the API actually returns to the frontend)
# ---------------------------------------------------------------------------

class InspectionResult(BaseModel):
    id: int
    scan_mode: ScanMode
    product_name: Optional[str] = None
    listing_url: Optional[str] = None
    created_at: datetime
    created_by: str
    extraction: ExtractionResult
    rule_result: RuleEngineResult
    evidence: Optional[EvidenceRecord] = None
    overall_tier: VerdictTier


class BulkJobStatus(BaseModel):
    job_id: str
    status: JobStatus
    total_items: int
    completed_items: int
    failed_items: int = 0
    # Names of files that failed processing so the frontend can show a retry list.
    # Empty list means no failures or status was loaded from DB (no filename persisted).
    failed_filenames: list[str] = []


class InspectionSummary(BaseModel):
    """Lightweight row for dashboard/search list views."""
    id: int
    product_name: Optional[str]
    brand: Optional[str] = None
    created_at: datetime
    overall_tier: VerdictTier
    violation_count: int


class DashboardStats(BaseModel):
    total_scans: int
    likely_compliant: int
    needs_review: int
    likely_violation: int
    top_violation_types: list[dict]  # [{"rule_id": ..., "count": ...}, ...]
