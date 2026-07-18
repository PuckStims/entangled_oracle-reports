"""
Backend karmic/past-life evidence extraction.

This module produces computation payloads only. It does not select prose,
assemble reports, or claim literal past-life facts.
"""

from __future__ import annotations

from typing import Any

from formulas.standard.confidence import (
    APPROXIMATE_BIRTH_TIME,
    EXACT_BIRTH_TIME,
    UNKNOWN_BIRTH_TIME,
)
from formulas.standard.contracts import KarmicComputationPayload, KarmicEvidenceRecord
from formulas.standard.dignity import TRADITIONAL_DOMICILE
from formulas.standard.karmic import evaluate_karmic_formulas
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from selectors.utils import get_body_data, get_body_house

SCHEMA_VERSION = "karmic.v1"
FORMULA_VERSION = "1.0.0"

NODE_ASPECT_BODIES = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Pluto", "Chiron")
RETROGRADE_BODIES = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron")


def build_karmic_payload(natal_payload: dict) -> dict[str, Any]:
    """Returns a versioned, auditable karmic computation payload."""
    methodology = get_active_methodology_metadata()
    birth_time_state = _birth_time_state(natal_payload)
    evidence_records = _build_evidence_records(natal_payload, birth_time_state)
    missing_inputs = sorted(
        {
            item
            for record in evidence_records
            for item in record.missing_inputs
        }
    )
    assumptions = _chart_assumptions(natal_payload, birth_time_state)

    payload = KarmicComputationPayload(
        schema_version=SCHEMA_VERSION,
        methodology={
            "id": methodology["id"],
            "label": methodology["label"],
            "zodiac": methodology["zodiac"],
            "house_system": methodology["house_system"],
            "method_family": "natal_karmic_symbolic",
            "formula_version": FORMULA_VERSION,
            "literal_past_life_claims": False,
        },
        input_confidence={
            "birth_time_state": birth_time_state,
            "houses_angles_eligible": birth_time_state == EXACT_BIRTH_TIME,
            "time_sensitive_claim_policy": (
                "available"
                if birth_time_state == EXACT_BIRTH_TIME
                else "withheld_or_reduced"
            ),
        },
        chart_references=_chart_references(natal_payload),
        evidence_records=[record.to_dict() for record in evidence_records],
        scores=evaluate_karmic_formulas(evidence_records, birth_time_state),
        routing_tags=_routing_tags(evidence_records),
        missing_inputs=missing_inputs,
        assumptions=assumptions,
        audit={
            "source": "engine.karmic_engine.build_karmic_payload",
            "schema_version": SCHEMA_VERSION,
            "formula_version": FORMULA_VERSION,
            "record_count": len(evidence_records),
            "computed_from": "natal_payload",
        },
    )
    return payload.to_dict()


def _birth_time_state(payload: dict) -> str:
    profile = payload.get("user_profile", {})
    if bool(payload.get("simple_mode") or profile.get("simple_mode")):
        return UNKNOWN_BIRTH_TIME
    state = (
        profile.get("birth_time_state")
        or profile.get("birth_time_confidence")
        or EXACT_BIRTH_TIME
    )
    if state in {EXACT_BIRTH_TIME, APPROXIMATE_BIRTH_TIME, UNKNOWN_BIRTH_TIME}:
        return state
    if "approximate" in str(state).lower():
        return APPROXIMATE_BIRTH_TIME
    if "unknown" in str(state).lower():
        return UNKNOWN_BIRTH_TIME
    return EXACT_BIRTH_TIME


def _build_evidence_records(payload: dict, birth_time_state: str) -> list[KarmicEvidenceRecord]:
    records: list[KarmicEvidenceRecord] = []
    records.extend(_node_axis_records(payload, birth_time_state))
    records.extend(_nodal_aspect_records(payload))
    records.extend(_twelfth_house_records(payload, birth_time_state))
    records.extend(_saturn_pluto_records(payload, birth_time_state))
    records.extend(_retrograde_records(payload))
    return sorted(records, key=lambda record: record.id)


