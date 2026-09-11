"""
debug_visualize.py
==================
MetroScan AI -- Debug & Visualization Script
Person 4 of 6 | Hackathon MVP

PURPOSE:
    Runs the relative font-size pipeline on any image that has been annotated
    with text region bounding boxes, and saves an annotated output image with:
      - Every text region bounding box drawn on the image
      - The reference (largest) box highlighted distinctly in gold/cyan
      - A colour-coded HUD overlay showing each declaration's ratio and status

WHAT IS DRAWN ON THE OUTPUT IMAGE:
    - All text region boxes (grey outline for non-declaration regions)
    - Reference (tallest) box: thick gold/cyan outline with [REF] label
    - Declaration boxes colour-coded by tier:
        Green  -> likely_compliant
        Yellow -> needs_review
        Red    -> likely_violation
    - HUD panel (bottom-left): per-declaration ratio + status table

USAGE (command-line):
    # After running generate_synthetic_test.py:
    python debug_visualize.py --image test_images/synthetic_label.png

    # With explicit regions as a Python literal:
    python debug_visualize.py --image photo.jpg --regions "[...]"

    # Restrict which declarations to evaluate:
    python debug_visualize.py --image test_images/synthetic_label.png --declarations mrp,ingredients

USAGE (as a module):
    from debug_visualize import run_debug_visualization

    text_regions = [
        {"label": "brand_name", "text": "ACME",
         "bbox": {"x": 80, "y": 60, "width": 400, "height": 120}},
        {"label": "mrp", "text": "MRP Rs. 45",
         "bbox": {"x": 80, "y": 275, "width": 200, "height": 15}},
    ]
    run_debug_visualization("test_images/synthetic_label.png", text_regions)

OUTPUT:
    output/debug_visualizations/<input_stem>_debug.png
"""

import argparse
import ast
import os
import sys

import cv2
import numpy as np

from physical_measurement import (
    get_text_bboxes,
    find_largest_text_height,
    check_declaration_font_size,
    MIN_RATIO_THRESHOLD,
    REVIEW_BAND,
)

OUTPUT_DIR: str = os.path.join("output", "debug_visualizations")

# ---------------------------------------------------------------------------
# Colour palette (BGR)
# ---------------------------------------------------------------------------
COL_REFERENCE  = (0,   200, 220)   # gold/cyan for the reference box
COL_COMPLIANT  = (60,  200,  60)   # green
COL_REVIEW     = (0,   200, 230)   # amber/yellow
COL_VIOLATION  = (40,   40, 220)   # red
COL_NEUTRAL    = (160, 160, 160)   # grey for non-declaration regions
COL_HUD_BG     = (28,   28,  28)   # dark HUD background
COL_HUD_TEXT   = (220, 220, 220)   # light HUD text

STATUS_COLORS: dict = {
    "likely_compliant": COL_COMPLIANT,
    "needs_review":     COL_REVIEW,
    "likely_violation": COL_VIOLATION,
}

STATUS_SHORT: dict = {
    "likely_compliant": "COMPLIANT",
    "needs_review":     "REVIEW",
    "likely_violation": "VIOLATION",
}


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_rounded_rect(
    img: np.ndarray,
    x: int, y: int, w: int, h: int,
    color: tuple,
    radius: int = 10,
    thickness: int = -1,
) -> None:
    """Draw a filled rounded rectangle (used for HUD panels)."""
    for cx, cy in [
        (x + radius, y + radius),
        (x + w - radius, y + radius),
        (x + radius, y + h - radius),
        (x + w - radius, y + h - radius),
    ]:
        cv2.circle(img, (cx, cy), radius, color, thickness)
    cv2.rectangle(img, (x + radius, y), (x + w - radius, y + h), color, thickness)
    cv2.rectangle(img, (x, y + radius), (x + w, y + h - radius), color, thickness)


def _put_outlined_text(
    img: np.ndarray,
    text: str,
    pos: tuple,
    scale: float = 0.48,
    color: tuple = COL_HUD_TEXT,
    thickness: int = 1,
) -> None:
    """Draw text with a thin dark outline for readability on any background."""
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# Overlay drawing functions
# ---------------------------------------------------------------------------

