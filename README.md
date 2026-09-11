# METROSCAN AI — Integrated Platform

FastAPI backend and OCR extraction pipeline for the METROSCAN AI compliance platform. Handles auth,
request orchestration, and wires together OCR/extraction, the rule engine,
and evidence/storage.

## Quickstart

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive Swagger UI.

Run tests:
```bash
pytest
```

## How this avoids merge conflicts

Everyone works in their **own file** and imports a **shared contract**:

| Who | Owns | Never touches |
|---|---|---|
| **Dev2 (Backend)** | `app/api/routes/*.py`, `app/services/pipeline.py`, `app/core/*`, `app/main.py`, `app/models/schemas.py` | other devs' interface files |
| **Dev3 (OCR)** | `src/`, `ocr_extraction/`, `app/services/extraction_interface.py` | routes, main.py |
| **Dev4 (Rules)** | `rule_engine/`, `physical_measurement.py`, `app/services/rule_engine_interface.py` | routes, main.py |
| **Dev5 (Evidence/PDF)** | `data_evidence/`, `app/services/storage_interface.py` | routes, main.py |
| **Dev1 (Frontend)** | `frontend/` (React + Vite) | backend source code |

---

# OCR & Extraction Module (Role 3)

Located in `src/` and `ocr_extraction/`:
- `src/data_contract.py`: Shared data contract for OCR extraction results.
- `src/ocr_engine.py`: PaddleOCR wrapper with `MockOCREngine` fallback.
- `src/field_extractor.py`: Regex and pattern-based field extraction.
- `src/pipeline.py`: End-to-end OCR + extraction pipeline.
```
ocr_extraction/
├── src/
│   ├── data_contract.py     # <-- THE SHARED CONTRACT
│   ├── ocr_engine.py        # PaddleOCR wrapper (+ MockOCREngine fallback)
│   ├── field_extractor.py   # regex/spaCy field parsing
│   └── pipeline.py          # ties OCR + extraction together
├── tests/
│   └── test_field_extractor.py   # Unit tests
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
>>>>>>> origin/ocrdone1
