"""
INTERFACE OWNED BY: Dev5 (data & evidence engineer)

Two contracts:
  1. hash_and_store_image(image_path) -> EvidenceRecord
  2. generate_report(inspection: InspectionResult, format: str) -> ReportResponse

HOW TO INTEGRATE (Dev5, read this):
  1. Do NOT touch api/routes/*.py or main.py.
  2. Replace the body of both functions below. Keep signatures identical.
  3. hash_and_store_image should SHA-256 the raw image bytes (evidence must
     be tamper-evident — hash the original, not a re-encoded copy) and save
     an annotated copy (bounding boxes drawn) if you have one.
  4. generate_report should use ReportLab for PDF (matches the team's
     "Primary tools" list) and write to app/core/config.settings.UPLOAD_DIR
     or wherever your report output folder is; return the path.
  5. Test locally with: `python -m app.services.storage_interface`

Until you push your version, this stub computes a real SHA-256 hash (that
part doesn't need mocking) and fakes the PDF path so the API layer and
frontend can be built against it today.
"""
import hashlib
import os
from datetime import datetime, timezone

from app.core.config import settings
from app.models.schemas import EvidenceRecord, InspectionResult, ReportResponse


def hash_and_store_image(image_path: str) -> EvidenceRecord:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    with open(image_path, "rb") as f:
        file_bytes = f.read()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # ---- MOCK: real implementation should also save an annotated copy
    # with bounding boxes drawn (using data from RuleEngineResult) ----
    annotated_path = None

    return EvidenceRecord(
        image_id=os.path.basename(image_path),
        sha256_hash=sha256_hash,
        annotated_image_path=annotated_path,
        stored_at=datetime.now(timezone.utc),
    )


def generate_report(inspection: InspectionResult, format: str = "pdf") -> ReportResponse:
    # ---- MOCK: replace with real ReportLab PDF generation ----
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"report_{inspection.id}.{format}")
    with open(file_path, "w") as f:
        f.write(f"MOCK REPORT for inspection {inspection.id} — replace with real ReportLab PDF.\n")

    return ReportResponse(inspection_id=inspection.id, file_path=file_path, format=format)


if __name__ == "__main__":
    # Requires a real file at this path to test the hashing for real.
    print("Run this after placing a sample image at ./sample_label.jpg")
