import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.db_models import User
from app.models.schemas import InspectionResult, ScanMode
from app.services.pipeline import inspection_to_result, run_full_pipeline

router = APIRouter(prefix="/scan", tags=["single-scan"])


@router.post("", response_model=InspectionResult)
def single_scan(
    file: UploadFile = File(...),
    product_name: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Guided single-image capture — physical in-store inspection mode."""
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Upload a JPEG, PNG, or WEBP image.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    dest_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    inspection = run_full_pipeline(
        db=db,
        image_path=dest_path,
        created_by=user.email,
        scan_mode=ScanMode.SINGLE,
        product_name=product_name,
    )
    return inspection_to_result(inspection)
