"""
METROSCAN AI — Shared Data Contract (Pydantic Models)
=====================================================

This is the SINGLE SOURCE OF TRUTH for data shapes passed between modules.

██████████████████████████████████████████████████████████████████████████████
██  WARNING: Do NOT modify this file without announcing to the whole team. ██
██  Every module depends on these exact shapes. Changing a field name or   ██
██  type here will break OCR, rule engine, evidence, backend, AND frontend.██
██████████████████████████████████████████████████████████████████████████████

Data flow:
  OCR Extraction  →  Declarations (list of DeclarationField)
  Rule Engine      →  ComplianceResult (compliance + font_check + tier)
  Data & Evidence  →  EvidenceRecord (hash, timestamp, pdf_path)
  Backend          →  InspectionResult (combines all of the above)
  Frontend         →  Renders InspectionResult as JSON via the API

Usage in any module:
  import sys, os
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
  from shared.models import InspectionResult, Declarations, ...
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FieldStatus(str, Enum):
    """Status of a single extracted/validated field."""
    present = "present"
    missing = "missing"
    unclear = "unclear"


class ComplianceStatus(str, Enum):
    """Per-field compliance verdict."""
    PASS = "pass"
    FAIL = "fail"
    FLAG = "flag"  # needs human review


class FontCheckStatus(str, Enum):
    """Whether the font size meets the minimum threshold."""
    PASS = "pass"
    FAIL = "fail"
    UNABLE_TO_CHECK = "unable_to_check"


class Tier(str, Enum):
    """Final tier assigned to an inspection."""
    LIKELY_COMPLIANT = "likely_compliant"
    NEEDS_REVIEW = "needs_review"
    LIKELY_VIOLATION = "likely_violation"


# ---------------------------------------------------------------------------
# Declaration fields (output of OCR extraction — Person 3)
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    """Pixel-level bounding box from OCR."""
    x: int = Field(..., description="Top-left x")
    y: int = Field(..., description="Top-left y")
    w: int = Field(..., description="Width in px")
    h: int = Field(..., description="Height in px")


class DeclarationField(BaseModel):
    """A single mandatory declaration extracted from the label."""
    field_name: str = Field(
        ...,
        description="One of: mrp, net_quantity, manufacturer, date_declaration",
    )
    value: Optional[str] = Field(None, description="Extracted text value")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box of the text")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="OCR confidence score"
    )
    status: FieldStatus = Field(
        FieldStatus.missing, description="Extraction status"
    )


class Declarations(BaseModel):
    """Full set of declarations extracted from one product label."""
    mrp: DeclarationField
    net_quantity: DeclarationField
    manufacturer: DeclarationField
    date_declaration: DeclarationField


# ---------------------------------------------------------------------------
# Font-size check (output of rule engine — Person 4)
# ---------------------------------------------------------------------------

class FontCheckEntry(BaseModel):
    """Font-size ratio check for one field."""
    field: str
    text_height_px: float = Field(
        ..., description="Height of the text bounding box in pixels"
    )
    reference_height_px: float = Field(
        ..., description="Height of the label/package region in pixels"
    )
    ratio: float = Field(
        ..., description="text_height_px / reference_height_px"
    )
    threshold: float = Field(
        ..., description="Minimum acceptable ratio per rules"
    )
    status: FontCheckStatus


# ---------------------------------------------------------------------------
# Compliance & Tier (output of rule engine — Person 4)
# ---------------------------------------------------------------------------

class FieldCompliance(BaseModel):
    """Compliance verdict for one declaration field."""
    field: str
    status: ComplianceStatus
    reason: str = Field("", description="Human-readable explanation")


class ComplianceResult(BaseModel):
    """Full compliance output: per-field verdicts + font checks + tier."""
    compliance: List[FieldCompliance]
    font_check: List[FontCheckEntry]
    tier: Tier


# ---------------------------------------------------------------------------
# Evidence record (output of data & evidence — Person 5)
# ---------------------------------------------------------------------------

class EvidenceRecord(BaseModel):
    """Immutable evidence snapshot for one inspection."""
    image_url: str = Field(..., description="Path or URL to the original image")
    sha256_hash: str = Field(
        ..., description="SHA-256 hex digest of the original image bytes"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of evidence creation",
    )
    pdf_path: Optional[str] = Field(
        None, description="Path to the generated PDF report"
    )


# ---------------------------------------------------------------------------
# Top-level inspection result (what the API returns & frontend renders)
# ---------------------------------------------------------------------------

class InspectionResult(BaseModel):
    """The complete result of inspecting one product label.

    This is the shape returned by GET /results/{id} and rendered by the
    frontend dashboard. Every module contributes a piece:
      - Person 3 (OCR)       → declarations
      - Person 4 (Rules)     → compliance_result
      - Person 5 (Evidence)  → evidence
      - Person 2 (Backend)   → id, product_name, created_at
    """
    id: str = Field(..., description="Unique inspection ID (UUID)")
    product_name: str = Field("Unknown Product", description="Label product name")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    declarations: Declarations
    compliance_result: ComplianceResult
    evidence: EvidenceRecord