def _node_axis_records(payload: dict, birth_time_state: str) -> list[KarmicEvidenceRecord]:
    records = []
    south_node = get_body_data(payload, "South_Node")
    north_node = get_body_data(payload, "North_Node")
    for node_name, node_data, family, label in (
        ("South_Node", south_node, "south_node_axis", "South Node inherited pattern"),
        ("North_Node", north_node, "north_node_axis", "North Node release direction"),
    ):
        if not node_data:
            records.append(_missing_record(family, node_name, [node_name]))
            continue
        records.append(
            KarmicEvidenceRecord(
                id=f"{family}:sign:{node_data.get('sign', 'unknown')}",
                family=family,
                label=label,
                method_tags=["core", "karmic_symbolic", "evolutionary"],
                confidence="high",
                score=0.7,
                drivers=[node_name, str(node_data.get("sign", ""))],
                audit_data={
                    "body": node_name,
                    "sign": node_data.get("sign"),
                    "longitude": node_data.get("longitude"),
                },
            )
        )
        records.append(
            _house_record(
                family=f"{family}_house",
                label=f"{label} house",
                body=node_name,
                body_data=node_data,
                birth_time_state=birth_time_state,
                base_score=0.55,
            )
        )
        ruler = TRADITIONAL_DOMICILE.get(str(node_data.get("sign") or ""))
        if ruler:
            ruler_data = get_body_data(payload, ruler)
            records.append(
                KarmicEvidenceRecord(
                    id=f"{family}:ruler:{ruler}",
                    family=f"{family}_ruler",
                    label=f"{label} ruler",
                    method_tags=["traditional", "karmic_symbolic"],
                    confidence="high" if ruler_data else "low",
                    score=0.45 if ruler_data else 0.0,
                    drivers=[node_name, ruler],
                    missing_inputs=[] if ruler_data else [ruler],
                    audit_data={
                        "node": node_name,
                        "node_sign": node_data.get("sign"),
                        "traditional_ruler": ruler,
                        "ruler_sign": ruler_data.get("sign") if ruler_data else None,
                        "ruler_house": ruler_data.get("house") if ruler_data else None,
                    },
                )
            )
    return records


def _nodal_aspect_records(payload: dict) -> list[KarmicEvidenceRecord]:
    records = []
    for aspect in payload.get("aspects", []):
        body_a = aspect.get("body_1")
        body_b = aspect.get("body_2")
        pair = {body_a, body_b}
        if "South_Node" not in pair and "North_Node" not in pair:
            continue
        other = body_b if body_a in {"South_Node", "North_Node"} else body_a
        if other not in NODE_ASPECT_BODIES:
            continue
        node = body_a if body_a in {"South_Node", "North_Node"} else body_b
        orb = float(aspect.get("orb", 10.0))
        strength = round(max(0.0, (10.0 - orb) / 10.0), 4)
        records.append(
            KarmicEvidenceRecord(
                id=f"nodal_aspect:{node}:{other}:{aspect.get('aspect')}",
                family="nodal_aspect",
                label="Nodal aspect",
                method_tags=["core", "karmic_symbolic"],
                confidence="high",
                score=round(0.35 + strength * 0.45, 4),
                drivers=[node, other, str(aspect.get("aspect"))],
                audit_data={
                    "node": node,
                    "other_body": other,
                    "aspect": aspect.get("aspect"),
                    "orb": aspect.get("orb"),
                    "angle": aspect.get("angle"),
                },
            )
        )
    return records


