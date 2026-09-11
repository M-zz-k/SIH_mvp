from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.db_models import Inspection, User
from app.models.schemas import DashboardStats, UserRole

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    # Only supervisors/admins see aggregate stats — inspectors just see their own scans via /results
    user: User = Depends(require_role(UserRole.SUPERVISOR, UserRole.ADMIN)),
):
    rows = db.query(Inspection).all()

    tier_counts = Counter(r.overall_tier.value if hasattr(r.overall_tier, "value") else r.overall_tier for r in rows)

    violation_type_counter = Counter()
    for r in rows:
        if r.rule_result_json:
            for v in r.rule_result_json.get("violations", []):
                violation_type_counter[v.get("rule_id", "unknown")] += 1

    top_violations = [
        {"rule_id": rule_id, "count": count}
        for rule_id, count in violation_type_counter.most_common(10)
    ]

    return DashboardStats(
        total_scans=len(rows),
        likely_compliant=tier_counts.get("likely_compliant", 0),
        needs_review=tier_counts.get("needs_officer_review", 0),
        likely_violation=tier_counts.get("likely_violation", 0),
        top_violation_types=top_violations,
    )
