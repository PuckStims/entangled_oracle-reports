"""
Tests for Place Resonance practical context modifier blocks.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

BLOCK_FILE = (
    Path(__file__).resolve().parent.parent
    / "products"
    / "location_services"
    / "blocks"
    / "plainspeak"
    / "place_context_modifier_blocks.json"
)

EXPECTED_AXES = {
    "social_connection",
    "visibility",
    "restoration",
    "isolation",
    "pressure",
    "movement",
    "stability",
    "intimacy",
}

EXPECTED_EXPRESSIONS = {"supportive", "demanding", "thin", "mixed"}
FORBIDDEN_SOFTENING_PHRASES = (
    "personal reflection without many ripples",
    "only you can know",
    "could mean many different things",
)


def _load() -> dict:
    return json.loads(BLOCK_FILE.read_text(encoding="utf-8"))


def _leaf_dicts(node):
    if isinstance(node, dict):
        if "body" in node:
            yield node
        for value in node.values():
            yield from _leaf_dicts(value)


def test_place_context_modifier_blocks_parse_and_cover_expected_axes():
    data = _load()
    axes = set(data) - {"_note", "_version", "fallback"}
    assert axes == EXPECTED_AXES
    assert data["_version"] == "0.1.0-authored"


@pytest.mark.parametrize("axis", sorted(EXPECTED_AXES))
def test_each_context_axis_has_expected_expression_leaves(axis):
    axis_block = _load()[axis]
    expressions = set(axis_block) - {"_note", "fallback"}
    assert expressions == EXPECTED_EXPRESSIONS


def test_every_context_modifier_leaf_is_authored_and_bounded():
    for leaf in _leaf_dicts(_load()):
        assert isinstance(leaf.get("body"), str) and leaf["body"].strip()
        assert leaf["body"] != "TODO"
        assert isinstance(leaf.get("_note"), str) and leaf["_note"].strip()
        assert leaf.get("claim_level") == "bounded_interpretation"
        assert isinstance(leaf.get("requires_evidence"), list) and leaf["requires_evidence"]


def test_isolation_demanding_leaf_names_social_thinning_without_guarantee():
    leaf = _load()["isolation"]["demanding"]
    body = leaf["body"].lower()
    assert "isolation or social thinning" in body
    assert "does not mean" in body
    assert "lonely or miserable" in body
    assert "real caution" in body


def test_context_modifier_leaves_do_not_use_empty_softening_phrases():
    for leaf in _leaf_dicts(_load()):
        body = leaf["body"].lower()
        for phrase in FORBIDDEN_SOFTENING_PHRASES:
            assert phrase not in body, leaf
