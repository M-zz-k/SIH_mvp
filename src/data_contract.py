"""
data_contract.py
-----------------
This is the SHARED DATA CONTRACT for the MetroScan AI pipeline.

Role 3 (OCR & extraction engineer) PRODUCES objects of type `LabelExtractionResult`.
Role 4 (rule engine / font-heuristic dev) and Role 2 (backend/API lead) CONSUME them.

Keeping this contract stable and versioned means all three roles can build in
parallel against mock JSON before the real pipeline exists.

Every field extraction below stores not just the parsed value but also:
  - the raw OCR text it was parsed from (for audit trail / evidence)
  - a confidence score
  - the bounding box of the text on the label (needed by Role 4's relative
    font-size heuristic, and useful for UI highlighting in Role 1's frontend)
  - a `found` flag, since Rule 6/7 compliance checks care about MISSING fields
    just as much as wrong ones.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

CONTRACT_VERSION = "1.0.0"

# A bounding box is 4 (x, y) points, as returned by PaddleOCR / most OCR engines,
# going clockwise from top-left.
BBox = Tuple[
    Tuple[float, float],
    Tuple[float, float],
    Tuple[float, float],
    Tuple[float, float],
]


class FieldName(str, Enum):
    MRP = "mrp"
    NET_QUANTITY = "net_quantity"
    UNIT_SALE_PRICE = "unit_sale_price"
    MANUFACTURER_NAME = "manufacturer_name"
    MANUFACTURER_ADDRESS = "manufacturer_address"
    CONSUMER_CARE = "consumer_care"
    MFG_DATE = "mfg_date"
    COUNTRY_OF_ORIGIN = "country_of_origin"
    BEST_BEFORE_DATE = "best_before_date"
    BATCH_NUMBER = "batch_number"


class TextBlock(BaseModel):
    """One raw text detection from the OCR engine, before field parsing."""

    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BBox
    line_height_px: float  # used by Role 4's relative font-size heuristic


class ExtractedField(BaseModel):
    """One parsed, structured field (e.g. MRP) derived from one or more TextBlocks."""

    field: FieldName
    found: bool
    value: Optional[str] = None          # normalized value, e.g. "199.00"
    unit: Optional[str] = None           # e.g. "Rs", "g", "ml", "kg"
    raw_text: Optional[str] = None       # the exact OCR substring matched
    confidence: float = 0.0
    bbox: Optional[BBox] = None
    line_height_px: Optional[float] = None
    extraction_method: Optional[str] = None  # "regex" | "ner" | "heuristic"


class LabelExtractionResult(BaseModel):
    """
    Top-level object Role 3's pipeline emits for ONE scanned label/image.
    This is what gets POSTed to the backend (Role 2) and consumed by the
    rule engine (Role 4) and stored by Role 5 (data & evidence engineer).
    """

    contract_version: str = CONTRACT_VERSION
    source_image: str
    label_id: str
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    raw_text: str                         # full concatenated OCR text (for audit)
    text_blocks: List[TextBlock] = []     # every OCR detection with bbox + height
    fields: List[ExtractedField] = []     # structured, rule-engine-ready fields

    ocr_engine: str = "paddleocr"
    ocr_lang: List[str] = ["en"]
    processing_ms: Optional[float] = None
    warnings: List[str] = []              # e.g. "low confidence", "blurry image"

    def get_field(self, name: FieldName) -> Optional[ExtractedField]:
        for f in self.fields:
            if f.field == name:
                return f
        return None

    def missing_fields(self) -> List[FieldName]:
        found = {f.field for f in self.fields if f.found}
        return [f for f in FieldName if f not in found]