def _twelfth_house_records(payload: dict, birth_time_state: str) -> list[KarmicEvidenceRecord]:
    records = []
    for body_name, body_data in payload.get("standard_planets", {}).items():
        if body_name in {"North_Node", "South_Node"} or not isinstance(body_data, dict):
            continue
        if body_data.get("house") != 12:
            continue
        records.append(
            _time_sensitive_record(
                id=f"twelfth_house:{body_name}",
                family="twelfth_house",
                label="12th-house carryover indicator",
                birth_time_state=birth_time_state,
                base_score=0.48,
                drivers=[body_name, "12th house"],
                audit_data={
                    "body": body_name,
                    "sign": body_data.get("sign"),
                    "house": body_data.get("house"),
                    "longitude": body_data.get("longitude"),
                },
            )
        )
    house_12 = (payload.get("houses") or {}).get("House_12", {})
    ruler = TRADITIONAL_DOMICILE.get(str(house_12.get("sign") or ""))
    if ruler:
        ruler_data = get_body_data(payload, ruler)
        records.append(
            _time_sensitive_record(
                id=f"twelfth_house_ruler:{ruler}",
                family="twelfth_house_ruler",
                label="12th-house ruler",
                birth_time_state=birth_time_state,
                base_score=0.36,
                drivers=[ruler, "12th house"],
                audit_data={
                    "house_sign": house_12.get("sign"),
                    "traditional_ruler": ruler,
                    "ruler_sign": ruler_data.get("sign") if ruler_data else None,
                    "ruler_house": ruler_data.get("house") if ruler_data else None,
                },
            )
        )
    return records


def _saturn_pluto_records(payload: dict, birth_time_state: str) -> list[KarmicEvidenceRecord]:
    records = []
    for body_name, label, score in (
        ("Saturn", "Saturn karmic pressure", 0.5),
        ("Pluto", "Pluto soul-pressure marker", 0.42),
    ):
        body_data = get_body_data(payload, body_name)
        if not body_data:
            records.append(_missing_record(body_name.lower(), body_name, [body_name]))
            continue
        records.append(
            KarmicEvidenceRecord(
                id=f"{body_name.lower()}:sign:{body_data.get('sign', 'unknown')}",
                family=f"{body_name.lower()}_sign",
                label=label,
                method_tags=["core", "karmic_symbolic"],
                confidence="high",
                score=score,
                drivers=[body_name, str(body_data.get("sign", ""))],
                audit_data={
                    "body": body_name,
                    "sign": body_data.get("sign"),
                    "longitude": body_data.get("longitude"),
                },
            )
        )
        records.append(
            _house_record(
                family=f"{body_name.lower()}_house",
                label=f"{label} house",
                body=body_name,
                body_data=body_data,
                birth_time_state=birth_time_state,
                base_score=score * 0.8,
            )
        )
    return records


def _retrograde_records(payload: dict) -> list[KarmicEvidenceRecord]:
    records = []
    for body_name in RETROGRADE_BODIES:
        body_data = get_body_data(payload, body_name)
        if not body_data or not body_data.get("retrograde"):
            continue
        records.append(
            KarmicEvidenceRecord(
                id=f"retrograde:{body_name}",
                family="retrograde",
                label="Retrograde carryover indicator",
                method_tags=["modern", "karmic_symbolic"],
                confidence="high",
                score=0.28,
                drivers=[body_name, "retrograde"],
                assumptions=["retrograde_is_symbolic_carryover_marker_not_debt"],
                audit_data={
                    "body": body_name,
                    "sign": body_data.get("sign"),
                    "house": body_data.get("house"),
                    "speed": body_data.get("speed"),
                },
            )
        )
    return records


def _house_record(
    *,
    family: str,
    label: str,
    body: str,
    body_data: dict,
    birth_time_state: str,
    base_score: float,
) -> KarmicEvidenceRecord:
    return _time_sensitive_record(
        id=f"{family}:{body}:house:{body_data.get('house', 'unknown')}",
        family=family,
        label=label,
        birth_time_state=birth_time_state,
        base_score=base_score,
        drivers=[body, f"house {body_data.get('house')}"],
        audit_data={
            "body": body,
            "house": body_data.get("house"),
            "sign": body_data.get("sign"),
            "longitude": body_data.get("longitude"),
        },
    )


