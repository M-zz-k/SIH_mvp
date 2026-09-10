"""
OCR & Extraction Module — Person 3's workspace
================================================

This module takes a product label image and extracts the four mandatory
declarations using PaddleOCR:
  - MRP (Maximum Retail Price)
  - Net Quantity
  - Manufacturer name & address
  - Date declaration (mfg/expiry/best-before)

Input:  image file path (str)
Output: shared.models.Declarations

Currently returns HARDCODED MOCK DATA so the rest of the pipeline can run
end-to-end from Day 1. Replace the mock with real PaddleOCR logic.
"""

import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.models import (
    Declarations,
    DeclarationField,
    BoundingBox,
    FieldStatus,
)


def extract_declarations(image_path: str) -> Declarations:
    """Run OCR on a product label image and return structured declarations.

    Args:
        image_path: Absolute or relative path to the label image file.

    Returns:
        A Declarations object with mrp, net_quantity, manufacturer, and
        date_declaration fields populated from OCR output.

    # TODO(Person 3 — OCR Engineer): Replace the mock below with real logic:
    #   1. Load the image with OpenCV / PIL
    #   2. Run PaddleOCR to get text + bounding boxes + confidence scores
    #   3. Classify each text region into one of the four declaration fields
    #      (hint: keyword matching on "MRP", "Net", "Mfg", "Best Before", etc.)
    #   4. Build DeclarationField objects with real values, bboxes, confidences
    #   5. Return a Declarations object
    #
    # Suggested starting point:
    #   from paddleocr import PaddleOCR
    #   ocr = PaddleOCR(use_angle_cls=True, lang='en')
    #   result = ocr.ocr(image_path, cls=True)
    """

    # ---------- MOCK DATA — remove once real OCR is wired up ----------
    return Declarations(
        mrp=DeclarationField(
            field_name="mrp",
            value="₹28.00",
            bbox=BoundingBox(x=120, y=340, w=95, h=22),
            confidence=0.96,
            status=FieldStatus.present,
        ),
        net_quantity=DeclarationField(
            field_name="net_quantity",
            value="1 kg",
            bbox=BoundingBox(x=120, y=370, w=60, h=20),
            confidence=0.98,
            status=FieldStatus.present,
        ),
        manufacturer=DeclarationField(
            field_name="manufacturer",
            value="Tata Chemicals Ltd., Mumbai 400001",
            bbox=BoundingBox(x=40, y=410, w=280, h=18),
            confidence=0.91,
            status=FieldStatus.present,
        ),
        date_declaration=DeclarationField(
            field_name="date_declaration",
            value="Best Before: Jun 2027",
            bbox=BoundingBox(x=40, y=440, w=180, h=16),
            confidence=0.89,
            status=FieldStatus.present,
        ),
    )
