"""
engine/solar_arc.py - Phase 5 Solar Arc direction scanner.

Convention: Naibod-adjusted secondary progression of the Sun.
arc(t) = progressed_Sun.longitude(t) - natal_Sun.longitude, where the
progressed Sun uses one ephemeris day per year of life.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

try:
    import swisseph as swe
except ImportError:  # pragma: no cover - no-ephemeris environments mock scanner helpers
    swe = None

from engine.asteroid_policy import load_asteroid_policy
from engine.forecast_event_adapter import normalize_to_forecast_event
from formulas.standard.normalization import normalize_angle_name


FORMULA_VERSION = "solar_arc_phase5.0.0"
POLICY_VERSION = "phase0.1.1"
TROPICAL_YEAR_DAYS = 365.2425
SOLAR_ARC_ORB = 1.0
EXACT_ORB = 0.05
SCAN_STEP_DAYS = 7
CHAPTER_WINDOW_DAYS = 90

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
    "Jupiter": swe.JUPITER if swe is not None else 5,
    "Saturn": swe.SATURN if swe is not None else 6,
    "Uranus": swe.URANUS if swe is not None else 7,
    "Neptune": swe.NEPTUNE if swe is not None else 8,
    "Pluto": swe.PLUTO if swe is not None else 9,
    "Chiron": swe.CHIRON if swe is not None else 15,
}

ASPECTS = {
    "Conjunction": 0.0,
    "Sextile": 60.0,
    "Square": 90.0,
    "Trine": 120.0,
    "Opposition": 180.0,
}

PLANET_SOURCES = (
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
)
ANGLE_SOURCES = ("Ascendant", "Midheaven", "Vertex")
ANCHOR_ASTEROIDS = frozenset({"Kassandra", "Aletheia", "Destinn", "Karma", "Kaali", "Medea", "Hermes", "Chaos"})
ANGLE_NAMES = frozenset({"ASC", "Ascendant", "MC", "Midheaven", "IC", "Imum Coeli", "DSC", "Descendant", "Vertex"})


def solar_arc_at(natal_payload: dict, moment: datetime) -> float:
    """Return the Naibod secondary-Sun arc for a report moment."""
    natal_sun = _natal_longitude(natal_payload, "Sun")
    natal_jd = _natal_jd(natal_payload)
    birth_dt = _birth_datetime(natal_payload)
    if natal_sun is None or natal_jd is None or birth_dt is None:
        raise ValueError("Solar Arc requires natal Sun longitude, natal Julian day, and birth date")
    age_years = max(0.0, (_ensure_utc(moment) - birth_dt).total_seconds() / 86400.0 / TROPICAL_YEAR_DAYS)
    progressed_sun = _body_longitude_at_jd("Sun", natal_jd + age_years)
    return (progressed_sun - natal_sun) % 360.0


def directed_longitude(natal_payload: dict, body_name: str, moment: datetime) -> float | None:
    natal = _natal_longitude(natal_payload, body_name)
    if natal is None:
        return None
    return (natal + solar_arc_at(natal_payload, moment)) % 360.0


def scan_solar_arc_events(natal_payload: dict, start_date: datetime, end_date: datetime) -> list[dict]:
    start = _ensure_utc(start_date)
    end = _ensure_utc(end_date)
    birth_time_state = _birth_time_status(natal_payload)
    sources = _directed_sources(natal_payload, birth_time_state)
    targets = _natal_targets(natal_payload)
    events: list[dict] = []

    for source_name, source in sources.items():
        for target_name, target in targets.items():
            # Skip a directed point against its own natal position -- see
            # engine/progressions.py's identical check for why this needs
            # normalized comparison rather than plain string equality
            # (ANGLE_SOURCES uses the long form, _natal_targets' angle
            # entries use the canonical short form).
            if normalize_angle_name(source_name) == normalize_angle_name(target_name):
                continue
            allowed_aspects = _allowed_aspects(source, target)
            if not allowed_aspects:
                continue
            for aspect_name in allowed_aspects:
                exact_at = _find_contact_exact(natal_payload, source_name, target["longitude"], ASPECTS[aspect_name], start, end)
                if exact_at is None:
                    continue
                source_lon = directed_longitude(natal_payload, source_name, exact_at)
                if source_lon is None:
                    continue
                orb = abs(_aspect_delta(source_lon, target["longitude"], ASPECTS[aspect_name]))
                if orb > SOLAR_ARC_ORB:
                    continue
                events.append(_solar_arc_event(source_name, target_name, source, target, aspect_name, orb, exact_at, birth_time_state, start))

    events.sort(key=lambda event: (event["peak_datetime"], event["transit_planet"], event["natal_target"]))
    return [normalize_to_forecast_event(e) for e in events]


def _find_contact_exact(
    natal_payload: dict,
    source_name: str,
    target_longitude: float,
    aspect_angle: float,
    start: datetime,
    end: datetime,
) -> datetime | None:
    cursor = start
    step = timedelta(days=SCAN_STEP_DAYS)
    best_time: datetime | None = None
    best_abs = 999.0
    previous_time = cursor
    previous_value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, previous_time)

    while cursor <= end:
        current_value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, cursor)
        if abs(current_value) < best_abs:
            best_abs = abs(current_value)
            best_time = cursor
        if _crossed_zero(previous_value, current_value):
            return _bisect_contact(natal_payload, source_name, target_longitude, aspect_angle, previous_time, cursor)
        previous_time = cursor
        previous_value = current_value
        cursor += step

    if best_time is not None and best_abs <= SOLAR_ARC_ORB:
        return best_time
    return None


def _bisect_contact(
    natal_payload: dict,
    source_name: str,
    target_longitude: float,
    aspect_angle: float,
    low: datetime,
    high: datetime,
) -> datetime:
    low_value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, low)
    for _ in range(48):
        midpoint = low + (high - low) / 2
        mid_value = _contact_delta(natal_payload, source_name, target_longitude, aspect_angle, midpoint)
        if abs(mid_value) <= EXACT_ORB:
            return midpoint
        if _crossed_zero(low_value, mid_value):
            high = midpoint
        else:
            low = midpoint
            low_value = mid_value
        if abs((high - low).total_seconds()) <= 3600:
            break
    return low + (high - low) / 2


def _format_event_date(moment: datetime) -> str:
    """Consistent user-facing date format for report contexts (mirrors engine/transit_engine.py)."""
    return _ensure_utc(moment).strftime("%B %d, %Y")


def _target_display(target_name: str) -> str:
    """Report-friendly natal target label (mirrors engine/transit_engine.py's _target_display)."""
    angle_labels = {
        "ASC": "your Ascendant", "Ascendant": "your Ascendant",
        "MC": "your Midheaven", "Midheaven": "your Midheaven",
        "DSC": "your Descendant", "Descendant": "your Descendant",
        "IC": "your Imum Coeli", "Imum Coeli": "your Imum Coeli",
        "Vertex": "your Vertex",
    }
    return angle_labels.get(target_name, f"your {target_name}")


def _solar_arc_event(
    source_name: str,
    target_name: str,
    source: dict,
    target: dict,
    aspect_name: str,
    orb: float,
    exact_at: datetime,
    birth_time_state: str,
    start: datetime,
) -> dict:
    angle_involved = source["kind"] == "angle" or target["kind"] == "angle"
    asteroid_involved = source["kind"] == "asteroid" or target["kind"] == "asteroid"
    confidence_state = "withheld" if angle_involved and birth_time_state != "exact" else "moderate"
    angle_support = 1.0 if not angle_involved or birth_time_state == "exact" else 0.4
    confidence = min(0.90, 0.95 * angle_support * 0.80)
    variant = "solar_arc_asteroid_aspect" if asteroid_involved else "solar_arc_angle_aspect" if angle_involved else "solar_arc_body_aspect"
    route = "solar_arc_to_asteroid" if target["kind"] == "asteroid" else "solar_arc_to_angle" if target["kind"] == "angle" else "solar_arc_to_body"
    exact_at = _ensure_utc(exact_at)

    is_exact = abs((start - exact_at).total_seconds()) < 3600
    arc_phase = "exact" if is_exact else "building" if start < exact_at else "receding"
    entry_at = exact_at - timedelta(days=CHAPTER_WINDOW_DAYS)
    leave_at = exact_at + timedelta(days=CHAPTER_WINDOW_DAYS)

    return {
        "event_type": "solar_arc",
        "transit_planet": source_name,
        "natal_target": target_name,
        "natal_target_display": _target_display(target_name),
        "aspect": aspect_name,
        "method_variant": variant,
        "clock_role": "chapter",
        "activation_route": route,
        "independence_group": "solar_arc_family",
        "temporal_precision": "season",
        "arc_phase": arc_phase,
        "orb": round(orb, 4),
        "orb_limit": SOLAR_ARC_ORB,
        "exactness": round(max(0.0, 1.0 - orb / SOLAR_ARC_ORB), 5),
        "weight": 0.80,
        "target_relevance": target.get("relevance", 0.65),
        "trigger_strength": round(0.80 * target.get("relevance", 0.65) * max(0.0, 1.0 - orb / SOLAR_ARC_ORB), 5),
        "signal_strength": round(0.80 * target.get("relevance", 0.65) * max(0.0, 1.0 - orb / SOLAR_ARC_ORB), 5),
        "raw_score": round(0.80 * target.get("relevance", 0.65) * max(0.0, 1.0 - orb / SOLAR_ARC_ORB), 5),
        "entry_datetime": entry_at,
        "peak_datetime": exact_at,
        "leave_datetime": leave_at,
        "entry_date": _format_event_date(entry_at),
        "peak_date": _format_event_date(exact_at),
        "leave_date": _format_event_date(leave_at),
        "exact_datetimes": [exact_at],
        "confidence": confidence,
        "confidence_components": {
            "calculation_integrity": 0.95,
            "angle_support": angle_support,
            "method_maturity": 0.80,
        },
        "confidence_state": confidence_state,
        "birth_time_dependency": "hard" if angle_involved else "soft",
        "report_surface_visibility": ["internal_rd", "engineering_diagnostic"],
        "formula_version": FORMULA_VERSION,
        "policy_version": POLICY_VERSION,
    }


def _directed_sources(natal_payload: dict, birth_time_state: str) -> dict[str, dict]:
    sources: dict[str, dict] = {}
    for name in PLANET_SOURCES:
        longitude = _natal_longitude(natal_payload, name)
        if longitude is not None:
            sources[name] = {"longitude": longitude, "kind": _body_kind(name)}
    if birth_time_state == "exact":
        for name in ANGLE_SOURCES:
            longitude = _angle_longitude(natal_payload, name)
            if longitude is not None:
                sources[name] = {"longitude": longitude, "kind": "angle"}
    policy = load_asteroid_policy()
    custom = natal_payload.get("custom_asteroids") if isinstance(natal_payload.get("custom_asteroids"), dict) else {}
    for name in ANCHOR_ASTEROIDS:
        data = custom.get(name)
        if not isinstance(data, dict):
            continue
        longitude = data.get("longitude")
        if isinstance(longitude, (int, float)) and policy.source_eligible(name, "solar_arc"):
            sources[name] = {"longitude": float(longitude), "kind": "asteroid"}
    return sources


def _natal_targets(natal_payload: dict) -> dict[str, dict]:
    targets: dict[str, dict] = {}
    standard = natal_payload.get("standard_planets") if isinstance(natal_payload.get("standard_planets"), dict) else {}
    for name, data in standard.items():
        if isinstance(data, dict) and isinstance(data.get("longitude"), (int, float)):
            targets[name] = {"longitude": float(data["longitude"]), "kind": _body_kind(name), "relevance": 0.70}
    # Canonical short-form angle names only — see engine/progressions.py's
    # _natal_targets for why the long form ("Ascendant"/"Midheaven") is
    # not used here even though it would also dedupe: the content
    # libraries and THEME_MAP key on "ASC"/"MC", not the long form.
    # IC is intentionally omitted — its alias currently can't resolve
    # (space vs. underscore mismatch against the natal payload), so
    # leaving it out preserves existing behavior rather than silently
    # changing event inclusion.
    for name in ("ASC", "MC", "DSC", "Vertex"):
        longitude = _angle_longitude(natal_payload, name)
        if longitude is not None:
            targets[name] = {"longitude": longitude, "kind": "angle", "relevance": 0.85}
    policy = load_asteroid_policy()
    custom = natal_payload.get("custom_asteroids") if isinstance(natal_payload.get("custom_asteroids"), dict) else {}
    for name, data in custom.items():
        if not isinstance(data, dict) or not policy.target_eligible(name, "solar_arc"):
            continue
        longitude = data.get("longitude")
        if isinstance(longitude, (int, float)):
            targets[name] = {"longitude": float(longitude), "kind": "asteroid", "relevance": policy.target_weight(name)}
    return targets


def _allowed_aspects(source: dict, target: dict) -> list[str]:
    if source["kind"] == "asteroid" or target["kind"] == "asteroid":
        return ["Conjunction"]
    return list(ASPECTS.keys())


def _contact_delta(natal_payload: dict, source_name: str, target_longitude: float, aspect_angle: float, moment: datetime) -> float:
    source_longitude = directed_longitude(natal_payload, source_name, moment)
    if source_longitude is None:
        return 999.0
    return _aspect_delta(source_longitude, target_longitude, aspect_angle)


def _aspect_delta(source_longitude: float, target_longitude: float, aspect_angle: float) -> float:
    return _signed_angle_delta(source_longitude - target_longitude, aspect_angle)


def _body_longitude_at_jd(body_name: str, jd: float) -> float:
    if swe is None:
        raise RuntimeError("swisseph is unavailable; Solar Arc scanner cannot compute live positions")
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
    if name in {"North_Node", "South_Node"}:
        return "node"
    if name in ANGLE_NAMES:
        return "angle"
    return "planet"


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
