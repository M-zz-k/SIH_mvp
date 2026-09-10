"""
OCR Extraction Module Test Suite
=================================

Comprehensive test suite verifying:
  1. OpenCV Preprocessing & Deskew Angle Calculation
  2. Engine Architecture (PaddleOCREngine, MLKitResultAdapter, get_ocr_engine factory)
  3. ML Kit Payload Normalization
  4. Regex Extractor Rules (MRP, Net Qty, Manufacturer, Date)
  5. Single Image Extraction (extract_declarations)
  6. Bulk Batch Processing & Error Resilience (extract_declarations_bulk)
"""

import sys
import os
import json
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ocr_extraction.preprocess import preprocess_image, calculate_deskew_angle
from ocr_extraction.engine import (
    get_ocr_engine,
    PaddleOCREngine,
    MLKitResultAdapter,
    normalize_mlkit_payload,
    calculate_iou,
    deduplicate_text_blocks,
)
from ocr_extraction.extractors import (
    extract_mrp,
    extract_net_quantity,
    extract_manufacturer,
    extract_date_declaration,
)
from ocr_extraction.extract import extract_declarations, extract_declarations_bulk
from ocr_extraction.tests.generate_test_images import generate_all_test_images


class TestOCRExtractionModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(__file__)
        cls.images_dir = os.path.join(cls.test_dir, "images")
        cls.test_image_paths = generate_all_test_images(cls.images_dir)
        cls.mlkit_json_path = os.path.join(cls.test_dir, "sample_mlkit_payload.json")

    def test_01_preprocessing_and_deskew(self):
        """Test OpenCV preprocessing, CLAHE, and deskew angle calculation."""
        for img_path in self.test_image_paths:
            processed_img, angle = preprocess_image(img_path, enable_deskew=True)
            self.assertIsNotNone(processed_img)
            self.assertEqual(len(processed_img.shape), 3)  # 3-channel BGR
            self.assertIsInstance(angle, float)

    def test_02_iou_and_deduplication(self):
        """Test bounding box IoU computation and text block deduplication."""
        box1 = [50, 50, 100, 40]
        box2 = [60, 55, 95, 38]  # High overlap
        box3 = [300, 300, 100, 40]  # No overlap

        iou_12 = calculate_iou(box1, box2)
        iou_13 = calculate_iou(box1, box3)

        self.assertGreater(iou_12, 0.6)
        self.assertEqual(iou_13, 0.0)

        blocks = [
            {"text": "MRP Rs 100", "bbox": box1, "confidence": 0.95},
            {"text": "MRP Rs 100", "bbox": box2, "confidence": 0.80},
            {"text": "Net Qty 1kg", "bbox": box3, "confidence": 0.90},
        ]
        deduped = deduplicate_text_blocks(blocks, iou_threshold=0.5)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["confidence"], 0.95)

    def test_03_mlkit_adapter_and_normalization(self):
        """Test normalizing Google ML Kit JSON payload."""
        with open(self.mlkit_json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        blocks = normalize_mlkit_payload(payload)
        self.assertEqual(len(blocks), 4)
        for b in blocks:
            self.assertIn("text", b)
            self.assertIn("bbox", b)
            self.assertEqual(len(b["bbox"]), 4)  # [x, y, w, h]
            self.assertIn("confidence", b)
            self.assertIn("language", b)

        # Test MLKitResultAdapter via factory
        adapter = get_ocr_engine("mobile", raw_payload=payload)
        res_blocks = adapter.detect_and_recognize("dummy_path")
        self.assertEqual(len(res_blocks), 4)

    def test_04_ocr_engine_factory(self):
        """Test factory function get_ocr_engine for server and mobile modes."""
        server_engine = get_ocr_engine("server")
        self.assertIsInstance(server_engine, PaddleOCREngine)

        mobile_engine = get_ocr_engine("mobile", raw_payload={"blocks": []})
        self.assertIsInstance(mobile_engine, MLKitResultAdapter)

        with self.assertRaises(ValueError):
            get_ocr_engine("invalid_mode")

    def test_05_structured_extractors(self):
        """Test regex extraction rules for mandatory fields."""
        sample_blocks = [
            {"text": "M.R.P.: Rs 150.00 (Incl. of all taxes)", "bbox": [40, 100, 320, 28], "confidence": 0.95},
            {"text": "Net Quantity: 500 g", "bbox": [40, 140, 180, 24], "confidence": 0.96},
            {"text": "Manufactured by: Tata Chemicals Ltd, Mumbai 400001", "bbox": [40, 180, 420, 30], "confidence": 0.91},
            {"text": "Best Before 12 Months from Mfg", "bbox": [40, 220, 260, 24], "confidence": 0.88},
        ]

        mrp_res = extract_mrp(sample_blocks)
        self.assertEqual(mrp_res["status"], "detected")
        self.assertIn("150.00", mrp_res["value"])

        qty_res = extract_net_quantity(sample_blocks)
        self.assertEqual(qty_res["status"], "detected")
        self.assertEqual(qty_res["value"], "500 g")

        mfg_res = extract_manufacturer(sample_blocks)
        self.assertEqual(mfg_res["status"], "detected")
        self.assertIn("Tata Chemicals", mfg_res["value"])

        date_res = extract_date_declaration(sample_blocks)
        self.assertEqual(date_res["status"], "detected")
        self.assertIn("Best Before 12 Months", date_res["value"])

    def test_06_low_confidence_handling(self):
        """Test low confidence flagging below threshold."""
        low_conf_blocks = [
            {"text": "MRP ₹50.00", "bbox": [10, 10, 50, 20], "confidence": 0.45},
        ]
        mrp_res = extract_mrp(low_conf_blocks, min_confidence=0.6)
        self.assertEqual(mrp_res["status"], "low_confidence")
        self.assertEqual(mrp_res["confidence"], 0.45)

    def test_07_extract_declarations_single(self):
        """Test single image extract_declarations pipeline."""
        img_path = self.test_image_paths[0]  # Compliant label
        result = extract_declarations(img_path, engine_mode="server")

        self.assertIn("mrp", result)
        self.assertIn("net_quantity", result)
        self.assertIn("manufacturer", result)
        self.assertIn("date_declaration", result)
        self.assertIn("raw_ocr", result)
        self.assertIsInstance(result["raw_ocr"], list)

    def test_08_extract_declarations_bulk_and_resilience(self):
        """Test bulk batch processing with error resilience for invalid images."""
        batch_input = [
            self.test_image_paths[0],
            self.test_image_paths[1],
            "non_existent_invalid_image.jpg",  # Should trigger extraction_failed
        ]

        results = extract_declarations_bulk(batch_input, engine_mode="server")
        self.assertEqual(len(results), 3)

        # First two should succeed
        self.assertIn(results[0]["mrp"]["status"], ["detected", "low_confidence"])
        self.assertIn(results[1]["mrp"]["status"], ["detected", "low_confidence"])

        # Third should have failed status gracefully
        self.assertEqual(results[2]["status"], "extraction_failed")
        self.assertIn("error", results[2])


if __name__ == "__main__":
    unittest.main()
