from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.db_models import Inspection, User
from app.models.schemas import InspectionResult, InspectionSummary, VerdictTier
from app.services.pipeline import inspection_to_result

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=list[InspectionSummary])
def search_results(
    q: str | None = Query(None, description="Search product name/brand"),
    tier: VerdictTier | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Searchable repository — filter by product, brand, date, violation type."""
    query = db.query(Inspection)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Inspection.product_name.ilike(like)) | (Inspection.brand.ilike(like))
        )
    if tier:
        query = query.filter(Inspection.overall_tier == tier.value)
    if date_from:
        query = query.filter(Inspection.created_at >= date_from)
    if date_to:
        query = query.filter(Inspection.created_at <= date_to)

    rows = query.order_by(Inspection.created_at.desc()).limit(200).all()
    return [
        InspectionSummary(
            id=r.id,
            product_name=r.product_name,
            brand=r.brand,
            created_at=r.created_at,
            overall_tier=r.overall_tier.value if hasattr(r.overall_tier, "value") else r.overall_tier,
            violation_count=r.violation_count or 0,
        )
        for r in rows
    ]


@router.get("/{inspection_id}", response_model=InspectionResult)
def get_result(inspection_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection_to_result(inspection)


@router.post("/{inspection_id}/report")
def generate_report(
    inspection_id: int,
    format: str = "pdf",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.storage_interface import generate_report as generate_report_file

    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    result = inspection_to_result(inspection)
    report = generate_report_file(result, format=format)
    return report
