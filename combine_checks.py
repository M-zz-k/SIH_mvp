"""
combine_checks.py
=================
MetroScan AI -- Integration Wrapper (Person 4 Final Deliverable)
Person 4 of 6 | Hackathon MVP

PURPOSE:
    Combines the two independent compliance checks produced by Person 4 into a
    single callable for the integration teammate (Person 5 / pipeline owner).

    The two sub-checks are:

    1. RULE CHECK  (rule_engine.check_declaration)
       Presence + format + OCR confidence check.  Verifies that the extracted
       text is non-empty, matches the expected format for its field type, and
       was extracted with sufficient OCR confidence.

    2. FONT CHECK  (physical_measurement.check_declaration_font_size)
       Relative font-size heuristic.  Verifies that the declaration text is
       visually large enough on the label relative to the reference (tallest)
       text block.

    Both sub-checks return a three-tier status:
        likely_compliant | needs_review | likely_violation

    The overall status uses a "worst wins" policy -- a single failing sub-check
    is NOT hidden by the other one passing.

PUBLIC API:
    from combine_checks import check_label_declaration

    result = check_label_declaration(
        field_data   = {"field": "mrp", "text": "\u20b930.00", "confidence": 0.92},
        text_regions = [
            {"label": "reference",    "text": "BrandName",
             "bbox": {"x": 0, "y": 0, "width": 300, "height": 80}},
            {"label": "mrp",          "text": "\u20b930.00",
             "bbox": {"x": 0, "y": 0, "width": 120, "height": 24}},
        ],
    )
    # Returns a single dict -- see check_label_declaration() for exact schema.

DESIGN PRINCIPLES:
    - This module is an ORCHESTRATOR only.  No compliance logic lives here;
      all logic stays inside physical_measurement.py and rule_engine.py.
    - Both sub-checks are called independently so a crash in one never
      prevents the other from running.
    - Every failure path returns a valid dict with status="needs_review".
      This module NEVER raises an exception.

Dependencies:
    physical_measurement  (same package, no install required)
    rule_engine           (same package, no install required)
"""

from __future__ import annotations

import sys
from typing import List, Optional

from physical_measurement import check_declaration_font_size
from rule_engine import check_declaration

# Force UTF-8 output so non-ASCII field values (e.g. \u20b9) print correctly
# on Windows regardless of the active console codepage.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Tier ordering -- used by _worst_status() to compare severity
# ---------------------------------------------------------------------------
_TIER_RANK: dict[str, int] = {
    "likely_compliant": 0,
    "needs_review":     1,
    "likely_violation": 2,
}
_RANK_TIER: dict[int, str] = {v: k for k, v in _TIER_RANK.items()}

# Safe fallback status returned when a sub-check errors out unexpectedly.
_SAFE_STATUS: str = "needs_review"


