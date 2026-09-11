"""
INTERFACE OWNED BY: Dev4 (rule engine & font-heuristic developer)

Contract: run_rule_engine(extraction: ExtractionResult) -> RuleEngineResult

HOW TO INTEGRATE (Dev4, read this):
  1. Do NOT touch api/routes/*.py or main.py.
  2. Replace the body of `run_rule_engine` below with your deterministic
     rule checks (presence/format/completeness against LMR 2011) and the
     relative font-size heuristic (declaration bbox height / largest_text_bbox
     height from the ExtractionResult).
  3. Every field in extraction.fields must get a verdict in field_verdicts.
  4. overall_tier = the worst tier across all fields (LIKELY_VIOLATION beats
     NEEDS_REVIEW beats LIKELY_COMPLIANT). Any field with confidence < 0.75
     should never be marked LIKELY_COMPLIANT — route it to NEEDS_REVIEW,
     per the project's "low-confidence extractions always go to the middle
     tier" rule.
  5. Keep your rule definitions in a versioned JSON/dict (rule_set_version
     field) so the citation stays auditable.
  6. Test locally with: `python -m app.services.rule_engine_interface`

Until you push your version, this stub applies simple presence/confidence
checks so the pipeline is demoable end-to-end today.
"""
from app.models.schemas import (
    ExtractionResult,
    RuleEngineResult,
    RuleViolation,
    FontHeuristicResult,
    VerdictTier,
)

CONFIDENCE_REVIEW_THRESHOLD = 0.75
RULE_SET_VERSION = "lmr2011-v0.1-mock"

TIER_SEVERITY = {
    VerdictTier.LIKELY_COMPLIANT: 0,
    VerdictTier.NEEDS_REVIEW: 1,
    VerdictTier.LIKELY_VIOLATION: 2,
}


def _worst_tier(tiers: list[VerdictTier]) -> VerdictTier:
    if not tiers:
        return VerdictTier.NEEDS_REVIEW
    return max(tiers, key=lambda t: TIER_SEVERITY[t])


def run_rule_engine(extraction: ExtractionResult) -> RuleEngineResult:
    field_verdicts: dict[str, VerdictTier] = {}
    violations: list[RuleViolation] = []
    font_heuristics: list[FontHeuristicResult] = []

    for f in extraction.fields:
        # ---- MOCK RULE LOGIC (replace with real LMR 2011 checks) ----
        if not f.parsed_value:
            tier = VerdictTier.LIKELY_VIOLATION
            violations.append(
                RuleViolation(
                    rule_id=f"LMR2011-missing-{f.field_name}",
                    field_name=f.field_name,
                    description=f"Mandatory declaration '{f.field_name}' not found on label.",
                    citation="Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6",
                    tier=tier,
                )
            )
        elif f.confidence < CONFIDENCE_REVIEW_THRESHOLD:
            tier = VerdictTier.NEEDS_REVIEW
        else:
            tier = VerdictTier.LIKELY_COMPLIANT

        field_verdicts[f.field_name] = tier

        # ---- MOCK font-size heuristic on net_quantity/mrp only ----
        if f.field_name in ("net_quantity", "mrp") and f.bounding_box and extraction.largest_text_bbox:
            ratio = f.bounding_box.height / max(extraction.largest_text_bbox.height, 1)
            heuristic_tier = (
                VerdictTier.LIKELY_VIOLATION if ratio < 0.3
                else VerdictTier.NEEDS_REVIEW if ratio < 0.5
                else VerdictTier.LIKELY_COMPLIANT
            )
            font_heuristics.append(
                FontHeuristicResult(
                    field_name=f.field_name,
                    declaration_height_px=f.bounding_box.height,
                    reference_height_px=extraction.largest_text_bbox.height,
                    ratio=round(ratio, 3),
                    tier=heuristic_tier,
                )
            )

    overall = _worst_tier(list(field_verdicts.values()) + [h.tier for h in font_heuristics])

    return RuleEngineResult(
        image_id=extraction.image_id,
        rule_set_version=RULE_SET_VERSION,
        field_verdicts=field_verdicts,
        violations=violations,
        font_heuristics=font_heuristics,
        overall_tier=overall,
    )


if __name__ == "__main__":
    from app.services.extraction_interface import run_extraction

    extraction = run_extraction("sample_label.jpg")
    result = run_rule_engine(extraction)
    print(result.model_dump_json(indent=2))
