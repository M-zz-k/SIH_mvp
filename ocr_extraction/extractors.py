"""
Structured Extraction Layer for METROSCAN AI
=============================================

Pattern matching rules for extracting mandatory declarations required under
India's Legal Metrology (Packaged Commodities) Rules, 2011:
  1. Maximum Retail Price (MRP)
  2. Net Quantity
  3. Manufacturer Name & Address
  4. Date Declaration (Mfg / Expiry / Best Before)
"""

import re
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# REGEX CONSTANTS FOR MANDATORY LEGAL METROLOGY DECLARATIONS
# ---------------------------------------------------------------------------

# MRP Patterns: Matches MRP, M.R.P., Rs., ₹, Incl. of all taxes, etc.
MRP_PATTERNS = [
    re.compile(
        r"(?:M\.?R\.?P\.?|MAX(?:IMUM)?\s*RETAIL\s*PRICE|PRICE)\s*:?\s*(?:RS\.?|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:RS\.?|₹)\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:/-|INCL|PER)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([0-9]+(?:\.[0-9]{2})?)\s*(?:RS|RUPEES)\b",
        re.IGNORECASE,
    ),
]

# Net Quantity Patterns: Matches Net Wt., Net Qty, Net Quantity followed by value + unit (g, kg, ml, l, mg, etc.)
NET_QTY_PATTERNS = [
    re.compile(
        r"(?:NET\s*(?:WT\.?|WEIGHT|QUANTITY|QTY\.?)|N\.?W\.?)\s*:?\s*([0-9]+(?:\.[0-9]+)?\s*(?:G|GM|GMS|KG|ML|L|LITRE|LITRES|LITER|MG))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([0-9]+(?:\.[0-9]+)?\s*(?:G|GM|GMS|KG|ML|L|LITRE|LITRES|LITER|MG))\b",
        re.IGNORECASE,
    ),
]

# Manufacturer Patterns: Matches text following "Manufactured by", "Mfd by", "Packed by", "Marketed by", "Importer"
MANUFACTURER_PATTERNS = [
    re.compile(
        r"(?:MANUFACTURED\s+BY|MFD\s+BY|PACKED\s+BY|MARKETED\s+BY|IMPORTER|MFG\s+BY|MANUFACTURER)\s*:?\s*(.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:MFD\.|MFG\.|MKTD\.)\s+BY\s*:?\s*(.+)",
        re.IGNORECASE,
    ),
]

# Date Patterns: Matches "Best Before", "Mfg Date", "Mfd", "Use By", "Exp", "Expiry", "PKD" followed by date/duration
DATE_PATTERNS = [
    re.compile(
        r"(?:BEST\s+BEFORE|MFG\s+DATE|MFD|USE\s+BY|EXP(?:IRY)?|DATE\s+OF\s+MFG|PKD|PACKED)\s*:?\s*([A-Za-z0-9\/\.\-\s]{2,25})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([0-9]{1,2}\/[0-9]{2,4}|[0-9]{1,2}\-[0-9]{2,4}|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*\s+[0-9]{4})\b",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Helper: Determine Detection Status
# ---------------------------------------------------------------------------

def _resolve_status(found: bool, confidence: float, min_confidence: float = 0.6) -> str:
    if not found:
        return "not_detected"
    if confidence < min_confidence:
        return "low_confidence"
    return "detected"


# ---------------------------------------------------------------------------
# Extractor Functions
# ---------------------------------------------------------------------------

def extract_mrp(blocks: List[Dict[str, Any]], min_confidence: float = 0.6) -> Dict[str, Any]:
    """Extract MRP (Maximum Retail Price) from OCR text blocks."""
    for block in blocks:
        text = block.get("text", "")
        confidence = float(block.get("confidence", 0.0))
        bbox = block.get("bbox")

        for pattern in MRP_PATTERNS:
            match = pattern.search(text)
            if match:
                value_str = match.group(1) if match.groups() else match.group(0)
                formatted_value = f"₹{value_str}" if not value_str.startswith("₹") else value_str
                status = _resolve_status(True, confidence, min_confidence)
                return {
                    "value": formatted_value,
                    "bbox": bbox,
                    "confidence": round(confidence, 4),
                    "status": status,
                }

    return {
        "value": None,
        "bbox": None,
        "confidence": 0.0,
        "status": "not_detected",
    }


def extract_net_quantity(blocks: List[Dict[str, Any]], min_confidence: float = 0.6) -> Dict[str, Any]:
    """Extract Net Quantity from OCR text blocks."""
    for block in blocks:
        text = block.get("text", "")
        confidence = float(block.get("confidence", 0.0))
        bbox = block.get("bbox")

        for pattern in NET_QTY_PATTERNS:
            match = pattern.search(text)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                status = _resolve_status(True, confidence, min_confidence)
                return {
                    "value": value.strip(),
                    "bbox": bbox,
                    "confidence": round(confidence, 4),
                    "status": status,
                }

    return {
        "value": None,
        "bbox": None,
        "confidence": 0.0,
        "status": "not_detected",
    }


def extract_manufacturer(blocks: List[Dict[str, Any]], min_confidence: float = 0.6) -> Dict[str, Any]:
    """Extract Manufacturer Name and Address from OCR text blocks."""
    for idx, block in enumerate(blocks):
        text = block.get("text", "")
        confidence = float(block.get("confidence", 0.0))
        bbox = block.get("bbox")

        for pattern in MANUFACTURER_PATTERNS:
            match = pattern.search(text)
            if match:
                captured = match.group(1).strip() if match.groups() else ""
                # If matched keyword but captured string is very short, append next block text if available
                if len(captured) < 5 and idx + 1 < len(blocks):
                    next_text = blocks[idx + 1].get("text", "").strip()
                    captured = f"{captured} {next_text}".strip()

                val = captured if captured else text
                status = _resolve_status(True, confidence, min_confidence)
                return {
                    "value": val,
                    "bbox": bbox,
                    "confidence": round(confidence, 4),
                    "status": status,
                }

    return {
        "value": None,
        "bbox": None,
        "confidence": 0.0,
        "status": "not_detected",
    }


def extract_date_declaration(blocks: List[Dict[str, Any]], min_confidence: float = 0.6) -> Dict[str, Any]:
    """Extract Date Declaration (Mfg Date / Expiry / Best Before) from OCR text blocks."""
    for block in blocks:
        text = block.get("text", "")
        confidence = float(block.get("confidence", 0.0))
        bbox = block.get("bbox")

        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                val = match.group(0).strip()
                status = _resolve_status(True, confidence, min_confidence)
                return {
                    "value": val,
                    "bbox": bbox,
                    "confidence": round(confidence, 4),
                    "status": status,
                }

    return {
        "value": None,
        "bbox": None,
        "confidence": 0.0,
        "status": "not_detected",
    }