def _worst_status(status_a: str, status_b: str) -> str:
    """
    Return the more severe of two tier strings.

    Severity order (ascending): likely_compliant < needs_review < likely_violation.
    Unknown tier strings are treated as needs_review.

    Parameters
    ----------
    status_a, status_b : str
        Two tier strings to compare.

    Returns
    -------
    str
        The higher-severity tier string.
    """
    rank_a = _TIER_RANK.get(status_a, _TIER_RANK[_SAFE_STATUS])
    rank_b = _TIER_RANK.get(status_b, _TIER_RANK[_SAFE_STATUS])
    return _RANK_TIER[max(rank_a, rank_b)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_label_declaration(
    field_data: dict,
    text_regions: List[dict],
) -> dict:
    """
    Run both compliance checks for one declaration and return a merged result.

    This is the single integration point for Person 4's deliverable.  Pass in
    the OCR extraction dict and all text-region bounding boxes from the label;
    receive one unified compliance dict.

    Parameters
    ----------
    field_data : dict
        OCR extraction result for the declaration, shaped as::

            {
                "field":      str,    # e.g. "mrp", "net_quantity", ...
                "text":       str,    # extracted text
                "confidence": float   # OCR confidence, 0.0 -- 1.0
            }

        Missing keys are tolerated; ``text`` defaults to ``""``,
        ``confidence`` defaults to ``0.0``.

    text_regions : list[dict]
        All annotated text regions on the label (used for both the font-size
        reference search and the target declaration lookup).  Each region::

            {
                "label": str,
                "text":  str,
                "bbox":  {"x": int, "y": int, "width": int, "height": int}
            }

        May be an empty list -- the font check will then return needs_review.

    Returns
    -------
    dict
        Unified compliance result::

            {
                "field":   str,    # declaration field name
                "value":   str,    # extracted text that was evaluated
                "rule_check": {
                    "present":      bool,
                    "format_valid": bool,
                    "status":       str    # tier string
                },
                "font_check": {
                    "ratio":  float | None,  # None if font check could not run
                    "status": str            # tier string
                },
                "overall_status": str   # worst of rule_check.status and
                                        # font_check.status
            }

    Notes
    -----
    - This function NEVER raises an exception.
    - If a sub-check fails unexpectedly, that sub-check's status is set to
      ``"needs_review"`` and a warning is printed to stderr.
    - The ``overall_status`` uses a "worst wins" policy: a single failing
      sub-check is not hidden by the other one passing.

    Examples
    --------
    >>> result = check_label_declaration(
    ...     field_data={"field": "mrp", "text": "Rs. 30", "confidence": 0.90},
    ...     text_regions=[
    ...         {"label": "reference", "text": "BrandName",
    ...          "bbox": {"x": 0, "y": 0, "width": 300, "height": 80}},
    ...         {"label": "mrp", "text": "Rs. 30",
    ...          "bbox": {"x": 0, "y": 0, "width": 120, "height": 24}},
    ...     ],
    ... )
    >>> result["overall_status"]
    'likely_compliant'
    """
    # Resolve field name and text up front for use in error fallbacks.
    field = ""
    value = ""
    try:
        field = str(field_data.get("field", "") or "")
        value = str(field_data.get("text",  "") or "")
    except Exception:
        pass

    # ------------------------------------------------------------------
    # Safe default result -- returned if something catastrophic happens
    # before we can build a proper response.
    # ------------------------------------------------------------------
    _default: dict = {
        "field": field,
        "value": value,
        "rule_check": {
            "present":      False,
            "format_valid": False,
            "status":       _SAFE_STATUS,
        },
        "font_check": {
            "ratio":  None,
            "status": _SAFE_STATUS,
        },
        "overall_status": _SAFE_STATUS,
    }

    try:
        # --------------------------------------------------------------
        # SUB-CHECK 1: Rule engine (presence + format + confidence)
        # --------------------------------------------------------------
        rule_result: dict = {}
        try:
            rule_result = check_declaration(field_data)
        except Exception as exc:
            print(
                f"[check_label_declaration] WARNING: rule check raised unexpectedly "
                f"for field='{field}': {exc}  -- using safe default.",
                file=sys.stderr,
            )
            rule_result = {
                "field":        field,
                "value":        value,
                "present":      False,
                "format_valid": False,
                "status":       _SAFE_STATUS,
            }

        rule_summary: dict = {
            "present":      rule_result.get("present",      False),
            "format_valid": rule_result.get("format_valid", False),
            "status":       rule_result.get("status",       _SAFE_STATUS),
        }

        # --------------------------------------------------------------
        # SUB-CHECK 2: Font-size heuristic
        # --------------------------------------------------------------
        font_result: dict = {}
        try:
            font_result = check_declaration_font_size(
                text_regions=text_regions,
                declaration_label=field,
            )
        except Exception as exc:
            print(
                f"[check_label_declaration] WARNING: font check raised unexpectedly "
                f"for field='{field}': {exc}  -- using safe default.",
                file=sys.stderr,
            )
            font_result = {
                "ratio":  None,
                "status": _SAFE_STATUS,
            }

        font_summary: dict = {
            "ratio":  font_result.get("ratio",  None),
            "status": font_result.get("status", _SAFE_STATUS),
        }

        # --------------------------------------------------------------
        # Overall status: worst-wins across the two sub-checks
        # --------------------------------------------------------------
        overall = _worst_status(rule_summary["status"], font_summary["status"])

        # Refresh field/value from the rule result in case it normalised them.
        field = rule_result.get("field", field) or field
        value = rule_result.get("value", value) or value

        return {
            "field":          field,
            "value":          value,
            "rule_check":     rule_summary,
            "font_check":     font_summary,
            "overall_status": overall,
        }

    except Exception as exc:
        print(
            f"[check_label_declaration] WARNING: unhandled exception for "
            f"field='{field}': {exc}  -- returning safe default.",
            file=sys.stderr,
        )
        return _default
