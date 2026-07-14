"""
Tests for the Round 4 Place Resonance block scaffold under
products/location_services/blocks/plainspeak/.

These are JSON content scaffolds (TODO bodies + rich _note guidance), not
runtime code -- there is no selector/loader wired to them yet (deliberately
out of scope for this round; see BLOCK_SCHEMA.md's Initial Content Priority
and PROSE_PURPOSE_REVIEW.md's Recommended Claude Boundary). This file
validates the scaffold's structural contract against the real evidence
record fields documented in LOCATION_EVIDENCE_RECORD_CONTRACT.md and
BLOCK_SCHEMA.md -- not against any rendering behavior, since none exists
yet.

Covers:
- all four files exist and parse as valid JSON
- required top-level keys/families are present
- canonical long angle names only (no ASC/MC/DSC/IC, no Vertex)
- contact strength bands match engine.location_services.CONTACT_STRENGTH_BANDS exactly
- movement types match the real v0.1 set and exclude the deferred domain buckets
- literal "TODO" bodies are present (intentional scaffold state) and every
  TODO leaf carries a non-empty _note, claim_level, and requires_evidence
- unsupported_method keys match engine.location_services.UNSUPPORTED_METHODS exactly
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from engine.location_services import CONTACT_STRENGTH_BANDS, UNSUPPORTED_METHODS

BLOCKS_DIR = Path(__file__).resolve().parent.parent / "products" / "location_services" / "blocks" / "plainspeak"

FILES = {
    "technical_appendix": BLOCKS_DIR / "technical_appendix_blocks.json",
    "relocated_angle_contact": BLOCKS_DIR / "relocated_angle_contact_blocks.json",
    "planet_relocated_house": BLOCKS_DIR / "planet_relocated_house_blocks.json",
    "location_synthesis": BLOCKS_DIR / "location_synthesis_blocks.json",
}

CANONICAL_ANGLE_NAMES = {"Ascendant", "Midheaven", "Descendant", "Imum_Coeli"}
FORBIDDEN_ANGLE_ALIASES = {"ASC", "MC", "DSC", "IC", "Asc", "Mc", "Dsc", "Ic"}

# Real v0.1 movement types (engine.location_services._movement_type's actual
# return values). moves_public/private/relational/operational are the
# deferred house-domain taxonomy this round must not invent.
REAL_MOVEMENT_TYPES = {"same_house", "newly_angular", "leaves_angular", "house_changed", "unknown"}
FORBIDDEN_DOMAIN_MOVEMENT_TYPES = {"moves_public", "moves_private", "moves_relational", "moves_operational"}

CORE_BODIES = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
ANGULAR_HOUSES = {1, 4, 7, 10}

SYNTHESIS_CATEGORIES = {
    "convergent_place_signature", "angle_led_signature", "house_shift_led_signature",
    "repeated_body_signature", "quiet_continuity_signature", "mixed_public_private_signature",
    "purpose_aligned_signature", "purpose_tradeoff_signature", "low_signal_signature", "fallback",
}


def _load(key: str) -> dict:
    return json.loads(FILES[key].read_text(encoding="utf-8"))


def _all_keys(node, keys: set | None = None) -> set:
    if keys is None:
        keys = set()
    if isinstance(node, dict):
        keys.update(node.keys())
        for value in node.values():
            _all_keys(value, keys)
    return keys


def _leaf_dicts(node):
    """Yields every dict that looks like a terminal scaffold leaf (has a 'body' key)."""
    if isinstance(node, dict):
        if "body" in node:
            yield node
        for value in node.values():
            yield from _leaf_dicts(value)


# ── Files exist and parse ───────────────────────────────────────────────────

@pytest.mark.parametrize("key", list(FILES.keys()))
def test_block_file_exists(key):
    assert FILES[key].exists(), f"missing scaffold file: {FILES[key]}"


@pytest.mark.parametrize("key", list(FILES.keys()))
def test_block_file_is_valid_json(key):
    assert isinstance(_load(key), dict)


@pytest.mark.parametrize("key", list(FILES.keys()))
def test_block_file_has_note_and_version(key):
    data = _load(key)
    assert isinstance(data.get("_note"), str) and data["_note"].strip()
    assert data.get("_version") == "0.1.0-scaffold"


@pytest.mark.parametrize("key", list(FILES.keys()))
def test_block_file_has_top_level_fallback(key):
    assert "fallback" in _load(key)


# ── Canonical angle names ───────────────────────────────────────────────────

def test_relocated_angle_contact_blocks_use_only_canonical_angle_names():
    data = _load("relocated_angle_contact")
    top_level_angle_keys = set(data.keys()) - {"_note", "_version", "fallback"}
    assert top_level_angle_keys == CANONICAL_ANGLE_NAMES
    assert "Vertex" not in data, (
        "Vertex is never emitted in relocated_angle_contacts (excluded from "
        "AXIS_ANGLES in formulas/standard/angularity.py) and must not appear here"
    )


@pytest.mark.parametrize("key", list(FILES.keys()))
def test_no_forbidden_angle_aliases_as_keys(key):
    parsed_keys = _all_keys(_load(key))
    hit = parsed_keys & FORBIDDEN_ANGLE_ALIASES
    assert not hit, f"{key} uses short angle alias(es) {hit} as JSON key(s); use long canonical names only"


# ── Contact strength bands ──────────────────────────────────────────────────

def test_contact_strength_band_labels_match_engine_constant():
    expected_bands = {label for label, _ in CONTACT_STRENGTH_BANDS}
    assert expected_bands == {"tight", "moderate", "wide"}


def test_relocated_angle_contact_blocks_use_exactly_the_real_bands():
    data = _load("relocated_angle_contact")
    expected_bands = {label for label, _ in CONTACT_STRENGTH_BANDS}
    for angle in CANONICAL_ANGLE_NAMES:
        for body in list(CORE_BODIES) + ["fallback"]:
            band_keys = set(data[angle][body].keys()) - {"_note", "fallback"}
            assert band_keys == expected_bands, (angle, body, band_keys)


# ── Movement types ───────────────────────────────────────────────────────────

def _reachable_movement_types(house_number: int) -> set:
    if house_number in ANGULAR_HOUSES:
        return {"same_house", "newly_angular", "house_changed"}
    return {"same_house", "leaves_angular", "house_changed"}


def test_planet_relocated_house_blocks_movement_types_are_real_and_reachable():
    data = _load("planet_relocated_house")
    for body in list(CORE_BODIES) + ["fallback"]:
        block = data[body]
        for house_number in range(1, 13):
            movement_keys = set(block[str(house_number)].keys()) - {"_note", "fallback"}
            assert movement_keys <= REAL_MOVEMENT_TYPES, (body, house_number, movement_keys)
            assert movement_keys == _reachable_movement_types(house_number), (body, house_number, movement_keys)


def test_no_forbidden_domain_movement_types_anywhere_in_house_file():
    hit = _all_keys(_load("planet_relocated_house")) & FORBIDDEN_DOMAIN_MOVEMENT_TYPES
    assert not hit, f"deferred house-domain taxonomy leaked into the scaffold as engine movement_type key(s): {hit}"


@pytest.mark.parametrize("key", list(FILES.keys()))
def test_no_forbidden_domain_movement_types_in_any_scaffold_file(key):
    hit = _all_keys(_load(key)) & FORBIDDEN_DOMAIN_MOVEMENT_TYPES
    assert not hit, f"{key} must not invent house-domain taxonomy keys: {hit}"


def test_planet_relocated_house_blocks_cover_core_bodies_all_houses_and_unknown():
    data = _load("planet_relocated_house")
    for body in CORE_BODIES:
        assert body in data
        house_keys = {k for k in data[body] if k.isdigit()}
        assert house_keys == {str(n) for n in range(1, 13)}
        assert "unknown" in data[body]


def test_planet_relocated_house_blocks_have_fallback_body_covering_all_houses():
    data = _load("planet_relocated_house")
    fallback = data["fallback"]
    house_keys = {k for k in fallback if k.isdigit()}
    assert house_keys == {str(n) for n in range(1, 13)}
    assert "unknown" in fallback


# ── Technical appendix ───────────────────────────────────────────────────────

def test_technical_appendix_unsupported_method_keys_match_engine_constant():
    data = _load("technical_appendix")
    method_keys = set(data["unsupported_method"].keys()) - {"_note", "fallback"}
    assert method_keys == set(UNSUPPORTED_METHODS)


def test_technical_appendix_covers_expected_families():
    data = _load("technical_appendix")
    for family in ("calculation_note", "unsupported_method", "confidence_note", "coordinate_precision_note", "warning_summary"):
        assert family in data, f"missing technical_appendix family: {family}"


def test_technical_appendix_warning_summary_covers_real_engine_templates():
    from engine.location_services import _WARNING_TEMPLATES

    data = _load("technical_appendix")
    warning_keys = set(data["warning_summary"].keys()) - {"_note", "fallback"}
    real_template_keys = {key for key, _ in _WARNING_TEMPLATES}
    assert real_template_keys <= warning_keys | {"fallback"}
    assert warning_keys == real_template_keys


def test_technical_appendix_confidence_note_covers_reachable_states():
    data = _load("technical_appendix")
    confidence_keys = set(data["confidence_note"].keys()) - {"_note", "fallback"}
    assert confidence_keys == {
        "exact_birth_time", "approximate_birth_time", "unknown_birth_time", "angle_dependent_unavailable",
    }


# ── Location synthesis ───────────────────────────────────────────────────────

def test_location_synthesis_covers_all_prose_purpose_review_categories():
    data = _load("location_synthesis")
    top_level = set(data.keys()) - {"_note", "_version"}
    assert top_level == SYNTHESIS_CATEGORIES


def test_location_synthesis_mixed_public_private_names_taxonomy_boundary():
    """Contradiction/conflict categories are deferred unless scaffolded with an
    explicit 'taxonomy not implemented' note -- verify that note is actually present."""
    data = _load("location_synthesis")
    note = data["mixed_public_private_signature"]["_note"]
    assert "TAXONOMY NOT IMPLEMENTED" in note


def test_location_synthesis_does_not_populate_contradictory_evidence_logic():
    text = FILES["location_synthesis"].read_text(encoding="utf-8")
    assert '"contradictory_evidence"' not in text or "always" in text.lower()


# ── TODO scaffold status (intentional, not final prose) ─────────────────────

@pytest.mark.parametrize("key", list(FILES.keys()))
def test_todo_leaves_are_present_and_are_the_only_body_value(key):
    """
    Literal TODO is allowed only in new scaffold-only files with tests that
    knowingly permit it (CONTENT_LEAD_HANDOFF.md's No-Prose Scaffolding
    Preference) -- this is that test. Every leaf's body must be exactly
    "TODO"; this round must not author any final reader-facing prose.
    """
    leaves = list(_leaf_dicts(_load(key)))
    assert leaves, f"{key} has no scaffold leaves at all"
    non_todo = [leaf for leaf in leaves if leaf.get("body") != "TODO"]
    assert not non_todo, f"{key} has {len(non_todo)} leaf(ves) with a non-TODO body -- this round must not author final prose"


@pytest.mark.parametrize("key", list(FILES.keys()))
def test_every_todo_leaf_has_note_claim_level_and_requires_evidence(key):
    for leaf in _leaf_dicts(_load(key)):
        assert isinstance(leaf.get("_note"), str) and leaf["_note"].strip(), leaf
        assert leaf.get("claim_level"), leaf
        assert isinstance(leaf.get("requires_evidence"), list) and leaf["requires_evidence"], leaf


def test_technical_appendix_leaves_use_technical_disclosure_claim_level():
    for leaf in _leaf_dicts(_load("technical_appendix")):
        assert leaf["claim_level"] == "technical_disclosure"


@pytest.mark.parametrize("key", ["relocated_angle_contact", "planet_relocated_house", "location_synthesis"])
def test_interpretive_files_use_bounded_interpretation_claim_level(key):
    for leaf in _leaf_dicts(_load(key)):
        assert leaf["claim_level"] == "bounded_interpretation"


# ── Leaf-count sanity (catches silent grid truncation) ──────────────────────

def test_relocated_angle_contact_blocks_leaf_count_matches_expected_grid_size():
    # 4 angles x (10 bodies + 1 fallback) x 3 bands = 132, plus 1 top-level
    # fallback, plus 4 angle-level fallback-body fallback leaves, plus 10
    # per-body fallback leaves, plus 4 per-fallback-body fallback leaves.
    leaves = list(_leaf_dicts(_load("relocated_angle_contact")))
    assert len(leaves) == 177


def test_planet_relocated_house_blocks_leaf_count_matches_expected_grid_size():
    leaves = list(_leaf_dicts(_load("planet_relocated_house")))
    assert len(leaves) == 539
