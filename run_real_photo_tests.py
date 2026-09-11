"""
run_real_photo_tests.py
=======================
MetroScan AI -- Batch Real-Photo Test Runner
Person 4 of 6 | Hackathon MVP

PURPOSE:
    1. Scans test_images/real_photos/ for (image, .json annotation) pairs.
    2. Runs check_declaration_font_size() for every non-reference declaration
       in each photo.
    3. Prints a clean summary table to the console.
    4. Saves a debug-annotated image per photo via debug_visualize.
    5. Runs a threshold sensitivity report across all results so you can
       pick better threshold values based on real data instead of guessing.

USAGE:
    python run_real_photo_tests.py
    python run_real_photo_tests.py --photos-dir path/to/photos --verbose

ASSUMPTIONS:
    - Image and annotation files share the same stem:
        label1.jpg  <-->  label1.json
    - Supported image extensions: .jpg .jpeg .png .bmp .webp
    - The reference field (brand_name or whichever is tallest) is determined
      automatically -- the same way the pipeline always works (max height).
    - The threshold sensitivity report uses a hardcoded candidate grid by
      default. Pass --no-sensitivity to skip it.
"""

import argparse
import json
import os
import sys
from typing import List, Tuple

import cv2
import numpy as np

from physical_measurement import (
    check_declaration_font_size,
    classify_font_size,
    find_largest_text_height,
    get_text_bboxes,
    MIN_RATIO_THRESHOLD,
    REVIEW_BAND,
)
from debug_visualize import run_debug_visualization

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PHOTOS_DIR: str = os.path.join("test_images", "real_photos")
OUTPUT_DIR: str = os.path.join("output", "debug_visualizations")
IMAGE_EXTS: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