def draw_all_bboxes(
    image: np.ndarray,
    text_regions: list,
    declaration_results: dict,
    reference_label: str,
) -> np.ndarray:
    """
    Draw all text bounding boxes on the image with tier colour-coding.

    Parameters
    ----------
    image : np.ndarray
        BGR image to annotate (copied internally).
    text_regions : list[dict]
        All validated text region dicts.
    declaration_results : dict
        Mapping of label -> result dict (from check_declaration_font_size).
        Regions not in this mapping are drawn in neutral grey.
    reference_label : str
        Label key of the reference (tallest) region; drawn with special styling.

    Returns
    -------
    np.ndarray
        Annotated BGR image.
    """
    out = image.copy()

    for region in text_regions:
        label = region["label"]
        b = region["bbox"]
        x, y, w, h = b["x"], b["y"], b["width"], b["height"]
        is_reference = (label == reference_label)
        result = declaration_results.get(label)

        if is_reference:
            # Reference box: thick gold/cyan outline + corner ticks
            cv2.rectangle(out, (x - 2, y - 2), (x + w + 2, y + h + 2),
                          COL_REFERENCE, 3)
            cv2.rectangle(out, (x, y), (x + w, y + h), COL_REFERENCE, 1)
            _put_outlined_text(
                out, f"[REF] {label}  ({h}px)",
                (x, y - 9), scale=0.44, color=COL_REFERENCE,
            )
            tick = 7
            for px, py in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
                cv2.line(out, (px - tick, py), (px + tick, py), COL_REFERENCE, 2)
                cv2.line(out, (px, py - tick), (px, py + tick), COL_REFERENCE, 2)

        elif result is not None:
            status = result.get("status", "needs_review")
            col = STATUS_COLORS.get(status, COL_NEUTRAL)
            ratio = result.get("ratio")
            ratio_str = f"{ratio:.3f}" if ratio is not None else "N/A"
            cv2.rectangle(out, (x, y), (x + w, y + h), col, 2)
            lbl = f"{label}  r={ratio_str}  [{STATUS_SHORT.get(status, status)}]"
            _put_outlined_text(out, lbl, (x, y - 8), scale=0.42, color=col)

        else:
            # Non-declaration context region (e.g. not in declaration_results)
            cv2.rectangle(out, (x, y), (x + w, y + h), COL_NEUTRAL, 1)
            _put_outlined_text(out, label, (x, y - 8), scale=0.40, color=COL_NEUTRAL)

    return out


def draw_hud(
    image: np.ndarray,
    declaration_results: dict,
    reference_height_px: float,
) -> np.ndarray:
    """
    Draw a semi-transparent HUD panel in the bottom-left corner.

    Shows per-declaration ratio and tier status, colour-coded by verdict.

    Parameters
    ----------
    image : np.ndarray
        BGR image to annotate.
    declaration_results : dict
        Mapping of label -> result dict.
    reference_height_px : float
        Pixel height of the reference (displayed in the header row).

    Returns
    -------
    np.ndarray
        Annotated BGR image.
    """
    out = image.copy()
    h_img = out.shape[0]

    n_rows = len(declaration_results) + 2   # header + separator + per-entry rows
    row_h = 22
    panel_h = n_rows * row_h + 28
    panel_w = 460
    margin = 14
    px = margin
    py = h_img - panel_h - margin

    # Semi-transparent dark panel
    overlay = out.copy()
    _draw_rounded_rect(overlay, px, py, panel_w, panel_h,
                       color=COL_HUD_BG, radius=10, thickness=-1)
    cv2.addWeighted(overlay, 0.80, out, 0.20, 0, out)

    text_x = px + 12
    line_y = py + 20

    _put_outlined_text(
        out, "MetroScan AI  |  Font Size Heuristic",
        (text_x, line_y), scale=0.50, color=(200, 200, 200),
    )
    _put_outlined_text(
        out,
        f"ref={reference_height_px:.0f}px  thresh={MIN_RATIO_THRESHOLD}  "
        f"band=+/-{REVIEW_BAND}",
        (text_x, line_y + row_h), scale=0.42, color=(160, 160, 160),
    )

    for i, (label, result) in enumerate(declaration_results.items()):
        row_y = line_y + (i + 2) * row_h
        status = result.get("status", "needs_review")
        ratio  = result.get("ratio")
        decl_h = result.get("declaration_height_px")

        col = STATUS_COLORS.get(status, COL_NEUTRAL)
        tier_tag = STATUS_SHORT.get(status, status)
        ratio_str = f"{ratio:.3f}" if ratio is not None else "N/A"
        h_str = f"{decl_h:.0f}px" if decl_h is not None else "N/A"

        line = f"  {label:<16s}  {h_str:>6s}  ratio={ratio_str}  {tier_tag}"
        _put_outlined_text(out, line, (text_x, row_y), scale=0.44, color=col)

    return out


# ---------------------------------------------------------------------------
# Main visualization function (module-level API)
# ---------------------------------------------------------------------------

