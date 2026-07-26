"""Feature extraction from EO-style natal payloads."""

from __future__ import annotations

from collections import Counter
from typing import Any

from eia_engine.schema import CONFIDENCE_MODIFIERS

ELEMENT_BY_SIGN = {
    "Aries": "fire",
    "Leo": "fire",
    "Sagittarius": "fire",
    "Taurus": "earth",
    "Virgo": "earth",
    "Capricorn": "earth",
    "Gemini": "air",
    "Libra": "air",
    "Aquarius": "air",
    "Cancer": "water",
    "Scorpio": "water",
    "Pisces": "water",
}

MODALITY_BY_SIGN = {
    "Aries": "cardinal",
    "Cancer": "cardinal",
    "Libra": "cardinal",
    "Capricorn": "cardinal",
    "Taurus": "fixed",
    "Leo": "fixed",
    "Scorpio": "fixed",
    "Aquarius": "fixed",
    "Gemini": "mutable",
    "Virgo": "mutable",
    "Sagittarius": "mutable",
    "Pisces": "mutable",
}


def extract_astrology_features(natal_chart: dict[str, Any]) -> dict[str, Any]:
    planets = _normalise_points(natal_chart.get("standard_planets", {}))
    angles = _normalise_points(natal_chart.get("angles", {}))
    all_points = {**planets, **angles}

    element_counts: Counter[str] = Counter()
    modality_counts: Counter[str] = Counter()
    house_counts: Counter[int] = Counter()
    for point in all_points.values():
        sign = point.get("sign")
        house = _coerce_house(point.get("house"))
        if sign in ELEMENT_BY_SIGN:
            element_counts[ELEMENT_BY_SIGN[sign]] += 1
        if sign in MODALITY_BY_SIGN:
            modality_counts[MODALITY_BY_SIGN[sign]] += 1
        if house:
            house_counts[house] += 1

    confidence = (
        natal_chart.get("birth_time_confidence")
        or natal_chart.get("client", {}).get("birth_time_confidence")
        or natal_chart.get("user_profile", {}).get("birth_time_confidence")
        or ("unknown" if natal_chart.get("user_profile", {}).get("simple_mode") else "exact")
    )
    confidence_key = str(confidence).lower()

    return {
        "body_signs": {body: point.get("sign") for body, point in all_points.items()},
        "body_houses": {body: _coerce_house(point.get("house")) for body, point in all_points.items()},
        "element_balance": _normalise_counts(element_counts),
        "modality_balance": _normalise_counts(modality_counts),
        "emphasized_houses": {house for house, count in house_counts.items() if count >= 1},
        "aspects": _normalise_aspects(natal_chart.get("aspects", [])),
        "birth_time_confidence": confidence_key,
        "confidence_modifier": CONFIDENCE_MODIFIERS.get(confidence_key, 1.0),
    }


def _normalise_points(points: dict[str, Any]) -> dict[str, dict[str, Any]]:
    normalised = {}
    for name, value in points.items():
        point = value if isinstance(value, dict) else {}
        normalised[_body_name(name)] = dict(point)
    return normalised


def _normalise_counts(counts: Counter[str]) -> dict[str, float]:
    total = sum(counts.values()) or 1
    return {key: round(value / total, 4) for key, value in sorted(counts.items())}


def _normalise_aspects(aspects: list[Any]) -> set[tuple[str, str, str]]:
    normalised = set()
    for aspect in aspects:
        if not isinstance(aspect, dict):
            continue
        first = aspect.get("body1") or aspect.get("body_1") or aspect.get("planet1") or aspect.get("from")
        second = aspect.get("body2") or aspect.get("body_2") or aspect.get("planet2") or aspect.get("to")
        aspect_type = aspect.get("aspect") or aspect.get("type") or aspect.get("name")
        if first and second and aspect_type:
            pair = sorted([_body_name(str(first)), _body_name(str(second))])
            normalised.add((pair[0], pair[1], str(aspect_type).lower()))
    return normalised


def _body_name(name: str) -> str:
    cleaned = name.replace("_", " ").strip()
    aliases = {"asc": "Ascendant", "mc": "Midheaven"}
    return aliases.get(cleaned.lower(), cleaned.title())


def _coerce_house(value: Any) -> int | None:
    try:
        house = int(value)
    except (TypeError, ValueError):
        return None
    return house if 1 <= house <= 12 else None
