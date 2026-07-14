"""
Tests for engine/location_services.py's build_location_evidence_record()
and its private helpers (Round 2: Contract Formation; Round 3 adds
warning_summary coverage).

Covers:
- Stable top-level keys matching CONTENT_LEAD_HANDOFF.md's requested field
  families
- Stable, deterministic evidence IDs
- purpose_lens / relationship_to_place pass-through and type validation
- Relocated angle contacts: body/angle/orb/contact_strength fields
- House changes: natal house, relocated house, changed flag, movement type
- No mutation of natal or relocated payloads
- Condition-bearing formulas (evaluate_all_planetary_conditions) are only
  ever called with natal_payload, never the relocated payload
- Evidence ranking follows EVIDENCE_TO_MEANING_MATRIX.md's Evidence
  Priority rules deterministically
- warning_summary aggregates repeated per-body warnings without altering
  the raw warnings list

Reuses the hand-built Chicago-birth fixture from
test_location_services_relocated_payload.py rather than duplicating it.
"""
import copy
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from engine.location_services import (
    UNSUPPORTED_METHODS,
    _contact_strength,
    _evidence_ranking,
    _house_type,
    _movement_type,
    _summarize_warnings,
    build_location_evidence_record,
    build_relocated_payload,
)
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload

TOP_LEVEL_KEYS = {
    "formula_version",
    "birth_context",
    "destination_context",
    "relocated_chart",
    "planet_house_changes",
    "relocated_angle_contacts",
    "natal_modifiers",
    "evidence_ranking",
    "purpose_lens",
    "relationship_to_place",
    "appendix_trace",
    "unsupported_methods",
    "warnings",
    "warning_summary",
}


# ── Top-level contract shape ────────────────────────────────────────────────

def test_top_level_keys_match_content_lead_handoff():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    assert set(record.keys()) == TOP_LEVEL_KEYS


def test_unsupported_methods_are_listed_at_top_level_and_in_appendix():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    assert set(record["unsupported_methods"]) == set(UNSUPPORTED_METHODS)
    assert set(record["appendix_trace"]["unsupported_methods"]) == set(UNSUPPORTED_METHODS)
    assert set(record["evidence_ranking"]["speculative_or_excluded_evidence"]) == set(UNSUPPORTED_METHODS)


def test_appendix_trace_has_required_technical_fields():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)
    appendix = record["appendix_trace"]

    for field in (
        "calculation_sources",
        "tolerances",
        "unsupported_methods",
        "warnings",
        "warning_summary",
        "birth_time_confidence",
        "coordinate_precision",
        "methodology",
    ):
        assert field in appendix


# ── purpose_lens / relationship_to_place pass-through ──────────────────────

def test_purpose_lens_and_relationship_to_place_pass_through_unchanged():
    natal = _build_natal_payload()
    record = build_location_evidence_record(
        natal, SYDNEY, purpose_lens="career", relationship_to_place="possible_move"
    )

    assert record["purpose_lens"] == "career"
    assert record["relationship_to_place"] == "possible_move"


def test_purpose_lens_and_relationship_to_place_default_to_none():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    assert record["purpose_lens"] is None
    assert record["relationship_to_place"] is None


def test_purpose_lens_rejects_non_string():
    natal = _build_natal_payload()
    with pytest.raises(ValueError, match="purpose_lens"):
        build_location_evidence_record(natal, SYDNEY, purpose_lens=42)


def test_relationship_to_place_rejects_non_string():
    natal = _build_natal_payload()
    with pytest.raises(ValueError, match="relationship_to_place"):
        build_location_evidence_record(natal, SYDNEY, relationship_to_place=["current_home"])


# ── Determinism ─────────────────────────────────────────────────────────────

def test_evidence_record_is_deterministic_for_identical_inputs():
    natal = _build_natal_payload()
    record_a = build_location_evidence_record(natal, dict(SYDNEY), purpose_lens="rest")
    record_b = build_location_evidence_record(natal, dict(SYDNEY), purpose_lens="rest")

    assert record_a == record_b


def test_house_change_and_angle_contact_ids_are_stable_format():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    for item in record["planet_house_changes"]:
        assert item["id"] == f"house_change:{item['body']}"

    for item in record["relocated_angle_contacts"]:
        assert item["id"] == f"angle_contact:{item['body']}:{item['angle']}"


# ── House changes ────────────────────────────────────────────────────────────

def test_house_change_items_cover_every_standard_planet():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    bodies = {item["body"] for item in record["planet_house_changes"]}
    assert bodies == set(natal["standard_planets"].keys())


