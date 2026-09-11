"""
test_combine_checks.py
======================
MetroScan AI -- Integration Wrapper Test Script
Person 4 of 6 | Hackathon MVP

PURPOSE:
    Verifies that combine_checks.check_label_declaration() correctly merges
    rule_engine and physical_measurement results under all key scenarios:

        1. Both sub-checks pass       -> overall likely_compliant
        2. Rule check fails            -> overall degrades to its tier
        3. Font check fails            -> overall degrades to its tier
        4. Both sub-checks fail        -> overall likely_violation
        5. Missing / malformed input   -> overall needs_review, no crash

    Run with:
        python -X utf8 test_combine_checks.py
        python -X utf8 test_combine_checks.py --verbose

    Exit code 0 = all tests passed.
    Exit code 1 = one or more failures.
"""

from __future__ import annotations

import argparse
import sys

from combine_checks import check_label_declaration, _worst_status

# Force UTF-8 output for non-ASCII characters on Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

# A label that has a tall reference element and a reasonably-sized MRP box.
# ratio = 24 / 80 = 0.30 -- well above the 0.15 compliant threshold.
_REGIONS_MRP_OK: list = [
    {
        "label": "reference",
        "text":  "BrandName",
        "bbox":  {"x": 0, "y": 0, "width": 300, "height": 80},
    },
    {
        "label": "mrp",
        "text":  "\u20b930.00",
        "bbox":  {"x": 0, "y": 100, "width": 120, "height": 24},
    },
]

# MRP box is tiny relative to reference: ratio = 5 / 80 = 0.0625 < 0.09
# -> font check = likely_violation
_REGIONS_MRP_TINY: list = [
    {
        "label": "reference",
        "text":  "BrandName",
        "bbox":  {"x": 0, "y": 0, "width": 300, "height": 80},
    },
    {
        "label": "mrp",
        "text":  "\u20b930.00",
        "bbox":  {"x": 0, "y": 100, "width": 120, "height": 5},
    },
]

# MRP box is borderline: ratio = 11 / 80 = 0.1375 -- inside review band
# (0.09 <= ratio < 0.15) -> font check = needs_review
_REGIONS_MRP_BORDERLINE: list = [
    {
        "label": "reference",
        "text":  "BrandName",
        "bbox":  {"x": 0, "y": 0, "width": 300, "height": 80},
    },
    {
        "label": "mrp",
        "text":  "\u20b930.00",
        "bbox":  {"x": 0, "y": 100, "width": 120, "height": 11},
    },
]

# No mrp region present in the list -> font check can't find the declaration
_REGIONS_NO_MRP: list = [
    {
        "label": "reference",
        "text":  "BrandName",
        "bbox":  {"x": 0, "y": 0, "width": 300, "height": 80},
    },
]

