# MetroScan AI — Physical Measurement Module

> **Module owner:** Person 4  
> **Stack:** Python 3.x + OpenCV (opencv-contrib-python)

---

## Quick Start (tonight — synthetic)

```bash
pip install opencv-contrib-python numpy

# 1. Generate the synthetic test image
python generate_synthetic_test.py

# 2. Run the full pipeline + debug viz (use the bbox printed by step 1)
python debug_visualize.py --image test_images/synthetic_test.png --bbox 400,270,180,15

# 3. Check the annotated output
#    output/debug_visualizations/synthetic_test_debug.png
```

---

## Quick Start (tomorrow — real printed photo)

```bash
python debug_visualize.py \
  --image /path/to/real_photo.jpg \
  --bbox <x>,<y>,<width>,<height> \
  --marker-size 38.5          # <-- use your ruler measurement here
```

---

## 🔧 Swapping synthetic → real `marker_size_mm`

The **only thing you need to change** when you have a ruler measurement is the
physical size constant. You have two options:

### Option A — CLI flag (no code change needed)
```bash
python debug_visualize.py --image photo.jpg --bbox x,y,w,h --marker-size 38.5
```
Pass the ruler-measured value (in mm) to `--marker-size`.  
The pipeline will use it automatically.

### Option B — Update the module constant (for the shared integration)
Open `physical_measurement.py`, find line:
```python
MARKER_SIZE_MM: float = 40.0   # Physical printed size of the ArUco marker
```
Change `40.0` to your actual ruler measurement, e.g.:
```python
MARKER_SIZE_MM: float = 38.5   # Confirmed with ruler 2026-09-10
```
After this change, all calls to `measure_mrp_font_height(...)` that don't
pass `marker_size_mm` explicitly will automatically use the new value.

> **Why does this matter?**  
> Every 1 mm error in the marker size causes a proportional error in ALL
> measurements. At 40 mm nominal, a 2 mm print shrinkage means a ~5% scale
> error — which at a 3 mm font height would read as 2.85 mm instead of 3 mm.
> Always measure with a ruler before the final demo.

---

## Team Integration API

```python
from physical_measurement import measure_mrp_font_height

result = measure_mrp_font_height(
    image_path="photo.jpg",
    mrp_bbox={"x": 320, "y": 460, "width": 200, "height": 18},
    # marker_size_mm=40.0,   # optional override
    # required_mm=2.5,       # optional override
)

# result shape (fixed contract — do NOT rename fields):
# {
#   "field":       "mrp_font_height",
#   "detected_mm": 3.142,        # or null if marker not found
#   "required_mm": 2.5,
#   "status":      "pass"        # "pass" | "fail" | "not_detected"
# }
```

---

## File Map

| File | Purpose |
|------|---------|
| `physical_measurement.py` | Core module — import this in integration |
| `generate_synthetic_test.py` | Generates noise-free test image + prints expected values |
| `debug_visualize.py` | Visualizer — run on any image to inspect pipeline |
| `test_images/` | Synthetic test images |
| `output/debug_visualizations/` | Annotated debug output images |
| `assets/aruco_marker_40mm.png` | Pre-generated ArUco marker (ID 23, DICT_4X4_50) |

---

## Assumptions & MVP limitations

- Moderate camera tilt is handled (averaging all 4 marker sides).
- Full 3D pose / homography correction is **out of scope** for this MVP.
- One marker per frame assumed; if multiple exist, ID 23 is used.
- No ML models — classical CV only for speed and simplicity.