def test_house_change_items_have_required_fields():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    for item in record["planet_house_changes"]:
        assert isinstance(item["natal_house"], int)
        assert isinstance(item["relocated_house"], int)
        assert isinstance(item["house_changed"], bool)
        assert item["natal_house_type"] in {"angular", "succedent", "cadent", "unknown"}
        assert item["relocated_house_type"] in {"angular", "succedent", "cadent", "unknown"}
        assert item["movement_type"] in {
            "same_house", "newly_angular", "leaves_angular", "house_changed", "unknown",
        }
        assert item["house_changed"] == (item["natal_house"] != item["relocated_house"])


def test_no_house_changes_when_destination_matches_birth_coordinates():
    """
    The hand-built fixture's natal angles are fabricated for speed/
    determinism, not real ephemeris output, so relocating "to the same
    place" against it would spuriously show changes (build_relocated_payload
    always computes real angles). This invariant needs a real natal chart.
    """
    from engine.natal_engine import generate_payload

    natal = generate_payload({
        "name": "Same Place Test",
        "date": "1990-06-15",
        "time": "14:22",
        "location": "Chicago, Illinois",
    })
    same_place = {
        "latitude": natal["user_profile"]["resolved_coordinates"]["latitude"],
        "longitude": natal["user_profile"]["resolved_coordinates"]["longitude"],
        "timezone": natal["user_profile"]["timezone"],
    }
    record = build_location_evidence_record(natal, same_place)

    assert all(not item["house_changed"] for item in record["planet_house_changes"])
    assert all(item["movement_type"] == "same_house" for item in record["planet_house_changes"])


# ── Relocated angle contacts ─────────────────────────────────────────────────

def test_angle_contact_items_have_required_fields():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    assert record["relocated_angle_contacts"], "expected at least one relocated angle contact for this fixture"
    for item in record["relocated_angle_contacts"]:
        assert item["angle"] in {"Ascendant", "Descendant", "Midheaven", "Imum_Coeli"}
        assert isinstance(item["orb"], (int, float))
        assert item["contact_strength"] in {"tight", "moderate", "wide"}
        assert item["relocated_house_type"] == "angular"


# ── Natal modifiers (natal-only, never recomputed on relocated payload) ────

def test_natal_modifiers_only_cover_emphasized_bodies():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    emphasized = {item["body"] for item in record["relocated_angle_contacts"]}
    emphasized |= {item["body"] for item in record["planet_house_changes"] if item["house_changed"]}

    assert set(record["natal_modifiers"].keys()) == emphasized


def test_natal_modifiers_carry_natal_only_condition_fields():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    for body_name, modifier in record["natal_modifiers"].items():
        assert modifier["body"] == body_name
        assert modifier["source_standard_formula"] == (
            "formulas.standard.planetary_condition.evaluate_all_planetary_conditions"
        )
        assert "condition_classification" in modifier
        assert "overall_condition_score" in modifier
        assert "essential_dignity" in modifier
        assert "sect_condition" in modifier
        assert "was_natal_angular" in modifier


def test_evaluate_all_planetary_conditions_is_only_ever_called_with_natal_payload():
    """
    The whole point of this boundary: relocation must never rewrite natal
    condition. Patch the condition formula and assert every call it
    receives is natal_payload, never the relocated payload.
    """
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    from formulas.standard.planetary_condition import (
        evaluate_all_planetary_conditions as real_evaluate,
    )

    calls = []

    def _spy(payload):
        calls.append(payload)
        return real_evaluate(payload)

    with patch("engine.location_services.evaluate_all_planetary_conditions", side_effect=_spy):
        build_location_evidence_record(natal, SYDNEY)

    assert calls, "expected evaluate_all_planetary_conditions to be called at least once"
    for payload in calls:
        assert payload is natal
        assert payload is not relocated


# ── No mutation ──────────────────────────────────────────────────────────────

def test_build_location_evidence_record_does_not_mutate_natal_payload():
    natal = _build_natal_payload()
    snapshot = copy.deepcopy(natal)

    build_location_evidence_record(natal, SYDNEY, purpose_lens="study")

    assert natal == snapshot


# ── Evidence ranking (unit-level, against the private helper) ──────────────

def test_evidence_ranking_prioritizes_angle_contacts_and_newly_angular_moves():
    house_change_items = [
        {"id": "house_change:Mars", "body": "Mars", "house_changed": True, "movement_type": "newly_angular"},
        {"id": "house_change:Moon", "body": "Moon", "house_changed": True, "movement_type": "house_changed"},
        {"id": "house_change:Saturn", "body": "Saturn", "house_changed": False, "movement_type": "same_house"},
    ]
    angle_contact_items = [
        {"id": "angle_contact:Venus:Midheaven", "body": "Venus", "angle": "Midheaven"},
    ]
    comparison = {"angle_comparison": {}}

    ranking = _evidence_ranking({}, comparison, house_change_items, angle_contact_items, {})

    assert "angle_contact:Venus:Midheaven" in ranking["primary_evidence"]
    assert "house_change:Mars" in ranking["primary_evidence"]
    assert "house_change:Moon" in ranking["supporting_evidence"]
    assert "house_change:Saturn" not in ranking["primary_evidence"]
    assert "house_change:Saturn" not in ranking["supporting_evidence"]


