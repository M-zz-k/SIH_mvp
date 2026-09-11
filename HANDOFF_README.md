# MetroScan AI — Person 4 Compliance Modules
## Integration Handoff Document

**Author:** Person 4 of 6  
**Last updated:** 2026-09-11  
**Validated on:** Real label photo (`label1.jpg`, 1204x1600 px)

---

## What Was Built

Person 4 delivers **two independent compliance checks** combined into one
integration point.

| Module | Responsibility |
|---|---|
| `physical_measurement.py` | Font-size heuristic -- checks that each mandatory declaration is visually large enough relative to the reference (tallest) text on the label |
| `rule_engine.py` | Declaration rule engine -- checks that each declaration is present (non-empty), passes a format regex, and was extracted with sufficient OCR confidence |
| `combine_checks.py` | **Integration wrapper** -- calls both modules and merges into one result dict. **This is the only file you need to import.** |

> Do not call `physical_measurement.py` or `rule_engine.py` directly.
> Use `combine_checks.check_label_declaration()` exclusively.

---

## Quick Start

```python
from combine_checks import check_label_declaration

result = check_label_declaration(
    field_data   = {"field": "mrp", "text": "Rs. 30.00 incl. of all taxes", "confidence": 0.92},
    text_regions = [... all annotated regions from the label ...],
)

print(result["overall_status"])   # "likely_compliant" | "needs_review" | "likely_violation"
```

---

## Function Signature

```python
def check_label_declaration(
    field_data:   dict,
    text_regions: list[dict],
) -> dict:
```

### Parameter: `field_data`

The OCR extraction result for **one declaration field**.

```python
{
    "field":      str,    # field name -- one of the four below
    "text":       str,    # extracted text from OCR
    "confidence": float   # OCR confidence score, 0.0-1.0
}
```

**Supported field names:**

| `field` value | What it represents |
|---|---|
| `"mrp"` | Maximum Retail Price -- must contain Rs/rupee symbol + a number |
| `"net_quantity"` | Net weight/volume -- must contain a number + unit (g, kg, ml, l, pcs ...) |
| `"manufacturer"` | Manufacturer name -- must contain at least two consecutive letters |
| `"date_declaration"` | Best-before / expiry -- must match a date pattern or keyword (best before, mfg, exp, use by ...) |

Missing keys, `None` values, and out-of-range confidence are all handled
gracefully -- the function never raises.

---

### Parameter: `text_regions`

All annotated text bounding boxes from the label. Used by the font-size
module to find the tallest text (reference baseline) and the declaration height.

```python
[
    {
        "label": str,   # field name -- same vocabulary as field_data["field"]
        "text":  str,   # OCR text (may be empty)
        "bbox": {
            "x":      int,   # left edge, original image pixels
            "y":      int,   # top edge, original image pixels
            "width":  int,   # box width
            "height": int    # box height -- what the font check measures
        }
    },
    ...
]
```

The list must include a region whose bbox height is the tallest on the label
(typically the brand name, annotated as `"reference"`). This becomes the
reference denominator for the font-size ratio. The tallest height is picked
automatically -- no special label name required.

---

## Return Value

```python
{
    "field": str,          # the declaration field name
    "value": str,          # the text that was evaluated (normalised)

    "rule_check": {
        "present":      bool,        # True if text is non-empty
        "format_valid": bool,        # True if text matches the format regex
        "status":       str          # tier string
    },

    "font_check": {
        "ratio":  float | None,      # declaration height / reference height
                                     # None if the font check could not run
        "status": str                # tier string
    },

    "overall_status": str            # worst-wins across both sub-checks
}
```

Key names are fixed -- do not rename them.

### Real results from label1.jpg (validation run)

| field | ratio | rule_check | font_check | overall_status |
|---|---|---|---|---|
| `net_quantity` | 0.710 | likely_compliant | likely_compliant | **likely_compliant** |
| `mrp` | 0.460 | likely_compliant | likely_compliant | **likely_compliant** |
| `ingredients` | 0.270 | likely_compliant | likely_compliant | **likely_compliant** |

---

## Status Values and What To Do With Them

All three status fields use the same three-tier vocabulary.

### `"likely_compliant"`
Text content and visual font size both look correct.  
**No action required.** Pass this declaration in the final report.

