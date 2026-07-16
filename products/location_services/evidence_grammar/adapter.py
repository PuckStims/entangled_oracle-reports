"""
Adapter from LocationEvidenceRecord to normalized Location Services evidence.

Phase 1 of the locational grammar upgrade creates an inspectable middle layer
between calculation and report prose. The adapter consumes existing evidence
records without mutating them and emits JSON-like dictionaries with stable IDs,
technical source factors, bounded interpretation tags, and explicit unavailable
notes for future methods.
"""
from __future__ import annotations

import copy
from typing import Any


GRAMMAR_VERSION = "location_services_evidence_grammar_v0.1.0"

REQUIRED_ITEM_FIELDS = {
    "evidence_id",
    "family",
    "subject",
    "interface",
    "strength",
    "confidence",
    "themes",
    "supports",
    "costs",
    "source_factors",
    "calculation_status",
    "claim_boundary",
}

_ANGLE_INTERFACES = {
    "Ascendant": "asc",
    "Descendant": "dc",
    "Midheaven": "mc",
    "Imum_Coeli": "ic",
    "Vertex": "vertex",
}

_ANGLE_THEMES = {
    "Ascendant": {
        "themes": ["embodiment", "self_presentation", "arrival_pattern"],
        "supports": ["visibility", "self_direction"],
        "costs": ["overidentification", "constant_self_focus"],
    },
    "Midheaven": {
        "themes": ["public_role", "visibility", "contribution"],
        "supports": ["career", "creative_visibility", "authority"],
        "costs": ["public_exposure", "recognition_pressure"],
    },
    "Descendant": {
        "themes": ["partnership", "mirroring", "direct_others"],
        "supports": ["relationship", "clients", "collaboration"],
        "costs": ["projection", "relational_pressure"],
    },
    "Imum_Coeli": {
        "themes": ["home", "privacy", "belonging"],
        "supports": ["rest", "roots", "emotional_recovery"],
        "costs": ["enclosure", "family_pattern_activation"],
    },
}

_BODY_THEMES = {
    "Sun": ("authorship", "vitality", "purpose"),
    "Moon": ("belonging", "body_rhythm", "care"),
    "Mercury": ("language", "learning", "exchange"),
    "Venus": ("value", "connection", "aesthetics"),
    "Mars": ("action", "boundary", "stamina"),
    "Jupiter": ("growth", "teaching", "opportunity"),
    "Saturn": ("structure", "commitment", "limits"),
    "Uranus": ("independence", "experimentation", "disruption"),
    "Neptune": ("imagination", "sensitivity", "atmosphere"),
    "Pluto": ("power", "depth", "transformation"),
    "Chiron": ("wound_work", "integration", "teaching_edge"),
    "North_Node": ("developmental_pull", "future_orientation"),
    "South_Node": ("familiar_pattern", "release_pattern"),
    "Lilith_BML": ("raw_autonomy", "refusal", "shadow_visibility"),
}

_HOUSE_THEMES = {
    1: ("embodiment", "identity", "self_presentation"),
    2: ("resources", "self_worth", "skills"),
    3: ("communication", "learning", "local_movement"),
    4: ("home", "roots", "privacy"),
    5: ("creativity", "pleasure", "romance"),
    6: ("daily_work", "health", "maintenance"),
    7: ("partnership", "clients", "contracts"),
    8: ("shared_resources", "intimacy", "deep_change"),
    9: ("study", "travel", "worldview"),
    10: ("career", "reputation", "public_contribution"),
    11: ("community", "audience", "future_plans"),
    12: ("solitude", "retreat", "hidden_patterns"),
}

_CONTACT_STRENGTH = {
    "tight": 0.94,
    "moderate": 0.76,
    "wide": 0.55,
    "unknown": 0.4,
}

_MOVEMENT_STRENGTH = {
    "newly_angular": 0.86,
    "leaves_angular": 0.7,
    "house_changed": 0.58,
    "same_house": 0.18,
    "unknown": 0.3,
}

_CONFIDENCE_BY_BIRTH_TIME = {
    "exact_birth_time": 0.96,
    "approximate_birth_time": 0.64,
    "unknown_birth_time": 0.34,
}

