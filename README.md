# MetroScan AI — OCR & Extraction Module (Role 3)

Owns: **OCR integration + structured field extraction (regex/pattern rules) into the
shared data contract**, per the team's Step 2 role split (Team HexaD, SIH 2026, PS #26034).

This module takes a scanned/uploaded label image and turns it into a structured,
rule-engine-ready JSON object — nothing more. It does **not** decide compliance
(that's Role 4's rule engine) and does **not** touch the database or API routes
(that's Role 2's backend). This separation is what lets all three of you build
in parallel against the shared contract.

## What it does

```
image (jpg/png) --> OCR (PaddleOCR) --> text blocks (text + bbox + confidence)
                                              |
                                              v
                               regex / pattern extraction (+ optional spaCy NER)
                                              |
                                              v
                           LabelExtractionResult  (the shared data contract)
```

Extracted fields (mapped to Legal Metrology Rules 6 & 7 mandatory declarations):

| Field | Example |
|---|---|
| `mrp` | `199.00` |
| `unit_sale_price` | `49.75` |
| `net_quantity` (+ unit) | `250` / `g` |
| `manufacturer_name` | `Sunrise Foods Pvt. Ltd.` |
| `manufacturer_address` | `Plot 12, MIDC, Pune, Maharashtra - 411019` |
| `consumer_care` | `1800-123-4567, care@brand.com` |
| `mfg_date` | `03/2026` |
| `best_before_date` | `12 months from Mfg.` |
| `country_of_origin` | `India` |
| `batch_number` | `AB1234/26` |

Every field also carries: `found` (bool), `raw_text`, `confidence`, `bbox`
(4-point box on the image), `line_height_px` (feeds Role 4's relative
font-size heuristic directly — no need to re-run OCR), and
`extraction_method` (`regex` / `regex+ner` / `heuristic`) for audit trail.

## Project structure

```
ocr_extraction/
├── src/
│   ├── data_contract.py     # <-- THE SHARED CONTRACT. Read this first.
│   ├── ocr_engine.py        # PaddleOCR wrapper (+ MockOCREngine fallback)
│   ├── field_extractor.py   # regex/spaCy field parsing
│   └── pipeline.py          # ties OCR + extraction together
├── tests/
│   └── test_field_extractor.py   # 11 unit tests, no GPU/PaddleOCR needed
├── main.py                  # CLI
└── requirements.txt
```

## Quick start

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional, for manufacturer NER

# single label image
python main.py --image path/to/label.jpg --out result.json

# bulk folder (e.g. downloaded e-commerce listing images)
python main.py --folder path/to/images/ --out results.json
```

### Developing before PaddleOCR is installed / without real images

Every other role can build against this module **today** using the mock
engine, which returns a deterministic fake label:

```bash
python main.py --image anything.jpg --mock --out result.json
```

```python
from pipeline import process_label_image
result = process_label_image("label.jpg", force_mock=True)
print(result.model_dump_json(indent=2))
```

## Using this from the backend (Role 2)

```python
import sys
sys.path.insert(0, "ocr_extraction/src")
from pipeline import process_label_image

result = process_label_image(image_path)
# result is a pydantic model -> result.model_dump() gives you a plain dict
# ready to store in Postgres (Role 5) or hand to the rule engine (Role 4)
```

## Using this from the rule engine (Role 4)

```python
from data_contract import FieldName

mrp_field = result.get_field(FieldName.MRP)
if not mrp_field.found:
    # Rule 6/7 violation: missing mandatory declaration
    ...

for block in result.text_blocks:
    # block.line_height_px + block.bbox is everything needed for the
    # relative font-size heuristic (compare against the largest text block
    # on the same label, e.g. the brand name)
    ...
```

## Running tests

```bash
pytest tests/ -v
```

11/11 passing — covers MRP (multiple formats), net quantity (g/ml), mfg
date, consumer care, country of origin, manufacturer name + multi-line
address, batch number, missing-field handling, and a full mock-engine
end-to-end run.

## Extending

- **New field?** Add it to `FieldName` in `data_contract.py`, write a regex
  in `field_extractor.py`, wire it into `extract_fields()`, add a test.
- **Multilingual (Hindi) OCR?** `get_engine(lang="hi")` — PaddleOCR supports
  a Hindi model out of the box; regex patterns will need Devanagari
  equivalents added alongside the English ones (kept as separate patterns,
  not merged, so both remain auditable).
- **Curved/cylindrical packaging (future scope, per slide 6):** plug a
  TextSnake/DewarpNet unwarping step in front of `ocr_engine.py` — the rest
  of the pipeline doesn't need to change.
