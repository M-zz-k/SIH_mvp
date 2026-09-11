"""
SQLAlchemy ORM models — how data is actually stored.
Kept deliberately separate from schemas.py (the API/service contract) so
Dev5 can evolve the storage schema (e.g. swap SQLite -> Postgres, add
indexes) without breaking anyone importing from schemas.py.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum, JSON, Text
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class UserRoleDB(str, enum.Enum):
    inspector = "inspector"
    supervisor = "supervisor"
    admin = "admin"


class VerdictTierDB(str, enum.Enum):
    likely_compliant = "likely_compliant"
    needs_officer_review = "needs_officer_review"
    likely_violation = "likely_violation"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRoleDB), default=UserRoleDB.inspector, nullable=False)
    created_at = Column(DateTime, default=utcnow)


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    scan_mode = Column(String, nullable=False)  # "single_scan" | "bulk"
    product_name = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    listing_url = Column(String, nullable=True)
    image_id = Column(String, nullable=False)

    # Full JSON blobs of the module outputs — fast to ship for a 2-day MVP,
    # queryable columns (brand, overall_tier) are duplicated above/below
    # for search/filter without needing to parse JSON in SQL.
    extraction_json = Column(JSON, nullable=True)
    rule_result_json = Column(JSON, nullable=True)

    overall_tier = Column(SAEnum(VerdictTierDB), nullable=False, default=VerdictTierDB.needs_officer_review)
    violation_count = Column(Integer, default=0)

    sha256_hash = Column(String, nullable=True)
    annotated_image_path = Column(String, nullable=True)
    report_pdf_path = Column(String, nullable=True)

    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    bulk_job_id = Column(String, nullable=True, index=True)


class BulkJob(Base):
    __tablename__ = "bulk_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="queued")  # queued | processing | done | failed
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)