_CONDITION_SUPPORTS = {
    "strong": ["reliable_access", "integration_capacity"],
    "supported": ["reliable_access", "integration_capacity"],
    "constructive": ["integration_capacity"],
    "mixed": ["growth_edge", "conscious_handling"],
    "challenged": ["growth_edge", "conscious_handling"],
    "unknown": [],
}

_CONDITION_COSTS = {
    "strong": ["overreliance"],
    "supported": ["overreliance"],
    "constructive": ["overreliance"],
    "mixed": ["uneven_expression"],
    "challenged": ["strain", "compensation_needed"],
    "unknown": ["interpretive_uncertainty"],
}


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _clamp01(value: Any, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))


def _birth_time_confidence(record: dict) -> float:
    birth_context = record.get("birth_context") or {}
    state = birth_context.get("birth_time_confidence")
    return _CONFIDENCE_BY_BIRTH_TIME.get(state, 0.72)


def _angle_payload(angle: str | None) -> dict[str, list[str]]:
    return _ANGLE_THEMES.get(angle or "", {"themes": [], "supports": [], "costs": []})


def _body_themes(body: str | None) -> list[str]:
    return list(_BODY_THEMES.get(body or "", ()))


def _house_themes(house: Any) -> list[str]:
    return list(_HOUSE_THEMES.get(house, ()))