# Completely empty list of regions
_REGIONS_EMPTY: list = []


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_CASES: list[dict] = [

    # =========================================================================
    # SCENARIO 1: Both sub-checks pass -> overall likely_compliant
    # =========================================================================
    {
        "name": "both pass -- valid MRP text + font large enough",
        "field_data":    {"field": "mrp", "text": "\u20b930.00", "confidence": 0.92},
        "text_regions":  _REGIONS_MRP_OK,
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "likely_compliant",
    },
    {
        "name": "both pass -- valid net_quantity text + font large enough",
        "field_data":   {"field": "net_quantity", "text": "38.5 g", "confidence": 0.88},
        "text_regions": [
            {"label": "reference",    "text": "Brand",
             "bbox": {"x": 0, "y": 0, "width": 300, "height": 80}},
            {"label": "net_quantity", "text": "38.5 g",
             "bbox": {"x": 0, "y": 150, "width": 100, "height": 22}},
        ],
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "likely_compliant",
    },

    # =========================================================================
    # SCENARIO 2: Rule check fails, font check passes -> overall degrades
    # =========================================================================
    {
        "name": "rule fails (missing text) + font OK -> overall likely_violation",
        "field_data":   {"field": "mrp", "text": "", "confidence": 0.92},
        "text_regions": _REGIONS_MRP_OK,
        "expect_rule_status": "likely_violation",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "likely_violation",
    },
    {
        "name": "rule fails (no currency symbol) + font OK -> overall needs_review",
        "field_data":   {"field": "mrp", "text": "30.00", "confidence": 0.90},
        "text_regions": _REGIONS_MRP_OK,
        "expect_rule_status": "needs_review",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "needs_review",
    },
    {
        "name": "rule fails (low confidence) + font OK -> overall needs_review",
        "field_data":   {"field": "mrp", "text": "\u20b930.00", "confidence": 0.35},
        "text_regions": _REGIONS_MRP_OK,
        "expect_rule_status": "needs_review",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "needs_review",
    },

    # =========================================================================
    # SCENARIO 3: Font check fails, rule check passes -> overall degrades
    # =========================================================================
    {
        "name": "font fails (text too small) + rule OK -> overall likely_violation",
        "field_data":   {"field": "mrp", "text": "\u20b930.00", "confidence": 0.92},
        "text_regions": _REGIONS_MRP_TINY,
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "likely_violation",
        "expect_overall":     "likely_violation",
    },
    {
        "name": "font borderline (needs_review) + rule OK -> overall needs_review",
        "field_data":   {"field": "mrp", "text": "\u20b930.00", "confidence": 0.92},
        "text_regions": _REGIONS_MRP_BORDERLINE,
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "needs_review",
        "expect_overall":     "needs_review",
    },
    {
        "name": "font fails (label not in regions) + rule OK -> overall needs_review",
        "field_data":   {"field": "mrp", "text": "\u20b930.00", "confidence": 0.92},
        "text_regions": _REGIONS_NO_MRP,
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "needs_review",
        "expect_overall":     "needs_review",
    },

    # =========================================================================
    # SCENARIO 4: Both sub-checks fail -> overall likely_violation
    # =========================================================================
    {
        "name": "both fail -- missing text + tiny font -> overall likely_violation",
        "field_data":   {"field": "mrp", "text": "", "confidence": 0.92},
        "text_regions": _REGIONS_MRP_TINY,
        "expect_rule_status": "likely_violation",
        "expect_font_status": "likely_violation",
        "expect_overall":     "likely_violation",
    },
    {
        "name": "both fail -- bad format + tiny font -> overall likely_violation",
        "field_data":   {"field": "mrp", "text": "thirty rupees", "confidence": 0.90},
        "text_regions": _REGIONS_MRP_TINY,
        "expect_rule_status": "needs_review",
        "expect_font_status": "likely_violation",
        "expect_overall":     "likely_violation",
    },

    # =========================================================================
    # SCENARIO 5: Missing / malformed inputs -> needs_review, no crash
    # =========================================================================
    {
        "name": "empty field_data dict -> needs_review, no crash",
        "field_data":   {},
        "text_regions": _REGIONS_MRP_OK,
        "expect_rule_status": "likely_violation",  # empty text -> absent
        "expect_font_status": "needs_review",       # empty field name -> not found
        "expect_overall":     "likely_violation",
    },
    {
        "name": "null text in field_data -> rule sees absent",
        "field_data":   {"field": "mrp", "text": None, "confidence": 0.90},
        "text_regions": _REGIONS_MRP_OK,
        "expect_rule_status": "likely_violation",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "likely_violation",
    },
    {
        "name": "empty text_regions list -> font check needs_review",
        "field_data":   {"field": "mrp", "text": "\u20b930.00", "confidence": 0.92},
        "text_regions": _REGIONS_EMPTY,
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "needs_review",
        "expect_overall":     "needs_review",
    },
    {
        "name": "null confidence -> treated as 0.0 -> rule needs_review",
        "field_data":   {"field": "mrp", "text": "\u20b930.00", "confidence": None},
        "text_regions": _REGIONS_MRP_OK,
        "expect_rule_status": "needs_review",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "needs_review",
    },
    {
        "name": "other fields work -- manufacturer both pass",
        "field_data":   {
            "field": "manufacturer", "text": "ABC Foods Pvt. Ltd.", "confidence": 0.88
        },
        "text_regions": [
            {"label": "reference",    "text": "Brand",
             "bbox": {"x": 0, "y": 0, "width": 300, "height": 80}},
            {"label": "manufacturer", "text": "ABC Foods Pvt. Ltd.",
             "bbox": {"x": 0, "y": 200, "width": 200, "height": 18}},
        ],
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "likely_compliant",
    },
    {
        "name": "date_declaration -- valid format + font OK",
        "field_data":   {
            "field": "date_declaration", "text": "Best Before: 12/2026", "confidence": 0.91
        },
        "text_regions": [
            {"label": "reference",        "text": "Brand",
             "bbox": {"x": 0, "y": 0, "width": 300, "height": 80}},
            {"label": "date_declaration", "text": "Best Before: 12/2026",
             "bbox": {"x": 0, "y": 200, "width": 200, "height": 16}},
        ],
        "expect_rule_status": "likely_compliant",
        "expect_font_status": "likely_compliant",
        "expect_overall":     "likely_compliant",
    },
]


