"""
models.py
The schema. Everything hangs off Inspection by inspection_id.

User ──< Inspection ──< EvidenceImage
                    ──< ExtractedField
                    ──< RuleViolation
                    ──< Report

Import table classes directly wherever you need them:
    from models import Inspection, EvidenceImage
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    INSPECTOR = "inspector"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class InputMode(str, Enum):
    BULK = "bulk"          # bulk e-commerce listing upload / CSV
    SINGLE = "single"       # guided single-label mobile scan


class InspectionStatus(str, Enum):
    PENDING = "pending"         # queued, not processed yet
    PROCESSING = "processing"   # OCR/rule engine running
    NEEDS_REVIEW = "needs_review"
    AUTO_CLEARED = "auto_cleared"
    CONFIRMED_VIOLATION = "confirmed_violation"
    DISMISSED = "dismissed"


class ViolationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ViolationStatus(str, Enum):
    AUTO_CLEAR = "auto_clear"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"   # officer reviewed and disagreed with the flag


class ReportType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.INSPECTOR)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    inspections: List["Inspection"] = Relationship(back_populates="user")


class Inspection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    input_mode: InputMode
    status: InspectionStatus = Field(default=InspectionStatus.PENDING)

    # For bulk mode this is the listing URL; for single mode it can be
    # a short label like "mobile-capture" or a store name.
    source: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="inspections")
    evidence_images: List["EvidenceImage"] = Relationship(back_populates="inspection")
    extracted_fields: List["ExtractedField"] = Relationship(back_populates="inspection")
    rule_violations: List["RuleViolation"] = Relationship(back_populates="inspection")
    reports: List["Report"] = Relationship(back_populates="inspection")


class EvidenceImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    inspection_id: int = Field(foreign_key="inspection.id", index=True)

    original_filename: str
    file_path: str          # storage key/path inside the bucket, NOT a local path
    file_hash: str = Field(index=True)   # SHA-256 hex digest, the "tamper-proof seal"
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None

    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    inspection: Optional[Inspection] = Relationship(back_populates="evidence_images")


class ExtractedField(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    inspection_id: int = Field(foreign_key="inspection.id", index=True)

    # e.g. "mrp", "net_quantity", "manufacturer_name", "mfg_date", "consumer_care"
    field_name: str
    field_value: Optional[str] = None
    confidence: Optional[float] = None   # 0.0 - 1.0, from OCR

    # JSON-encoded [x, y, w, h] or polygon points on the source image,
    # stored as text so this file has no extra JSON-column dependency.
    bounding_box: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    inspection: Optional[Inspection] = Relationship(back_populates="extracted_fields")


class RuleViolation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    inspection_id: int = Field(foreign_key="inspection.id", index=True)

    rule_code: str          # e.g. "LM-PCR-2011-R6" — versioned, citable rule id
    rule_description: str
    severity: ViolationSeverity = Field(default=ViolationSeverity.MEDIUM)
    status: ViolationStatus = Field(default=ViolationStatus.NEEDS_REVIEW)

    detected_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    reviewed_at: Optional[datetime] = None
    reviewer_note: Optional[str] = None

    inspection: Optional[Inspection] = Relationship(back_populates="rule_violations")


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    inspection_id: int = Field(foreign_key="inspection.id", index=True)

    report_type: ReportType
    file_path: str          # storage key/path to the generated PDF/DOCX
    evidence_hash: str      # SHA-256 of the generated report file itself

    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    inspection: Optional[Inspection] = Relationship(back_populates="reports")
