"""
pipeline.py
-----------
Orchestrates: image -> OCR -> field extraction -> LabelExtractionResult
(the shared data contract object).

This is the single function the backend/API lead (Role 2) needs to call
to wire this module into the FastAPI endpoints:

    from pipeline import process_label_image
    result = process_label_image("path/to/label.jpg")
    backend_db.save(result.dict())
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import List, Optional

if __package__:
    from .data_contract import LabelExtractionResult
    from .field_extractor import extract_fields
    from .ocr_engine import get_engine
else:
    from data_contract import LabelExtractionResult
    from field_extractor import extract_fields
    from ocr_engine import get_engine

MIN_CONFIDENCE_WARNING_THRESHOLD = 0.6


def process_label_image(
    image_path: str,
    lang: str = "en",
    force_mock: bool = False,
    label_id: Optional[str] = None,
) -> LabelExtractionResult:
    """Run the full OCR + extraction pipeline on a single label image."""
    start = time.perf_counter()

    engine = get_engine(lang=lang, force_mock=force_mock)
    blocks = engine.extract(image_path)

    fields = extract_fields(blocks)

    warnings: List[str] = []
    if not blocks:
        warnings.append("No text detected - image may be blank, blurry, or unreadable.")
    low_conf_blocks = [b for b in blocks if b.confidence < MIN_CONFIDENCE_WARNING_THRESHOLD]
    if low_conf_blocks:
        warnings.append(
            f"{len(low_conf_blocks)} text block(s) had low OCR confidence "
            f"(< {MIN_CONFIDENCE_WARNING_THRESHOLD}); route to human review."
        )

    result = LabelExtractionResult(
        source_image=str(image_path),
        label_id=label_id or str(uuid.uuid4()),
        raw_text="\n".join(b.text for b in blocks),
        text_blocks=blocks,
        fields=fields,
        ocr_engine="mock" if (force_mock or engine.__class__.__name__ == "MockOCREngine") else "paddleocr",
        ocr_lang=[lang],
        processing_ms=(time.perf_counter() - start) * 1000,
        warnings=warnings,
    )
    return result


def process_batch(
    image_paths: List[str],
    lang: str = "en",
    force_mock: bool = False,
) -> List[LabelExtractionResult]:
    """Bulk mode: process a list of images (e.g. from a CSV of e-commerce
    listing image URLs already downloaded to disk by the backend)."""
    return [process_label_image(p, lang=lang, force_mock=force_mock) for p in image_paths]