# ---------------------------------------------------------------------------
# _worst_status unit checks
# ---------------------------------------------------------------------------

def _run_worst_status_checks(verbose: bool = False) -> int:
    """
    Sanity-check the _worst_status() helper used for overall_status logic.

    Returns
    -------
    int
        Number of failures.
    """
    cases = [
        ("likely_compliant", "likely_compliant", "likely_compliant"),
        ("likely_compliant", "needs_review",     "needs_review"),
        ("likely_compliant", "likely_violation",  "likely_violation"),
        ("needs_review",     "likely_compliant", "needs_review"),
        ("needs_review",     "needs_review",     "needs_review"),
        ("needs_review",     "likely_violation",  "likely_violation"),
        ("likely_violation",  "likely_compliant", "likely_violation"),
        ("likely_violation",  "needs_review",     "likely_violation"),
        ("likely_violation",  "likely_violation",  "likely_violation"),
        # Symmetric
        ("needs_review",     "likely_compliant", "needs_review"),
    ]
    failures = 0
    for a, b, expected in cases:
        got = _worst_status(a, b)
        if got != expected:
            failures += 1
            print(f"  [FAIL] _worst_status({a!r}, {b!r}) -> {got!r}, expected {expected!r}")
        elif verbose:
            print(f"  [PASS] _worst_status({a!r}, {b!r}) -> {got!r}")
    return failures


# ---------------------------------------------------------------------------
# Integration test runner
# ---------------------------------------------------------------------------

def _run_tests(verbose: bool = False) -> int:
    """
    Execute all integration test cases and report results.

    Returns
    -------
    int
        Number of failed tests.
    """
    failures = 0
    passes   = 0

    print("=" * 74)
    print(f"  MetroScan AI -- combine_checks.py test suite  ({len(TEST_CASES)} cases)")
    print("=" * 74)
    print()

    for tc in TEST_CASES:
        result = check_label_declaration(tc["field_data"], tc["text_regions"])

        got_rule    = result.get("rule_check", {}).get("status", "")
        got_font    = result.get("font_check", {}).get("status", "")
        got_overall = result.get("overall_status", "")

        exp_rule    = tc["expect_rule_status"]
        exp_font    = tc["expect_font_status"]
        exp_overall = tc["expect_overall"]

        ok = (got_rule == exp_rule and got_font == exp_font and got_overall == exp_overall)

        if ok:
            passes += 1
            if verbose:
                print(f"  [PASS]  {tc['name']}")
                print(f"          rule={got_rule}  font={got_font}  overall={got_overall}")
                print()
        else:
            failures += 1
            print(f"  [FAIL]  {tc['name']}")
            if got_rule != exp_rule:
                print(f"          rule_check.status:  got={got_rule!r}  "
                      f"expected={exp_rule!r}")
            if got_font != exp_font:
                print(f"          font_check.status:  got={got_font!r}  "
                      f"expected={exp_font!r}")
            if got_overall != exp_overall:
                print(f"          overall_status:     got={got_overall!r}  "
                      f"expected={exp_overall!r}")
            print(f"          field_data:   {tc['field_data']}")
            print(f"          full result:  {result}")
            print()

    print("-" * 74)
    print(f"  Results: {passes} passed, {failures} failed  (of {len(TEST_CASES)} total)")
    if failures == 0:
        print("  ALL TESTS PASSED.")
    else:
        print(f"  {failures} TEST(S) FAILED -- see details above.")
    print("=" * 74)

    return failures


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MetroScan AI -- combine_checks.py test suite",
        epilog="Exit code 0 = all tests passed.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print passing test cases in addition to failures",
    )
    args = parser.parse_args()

    print()
    print(">> Running _worst_status() unit checks ...")
    print()
    failures_ws = _run_worst_status_checks(verbose=args.verbose)
    if not args.verbose:
        status_label = "PASS" if failures_ws == 0 else "FAIL"
        print(f"  _worst_status checks: [{status_label}]  ({10} cases)")

    print()
    print(">> Running check_label_declaration() integration tests ...")
    print()
    failures_int = _run_tests(verbose=args.verbose)

    total = failures_ws + failures_int
    print()
    if total == 0:
        print("[TOTAL] All checks passed.")
    else:
        print(f"[TOTAL] {total} failure(s) detected.")

    sys.exit(0 if total == 0 else 1)


if __name__ == "__main__":
    main()
