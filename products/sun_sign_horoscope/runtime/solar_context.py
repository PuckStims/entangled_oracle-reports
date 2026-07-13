"""Solar-house context helpers for synthesized horoscope products.

This module extracts the reusable part of the sun-sign card tooling so report
builders can add a traditional solar layer without depending on card rendering.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import swisseph as swe

from config import HOUSE_DOMAINS
from engine.transit_engine import _planet_state, _whole_sign_house
from selectors.block_selector import select_block

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_BODY_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

_FEATURE_PLANETS = [
    "Sun", "Mercury", "Venus", "Mars", "Jupiter",
    "Saturn", "Uranus", "Neptune", "Pluto",
]
_FAST_MOVERS = {"Sun", "Mercury", "Venus", "Mars"}
_FEATURE_ORB = 6.0
_ASPECT_ANGLES = [
    ("Conjunction", 0),
    ("Opposition", 180),
    ("Square", 90),
    ("Trine", 120),
    ("Sextile", 60),
]
_SIGNIFICANCE = {
    "Sun": 0.65,
    "Mercury": 0.45,
    "Venus": 0.50,
    "Mars": 0.55,
    "Jupiter": 0.75,
    "Saturn": 0.85,
    "Uranus": 0.90,
    "Neptune": 0.95,
    "Pluto": 1.00,
}


def _ensure_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _noon_utc(moment: datetime) -> datetime:
    moment = _ensure_utc(moment)
    return moment.replace(hour=12, minute=0, second=0, microsecond=0)


def _aspect_orb(separation: float) -> tuple[str, float] | None:
    best: tuple[str, float] | None = None
    for name, angle in _ASPECT_ANGLES:
        orb = abs(separation - angle)
        if orb <= _FEATURE_ORB and (best is None or orb < best[1]):
            best = (name, orb)
    return best


def _pick_feature(longitudes: dict[str, float]) -> dict[str, Any]:
    best: tuple[float, str, str, str] | None = None
    names = [planet for planet in _FEATURE_PLANETS if planet in longitudes]

    for index, first in enumerate(names):
        for second in names[index + 1:]:
            if first not in _FAST_MOVERS and second not in _FAST_MOVERS:
                continue
            separation = abs(longitudes[first] - longitudes[second]) % 360
            if separation > 180:
                separation = 360 - separation
            hit = _aspect_orb(separation)
            if not hit:
                continue
            aspect, orb = hit
            score = max(_SIGNIFICANCE[first], _SIGNIFICANCE[second]) * (1.0 - orb / _FEATURE_ORB)
            fast_candidates = [planet for planet in (first, second) if planet in _FAST_MOVERS]
            planet = max(fast_candidates, key=_SIGNIFICANCE.get)
            partner = second if planet == first else first
            if best is None or score > best[0]:
                best = (score, planet, partner, aspect)

    if best is None:
        return {
            "planet": "Sun",
            "longitude": longitudes["Sun"],
            "partner": "",
            "aspect": "",
            "score": 0.0,
        }

    score, planet, partner, aspect = best
    return {
        "planet": planet,
        "longitude": longitudes[planet],
        "partner": partner,
        "aspect": aspect,
        "score": round(score, 4),
    }


def _sun_sign_from_payload(payload: dict[str, Any]) -> str:
    standard_planets = payload.get("standard_planets") if isinstance(payload, dict) else {}
    sun = standard_planets.get("Sun") if isinstance(standard_planets, dict) else {}
    sign = sun.get("sign") if isinstance(sun, dict) else ""
    return sign if sign in ZODIAC_SIGNS else ""


def _relation_between_houses(solar_house: int, natal_house: int) -> str:
    if not (1 <= solar_house <= 12 and 1 <= natal_house <= 12):
        return "fallback"
    if solar_house == natal_house:
        return "same_house"
    solar_quadrant = (solar_house - 1) // 3
    natal_quadrant = (natal_house - 1) // 3
    if solar_quadrant == natal_quadrant:
        return "supportive"
    if abs(solar_house - natal_house) in {3, 6, 9}:
        return "tension"
    return "different_fields"


def build_solar_day_context(
    payload: dict[str, Any],
    report_start_date: datetime,
    *,
    natal_activation_house: int | None = None,
    bridge_report_type: str = "daily_horoscope",
) -> dict[str, Any]:
    """Builds one solar-house layer for the native Sun sign."""
    sun_sign = _sun_sign_from_payload(payload)
    if not sun_sign:
        return {
            "solar_layer_available": False,
            "solar_bridge_relation": "fallback",
            "solar_natal_bridge_block": "",
        }

    moment = _noon_utc(report_start_date)
    longitudes = {
        name: _planet_state(body_id, moment)["longitude"]
        for name, body_id in _BODY_IDS.items()
    }
    feature = _pick_feature(longitudes)
    solar_ascendant = ZODIAC_SIGNS.index(sun_sign) * 30.0
    solar_house = _whole_sign_house(feature["longitude"], solar_ascendant)
    solar_house_name = HOUSE_DOMAINS.get(solar_house, "chart")
    relation = _relation_between_houses(solar_house, int(natal_activation_house or 0))

    solar_activation_block = select_block(
        "daily_horoscope",
        "your_activation",
        feature["planet"],
        str(solar_house),
    )
    bridge_block = select_block(
        bridge_report_type,
        "solar_natal_bridge",
        relation,
        fallback="The broad Sun-sign layer and the personal chart layer are both active today. Let the solar theme name the general weather, then use the natal activation to choose where the day asks for a more specific response.",
    )

    return {
        "solar_layer_available": True,
        "solar_sign": sun_sign,
        "solar_feature_planet": feature["planet"],
        "solar_feature_partner": feature["partner"],
        "solar_feature_aspect": feature["aspect"],
        "solar_feature_score": feature["score"],
        "solar_activation_house": solar_house,
        "solar_activation_house_name": solar_house_name,
        "solar_activation_block": solar_activation_block,
        "solar_bridge_relation": relation,
        "solar_natal_bridge_block": bridge_block,
    }


def build_weekly_solar_context(
    payload: dict[str, Any],
    report_start_date: datetime,
    report_end_date: datetime,
    *,
    natal_houses: list[int] | None = None,
) -> dict[str, Any]:
    """Builds a compact weekly solar theme from daily solar-house layers."""
    start = _ensure_utc(report_start_date)
    end = _ensure_utc(report_end_date)
    natal_houses = natal_houses or []

    days: list[dict[str, Any]] = []
    cursor = start
    while cursor < end:
        natal_house = natal_houses[len(days)] if len(days) < len(natal_houses) else None
        ctx = build_solar_day_context(
            payload,
            cursor,
            natal_activation_house=natal_house,
            bridge_report_type="weekly_horoscope",
        )
        if ctx.get("solar_layer_available"):
            ctx["solar_date"] = cursor.strftime("%B %d, %Y")
            days.append(ctx)
        cursor += timedelta(days=1)

    if not days:
        return {
            "weekly_solar_layer_available": False,
            "weekly_solar_days": [],
            "weekly_solar_bridge_block": "",
        }

    def sort_key(item: dict[str, Any]) -> tuple[int, float]:
        house_count = sum(1 for day in days if day["solar_activation_house"] == item["solar_activation_house"])
        return (house_count, float(item.get("solar_feature_score") or 0.0))

    dominant = max(days, key=sort_key)
    return {
        "weekly_solar_layer_available": True,
        "weekly_solar_days": days,
        "weekly_solar_sign": dominant["solar_sign"],
        "weekly_solar_feature_planet": dominant["solar_feature_planet"],
        "weekly_solar_feature_partner": dominant["solar_feature_partner"],
        "weekly_solar_feature_aspect": dominant["solar_feature_aspect"],
        "weekly_solar_theme_house": dominant["solar_activation_house"],
        "weekly_solar_theme_house_name": dominant["solar_activation_house_name"],
        "weekly_solar_theme_block": dominant["solar_activation_block"],
        "weekly_solar_bridge_relation": dominant["solar_bridge_relation"],
        "weekly_solar_bridge_block": dominant["solar_natal_bridge_block"],
    }
