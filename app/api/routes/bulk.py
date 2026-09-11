"""
Bulk mode: upload multiple listing images (or a CSV of product URLs) in one
request; each is run through the pipeline and tagged with a shared job id.

For the 2-day MVP this runs synchronously in the request (fine for demo-scale
batches, e.g. 10-30 images). If you have time left, swap the for-loop below
for a background task / Celery queue — the pipeline() call doesn't change.
"""
import logging
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.db_models import BulkJob, User
from app.models.schemas import BulkJobStatus, InspectionResult, JobStatus, ScanMode
from app.services.pipeline import inspection_to_result, run_full_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bulk", tags=["bulk"])


@router.post("", response_model=BulkJobStatus)
def bulk_upload(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    job_id = str(uuid.uuid4())
    job = BulkJob(
        job_id=job_id,
        status=JobStatus.PROCESSING.value,
        total_items=len(files),
        created_by=user.email,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    completed, failed = 0, 0
    failed_filenames: list[str] = []   # ← track which files specifically failed

    for file in files:
        try:
            dest_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
            with open(dest_path, "wb") as out:
                shutil.copyfileobj(file.file, out)

            run_full_pipeline(
                db=db,
                image_path=dest_path,
                created_by=user.email,
                scan_mode=ScanMode.BULK,
                product_name=file.filename,
                bulk_job_id=job_id,
            )
            completed += 1
        except Exception as exc:   # noqa: BLE001
            failed += 1
            failed_filenames.append(file.filename or "<unnamed>")
            # Log the real error so it's visible in server output without crashing.
            logger.exception("Bulk pipeline failed for file %r: %s", file.filename, exc)

    job.status = JobStatus.DONE.value
    job.completed_items = completed
    job.failed_items = failed
    db.commit()
    db.refresh(job)

    return BulkJobStatus(
        job_id=job.job_id,
        status=JobStatus(job.status),
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        failed_filenames=failed_filenames,
    )


@router.get("/{job_id}", response_model=BulkJobStatus)
def get_bulk_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = db.query(BulkJob).filter(BulkJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return BulkJobStatus(
        job_id=job.job_id,
        status=JobStatus(job.status),
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        # failed_filenames not persisted in DB — frontend uses POST response for that
    )


@router.get("/{job_id}/results", response_model=list[InspectionResult])
def get_bulk_job_results(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.db_models import Inspection

    rows = db.query(Inspection).filter(Inspection.bulk_job_id == job_id).all()
    return [inspection_to_result(r) for r in rows]
