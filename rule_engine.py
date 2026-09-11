"""
rule_engine.py
==============
MetroScan AI -- Declaration Rule Engine
Person 4 of 6 | Hackathon MVP

PURPOSE:
    Deterministic rule-based checks for presence and format of mandatory
    label declarations.  This module is INDEPENDENT of physical_measurement.py;
    both produce separate result dicts that a downstream integrator (another
    teammate) combines into a single compliance verdict.

DECLARATIONS COVERED:
    mrp               MRP price (₹ or Rs + numeric value)
    net_quantity      Net weight / volume (number + unit)
    manufacturer      Manufacturer name (free-text, permissive check)
    date_declaration  Best-before / expiry date or keyword

INPUT CONTRACT:
    Each function that accepts raw extraction input expects a dict shaped as::

        {
            "field":      str,          # one of the four field names above
            "text":       str,          # extracted text from OCR / extraction
            "confidence": float         # 0.0 – 1.0 OCR confidence score
        }

    This mirrors the stub format agreed with the OCR team.  Null / missing
    values are handled gracefully -- the module never raises.

OUTPUT CONTRACT (classify_declaration):
    {
        "field":        str,    # same as input field name
        "value":        str,    # the text that was evaluated
        "present":      bool,   # True if text is non-empty
        "format_valid": bool,   # True if the text matches the format regex
        "status":       str     # "likely_compliant" | "needs_review" | "likely_violation"
    }

DESIGN NOTES:
    - All regex patterns live in FIELD_PATTERNS (tunable config at module top).
    - No exception is ever raised; every edge case returns a valid dict with
      status="needs_review" as the safe default.
    - Pattern keys must match the field name strings exactly.

Dependencies:
    re  (standard library only -- no third-party packages)
"""

from __future__ import annotations

import re
import sys
from typing import Optional

# Force UTF-8 output so the rupee symbol (\u20b9) and other non-ASCII
# characters print correctly on Windows regardless of the console codepage.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Configurable regex patterns
#
# Each entry maps a field name -> compiled regex that the extracted text must
# MATCH (re.search, so the pattern can appear anywhere in the string).
#
# Tune these patterns here; do not scatter them across functions.
# ---------------------------------------------------------------------------

# Assumption: MRP must contain ₹ or Rs (case-insensitive) and at least one
# digit.  Amounts like "₹30.00", "Rs. 199", "₹1,299.00" all pass.
_MRP_PATTERN: re.Pattern = re.compile(
    r"(₹|rs\.?\s*)",
    re.IGNORECASE,
)
_MRP_NUMBER_PATTERN: re.Pattern = re.compile(
    r"\d+",
)

# Assumption: net_quantity must have a number (integer or decimal, with optional
# comma thousands separator) immediately followed (with optional whitespace) by
# a recognised unit.  Covers: g, kg, ml, l, L, oz, lb, lbs, pcs, pieces, units,
# nos, tabs, capsules, sachets, packets.
_NET_QTY_PATTERN: re.Pattern = re.compile(
    r"\d[\d,]*\.?\d*\s*"
    r"(g|kg|ml|l|oz|lb|lbs|pcs|pieces|units?|nos?|tabs?|capsules?|sachets?|packets?)",
    re.IGNORECASE,
)

# Assumption: manufacturer is a free-text name; we cannot regex-validate a
# company name precisely.  The permissive rule is: the string must contain
# at least 2 consecutive word characters that include at least one letter
# (i.e., not just digits or punctuation).  This rejects empty strings and
# strings that are pure numbers / symbols, but accepts any real business name.
_MANUFACTURER_PATTERN: re.Pattern = re.compile(
    r"[A-Za-z]{2,}",
)

