"""
ocr_engine.py
-------------
Thin wrapper around PaddleOCR (per the tech stack: "PaddleOCR, regex/spaCy").

Responsibilities of this module ONLY:
  1. Run OCR on an image.
  2. Return a list of TextBlock (text + confidence + bbox + computed line height).

It deliberately does NOT do any field parsing (MRP, quantity, etc.) -- that is
field_extractor.py's job. Keeping OCR and parsing separate means the field
extractor can be unit-tested with plain strings, without needing PaddleOCR
installed or a GPU.

If paddleocr isn't installed (e.g. in a lightweight dev/test environment),
this module falls back to a MockOCREngine so the rest of the pipeline can
still be exercised end-to-end with sample text.
"""

from __future__ import annotations

import logging
from typing import List, Optional

if __package__:
    from .data_contract import TextBlock
else:
    from data_contract import TextBlock

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR  # type: ignore

    _PADDLE_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    _PADDLE_AVAILABLE = False


def _line_height_from_bbox(bbox) -> float:
    """bbox = 4 (x, y) points, clockwise from top-left.
    Height = average of the two vertical edges."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = bbox
    left_edge = abs(y3 - y0)
    right_edge = abs(y2 - y1)
    return (left_edge + right_edge) / 2.0


class OCREngine:
    """
    Real PaddleOCR-backed engine.

    PaddleOCR rewrote its API in v3.x (the "pipeline" architecture). This
    class supports BOTH:
      - v3.x: PaddleOCR(..., use_textline_orientation=..., device=...) and
              .predict(image) -> list of Result objects with
              res["rec_texts"] / res["rec_scores"] / res["rec_polys"]
      - v2.x (legacy): PaddleOCR(use_angle_cls=..., lang=..., use_gpu=...)
              and .ocr(image, cls=True) -> [[ [bbox, (text, conf)], ... ]]

    so this keeps working regardless of which paddleocr version someone on
    the team has installed.
    """

    def __init__(self, lang: str = "en", use_angle_cls: bool = True, use_gpu: bool = False):
        if not _PADDLE_AVAILABLE:
            raise RuntimeError(
                "paddleocr is not installed. Run `pip install paddleocr paddlepaddle` "
                "or use MockOCREngine for local development/testing."
            )
        self.lang = lang
        self._is_v3 = _paddleocr_major_version() >= 3

        if self._is_v3:
            self._ocr = PaddleOCR(
                lang=lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=use_angle_cls,
                device="gpu" if use_gpu else "cpu",
                enable_mkldnn=False,
            )
        else:  # pragma: no cover - legacy path
            self._ocr = PaddleOCR(
                use_angle_cls=use_angle_cls, lang=lang, use_gpu=use_gpu, show_log=False
            )

    def extract(self, image_path: str) -> List[TextBlock]:
        if self._is_v3:
            return self._extract_v3(image_path)
        return self._extract_v2(image_path)  # pragma: no cover - legacy path

    def _extract_v3(self, image_path: str) -> List[TextBlock]:
        blocks: List[TextBlock] = []
        for page_result in self._ocr.predict(image_path):
            texts = page_result["rec_texts"]
            scores = page_result["rec_scores"]
            polys = page_result["rec_polys"]
            for text, score, poly in zip(texts, scores, polys):
                bbox = tuple(tuple(float(c) for c in pt) for pt in poly)
                blocks.append(
                    TextBlock(
                        text=text,
                        confidence=float(score),
                        bbox=bbox,  # type: ignore
                        line_height_px=_line_height_from_bbox(bbox),
                    )
                )
        return blocks

    def _extract_v2(self, image_path: str) -> List[TextBlock]:  # pragma: no cover - legacy path
        result = self._ocr.ocr(image_path, cls=True)
        blocks: List[TextBlock] = []
        if not result or result[0] is None:
            return blocks
        for line in result[0]:
            bbox, (text, confidence) = line
            blocks.append(
                TextBlock(
                    text=text,
                    confidence=float(confidence),
                    bbox=tuple(tuple(pt) for pt in bbox),  # type: ignore
                    line_height_px=_line_height_from_bbox(bbox),
                )
            )
        return blocks


def _paddleocr_major_version() -> int:
    try:
        import paddleocr  # type: ignore

        return int(paddleocr.__version__.split(".")[0])
    except Exception:  # pragma: no cover
        return 3  # assume modern if we can't tell


class MockOCREngine:
    """
    Deterministic stand-in for PaddleOCR, used for:
      - unit tests that shouldn't need a real model / GPU
      - other roles (backend, frontend, rule engine) developing against
        this pipeline before PaddleOCR is wired up on their machines
    """

    def __init__(self, lang: str = "en"):
        self.lang = lang

    def extract(self, image_path: str) -> List[TextBlock]:
        # Returns a small, deterministic fake label so downstream code is testable.
        lines = [
            ("BRAND NAME CO.", 40.0),
            ("MRP: Rs. 199.00 (Incl. of all taxes)", 14.0),
            ("Net Qty: 250 g", 14.0),
            ("Mfg. Date: 03/2026", 12.0),
            ("Best Before: 12 months from Mfg.", 12.0),
            ("Manufactured by: Sunrise Foods Pvt. Ltd.,", 12.0),
            ("Plot 12, MIDC, Pune, Maharashtra - 411019", 12.0),
            ("Customer Care: 1800-123-4567, care@brand.com", 11.0),
            ("Country of Origin: India", 12.0),
        ]
        blocks = []
        y = 0.0
        for text, height in lines:
            bbox = ((10.0, y), (300.0, y), (300.0, y + height), (10.0, y + height))
            blocks.append(
                TextBlock(text=text, confidence=0.95, bbox=bbox, line_height_px=height)
            )
            y += height + 6
        return blocks


def get_engine(lang: str = "en", force_mock: bool = False):
    """Factory: use real PaddleOCR if available, else fall back to mock."""
    if not force_mock and _PADDLE_AVAILABLE:
        return OCREngine(lang=lang)
    if not force_mock:
        logger.warning("paddleocr not installed - falling back to MockOCREngine.")
    return MockOCREngine(lang=lang)
