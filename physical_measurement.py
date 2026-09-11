"""
physical_measurement.py
=======================
MetroScan AI -- Font Size Heuristic Module
Person 4 of 6 | Hackathon MVP

Responsibilities:
  1. Accept pre-supplied text bounding boxes (from Person 2's OCR module).
  2. Find the tallest text region on the label (used as the reference baseline).
  3. Compute each declaration's height as a ratio of the reference height.
  4. Classify that ratio into a THREE-TIER verdict:
       likely_compliant / needs_review / likely_violation
  5. Orchestrate the above into a single callable for teammate integration.

PIVOT NOTE (v2 -- after project direction change):
  The previous version used an ArUco marker + physical ruler to express
  measurements in absolute millimetres. That design required camera
  calibration and a reference object, which was the single biggest failure
  point for demo conditions. This version removes all of that:

    REMOVED: detect_marker(), compute_pixel_to_mm_ratio()
    REMOVED: any dependency on marker_size_mm, ARUCO, or cv2.aruco

  Instead, we compare declaration text height RELATIVE to the largest text
  block on the same label (almost always the brand name). No calibration
  is needed -- the ratio is dimensionless and camera-distance-independent.

Dependencies:
    opencv-python >= 4.x  (standard build, NOT contrib; aruco not needed)
    numpy

ASSUMPTIONS (MVP):
  - The largest text on a label is a reliable visual anchor (brand name).
    We do NOT hardcode which label key is the reference -- we simply
    take max(height) across all supplied regions.
  - Threshold defaults (MIN_RATIO_THRESHOLD, REVIEW_BAND) are initial guesses.
    They WILL need tuning once we have real label photos. See classify_font_size().
  - Each bbox dict uses the shared OCR contract from Person 2:
      {"label": str, "text": str,
       "bbox": {"x": int, "y": int, "width": int, "height": int}}
"""

from __future__ import annotations

import sys
from typing import List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Module-level configurable thresholds
#
# These are the PRIMARY knobs to tune once real label photos are available.
#
# Tier geometry (using defaults 0.12, 0.03):
#   ratio < 0.09            -> likely_violation
#   0.09 <= ratio < 0.15    -> needs_review
#   ratio >= 0.15           -> likely_compliant
# ---------------------------------------------------------------------------
MIN_RATIO_THRESHOLD: float = 0.12  # centre of the ambiguous review band
REVIEW_BAND: float = 0.03         # +/- half-width of the ambiguous band


# ---------------------------------------------------------------------------
# 1. TEXT REGION STUB / PASSTHROUGH
# ---------------------------------------------------------------------------

def get_text_bboxes(
    image: np.ndarray,
    supplied_regions: Optional[List[dict]] = None,
) -> List[dict]:
    """
    Return a validated list of text bounding-box dicts for downstream processing.

    OCR is owned by Person 2 -- this function is intentionally a STUB.
    When supplied_regions is provided it is returned unchanged after basic
    validation. The image parameter is accepted so the signature is stable
    when Person 2 wires in real OCR detection later.

    Parameters
    ----------
    image : np.ndarray
        BGR image (unused in stub mode; reserved for future OCR integration).
    supplied_regions : list[dict] or None
        Pre-supplied list of text regions, each shaped as::

            {
                "label": str,   # e.g. "mrp", "brand_name", "net_quantity"
                "text":  str,   # OCR string (may be empty string)
                "bbox": {"x": int, "y": int, "width": int, "height": int}
            }

        If None or empty, an empty list is returned.

    Returns
    -------
    list[dict]
        Validated list of region dicts. Malformed entries are dropped with
        a stderr warning; the function never raises.

    Notes
    -----
    Stub assumption: the caller is responsible for correct pixel coordinates.
    No coordinate normalisation or clamping is performed at this stage.
    """
    if not supplied_regions:
        return []

    required_bbox_keys = {"x", "y", "width", "height"}
    valid: List[dict] = []

    for idx, region in enumerate(supplied_regions):
        try:
            if not isinstance(region, dict):
                raise TypeError(f"region {idx} is not a dict")
            if "label" not in region or "bbox" not in region:
                raise KeyError(f"region {idx} missing label or bbox key")
            bbox = region["bbox"]
            missing = required_bbox_keys - set(bbox.keys())
            if missing:
                raise KeyError(f"region {idx} bbox missing keys: {missing}")
            valid.append(region)
        except (TypeError, KeyError) as exc:
            print(f"[get_text_bboxes] WARNING: dropping region {idx}: {exc}",
                  file=sys.stderr)

    return valid


# ---------------------------------------------------------------------------
# 2. FIND REFERENCE TEXT (largest bbox height on the label)
# ---------------------------------------------------------------------------

def find_largest_text_height(text_regions: List[dict]) -> float:
    """
    Return the pixel height of the tallest bounding box across all regions.

    This value is used as the reference denominator in the relative ratio.
    In practice this will almost always correspond to the brand name, but we
    intentionally do NOT hardcode that assumption -- we simply take the maximum
    height regardless of which label key it belongs to. This keeps the function
    robust if the label hierarchy changes or the OCR module renames fields.

    Parameters
    ----------
    text_regions : list[dict]
        Validated region dicts (as returned by get_text_bboxes).

    Returns
    -------
    float
        Maximum bbox["height"] found. Returns 0.0 if the list is empty or all
        heights are non-positive -- callers should treat 0.0 as not usable.

    Assumption
    ----------
    The tallest bounding box on a product label is a reliable visual anchor.
    If multiple regions share the same maximum height, the first one found
    (by iteration order from the upstream OCR / caller) is used.
    """
    max_height = 0.0
    for region in text_regions:
        try:
            h = float(region["bbox"]["height"])
            if h > max_height:
                max_height = h
        except (KeyError, TypeError, ValueError):
            continue
    return max_height