# Default candidate thresholds to sweep in the sensitivity report.
# Each tuple is (min_ratio_threshold, review_band).
# Assumption: these are reasonable starting points; adjust after seeing results.
DEFAULT_THRESHOLD_GRID: List[Tuple[float, float]] = [
    (0.08, 0.02),
    (0.10, 0.02),
    (0.10, 0.03),
    (0.12, 0.02),
    (0.12, 0.03),   # <-- current default in physical_measurement.py
    (0.12, 0.04),
    (0.15, 0.03),
    (0.15, 0.05),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_pairs(photos_dir: str) -> List[Tuple[str, str]]:
    """
    Scan photos_dir for (image_path, json_path) pairs.

    Returns only pairs where BOTH the image AND the .json annotation exist.
    Logs skipped files to stderr.

    Parameters
    ----------
    photos_dir : str
        Directory to scan.

    Returns
    -------
    list of (image_path, json_path) tuples, sorted by image filename.
    """
    if not os.path.isdir(photos_dir):
        print(f"[ERROR] Photos directory not found: {photos_dir}", file=sys.stderr)
        print(f"        Create it and add images + .json annotations,",
              file=sys.stderr)
        print(f"        or run annotate_real_photo.py to generate annotations.",
              file=sys.stderr)
        return []

    pairs = []
    for fname in sorted(os.listdir(photos_dir)):
        fpath = os.path.join(photos_dir, fname)
        stem, ext = os.path.splitext(fname)
        if ext.lower() not in IMAGE_EXTS:
            continue
        # Skip auto-generated preview/debug images produced by annotation tools.
        # These contain "_preview" or "_debug" in their stem (e.g. label1_preview.png).
        if "_preview" in stem or "_debug" in stem:
            print(f"[SKIP] Ignoring generated file: {fname}", file=sys.stderr)
            continue
        json_path = os.path.join(photos_dir, f"{stem}.json")
        if not os.path.isfile(json_path):
            print(f"[SKIP] No annotation found for: {fname}  "
                  f"(run annotate_real_photo.py --image {fpath})", file=sys.stderr)
            continue
        pairs.append((fpath, json_path))

    return pairs


def _load_annotations(json_path: str) -> List[dict]:
    """
    Load a text_regions annotation file.

    Parameters
    ----------
    json_path : str
        Path to the .json file produced by annotate_real_photo.py.

    Returns
    -------
    list[dict] or [] on error.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Expected a JSON list at the top level")
        return data
    except Exception as exc:
        print(f"[ERROR] Failed to load annotations: {json_path} -- {exc}",
              file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Single-photo test
# ---------------------------------------------------------------------------

def test_single_photo(
    image_path: str,
    json_path: str,
    verbose: bool = False,
) -> List[dict]:
    """
    Run the pipeline on one real photo and return its results.

    Parameters
    ----------
    image_path : str
        Path to the real label photo.
    json_path : str
        Path to the matching .json annotation file.
    verbose : bool
        If True, print per-declaration details in addition to the summary row.

    Returns
    -------
    list[dict]
        One entry per declaration evaluated, each with:
            {
                "photo":                 str,
                "declaration_label":     str,
                "declaration_height_px": float | None,
                "reference_height_px":   float | None,
                "ratio":                 float | None,
                "status":                str,
            }
    """
    stem = os.path.splitext(os.path.basename(image_path))[0]
    text_regions = _load_annotations(json_path)

    if not text_regions:
        print(f"  [{stem}] No valid annotations -- skipped.")
        return []

    # Validate regions through the pipeline's own stub
    dummy = np.zeros((1, 1, 3), dtype=np.uint8)
    valid_regions = get_text_bboxes(image=dummy, supplied_regions=text_regions)
    if not valid_regions:
        print(f"  [{stem}] All annotations failed validation -- skipped.")
        return []

    # Find reference label (tallest bbox -- same logic as core module)
    ref_height = find_largest_text_height(valid_regions)
    ref_region = next(
        (r for r in valid_regions if float(r["bbox"]["height"]) == ref_height), None
    )
    ref_label = ref_region["label"] if ref_region else ""

    # Evaluate every label that is NOT the reference
    declaration_labels = [r["label"] for r in valid_regions if r["label"] != ref_label]

    if verbose:
        print(f"  [{stem}]  ref='{ref_label}' ({ref_height:.0f}px)  "
              f"evaluating: {declaration_labels}")

    results = []
    for label in declaration_labels:
        result = check_declaration_font_size(
            text_regions=valid_regions,
            declaration_label=label,
        )
        row = {
            "photo":                 stem,
            "declaration_label":     label,
            "declaration_height_px": result["declaration_height_px"],
            "reference_height_px":   result["reference_height_px"],
            "ratio":                 result["ratio"],
            "status":                result["status"],
        }
        results.append(row)

        if verbose:
            ratio_s = f"{result['ratio']:.3f}" if result["ratio"] is not None else "N/A"
            print(f"    {label:<20s}  ratio={ratio_s}  {result['status']}")

    return results


# ---------------------------------------------------------------------------
# Summary table printer
# ---------------------------------------------------------------------------

def print_summary_table(all_results: List[dict]) -> None:
    """
    Print a formatted summary table of all results to stdout.

    Parameters
    ----------
    all_results : list[dict]
        Flat list of result rows (as returned by test_single_photo).
    """
    if not all_results:
        print("  (No results to display)")
        return

    # Column widths
    W_PHOTO  = max(len(r["photo"]) for r in all_results)
    W_PHOTO  = max(W_PHOTO, 5)   # minimum "Photo"
    W_LABEL  = max(len(r["declaration_label"]) for r in all_results)
    W_LABEL  = max(W_LABEL, 11)  # minimum "Declaration"

    STATUS_ICONS = {
        "likely_compliant": "[OK] ",
        "needs_review":     "[??] ",
        "likely_violation": "[!!] ",
    }

    header = (f"  {'Photo':<{W_PHOTO}}  {'Declaration':<{W_LABEL}}  "
              f"{'Decl.h':>7}  {'Ref.h':>6}  {'Ratio':>6}  Status")
    sep    = "  " + "-" * (len(header) - 2)

    print(header)
    print(sep)

    last_photo = None
    for r in all_results:
        # Blank line between photos for readability
        if r["photo"] != last_photo and last_photo is not None:
            print()
        last_photo = r["photo"]

        ratio_s  = f"{r['ratio']:.3f}"  if r["ratio"]  is not None else "  N/A"
        decl_s   = (f"{r['declaration_height_px']:.0f}px"
                    if r["declaration_height_px"] is not None else "N/A")
        ref_s    = (f"{r['reference_height_px']:.0f}px"
                    if r["reference_height_px"] is not None else "N/A")
        icon = STATUS_ICONS.get(r["status"], "     ")

        print(f"  {r['photo']:<{W_PHOTO}}  {r['declaration_label']:<{W_LABEL}}  "
              f"{decl_s:>7}  {ref_s:>6}  {ratio_s:>6}  {icon}{r['status']}")

    print(sep)

    # Tier counts
    statuses = [r["status"] for r in all_results]
    n_ok  = statuses.count("likely_compliant")
    n_rev = statuses.count("needs_review")
    n_vio = statuses.count("likely_violation")
    print(f"  Total: {len(all_results)}  |  "
          f"[OK] {n_ok}  [??] {n_rev}  [!!] {n_vio}")


# ---------------------------------------------------------------------------
# Threshold sensitivity report
# ---------------------------------------------------------------------------

def threshold_sensitivity_report(
    all_results: List[dict],
    thresholds_to_test: List[Tuple[float, float]] = None,
) -> None:
    """
    Print a sensitivity table showing tier counts under different threshold settings.

    For each (min_ratio_threshold, review_band) pair, re-classifies every
    collected ratio and counts how many declarations fall into each tier.
    This lets you pick sensible thresholds by eyeballing real data rather
    than guessing.

    Parameters
    ----------
    all_results : list[dict]
        Flat list of result rows from test_single_photo() -- must contain
        a "ratio" key (may be None for failed lookups, which are excluded).
    thresholds_to_test : list of (min_ratio_threshold, review_band) tuples
        Candidate threshold pairs to evaluate. Defaults to DEFAULT_THRESHOLD_GRID.

    Notes
    -----
    - The current production default is marked with a "<-- current" arrow.
    - Ratios that are None (edge cases / errors) are excluded from all counts
      so they don't distort the comparison.
    """
    if thresholds_to_test is None:
        thresholds_to_test = DEFAULT_THRESHOLD_GRID

    # Only work with rows that have a valid ratio
    valid = [r for r in all_results if r["ratio"] is not None]
    ratios = [r["ratio"] for r in valid]

    if not ratios:
        print("  (No valid ratios to analyse -- cannot generate sensitivity report)")
        return

    n = len(ratios)
    print()
    print("=" * 74)
    print(f"THRESHOLD SENSITIVITY REPORT  ({n} declarations with valid ratios)")
    print()
    print(f"  {'min_thresh':>10}  {'band':>6}  "
          f"{'compliant':>10}  {'review':>8}  {'violation':>10}  "
          f"{'lower':>7}  {'upper':>7}")
    print("  " + "-" * 70)

    current_t = MIN_RATIO_THRESHOLD
    current_b = REVIEW_BAND

    for t, b in thresholds_to_test:
        counts = {"likely_compliant": 0, "needs_review": 0, "likely_violation": 0}
        for ratio in ratios:
            tier = classify_font_size(ratio, min_ratio_threshold=t, review_band=b)
            counts[tier] += 1

        is_current = (abs(t - current_t) < 1e-9 and abs(b - current_b) < 1e-9)
        marker = " <-- current" if is_current else ""

        pct = lambda k: f"{counts[k]:>3} ({counts[k]/n*100:4.1f}%)"

        print(f"  {t:>10.3f}  {b:>6.3f}  "
              f"{pct('likely_compliant'):>10}  "
              f"{pct('needs_review'):>8}  "
              f"{pct('likely_violation'):>10}  "
              f"{t-b:>7.3f}  {t+b:>7.3f}"
              f"{marker}")

    print("  " + "-" * 70)
    print()
    print("  Interpretation:")
    print("    - A good threshold keeps likely_violation small (few false alarms)")
    print("      and likely_compliant large, with needs_review as the safety buffer.")
    print("    - Widen the band if real labels cluster near the boundary.")
    print("    - Narrow the band if you have high confidence in the annotation quality.")
    print("=" * 74)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MetroScan AI -- Batch test runner for real label photos",
        epilog="Example:  python run_real_photo_tests.py --verbose",
    )
    parser.add_argument(
        "--photos-dir", default=PHOTOS_DIR,
        help=f"Directory with image + .json pairs (default: {PHOTOS_DIR})",
    )
    parser.add_argument(
        "--output-dir", default=OUTPUT_DIR,
        help=f"Where debug images are saved (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print per-declaration details for each photo",
    )
    parser.add_argument(
        "--no-sensitivity", action="store_true",
        help="Skip the threshold sensitivity report",
    )
    parser.add_argument(
        "--no-debug-images", action="store_true",
        help="Skip saving debug-annotated output images (faster for large batches)",
    )
    args = parser.parse_args()

    # --- Find image+annotation pairs ---
    pairs = _find_pairs(args.photos_dir)
    if not pairs:
        print(f"[INFO] No image+annotation pairs found in: {args.photos_dir}")
        print(f"       Run: python annotate_real_photo.py --image <path_to_photo>")
        sys.exit(0)

    print(f"[INFO] Found {len(pairs)} image+annotation pair(s) in {args.photos_dir}")
    print()

    all_results: List[dict] = []

    for image_path, json_path in pairs:
        stem = os.path.splitext(os.path.basename(image_path))[0]
        print(f"--- {stem} ---")

        results = test_single_photo(image_path, json_path, verbose=args.verbose)
        all_results.extend(results)

        # Save debug-annotated image via existing debug_visualize module
        if not args.no_debug_images and results:
            try:
                annotations = _load_annotations(json_path)
                run_debug_visualization(
                    image_path=image_path,
                    text_regions=annotations,
                    output_dir=args.output_dir,
                )
            except Exception as exc:
                print(f"[WARN] Debug image failed for {stem}: {exc}", file=sys.stderr)

        print()

    # --- Summary table ---
    if all_results:
        print()
        print("=" * 74)
        print("SUMMARY TABLE")
        print("=" * 74)
        print_summary_table(all_results)

    # --- Threshold sensitivity report ---
    if not args.no_sensitivity and all_results:
        threshold_sensitivity_report(all_results)
    elif not all_results:
        print("[INFO] No results collected -- nothing to report.")


if __name__ == "__main__":
    main()
