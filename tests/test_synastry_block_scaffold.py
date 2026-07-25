import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import REPORT_BLOCK_DIRS
from engine.synastry import ASPECT_POLARITY, TOPIC_SPECS


BLOCKS_DIR = Path(__file__).resolve().parent.parent / "products" / "synastry" / "blocks" / "plainspeak"
SCHEMA_DOC = Path(__file__).resolve().parent.parent / "products" / "synastry" / "BLOCK_SCHEMA.md"

FILES = {
    "technical_appendix": BLOCKS_DIR / "technical_appendix_blocks.json",
    "directional_aspect": BLOCKS_DIR / "directional_aspect_blocks.json",
    "house_overlay": BLOCKS_DIR / "house_overlay_blocks.json",
    "composite": BLOCKS_DIR / "composite_blocks.json",
    "repeated_theme": BLOCKS_DIR / "repeated_theme_blocks.json",
    "topic_convergence": BLOCKS_DIR / "topic_convergence_blocks.json",
}

FORBIDDEN_VERDICT_TERMS = {
    "compatible",
    "incompatible",
    "doomed",
    "soulmate",
    "twin flame",
    "destined",
    "karmic debt",
}

CORE_BODY_KEYS = {
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Chiron",
    "North_Node",
    "South_Node",
}


def _load(key: str) -> dict:
    return json.loads(FILES[key].read_text(encoding="utf-8"))


def _leaf_dicts(node):
    if isinstance(node, dict):
        if "body" in node:
            yield node
        for value in node.values():
            yield from _leaf_dicts(value)


def _all_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _all_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _all_strings(value)


def _keys(node, acc=None):
    if acc is None:
        acc = set()
    if isinstance(node, dict):
        acc.update(node.keys())
        for value in node.values():
            _keys(value, acc)
    return acc


def test_synastry_block_directory_is_registered_without_product_exposure():
    assert REPORT_BLOCK_DIRS["synastry"] == str(BLOCKS_DIR)


def test_schema_doc_exists_and_marks_round1_authored_boundary():
    text = SCHEMA_DOC.read_text(encoding="utf-8")
    assert "Status: v0.1 round 1 authored prose" in text
    assert "round-1 testing" in text
    assert "still not exposed as a client report" in text


def test_all_round1_files_exist_and_parse():
    for path in FILES.values():
        assert path.exists(), path
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


def test_all_round1_files_have_version_note_and_fallback():
    for key in FILES:
        data = _load(key)
        assert data["_version"] == "0.1.0-round1"
        assert isinstance(data["_note"], str) and len(data["_note"]) > 80
        assert "fallback" in data


def test_every_terminal_leaf_has_authored_body_note_claim_level_and_evidence():
    for key in FILES:
        leaves = list(_leaf_dicts(_load(key)))
        assert leaves, key
        for leaf in leaves:
            assert isinstance(leaf["body"], str) and len(leaf["body"].strip()) >= 40, leaf
            assert leaf["body"].strip() != "TODO", leaf
            assert isinstance(leaf.get("_note"), str) and len(leaf["_note"]) >= 40, leaf
            assert leaf.get("claim_level") in {"bounded_interpretation", "technical_disclosure"}, leaf
            assert isinstance(leaf.get("requires_evidence"), list) and leaf["requires_evidence"], leaf


def test_no_terminal_leaf_contains_placeholder_todo_text():
    for key in FILES:
        for leaf in _leaf_dicts(_load(key)):
            assert "TODO" not in leaf["body"], (key, leaf)


def test_no_verdict_language_in_round1_notes_or_schema():
    texts = []
    for path in list(FILES.values()) + [SCHEMA_DOC]:
        texts.extend(
            _all_strings(json.loads(path.read_text(encoding="utf-8")))
            if path.suffix == ".json"
            else [path.read_text(encoding="utf-8")]
        )
    joined = "\n".join(texts).lower()
    for term in FORBIDDEN_VERDICT_TERMS:
        # The schema is allowed to name forbidden words only in its explicit avoid list.
        assert len(re.findall(rf"\b{re.escape(term)}\b", joined)) <= 1, term


def test_directional_aspect_file_covers_all_major_aspects_and_polarities():
    data = _load("directional_aspect")
    aspect_keys = set(data["aspect"].keys()) - {"_note", "fallback"}
    assert aspect_keys == set(ASPECT_POLARITY)
    for aspect, polarity in ASPECT_POLARITY.items():
        assert polarity in data["aspect"][aspect]["body_to_body"]
        assert polarity in data["aspect"][aspect]["angle_dependent"]


def test_house_overlay_file_covers_core_source_bodies_and_twelve_houses():
    data = _load("house_overlay")
    source_body_keys = set(data["source_body"].keys()) - {"_note", "fallback"}
    assert CORE_BODY_KEYS <= source_body_keys
    house_keys = set(data["target_house"].keys()) - {"_note", "fallback"}
    assert house_keys == {str(index) for index in range(1, 13)}


def test_composite_file_covers_body_midpoints_aspects_and_non_live_layers():
    data = _load("composite")
    body_keys = set(data["body_midpoint"].keys()) - {"_note", "fallback"}
    assert CORE_BODY_KEYS <= body_keys
    aspect_keys = set(data["composite_aspect"].keys()) - {"_note", "fallback"}
    assert aspect_keys == set(ASPECT_POLARITY)
    unsupported = set(data["unsupported_layer"].keys()) - {"_note", "fallback"}
    assert unsupported == {"composite_houses", "davison"}


def test_repeated_theme_file_covers_engine_theme_types():
    data = _load("repeated_theme")
    theme_types = set(data["theme_type"].keys()) - {"_note", "fallback"}
    assert theme_types == {
        "same_sign_emphasis",
        "same_element_concentration",
        "same_modality_concentration",
        "repeated_aspect_family",
        "shared_house_emphasis",
    }


def test_topic_convergence_file_covers_engine_topic_specs_and_localization():
    data = _load("topic_convergence")
    topic_keys = set(data["topic_signature"].keys()) - {"_note", "fallback"}
    assert topic_keys == set(TOPIC_SPECS)
    localization_keys = set(data["convergence"].keys()) - {"_note", "fallback"}
    assert localization_keys == {"body_only", "angle_localized", "house_localized"}


def test_technical_appendix_file_covers_sidecar_boundaries():
    data = _load("technical_appendix")
    assert {"calculation_note", "confidence_note", "withheld_reason", "unsupported_layer", "claim_safety"} <= set(data)
    unsupported = set(data["unsupported_layer"].keys()) - {"_note", "fallback"}
    assert unsupported == {"composite_houses", "davison", "relationship_timing"}
    claim_safety = set(data["claim_safety"].keys()) - {"_note", "fallback"}
    assert claim_safety == {"client_report_available_false", "relationship_verdicts_supported_false"}


def test_no_short_angle_alias_keys_in_any_synastry_block_file():
    forbidden = {"ASC", "MC", "DSC", "IC", "Asc", "Mc", "Dsc", "Ic"}
    for key in FILES:
        assert not (_keys(_load(key)) & forbidden), key
