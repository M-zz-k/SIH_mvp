"""
field_extractor.py
-------------------
Turns raw OCR TextBlocks into the structured fields required by the
Legal Metrology (Packaged Commodities) Rules, 2011 (Rules 6 & 7):

    - MRP (Maximum Retail Price)
    - Net Quantity (weight/volume/count)
    - Unit Sale Price (optional, for multi-packs)
    - Manufacturer / Packer / Importer name & address
    - Consumer care / customer care details
    - Month & Year of manufacture / import / packing
    - Best-before / expiry date (where applicable)
    - Country of origin
    - Batch / lot number

Approach: regex/pattern rules first (fast, deterministic, auditable - matches
the project's "deterministic rule engine, not AI guesswork" design goal),
with an optional spaCy NER pass to catch manufacturer names/addresses that
don't match a fixed pattern (spaCy is optional; falls back gracefully).
"""

from __future__ import annotations

import re
from typing import List, Optional

if __package__:
    from .data_contract import ExtractedField, FieldName, TextBlock
else:
    from data_contract import ExtractedField, FieldName, TextBlock

try:
    import spacy  # type: ignore

    _SPACY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SPACY_AVAILABLE = False

_nlp = None  # lazily loaded spaCy pipeline


def _get_nlp():
    global _nlp
    if _nlp is None and _SPACY_AVAILABLE:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            _nlp = False  # model not downloaded; disable NER fallback
    return _nlp or None


# ---------------------------------------------------------------------------
# Regex patterns. Kept as named, documented constants so Role 4 (rule engine)
# can audit exactly what triggers a field match -- every flag must be
# traceable to an explicit rule, per the "fully auditable, not a black box"
# requirement in the pitch.
# ---------------------------------------------------------------------------

_MRP_PATTERN = re.compile(
    r"(?:M\.?R\.?P\.?|Maximum\s+Retail\s+Price)\s*[:\-]?\s*"
    r"(?:Rs\.?|₹|INR)?\s*([0-9]+(?:[.,][0-9]{1,2})?)",
    re.IGNORECASE,
)

_UNIT_SALE_PRICE_PATTERN = re.compile(
    r"(?:Unit\s+Sale\s+Price|U\.?S\.?P\.?)\s*[:\-]?\s*"
    r"(?:Rs\.?|₹|INR)?\s*([0-9]+(?:[.,][0-9]{1,2})?)",
    re.IGNORECASE,
)

_NET_QTY_PATTERN = re.compile(
    r"(?:Net\s*(?:Qty|Quantity|Wt|Weight|Vol|Volume)\.?)\s*[:\-]?\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*(g|gm|gms|grams?|kg|ml|l|litres?|liters?|pcs?|pieces?|units?)",
    re.IGNORECASE,
)

_MFG_DATE_PATTERN = re.compile(
    r"(?:Mfg\.?\s*Date|Manufactur(?:ed|ing)\s*(?:Date|on)|Packed\s*on|Pkd\.?\s*Date|Date\s*of\s*(?:Mfg|Manufacture|Packing))"
    r"\s*[:\-]?\s*([0-3]?[0-9][/\-.][01]?[0-9][/\-.][0-9]{2,4}|[01]?[0-9][/\-.][0-9]{4}|[01]?[0-9]/[0-9]{4})",
    re.IGNORECASE,
)

_BEST_BEFORE_PATTERN = re.compile(
    r"(?:Best\s*Before|Use\s*By|Expiry|Exp\.?\s*Date)\s*[:\-]?\s*"
    r"(.+?(?:from\s+(?:Mfg|Manufacture|Packing)\.?|"
    r"[0-3]?[0-9][/\-.][01]?[0-9][/\-.][0-9]{2,4}))",
    re.IGNORECASE,
)

_CONSUMER_CARE_PATTERN = re.compile(
    r"(?:Customer\s*Care|Consumer\s*Care|For\s*(?:Complaints|Queries|Feedback))\s*[:\-]?\s*"
    r"([^\n]*(?:[0-9]{4,}[^\n]*|[\w.+-]+@[\w-]+\.[\w.-]+[^\n]*))",
    re.IGNORECASE,
)