def run_debug_visualization(
    image_path: str,
    text_regions: list,
    declaration_labels: list = None,
    output_dir: str = OUTPUT_DIR,
) -> str:
    """
    Run the full relative font-size pipeline and save an annotated debug image.

    Parameters
    ----------
    image_path : str
        Path to the input image.
    text_regions : list[dict]
        All text regions on the label (from OCR / test harness).
    declaration_labels : list[str] or None
        Label keys to evaluate for compliance. If None, all labels except the
        reference (tallest) are checked automatically.
    output_dir : str
        Directory where the annotated output image is saved.

    Returns
    -------
    str
        Absolute path to the saved debug image.
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Cannot load image: {image_path}", file=sys.stderr)
        sys.exit(1)
    print(f"[INFO] Loaded: {image_path}  ({image.shape[1]}x{image.shape[0]})")

    # Validate regions
    dummy = np.zeros((1, 1, 3), dtype=np.uint8)
    valid_regions = get_text_bboxes(image=dummy, supplied_regions=text_regions)
    if not valid_regions:
        print("[ERROR] No valid text regions.", file=sys.stderr)
        sys.exit(1)
    print(f"[INFO] {len(valid_regions)} valid text region(s)")

    # Determine reference (tallest) region
    reference_height = find_largest_text_height(valid_regions)
    reference_region = next(
        (r for r in valid_regions
         if float(r["bbox"]["height"]) == reference_height),
        None,
    )
    reference_label = reference_region["label"] if reference_region else ""
    print(f"[INFO] Reference: '{reference_label}'  ({reference_height:.0f}px)")

    # Determine which labels to evaluate
    if declaration_labels is None:
        declaration_labels = [
            r["label"] for r in valid_regions if r["label"] != reference_label
        ]
    print(f"[INFO] Evaluating: {declaration_labels}")

    # Run pipeline per declaration
    declaration_results: dict = {}
    for label in declaration_labels:
        result = check_declaration_font_size(
            text_regions=valid_regions,
            declaration_label=label,
        )
        declaration_results[label] = result
        ratio_str = (f"{result['ratio']:.3f}" if result["ratio"] is not None
                     else "N/A")
        print(f"[INFO]   {label:<20s}  ratio={ratio_str}  "
              f"status={result['status']}")

    # Draw all overlays
    annotated = draw_all_bboxes(
        image, valid_regions, declaration_results, reference_label,
    )
    annotated = draw_hud(annotated, declaration_results, reference_height)

    # Save output
    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(output_dir, f"{stem}_debug.png")
    cv2.imwrite(out_path, annotated)
    print(f"[OK] Debug image saved to: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_regions(value: str) -> list:
    """Parse a text_regions list from a Python literal string."""
    try:
        result = ast.literal_eval(value)
        if not isinstance(result, list):
            raise ValueError("Must be a Python list")
        return result
    except Exception as exc:
        print(f"[ERROR] --regions parse failed: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MetroScan AI -- Debug visualizer for font-size heuristic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick run using the synthetic test image (no --regions needed):
  python debug_visualize.py --image test_images/synthetic_label.png

  # Providing custom text regions as a Python literal:
  python debug_visualize.py --image photo.jpg --regions "[{...}]"

  # Evaluate specific declarations only:
  python debug_visualize.py --image test_images/synthetic_label.png --declarations mrp,ingredients
        """,
    )
    parser.add_argument("--image",        required=True, help="Path to input image")
    parser.add_argument("--regions",      default=None,
                        help="Python list literal of text_regions dicts. "
                             "If omitted, loads from generate_synthetic_test.py")
    parser.add_argument("--declarations", default=None,
                        help="Comma-separated label keys to evaluate "
                             "(default: all except reference)")
    parser.add_argument("--output-dir",   default=OUTPUT_DIR,
                        help=f"Output directory (default: {OUTPUT_DIR})")

    args = parser.parse_args()

    # Resolve text_regions
    if args.regions:
        text_regions = _parse_regions(args.regions)
    else:
        try:
            from generate_synthetic_test import build_text_regions_list
            text_regions = build_text_regions_list()
            print("[INFO] No --regions supplied; loaded from generate_synthetic_test.py")
        except ImportError:
            print(
                "[ERROR] --regions not supplied and generate_synthetic_test.py "
                "not importable. Provide --regions explicitly.",
                file=sys.stderr,
            )
            sys.exit(1)

    declaration_labels = (
        [s.strip() for s in args.declarations.split(",")]
        if args.declarations else None
    )

    run_debug_visualization(
        image_path=args.image,
        text_regions=text_regions,
        declaration_labels=declaration_labels,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