# ---------------------------------------------------------------------------
# 3. RELATIVE SIZE COMPUTATION
# ---------------------------------------------------------------------------

def compute_relative_ratio(
    declaration_bbox_height: float,
    reference_height: float,
) -> float:
    """
    Compute the declaration text height as a fraction of the reference height.

    Parameters
    ----------
    declaration_bbox_height : float
        Pixel height of the declaration text bounding box (e.g. MRP price).
    reference_height : float
        Pixel height of the reference (largest) text on the label.

    Returns
    -------
    float
        declaration_bbox_height / reference_height.
        Returns 0.0 if reference_height is non-positive (safe division).

    Examples
    --------
    >>> compute_relative_ratio(18.0, 120.0)
    0.15
    >>> compute_relative_ratio(10.0, 120.0)
    0.08333333333333333
    """
    if reference_height <= 0.0:
        return 0.0
    return declaration_bbox_height / reference_height


# ---------------------------------------------------------------------------
# 4. TIERED CLASSIFICATION
# ---------------------------------------------------------------------------

def classify_font_size(
    ratio: float,
    min_ratio_threshold: float = MIN_RATIO_THRESHOLD,
    review_band: float = REVIEW_BAND,
) -> str:
    """
    Map a relative height ratio to one of three compliance tiers.

    Tier geometry
    -------------
    Given min_ratio_threshold (T) and review_band (B):

        ratio < T - B           -> "likely_violation"
        T - B <= ratio < T + B  -> "needs_review"
        ratio >= T + B           -> "likely_compliant"

    Parameters
    ----------
    ratio : float
        Output of compute_relative_ratio().
    min_ratio_threshold : float
        Centre of the ambiguous review band. Default 0.12.
        Tune this against real label photos before the demo.
    review_band : float
        Half-width of the ambiguous band. Default 0.03.
        Widen to route more borderline cases to human review;
        narrow to shrink the needs_review bucket.

    Returns
    -------
    str
        One of: "likely_compliant", "needs_review", "likely_violation".

    Notes
    -----
    Both thresholds are parameters (not hardcoded) so callers can override
    them without modifying this function.
    """
    lower = min_ratio_threshold - review_band
    upper = min_ratio_threshold + review_band

    if ratio >= upper:
        return "likely_compliant"
    elif ratio < lower:
        return "likely_violation"
    else:
        return "needs_review"


# ---------------------------------------------------------------------------
# 5. MAIN ORCHESTRATOR
# ---------------------------------------------------------------------------

def check_declaration_font_size(
    text_regions: List[dict],
    declaration_label: str,
    min_ratio_threshold: float = MIN_RATIO_THRESHOLD,
    review_band: float = REVIEW_BAND,
) -> dict:
    """
    Run the full relative font-size pipeline for one declaration field.

    This is the public API consumed by teammates integrating this module.
    Pass in ALL text regions from the label and the label key to evaluate;
    receive a structured result matching the team JSON contract.

    Parameters
    ----------
    text_regions : list[dict]
        All text regions detected on the label. Must include both the
        declaration being checked AND the reference text (tallest region).
    declaration_label : str
        The "label" key of the field to evaluate, e.g. "mrp".
    min_ratio_threshold : float
        Centre threshold for the compliance band (default 0.12).
    review_band : float
        Half-width of the ambiguous band (default 0.03).

    Returns
    -------
    dict
        Fixed JSON contract (field names shared with team, do not rename)::

            {
                "field":                 "<declaration_label>_font_size",
                "declaration_height_px":  float | None,
                "reference_height_px":    float | None,
                "ratio":                  float | None,
                "status": "likely_compliant" | "needs_review" | "likely_violation"
            }

    Notes
    -----
    Returns status="needs_review" with null numeric fields for any
    unresolvable edge case (empty list, label not found, zero reference).
    This function NEVER raises an exception.
    """
    field_key = f"{declaration_label}_font_size"

    needs_review_response: dict = {
        "field":                 field_key,
        "declaration_height_px": None,
        "reference_height_px":   None,
        "ratio":                 None,
        "status":                "needs_review",
    }

    # Guard: empty input
    if not text_regions:
        print("[check_declaration_font_size] WARNING: text_regions is empty.",
              file=sys.stderr)
        return needs_review_response

    # Validate regions
    dummy_image = np.zeros((1, 1, 3), dtype=np.uint8)
    valid_regions = get_text_bboxes(image=dummy_image,
                                    supplied_regions=text_regions)
    if not valid_regions:
        print("[check_declaration_font_size] WARNING: no valid regions after validation.",
              file=sys.stderr)
        return needs_review_response

    # Find the target declaration region
    declaration_region = next(
        (r for r in valid_regions if r["label"] == declaration_label), None
    )
    if declaration_region is None:
        print(f"[check_declaration_font_size] WARNING: label '{declaration_label}'"
              " not found in text_regions.", file=sys.stderr)
        return needs_review_response

    declaration_height = float(declaration_region["bbox"]["height"])

    # Find reference height (tallest bbox across the whole label)
    reference_height = find_largest_text_height(valid_regions)
    if reference_height <= 0.0:
        print("[check_declaration_font_size] WARNING: reference height is 0.",
              file=sys.stderr)
        return needs_review_response

    # Compute ratio and classify
    ratio = compute_relative_ratio(declaration_height, reference_height)
    status = classify_font_size(ratio, min_ratio_threshold, review_band)

    return {
        "field":                 field_key,
        "declaration_height_px": round(declaration_height, 3),
        "reference_height_px":   round(reference_height, 3),
        "ratio":                 round(ratio, 4),
        "status":                status,
    }
