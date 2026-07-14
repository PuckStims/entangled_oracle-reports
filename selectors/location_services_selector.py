"""
Structured block selector for Location Services.

Unlike selectors.block_selector.select_block(), these helpers return the
whole scaffold leaf dict. Location Services leaves carry body text plus
metadata (_note, claim_level, requires_evidence), and the selector should
preserve that structure for later report assembly.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import REPORT_BLOCK_DIRS
from formulas.standard.normalization import normalize_angle_name


REPORT_TYPE = "location_services"
CORE_BODIES = {
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
}

# Non-core bodies that have named sub-keys inside the block-file "fallback"
# body block, allowing body-specific prose without exploding the grid.
# Any body not in CORE_BODIES and not in this set routes to the generic
# "fallback" body prose (which is correct for anonymous custom asteroids).
NAMED_NON_CORE_BODIES = {
    "Chiron",
    "North_Node",
    "South_Node",
    "Lilith_BML",
}

ANGLE_CONTACT_ANGLES = {"Ascendant", "Midheaven", "Descendant", "Imum_Coeli"}
REQUIRED_LEAF_KEYS = {"body", "_note", "claim_level", "requires_evidence"}

_cache: dict[str, dict[str, Any]] = {}


def clear_cache() -> None:
    """Clear the local Location Services block cache."""
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
            raise ValueError(f"Location Services block file must contain an object: {path}")
        _cache[cache_key] = parsed
    return _cache[cache_key]


def _body_key(body: str | None) -> str:
    candidate = str(body or "").strip()
    return candidate if candidate in CORE_BODIES else "fallback"


def _normalize_angle_for_contact(angle: str | None) -> str:
    normalized = normalize_angle_name(angle)
    if normalized == "Vertex":
        raise ValueError("Vertex is not emitted in relocated_angle_contacts.")
    if normalized not in ANGLE_CONTACT_ANGLES:
        raise ValueError(f"Unsupported relocated angle contact angle: {angle!r}")
    return normalized


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
    raise KeyError("Location Services block file has no structured fallback leaf.")


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


def _select_from_fallback_body_block(
    fallback_body_block: dict[str, Any],
    body: str | None,
    strength_key: str,
) -> dict[str, Any] | None:
    """
    Within a block-file "fallback" body section, try:
      1. A named sub-key for common non-core bodies (Chiron, North_Node, etc.)
         at the given strength.
      2. The generic strength key (tight / moderate / wide / fallback).
      3. The generic fallback key.

    Returns a leaf dict or None if the block itself is not a dict.
    This allows named non-core bodies to carry body-specific prose without
    needing their own top-level grid entry, while anonymous asteroids still
    get the well-worded generic prose.
    """
    if not isinstance(fallback_body_block, dict):
        return None

    body_name = str(body or "").strip()

    # 1. Try named sub-key if this body is a known named non-core body.
    if body_name in NAMED_NON_CORE_BODIES:
        named_block = fallback_body_block.get(body_name)
        if isinstance(named_block, dict):
            leaf = _leaf_or_none(named_block.get(strength_key))
            if leaf:
                return _copy_leaf(leaf)
            leaf = _leaf_or_none(named_block.get("fallback"))
            if leaf:
                return _copy_leaf(leaf)

    # 2. Try the generic strength key.
    leaf = _leaf_or_none(fallback_body_block.get(strength_key))
    if leaf:
        return _copy_leaf(leaf)

    # 3. Try the generic fallback key.
    leaf = _leaf_or_none(fallback_body_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)

    return None


def select_technical_appendix_leaf(family: str, sub_key: str) -> dict[str, Any]:
    """
    Select a technical appendix leaf by family and sub-key.

    Examples:
    - ("calculation_note", "relocated_chart")
    - ("unsupported_method", "astrocartography")
    - ("warning_summary", "no_natal_condition_record")
    """
    blocks = _load_blocks("technical_appendix_blocks")
    return _select_family_leaf(blocks, family, sub_key)


def select_angle_contact_leaf(angle: str, body: str, contact_strength: str) -> dict[str, Any]:
    """
    Select a structured leaf for a relocated angle contact.

    Key path: angle -> body (or named non-core key inside fallback) -> contact_strength.

    For core bodies (Sun-Pluto): angle -> body -> contact_strength.
    For named non-core bodies (Chiron, North_Node, South_Node, Lilith_BML):
        angle -> "fallback" body block -> body_name -> contact_strength.
    For anonymous asteroids and unrecognised bodies:
        angle -> "fallback" body block -> contact_strength (generic prose).
    """
    blocks = _load_blocks("relocated_angle_contact_blocks")
    angle_key = _normalize_angle_for_contact(angle)
    body_key = _body_key(body)

    angle_block = blocks.get(angle_key)
    if not isinstance(angle_block, dict):
        return _fallback_leaf(blocks)

    if body_key != "fallback":
        # Core body path (unchanged).
        body_block = angle_block.get(body_key)
        if isinstance(body_block, dict):
            leaf = _leaf_or_none(body_block.get(str(contact_strength)))
            if leaf:
                return _copy_leaf(leaf)
            leaf = _leaf_or_none(body_block.get("fallback"))
            if leaf:
                return _copy_leaf(leaf)
        # Core body block missing -- fall through to angle fallback.
        leaf = _leaf_or_none(angle_block.get("fallback"))
        if leaf:
            return _copy_leaf(leaf)
        return _fallback_leaf(blocks)

    # Non-core body path: look inside the "fallback" body block.
    fallback_body_block = angle_block.get("fallback")
    result = _select_from_fallback_body_block(fallback_body_block, body, str(contact_strength))
    if result is not None:
        return result

    # Top-level file fallback as last resort.
    return _fallback_leaf(blocks)


def select_planet_house_leaf(
    body: str,
    relocated_house: int | None,
    movement_type: str,
) -> dict[str, Any]:
    """
    Select body/fallback -> relocated_house -> movement_type.

    The scaffold stores movement_type == "unknown" as a body-level leaf, not
    under a house number. A missing relocated house uses the same route.

    For named non-core bodies (Chiron, North_Node, South_Node, Lilith_BML),
    the selector first tries a named sub-key inside the "fallback" body block's
    house entry before using the generic fallback prose.
    """
    blocks = _load_blocks("planet_relocated_house_blocks")
    body_key = _body_key(body)
    body_block = blocks.get(body_key)
    if not isinstance(body_block, dict):
        return _fallback_leaf(blocks)

    if movement_type == "unknown" or relocated_house is None:
        # Unknown house: use the body-level "unknown" key.
        if body_key == "fallback":
            # Try named non-core body's unknown key first.
            body_name = str(body or "").strip()
            if body_name in NAMED_NON_CORE_BODIES:
                named_block = body_block.get(body_name)
                if isinstance(named_block, dict):
                    leaf = _leaf_or_none(named_block.get("unknown"))
                    if leaf:
                        return _copy_leaf(leaf)
        leaf = _leaf_or_none(body_block.get("unknown"))
        if leaf:
            return _copy_leaf(leaf)
        return _fallback_leaf(blocks)

    try:
        house_key = str(int(relocated_house))
    except (TypeError, ValueError):
        leaf = _leaf_or_none(body_block.get("unknown"))
        if leaf:
            return _copy_leaf(leaf)
        return _fallback_leaf(blocks)

    house_block = body_block.get(house_key)
    if not isinstance(house_block, dict):
        leaf = _leaf_or_none(body_block.get("unknown"))
        if leaf:
            return _copy_leaf(leaf)
        return _fallback_leaf(blocks)

    if body_key == "fallback":
        # Non-core body: try named routing inside the house block.
        body_name = str(body or "").strip()
        if body_name in NAMED_NON_CORE_BODIES:
            named_block = house_block.get(body_name)
            if isinstance(named_block, dict):
                leaf = _leaf_or_none(named_block.get(str(movement_type)))
                if leaf:
                    return _copy_leaf(leaf)
                leaf = _leaf_or_none(named_block.get("fallback"))
                if leaf:
                    return _copy_leaf(leaf)

    leaf = _leaf_or_none(house_block.get(str(movement_type)))
    if leaf:
        return _copy_leaf(leaf)

    leaf = _leaf_or_none(house_block.get("fallback"))
    if leaf:
        return _copy_leaf(leaf)

    return _fallback_leaf(blocks)


def select_synthesis_leaf(synthesis_category: str) -> dict[str, Any]:
    """Select a location synthesis leaf by category."""
    blocks = _load_blocks("location_synthesis_blocks")
    leaf = _leaf_or_none(blocks.get(str(synthesis_category)))
    if leaf:
        return _copy_leaf(leaf)
    return _fallback_leaf(blocks)

