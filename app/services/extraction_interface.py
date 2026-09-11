"""
INTERFACE OWNED BY: Dev3 (OCR & extraction engineer)

Contract: run_extraction(image_path) -> ExtractionResult (see models/schemas.py)

HOW TO INTEGRATE (Dev3, read this):
  1. Do NOT touch api/routes/*.py or main.py.
  2. Replace the body of `run_extraction` below with your real PaddleOCR +
     regex/spaCy pipeline. Keep the function name and signature identical.
  3. Your return value MUST be an ExtractionResult. If a field can't be
     found, still include it in `fields` with parsed_value=None and low
     confidence — don't omit it, the rule engine expects every field key
     to be present.
  4. Test locally with: `python -m app.services.extraction_interface`
     (see the __main__ block at the bottom).

Until you push your version, this stub returns realistic mock data so the
rest of the pipeline (rule engine -> storage -> dashboard) is testable and
demoable end-to-end today.
"""
import uuid

from app.models.schemas import BoundingBox, ExtractedField, ExtractionResult

REQUIRED_FIELDS = [
    "manufacturer_packer_importer",
    "net_quantity",
    "mrp",
    "date_of_manufacture_packing",
    "consumer_care",
    "country_of_origin",
]


def run_extraction(image_path: str) -> ExtractionResult:
    """
    Real implementation (Dev3) should:
      1. Run PaddleOCR on image_path -> raw text + word-level bounding boxes.
      2. Parse raw text into the REQUIRED_FIELDS above using regex/spaCy.
      3. Return one ExtractedField per required field (never skip one).
      4. Also return `largest_text_bbox` — the bounding box of the largest
         text block on the label (used by Dev4's font-size heuristic).
    """
    # ---- MOCK IMPLEMENTATION (remove when real OCR is wired in) ----
    image_id = str(uuid.uuid4())
    mock_values = {
        "manufacturer_packer_importer": ("Acme Foods Pvt Ltd, Pune, MH", 0.91),
        "net_quantity": ("500 g", 0.95),
        "mrp": ("Rs. 199.00 (incl. of all taxes)", 0.88),
        "date_of_manufacture_packing": ("08/2026", 0.72),
        "consumer_care": ("care@acmefoods.example, 1800-000-0000", 0.65),
        "country_of_origin": ("India", 0.93),
    }
    fields = [
        ExtractedField(
            field_name=name,
            raw_text=value,
            parsed_value=value,
            confidence=conf,
            bounding_box=BoundingBox(x=20, y=40 + i * 30, width=220, height=18),
        )
        for i, (name, (value, conf)) in enumerate(mock_values.items())
    ]

    return ExtractionResult(
        image_id=image_id,
        ocr_engine="mock",
        fields=fields,
        largest_text_bbox=BoundingBox(x=20, y=10, width=180, height=40),
        raw_ocr_text=" | ".join(v for v, _ in mock_values.values()),
    )


if __name__ == "__main__":
    # Quick standalone smoke test — run with: python -m app.services.extraction_interface
    result = run_extraction("sample_label.jpg")
    print(result.model_dump_json(indent=2))
