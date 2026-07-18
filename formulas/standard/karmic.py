"""
Formula layer for natal karmic/past-life evidence.

These indices are descriptive and symbolic. They rank evidence density and
salience; they do not assert literal past-life facts.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from formulas.standard.confidence import (
    APPROXIMATE_BIRTH_TIME,
    EXACT_BIRTH_TIME,
    UNKNOWN_BIRTH_TIME,
)
from formulas.standard.contracts import KarmicEvidenceRecord, StandardFormulaResult
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.methodology_profiles import get_active_methodology_metadata

FORMULA_VERSION = "1.0.0"

MethodRegistry.register(
    method_id="karmic_carryover_index",
    category="core_standard",
    lineage_tags=["evolutionary", "karmic_symbolic", "descriptive"],
    requires_exact_time=False,
    required_data=["standard_planets", "aspects"],
    time_requirement="birth_time_optional_with_house_gating",
    formula_version=FORMULA_VERSION,
    assumptions=["symbolic_evidence_density_not_literal_past_life_proof"],
)

MethodRegistry.register(
    method_id="hidden_memory_load",
    category="core_standard",
    lineage_tags=["evolutionary", "karmic_symbolic", "twelfth_house"],
    requires_exact_time=True,
    required_data=["standard_planets", "houses"],
    time_requirement="exact_birth_time_or_reduced",
    formula_version=FORMULA_VERSION,
    assumptions=["house_dependent_score_reduced_or_withheld_without_exact_time"],
)

MethodRegistry.register(
    method_id="nodal_entanglement_rating",
    category="core_standard",
    lineage_tags=["evolutionary", "karmic_symbolic", "nodal_aspects"],
    requires_exact_time=False,
    required_data=["standard_planets", "aspects"],
    time_requirement="birth_time_optional_with_house_gating",
    formula_version=FORMULA_VERSION,
    assumptions=["nodal_aspect_density_is_symbolic_not_deterministic"],
)

MethodRegistry.register(
    method_id="present_echo_resonance",
    category="core_standard",
    lineage_tags=["evolutionary", "karmic_symbolic", "present_life_echo"],
    requires_exact_time=False,
    required_data=["standard_planets", "aspects"],
    time_requirement="birth_time_optional_with_house_gating",
    formula_version=FORMULA_VERSION,
    assumptions=["present_echo_score_requires_interpretive_review_before_report_use"],
)

MethodRegistry.register(
    method_id="retrograde_unfinished_cluster",
    category="core_standard",
    lineage_tags=["modern", "karmic_symbolic", "retrograde"],
    requires_exact_time=False,
    required_data=["standard_planets"],
    time_requirement="birth_time_optional",
    formula_version=FORMULA_VERSION,
    assumptions=["retrograde_is_not_karmic_debt"],
)


def evaluate_karmic_formulas(
    evidence_records: list[KarmicEvidenceRecord | dict[str, Any]],
    birth_time_state: str,
) -> dict[str, Any]:
    """Returns named karmic formula results plus raw family diagnostics."""
    records = [_coerce_record(record) for record in evidence_records]
    by_family = _family_scores(records)
    confidence_modifier = _confidence_modifier(birth_time_state)

    formula_specs = [
        (
            "karmic_carryover_index",
            "Karmic Carryover Index",
            {
                "south_node_axis": 1.0,
                "south_node_axis_ruler": 0.85,
                "nodal_aspect": 0.55,
                "saturn_sign": 0.2,
            },
            ["south_node_axis", "south_node_axis_ruler", "nodal_aspect"],
            "inherited_pattern_density",
        ),
        (
            "hidden_memory_load",
            "Hidden Memory Load",
            {
                "twelfth_house": 1.0,
                "twelfth_house_ruler": 0.75,
                "retrograde": 0.35,
                "pluto_house": 0.25,
            },
            ["twelfth_house", "twelfth_house_ruler", "retrograde"],
            "private_or_unconscious_carryover_density",
        ),
        (
            "nodal_entanglement_rating",
            "Nodal Entanglement Rating",
            {
                "nodal_aspect": 1.0,
                "south_node_axis_house": 0.35,
                "north_node_axis_house": 0.25,
                "south_node_axis_ruler": 0.25,
                "north_node_axis_ruler": 0.15,
            },
            ["nodal_aspect", "south_node_axis_house", "north_node_axis_house"],
            "node_network_integration",
        ),
        (
            "present_echo_resonance",
            "Present Echo Resonance",
            {
                "nodal_aspect": 0.55,
                "saturn_sign": 0.45,
                "saturn_house": 0.35,
                "pluto_sign": 0.35,
                "pluto_house": 0.3,
                "twelfth_house": 0.35,
            },
            ["nodal_aspect", "saturn_sign", "pluto_sign", "twelfth_house"],
            "visible_repetition_or_pressure_signature",
        ),
        (
            "retrograde_unfinished_cluster",
            "Retrograde Unfinished Cluster",
            {
                "retrograde": 1.0,
            },
            ["retrograde"],
            "retrograde_cluster_density",
        ),
    ]

    results: dict[str, Any] = {
        "formula_version": FORMULA_VERSION,
        "family_raw_scores": by_family,
    }
    for method_id, label, weights, driver_families, classification in formula_specs:
        results[method_id] = _build_formula_result(
            method_id=method_id,
            label=label,
            classification=classification,
            records=records,
            by_family=by_family,
            weights=weights,
            driver_families=driver_families,
            birth_time_state=birth_time_state,
            confidence_modifier=confidence_modifier,
        ).to_dict()
    return results


def _coerce_record(record: KarmicEvidenceRecord | dict[str, Any]) -> dict[str, Any]:
    if isinstance(record, KarmicEvidenceRecord):
        return record.to_dict()
    return record if isinstance(record, dict) else {}


def _family_scores(records: list[dict[str, Any]]) -> dict[str, float]:
    by_family: dict[str, float] = defaultdict(float)
    for record in records:
        if record.get("confidence") == "withheld":
            continue
        family = str(record.get("family") or "")
        if not family:
            continue
        by_family[family] += _safe_float(record.get("score"))
    return {key: round(value, 4) for key, value in sorted(by_family.items())}


def _build_formula_result(
    *,
    method_id: str,
    label: str,
    classification: str,
    records: list[dict[str, Any]],
    by_family: dict[str, float],
    weights: dict[str, float],
    driver_families: list[str],
    birth_time_state: str,
    confidence_modifier: float,
) -> StandardFormulaResult:
    methodology = get_active_methodology_metadata()
    raw_score = _weighted_family_score(by_family, weights)
    adjusted_score = round(raw_score * confidence_modifier, 4)
    relevant_records = [
        record for record in records
        if record.get("family") in weights and record.get("confidence") != "withheld"
    ]
    withheld_records = [
        record for record in records
        if record.get("family") in weights and record.get("confidence") == "withheld"
    ]
    drivers = _top_drivers(relevant_records, driver_families)
    missing_inputs = sorted(
        {
            item
            for record in withheld_records
            for item in _as_list(record.get("missing_inputs"))
        }
    )
    assumptions = [
        "descriptive_symbolic_index_not_literal_past_life_proof",
        "score_supports_ranking_not_truth_claim",
    ]
    if birth_time_state == UNKNOWN_BIRTH_TIME and withheld_records:
        assumptions.append("time_sensitive_evidence_withheld_from_score")
    elif birth_time_state == APPROXIMATE_BIRTH_TIME:
        assumptions.append("approximate_birth_time_confidence_reduction_applied")

    return StandardFormulaResult(
        id=method_id,
        label=label,
        method_status="backend_computation",
        tradition_tags=["evolutionary", "karmic_symbolic", "tropical_whole"],
        score=adjusted_score,
        raw_score=raw_score,
        theoretical_max=1.0,
        tier=_tier(adjusted_score),
        visibility_state="internal_only",
        classification=classification,
        drivers=drivers,
        supporting_factors=sorted(
            family for family, value in by_family.items()
            if family in weights and value > 0
        ),
        challenging_factors=[],
        components={
            "family_weights": weights,
            "family_scores": {family: by_family.get(family, 0.0) for family in weights},
            "confidence_modifier": confidence_modifier,
            "birth_time_state": birth_time_state,
            "withheld_record_count": len(withheld_records),
            "raw_record_count": len(relevant_records) + len(withheld_records),
        },
        missing_inputs=missing_inputs,
        assumptions=assumptions,
        formula_version=FORMULA_VERSION,
        methodology_id=methodology["id"],
        methodology_label=methodology["label"],
        zodiac=methodology["zodiac"],
        house_system=methodology["house_system"],
        audit_data={
            "source": "formulas.standard.karmic.evaluate_karmic_formulas",
            "claim_boundary": "symbolic_evidence_density",
            "literal_past_life_claim": False,
            "source_record_ids": [
                str(record.get("id")) for record in relevant_records[:12]
            ],
        },
    )


def _weighted_family_score(by_family: dict[str, float], weights: dict[str, float]) -> float:
    weighted_total = sum(by_family.get(family, 0.0) * weight for family, weight in weights.items())
    max_expected = max(1.0, sum(weights.values()) * 0.75)
    return round(max(0.0, min(1.0, weighted_total / max_expected)), 4)


def _confidence_modifier(birth_time_state: str) -> float:
    return {
        EXACT_BIRTH_TIME: 1.0,
        APPROXIMATE_BIRTH_TIME: 0.72,
        UNKNOWN_BIRTH_TIME: 0.45,
    }.get(birth_time_state, 0.6)


def _top_drivers(records: list[dict[str, Any]], driver_families: list[str]) -> list[str]:
    ranked = sorted(
        [
            record for record in records
            if record.get("family") in driver_families
        ],
        key=lambda record: (-_safe_float(record.get("score")), str(record.get("id"))),
    )
    drivers: list[str] = []
    for record in ranked[:6]:
        for driver in _as_list(record.get("drivers")):
            text = str(driver).strip()
            if text and text not in drivers:
                drivers.append(text)
    return drivers[:8]


def _tier(score: float) -> str:
    if score >= 0.75:
        return "DOMINANT"
    if score >= 0.45:
        return "PRESENT"
    if score > 0.0:
        return "SUBTLE"
    return "WITHHELD"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value:
        return [value]
    return []
