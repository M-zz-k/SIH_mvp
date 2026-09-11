"""
generate_synthetic_test.py
==========================
MetroScan AI -- Synthetic Label Image Generator
Person 4 of 6 | Hackathon MVP

PURPOSE:
    Creates a controlled, noise-free synthetic "product label" so we can
    validate the full relative font-size pipeline without needing real
    product photos. Every rectangle is drawn at a KNOWN pixel height, so
    we can pre-compute the EXPECTED pipeline output and assert exact equality.

HOW IT WORKS:
    1. Draw several filled rectangles on a canvas, each representing a text
       region at a precisely defined pixel height:
         - brand_name  : tallest  (simulates the big product name / reference)
         - net_quantity: medium height
         - mrp         : small    (the declaration under scrutiny)
         - ingredients : very small (deliberately below the violation threshold)
    2. Output the expected text_regions list with known pixel heights.
    3. For each declaration, print the expected ratio and status so you can
       confirm the pipeline output matches exactly.

USAGE:
    python generate_synthetic_test.py

OUTPUT:
    test_images/synthetic_label.png   -- the synthetic label image
    Prints a ground-truth results table to stdout.
"""

import os
import sys

import cv2
import numpy as np

# Import our pipeline to verify expected values at generation time
from physical_measurement import (
    check_declaration_font_size,
    MIN_RATIO_THRESHOLD,
    REVIEW_BAND,
)

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------
CANVAS_W: int = 860
CANVAS_H: int = 520
CANVAS_BG: tuple = (245, 243, 238)   # off-white label background (BGR)

OUTPUT_DIR: str = "test_images"
OUTPUT_FILENAME: str = "synthetic_label.png"

# ---------------------------------------------------------------------------
# Synthetic text regions -- KNOWN ground-truth pixel heights
#
# Heights are chosen to exercise all three tier outcomes with default thresholds
# (MIN_RATIO_THRESHOLD=0.12, REVIEW_BAND=0.03, so bands are <0.09 / 0.09-0.15 / >=0.15):
#
#   brand_name    = 120 px  (reference denominator)
#   net_quantity  =  24 px  ratio = 24/120 = 0.200  -> likely_compliant  (>= 0.15)
#   mrp           =  15 px  ratio = 15/120 = 0.125  -> needs_review      (0.09-0.15)
#   ingredients   =   9 px  ratio =  9/120 = 0.075  -> likely_violation  (< 0.09)
#
# NOTE: if you change these heights, re-run the script to check the table.
# ---------------------------------------------------------------------------
REGIONS_SPEC: list = [
    {
        "label":  "brand_name",
        "text":   "ACME FOODS",
        "color":  (30,  30,  30),   # near-black
        "width":  400,
        "height": 120,
        "x":      80,
        "y":      60,
    },
    {
        "label":  "net_quantity",
        "text":   "Net Qty: 500g",
        "color":  (50,  80, 120),   # dark blue
        "width":  260,
        "height": 24,
        "x":      80,
        "y":      220,
    },
    {
        "label":  "mrp",
        "text":   "MRP Rs. 45",
        "color":  (20, 100,  20),   # dark green
        "width":  200,
        "height": 15,
        "x":      80,
        "y":      275,
    },
    {
        "label":  "ingredients",
        "text":   "Ingredients: wheat, salt...",
        "color":  (80,  40,  80),   # dark purple
        "width":  560,
        "height": 9,
        "x":      80,
        "y":      330,
    },
]

# Labels we want to check for compliance (brand_name is the reference)
DECLARATION_LABELS: list = ["mrp", "net_quantity", "ingredients"]


# ---------------------------------------------------------------------------
# Build the standard text_regions list
# ---------------------------------------------------------------------------

