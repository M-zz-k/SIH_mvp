# METROSCAN AI — Architecture Overview

## Data Flow

```
Officer uploads image(s) / CSV
        │
        ▼
┌─────────────────┐
│  Backend API     │  (FastAPI — Person 2)
│  /upload/single  │
│  /upload/bulk    │
└───────┬─────────┘
        │  calls in sequence:
        ▼
┌─────────────────┐
│  OCR Extraction  │  (PaddleOCR — Person 3)
│  extract.py      │  → returns Declarations
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│  Rule Engine     │  (Rules + Font check — Person 4)
│  validate.py     │  → returns Compliance + Tier
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│  Data & Evidence │  (Hash + PDF — Person 5)
│  evidence.py     │  → returns Evidence record
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│  Frontend        │  (React Dashboard — Person 1)
│  Results view    │  ← polls /results/{id}
└─────────────────┘
```

## Shared Data Contract

All modules communicate using the schema defined in `/shared/models.py`.
**Do not change the schema shape without a team-wide announcement.**

## Legal Reference

India's Legal Metrology (Packaged Commodities) Rules, 2011 — the rule engine
validates declarations required under these rules:
- MRP (Maximum Retail Price)
- Net Quantity
- Manufacturer name & address
- Date of manufacture / expiry / best before
