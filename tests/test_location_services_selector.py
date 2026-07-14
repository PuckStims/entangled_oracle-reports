"""
Tests for the structured Location Services block selector.

The Location Services selector returns whole leaf dictionaries, not prose
strings. These tests lock the traversal and fallback behavior to the current
Place Resonance scaffold without invoking the evidence engine.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import REPORT_BLOCK_DIRS
from selectors import block_selector
from selectors import location_services_selector as selector
from selectors.location_services_selector import (
    select_angle_contact_leaf,
    select_planet_house_leaf,
    select_synthesis_leaf,
    select_technical_appendix_leaf,
)


REQUIRED_LEAF_KEYS = {"body", "_note", "claim_level", "requires_evidence"}
BLOCK_ROOT = Path(__file__).resolve().parent.parent / "products" / "location_services" / "blocks" / "plainspeak"


def _assert_leaf(leaf: dict) -> dict:
    assert isinstance(leaf, dict)
    assert REQUIRED_LEAF_KEYS <= set(leaf)
    assert isinstance(leaf["body"], str) and leaf["body"].strip()
    assert isinstance(leaf["_note"], str) and leaf["_note"].strip()
    assert isinstance(leaf["claim_level"], str) and leaf["claim_level"].strip()
    assert isinstance(leaf["requires_evidence"], list)
    return leaf


def test_config_has_location_services_block_root():
    root = Path(REPORT_BLOCK_DIRS["location_services"])
    assert root == BLOCK_ROOT
    assert root.is_dir()


def test_location_services_block_root_does_not_alias_other_product_roots():
    location_root = Path(REPORT_BLOCK_DIRS["location_services"]).resolve()
    for report_type, root in REPORT_BLOCK_DIRS.items():
        if report_type == "location_services":
            continue
        assert Path(root).resolve() != location_root


@pytest.mark.parametrize(
    ("selector_call", "expected_claim_level"),
    [
        (lambda: select_technical_appendix_leaf("calculation_note", "relocated_chart"), "technical_disclosure"),
        (lambda: select_angle_contact_leaf("Midheaven", "Sun", "tight"), "bounded_interpretation"),
        (lambda: select_planet_house_leaf("Venus", 10, "same_house"), "bounded_interpretation"),
        (lambda: select_synthesis_leaf("angle_led_signature"), "bounded_interpretation"),
    ],
)
def test_selector_functions_return_structured_leaf_dicts(selector_call, expected_claim_level):
    leaf = _assert_leaf(selector_call())
    assert leaf["claim_level"] == expected_claim_level


def test_technical_appendix_warning_summary_selects_known_warning_key():
    leaf = _assert_leaf(select_technical_appendix_leaf("warning_summary", "no_natal_condition_record"))
    assert leaf["claim_level"] == "technical_disclosure"
    assert "warning_summary" in leaf["requires_evidence"]


def test_technical_appendix_unknown_warning_uses_family_fallback():
    leaf = _assert_leaf(select_technical_appendix_leaf("warning_summary", "new_warning_kind"))
    assert "warning_summary" in leaf["requires_evidence"]
    assert "warning_summary" in leaf["_note"]


def test_technical_appendix_unknown_family_uses_top_level_fallback():
    leaf = _assert_leaf(select_technical_appendix_leaf("missing_family", "anything"))
    assert leaf["requires_evidence"] == ["appendix_trace"]


def test_short_and_long_angle_aliases_select_same_leaf():
    assert select_angle_contact_leaf("MC", "Sun", "tight") == select_angle_contact_leaf("Midheaven", "Sun", "tight")
    assert select_angle_contact_leaf("ASC", "Moon", "wide") == select_angle_contact_leaf("Ascendant", "Moon", "wide")


def test_vertex_angle_is_rejected_for_relocated_contacts():
    with pytest.raises(ValueError, match="Vertex"):
        select_angle_contact_leaf("Vertex", "Sun", "tight")


@pytest.mark.parametrize(
    ("body", "expected_note"),
    [
        ("North_Node", "growth-direction"),
        ("South_Node", "familiar"),
        ("Lilith_BML", "disowned power"),
    ],
)
def test_named_non_core_angle_contact_bodies_use_named_fallback_subkeys(body, expected_note):
    leaf = _assert_leaf(select_angle_contact_leaf("Ascendant", body, "tight"))
    assert leaf["requires_evidence"] == ["relocated_angle_contacts"]
    assert body.lower() in leaf["_note"].lower()
    assert expected_note in leaf["_note"].lower()


@pytest.mark.parametrize("body", ["Sirene", "Aphrodite"])
def test_anonymous_non_core_angle_contact_bodies_use_generic_fallback(body):
    leaf = _assert_leaf(select_angle_contact_leaf("Ascendant", body, "tight"))
    assert leaf["requires_evidence"] == ["relocated_angle_contacts"]
    assert "uncovered anonymous asteroid" in leaf["_note"].lower()


def test_unknown_contact_strength_uses_body_fallback():
    leaf = _assert_leaf(select_angle_contact_leaf("Midheaven", "Sun", "razor_close"))
    assert leaf["requires_evidence"] == ["relocated_angle_contacts"]
    assert "contact_strength" in leaf["_note"]


@pytest.mark.parametrize(
    ("body", "house", "movement_type"),
    [
        ("Sun", 1, "newly_angular"),
        ("Moon", 2, "leaves_angular"),
        ("Mercury", 3, "house_changed"),
        ("Venus", 10, "same_house"),
        ("Mars", 7, "newly_angular"),
        ("Jupiter", 11, "leaves_angular"),
        ("Pluto", 8, "house_changed"),
    ],
)
def test_planet_house_valid_combinations_return_leaves(body, house, movement_type):
    leaf = _assert_leaf(select_planet_house_leaf(body, house, movement_type))
    assert "planet_house_changes" in leaf["requires_evidence"]


@pytest.mark.parametrize(
    ("body", "house", "movement_type"),
    [
        ("Sun", 1, "leaves_angular"),
        ("Moon", 2, "newly_angular"),
        ("Mars", 4, "leaves_angular"),
        ("Venus", 5, "newly_angular"),
        ("Jupiter", 7, "leaves_angular"),
        ("Saturn", 8, "newly_angular"),
        ("Pluto", 10, "leaves_angular"),
    ],
)
def test_planet_house_impossible_movement_types_use_house_fallback(body, house, movement_type):
    leaf = _assert_leaf(select_planet_house_leaf(body, house, movement_type))
    assert leaf["requires_evidence"] == ["planet_house_changes"]
    assert "movement_type not listed" in leaf["_note"]


def test_planet_house_unknown_movement_type_routes_to_body_unknown_leaf():
    leaf = _assert_leaf(select_planet_house_leaf("Sun", 1, "unknown"))
    assert leaf["requires_evidence"] == ["planet_house_changes"]
    assert "could not be determined" in leaf["_note"]


def test_planet_house_none_house_routes_to_body_unknown_leaf():
    leaf = _assert_leaf(select_planet_house_leaf("Sun", None, "same_house"))
    assert leaf["requires_evidence"] == ["planet_house_changes"]
    assert "could not be determined" in leaf["_note"]


def test_non_core_body_with_missing_house_uses_fallback_body_unknown_leaf():
    leaf = _assert_leaf(select_planet_house_leaf("Lilith_BML", None, "unknown"))
    assert leaf["requires_evidence"] == ["planet_house_changes"]
    assert "uncovered body" in leaf["_note"].lower()


def test_synthesis_known_category_and_fallback_are_structured():
    known = _assert_leaf(select_synthesis_leaf("convergent_place_signature"))
    fallback = _assert_leaf(select_synthesis_leaf("not_real"))
    assert known["claim_level"] == "bounded_interpretation"
    assert fallback["claim_level"] == "bounded_interpretation"
    assert fallback["requires_evidence"] == ["evidence_ranking"]


def test_selector_returns_deep_copies_of_cached_leaves():
    first = select_angle_contact_leaf("Midheaven", "Sun", "tight")
    first["body"] = "MUTATED"
    second = select_angle_contact_leaf("Midheaven", "Sun", "tight")
    assert second["body"] != "MUTATED"


def test_selector_cache_is_separate_from_generic_block_selector_cache():
    selector.clear_cache()
    block_selector.clear_cache()

    assert selector._cache == {}
    assert block_selector._block_cache == {}

    select_angle_contact_leaf("Midheaven", "Sun", "tight")

    assert selector._cache
    assert all(key.startswith("location_services/") for key in selector._cache)
    assert block_selector._block_cache == {}


def test_selector_module_does_not_depend_on_location_engine():
    module_path = Path(selector.__file__)
    source = module_path.read_text(encoding="utf-8")
    assert "engine.location_services" not in source
    assert not hasattr(selector, "build_location_evidence_record")
