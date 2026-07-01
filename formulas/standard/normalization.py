"""
Shared normalization helpers for standard astrology payloads.
"""

from __future__ import annotations

from typing import Any


CANONICAL_ANGLE_NAMES = (
    "Ascendant",
    "Midheaven",
    "Descendant",
    "Imum_Coeli",
    "Vertex",
)

ANGLE_ALIAS_MAP = {
    "ASC": "Ascendant",
    "Asc": "Ascendant",
    "asc": "Ascendant",
    "MC": "Midheaven",
    "Mc": "Midheaven",
    "mc": "Midheaven",
    "DSC": "Descendant",
    "Dsc": "Descendant",
    "dsc": "Descendant",
    "IC": "Imum_Coeli",
    "Ic": "Imum_Coeli",
    "ic": "Imum_Coeli",
    "Ascendant": "Ascendant",
    "Midheaven": "Midheaven",
    "Descendant": "Descendant",
    "Imum_Coeli": "Imum_Coeli",
    "Vertex": "Vertex",
}


def normalize_angle_name(angle_name: str | None) -> str:
    """Returns the canonical angle key for known aliases."""
    if not angle_name:
        return ""
    normalized = ANGLE_ALIAS_MAP.get(str(angle_name).strip())
    return normalized or str(angle_name).strip()


def is_canonical_angle_name(angle_name: str | None) -> bool:
    """Returns True when the provided angle name is already canonical."""
    return normalize_angle_name(angle_name) in CANONICAL_ANGLE_NAMES


def normalize_angle_payload(angles: dict[str, Any] | None) -> dict[str, Any]:
    """Rekeys an angle mapping to canonical names while preserving values."""
    normalized: dict[str, Any] = {}
    for key, value in (angles or {}).items():
        normalized[normalize_angle_name(key)] = value
    return normalized
