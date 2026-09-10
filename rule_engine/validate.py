"""
Rule Engine & Font-Heuristic Module — Person 4's workspace
===========================================================

This module takes structured declarations (from OCR extraction) and:
  1. Validates each field against the Legal Metrology Rules 2011
  2. Checks font sizes using a relative bounding-box-height heuristic
  3. Assigns a final tier: likely_compliant / needs_review / likely_violation

Input:  shared.models.Declarations
Output: shared.models.ComplianceResult

Currently returns HARDCODED MOCK DATA so the rest of the pipeline can run
end-to-end from Day 1.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.models import (
    Declarations,
    ComplianceResult,
    FieldCompliance,
    ComplianceStatus,
    FontCheckEntry,
    FontCheckStatus,
    Tier,
)


def validate(declarations: Declarations) -> ComplianceResult:
    """Validate declarations against Legal Metrology Rules and check font sizes.

    Args:
        declarations: The structured declarations object from OCR extraction.

    Returns:
        A ComplianceResult with per-field compliance, font check results,
        and the final tier.

    # TODO(Person 4 — Rule Engine Developer): Replace mock with real logic:
    #
    #   COMPLIANCE CHECKS:
    #   1. MRP: Must use '₹' symbol, must be numeric, must be present
    #   2. Net Quantity: Must have value + standard unit with space (e.g. "1 kg")
    #   3. Manufacturer: Must have name AND address (city + pincode)
    #   4. Date Declaration: Must have month+year, not just year
    #
    #   FONT SIZE HEURISTIC:
    #   1. Get bbox height of each field from declarations
    #   2. Get reference height (full label height or largest text region)
    #   3. Compute ratio = text_height_px / reference_height_px
    #   4. Compare against threshold (suggest 0.03 = 3% of label height)
    #   5. If ratio < threshold → font too small → fail
    #
    #   TIER ASSIGNMENT:
    #   - All pass + all fonts OK → likely_compliant
    #   - Any flag OR borderline font → needs_review
    #   - Any fail → likely_violation
    """

    # ---------- MOCK DATA — remove once real rules are wired up ----------
    compliance = [
        FieldCompliance(
            field="mrp",
            status=ComplianceStatus.PASS,
            reason="MRP clearly stated with ₹ symbol",
        ),
        FieldCompliance(
            field="net_quantity",
            status=ComplianceStatus.PASS,
            reason="Net quantity in standard unit (kg)",
        ),
        FieldCompliance(
            field="manufacturer",
            status=ComplianceStatus.PASS,
            reason="Full name and address present",
        ),
        FieldCompliance(
            field="date_declaration",
            status=ComplianceStatus.PASS,
            reason="Best-before date present",
        ),
    ]

    font_check = [
        FontCheckEntry(
            field="mrp",
            text_height_px=22,
            reference_height_px=500,
            ratio=0.044,
            threshold=0.03,
            status=FontCheckStatus.PASS,
        ),
        FontCheckEntry(
            field="net_quantity",
            text_height_px=20,
            reference_height_px=500,
            ratio=0.040,
            threshold=0.03,
            status=FontCheckStatus.PASS,
        ),
    ]

    return ComplianceResult(
        compliance=compliance,
        font_check=font_check,
        tier=Tier.LIKELY_COMPLIANT,
    )
