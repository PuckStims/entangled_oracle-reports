"""
Structured block selector for synastry round-1 prose leaves.

Unlike selectors.block_selector.select_block(), these helpers return the full
leaf dictionary so the synastry assembler can keep authored prose together with
its note, claim level, and evidence requirements.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import REPORT_BLOCK_DIRS
from engine.synastry import ANGLE_POINTS, ASPECT_POLARITY, CORE_BODIES, OPTIONAL_BODIES, TOPIC_SPECS


REPORT_TYPE = "synastry"
REQUIRED_LEAF_KEYS = {"body", "_note", "claim_level", "requires_evidence"}
ALL_BODIES = set(CORE_BODIES) | set(OPTIONAL_BODIES)
ANGLE_SET = set(ANGLE_POINTS)
BODY_PAIR_FAMILIES = {
    "luminary_contact",
    "personal_planet_contact",
    "social_planet_contact",
    "outer_planet_contact",
    "angle_contact",
    "node_or_chiron_contact",
}

_cache: dict[str, dict[str, Any]] = {}


def clear_cache() -> None:
    _cache.clear()


def _blocks_root() -> str:
    root = REPORT_BLOCK_DIRS.get(REPORT_TYPE)
    if not root:
        raise FileNotFoundError(f"Unknown block report_type: {REPORT_TYPE}")
    return root


def _load_blocks(block_file: str) -> dict[str, Any]:
    cache_key = f"{REPORT_TYPE}/{block_file}"
    if cache_key not in _cache:
        path = os.path.join(_blocks_root(), f"{block_file}.json")
        with open(path, "r", encoding="utf-8") as handle:
            parsed = json.load(handle)
        if not isinstance(parsed, dict):
            raise ValueError(f"Synastry block file must contain an object: {path}")
        _cache[cache_key] = parsed
    return _cache[cache_key]


def _leaf_or_none(node: Any) -> dict[str, Any] | None:
    if isinstance(node, dict) and REQUIRED_LEAF_KEYS <= set(node):
        return node
    return None


def _copy_leaf(leaf: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(leaf)


def _fallback_leaf(blocks: dict[str, Any]) -> dict[str, Any]:
    leaf = _leaf_or_none(blocks.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    raise KeyError("Synastry block file has no structured fallback leaf.")


def _select_family_leaf(blocks: dict[str, Any], family: str, sub_key: str) -> dict[str, Any]:
    family_block = blocks.get(family)
    if not isinstance(family_block, dict):
        return _fallback_leaf(blocks)
    leaf = _leaf_or_none(family_block.get(str(sub_key)))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(family_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def classify_body_pair_family(body_names: list[str] | tuple[str, ...] | set[str]) -> str:
    names = {str(name) for name in body_names if isinstance(name, str)}
    if names & ANGLE_SET:
        return "angle_contact"
    if names & {"North_Node", "South_Node", "Chiron"}:
        return "node_or_chiron_contact"
    if names & {"Sun", "Moon"}:
        return "luminary_contact"
    if names <= {"Mercury", "Venus", "Mars"} and names:
        return "personal_planet_contact"
    if names & {"Jupiter", "Saturn"}:
        return "social_planet_contact"
    if names & {"Uranus", "Neptune", "Pluto"}:
        return "outer_planet_contact"
    return "fallback"


def select_technical_appendix_leaf(family: str, sub_key: str) -> dict[str, Any]:
    blocks = _load_blocks("technical_appendix_blocks")
    return _select_family_leaf(blocks, family, sub_key)


def select_directional_aspect_leaf(aspect: str | None, dependency: str | None, polarity: str | None) -> dict[str, Any]:
    blocks = _load_blocks("directional_aspect_blocks")
    aspect_block = blocks.get("aspect", {})
    if not isinstance(aspect_block, dict):
        return _fallback_leaf(blocks)

    normalized_aspect = str(aspect or "fallback")
    normalized_dependency = "angle_dependent" if dependency != "body_to_body" else "body_to_body"
    normalized_polarity = str(polarity or "mixed")

    branch = aspect_block.get(normalized_aspect)
    if not isinstance(branch, dict):
        return _leaf_or_none(aspect_block.get("fallback")) and _copy_leaf(aspect_block["fallback"]) or _fallback_leaf(blocks)

    dependency_block = branch.get(normalized_dependency)
    if isinstance(dependency_block, dict):
        leaf = _leaf_or_none(dependency_block.get(normalized_polarity))
        if leaf:
            return _copy_leaf(leaf)
    leaf = _leaf_or_none(branch.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(aspect_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def select_body_pair_family_leaf(family: str) -> dict[str, Any]:
    blocks = _load_blocks("directional_aspect_blocks")
    body_pair_block = blocks.get("body_pair_family", {})
    if not isinstance(body_pair_block, dict):
        return _fallback_leaf(blocks)
    leaf = _leaf_or_none(body_pair_block.get(str(family)))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(body_pair_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def select_house_overlay_source_body_leaf(body: str | None) -> dict[str, Any]:
    blocks = _load_blocks("house_overlay_blocks")
    source_body_block = blocks.get("source_body", {})
    if not isinstance(source_body_block, dict):
        return _fallback_leaf(blocks)
    key = str(body or "fallback")
    leaf = _leaf_or_none(source_body_block.get(key))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(source_body_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def select_house_overlay_target_house_leaf(house_number: int | str | None) -> dict[str, Any]:
    blocks = _load_blocks("house_overlay_blocks")
    target_house_block = blocks.get("target_house", {})
    if not isinstance(target_house_block, dict):
        return _fallback_leaf(blocks)
    key = str(house_number) if house_number is not None else "fallback"
    leaf = _leaf_or_none(target_house_block.get(key))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(target_house_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def select_house_overlay_confidence_leaf(confidence_state: str | None, *, withheld: bool = False) -> dict[str, Any]:
    blocks = _load_blocks("house_overlay_blocks")
    confidence_block = blocks.get("confidence_band", {})
    if not isinstance(confidence_block, dict):
        return _fallback_leaf(blocks)
    key = "withheld" if withheld else str(confidence_state or "fallback")
    leaf = _leaf_or_none(confidence_block.get(key))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(confidence_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def select_composite_body_midpoint_leaf(body: str | None) -> dict[str, Any]:
    blocks = _load_blocks("composite_blocks")
    body_block = blocks.get("body_midpoint", {})
    if not isinstance(body_block, dict):
        return _fallback_leaf(blocks)
    key = str(body or "fallback")
    leaf = _leaf_or_none(body_block.get(key))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(body_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def select_composite_aspect_leaf(aspect: str | None) -> dict[str, Any]:
    blocks = _load_blocks("composite_blocks")
    aspect_block = blocks.get("composite_aspect", {})
    if not isinstance(aspect_block, dict):
        return _fallback_leaf(blocks)
    key = str(aspect or "fallback")
    leaf = _leaf_or_none(aspect_block.get(key))
    if leaf:
        return _copy_leaf(leaf)
    leaf = _leaf_or_none(aspect_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)


def select_composite_ambiguity_leaf(kind: str | None) -> dict[str, Any]:
    blocks = _load_blocks("composite_blocks")
    return _select_family_leaf(blocks, "ambiguity_note", str(kind or "fallback"))


def select_composite_unsupported_layer_leaf(layer: str | None) -> dict[str, Any]:
    blocks = _load_blocks("composite_blocks")
    return _select_family_leaf(blocks, "unsupported_layer", str(layer or "fallback"))


def select_repeated_theme_type_leaf(theme_type: str | None) -> dict[str, Any]:
    blocks = _load_blocks("repeated_theme_blocks")
    return _select_family_leaf(blocks, "theme_type", str(theme_type or "fallback"))


def select_repeated_theme_confidence_leaf(confidence_state: str | None) -> dict[str, Any]:
    blocks = _load_blocks("repeated_theme_blocks")
    return _select_family_leaf(blocks, "confidence_state", str(confidence_state or "fallback"))


def select_topic_signature_leaf(signature_key: str | None) -> dict[str, Any]:
    blocks = _load_blocks("topic_convergence_blocks")
    return _select_family_leaf(blocks, "topic_signature", str(signature_key or "fallback"))


def select_topic_polarity_leaf(polarity: str | None) -> dict[str, Any]:
    blocks = _load_blocks("topic_convergence_blocks")
    return _select_family_leaf(blocks, "polarity", str(polarity or "fallback"))


def select_topic_convergence_leaf(localization: str | None) -> dict[str, Any]:
    blocks = _load_blocks("topic_convergence_blocks")
    return _select_family_leaf(blocks, "convergence", str(localization or "fallback"))


def select_topic_confidence_leaf(confidence_state: str | None) -> dict[str, Any]:
    blocks = _load_blocks("topic_convergence_blocks")
    return _select_family_leaf(blocks, "confidence_note", str(confidence_state or "fallback"))

