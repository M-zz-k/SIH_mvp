"""
Data & Evidence Module — Person 5's workspace
===============================================

This module handles:
  1. SHA-256 hashing of original images for tamper-proof evidence
  2. PDF report generation (using ReportLab)
  3. Database schema management (PostgreSQL via SQLAlchemy)
  4. Image storage (local filesystem for MVP, S3-compatible later)

Currently returns HARDCODED MOCK DATA so the rest of the pipeline can run
end-to-end from Day 1.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.models import EvidenceRecord, InspectionResult


def hash_image(image_path: str) -> str:
    """Compute SHA-256 hash of the image file for evidence integrity.

    Args:
        image_path: Path to the image file.

    Returns:
        Hex-encoded SHA-256 digest string.

    # TODO(Person 5 — Data & Evidence Engineer): Replace mock with real logic:
    #   import hashlib
    #   with open(image_path, "rb") as f:
    #       return hashlib.sha256(f.read()).hexdigest()
    """

    # ---------- MOCK — replace with real hashing ----------
    return "a1b2c3d4e5f6789012345678abcdef0123456789abcdef0123456789abcdef01"


def generate_pdf(result: dict) -> str:
    """Generate a PDF compliance report for one inspection.

    Args:
        result: A dict matching the InspectionResult schema (or an
                InspectionResult.model_dump() output).

    Returns:
        File path to the generated PDF.

    # TODO(Person 5 — Data & Evidence Engineer): Replace mock with real logic:
    #   1. Use ReportLab to create a PDF
    #   2. Include: product name, all declarations, compliance verdicts,
    #      font check results, tier, evidence hash, timestamp
    #   3. Save to /reports/{inspection_id}.pdf
    #   4. Return the file path
    #
    # Suggested starting point:
    #   from reportlab.lib.pagesizes import A4
    #   from reportlab.pdfgen import canvas
    #   c = canvas.Canvas(pdf_path, pagesize=A4)
    #   ...
    """

    # ---------- MOCK — replace with real PDF generation ----------
    inspection_id = result.get("id", "unknown")
    mock_path = f"reports/{inspection_id}.pdf"
    return mock_path


def create_evidence_record(image_path: str, pdf_path: str) -> EvidenceRecord:
    """Create a complete evidence record for an inspection.

    Args:
        image_path: Path to the original uploaded image.
        pdf_path: Path to the generated PDF report.

    Returns:
        An EvidenceRecord object.

    # TODO(Person 5): Wire this to use real hash_image() once implemented.
    """

    return EvidenceRecord(
        image_url=image_path,
        sha256_hash=hash_image(image_path),
        timestamp=datetime.utcnow(),
        pdf_path=pdf_path,
    )


# ---------------------------------------------------------------------------
# Database helpers — Person 5 should implement these
# ---------------------------------------------------------------------------

def save_inspection(result: InspectionResult) -> str:
    """Persist an inspection result to PostgreSQL.

    # TODO(Person 5): Implement with SQLAlchemy:
    #   1. Create engine from DATABASE_URL env var
    #   2. Define ORM model matching InspectionResult
    #   3. Insert and return the ID

    Returns:
        The inspection ID.
    """
    return result.id


def get_inspection(inspection_id: str) -> dict | None:
    """Retrieve an inspection result by ID.

    # TODO(Person 5): Query from PostgreSQL and return as dict.

    Returns:
        InspectionResult as dict, or None if not found.
    """
    return None


def search_inspections(query: str = "", tier: str = "", limit: int = 50) -> list[dict]:
    """Search inspections by product name or filter by tier.

    # TODO(Person 5): Implement full-text search in PostgreSQL.

    Returns:
        List of InspectionResult dicts.
    """
    return []
