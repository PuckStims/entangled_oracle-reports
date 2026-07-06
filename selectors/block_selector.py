"""
selectors/block_selector.py — Paragraph Block Selector
Loads block databases from JSON and selects the right block
using the nested key path defined in the template specs.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REPORT_BLOCK_DIRS

# Cache loaded JSON files so we don't re-read from disk on every selection
_block_cache: dict = {}


def _load_blocks(report_type: str, block_file: str) -> dict:
    """Loads a block JSON file and caches it."""
    cache_key = f"{report_type}/{block_file}"
    if cache_key not in _block_cache:
        base_dir = REPORT_BLOCK_DIRS.get(report_type)
        if not base_dir:
            raise FileNotFoundError(f"Unknown block report_type: {report_type}")
        path = os.path.join(base_dir, f"{block_file}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                _block_cache[cache_key] = json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Block file not found: {path}") from exc
    return _block_cache[cache_key]


def clear_cache():
    """Clears the block cache — useful when editing blocks during development."""
    _block_cache.clear()


def select_block(report_type: str, block_file: str, *keys: str,
                 fallback: str = "") -> str:
    """
    Selects a paragraph block from a JSON database using a key path.

    Usage:
        select_block("daily_horoscope", "todays_sky", "new_moon", "fire")
        select_block("year_ahead", "transit_blocks", "Jupiter", "Trine", "Moon")  # transit_planet → aspect_type → natal_planet_name

    Falls back through the key hierarchy if an exact match isn't found:
        1. Try full key path
        2. Try dropping the last key
        3. Try dropping the last two keys
        4. Return fallback string

    The fallback hierarchy lets you write a "generic" block at a higher level
    that catches any combination you haven't written a specific block for yet.
    Use the key "fallback" at any level as a catch-all.
    """
    try:
        blocks = _load_blocks(report_type, block_file)
    except FileNotFoundError:
        return fallback or f"[MISSING BLOCK FILE: {report_type}/{block_file}]"

    # Try exact key path first
    result = _traverse(blocks, list(keys))
    if isinstance(result, str):
        return result

    # Try fallback key at current level
    keys_list = list(keys)
    while keys_list:
        result = _traverse(blocks, keys_list[:-1] + ["fallback"])
        if isinstance(result, str):
            return result
        keys_list.pop()

    # Last resort: top-level fallback
    if "fallback" in blocks and isinstance(blocks["fallback"], str):
        return blocks["fallback"]

    return fallback or f"[BLOCK NOT FOUND: {report_type}/{block_file}/{'/'.join(keys)}]"


def _traverse(data: dict, keys: list):
    """Traverses a nested dict following a key path."""
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def select_block_from_path(file_path: str, *keys: str, fallback: str = "") -> str:
    """
    Like select_block but loads from an explicit absolute file path.

    Used by content-pack routing so block files outside BLOCKS_DIR can be
    reached without moving or copying them.  Cached by path, same as
    select_block.
    """
    cache_key = f"__path__:{file_path}"
    if cache_key not in _block_cache:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                _block_cache[cache_key] = json.load(f)
        except FileNotFoundError:
            return fallback or f"[MISSING BLOCK FILE: {file_path}]"
    blocks = _block_cache[cache_key]

    result = _traverse(blocks, list(keys))
    if isinstance(result, str):
        return result

    keys_list = list(keys)
    while keys_list:
        result = _traverse(blocks, keys_list[:-1] + ["fallback"])
        if isinstance(result, str):
            return result
        keys_list.pop()

    if "fallback" in blocks and isinstance(blocks["fallback"], str):
        return blocks["fallback"]

    return fallback or f"[BLOCK NOT FOUND: {file_path}/{'/'.join(keys)}]"


def select_block_traced(report_type: str, block_file: str, *keys: str,
                        fallback: str = "") -> tuple:
    """
    Like select_block but returns (text, resolved_key_path, fallback_used).

    resolved_key_path is the key list that actually matched.
    fallback_used is True whenever the exact key path was not found.
    Used by the Soul Ecosystem selection trace (SE_TRACE=1).
    """
    try:
        blocks = _load_blocks(report_type, block_file)
    except FileNotFoundError:
        text = fallback or f"[MISSING BLOCK FILE: {report_type}/{block_file}]"
        return (text, [], True)

    result = _traverse(blocks, list(keys))
    if isinstance(result, str):
        return (result, list(keys), False)

    keys_list = list(keys)
    while keys_list:
        candidate = keys_list[:-1] + ["fallback"]
        result = _traverse(blocks, candidate)
        if isinstance(result, str):
            return (result, candidate, True)
        keys_list.pop()

    if "fallback" in blocks and isinstance(blocks["fallback"], str):
        return (blocks["fallback"], ["fallback"], True)

    text = fallback or f"[BLOCK NOT FOUND: {report_type}/{block_file}/{'/'.join(keys)}]"
    return (text, [], True)


def select_tier_block(report_type: str, block_file: str,
                      archetype: str, tier: str) -> str:
    """
    Convenience function for proprietary index blocks.
    Tries: archetype + tier, then archetype + 'fallback', then 'subtle'.

    Usage:
        select_tier_block("soul_ecosystem", "foresight_pattern",
                          "Vindicated Oracle", "DOMINANT")
    """
    # Normalize tier to lowercase for JSON keys
    tier_key = tier.lower()
    archetype_key = archetype.lower().replace(" ", "_").replace("/", "_")

    result = select_block(report_type, block_file, archetype_key, tier_key)
    if not result.startswith("[BLOCK NOT FOUND"):
        return result

    # Try the tier without archetype specificity
    result = select_block(report_type, block_file, tier_key)
    if not result.startswith("[BLOCK NOT FOUND"):
        return result

    # Last resort: subtle tier placeholder
    return select_block(report_type, block_file, "subtle",
                        fallback="[TODO: Write this block]")