def _condition_key(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "unknown"
    lowered = value.strip().lower()
    if "strong" in lowered or "dignified" in lowered:
        return "strong"
    if "support" in lowered or "construct" in lowered:
        return "supported"
    if "mixed" in lowered:
        return "mixed"
    if "challenge" in lowered or "difficult" in lowered or "debil" in lowered:
        return "challenged"
    return lowered


def _condition_strength(modifier: dict) -> float:
    score = modifier.get("overall_condition_score")
    if isinstance(score, (int, float)):
        return _clamp01(abs(score) / 10.0, default=0.5)
    return 0.62 if modifier.get("was_natal_angular") else 0.48


def _modifier_confidence(modifier: dict, fallback: float) -> float:
    confidence = modifier.get("confidence")
    if isinstance(confidence, (int, float)):
        return _clamp01(confidence, default=fallback)
    if isinstance(confidence, str):
        return _CONFIDENCE_BY_BIRTH_TIME.get(confidence, fallback)
    missing_inputs = modifier.get("missing_inputs") or []
    if missing_inputs:
        return min(fallback, 0.58)
    return fallback


def _source(record: dict, field: str, source: dict | None = None) -> dict:
    factors = {
        "source_record_field": field,
        "source_record_formula_version": record.get("formula_version"),
    }
    if source:
        factors.update(_copy(source))
    return factors


def _item(
    *,
    evidence_id: str,
    family: str,
    subject: str,
    interface: str,
    strength: float,
    confidence: float,
    themes: list[str],
    supports: list[str],
    costs: list[str],
    source_factors: dict,
    calculation_status: str = "computed",
    claim_boundary: str = "bounded_interpretation",
) -> dict:
    item = {
        "evidence_id": evidence_id,
        "family": family,
        "subject": subject,
        "interface": interface,
        "strength": round(_clamp01(strength, default=0.0), 4),
        "confidence": round(_clamp01(confidence, default=0.0), 4),
        "themes": list(dict.fromkeys(themes)),
        "supports": list(dict.fromkeys(supports)),
        "costs": list(dict.fromkeys(costs)),
        "source_factors": source_factors,
        "calculation_status": calculation_status,
        "claim_boundary": claim_boundary,
    }
    missing = REQUIRED_ITEM_FIELDS - set(item)
    if missing:
        raise ValueError(f"normalized evidence item is missing: {', '.join(sorted(missing))}")
    return item


def _angle_contact_items(record: dict) -> list[dict]:
    confidence = _birth_time_confidence(record)
    items = []
    for source in record.get("relocated_angle_contacts", []) or []:
        if not isinstance(source, dict):
            continue
        angle = source.get("angle")
        body = source.get("body")
        angle_payload = _angle_payload(angle)
        strength = _CONTACT_STRENGTH.get(source.get("contact_strength"), _CONTACT_STRENGTH["unknown"])
        source_factors = _source(record, "relocated_angle_contacts", {
            "source_evidence_id": source.get("id"),
            "body": body,
            "angle": angle,
            "orb": source.get("orb"),
            "contact_strength": source.get("contact_strength"),
            "relocated_house_type": source.get("relocated_house_type"),
        })
        items.append(_item(
            evidence_id=source.get("id") or f"angle_contact:{body}:{angle}",
            family="angularity",
            subject=str(body),
            interface=_ANGLE_INTERFACES.get(angle, str(angle or "unknown")),
            strength=strength,
            confidence=confidence,
            themes=_body_themes(body) + angle_payload["themes"],
            supports=angle_payload["supports"],
            costs=angle_payload["costs"],
            source_factors=source_factors,
        ))
    return items


def _house_expression_items(record: dict) -> list[dict]:
    confidence = _birth_time_confidence(record)
    items = []
    for source in record.get("planet_house_changes", []) or []:
        if not isinstance(source, dict):
            continue
        body = source.get("body")
        relocated_house = source.get("relocated_house")
        movement_type = source.get("movement_type") or "unknown"
        strength = _MOVEMENT_STRENGTH.get(movement_type, _MOVEMENT_STRENGTH["unknown"])
        supports = _house_themes(relocated_house)
        if source.get("relocated_house_type") == "angular":
            supports.append("foregrounded_expression")
        costs = []
        if movement_type == "leaves_angular":
            costs.append("reduced_public_prominence")
        elif movement_type == "same_house":
            costs.append("less_location_specific_change")
        source_factors = _source(record, "planet_house_changes", {
            "source_evidence_id": source.get("id"),
            "body": body,
            "natal_house": source.get("natal_house"),
            "relocated_house": relocated_house,
            "house_changed": source.get("house_changed"),
            "natal_house_type": source.get("natal_house_type"),
            "relocated_house_type": source.get("relocated_house_type"),
            "movement_type": movement_type,
        })
        items.append(_item(
            evidence_id=source.get("id") or f"house_change:{body}",
            family="relocated_house_expression",
            subject=str(body),
            interface=f"house:{relocated_house}" if relocated_house is not None else "house:unknown",
            strength=strength,
            confidence=confidence,
            themes=_body_themes(body) + _house_themes(relocated_house),
            supports=supports,
            costs=costs,
            source_factors=source_factors,
        ))
    return items


def _natal_condition_items(record: dict) -> list[dict]:
    fallback_confidence = _birth_time_confidence(record)
    items = []
    for body, modifier in sorted((record.get("natal_modifiers") or {}).items()):
        if not isinstance(modifier, dict):
            continue
        condition = _condition_key(modifier.get("condition_classification"))
        themes = _body_themes(body) + ["natal_condition"]
        if modifier.get("was_natal_angular"):
            themes.append("natal_angularity")
        source_factors = _source(record, "natal_modifiers", {
            "source_evidence_id": f"natal_modifier:{body}",
            "body": body,
            "condition_classification": modifier.get("condition_classification"),
            "overall_condition_score": modifier.get("overall_condition_score"),
            "was_natal_angular": modifier.get("was_natal_angular"),
            "natal_house_type": modifier.get("natal_house_type"),
            "routing_tags": _copy(modifier.get("routing_tags", [])),
            "missing_inputs": _copy(modifier.get("missing_inputs", [])),
        })
        items.append(_item(
            evidence_id=f"natal_modifier:{body}",
            family="natal_condition",
            subject=str(body),
            interface="natal_condition",
            strength=_condition_strength(modifier),
            confidence=_modifier_confidence(modifier, fallback_confidence),
            themes=themes,
            supports=_CONDITION_SUPPORTS.get(condition, []),
            costs=_CONDITION_COSTS.get(condition, []),
            source_factors=source_factors,
        ))
    return items


def _confidence_items(record: dict) -> list[dict]:
    birth_context = record.get("birth_context") or {}
    state = birth_context.get("birth_time_confidence") or "unknown_birth_time"
    confidence = _CONFIDENCE_BY_BIRTH_TIME.get(state, 0.5)
    costs = [] if state == "exact_birth_time" else ["angle_and_house_sensitivity"]
    source_factors = _source(record, "birth_context", {
        "birth_time_confidence": state,
        "appendix_birth_time_confidence": (record.get("appendix_trace") or {}).get("birth_time_confidence"),
        "confidence_notes": _copy((record.get("evidence_ranking") or {}).get("confidence_notes", [])),
    })
    return [_item(
        evidence_id=f"confidence_note:birth_time:{state}",
        family="confidence_note",
        subject="birth_time",
        interface=state,
        strength=1.0 - confidence,
        confidence=1.0,
        themes=["calculation_sensitivity"],
        supports=[],
        costs=costs,
        source_factors=source_factors,
        claim_boundary="technical_context",
    )]


def _warning_items(record: dict) -> list[dict]:
    items = []
    for warning in record.get("warning_summary", []) or []:
        if not isinstance(warning, dict):
            continue
        key = warning.get("key") or "unknown"
        count = warning.get("count") if isinstance(warning.get("count"), int) else 1
        source_factors = _source(record, "warning_summary", {
            "source_evidence_id": warning.get("id"),
            "key": key,
            "message": warning.get("message"),
            "count": count,
            "examples": _copy(warning.get("examples", [])),
        })
        items.append(_item(
            evidence_id=warning.get("id") or f"warning_summary:{key}",
            family="technical_warning",
            subject=str(key),
            interface="technical_appendix",
            strength=min(1.0, 0.25 + (count * 0.15)),
            confidence=1.0,
            themes=["calculation_warning"],
            supports=[],
            costs=["interpretive_limitation"],
            source_factors=source_factors,
            claim_boundary="technical_context",
        ))
    return items


def _unsupported_method_items(record: dict) -> list[dict]:
    items = []
    for method in record.get("unsupported_methods", []) or []:
        source_factors = _source(record, "unsupported_methods", {
            "method": method,
            "appendix_unsupported_methods": _copy((record.get("appendix_trace") or {}).get("unsupported_methods", [])),
        })
        items.append(_item(
            evidence_id=f"unsupported_method:{method}",
            family="unsupported_method",
            subject=str(method),
            interface="future_method",
            strength=0.0,
            confidence=1.0,
            themes=[],
            supports=[],
            costs=["method_not_computed"],
            source_factors=source_factors,
            calculation_status="unavailable",
            claim_boundary="unavailable_method_note",
        ))
    return items


def normalize_location_evidence_record(record: dict) -> dict:
    """
    Convert a LocationEvidenceRecord into normalized evidence grammar output.

    The returned object is a pure adapter result: it shares no mutable child
    objects with the source record and does not alter current report assembly.
    """
    if not isinstance(record, dict):
        raise ValueError("record must be a LocationEvidenceRecord dict.")

    items = []
    items.extend(_angle_contact_items(record))
    items.extend(_house_expression_items(record))
    items.extend(_natal_condition_items(record))
    items.extend(_confidence_items(record))
    items.extend(_warning_items(record))
    items.extend(_unsupported_method_items(record))

    return {
        "grammar_version": GRAMMAR_VERSION,
        "source_record_formula_version": record.get("formula_version"),
        "purpose_lens": record.get("purpose_lens"),
        "relationship_to_place": record.get("relationship_to_place"),
        "item_count": len(items),
        "items": items,
        "computed_item_count": sum(1 for item in items if item["calculation_status"] == "computed"),
        "unavailable_item_count": sum(1 for item in items if item["calculation_status"] == "unavailable"),
        "source_trace": {
            "record_fields": [
                "relocated_angle_contacts",
                "planet_house_changes",
                "natal_modifiers",
                "birth_context",
                "warning_summary",
                "appendix_trace",
                "unsupported_methods",
            ],
            "appendix_trace": _copy(record.get("appendix_trace") or {}),
        },
    }
