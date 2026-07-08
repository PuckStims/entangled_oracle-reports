"""
engine/progressions.py - Phase 5 secondary progression scanner.

Convention: one ephemeris day per year of life. This module emits internal
evidence records only; client prose remains unchanged.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

try:
    import swisseph as swe
except ImportError:  # pragma: no cover
    swe = None

from engine.asteroid_policy import load_asteroid_policy


FORMULA_VERSION = "progressions_phase5.0.0"
POLICY_VERSION = "phase0.1.1"
TROPICAL_YEAR_DAYS = 365.2425
SCAN_STEP_DAYS = 7
CONTACT_ORB = 1.0
ANGLE_ORB = 0.5
CHAPTER_WINDOW_DAYS = 60

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")
if swe is not None:
    swe.set_ephe_path(EPHE_PATH)
CALC_FLAGS = (swe.FLG_SWIEPH | swe.FLG_SPEED) if swe is not None else 0

BODY_IDS = {
    "Sun": swe.SUN if swe is not None else 0,
    "Moon": swe.MOON if swe is not None else 1,
    "Mercury": swe.MERCURY if swe is not None else 2,
    "Venus": swe.VENUS if swe is not None else 3,
    "Mars": swe.MARS if swe is not None else 4,
}

ASPECTS = {
    "Conjunction": 0.0,
    "Sextile": 60.0,
    "Square": 90.0,
    "Trine": 120.0,
    "Opposition": 180.0,
}

PHASE_ANGLES = {
    "progressed_new_moon": 0.0,
    "progressed_first_quarter": 90.0,
    "progressed_full_moon": 180.0,
    "progressed_last_quarter": 270.0,
}

PLANET_SOURCES = ("Sun", "Moon", "Mercury", "Venus", "Mars")
ANGLE_SOURCES = ("Ascendant", "Midheaven")
ANCHOR_ASTEROIDS = frozenset({"Kassandra", "Aletheia", "Destinn", "Karma", "Kaali", "Medea", "Hermes", "Chaos"})
ANGLE_NAMES = frozenset({"ASC", "Ascendant", "MC", "Midheaven", "IC", "Imum Coeli", "DSC", "Descendant", "Vertex"})
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def build_progressed_chart(natal_payload: dict, moment: datetime) -> dict:
    natal_jd = _natal_jd(natal_payload)
    birth_dt = _birth_datetime(natal_payload)
    if natal_jd is None or birth_dt is None:
        raise ValueError("Secondary progressions require natal Julian day and birth date")
    age_years = max(0.0, (_ensure_utc(moment) - birth_dt).total_seconds() / 86400.0 / TROPICAL_YEAR_DAYS)
    progressed_jd = natal_jd + age_years
    positions = {}
    for body in PLANET_SOURCES:
        positions[body] = {
            "longitude": _body_longitude_at_jd(body, progressed_jd),
            "sign": _sign_for_longitude(_body_longitude_at_jd(body, progressed_jd)),
        }
    birth_time_state = _birth_time_status(natal_payload)
    if birth_time_state == "exact":
        for angle in ANGLE_SOURCES:
            natal = _angle_longitude(natal_payload, angle)
            if natal is not None:
                positions[angle] = {
                    "longitude": (natal + age_years) % 360.0,
                    "sign": _sign_for_longitude((natal + age_years) % 360.0),
                }
    return {
        "progressed_jd": progressed_jd,
        "age_years": age_years,
        "positions": positions,
        "lunation_phase_angle": _phase_angle(positions["Moon"]["longitude"], positions["Sun"]["longitude"]),
    }


def scan_progression_events(natal_payload: dict, start_date: datetime, end_date: datetime) -> list[dict]:
    start = _ensure_utc(start_date)
    end = _ensure_utc(end_date)
    birth_time_state = _birth_time_status(natal_payload)
    sources = _progressed_sources(natal_payload, birth_time_state)
    targets = _natal_targets(natal_payload)
    events: list[dict] = []

    for source_name, source in sources.items():
        for target_name, target in targets.items():
            if source_name == target_name:
                continue
            aspects = ["Conjunction"] if source["kind"] == "asteroid" or target["kind"] == "asteroid" else list(ASPECTS.keys())
            for aspect_name in aspects:
                exact_at = _find_contact_exact(natal_payload, source_name, target["longitude"], ASPECTS[aspect_name], start, end)
                if exact_at is None:
                    continue
                source_lon = progressed_longitude(natal_payload, source_name, exact_at)
                if source_lon is None:
                    continue
                orb = abs(_aspect_delta(source_lon, target["longitude"], ASPECTS[aspect_name]))
                limit = ANGLE_ORB if source["kind"] == "angle" or target["kind"] == "angle" else CONTACT_ORB
                if orb <= limit:
                    events.append(_progression_contact_event(source_name, target_name, source, target, aspect_name, orb, limit, exact_at, birth_time_state))

    events.extend(_progressed_ingresses(natal_payload, start, end, sources, birth_time_state))
    events.extend(_progressed_lunation_phase_events(natal_payload, start, end))
    events.sort(key=lambda event: (event["peak_datetime"], event["event_type"], event["transit_planet"]))
    return events


def progressed_longitude(natal_payload: dict, body_name: str, moment: datetime) -> float | None:
    if body_name in ANGLE_NAMES:
        natal = _angle_longitude(natal_payload, body_name)
        if natal is None:
            return None
        birth_dt = _birth_datetime(natal_payload)
        if birth_dt is None:
            return None
        age_years = max(0.0, (_ensure_utc(moment) - birth_dt).total_seconds() / 86400.0 / TROPICAL_YEAR_DAYS)
        return (natal + age_years) % 360.0
    if body_name in ANCHOR_ASTEROIDS:
        natal = _natal_longitude(natal_payload, body_name)
        if natal is None:
            return None
        birth_dt = _birth_datetime(natal_payload)
        if birth_dt is None:
            return None
        age_years = max(0.0, (_ensure_utc(moment) - birth_dt).total_seconds() / 86400.0 / TROPICAL_YEAR_DAYS)
        return (natal + age_years * 0.1) % 360.0
    natal_jd = _natal_jd(natal_payload)
    birth_dt = _birth_datetime(natal_payload)
    if natal_jd is None or birth_dt is None:
        return None
    age_years = max(0.0, (_ensure_utc(moment) - birth_dt).total_seconds() / 86400.0 / TROPICAL_YEAR_DAYS)
    return _body_longitude_at_jd(body_name, natal_jd + age_years)


def _find_contact_exact(natal_payload: dict, source_name: str, target_longitude: float, aspect_angle: float, start: datetime, end: datetime) -> datetime | None:
    cursor = start
    step = timedelta(days=SCAN_STEP_DAYS)
    previous_time = cursor
    previous_value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, previous_time)
    best_time: datetime | None = None
    best_abs = 999.0
    while cursor <= end:
        value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, cursor)
        if abs(value) < best_abs:
            best_abs = abs(value)
            best_time = cursor
        if _crossed_zero(previous_value, value):
            return _bisect_contact(natal_payload, source_name, target_longitude, aspect_angle, previous_time, cursor)
        previous_time = cursor
        previous_value = value
        cursor += step
    if best_time is not None and best_abs <= CONTACT_ORB:
        return best_time
    return None


def _bisect_contact(natal_payload: dict, source_name: str, target_longitude: float, aspect_angle: float, low: datetime, high: datetime) -> datetime:
    low_value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, low)
    for _ in range(48):
        midpoint = low + (high - low) / 2
        mid_value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, midpoint)
        if abs(mid_value) <= 0.05:
            return midpoint
        if _crossed_zero(low_value, mid_value):
            high = midpoint
        else:
            low = midpoint
            low_value = mid_value
        if abs((high - low).total_seconds()) <= 3600:
            break
    return low + (high - low) / 2


def _progression_contact_event(source_name: str, target_name: str, source: dict, target: dict, aspect_name: str, orb: float, limit: float, exact_at: datetime, birth_time_state: str) -> dict:
    angle_involved = source["kind"] == "angle" or target["kind"] == "angle"
    asteroid_involved = source["kind"] == "asteroid" or target["kind"] == "asteroid"
    confidence_state = "withheld" if angle_involved and birth_time_state != "exact" else "moderate"
    angle_support = 1.0 if not angle_involved or birth_time_state == "exact" else 0.4
    source_is_moon = source_name == "Moon"
    variant = "progression_body_aspect"
    route = "progression_to_asteroid" if target["kind"] == "asteroid" else "progression_to_angle" if target["kind"] == "angle" else "progression_to_body"
    strength = round(0.78 * target.get("relevance", 0.65) * max(0.0, 1.0 - orb / max(limit, 0.01)), 5)
    exact_at = _ensure_utc(exact_at)
    return {
        "event_type": "progression",
        "transit_planet": source_name,
        "natal_target": target_name,
        "aspect": aspect_name,
        "method_variant": variant,
        "clock_role": "modifier" if source_is_moon else "chapter",
        "activation_route": route,
        "independence_group": "progression_family",
        "temporal_precision": "season" if not source_is_moon else "week",
        "orb": round(orb, 4),
        "orb_limit": limit,
        "exactness": round(max(0.0, 1.0 - orb / max(limit, 0.01)), 5),
        "weight": 0.78,
        "target_relevance": target.get("relevance", 0.65),
        "trigger_strength": strength,
        "signal_strength": strength,
        "entry_datetime": exact_at - timedelta(days=CHAPTER_WINDOW_DAYS if not source_is_moon else 14),
        "peak_datetime": exact_at,
        "leave_datetime": exact_at + timedelta(days=CHAPTER_WINDOW_DAYS if not source_is_moon else 14),
        "exact_datetimes": [exact_at],
        "confidence": min(0.90, 0.95 * angle_support * 0.80),
        "confidence_components": {"calculation_integrity": 0.95, "angle_support": angle_support, "method_maturity": 0.80},
        "confidence_state": confidence_state,
        "birth_time_dependency": "hard" if angle_involved else "soft",
        "asteroid_involved": asteroid_involved,
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "formula_version": FORMULA_VERSION,
        "policy_version": POLICY_VERSION,
    }


def _progressed_ingresses(natal_payload: dict, start: datetime, end: datetime, sources: dict[str, dict], birth_time_state: str) -> list[dict]:
    events: list[dict] = []
    for source_name, source in sources.items():
        if source["kind"] == "asteroid":
            continue
        cursor = start
        previous_sign = _sign_index(progressed_longitude(natal_payload, source_name, cursor))
        while cursor <= end:
            current_sign = _sign_index(progressed_longitude(natal_payload, source_name, cursor))
            if current_sign is not None and previous_sign is not None and current_sign != previous_sign:
                exact_at = _bisect_ingress(natal_payload, source_name, cursor - timedelta(days=SCAN_STEP_DAYS), cursor, current_sign)
                events.append(_progression_ingress_event(source_name, current_sign, exact_at, source, birth_time_state))
                previous_sign = current_sign
            cursor += timedelta(days=SCAN_STEP_DAYS)
    return events


def _bisect_ingress(natal_payload: dict, source_name: str, low: datetime, high: datetime, new_sign: int) -> datetime:
    for _ in range(48):
        midpoint = low + (high - low) / 2
        mid_sign = _sign_index(progressed_longitude(natal_payload, source_name, midpoint))
        if mid_sign == new_sign:
            high = midpoint
        else:
            low = midpoint
        if abs((high - low).total_seconds()) <= 3600:
            break
    return high


def _progression_ingress_event(source_name: str, sign_index: int, exact_at: datetime, source: dict, birth_time_state: str) -> dict:
    angle_involved = source["kind"] == "angle"
    angle_support = 1.0 if not angle_involved or birth_time_state == "exact" else 0.4
    exact_at = _ensure_utc(exact_at)
    return {
        "event_type": "progression",
        "transit_planet": source_name,
        "natal_target": "",
        "aspect": "",
        "method_variant": "progression_ingress",
        "clock_role": "trigger",
        "activation_route": "progression_to_body",
        "independence_group": "progression_family",
        "temporal_precision": "week",
        "orb": 0.0,
        "orb_limit": 0.0,
        "phase": SIGNS[sign_index],
        "weight": 0.65,
        "trigger_strength": 0.45,
        "signal_strength": 0.45,
        "entry_datetime": exact_at,
        "peak_datetime": exact_at,
        "leave_datetime": exact_at,
        "exact_datetimes": [exact_at],
        "confidence": min(0.90, 0.95 * angle_support * 0.80),
        "confidence_components": {"calculation_integrity": 0.95, "angle_support": angle_support, "method_maturity": 0.80},
        "confidence_state": "withheld" if angle_involved and birth_time_state != "exact" else "moderate",
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "formula_version": FORMULA_VERSION,
        "policy_version": POLICY_VERSION,
    }


def _progressed_lunation_phase_events(natal_payload: dict, start: datetime, end: datetime) -> list[dict]:
    events: list[dict] = []
    for variant, phase_angle in PHASE_ANGLES.items():
        exact_at = _find_phase_crossing(natal_payload, phase_angle, start, end)
        if exact_at is not None:
            events.append(_progressed_lunation_event(variant, phase_angle, exact_at))
    return events


def _find_phase_crossing(natal_payload: dict, phase_angle: float, start: datetime, end: datetime) -> datetime | None:
    cursor = start
    previous_time = cursor
    previous_value = _phase_delta(natal_payload, phase_angle, cursor)
    while cursor <= end:
        value = _phase_delta(natal_payload, phase_angle, cursor)
        if _crossed_zero(previous_value, value):
            return _bisect_phase(natal_payload, phase_angle, previous_time, cursor)
        previous_time = cursor
        previous_value = value
        cursor += timedelta(days=SCAN_STEP_DAYS)
    return None


def _bisect_phase(natal_payload: dict, phase_angle: float, low: datetime, high: datetime) -> datetime:
    low_value = _phase_delta(natal_payload, phase_angle, low)
    for _ in range(48):
        midpoint = low + (high - low) / 2
        mid_value = _phase_delta(natal_payload, phase_angle, midpoint)
        if abs(mid_value) <= 0.1:
            return midpoint
        if _crossed_zero(low_value, mid_value):
            high = midpoint
        else:
            low = midpoint
            low_value = mid_value
    return low + (high - low) / 2


def _progressed_lunation_event(variant: str, phase_angle: float, exact_at: datetime) -> dict:
    exact_at = _ensure_utc(exact_at)
    return {
        "event_type": "progression",
        "transit_planet": "Moon",
        "natal_target": "Sun",
        "aspect": "Phase",
        "method_variant": "progression_lunation_phase",
        "clock_role": "trigger",
        "activation_route": "progression_to_body",
        "independence_group": "progression_family",
        "temporal_precision": "week",
        "orb": 0.0,
        "orb_limit": 0.0,
        "phase": variant,
        "weight": 0.72,
        "trigger_strength": 0.5,
        "signal_strength": 0.5,
        "entry_datetime": exact_at,
        "peak_datetime": exact_at,
        "leave_datetime": exact_at + timedelta(days=365 * 3),
        "exact_datetimes": [exact_at],
        "confidence": 0.76,
        "confidence_components": {"calculation_integrity": 0.95, "angle_support": 1.0, "method_maturity": 0.80},
        "confidence_state": "moderate",
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "formula_version": FORMULA_VERSION,
        "policy_version": POLICY_VERSION,
        "phase_angle": phase_angle,
    }


def _phase_delta(natal_payload: dict, phase_angle: float, moment: datetime) -> float:
    moon = progressed_longitude(natal_payload, "Moon", moment)
    sun = progressed_longitude(natal_payload, "Sun", moment)
    if moon is None or sun is None:
        return 999.0
    return _signed_angle_delta(_phase_angle(moon, sun), phase_angle)


def _phase_angle(moon_longitude: float, sun_longitude: float) -> float:
    return (moon_longitude - sun_longitude) % 360.0


def _progressed_sources(natal_payload: dict, birth_time_state: str) -> dict[str, dict]:
    sources: dict[str, dict] = {name: {"kind": "planet"} for name in PLANET_SOURCES if _natal_longitude(natal_payload, name) is not None}
    if birth_time_state == "exact":
        for angle in ANGLE_SOURCES:
            if _angle_longitude(natal_payload, angle) is not None:
                sources[angle] = {"kind": "angle"}
    policy = load_asteroid_policy()
    custom = natal_payload.get("custom_asteroids") if isinstance(natal_payload.get("custom_asteroids"), dict) else {}
    for name in ANCHOR_ASTEROIDS:
        data = custom.get(name)
        if not isinstance(data, dict):
            continue
        if isinstance(data.get("longitude"), (int, float)) and policy.source_eligible(name, "progression"):
            sources[name] = {"kind": "asteroid"}
    return sources


def _natal_targets(natal_payload: dict) -> dict[str, dict]:
    targets: dict[str, dict] = {}
    standard = natal_payload.get("standard_planets") if isinstance(natal_payload.get("standard_planets"), dict) else {}
    for name, data in standard.items():
        if isinstance(data, dict) and isinstance(data.get("longitude"), (int, float)):
            targets[name] = {"longitude": float(data["longitude"]), "kind": _body_kind(name), "relevance": 0.70}
    for name in ("ASC", "Ascendant", "MC", "Midheaven", "IC", "Imum Coeli", "DSC", "Descendant", "Vertex"):
        longitude = _angle_longitude(natal_payload, name)
        if longitude is not None:
            targets[name] = {"longitude": longitude, "kind": "angle", "relevance": 0.85}
    policy = load_asteroid_policy()
    custom = natal_payload.get("custom_asteroids") if isinstance(natal_payload.get("custom_asteroids"), dict) else {}
    for name, data in custom.items():
        if not isinstance(data, dict) or not policy.target_eligible(name, "progression"):
            continue
        longitude = data.get("longitude")
        if isinstance(longitude, (int, float)):
            targets[name] = {"longitude": float(longitude), "kind": "asteroid", "relevance": policy.target_weight(name)}
    return targets


def _contact_delta(natal_payload: dict, source_name: str, target_longitude: float, aspect_angle: float, moment: datetime) -> float:
    source = progressed_longitude(natal_payload, source_name, moment)
    if source is None:
        return 999.0
    return _aspect_delta(source, target_longitude, aspect_angle)


def _aspect_delta(source_longitude: float, target_longitude: float, aspect_angle: float) -> float:
    return _signed_angle_delta(source_longitude - target_longitude, aspect_angle)


def _body_longitude_at_jd(body_name: str, jd: float) -> float:
    if swe is None:
        raise RuntimeError("swisseph is unavailable; progression scanner cannot compute live positions")
    coordinates, _flags = swe.calc_ut(jd, BODY_IDS[body_name], CALC_FLAGS)
    return float(coordinates[0] % 360.0)


def _natal_longitude(natal_payload: dict, body_name: str) -> float | None:
    if body_name in ANGLE_NAMES:
        return _angle_longitude(natal_payload, body_name)
    standard = natal_payload.get("standard_planets") if isinstance(natal_payload.get("standard_planets"), dict) else {}
    custom = natal_payload.get("custom_asteroids") if isinstance(natal_payload.get("custom_asteroids"), dict) else {}
    data = standard.get(body_name) if body_name in standard else custom.get(body_name)
    if not isinstance(data, dict):
        return None
    value = data.get("longitude")
    return float(value % 360.0) if isinstance(value, (int, float)) else None


def _angle_longitude(natal_payload: dict, name: str) -> float | None:
    aliases = {"ASC": "Ascendant", "MC": "Midheaven", "IC": "Imum Coeli", "DSC": "Descendant"}
    key = aliases.get(name, name)
    angles = natal_payload.get("angles") if isinstance(natal_payload.get("angles"), dict) else {}
    data = angles.get(key)
    if not isinstance(data, dict):
        return None
    value = data.get("longitude")
    return float(value % 360.0) if isinstance(value, (int, float)) else None


def _body_kind(name: str) -> str:
    if name in {"Sun", "Moon"}:
        return "luminary"
    if name in ANGLE_NAMES:
        return "angle"
    return "planet"


def _sign_index(longitude: float | None) -> int | None:
    if longitude is None:
        return None
    return int((longitude % 360.0) // 30)


def _sign_for_longitude(longitude: float) -> str:
    return SIGNS[_sign_index(longitude) or 0]


def _natal_jd(natal_payload: dict) -> float | None:
    user_profile = natal_payload.get("user_profile") if isinstance(natal_payload.get("user_profile"), dict) else {}
    value = natal_payload.get("julian_day") or user_profile.get("julian_day")
    return float(value) if isinstance(value, (int, float)) else None


def _birth_datetime(natal_payload: dict) -> datetime | None:
    user_profile = natal_payload.get("user_profile") if isinstance(natal_payload.get("user_profile"), dict) else {}
    raw_date = natal_payload.get("birth_date") or natal_payload.get("date") or user_profile.get("local_datetime")
    if not raw_date:
        return None
    try:
        parsed = date.fromisoformat(str(raw_date)[:10])
    except ValueError:
        return None
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)


def _birth_time_status(natal_payload: dict) -> str:
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


def _signed_angle_delta(longitude: float, target: float) -> float:
    return ((float(longitude) - float(target) + 180.0) % 360.0) - 180.0


def _crossed_zero(left: float, right: float) -> bool:
    if left == 0 or right == 0:
        return True
    return (left < 0 < right) or (right < 0 < left)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