### `"needs_review"`
Something is uncertain -- low OCR confidence, borderline font size, or an
inconclusive format check.  
**Flag for manual review.** Do not auto-pass or auto-fail.
Route to a human inspector or display a warning in the UI.

### `"likely_violation"`
Text is missing entirely, or the font is clearly too small.  
**Flag as a compliance issue.** Surface to the user with a clear violation
message. Do not pass in the final report.

### `overall_status` -- "worst wins" logic

A single failing sub-check is NOT hidden by the other one passing:

```
either sub-check == "likely_violation"  ->  overall = "likely_violation"
either sub-check == "needs_review"      ->  overall = "needs_review"
both sub-checks  == "likely_compliant"  ->  overall = "likely_compliant"
```

---

## Calling in a Loop (All Four Declarations)

```python
from combine_checks import check_label_declaration

# field_data list comes from your OCR / extraction module
extractions = [
    {"field": "mrp",              "text": "Rs. 30.00",           "confidence": 0.92},
    {"field": "net_quantity",     "text": "38.5 g",              "confidence": 0.91},
    {"field": "manufacturer",     "text": "ABC Foods Pvt. Ltd.", "confidence": 0.88},
    {"field": "date_declaration", "text": "Best Before: 12/2026","confidence": 0.90},
]

# text_regions comes from your bounding-box / annotation module
text_regions = [...]   # all regions on this label, including the reference

results = [
    check_label_declaration(fd, text_regions)
    for fd in extractions
]

for r in results:
    print(r["field"], r["font_check"]["ratio"], r["overall_status"])
```

---

## Running the Tests

No extra dependencies -- standard library + `opencv-python` + `numpy`.

```powershell
# Rule engine -- 35 unit tests
python -X utf8 test_rule_engine.py

# Integration wrapper -- 16 integration tests + 10 _worst_status unit checks
python -X utf8 test_combine_checks.py

# Font-size heuristic on real label photos
python -X utf8 run_real_photo_tests.py --verbose
```

All three commands exit with code `0` when every test passes.

Note: stderr lines like `[check_format] WARNING: unknown field ...` during
the edge-case tests are intentional -- they verify the warning path works.

---

## Error Handling Contract

`check_label_declaration()` never raises an exception.

| Input failure scenario | Behaviour |
|---|---|
| `field_data` is `{}` or missing keys | Defaults: `text=""`, `confidence=0.0` |
| `"text"` is `None` | Treated as absent -> `rule_check.status = "likely_violation"` |
| `"confidence"` is `None` | Treated as `0.0` -> routed to `"needs_review"` |
| `text_regions` is `[]` | Font check -> `"needs_review"`, `ratio=None` |
| Declaration label not in `text_regions` | Font check -> `"needs_review"`, `ratio=None` |
| Unknown `"field"` name | Format check returns `False` -> `"needs_review"` |
| Unexpected exception in either sub-check | Returns `"needs_review"`, warning to stderr |

---

## File Map

```
metroscan-physical-measurement/
|-- combine_checks.py          <- import this (integration entry point)
|-- rule_engine.py             <- presence + format + confidence logic
|-- physical_measurement.py    <- font-size heuristic logic
|-- annotate_real_photo.py     <- tool for drawing bounding boxes on photos
|-- run_real_photo_tests.py    <- batch font-size validation on real photos
|-- test_combine_checks.py     <- 16 integration tests
|-- test_rule_engine.py        <- 35 unit tests
|-- HANDOFF_README.md          <- this document
`-- test_images/
    `-- real_photos/
        |-- label1.jpg         <- validated test image
        `-- label1.json        <- ground-truth annotations
```

---

## Open Questions Before You Integrate

1. **Confidence scale:** `"confidence"` is expected as a float in `[0.0, 1.0]`.
   If your OCR module outputs 0-100 percentages, divide by 100 before passing in.

2. **Confidence threshold:** the default is `0.6`. To override globally, pass
   `confidence_threshold=<value>` to `check_label_declaration()`. Talk to
   Person 4 about what threshold fits your OCR engine.

3. **Additional fields:** to add new declaration types (e.g. `"fssai_no"`),
   add a regex pattern to `FIELD_PATTERNS` at the top of `rule_engine.py`.
   No other code changes are needed.