_COUNTRY_OF_ORIGIN_PATTERN = re.compile(
    r"(?:Country\s*of\s*Origin)\s*[:\-]?\s*([A-Za-z ]+)",
    re.IGNORECASE,
)

_BATCH_PATTERN = re.compile(
    r"\b(?:Batch\s*(?:No\.?|Number)?|Lot\s*(?:No\.?|Number)?)\s*[:\-]\s*([A-Za-z0-9\-/]+)",
    re.IGNORECASE,
)

_MANUFACTURER_PATTERN = re.compile(
    r"(?:Manufactured\s*(?:by|for)|Marketed\s*by|Packed\s*by|Imported\s*by)\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)

_ADDRESS_HINT_PATTERN = re.compile(
    r"\b(?:Plot|Village|Dist\.?|District|Road|Street|Industrial\s+Area|MIDC|Pin\s*[:\-]?\s*\d{6}|\d{6})\b",
    re.IGNORECASE,
)


def _merge_blocks_into_lines(blocks: List[TextBlock], y_tolerance_ratio: float = 0.6) -> List[TextBlock]:
    """
    Real OCR (unlike a clean mock label) frequently splits ONE printed line
    into several small detection boxes -- e.g. "Customer Care:" and
    "1800-123-4567, care@brand.com" come back as two separate blocks even
    though they're the same physical line on the label. Regex patterns like
    _CONSUMER_CARE_PATTERN expect both halves in the same string, so without
    this step they silently fail to match on real-world photos.

    This groups blocks whose vertical center is close together (same
    printed row) and joins them left-to-right into one synthetic TextBlock
    per line, which is what the regex patterns are written against.
    """
    if not blocks:
        return []

    items = []
    for b in blocks:
        ys = [pt[1] for pt in b.bbox]
        xs = [pt[0] for pt in b.bbox]
        items.append((sum(ys) / len(ys), min(xs), b))
    items.sort(key=lambda t: (t[0], t[1]))

    groups: List[List[tuple]] = [[items[0]]]
    for item in items[1:]:
        y_center, _, block = item
        group_y_avg = sum(g[0] for g in groups[-1]) / len(groups[-1])
        group_height_avg = sum(g[2].line_height_px for g in groups[-1]) / len(groups[-1])
        if abs(y_center - group_y_avg) <= y_tolerance_ratio * group_height_avg:
            groups[-1].append(item)
        else:
            groups.append([item])

    merged_lines: List[TextBlock] = []
    for group in groups:
        group_sorted = sorted(group, key=lambda t: t[1])  # left-to-right reading order
        group_blocks = [g[2] for g in group_sorted]
        text = " ".join(b.text for b in group_blocks)
        all_pts = [pt for b in group_blocks for pt in b.bbox]
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        x_min, x_max, y_min, y_max = min(xs), max(xs), min(ys), max(ys)
        merged_lines.append(
            TextBlock(
                text=text,
                confidence=sum(b.confidence for b in group_blocks) / len(group_blocks),
                bbox=((x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)),
                line_height_px=max(b.line_height_px for b in group_blocks),
            )
        )
    return merged_lines


def _find_field(
    blocks: List[TextBlock],
    field: FieldName,
    pattern: re.Pattern,
    unit_group: Optional[int] = None,
    value_group: int = 1,
    method: str = "regex",
) -> ExtractedField:
    for block in blocks:
        match = pattern.search(block.text)
        if match:
            value = match.group(value_group).strip().rstrip(",;.")
            unit = match.group(unit_group).strip() if (unit_group and match.group(unit_group)) else None
            return ExtractedField(
                field=field,
                found=True,
                value=value,
                unit=unit,
                raw_text=block.text,
                confidence=block.confidence,
                bbox=block.bbox,
                line_height_px=block.line_height_px,
                extraction_method=method,
            )
    return ExtractedField(field=field, found=False, extraction_method=method)


def _extract_manufacturer_address(blocks: List[TextBlock], name_field: ExtractedField) -> ExtractedField:
    """
    Address often spans the line(s) AFTER the manufacturer name line, and/or
    is recognisable by address-shaped keywords (Plot, Dist., PIN code, etc.).
    We concatenate the manufacturer line + following address-hint lines.
    """
    if not name_field.found:
        return ExtractedField(field=FieldName.MANUFACTURER_ADDRESS, found=False, extraction_method="heuristic")

    # locate index of the manufacturer block
    idx = next((i for i, b in enumerate(blocks) if b.text == name_field.raw_text), None)
    if idx is None:
        return ExtractedField(field=FieldName.MANUFACTURER_ADDRESS, found=False, extraction_method="heuristic")

    address_parts = []
    combined_bbox = None
    combined_height = None
    combined_conf = []
    # Look at up to 2 lines AFTER the manufacturer-name line that look like
    # an address continuation (street/plot/PIN keywords). The manufacturer
    # name line itself is excluded here since it's already captured in
    # MANUFACTURER_NAME - we don't want it duplicated in the address value.
    for b in blocks[idx + 1 : idx + 3]:
        if _ADDRESS_HINT_PATTERN.search(b.text):
            address_parts.append(b.text)
            combined_conf.append(b.confidence)
            if combined_bbox is None:
                combined_bbox = b.bbox
                combined_height = b.line_height_px
        else:
            break

    if not address_parts:
        return ExtractedField(field=FieldName.MANUFACTURER_ADDRESS, found=False, extraction_method="heuristic")

    full_text = " ".join(address_parts)
    return ExtractedField(
        field=FieldName.MANUFACTURER_ADDRESS,
        found=True,
        value=full_text,
        raw_text=full_text,
        confidence=sum(combined_conf) / len(combined_conf),
        bbox=combined_bbox,
        line_height_px=combined_height,
        extraction_method="heuristic",
    )


def _refine_manufacturer_with_ner(field: ExtractedField) -> ExtractedField:
    """Optional spaCy pass: if regex captured a manufacturer line but it's long
    or noisy, try to tighten it to the ORG entity spaCy finds within it."""
    nlp = _get_nlp()
    if nlp is None or not field.found or not field.value:
        return field
    doc = nlp(field.value)
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    if orgs:
        field.value = orgs[0]
        field.extraction_method = "regex+ner"
    return field


def extract_fields(blocks: List[TextBlock]) -> List[ExtractedField]:
    """Main entry point: run every field pattern against the OCR text blocks
    and return a fully populated list of ExtractedField, matching the shared
    data contract so Role 4 (rule engine) and Role 2 (backend) can consume it
    directly.

    Internally, blocks are first merged into full printed lines (see
    `_merge_blocks_into_lines`) since real OCR frequently fragments one
    printed line into multiple small detection boxes."""

    blocks = _merge_blocks_into_lines(blocks)

    mrp = _find_field(blocks, FieldName.MRP, _MRP_PATTERN)
    unit_sale_price = _find_field(blocks, FieldName.UNIT_SALE_PRICE, _UNIT_SALE_PRICE_PATTERN)
    net_qty = _find_field(blocks, FieldName.NET_QUANTITY, _NET_QTY_PATTERN, unit_group=2)
    mfg_date = _find_field(blocks, FieldName.MFG_DATE, _MFG_DATE_PATTERN)
    best_before = _find_field(blocks, FieldName.BEST_BEFORE_DATE, _BEST_BEFORE_PATTERN)
    consumer_care = _find_field(blocks, FieldName.CONSUMER_CARE, _CONSUMER_CARE_PATTERN)
    country_of_origin = _find_field(blocks, FieldName.COUNTRY_OF_ORIGIN, _COUNTRY_OF_ORIGIN_PATTERN)
    batch = _find_field(blocks, FieldName.BATCH_NUMBER, _BATCH_PATTERN)

    manufacturer_name = _find_field(blocks, FieldName.MANUFACTURER_NAME, _MANUFACTURER_PATTERN)
    manufacturer_name = _refine_manufacturer_with_ner(manufacturer_name)
    manufacturer_address = _extract_manufacturer_address(blocks, manufacturer_name)

    return [
        mrp,
        unit_sale_price,
        net_qty,
        manufacturer_name,
        manufacturer_address,
        consumer_care,
        mfg_date,
        best_before,
        country_of_origin,
        batch,
    ]