def build_text_regions_list() -> list:
    """
    Convert REGIONS_SPEC into the standard text_regions list accepted by the
    pipeline.

    Returns
    -------
    list[dict]
        Each entry shaped as::

            {"label": str, "text": str,
             "bbox": {"x": int, "y": int, "width": int, "height": int}}
    """
    return [
        {
            "label": spec["label"],
            "text":  spec["text"],
            "bbox": {
                "x":      spec["x"],
                "y":      spec["y"],
                "width":  spec["width"],
                "height": spec["height"],
            },
        }
        for spec in REGIONS_SPEC
    ]


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def generate_synthetic_image(text_regions: list) -> np.ndarray:
    """
    Build and return the synthetic label canvas (BGR NumPy array).

    Each text region is rendered as a filled rectangle at its exact specified
    height, with its label and pixel dimensions printed above it.

    Parameters
    ----------
    text_regions : list[dict]
        Standard text_regions list (as returned by build_text_regions_list).

    Returns
    -------
    np.ndarray
        BGR image of the synthetic label.
    """
    canvas = np.full((CANVAS_H, CANVAS_W, 3), CANVAS_BG, dtype=np.uint8)

    # Title banner
    cv2.putText(
        canvas, "MetroScan AI -- Synthetic Label (ground-truth test)",
        (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (40, 40, 40), 2, cv2.LINE_AA,
    )
    cv2.line(canvas, (20, 42), (CANVAS_W - 20, 42), (180, 180, 170), 1)

    # Render each region
    for spec, region in zip(REGIONS_SPEC, text_regions):
        x = region["bbox"]["x"]
        y = region["bbox"]["y"]
        w = region["bbox"]["width"]
        h = region["bbox"]["height"]
        color = spec["color"]
        label = region["label"]

        # Filled rectangle simulating the text block
        cv2.rectangle(canvas, (x, y), (x + w, y + h), color, -1)

        # Thin darker border for visibility on light background
        border_col = tuple(max(0, c - 40) for c in color)
        cv2.rectangle(canvas, (x - 1, y - 1), (x + w + 1, y + h + 1),
                      border_col, 1)

        # Annotation above the box
        annotation = f"{label}  [{h}px tall]"
        cv2.putText(
            canvas, annotation,
            (x, y - 7),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1, cv2.LINE_AA,
        )

    # Legend at the bottom
    note_y = CANVAS_H - 50
    cv2.putText(
        canvas,
        f"Thresholds: min_ratio={MIN_RATIO_THRESHOLD}  review_band={REVIEW_BAND}",
        (20, note_y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 100, 100), 1, cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        "Reference (denominator) = tallest bbox = brand_name",
        (20, note_y + 20),
        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 100, 100), 1, cv2.LINE_AA,
    )

    return canvas


# ---------------------------------------------------------------------------
# Expected value computation (runs the actual pipeline)
# ---------------------------------------------------------------------------

def compute_expected_results(text_regions: list) -> list:
    """
    Run the pipeline for every declaration label and collect expected outputs.

    Because all heights are known constants, the pipeline output is exact
    (zero detection uncertainty).

    Parameters
    ----------
    text_regions : list[dict]
        Standard text_regions list.

    Returns
    -------
    list[dict]
        One entry per label in DECLARATION_LABELS with the pipeline result.
    """
    results = []
    for label in DECLARATION_LABELS:
        pipeline_result = check_declaration_font_size(
            text_regions=text_regions,
            declaration_label=label,
        )
        results.append({
            "label":           label,
            "pipeline_result": pipeline_result,
        })
    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate the synthetic label image, save it, and print expected values."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    text_regions = build_text_regions_list()

    image = generate_synthetic_image(text_regions)
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    cv2.imwrite(out_path, image)
    print(f"[OK] Synthetic label image saved to: {out_path}")

    expected_results = compute_expected_results(text_regions)

    # Ground-truth table
    print()
    print("=" * 72)
    print("EXPECTED PIPELINE OUTPUT  (ground-truth, zero noise)")
    lower = MIN_RATIO_THRESHOLD - REVIEW_BAND
    upper = MIN_RATIO_THRESHOLD + REVIEW_BAND
    print(f"  Thresholds: MIN_RATIO_THRESHOLD={MIN_RATIO_THRESHOLD}  "
          f"REVIEW_BAND={REVIEW_BAND}")
    print(f"  Tiers: < {lower:.2f} -> likely_violation  |  "
          f"{lower:.2f}-{upper:.2f} -> needs_review  |  "
          f">= {upper:.2f} -> likely_compliant")
    print("=" * 72)

    ref_height = max(s["height"] for s in REGIONS_SPEC)
    print(f"\n  Reference height (tallest bbox): {ref_height} px  [label: brand_name]\n")

    for entry in expected_results:
        pr = entry["pipeline_result"]
        label = entry["label"]

        indicator = {
            "likely_compliant": "[OK] ",
            "needs_review":     "[??] ",
            "likely_violation": "[!!] ",
        }.get(pr["status"], "     ")

        print(f"  {indicator} {label}")
        print(f"           declaration_height_px : {pr['declaration_height_px']} px")
        print(f"           reference_height_px   : {pr['reference_height_px']} px")
        print(f"           ratio                 : {pr['ratio']}  "
              f"({pr['declaration_height_px']}/{pr['reference_height_px']})")
        print(f"           status                : {pr['status']}")
        print()

    print("  Run debug visualizer with:")
    print(f"    python debug_visualize.py --image {out_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