def _time_sensitive_record(
    *,
    id: str,
    family: str,
    label: str,
    birth_time_state: str,
    base_score: float,
    drivers: list[str],
    audit_data: dict[str, Any],
) -> KarmicEvidenceRecord:
    if birth_time_state == UNKNOWN_BIRTH_TIME:
        return KarmicEvidenceRecord(
            id=id,
            family=family,
            label=label,
            method_tags=["core", "karmic_symbolic"],
            claim_level="technical",
            confidence="withheld",
            birth_time_sensitivity="exact_time_required",
            score=0.0,
            drivers=drivers,
            missing_inputs=["birth_time"],
            assumptions=["noon_placeholder_not_valid_for_house_or_angle_claims"],
            audit_data={**audit_data, "birth_time_state": birth_time_state},
        )
    confidence = "moderate" if birth_time_state == APPROXIMATE_BIRTH_TIME else "high"
    score = base_score * (0.65 if birth_time_state == APPROXIMATE_BIRTH_TIME else 1.0)
    assumptions = ["approximate_birth_time_reduces_house_confidence"] if birth_time_state == APPROXIMATE_BIRTH_TIME else []
    return KarmicEvidenceRecord(
        id=id,
        family=family,
        label=label,
        method_tags=["core", "karmic_symbolic"],
        confidence=confidence,
        birth_time_sensitivity="exact_time_sensitive",
        score=round(score, 4),
        drivers=drivers,
        assumptions=assumptions,
        audit_data={**audit_data, "birth_time_state": birth_time_state},
    )


def _missing_record(family: str, label: str, missing_inputs: list[str]) -> KarmicEvidenceRecord:
    return KarmicEvidenceRecord(
        id=f"missing:{family}",
        family=family,
        label=label,
        method_tags=["core", "karmic_symbolic"],
        claim_level="technical",
        confidence="withheld",
        score=0.0,
        missing_inputs=missing_inputs,
    )


def _routing_tags(records: list[KarmicEvidenceRecord]) -> list[str]:
    tags = set()
    for record in records:
        if record.confidence == "withheld":
            continue
        tags.add(record.family)
        for driver in record.drivers:
            tags.add(_slug(driver))
    return sorted(tag for tag in tags if tag)


def _slug(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_")


def _chart_references(payload: dict) -> dict[str, Any]:
    profile = payload.get("user_profile", {})
    return {
        "queried_location": profile.get("queried_location"),
        "resolved_location": profile.get("resolved_location"),
        "timezone": profile.get("timezone"),
        "utc_datetime": profile.get("utc_datetime"),
        "julian_day": profile.get("julian_day"),
        "south_node": _body_reference(payload, "South_Node"),
        "north_node": _body_reference(payload, "North_Node"),
        "saturn": _body_reference(payload, "Saturn"),
        "pluto": _body_reference(payload, "Pluto"),
    }


def _body_reference(payload: dict, body: str) -> dict[str, Any]:
    data = get_body_data(payload, body)
    return {
        "body": body,
        "sign": data.get("sign"),
        "house": data.get("house"),
        "longitude": data.get("longitude"),
        "retrograde": data.get("retrograde"),
    }


def _chart_assumptions(payload: dict, birth_time_state: str) -> list[str]:
    assumptions = ["literal_past_life_claims_are_out_of_scope"]
    if birth_time_state == UNKNOWN_BIRTH_TIME:
        assumptions.append("simple_mode_uses_noon_placeholder_for_planet_math_only")
    elif birth_time_state == APPROXIMATE_BIRTH_TIME:
        assumptions.append("approximate_birth_time_reduces_house_angle_confidence")
    if get_body_house(payload, "South_Node") == 0:
        assumptions.append("south_node_house_unavailable")
    return assumptions
