"""
Place Resonance report-context assembly.

This module turns a LocationEvidenceRecord into a structured draft context
for the first Location Services product. It does not compute relocation
evidence, render HTML, or author prose. It selects existing block leaves and
keeps TODO scaffold leaves visible for later content passes.
"""
from __future__ import annotations

import copy
from typing import Any

from engine.location_services import build_location_evidence_record
from selectors.location_services_selector import (
    select_angle_contact_leaf,
    select_planet_house_leaf,
    select_synthesis_leaf,
    select_technical_appendix_leaf,
)


CONTEXT_VERSION = "place_resonance_context_v0.1.0"
REPORT_TYPE = "location_services.place_resonance"
PRODUCT_NAME = "Place Resonance"

PUBLIC_ANGLES = {"Ascendant", "Midheaven"}
PRIVATE_RELATIONAL_ANGLES = {"Descendant", "Imum_Coeli"}


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _index_by_id(items: list[dict]) -> dict[str, dict]:
    indexed = {}
    for item in items or []:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            indexed[item["id"]] = item
    return indexed


def _evidence_indexes(record: dict) -> dict[str, dict[str, dict]]:
    angle_contacts = _index_by_id(record.get("relocated_angle_contacts", []))
    house_changes = _index_by_id(record.get("planet_house_changes", []))
    natal_modifiers = {
        f"natal_modifier:{body_name}": modifier
        for body_name, modifier in (record.get("natal_modifiers") or {}).items()
        if isinstance(modifier, dict)
    }
    return {
        "angle_contacts": angle_contacts,
        "house_changes": house_changes,
        "natal_modifiers": natal_modifiers,
    }


def _evidence_type(evidence_id: str) -> str:
    if evidence_id.startswith("angle_contact:"):
        return "angle_contact"
    if evidence_id.startswith("house_change:"):
        return "house_change"
    if evidence_id.startswith("orientation_shift:"):
        return "orientation_shift"
    if evidence_id.startswith("natal_modifier:"):
        return "natal_modifier"
    return "unknown"


def _source_for_evidence_id(evidence_id: str, indexes: dict[str, dict[str, dict]]) -> dict | None:
    evidence_type = _evidence_type(evidence_id)
    if evidence_type == "angle_contact":
        return indexes["angle_contacts"].get(evidence_id)
    if evidence_type == "house_change":
        return indexes["house_changes"].get(evidence_id)
    if evidence_type == "natal_modifier":
        return indexes["natal_modifiers"].get(evidence_id)
    if evidence_type == "orientation_shift":
        angle_name = evidence_id.split(":", 1)[1] if ":" in evidence_id else None
        return {"id": evidence_id, "angle": angle_name}
    return None


def _leaf_for_evidence(source: dict | None, evidence_type: str) -> dict | None:
    if not isinstance(source, dict):
        return None

    if evidence_type == "angle_contact":
        return select_angle_contact_leaf(
            source.get("angle"),
            source.get("body"),
            source.get("contact_strength"),
        )

    if evidence_type == "house_change":
        return select_planet_house_leaf(
            source.get("body"),
            source.get("relocated_house"),
            source.get("movement_type"),
        )

    return None


def _evidence_summary_rows(record: dict) -> list[dict]:
    ranking = record.get("evidence_ranking") or {}
    indexes = _evidence_indexes(record)
    rows: list[dict] = []

    for tier_name in ("primary_evidence", "supporting_evidence", "contradictory_evidence"):
        for evidence_id in ranking.get(tier_name, []) or []:
            evidence_type = _evidence_type(evidence_id)
            source = _source_for_evidence_id(evidence_id, indexes)
            rows.append({
                "tier": tier_name,
                "id": evidence_id,
                "evidence_type": evidence_type,
                "source": _deepcopy(source),
                "selected_leaf": _leaf_for_evidence(source, evidence_type),
            })

    for method in ranking.get("speculative_or_excluded_evidence", []) or []:
        rows.append({
            "tier": "speculative_or_excluded_evidence",
            "id": f"unsupported_method:{method}",
            "evidence_type": "unsupported_method",
            "source": {"method": method},
            "selected_leaf": select_technical_appendix_leaf("unsupported_method", method),
        })

    return rows