# Assumption: date_declaration passes if it contains a date-like numeric
# pattern (dd/mm/yyyy, mm-yyyy, yyyy, bare month+year, etc.) OR one of the
# common label keywords.  Examples that pass:
#   "Best Before: 12/2026"   "MFG: 01-2024, EXP: 01-2025"   "Use by Dec 2025"
_DATE_PATTERN: re.Pattern = re.compile(
    r"""
    (
        # Numeric date patterns
        \d{1,2}[\/\-\.]\d{1,2}([\/\-\.]\d{2,4})?   # dd/mm/yy, dd-mm-yyyy …
        | \d{1,2}[\/\-\.]\d{2,4}                     # mm/yyyy, mm-yy
        | \d{4}                                       # bare 4-digit year
        | (jan|feb|mar|apr|may|jun|                   # month name
           jul|aug|sep|oct|nov|dec)\w*\s*\d{2,4}
        # Keyword patterns (the date text may follow on the same line)
        | best\s+before
        | use\s+by
        | expiry
        | exp\.?
        | mfg\.?
        | manufactured\s+(on|date)
        | bb\.?
        | best\s+by
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Master config dict -- used by check_format(); add new fields here.
# Each value is a list of patterns, ALL of which must match for the field
# to be considered format-valid (AND logic).  Most fields have one pattern;
# MRP has two (symbol check + digit check).
FIELD_PATTERNS: dict[str, list[re.Pattern]] = {
    "mrp":              [_MRP_PATTERN, _MRP_NUMBER_PATTERN],
    "net_quantity":     [_NET_QTY_PATTERN],
    "manufacturer":     [_MANUFACTURER_PATTERN],
    "date_declaration": [_DATE_PATTERN],
}

# Known valid field names -- used for guard-rail warnings only.
KNOWN_FIELDS: frozenset[str] = frozenset(FIELD_PATTERNS.keys())

# Default confidence threshold below which a result is routed to needs_review
# regardless of format validity.
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.6


# ---------------------------------------------------------------------------
# 1. PRESENCE CHECK
# ---------------------------------------------------------------------------

def check_presence(field_data: dict) -> bool:
    """
    Return True if the extraction result contains a non-empty text value.

    Parameters
    ----------
    field_data : dict
        Extraction dict with at least a ``"text"`` key::

            {"field": "mrp", "text": "₹30.00", "confidence": 0.92}

        Missing or null ``"text"`` values are treated as absent.

    Returns
    -------
    bool
        True  -- text is a non-empty, non-whitespace string.
        False -- text is missing, None, empty, or whitespace-only.

    Notes
    -----
    This function never raises.  Any exception from unexpected input types
    is caught and returns False (absent = safe default).
    """
    try:
        text = field_data.get("text", None)
        if text is None:
            return False
        return bool(str(text).strip())
    except Exception as exc:  # noqa: BLE001
        print(
            f"[check_presence] WARNING: unexpected input -- treating as absent. ({exc})",
            file=sys.stderr,
        )
        return False


# ---------------------------------------------------------------------------
# 2. FORMAT CHECK
# ---------------------------------------------------------------------------

def check_format(field: str, text: str) -> bool:
    """
    Return True if *text* matches all format rules for *field*.

    Rules are defined in :data:`FIELD_PATTERNS` at the top of this module --
    edit that dict to tune them without touching this function.

    Parameters
    ----------
    field : str
        One of: ``"mrp"``, ``"net_quantity"``, ``"manufacturer"``,
        ``"date_declaration"``.
    text : str
        The extracted text to validate.

    Returns
    -------
    bool
        True  -- all patterns for the field match (re.search) the text.
        False -- any pattern fails, the field is unknown, or text is empty.

    Notes
    -----
    - Uses ``re.search`` so the pattern may appear anywhere in the string.
    - An unknown ``field`` name logs a warning and returns False (safe default).
    - This function never raises.
    """
    try:
        if not text or not text.strip():
            return False

        patterns = FIELD_PATTERNS.get(field)
        if patterns is None:
            print(
                f"[check_format] WARNING: unknown field '{field}'. "
                f"Known fields: {sorted(KNOWN_FIELDS)}",
                file=sys.stderr,
            )
            return False

        # ALL patterns must match (AND logic).
        return all(pat.search(text) is not None for pat in patterns)

    except Exception as exc:  # noqa: BLE001
        print(
            f"[check_format] WARNING: unexpected error for field='{field}': {exc}",
            file=sys.stderr,
        )
        return False


# ---------------------------------------------------------------------------
# 3. COMBINED CLASSIFIER
# ---------------------------------------------------------------------------

def classify_declaration(
    field: str,
    text: str,
    confidence: float,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> dict:
    """
    Combine presence, format, and confidence into a single tiered verdict.

    Decision logic
    --------------
    ::

        not present                          → "likely_violation"
        present AND confidence < threshold   → "needs_review"
            (format is not evaluated; low confidence means the text itself
             is unreliable regardless of what it looks like)
        present AND confidence OK
            AND format invalid               → "needs_review"
        present AND confidence OK
            AND format valid                 → "likely_compliant"

    Parameters
    ----------
    field : str
        Declaration field name (``"mrp"``, ``"net_quantity"``,
        ``"manufacturer"``, ``"date_declaration"``).
    text : str
        Extracted text from OCR / extraction module.
    confidence : float
        OCR confidence score, 0.0 – 1.0.  Values outside that range are
        clamped to [0.0, 1.0] silently.
    confidence_threshold : float
        Minimum acceptable confidence; below this the result is
        ``"needs_review"``.  Default :data:`DEFAULT_CONFIDENCE_THRESHOLD`.

    Returns
    -------
    dict
        Fixed result contract::

            {
                "field":        str,   # same as input field
                "value":        str,   # the text that was evaluated
                "present":      bool,
                "format_valid": bool,
                "status":       str    # one of the three tier strings
            }

    Notes
    -----
    This function NEVER raises.  Any unexpected exception returns a
    ``"needs_review"`` dict with ``present=False`` and ``format_valid=False``.
    """
    # Safe default returned on any unrecoverable error.
    _safe_default: dict = {
        "field":        field if isinstance(field, str) else "unknown",
        "value":        text  if isinstance(text,  str) else "",
        "present":      False,
        "format_valid": False,
        "status":       "needs_review",
    }

    try:
        # Normalise inputs
        field      = str(field).strip() if field is not None else ""
        text       = str(text).strip()  if text  is not None else ""
        confidence = float(confidence)  if confidence is not None else 0.0
        confidence = max(0.0, min(1.0, confidence))  # clamp to [0, 1]

        present      = bool(text)  # equivalent to check_presence on normalised text
        format_valid = check_format(field, text) if present else False

        # Tiered decision
        if not present:
            status = "likely_violation"
        elif confidence < confidence_threshold:
            status = "needs_review"
        elif not format_valid:
            status = "needs_review"
        else:
            status = "likely_compliant"

        return {
            "field":        field,
            "value":        text,
            "present":      present,
            "format_valid": format_valid,
            "status":       status,
        }

    except Exception as exc:  # noqa: BLE001
        print(
            f"[classify_declaration] WARNING: unhandled exception for "
            f"field='{field}': {exc}  -- returning safe default.",
            file=sys.stderr,
        )
        _safe_default["field"] = field if isinstance(field, str) else "unknown"
        _safe_default["value"] = text  if isinstance(text,  str) else ""
        return _safe_default


# ---------------------------------------------------------------------------
# 4. CONVENIENCE WRAPPER  (accepts the full extraction dict)
# ---------------------------------------------------------------------------

def check_declaration(
    field_data: dict,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> dict:
    """
    Run the full presence + format + confidence pipeline from a raw extraction dict.

    This is the primary public API for teammates: pass in the extraction dict
    from the OCR / extraction module and receive a structured compliance result.

    Parameters
    ----------
    field_data : dict
        Extraction dict shaped as::

            {
                "field":      str,
                "text":       str,
                "confidence": float
            }

        Missing keys are tolerated: ``text`` defaults to ``""``,
        ``confidence`` defaults to ``0.0``.
    confidence_threshold : float
        Forwarded to :func:`classify_declaration`.

    Returns
    -------
    dict
        Same shape as :func:`classify_declaration` output.

    Notes
    -----
    This function NEVER raises.
    """
    try:
        field      = field_data.get("field",      "")
        text       = field_data.get("text",       "")
        confidence = field_data.get("confidence", 0.0)

        # Handle None values from the dict gracefully
        if field      is None: field      = ""
        if text       is None: text       = ""
        if confidence is None: confidence = 0.0

        return classify_declaration(
            field=field,
            text=text,
            confidence=float(confidence),
            confidence_threshold=confidence_threshold,
        )

    except Exception as exc:  # noqa: BLE001
        print(
            f"[check_declaration] WARNING: unhandled exception: {exc} "
            f"-- returning safe default.",
            file=sys.stderr,
        )
        return {
            "field":        field_data.get("field", "unknown") or "unknown",
            "value":        "",
            "present":      False,
            "format_valid": False,
            "status":       "needs_review",
        }
