"""
Tests for Place Resonance report-context assembly.

The assembler consumes an existing LocationEvidenceRecord, selects structured
block leaves, and returns an inspectable draft context. It should not mutate
the record or expand Location Services computation.
"""
import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from engine.location_services import build_location_evidence_record
from engine.natal_engine import generate_payload
from products.location_services.place_resonance.assembler import (
    assemble_place_resonance_context,
    build_place_resonance_context,
    select_synthesis_category,
)
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload


def _section(context: dict, section_id: str) -> dict:
    matches = [section for section in context["sections"] if section["id"] == section_id]
    assert len(matches) == 1
    return matches[0]


def _assert_leaf(leaf: dict) -> dict:
    assert isinstance(leaf, dict)
    assert {"body", "_note", "claim_level", "requires_evidence"} <= set(leaf)
    assert isinstance(leaf["body"], str) and leaf["body"].strip()
    return leaf


def test_assemble_place_resonance_context_has_stable_top_level_shape():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)

    assert context["context_version"] == "place_resonance_context_v0.1.0"
    assert context["report_type"] == "location_services.place_resonance"
    assert context["product_name"] == "Place Resonance"
    assert context["evidence_record_formula_version"] == record["formula_version"]
    assert context["section_order"] == [
        "place_signature",
        "evidence_summary",
        "relocated_angle_contacts",
        "planet_house_changes",
        "technical_appendix",
    ]


def test_assemble_place_resonance_context_does_not_mutate_evidence_record():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    before = copy.deepcopy(record)

    context = assemble_place_resonance_context(record)
    context["birth_context"]["birth_location"] = "MUTATED"
    _section(context, "planet_house_changes")["blocks"][0]["source"]["body"] = "MUTATED"

    assert record == before


def test_sydney_fixture_selects_convergent_signature():
    record = build_location_evidence_record(
        _build_natal_payload(),
        SYDNEY,
        purpose_lens="career",
        relationship_to_place="possible_move",
    )
    context = assemble_place_resonance_context(record)
    synthesis = _section(context, "place_signature")

    assert select_synthesis_category(record) == "convergent_place_signature"
    assert synthesis["category"] == "convergent_place_signature"
    assert synthesis["repeated_bodies"]
    _assert_leaf(synthesis["selected_leaf"])
    assert synthesis["selected_leaf"]["body"] != "TODO"
    assert context["purpose_lens"] == "career"
    assert context["relationship_to_place"] == "possible_move"


def test_quiet_same_place_chart_selects_quiet_continuity_signature():
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
    context = assemble_place_resonance_context(record)

    assert all(not item["house_changed"] for item in record["planet_house_changes"])
    assert select_synthesis_category(record) == "quiet_continuity_signature"
    assert _section(context, "place_signature")["category"] == "quiet_continuity_signature"


def test_angle_contact_section_selects_one_leaf_per_contact():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)
    section = _section(context, "relocated_angle_contacts")

    assert len(section["blocks"]) == len(record["relocated_angle_contacts"])
    for block in section["blocks"]:
        source = block["source"]
        leaf = _assert_leaf(block["selected_leaf"])
        assert source["id"] == block["id"]
        assert source["angle"] in {"Ascendant", "Midheaven", "Descendant", "Imum_Coeli"}
        assert source["contact_strength"] in {"tight", "moderate", "wide"}
        assert "relocated_angle_contacts" in leaf["requires_evidence"]


def test_house_change_section_selects_one_leaf_per_house_item():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)
    section = _section(context, "planet_house_changes")

    assert len(section["blocks"]) == len(record["planet_house_changes"])
    for block in section["blocks"]:
        source = block["source"]
        leaf = _assert_leaf(block["selected_leaf"])
        assert source["id"] == block["id"]
        assert source["movement_type"] in {
            "same_house", "newly_angular", "leaves_angular", "house_changed", "unknown",
        }
        assert "planet_house_changes" in leaf["requires_evidence"]


def test_evidence_summary_rows_follow_ranking_order_and_select_supported_leaves():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)
    rows = _section(context, "evidence_summary")["rows"]
    ranking = record["evidence_ranking"]

    expected_ids = (
        ranking["primary_evidence"]
        + ranking["supporting_evidence"]
        + ranking["contradictory_evidence"]
        + [f"unsupported_method:{method}" for method in ranking["speculative_or_excluded_evidence"]]
    )
    assert [row["id"] for row in rows] == expected_ids

    selected_rows = [row for row in rows if row["evidence_type"] in {"angle_contact", "house_change", "unsupported_method"}]
    assert selected_rows
    for row in selected_rows:
        _assert_leaf(row["selected_leaf"])


def test_technical_appendix_uses_warning_summary_not_raw_warning_strings():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)
    appendix = _section(context, "technical_appendix")

    assert appendix["raw_warning_count"] == len(record["warnings"])
    assert appendix["warning_summary_count"] == len(record["warning_summary"])
    assert all("selected_leaf" in block for block in appendix["blocks"])
    appendix_sources = [block["source"] for block in appendix["blocks"]]
    assert record["warning_summary"]
    assert any(source in record["warning_summary"] for source in appendix_sources if isinstance(source, dict))
    assert all(source not in record["warnings"] for source in appendix_sources)


def test_build_place_resonance_context_wrapper_builds_record_then_assembles():
    context = build_place_resonance_context(
        _build_natal_payload(),
        SYDNEY,
        purpose_lens="study",
        relationship_to_place="trial_visit",
    )

    assert context["product_name"] == "Place Resonance"
    assert context["purpose_lens"] == "study"
    assert context["relationship_to_place"] == "trial_visit"
    assert _section(context, "place_signature")["selected_leaf"]["body"]


def test_assemble_place_resonance_context_rejects_missing_required_fields():
    with pytest.raises(ValueError, match="missing required field"):
        assemble_place_resonance_context({"formula_version": "partial"})
