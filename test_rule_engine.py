"""
test_rule_engine.py
===================
MetroScan AI -- Rule Engine Test Script
Person 4 of 6 | Hackathon MVP

PURPOSE:
    Manually verify rule_engine.py against known-good, missing, and malformed
    inputs for all four declaration fields before connecting real OCR data.

    Run with:
        python test_rule_engine.py
        python test_rule_engine.py --verbose   # shows passing cases too

    Exit code 0 = all tests passed.
    Exit code 1 = one or more failures (failures are printed to stdout).

TEST STRUCTURE:
    3+ cases per field (valid / missing / malformed) x 4 fields = 12+ cases.
    Edge-case group tests null / empty / unknown inputs.

    Each case is a dict:
        {
            "name":            str   -- human-readable description
            "input":           dict  -- raw extraction dict fed to check_declaration()
            "expect_present":  bool  -- expected "present" value
            "expect_format":   bool  -- expected "format_valid" value
            "expect_status":   str   -- expected "status" string
        }
"""

from __future__ import annotations

import argparse
import sys

from rule_engine import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    check_declaration,
    check_format,
    check_presence,
    classify_declaration,
)


# ---------------------------------------------------------------------------
# Test-case definitions
# ---------------------------------------------------------------------------

TEST_CASES: list[dict] = [

    # =========================================================================
    # MRP
    # =========================================================================
    {
        "name": "mrp / valid -- rupee symbol + decimal amount",
        "input": {"field": "mrp", "text": "\u20b930.00 incl. of all taxes", "confidence": 0.92},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "mrp / valid -- Rs. prefix",
        "input": {"field": "mrp", "text": "Rs. 199", "confidence": 0.85},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "mrp / valid -- rupee with comma-separated thousands",
        "input": {"field": "mrp", "text": "MRP: \u20b91,299.00 (incl. taxes)", "confidence": 0.95},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "mrp / missing -- empty text",
        "input": {"field": "mrp", "text": "", "confidence": 0.90},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
    {
        "name": "mrp / missing -- null text",
        "input": {"field": "mrp", "text": None, "confidence": 0.90},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
    {
        "name": "mrp / malformed -- number only, no currency symbol",
        "input": {"field": "mrp", "text": "30.00", "confidence": 0.88},
        "expect_present": True,
        "expect_format":  False,
        "expect_status":  "needs_review",
    },
    {
        "name": "mrp / malformed -- currency symbol but no number",
        "input": {"field": "mrp", "text": "\u20b9 incl. taxes", "confidence": 0.75},
        "expect_present": True,
        "expect_format":  False,
        "expect_status":  "needs_review",
    },
    {
        "name": "mrp / low confidence -- valid format but confidence too low",
        "input": {"field": "mrp", "text": "\u20b999.00", "confidence": 0.40},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "needs_review",
    },

    # =========================================================================
    # NET QUANTITY
    # =========================================================================
    {
        "name": "net_quantity / valid -- grams",
        "input": {"field": "net_quantity", "text": "Net Wt. 38.5 g", "confidence": 0.91},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "net_quantity / valid -- kilograms",
        "input": {"field": "net_quantity", "text": "1.5 kg", "confidence": 0.88},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "net_quantity / valid -- millilitres",
        "input": {"field": "net_quantity", "text": "500ml", "confidence": 0.94},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "net_quantity / valid -- pieces",
        "input": {"field": "net_quantity", "text": "10 pieces", "confidence": 0.80},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "net_quantity / missing -- empty text",
        "input": {"field": "net_quantity", "text": "", "confidence": 0.85},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
    {
        "name": "net_quantity / malformed -- number without unit",
        "input": {"field": "net_quantity", "text": "38.5", "confidence": 0.87},
        "expect_present": True,
        "expect_format":  False,
        "expect_status":  "needs_review",
    },
    {
        "name": "net_quantity / malformed -- unit without number",
        "input": {"field": "net_quantity", "text": "grams only", "confidence": 0.80},
        "expect_present": True,
        "expect_format":  False,
        "expect_status":  "needs_review",
    },
    {
        "name": "net_quantity / low confidence -- valid format but confidence too low",
        "input": {"field": "net_quantity", "text": "200 ml", "confidence": 0.35},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "needs_review",
    },

    # =========================================================================
    # MANUFACTURER
    # =========================================================================
    {
        "name": "manufacturer / valid -- full company name",
        "input": {
            "field": "manufacturer",
            "text": "Manufactured by ABC Foods Pvt. Ltd., Mumbai - 400001",
            "confidence": 0.93,
        },
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "manufacturer / valid -- short company name",
        "input": {"field": "manufacturer", "text": "XY Corp", "confidence": 0.78},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "manufacturer / valid -- with address",
        "input": {
            "field": "manufacturer",
            "text": "Haldiram Foods International Ltd., New Delhi",
            "confidence": 0.89,
        },
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "manufacturer / missing -- empty text",
        "input": {"field": "manufacturer", "text": "", "confidence": 0.85},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
    {
        "name": "manufacturer / missing -- null text",
        "input": {"field": "manufacturer", "text": None, "confidence": 0.85},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
    {
        "name": "manufacturer / malformed -- digits and symbols only, no letters",
        "input": {"field": "manufacturer", "text": "12345 ***", "confidence": 0.80},
        "expect_present": True,
        "expect_format":  False,
        "expect_status":  "needs_review",
    },
    {
        "name": "manufacturer / low confidence",
        "input": {"field": "manufacturer", "text": "Best Bakes Ltd.", "confidence": 0.45},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "needs_review",
    },

    # =========================================================================
    # DATE DECLARATION
    # =========================================================================
    {
        "name": "date_declaration / valid -- best before with mm/yyyy",
        "input": {"field": "date_declaration", "text": "Best Before: 12/2026", "confidence": 0.91},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "date_declaration / valid -- MFG and EXP with full date",
        "input": {
            "field": "date_declaration",
            "text": "MFG: 01-2024, EXP: 01-2025",
            "confidence": 0.88,
        },
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "date_declaration / valid -- use by keyword",
        "input": {"field": "date_declaration", "text": "Use by Dec 2025", "confidence": 0.86},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "date_declaration / valid -- bare expiry abbreviation",
        "input": {"field": "date_declaration", "text": "Exp. 06/27", "confidence": 0.90},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "likely_compliant",
    },
    {
        "name": "date_declaration / missing -- empty text",
        "input": {"field": "date_declaration", "text": "", "confidence": 0.85},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
    {
        "name": "date_declaration / malformed -- only a generic label, no date or keyword",
        "input": {"field": "date_declaration", "text": "See bottom of pack", "confidence": 0.80},
        "expect_present": True,
        "expect_format":  False,
        "expect_status":  "needs_review",
    },
    {
        "name": "date_declaration / malformed -- whitespace only",
        "input": {"field": "date_declaration", "text": "   ", "confidence": 0.70},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
    {
        "name": "date_declaration / low confidence -- valid format but confidence too low",
        "input": {"field": "date_declaration", "text": "Best Before 03/2026", "confidence": 0.55},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "needs_review",
    },

    # =========================================================================
    # EDGE CASES
    # =========================================================================
    {
        "name": "edge / null confidence -- treated as 0.0 -> needs_review",
        "input": {"field": "mrp", "text": "\u20b950.00", "confidence": None},
        "expect_present": True,
        "expect_format":  True,
        "expect_status":  "needs_review",   # 0.0 < DEFAULT_CONFIDENCE_THRESHOLD
    },
    {
        "name": "edge / unknown field -- format check returns False",
        "input": {"field": "barcode", "text": "8901030012345", "confidence": 0.99},
        "expect_present": True,
        "expect_format":  False,
        "expect_status":  "needs_review",
    },
    {
        "name": "edge / missing field key entirely",
        "input": {"text": "\u20b930.00", "confidence": 0.90},   # no "field" key
        "expect_present": True,
        "expect_format":  False,   # empty field name -> unknown -> False
        "expect_status":  "needs_review",
    },
    {
        "name": "edge / empty dict",
        "input": {},
        "expect_present": False,
        "expect_format":  False,
        "expect_status":  "likely_violation",
    },
]


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def _run_tests(verbose: bool = False) -> int:
    """
    Execute all test cases and report results.

    Parameters
    ----------
    verbose : bool
        If True, also print passing test cases.

    Returns
    -------
    int
        Number of failed tests.
    """
    failures = 0
    passes   = 0

    col_w = max(len(tc["name"]) for tc in TEST_CASES) + 2

    print("=" * 74)
    print(f"  MetroScan AI -- rule_engine.py test suite  ({len(TEST_CASES)} cases)")
    print("=" * 74)
    print()

    for tc in TEST_CASES:
        result = check_declaration(tc["input"])

        got_present = result["present"]
        got_format  = result["format_valid"]
        got_status  = result["status"]

        exp_present = tc["expect_present"]
        exp_format  = tc["expect_format"]
        exp_status  = tc["expect_status"]

        ok = (got_present == exp_present
              and got_format  == exp_format
              and got_status  == exp_status)

        if ok:
            passes += 1
            if verbose:
                print(f"  [PASS]  {tc['name']}")
                print(f"          present={got_present}  format={got_format}  "
                      f"status={got_status}")
                print()
        else:
            failures += 1
            print(f"  [FAIL]  {tc['name']}")
            if got_present != exp_present:
                print(f"          present:      got={got_present!r}  "
                      f"expected={exp_present!r}")
            if got_format != exp_format:
                print(f"          format_valid: got={got_format!r}  "
                      f"expected={exp_format!r}")
            if got_status != exp_status:
                print(f"          status:       got={got_status!r}  "
                      f"expected={exp_status!r}")
            print(f"          input text:   {tc['input'].get('text')!r}")
            print(f"          full result:  {result}")
            print()

    print("-" * 74)
    print(f"  Results: {passes} passed, {failures} failed  "
          f"(of {len(TEST_CASES)} total)")
    if failures == 0:
        print("  ALL TESTS PASSED.")
    else:
        print(f"  {failures} TEST(S) FAILED -- see details above.")
    print("=" * 74)

    return failures


# ---------------------------------------------------------------------------
# Quick unit checks for the lower-level helpers
# ---------------------------------------------------------------------------

def _run_helper_checks(verbose: bool = False) -> int:
    """
    Lightweight sanity checks for check_presence() and check_format() directly.

    Returns
    -------
    int
        Number of failures.
    """
    failures = 0

    # check_presence
    presence_cases = [
        ({"field": "mrp", "text": "₹30.00", "confidence": 0.9}, True),
        ({"field": "mrp", "text": "",        "confidence": 0.9}, False),
        ({"field": "mrp", "text": None,      "confidence": 0.9}, False),
        ({"field": "mrp", "text": "   ",     "confidence": 0.9}, False),
        ({},                                                      False),
    ]
    for inp, expected in presence_cases:
        got = check_presence(inp)
        ok  = (got == expected)
        if not ok:
            failures += 1
            print(f"  [FAIL] check_presence({inp!r}) -> {got!r}, expected {expected!r}")
        elif verbose:
            print(f"  [PASS] check_presence: present={got}  input={inp.get('text')!r}")

    # check_format -- spot checks
    format_cases = [
        ("mrp",              "\u20b930.00",            True),
        ("mrp",              "30.00",              False),
        ("mrp",              "Rs. 199",            True),
        ("net_quantity",     "38.5 g",             True),
        ("net_quantity",     "38.5",               False),
        ("net_quantity",     "500ml",              True),
        ("manufacturer",     "ABC Corp Pvt Ltd",   True),
        ("manufacturer",     "12345",              False),
        ("date_declaration", "Best Before 12/26",  True),
        ("date_declaration", "See bottom of pack", False),
        ("date_declaration", "Exp. 2025",          True),
        ("unknown_field",    "anything",           False),
    ]
    for field, text, expected in format_cases:
        got = check_format(field, text)
        ok  = (got == expected)
        if not ok:
            failures += 1
            print(f"  [FAIL] check_format({field!r}, {text!r}) -> {got!r}, "
                  f"expected {expected!r}")
        elif verbose:
            print(f"  [PASS] check_format({field!r}, {text!r}) -> {got!r}")

    return failures


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MetroScan AI -- rule_engine.py test suite",
        epilog="Exit code 0 = all tests passed.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print passing test cases in addition to failures",
    )
    args = parser.parse_args()

    print()
    print(">> Running check_declaration() integration tests ...")
    print()
    failures_main = _run_tests(verbose=args.verbose)

    print()
    print(">> Running check_presence() / check_format() helper checks ...")
    print()
    failures_helpers = _run_helper_checks(verbose=args.verbose)

    total_failures = failures_main + failures_helpers
    if total_failures > 0:
        print()
        print(f"[TOTAL] {total_failures} failure(s) detected.")
    else:
        print()
        print("[TOTAL] All checks passed.")

    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
