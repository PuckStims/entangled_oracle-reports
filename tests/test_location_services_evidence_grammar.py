"""
Tests for the Phase 1 Location Services evidence grammar adapter.

The adapter should normalize today's LocationEvidenceRecord into reusable
evidence items without changing report assembly or pretending future methods
are computed.
"""
import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.location_services import build_location_evidence_record
from products.location_services.evidence_grammar.adapter import (
    GRAMMAR_VERSION,
    REQUIRED_ITEM_FIELDS,
    normalize_location_evidence_record,
)
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload


def _items_by_family(grammar: dict, family: str) -> list[dict]:
    return [item for item in grammar["items"] if item["family"] == family]


def _items_by_id(grammar: dict) -> dict[str, dict]:
    return {item["evidence_id"]: item for item in grammar["items"]}


def test_normalized_evidence_grammar_has_stable_top_level_shape():
    record = build_location_evidence_record(
        _build_natal_payload(),
        SYDNEY,
        purpose_lens="creative visibility",
        relationship_to_place="possible_move",
    )

    grammar = normalize_location_evidence_record(record)

    assert grammar["grammar_version"] == GRAMMAR_VERSION
    assert grammar["source_record_formula_version"] == record["formula_version"]
    assert grammar["purpose_lens"] == "creative visibility"
    assert grammar["relationship_to_place"] == "possible_move"
    assert grammar["item_count"] == len(grammar["items"])
    assert grammar["source_trace"]["record_fields"] == [
        "relocated_angle_contacts",
        "planet_house_changes",
        "natal_modifiers",
        "birth_context",
        "warning_summary",
        "appendix_trace",
        "unsupported_methods",
    ]


def test_every_normalized_item_satisfies_required_schema():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)

    assert grammar["items"]
    for item in grammar["items"]:
        assert REQUIRED_ITEM_FIELDS <= set(item)
        assert isinstance(item["evidence_id"], str) and item["evidence_id"]
        assert isinstance(item["family"], str) and item["family"]
        assert isinstance(item["subject"], str) and item["subject"]
        assert 0 <= item["strength"] <= 1
        assert 0 <= item["confidence"] <= 1
        assert isinstance(item["themes"], list)
        assert isinstance(item["supports"], list)
        assert isinstance(item["costs"], list)
        assert item["source_factors"]["source_record_formula_version"] == record["formula_version"]


def test_adapter_does_not_mutate_record_or_share_mutable_children():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    before = copy.deepcopy(record)

    grammar = normalize_location_evidence_record(record)
    grammar["source_trace"]["appendix_trace"]["unsupported_methods"].append("MUTATED")
    grammar["items"][0]["source_factors"]["source_record_formula_version"] = "MUTATED"

    assert record == before


def test_angle_contacts_normalize_with_source_ids_and_angle_interfaces():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)
    by_id = _items_by_id(grammar)

    assert _items_by_family(grammar, "angularity")
    for source in record["relocated_angle_contacts"]:
        item = by_id[source["id"]]
        assert item["family"] == "angularity"
        assert item["subject"] == source["body"]
        assert item["interface"] in {"asc", "dc", "mc", "ic"}
        assert item["source_factors"]["source_record_field"] == "relocated_angle_contacts"
        assert item["source_factors"]["source_evidence_id"] == source["id"]
        assert source["body"] in item["themes"] or item["themes"]


def test_house_changes_normalize_all_relocated_house_expression_items():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)
    house_items = _items_by_family(grammar, "relocated_house_expression")

    assert len(house_items) == len(record["planet_house_changes"])
    for source in record["planet_house_changes"]:
        item = _items_by_id(grammar)[source["id"]]
        assert item["family"] == "relocated_house_expression"
        assert item["interface"] == f"house:{source['relocated_house']}"
        assert item["source_factors"]["movement_type"] == source["movement_type"]
        assert item["source_factors"]["house_changed"] == source["house_changed"]


def test_natal_modifiers_become_natal_condition_items():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)
    natal_items = _items_by_family(grammar, "natal_condition")

    assert len(natal_items) == len(record["natal_modifiers"])
    for body, modifier in record["natal_modifiers"].items():
        item = _items_by_id(grammar)[f"natal_modifier:{body}"]
        assert item["subject"] == body
        assert item["interface"] == "natal_condition"
        assert item["source_factors"]["condition_classification"] == modifier["condition_classification"]
        assert item["source_factors"]["was_natal_angular"] == modifier["was_natal_angular"]


def test_birth_time_and_warning_notes_are_normalized_as_technical_context():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)
    confidence_items = _items_by_family(grammar, "confidence_note")
    warning_items = _items_by_family(grammar, "technical_warning")

    assert len(confidence_items) == 1
    confidence = confidence_items[0]
    assert confidence["evidence_id"].startswith("confidence_note:birth_time:")
    assert confidence["claim_boundary"] == "technical_context"
    assert confidence["source_factors"]["appendix_birth_time_confidence"] == (
        record["appendix_trace"]["birth_time_confidence"]
    )

    assert len(warning_items) == len(record["warning_summary"])
    for warning in record["warning_summary"]:
        item = _items_by_id(grammar)[warning["id"]]
        assert item["claim_boundary"] == "technical_context"
        assert item["source_factors"]["count"] == warning["count"]


def test_unsupported_methods_are_unavailable_notes_not_computed_evidence():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)
    unsupported = _items_by_family(grammar, "unsupported_method")

    assert len(unsupported) == len(record["unsupported_methods"])
    assert grammar["unavailable_item_count"] == len(record["unsupported_methods"])
    for item in unsupported:
        assert item["calculation_status"] == "unavailable"
        assert item["claim_boundary"] == "unavailable_method_note"
        assert item["strength"] == 0.0
        assert item["costs"] == ["method_not_computed"]


def test_normalized_evidence_ids_are_deterministic_for_identical_records():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)

    first = normalize_location_evidence_record(record)
    second = normalize_location_evidence_record(record)

    assert [item["evidence_id"] for item in first["items"]] == [
        item["evidence_id"] for item in second["items"]
    ]
    assert first == second
