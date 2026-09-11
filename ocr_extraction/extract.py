"""
OCR & Data Extraction Module — Main Entry Point for METROSCAN AI
================================================================

Exposes `extract_declarations` and `extract_declarations_bulk` for downstream
consumption by the backend orchestrator and rule engine.
"""

import sys
import os
import logging
from typing import List, Dict, Any

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ocr_extraction.engine import get_ocr_engine
from ocr_extraction.extractors import (
    extract_mrp,
    extract_net_quantity,
    extract_manufacturer,
    extract_date_declaration,
)

logger = logging.getLogger("metroscan.ocr_extract")


def extract_declarations(
    image_path: str,
    engine_mode: str = "server",
    min_confidence: float = 0.6,
) -> Dict[str, Any]:
    """Runs OCR + structured extraction on a single product label image.

    Args:
        image_path: Path to the product label image.
        engine_mode: "server" (PaddleOCR pipeline) or "mobile" (ML Kit adapter).
        min_confidence: Threshold below which detections are tagged "low_confidence".

    Returns:
        A dictionary matching the shared schema's `declarations` shape,
        plus a `raw_ocr` key containing every detected text block:
        {
          "mrp": {"value": ..., "bbox": [x, y, w, h], "confidence": ..., "status": ...},
          "net_quantity": {"value": ..., "bbox": ..., "confidence": ..., "status": ...},
          "manufacturer": {"value": ..., "bbox": ..., "confidence": ..., "status": ...},
          "date_declaration": {"value": ..., "bbox": ..., "confidence": ..., "status": ...},
          "raw_ocr": [
            {"text": ..., "bbox": [x, y, w, h], "polygon": [...], "confidence": ..., "language": ...},
            ...
          ]
        }
    """
    engine = get_ocr_engine(mode=engine_mode)
    raw_blocks = engine.detect_and_recognize(image_path)

    # Perform structured pattern matching per declaration field
    mrp = extract_mrp(raw_blocks, min_confidence=min_confidence)
    net_quantity = extract_net_quantity(raw_blocks, min_confidence=min_confidence)
    manufacturer = extract_manufacturer(raw_blocks, min_confidence=min_confidence)
    date_declaration = extract_date_declaration(raw_blocks, min_confidence=min_confidence)

    return {
        "mrp": mrp,
        "net_quantity": net_quantity,
        "manufacturer": manufacturer,
        "date_declaration": date_declaration,
        "raw_ocr": raw_blocks,
    }


def extract_declarations_bulk(
    image_paths: List[str],
    engine_mode: str = "server",
    min_confidence: float = 0.6,
) -> List[Dict[str, Any]]:
    """Runs extract_declarations over a batch of images (for bulk-upload flow).

    Args:
        image_paths: List of file paths to process.
        engine_mode: "server" or "mobile".
        min_confidence: Threshold for low_confidence tagging.

    Returns:
        A list of per-image extraction result dicts in the same order as input.
        If an individual image fails, returns a result with status="extraction_failed".
    """
    results: List[Dict[str, Any]] = []

    for path in image_paths:
        try:
            res = extract_declarations(path, engine_mode=engine_mode, min_confidence=min_confidence)
            res["image_path"] = path
            results.append(res)
        except Exception as e:
            logger.error(f"Extraction failed for image '{path}': {e}")
            results.append({
                "image_path": path,
                "status": "extraction_failed",
                "error": str(e),
                "mrp": {"value": None, "bbox": None, "confidence": 0.0, "status": "not_detected"},
                "net_quantity": {"value": None, "bbox": None, "confidence": 0.0, "status": "not_detected"},
                "manufacturer": {"value": None, "bbox": None, "confidence": 0.0, "status": "not_detected"},
                "date_declaration": {"value": None, "bbox": None, "confidence": 0.0, "status": "not_detected"},
                "raw_ocr": [],
            })

    return results