def _changed_house_items(record: dict) -> list[dict]:
    return [
        item for item in record.get("planet_house_changes", []) or []
        if isinstance(item, dict) and item.get("house_changed")
    ]


def _repeated_bodies(record: dict) -> set[str]:
    angle_bodies = {
        item.get("body") for item in record.get("relocated_angle_contacts", []) or []
        if isinstance(item, dict)
    }
    changed_house_bodies = {
        item.get("body") for item in _changed_house_items(record)
        if isinstance(item, dict)
    }
    return {body for body in angle_bodies & changed_house_bodies if isinstance(body, str)}


def _primary_angle_contacts(record: dict) -> list[dict]:
    primary_ids = set((record.get("evidence_ranking") or {}).get("primary_evidence", []) or [])
    return [
        item for item in record.get("relocated_angle_contacts", []) or []
        if isinstance(item, dict) and item.get("id") in primary_ids
    ]


def _primary_house_changes(record: dict) -> list[dict]:
    primary_ids = set((record.get("evidence_ranking") or {}).get("primary_evidence", []) or [])
    return [
        item for item in record.get("planet_house_changes", []) or []
        if isinstance(item, dict) and item.get("id") in primary_ids
    ]


def _has_public_private_angle_split(record: dict) -> bool:
    primary_angles = {item.get("angle") for item in _primary_angle_contacts(record)}
    return bool(primary_angles & PUBLIC_ANGLES) and bool(primary_angles & PRIVATE_RELATIONAL_ANGLES)


def select_synthesis_category(record: dict) -> str:
    """
    Classify the evidence pattern into one Location Services synthesis key.

    This is intentionally narrow and selector-side. It does not implement
    purpose-fit taxonomy, house-domain taxonomy, contradictory evidence, or
    dynamic timing.
    """
    ranking = record.get("evidence_ranking") or {}
    primary_ids = ranking.get("primary_evidence", []) or []
    changed_house_items = _changed_house_items(record)
    angle_contacts = record.get("relocated_angle_contacts", []) or []

    if not primary_ids:
        return "low_signal_signature"

    if not changed_house_items:
        return "quiet_continuity_signature"

    repeated_bodies = _repeated_bodies(record)
    if repeated_bodies:
        return "convergent_place_signature"

    if _has_public_private_angle_split(record):
        return "mixed_public_private_signature"

    primary_angle_count = len(_primary_angle_contacts(record))
    primary_house_count = len(_primary_house_changes(record))
    if primary_angle_count and primary_angle_count >= primary_house_count:
        return "angle_led_signature"
    if primary_house_count:
        return "house_shift_led_signature"

    if angle_contacts:
        return "angle_led_signature"
    return "low_signal_signature"


def _synthesis_section(record: dict) -> dict:
    category = select_synthesis_category(record)
    return {
        "id": "place_signature",
        "title": "Place Signature",
        "category": category,
        "selected_leaf": select_synthesis_leaf(category),
        "source_evidence_ids": list((record.get("evidence_ranking") or {}).get("primary_evidence", []) or []),
        "repeated_bodies": sorted(_repeated_bodies(record)),
    }


def _angle_contact_section(record: dict) -> dict:
    blocks = []
    for item in record.get("relocated_angle_contacts", []) or []:
        if not isinstance(item, dict):
            continue
        blocks.append({
            "id": item.get("id"),
            "source": _deepcopy(item),
            "selected_leaf": select_angle_contact_leaf(
                item.get("angle"),
                item.get("body"),
                item.get("contact_strength"),
            ),
        })
    return {
        "id": "relocated_angle_contacts",
        "title": "Relocated Angle Contacts",
        "blocks": blocks,
    }


def _house_change_section(record: dict) -> dict:
    blocks = []
    for item in record.get("planet_house_changes", []) or []:
        if not isinstance(item, dict):
            continue
        blocks.append({
            "id": item.get("id"),
            "source": _deepcopy(item),
            "selected_leaf": select_planet_house_leaf(
                item.get("body"),
                item.get("relocated_house"),
                item.get("movement_type"),
            ),
        })
    return {
        "id": "planet_house_changes",
        "title": "Relocated House Emphasis",
        "blocks": blocks,
    }


