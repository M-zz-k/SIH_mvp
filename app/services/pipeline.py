"""
OWNED BY: Dev2 / Anuska (backend/API lead) — this is the orchestration glue.

Calls extraction -> rule engine -> storage in sequence and persists the
result. This is the one place that imports all three interfaces, so routes
stay thin and testable. Nobody else should need to edit this file, but if
Dev3/4/5's function signatures change, update the calls here.
"""
from sqlalchemy.orm import Session

from app.models.db_models import Inspection
from app.models.schemas import InspectionResult, ScanMode
from app.services.extraction_interface import run_extraction
from app.services.rule_engine_interface import run_rule_engine
from app.services.storage_interface import hash_and_store_image


def run_full_pipeline(
    db: Session,
    image_path: str,
    created_by: str,
    scan_mode: ScanMode = ScanMode.SINGLE,
    product_name: str | None = None,
    listing_url: str | None = None,
    bulk_job_id: str | None = None,
) -> Inspection:
    """
    Runs one image through the full compliance pipeline and saves it.
    Returns the persisted Inspection ORM row (call .id, etc. on it).
    """
    extraction = run_extraction(image_path)
    rule_result = run_rule_engine(extraction)
    evidence = hash_and_store_image(image_path)

    inspection = Inspection(
        scan_mode=scan_mode.value,
        product_name=product_name,
        listing_url=listing_url,
        image_id=extraction.image_id,
        extraction_json=extraction.model_dump(mode="json"),
        rule_result_json=rule_result.model_dump(mode="json"),
        overall_tier=rule_result.overall_tier.value,
        violation_count=len(rule_result.violations),
        sha256_hash=evidence.sha256_hash,
        annotated_image_path=evidence.annotated_image_path,
        created_by=created_by,
        bulk_job_id=bulk_job_id,
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


def inspection_to_result(inspection: Inspection) -> InspectionResult:
    """Convert a DB row back into the API response schema."""
    from app.models.schemas import ExtractionResult, RuleEngineResult, EvidenceRecord

    return InspectionResult(
        id=inspection.id,
        scan_mode=ScanMode(inspection.scan_mode),
        product_name=inspection.product_name,
        listing_url=inspection.listing_url,
        created_at=inspection.created_at,
        created_by=inspection.created_by,
        extraction=ExtractionResult(**inspection.extraction_json),
        rule_result=RuleEngineResult(**inspection.rule_result_json),
        evidence=EvidenceRecord(
            image_id=inspection.image_id,
            sha256_hash=inspection.sha256_hash,
            annotated_image_path=inspection.annotated_image_path,
            stored_at=inspection.created_at,
        ) if inspection.sha256_hash else None,
        overall_tier=inspection.overall_tier.value if hasattr(inspection.overall_tier, "value") else inspection.overall_tier,
    )
