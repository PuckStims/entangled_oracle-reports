"""
engine/profections.py - Phase 4 annual profection periods.

Annual profection is represented as TimeLordPeriod evidence. It modifies
topic relevance; it does not produce client prose in Phase 4.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timezone
from typing import Any


FORMULA_VERSION = "profections_phase4.0.0"
POLICY_VERSION = "phase0.1.1"
TIME_LORD_PERIOD_SCHEMA_VERSION = "phase0.1.1"

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

TRADITIONAL_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

HOUSE_TOPICS = {
    1: ["identity", "body", "direction"],
    2: ["resources", "money", "values"],
    3: ["communication", "siblings", "local_environment"],
    4: ["home", "family", "foundations"],
    5: ["creativity", "pleasure", "children"],
    6: ["work", "health", "service"],
    7: ["partnership", "contracts", "other_people"],
    8: ["shared_resources", "grief", "obligation"],
    9: ["meaning", "travel", "education"],
    10: ["vocation", "visibility", "authority"],
    11: ["community", "allies", "future"],
    12: ["rest", "hidden_matters", "release"],
}


def annual_profection_periods(natal_payload: dict, start_date: datetime, end_date: datetime) -> list[dict]:
    """Returns annual profection TimeLordPeriod records intersecting the report window."""
    birth_date = _birth_date(natal_payload)
    asc_sign = _ascendant_sign(natal_payload)
    if birth_date is None or asc_sign not in SIGNS:
        return []

    start = _ensure_utc(start_date)
    end = _ensure_utc(end_date)
    start_year = start.year - 1
    end_year = end.year + 1
    periods: list[dict] = []

    for year in range(start_year, end_year + 1):
        period_start_date = _birthday_in_year(birth_date, year)
        next_start_date = _birthday_in_year(birth_date, year + 1)
        period_start = datetime.combine(period_start_date, time.min, tzinfo=timezone.utc)
        period_end = datetime.combine(next_start_date, time.min, tzinfo=timezone.utc)
        if period_end <= start or period_start >= end:
            continue
        age = _age_on_birthday(birth_date, year)
        periods.append(_annual_period(natal_payload, birth_date, asc_sign, age, period_start, period_end))

    periods.sort(key=lambda period: period["start_at"])
    return periods


def annual_profection_for_age(natal_payload: dict, age: int) -> dict | None:
    """Convenience API for tests and downstream topic checks."""
    asc_sign = _ascendant_sign(natal_payload)
    if asc_sign not in SIGNS:
        return None
    profected_house = (int(age) % 12) + 1
    profected_sign = _profected_sign(asc_sign, profected_house)
    time_lord = TRADITIONAL_RULERS[profected_sign]
    return {
        "age": int(age),
        "profected_house": profected_house,
        "profected_sign": profected_sign,
        "time_lord": time_lord,
        "activated_house_topics": HOUSE_TOPICS[profected_house],
    }


def _annual_period(
    natal_payload: dict,
    birth_date: date,
    asc_sign: str,
    age: int,
    start_at: datetime,
    end_at: datetime,
) -> dict:
    profection = annual_profection_for_age(natal_payload, age)
    assert profection is not None
    time_lord = profection["time_lord"]
    lord_state = _lord_natal_state(natal_payload, time_lord)
    confidence_state = _birth_time_confidence(natal_payload)
    confidence = 0.8415 if confidence_state != "unknown" else 0.65
    confidence_components = {
        "calculation_integrity": 0.99,
        "method_maturity": 0.85,
        "birth_time_state": 1.0 if confidence_state != "unknown" else 0.75,
    }

    record = {
        "schema_version": TIME_LORD_PERIOD_SCHEMA_VERSION,
        "period_id": "",
        "system": "annual_profection",
        "level": "year",
        "parent_period_id": None,
        "start_at": _iso_datetime(start_at),
        "end_at": _iso_datetime(end_at),
        "period_lord": time_lord,
        "period_sign": profection["profected_sign"],
        "period_house": profection["profected_house"],
        "lord_natal_state": lord_state,
        "is_peak": False,
        "is_loosing_of_the_bond": False,
        "activated_house_topics": list(profection["activated_house_topics"]),
        "natal_anchor_ids": [],
        "weight_modifier": 1.12,
        "confidence": round(confidence, 4),
        "confidence_components": confidence_components,
        "birth_time_dependency": "none",
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "formula_version": FORMULA_VERSION,
        "policy_version": POLICY_VERSION,
        "provenance": {
            "scanner": "engine.profections.annual_profection_periods",
            "scanner_version": FORMULA_VERSION,
            "birth_date": birth_date.isoformat(),
            "age": age,
            "ascendant_sign": asc_sign,
        },
    }
    record["period_id"] = _period_id(record)
    return record


def _lord_natal_state(natal_payload: dict, time_lord: str) -> dict:
    standard = natal_payload.get("standard_planets") if isinstance(natal_payload.get("standard_planets"), dict) else {}
    data = standard.get(time_lord) if isinstance(standard.get(time_lord), dict) else {}
    return {
        "condition": "available" if data else "unavailable",
        "house": int(data.get("house") or 0) if data else 0,
        "sign": str(data.get("sign") or "") if data else "",
        "retrograde": bool(data.get("retrograde", False)) if data else False,
        "aspects": [],
    }


def _profected_sign(asc_sign: str, profected_house: int) -> str:
    asc_index = SIGNS.index(asc_sign)
    return SIGNS[(asc_index + profected_house - 1) % 12]


def _birth_date(natal_payload: dict) -> date | None:
    user_profile = natal_payload.get("user_profile") if isinstance(natal_payload.get("user_profile"), dict) else {}
    raw = (
        natal_payload.get("birth_date")
        or natal_payload.get("date")
        or user_profile.get("local_datetime")
    )
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _ascendant_sign(natal_payload: dict) -> str:
    angles = natal_payload.get("angles") if isinstance(natal_payload.get("angles"), dict) else {}
    asc = angles.get("Ascendant") if isinstance(angles.get("Ascendant"), dict) else {}
    return str(asc.get("sign") or "")


def _birthday_in_year(birth_date: date, year: int) -> date:
    try:
        return birth_date.replace(year=year)
    except ValueError:
        # Feb 29 birthdays use Feb 28 in non-leap years for annual handoff.
        return date(year, 2, 28)


def _age_on_birthday(birth_date: date, year: int) -> int:
    return max(0, year - birth_date.year)


def _birth_time_confidence(natal_payload: dict) -> str:
    user_profile = natal_payload.get("user_profile") if isinstance(natal_payload.get("user_profile"), dict) else {}
    raw = str(
        user_profile.get("birth_time_state")
        or user_profile.get("birth_time_confidence")
        or natal_payload.get("birth_time_state")
        or ""
    ).lower()
    if "unknown" in raw:
        return "unknown"
    if "approx" in raw:
        return "approximate"
    return "exact"


def _period_id(record: dict[str, Any]) -> str:
    basis = {
        "system": record.get("system"),
        "level": record.get("level"),
        "start_at": record.get("start_at"),
        "period_lord": record.get("period_lord"),
        "period_house": record.get("period_house"),
    }
    digest = hashlib.sha256(json.dumps(basis, sort_keys=True).encode("utf-8")).hexdigest()[:8]
    return f"tlp_aprf_{digest}"


def _iso_datetime(value: datetime) -> str:
    value = _ensure_utc(value)
    return value.isoformat().replace("+00:00", "Z")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
