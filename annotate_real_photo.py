"""
annotate_real_photo.py
======================
MetroScan AI -- Interactive Bounding-Box Annotation Tool
Person 4 of 6 | Hackathon MVP

PURPOSE:
    Lets you manually draw bounding boxes on a real product-label photo so
    you can test the font-size pipeline without waiting for OCR from Person 2.

    APPEND MODE: if a .json file already exists for this image, existing boxes
    are loaded and shown as locked (grey) in the drawing window. You only draw
    NEW boxes on top; the final save merges old + new. You never lose
    previously annotated regions by re-running the tool.

HOW TO USE:
    python annotate_real_photo.py --image test_images/real_photos/label1.jpg
    python annotate_real_photo.py --image test_images/real_photos/label1.jpg --scale 0.6

TWO-PHASE WORKFLOW:
    PHASE 1 -- Drawing (OpenCV image window):
        Existing boxes are shown in GREY with their labels (locked, not editable).
        Click + drag    : draw a NEW bounding box
        u               : undo the last NEW box (cannot undo locked boxes)
        r               : clear box currently being drawn (mid-drag)
        q               : finish drawing -> move to Phase 2

    PHASE 2 -- Labelling (terminal only, window closed):
        Only NEW boxes are prompted. Locked boxes keep their existing labels.
        Type a label for each new box and press Enter.
        Press Enter with no text to discard that new box.

OUTPUT:
    - test_images/real_photos/<stem>.json        -- merged annotation file
    - test_images/real_photos/<stem>_preview.png -- preview with all boxes

OPTIONS:
    --scale 0.6     Scale the display window (useful for large phone photos).
                    Boxes are always saved in ORIGINAL pixel coordinates.
                    If omitted, scale is chosen automatically so the display
                    window is at most 900 px tall (fits most laptop screens).
    --overwrite     Discard existing annotations and start fresh (use with care).
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Drawing state (Phase 1 only)
# ---------------------------------------------------------------------------
_draw_state = {
    "drawing": False,
    "start":   None,
    "current": None,
}

# New boxes drawn this session (display coords) -- list of (bx, by, bw, bh)
# NOTE: this is reset inside run_annotation() at the start of each call so
# that repeated calls (e.g. in a batch loop) never carry over stale boxes.
_new_boxes: list = []

# Colors for NEW boxes (cycle)
_NEW_COLORS = [
    (0,   200, 220),
    (60,  200,  60),
    (0,   190, 230),
    (40,   40, 220),
    (180,  60, 180),
    (200, 130,  40),
    (30,  180, 180),
    (220, 100,  40),
]
_LOCKED_COLOR = (140, 140, 140)   # grey for existing/locked boxes

WINDOW_NAME = "MetroScan AI  |  PHASE 1: Draw NEW boxes  [drag=draw | u=undo | q=done]"


def _mouse_callback(event, x, y, flags, param):
    """Track mouse drag to define new bounding boxes during Phase 1."""
    if event == cv2.EVENT_LBUTTONDOWN:
        _draw_state["drawing"] = True
        _draw_state["start"]   = (x, y)
        _draw_state["current"] = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and _draw_state["drawing"]:
        _draw_state["current"] = (x, y)
    elif event == cv2.EVENT_LBUTTONUP and _draw_state["drawing"]:
        _draw_state["drawing"] = False
        x1, y1 = _draw_state["start"]
        bx, by = min(x1, x), min(y1, y)
        bw, bh = abs(x - x1), abs(y - y1)
        if bw >= 3 and bh >= 3:
            _new_boxes.append((bx, by, bw, bh))
        _draw_state["start"]   = None
        _draw_state["current"] = None


def _render_phase1(base: np.ndarray, locked: list, scale: float) -> np.ndarray:
    """
    Render the Phase 1 drawing frame.

    Shows locked (existing) boxes in grey with their labels, and new boxes
    numbered in colour.

    Parameters
    ----------
    base   : Display-scale image.
    locked : Existing annotations loaded from JSON (original coords).
    scale  : Display scale factor, to convert original -> display coords.
    """
    frame = base.copy()

    # Draw locked (existing) boxes in grey -- convert orig coords to display
    for ann in locked:
        b = ann["bbox"]
        dx = int(b["x"] * scale)
        dy = int(b["y"] * scale)
        dw = int(b["width"]  * scale)
        dh = int(b["height"] * scale)
        cv2.rectangle(frame, (dx, dy), (dx + dw, dy + dh), _LOCKED_COLOR, 1)
        lbl = f"[SAVED] {ann['label']}"
        (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)
        cv2.rectangle(frame, (dx, dy - th - 6), (dx + tw + 4, dy), _LOCKED_COLOR, -1)
        cv2.putText(frame, lbl, (dx + 2, dy - 3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 230, 230), 1, cv2.LINE_AA)

    # Draw new boxes (numbered, coloured)
    for i, (bx, by, bw, bh) in enumerate(_new_boxes):
        col = _NEW_COLORS[i % len(_NEW_COLORS)]
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), col, 2)
        badge = f" {i+1} "
        (tw, th), _ = cv2.getTextSize(badge, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(frame, (bx, by - th - 10), (bx + tw + 2, by), col, -1)
        cv2.putText(frame, badge, (bx + 1, by - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (15, 15, 15), 2, cv2.LINE_AA)

    # In-progress drag box (white)
    if _draw_state["drawing"] and _draw_state["start"] and _draw_state["current"]:
        x1, y1 = _draw_state["start"]
        x2, y2 = _draw_state["current"]
        cv2.rectangle(frame,
                      (min(x1,x2), min(y1,y2)),
                      (max(x1,x2), max(y1,y2)),
                      (255, 255, 255), 2)

    # Bottom HUD
    h_img, w_img = frame.shape[:2]
    cv2.rectangle(frame, (0, h_img - 30), (w_img, h_img), (28, 28, 28), -1)
    hud = (f"Saved: {len(locked)}  New: {len(_new_boxes)}  |  "
           f"drag=draw  u=undo new  r=clear current  q=done")
    cv2.putText(frame, hud, (8, h_img - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1, cv2.LINE_AA)

    return frame


def _render_preview(original: np.ndarray, all_annotations: list) -> np.ndarray:
    """Render the final preview with ALL annotations (locked + new)."""
    preview = original.copy()
    colors = _NEW_COLORS + [(0, 200, 220)]  # enough for any count
    for i, ann in enumerate(all_annotations):
        col = colors[i % len(colors)]
        b = ann["bbox"]
        x, y, w, h = b["x"], b["y"], b["width"], b["height"]
        cv2.rectangle(preview, (x, y), (x + w, y + h), col, 3)
        lbl = f"[{i+1}] {ann['label']}"
        (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.60, 2)
        cv2.rectangle(preview, (x, y - th - 10), (x + tw + 6, y), col, -1)
        cv2.putText(preview, lbl, (x + 3, y - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (15, 15, 15), 2, cv2.LINE_AA)
    return preview


def _load_existing(json_path: str) -> list:
    """Load existing annotations from a .json file, or return [] if not found."""
    if not os.path.isfile(json_path):
        return []
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Expected a JSON list")
        print(f"[INFO] Loaded {len(data)} existing annotation(s) from {json_path}")
        return data
    except Exception as exc:
        print(f"[WARN] Could not load existing JSON ({exc}) -- starting fresh.",
              file=sys.stderr)
        return []


# Target maximum display height (pixels).  Auto-scale shrinks images taller
# than this; images that already fit are shown at 1.0x.
_AUTO_SCALE_MAX_HEIGHT: int = 900


def run_annotation(
    image_path: str,
    output_dir: str,
    scale: float | None = None,
    overwrite: bool = False,
) -> None:
    """
    Two-phase annotation workflow with append/merge support.

    Parameters
    ----------
    image_path : str
        Path to the real product label photo.
    output_dir : str
        Directory where .json and _preview.png are saved.
    scale : float or None
        Display scale factor (boxes saved in original pixel coords).
        Pass None (the default) to auto-fit the image so it is at most
        _AUTO_SCALE_MAX_HEIGHT pixels tall on screen.
    overwrite : bool
        If True, discard any existing .json and start fresh.
    """
    original = cv2.imread(image_path)
    if original is None:
        print(f"[ERROR] Cannot load image: {image_path}", file=sys.stderr)
        sys.exit(1)

    h_orig, w_orig = original.shape[:2]
    stem = os.path.splitext(os.path.basename(image_path))[0]
    os.makedirs(output_dir, exist_ok=True)
    out_json    = os.path.join(output_dir, f"{stem}.json")
    out_preview = os.path.join(output_dir, f"{stem}_preview.png")

    print(f"[INFO] Loaded: {image_path}  ({w_orig}x{h_orig})")

    # ------------------------------------------------------------------
    # Auto-scale: choose display scale so the window fits on screen.
    # If the caller passed an explicit scale, honour it exactly.
    # If scale is None, shrink to fit _AUTO_SCALE_MAX_HEIGHT; images that
    # already fit are shown at 1.0x (no enlargement).
    # ------------------------------------------------------------------
    if scale is None:
        auto = min(1.0, _AUTO_SCALE_MAX_HEIGHT / h_orig)
        scale = round(auto, 3)   # tidy value e.g. 0.562 -> 0.562
        if scale < 1.0:
            print(f"[INFO] Auto-scale: {scale:.3f}x  "
                  f"(image too tall for screen; target <={_AUTO_SCALE_MAX_HEIGHT}px)")
        else:
            print(f"[INFO] Auto-scale: 1.000x  (image fits screen, no scaling needed)")

    # Reset session state so repeated calls in the same process don't
    # carry over boxes from a previous image.
    global _new_boxes
    _new_boxes = []
    _draw_state["drawing"] = False
    _draw_state["start"]   = None
    _draw_state["current"] = None

    # Load existing annotations (append mode) unless --overwrite requested
    locked: list = []
    if not overwrite:
        locked = _load_existing(out_json)
    else:
        if os.path.isfile(out_json):
            print("[INFO] --overwrite set: existing annotations discarded.")

    # Build display image at the chosen scale.
    # IMPORTANT: scale is now guaranteed to be a float, never None.
    if abs(scale - 1.0) > 0.001:
        display = cv2.resize(original,
                             (int(w_orig * scale), int(h_orig * scale)),
                             interpolation=cv2.INTER_AREA)
        print(f"[INFO] Display size: {display.shape[1]}x{display.shape[0]}px  "
              f"(scale={scale:.3f}x, original={w_orig}x{h_orig})")
    else:
        display = original
        scale   = 1.0
        print(f"[INFO] Display size: {w_orig}x{h_orig}px  (scale=1.000x, no resize)")

    print()
    print("=" * 62)
    print("  PHASE 1 -- DRAWING")
    if locked:
        print(f"  {len(locked)} existing region(s) shown in GREY (already saved).")
        print("  Draw NEW boxes only -- existing ones are kept automatically.")
    else:
        print("  No existing annotations -- draw all regions from scratch.")
    print()
    print("  Controls (in the image window):")
    print("    Click + drag  : draw a new box")
    print("    u             : undo last new box")
    print("    r             : clear current drag")
    print("    q             : done drawing -> go to labelling")
    print()
    print("  Suggested labels: brand_name  mrp  net_quantity")
    print("                    ingredients  manufacturer")
    print("=" * 62)
    print()

    # ------------------------------------------------------------------
    # PHASE 1: Drawing
    # ------------------------------------------------------------------
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(WINDOW_NAME, _mouse_callback)

    while True:
        cv2.imshow(WINDOW_NAME, _render_phase1(display, locked, scale))
        key = cv2.waitKey(20) & 0xFF

        if key == ord("q"):
            break
        if key == ord("u"):
            if _new_boxes:
                _new_boxes.pop()
                print(f"[INFO] Undo -- {len(_new_boxes)} new box(es) remaining")
            else:
                print("[INFO] Nothing to undo (existing/locked boxes cannot be undone).")
        if key == ord("r"):
            _draw_state["drawing"] = False
            _draw_state["start"]   = None
            _draw_state["current"] = None

    cv2.destroyAllWindows()

    if not _new_boxes:
        if locked:
            print()
            print("[INFO] No new boxes drawn. Existing annotations unchanged.")
        else:
            print("[WARN] No boxes drawn and no existing annotations. Nothing saved.")
        return

    print()
    print(f"[OK] Drawing phase complete -- {len(_new_boxes)} new box(es) captured.")
    print()

    # ------------------------------------------------------------------
    # PHASE 2: Labelling new boxes only (terminal)
    # ------------------------------------------------------------------
    print("=" * 62)
    print("  PHASE 2 -- LABELLING NEW BOXES")
    print(f"  {len(locked)} existing box(es) keep their labels automatically.")
    print(f"  Label the {len(_new_boxes)} new box(es) below.")
    print()
    print("  Suggested labels: brand_name  mrp  net_quantity")
    print("                    ingredients  manufacturer")
    print("=" * 62)
    print()

    new_annotations = []
    for i, (bx, by, bw, bh) in enumerate(_new_boxes):
        # Convert display coords -> original image coords
        ox = int(round(bx / scale))
        oy = int(round(by / scale))
        ow = int(round(bw / scale))
        oh = int(round(bh / scale))

        prompt = f"  New box {i+1}/{len(_new_boxes)} -- [{bx},{by}  {bw}x{bh}px display]  Label: "
        try:
            label = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[WARN] Input interrupted -- saving what we have so far.")
            break

        if not label:
            print(f"  [SKIP] New box {i+1} discarded.")
            continue

        # ------------------------------------------------------------------
        # Duplicate-label conflict detection
        # Check if this label already exists in the locked (existing) boxes
        # OR in boxes we've already accepted this session.
        # ------------------------------------------------------------------
        existing_labels_locked  = [a["label"] for a in locked]
        existing_labels_session = [a["label"] for a in new_annotations]
        conflict_in_locked  = label in existing_labels_locked
        conflict_in_session = label in existing_labels_session

        if conflict_in_locked or conflict_in_session:
            source = "existing saved annotation" if conflict_in_locked else "this session"
            print(f"  [!] Label '{label}' already exists ({source}).")
            print(f"      Options:")
            print(f"        b = keep BOTH (append this new box too)")
            print(f"        r = REPLACE the old box with this new one")
            print(f"        s = SKIP this new box (discard it)")
            try:
                choice = input("      Your choice [b/r/s]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                choice = "s"

            if choice == "r":
                # Remove the conflicting entry from whichever list holds it
                if conflict_in_locked:
                    locked = [a for a in locked if a["label"] != label]
                    print(f"  [REPLACE] Removed old locked box for '{label}'.")
                if conflict_in_session:
                    new_annotations = [a for a in new_annotations if a["label"] != label]
                    print(f"  [REPLACE] Removed earlier session box for '{label}'.")
                # Fall through to append the new one below
            elif choice == "s":
                print(f"  [SKIP] New box {i+1} ('{label}') discarded.")
                continue
            else:  # 'b' or anything unrecognised -> keep both
                print(f"  [BOTH] Keeping existing box AND adding this new one for '{label}'.")
                # Fall through to append below

        new_annotations.append({
            "label": label,
            "text":  "",
            "bbox":  {"x": ox, "y": oy, "width": ow, "height": oh},
        })
        print(f"  [OK]   New box {i+1} -> [{label}]  orig: {ow}x{oh}px")

    print()

    if not new_annotations:
        print("[WARN] All new boxes were discarded. Existing annotations unchanged.")
        return

    # ------------------------------------------------------------------
    # Merge existing (locked) + new annotations
    # ------------------------------------------------------------------
    all_annotations = locked + new_annotations   # locked first preserves order

    # Pre-save confirmation summary -- lets you verify nothing was lost
    # before any file is touched.
    print()
    print("=" * 62)
    print("  PRE-SAVE SUMMARY  (please verify before file is written)")
    print("=" * 62)
    if locked:
        print(f"  KEPT ({len(locked)} existing box(es) -- unchanged):")
        for ann in locked:
            b = ann["bbox"]
            print(f"    [KEPT]  {ann['label']:<22s}  "
                  f"x={b['x']} y={b['y']} w={b['width']} h={b['height']}")
    else:
        print("  KEPT: (none -- no existing annotations were loaded)")
    print()
    print(f"  ADDED ({len(new_annotations)} new box(es)):")
    for ann in new_annotations:
        b = ann["bbox"]
        print(f"    [NEW]   {ann['label']:<22s}  "
              f"x={b['x']} y={b['y']} w={b['width']} h={b['height']}")
    print()
    print(f"  TOTAL after save: {len(all_annotations)} annotation(s)")
    print("=" * 62)
    print()

    # Write the merged file
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_annotations, f, indent=2)
    print(f"[OK] Merged annotations saved to : {out_json}")
    print(f"     ({len(locked)} kept + {len(new_annotations)} added = "
          f"{len(all_annotations)} total)")

    # Preview image with all boxes
    # Convert locked entries to the internal format for preview rendering
    preview_anns = [
        {"label": a["label"], "bbox": a["bbox"]}
        for a in all_annotations
    ]
    preview = _render_preview(original, preview_anns)
    cv2.imwrite(out_preview, preview)
    print(f"[OK] Preview image saved to       : {out_preview}")

    print()
    print("  Full annotation summary:")
    for i, ann in enumerate(all_annotations):
        b = ann["bbox"]
        tag = " [NEW]" if i >= len(locked) else "      "
        print(f"    [{i+1}]{tag} {ann['label']:<22s}  "
              f"x={b['x']} y={b['y']} w={b['width']} h={b['height']}")
    print()
    print("  Next steps:")
    print("    python run_real_photo_tests.py --verbose")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MetroScan AI -- Bbox annotation tool (append mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # First run -- draw all boxes from scratch:\n"
            "  python annotate_real_photo.py --image test_images/real_photos/label1.jpg --scale 0.6\n"
            "\n"
            "  # Second run -- add more boxes to existing annotation:\n"
            "  python annotate_real_photo.py --image test_images/real_photos/label1.jpg --scale 0.6\n"
            "\n"
            "  # Start completely fresh (discards existing JSON):\n"
            "  python annotate_real_photo.py --image test_images/real_photos/label1.jpg --overwrite"
        ),
    )
    parser.add_argument("--image",     required=True, help="Path to the label photo")
    parser.add_argument(
        "--output-dir",
        default=os.path.join("test_images", "real_photos"),
        help="Where to save .json and _preview.png (default: test_images/real_photos/)",
    )
    parser.add_argument(
        "--scale", type=float, default=None,
        help=(
            "Display scale factor, e.g. 0.5 or 0.6. "
            "Boxes are ALWAYS saved in original image coords (the inverse "
            "division happens automatically). "
            "If omitted, scale is auto-chosen so the window is at most "
            f"{_AUTO_SCALE_MAX_HEIGHT}px tall (fits most laptop screens). "
            "Pass --scale 1.0 to force full-size."
        ),
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Discard existing .json and start fresh (default: append/merge mode)",
    )
    args = parser.parse_args()
    run_annotation(args.image, args.output_dir, scale=args.scale,
                   overwrite=args.overwrite)


if __name__ == "__main__":
    main()
