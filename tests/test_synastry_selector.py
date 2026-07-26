import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from config import REPORT_BLOCK_DIRS
from selectors import synastry_selector as selector
from selectors.synastry_selector import (
    classify_body_pair_family,
    normalize_body_pair_key,
    select_body_pair_family_leaf,
    select_composite_aspect_leaf,
    select_composite_unsupported_layer_leaf,
    select_directional_aspect_leaf,
    select_exact_body_pair_leaf,
    select_house_overlay_confidence_leaf,
    select_house_overlay_intersection_leaf,
    select_house_overlay_source_body_leaf,
    select_house_overlay_target_house_leaf,
    select_repeated_theme_confidence_leaf,
    select_repeated_theme_type_leaf,
    select_technical_appendix_leaf,
    select_topic_confidence_leaf,
    select_topic_convergence_leaf,
    select_topic_polarity_leaf,
    select_topic_signature_leaf,
)


REQUIRED_LEAF_KEYS = {"body", "_note", "claim_level", "requires_evidence"}
BLOCK_ROOT = Path(__file__).resolve().parent.parent / "products" / "synastry" / "blocks" / "plainspeak"


def _assert_leaf(leaf: dict) -> dict:
    assert isinstance(leaf, dict)
    assert REQUIRED_LEAF_KEYS <= set(leaf)
    assert isinstance(leaf["body"], str) and leaf["body"].strip()
    assert isinstance(leaf["_note"], str) and leaf["_note"].strip()
    assert isinstance(leaf["claim_level"], str) and leaf["claim_level"].strip()
    assert isinstance(leaf["requires_evidence"], list) and leaf["requires_evidence"]
    return leaf


def test_config_has_synastry_block_root():
    root = Path(REPORT_BLOCK_DIRS["synastry"])
    assert root == BLOCK_ROOT
    assert root.is_dir()


def test_synastry_selector_returns_structured_leaf_dicts():
    cases = [
        select_technical_appendix_leaf("calculation_note", "pair_payload"),
        select_directional_aspect_leaf("Conjunction", "body_to_body", "mixed"),
        select_body_pair_family_leaf("luminary_contact"),
        select_exact_body_pair_leaf({"Sun", "Moon"}),
        select_house_overlay_source_body_leaf("Venus"),
        select_house_overlay_target_house_leaf(7),
        select_house_overlay_intersection_leaf("Moon", 3),
        select_house_overlay_confidence_leaf("exact_birth_time"),
        select_composite_aspect_leaf("Trine"),
        select_composite_unsupported_layer_leaf("davison"),
        select_repeated_theme_type_leaf("same_sign_emphasis"),
        select_repeated_theme_confidence_leaf("unknown_birth_time"),
        select_topic_signature_leaf("communication"),
        select_topic_polarity_leaf("mixed"),
        select_topic_convergence_leaf("house_localized"),
        select_topic_confidence_leaf("approximate_birth_time"),
    ]
    for leaf in cases:
        _assert_leaf(leaf)


def test_body_pair_family_classifier_routes_expected_cases():
    assert classify_body_pair_family({"Sun", "Mars"}) == "luminary_contact"
    assert classify_body_pair_family({"Mercury", "Venus"}) == "personal_planet_contact"
    assert classify_body_pair_family({"Jupiter", "Moon"}) == "luminary_contact"
    assert classify_body_pair_family({"Jupiter", "Saturn"}) == "social_planet_contact"
    assert classify_body_pair_family({"Pluto", "Mars"}) == "outer_planet_contact"
    assert classify_body_pair_family({"North_Node", "Venus"}) == "node_or_chiron_contact"
    assert classify_body_pair_family({"Ascendant", "Venus"}) == "angle_contact"


def test_unknown_aspect_branch_falls_back_to_authored_leaf():
    leaf = _assert_leaf(select_directional_aspect_leaf("Quincunx", "body_to_body", "mixed"))
    assert "fully authored major routes" in leaf["body"]


def test_unknown_house_and_source_body_fall_back_cleanly():
    house_leaf = _assert_leaf(select_house_overlay_target_house_leaf(99))
    source_leaf = _assert_leaf(select_house_overlay_source_body_leaf("Ceres"))
    assert "explicitly authored leaves" in house_leaf["body"]
    assert "house overlay layer" in source_leaf["body"]


def test_exact_routes_return_specific_leaves_only_when_authored():
    pair_leaf = _assert_leaf(select_exact_body_pair_leaf({"Moon", "Sun"}))
    overlay_leaf = _assert_leaf(select_house_overlay_intersection_leaf("Moon", 3))
    assert "vitality and self-expression" in pair_leaf["body"]
    assert "identity and feeling" in pair_leaf["body"]
    assert "feeling travel through ordinary exchange" in overlay_leaf["body"]
    assert select_exact_body_pair_leaf({"Mercury", "Mars"}) is None
    assert select_house_overlay_intersection_leaf("Ceres", 3) is None


def test_body_pair_key_normalization_is_order_insensitive():
    assert normalize_body_pair_key(["Sun", "Moon"]) == "Moon__Sun"
    assert normalize_body_pair_key(["Moon", "Sun"]) == "Moon__Sun"


def test_topic_and_repeated_theme_unknown_keys_use_fallback_routes():
    topic_leaf = _assert_leaf(select_topic_signature_leaf("not_real"))
    theme_leaf = _assert_leaf(select_repeated_theme_type_leaf("new_theme_type"))
    assert "narrower authored route" in topic_leaf["body"] or "active" in topic_leaf["body"]
    assert "narrower authored route" in theme_leaf["body"] or "repeated-theme family" in theme_leaf["body"]


def test_selector_returns_deep_copies():
    first = select_topic_signature_leaf("communication")
    first["body"] = "MUTATED"
    second = select_topic_signature_leaf("communication")
    assert second["body"] != "MUTATED"


def test_selector_cache_uses_synastry_namespace_only():
    selector.clear_cache()
    assert selector._cache == {}
    select_house_overlay_source_body_leaf("Moon")
    assert selector._cache
    assert all(key.startswith("synastry/") for key in selector._cache)