def _technical_appendix_section(record: dict) -> dict:
    birth_context = record.get("birth_context") or {}
    destination_context = record.get("destination_context") or {}
    appendix_trace = record.get("appendix_trace") or {}

    blocks = [
        {
            "id": "calculation_note:relocated_chart",
            "source": {"family": "calculation_note", "sub_key": "relocated_chart"},
            "selected_leaf": select_technical_appendix_leaf("calculation_note", "relocated_chart"),
        },
        {
            "id": f"confidence_note:{birth_context.get('birth_time_confidence')}",
            "source": {"birth_time_confidence": birth_context.get("birth_time_confidence")},
            "selected_leaf": select_technical_appendix_leaf(
                "confidence_note",
                birth_context.get("birth_time_confidence") or "fallback",
            ),
        },
        {
            "id": f"coordinate_precision_note:{destination_context.get('coordinate_precision')}",
            "source": {"coordinate_precision": destination_context.get("coordinate_precision")},
            "selected_leaf": select_technical_appendix_leaf(
                "coordinate_precision_note",
                destination_context.get("coordinate_precision") or "fallback",
            ),
        },
    ]

    for method in record.get("unsupported_methods", []) or []:
        blocks.append({
            "id": f"unsupported_method:{method}",
            "source": {"method": method},
            "selected_leaf": select_technical_appendix_leaf("unsupported_method", method),
        })

    for warning in record.get("warning_summary", []) or []:
        if not isinstance(warning, dict):
            continue
        warning_key = warning.get("key") or "fallback"
        blocks.append({
            "id": warning.get("id") or f"warning_summary:{warning_key}",
            "source": _deepcopy(warning),
            "selected_leaf": select_technical_appendix_leaf("warning_summary", warning_key),
        })

    return {
        "id": "technical_appendix",
        "title": "Technical Appendix",
        "blocks": blocks,
        "raw_warning_count": len(appendix_trace.get("warnings", []) or record.get("warnings", []) or []),
        "warning_summary_count": len(record.get("warning_summary", []) or []),
    }


def assemble_place_resonance_context(evidence_record: dict) -> dict:
    """
    Build a structured Place Resonance draft context from an evidence record.

    The returned context is suitable for future template rendering, but it is
    not itself a rendered client report.
    """
    if not isinstance(evidence_record, dict):
        raise ValueError("evidence_record must be a dict.")

    required = {
        "formula_version",
        "birth_context",
        "destination_context",
        "planet_house_changes",
        "relocated_angle_contacts",
        "evidence_ranking",
        "appendix_trace",
        "unsupported_methods",
        "warning_summary",
    }
    missing = sorted(required - set(evidence_record))
    if missing:
        raise ValueError(f"evidence_record is missing required field(s): {', '.join(missing)}")

    sections = [
        _synthesis_section(evidence_record),
        {
            "id": "evidence_summary",
            "title": "Evidence Summary",
            "rows": _evidence_summary_rows(evidence_record),
        },
        _angle_contact_section(evidence_record),
        _house_change_section(evidence_record),
        _technical_appendix_section(evidence_record),
    ]

    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "evidence_record_formula_version": evidence_record.get("formula_version"),
        "birth_context": _deepcopy(evidence_record.get("birth_context")),
        "destination_context": _deepcopy(evidence_record.get("destination_context")),
        "purpose_lens": evidence_record.get("purpose_lens"),
        "relationship_to_place": evidence_record.get("relationship_to_place"),
        "sections": sections,
        "section_order": [section["id"] for section in sections],
    }


def build_place_resonance_context(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> dict:
    """
    Build a LocationEvidenceRecord and assemble it into a report context.
    """
    evidence_record = build_location_evidence_record(
        natal_payload,
        destination,
        purpose_lens=purpose_lens,
        relationship_to_place=relationship_to_place,
    )
    return assemble_place_resonance_context(evidence_record)