def test_evidence_ranking_treats_custom_body_contacts_as_supporting():
    house_change_items = [
        {"id": "house_change:Kassandra", "body": "Kassandra", "house_changed": True, "movement_type": "newly_angular"},
    ]
    angle_contact_items = [
        {"id": "angle_contact:Kassandra:Midheaven", "body": "Kassandra", "angle": "Midheaven"},
    ]

    ranking = _evidence_ranking({}, {"angle_comparison": {}}, house_change_items, angle_contact_items, {})

    assert "angle_contact:Kassandra:Midheaven" not in ranking["primary_evidence"]
    assert "house_change:Kassandra" not in ranking["primary_evidence"]
    assert "angle_contact:Kassandra:Midheaven" in ranking["supporting_evidence"]
    assert "house_change:Kassandra" in ranking["supporting_evidence"]


def test_evidence_ranking_promotes_repeated_body_to_primary():
    """
    A body with both an angle contact AND a house change is 'multiple
    high-priority factors repeat the same planet' per
    EVIDENCE_TO_MEANING_MATRIX.md, even when the house change itself isn't
    a newly_angular transition (e.g. a body can sit just inside a cadent
    whole-sign house while still within orb of the adjacent angle).
    """
    house_change_items = [
        {"id": "house_change:Venus", "body": "Venus", "house_changed": True, "movement_type": "house_changed"},
    ]
    angle_contact_items = [
        {"id": "angle_contact:Venus:Ascendant", "body": "Venus", "angle": "Ascendant"},
    ]
    comparison = {"angle_comparison": {}}

    ranking = _evidence_ranking({}, comparison, house_change_items, angle_contact_items, {})

    assert "house_change:Venus" in ranking["primary_evidence"]
    assert "house_change:Venus" not in ranking["supporting_evidence"]


def test_evidence_ranking_flags_orientation_shift_on_angle_sign_change():
    comparison = {
        "angle_comparison": {
            "Ascendant": {"sign_changed": True},
            "Midheaven": {"sign_changed": False},
            "Vertex": {"sign_changed": True},
        },
    }

    ranking = _evidence_ranking({}, comparison, [], [], {})

    assert "orientation_shift:Ascendant" in ranking["primary_evidence"]
    assert "orientation_shift:Midheaven" not in ranking["primary_evidence"]
    # Vertex is intentionally excluded from orientation-shift evidence.
    assert "orientation_shift:Vertex" not in ranking["primary_evidence"]


def test_evidence_ranking_contradictory_evidence_is_always_empty_in_v0_1():
    ranking = _evidence_ranking({}, {"angle_comparison": {}}, [], [], {})
    assert ranking["contradictory_evidence"] == []


def test_evidence_ranking_adds_confidence_note_for_non_exact_birth_time():
    natal_payload = {"user_profile": {"birth_time_state": "approximate_birth_time"}}
    ranking = _evidence_ranking(natal_payload, {"angle_comparison": {}}, [], [], {})

    assert any("approximate_birth_time" in note for note in ranking["confidence_notes"])


def test_evidence_ranking_no_confidence_note_for_exact_birth_time():
    natal_payload = {"user_profile": {"birth_time_state": "exact_birth_time"}}
    ranking = _evidence_ranking(natal_payload, {"angle_comparison": {}}, [], [], {})

    assert ranking["confidence_notes"] == []


# ── Private helpers ──────────────────────────────────────────────────────────

def test_house_type_known_and_unknown():
    assert _house_type(1) == "angular"
    assert _house_type(2) == "succedent"
    assert _house_type(3) == "cadent"
    assert _house_type(None) == "unknown"
    assert _house_type(13) == "unknown"


def test_contact_strength_bands():
    assert _contact_strength(0.0) == "tight"
    assert _contact_strength(2.0) == "tight"
    assert _contact_strength(2.01) == "moderate"
    assert _contact_strength(5.0) == "moderate"
    assert _contact_strength(5.01) == "wide"
    assert _contact_strength(8.0) == "wide"
    assert _contact_strength(None) == "unknown"


def test_movement_type_transitions():
    assert _movement_type(1, 1) == "same_house"
    assert _movement_type(3, 10) == "newly_angular"   # cadent -> angular
    assert _movement_type(1, 5) == "leaves_angular"    # angular -> succedent
    assert _movement_type(2, 3) == "house_changed"     # succedent -> cadent
    assert _movement_type(None, 4) == "unknown"
    assert _movement_type(4, None) == "unknown"


# ── warning_summary (Round 3) ────────────────────────────────────────────────

def test_summarize_warnings_collapses_repeated_per_body_template():
    warnings = [
        f"{body} is relocation-emphasized but has no natal condition record "
        "(evaluate_all_planetary_conditions covers Sun through Pluto only)."
        for body in ("Chiron", "DNA", "Kassandra")
    ]

    summary = _summarize_warnings(warnings)

    assert len(summary) == 1
    entry = summary[0]
    assert entry["key"] == "no_natal_condition_record"
    assert entry["id"] == "warning_summary:no_natal_condition_record"
    assert entry["count"] == 3
    assert entry["examples"] == ["Chiron", "DNA", "Kassandra"]
    assert entry["message"] == (
        "3 relocation-emphasized bodies have no natal condition record "
        "(evaluate_all_planetary_conditions covers Sun through Pluto only)."
    )


def test_summarize_warnings_collapses_missing_body_template():
    warnings = [
        "North_Node is missing from the relocated payload; house comparison skipped.",
        "South_Node is missing from the relocated payload; house comparison skipped.",
    ]

    summary = _summarize_warnings(warnings)

    assert len(summary) == 1
    assert summary[0]["key"] == "missing_from_relocated_payload"
    assert summary[0]["count"] == 2
    assert summary[0]["examples"] == ["North_Node", "South_Node"]


def test_summarize_warnings_leaves_single_occurrence_message_unchanged():
    warnings = ["destination.timezone was not provided. Something something."]

    summary = _summarize_warnings(warnings)

    assert len(summary) == 1
    assert summary[0]["count"] == 1
    assert summary[0]["message"] == warnings[0]
    assert summary[0]["examples"] == []


def test_summarize_warnings_collapses_identical_non_templated_duplicates():
    message = "2 natal aspect(s) involving an angle were excluded from the relocated aspect list."
    summary = _summarize_warnings([message, message])

    assert len(summary) == 1
    assert summary[0]["count"] == 2
    assert summary[0]["message"] == message  # unchanged: not a known per-body template


def test_summarize_warnings_keeps_distinct_non_templated_messages_separate():
    summary = _summarize_warnings(["Warning A.", "Warning B."])

    assert len(summary) == 2
    assert {entry["message"] for entry in summary} == {"Warning A.", "Warning B."}
    assert {entry["count"] for entry in summary} == {1}


def test_summarize_warnings_preserves_first_seen_order():
    warnings = [
        "Warning A.",
        "Chiron is relocation-emphasized but has no natal condition record "
        "(evaluate_all_planetary_conditions covers Sun through Pluto only).",
        "Warning B.",
        "DNA is relocation-emphasized but has no natal condition record "
        "(evaluate_all_planetary_conditions covers Sun through Pluto only).",
    ]

    summary = _summarize_warnings(warnings)

    assert len(summary) == 3
    assert summary[0]["message"] == "Warning A."
    assert summary[1]["key"] == "no_natal_condition_record"
    assert summary[1]["count"] == 2
    assert summary[2]["message"] == "Warning B."


def test_summarize_warnings_of_empty_list_is_empty():
    assert _summarize_warnings([]) == []


def test_build_location_evidence_record_warning_summary_matches_top_level_and_appendix():
    natal = _build_natal_payload()
    record = build_location_evidence_record(natal, SYDNEY)

    assert record["warning_summary"] == record["appendix_trace"]["warning_summary"]
    assert record["warning_summary"] == _summarize_warnings(record["warnings"])


def test_build_location_evidence_record_raw_warnings_list_is_unaggregated():
    """Raw `warnings` must stay exactly as generated -- one entry per
    occurrence, not collapsed -- even though warning_summary aggregates it."""
    from engine.natal_engine import generate_payload

    natal = generate_payload({
        "name": "Warning Aggregation Test",
        "date": "1990-06-15",
        "time": "14:22",
        "location": "Chicago, Illinois",
    })
    record = build_location_evidence_record(natal, {"location": "Denver, Colorado"})

    no_condition_record_warnings = [
        w for w in record["warnings"]
        if "has no natal condition record" in w
    ]
    summary_entry = next(
        entry for entry in record["warning_summary"]
        if entry["key"] == "no_natal_condition_record"
    )

    assert len(no_condition_record_warnings) == summary_entry["count"]
    assert len(no_condition_record_warnings) > 1, (
        "expected this fixture's Chicago -> Denver move to emphasize multiple "
        "asteroids without a natal condition record"
    )


def test_warning_summary_is_deterministic():
    natal = _build_natal_payload()
    record_a = build_location_evidence_record(natal, dict(SYDNEY))
    record_b = build_location_evidence_record(natal, dict(SYDNEY))

    assert record_a["warning_summary"] == record_b["warning_summary"]
