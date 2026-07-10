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
from engine.forecast_event_adapter import normalize_to_forecast_event


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
            progressed_angle_lon = _progressed_angle_longitude(natal_payload, angle, moment)
            if progressed_angle_lon is not None:
                positions[angle] = {
                    "longitude": progressed_angle_lon,
                    "sign": _sign_for_longitude(progressed_angle_lon),
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

    # Progressed to Progressed
    for source_name, source in sources.items():
        for target_name, target in sources.items():
            if source_name >= target_name: continue
            aspects = ["Conjunction"] if source["kind"] == "asteroid" or target["kind"] == "asteroid" else list(ASPECTS.keys())
            for aspect_name in aspects:
                exact_at = _find_prog_to_prog_contact_exact(natal_payload, source_name, target_name, ASPECTS[aspect_name], start, end)
                if exact_at is None: continue
                source_lon = progressed_longitude(natal_payload, source_name, exact_at)
                target_lon = progressed_longitude(natal_payload, target_name, exact_at)
                if source_lon is None or target_lon is None: continue
                orb = abs(_aspect_delta(source_lon, target_lon, ASPECTS[aspect_name]))
                limit = ANGLE_ORB if source["kind"] == "angle" or target["kind"] == "angle" else CONTACT_ORB
                if orb <= limit:
                    evt = _progression_contact_event(source_name, target_name, source, target, aspect_name, orb, limit, exact_at, birth_time_state)
                    evt["method_variant"] = "progressed_to_progressed"
                    s_lon_s = progressed_longitude(natal_payload, source_name, start)
                    t_lon_s = progressed_longitude(natal_payload, target_name, start)
                    if s_lon_s is not None and t_lon_s is not None:
                        s_speed = _progressed_speed(natal_payload, source_name, start)
                        t_speed = _progressed_speed(natal_payload, target_name, start)
                        evt["applying_state"] = _applying_state_relative_velocity(s_lon_s, s_speed, t_lon_s, t_speed, ASPECTS[aspect_name])
                    events.append(evt)

    # Transit to Progressed
    for transit_name in PLANET_SOURCES:
        t_source = {"kind": "planet"}
        for prog_name, prog_target in sources.items():
            aspects = ["Conjunction"] if prog_target["kind"] == "asteroid" else list(ASPECTS.keys())
            for aspect_name in aspects:
                exact_at = _find_transit_to_prog_contact_exact(natal_payload, transit_name, prog_name, ASPECTS[aspect_name], start, end)
                if exact_at is None: continue
                t_lon = _transit_longitude(transit_name, exact_at)
                p_lon = progressed_longitude(natal_payload, prog_name, exact_at)
                if t_lon is None or p_lon is None: continue
                orb = abs(_aspect_delta(t_lon, p_lon, ASPECTS[aspect_name]))
                limit = ANGLE_ORB if prog_target["kind"] == "angle" else CONTACT_ORB
                if orb <= limit:
                    evt = _progression_contact_event(transit_name, prog_name, t_source, prog_target, aspect_name, orb, limit, exact_at, birth_time_state)
                    evt["method_variant"] = "transit_to_progressed"
                    t_lon_s = _transit_longitude(transit_name, start)
                    p_lon_s = progressed_longitude(natal_payload, prog_name, start)
                    if t_lon_s is not None and p_lon_s is not None:
                        t_speed = _transit_speed(transit_name, start)
                        p_speed = _progressed_speed(natal_payload, prog_name, start)
                        evt["applying_state"] = _applying_state_relative_velocity(t_lon_s, t_speed, p_lon_s, p_speed, ASPECTS[aspect_name])
                    events.append(evt)

    events.sort(key=lambda event: (event["peak_datetime"], event["event_type"], event["transit_planet"]))
    return [normalize_to_forecast_event(e) for e in events]


def progressed_longitude(natal_payload: dict, body_name: str, moment: datetime) -> float | None:
    if body_name in ANGLE_NAMES:
        return _progressed_angle_longitude(natal_payload, body_name, moment)
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
    window_days = CHAPTER_WINDOW_DAYS if not source_is_moon else 14
    entry_at = exact_at - timedelta(days=window_days)
    leave_at = exact_at + timedelta(days=window_days)
    return {
        "event_type": "progression",
        "transit_planet": source_name,
        "natal_target": target_name,
        "natal_target_display": _target_display(target_name),
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
        "raw_score": strength,
        "entry_datetime": entry_at,
        "peak_datetime": exact_at,
        "leave_datetime": leave_at,
        "entry_date": _format_event_date(entry_at),
        "peak_date": _format_event_date(exact_at),
        "leave_date": _format_event_date(leave_at),
        "exact_datetimes": [exact_at],
        "confidence": min(0.90, 0.95 * angle_support * 0.80),
        "confidence_components": {"calculation_integrity": 0.95, "angle_support": angle_support, "method_maturity": 0.80},
        "confidence_state": confidence_state,
        "birth_time_dependency": "hard" if angle_involved else "soft",
        "asteroid_involved": asteroid_involved,
        "report_surface_visibility": ["internal_rd", "engineering_diagnostic"],
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
        "report_surface_visibility": ["internal_rd", "engineering_diagnostic"],
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
        "report_surface_visibility": ["internal_rd", "engineering_diagnostic"],
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
    # Canonical short-form angle names only, one entry per angle. Listing
    # both "ASC" and "Ascendant" here (as earlier code did) makes
    # _angle_longitude resolve the same longitude twice under two
    # different dict keys, so the contact scan below emits the same
    # aspect as two separate events ("...natal ASC" and "...natal
    # Ascendant"). Short form (not the long form) is required: it's the
    # target-key convention every progression/solar-arc content library
    # and generate.py's THEME_MAP already use ("ASC"/"MC" keys, no
    # "Ascendant"/"Midheaven" entries exist there) — using the long form
    # instead would still dedupe, but would silently route every angle
    # contact to generic fallback prose instead of its written block.
    # IC is intentionally omitted: its alias resolves to "Imum Coeli"
    # (space) while the natal payload stores "Imum_Coeli" (underscore),
    # so it has never actually matched here — fixing that lookup would
    # newly include IC contacts that have never appeared in a report
    # before, which is an event-inclusion change and needs separate
    # sign-off rather than riding along with a dedup fix.
    for name in ("ASC", "MC", "DSC", "Vertex"):
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


def _natal_coordinates(natal_payload: dict) -> tuple[float, float] | None:
    user_profile = natal_payload.get("user_profile") if isinstance(natal_payload.get("user_profile"), dict) else {}
    coordinates = user_profile.get("resolved_coordinates") if isinstance(user_profile.get("resolved_coordinates"), dict) else {}
    lat = coordinates.get("latitude")
    lon = coordinates.get("longitude")
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        return float(lat), float(lon)
    return None


def _progressed_angle_longitude(natal_payload: dict, angle_name: str, moment: datetime) -> float | None:
    """
    Computes a progressed angle (ASC/MC/IC/DSC) at genuine Swiss Ephemeris
    precision, using the same natal_jd + age_years convention already used
    for progressed planets (one ephemeris day per year of life), evaluated
    at the natal birth location via swe.houses — not a flat +1 degree/year
    approximation. Angle motion is non-linear (it depends on geographic
    latitude and where the angle sits relative to the ecliptic), so this
    mirrors the exact house-angle calculation and Porphyry polar fallback
    already used in engine/natal_engine.py rather than reimplementing the
    RA-to-ecliptic-longitude trigonometry by hand.
    """
    if swe is None:
        return None
    aliases = {"ASC": "Ascendant", "IC": "Imum Coeli", "DSC": "Descendant"}
    base_angle = aliases.get(angle_name, angle_name)
    natal_jd = _natal_jd(natal_payload)
    birth_dt = _birth_datetime(natal_payload)
    coordinates = _natal_coordinates(natal_payload)
    if natal_jd is None or birth_dt is None or coordinates is None:
        return None
    lat, lon = coordinates
    age_years = max(0.0, (_ensure_utc(moment) - birth_dt).total_seconds() / 86400.0 / TROPICAL_YEAR_DAYS)
    progressed_jd = natal_jd + age_years
    try:
        _cusps, ascmc = swe.houses(progressed_jd, lat, lon, b"P")
    except swe.Error:
        try:
            _cusps, ascmc = swe.houses(progressed_jd, lat, lon, b"O")
        except swe.Error:
            return None
    ascendant = ascmc[0] % 360.0
    midheaven = ascmc[1] % 360.0
    if base_angle in ("Ascendant", "ASC"):
        return ascendant
    if base_angle in ("Midheaven", "MC"):
        return midheaven
    if base_angle in ("Descendant", "DSC"):
        return (ascendant + 180.0) % 360.0
    if base_angle in ("Imum Coeli", "IC"):
        return (midheaven + 180.0) % 360.0
    return None


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

def _progressed_speed(natal_payload: dict, body_name: str, moment: datetime) -> float:
    if body_name in ANGLE_NAMES:
        moment_utc = _ensure_utc(moment)
        lon_now = _progressed_angle_longitude(natal_payload, body_name, moment_utc)
        lon_next = _progressed_angle_longitude(natal_payload, body_name, moment_utc + timedelta(days=1))
        if lon_now is None or lon_next is None:
            return 0.0
        return _signed_angle_delta(lon_next, lon_now)
    if body_name in ANCHOR_ASTEROIDS:
        return 0.1 / TROPICAL_YEAR_DAYS
    natal_jd = _natal_jd(natal_payload)
    birth_dt = _birth_datetime(natal_payload)
    if natal_jd is None or birth_dt is None or swe is None:
        return 0.0
    age_years = max(0.0, (_ensure_utc(moment) - birth_dt).total_seconds() / 86400.0 / TROPICAL_YEAR_DAYS)
    try:
        coordinates, _flags = swe.calc_ut(natal_jd + age_years, BODY_IDS.get(body_name, 0), CALC_FLAGS)
        return float(coordinates[3]) / TROPICAL_YEAR_DAYS
    except Exception:
        return 0.0

def _transit_speed(body_name: str, moment: datetime) -> float:
    if swe is None or body_name not in BODY_IDS:
        return 0.0
    try:
        y, m, d, h = moment.year, moment.month, moment.day, moment.hour + moment.minute/60.0 + moment.second/3600.0
        jd = swe.julday(y, m, d, h)
        coordinates, _flags = swe.calc_ut(jd, BODY_IDS[body_name], CALC_FLAGS)
        return float(coordinates[3])
    except Exception:
        return 0.0

def _transit_longitude(body_name: str, moment: datetime) -> float | None:
    if swe is None or body_name not in BODY_IDS:
        return None
    try:
        y, m, d, h = moment.year, moment.month, moment.day, moment.hour + moment.minute/60.0 + moment.second/3600.0
        jd = swe.julday(y, m, d, h)
        coordinates, _flags = swe.calc_ut(jd, BODY_IDS[body_name], CALC_FLAGS)
        return float(coordinates[0] % 360.0)
    except Exception:
        return None

def _applying_state_relative_velocity(
    lon_a: float, speed_a: float, 
    lon_b: float, speed_b: float, 
    aspect_angle: float
) -> str | None:
    current_gap = min(abs((lon_a - lon_b) % 360.0), 360.0 - abs((lon_a - lon_b) % 360.0))
    fut_a, fut_b = lon_a + speed_a, lon_b + speed_b
    future_gap = min(abs((fut_a - fut_b) % 360.0), 360.0 - abs((fut_a - fut_b) % 360.0))
    current_delta = abs(current_gap - aspect_angle)
    future_delta = abs(future_gap - aspect_angle)
    if abs(future_delta - current_delta) < 1e-6:
        return None
    return "applying" if future_delta < current_delta else "separating"

def _find_prog_to_prog_contact_exact(natal_payload: dict, source_name: str, target_name: str, aspect_angle: float, start: datetime, end: datetime) -> datetime | None:
    cursor = start
    step = timedelta(days=SCAN_STEP_DAYS)
    previous_time = cursor
    previous_value = _prog_to_prog_delta(natal_payload, source_name, target_name, aspect_angle, previous_time)
    best_time = None
    best_abs = 999.0
    while cursor <= end:
        value = _prog_to_prog_delta(natal_payload, source_name, target_name, aspect_angle, cursor)
        if abs(value) < best_abs:
            best_abs = abs(value)
            best_time = cursor
        if _crossed_zero(previous_value, value):
            return _bisect_prog_to_prog(natal_payload, source_name, target_name, aspect_angle, previous_time, cursor)
        previous_time = cursor
        previous_value = value
        cursor += step
    if best_time is not None and best_abs <= CONTACT_ORB:
        return best_time
    return None

def _prog_to_prog_delta(natal_payload: dict, source_name: str, target_name: str, aspect_angle: float, moment: datetime) -> float:
    s_lon = progressed_longitude(natal_payload, source_name, moment)
    t_lon = progressed_longitude(natal_payload, target_name, moment)
    if s_lon is None or t_lon is None:
        return 999.0
    return _aspect_delta(s_lon, t_lon, aspect_angle)

def _bisect_prog_to_prog(natal_payload: dict, source_name: str, target_name: str, aspect_angle: float, low: datetime, high: datetime) -> datetime:
    low_value = _prog_to_prog_delta(natal_payload, source_name, target_name, aspect_angle, low)
    for _ in range(48):
        midpoint = low + (high - low) / 2
        mid_value = _prog_to_prog_delta(natal_payload, source_name, target_name, aspect_angle, midpoint)
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

def _find_transit_to_prog_contact_exact(natal_payload: dict, transit_name: str, prog_name: str, aspect_angle: float, start: datetime, end: datetime) -> datetime | None:
    cursor = start
    step = timedelta(days=1)
    previous_time = cursor
    previous_value = _transit_to_prog_delta(natal_payload, transit_name, prog_name, aspect_angle, previous_time)
    best_time = None
    best_abs = 999.0
    while cursor <= end:
        value = _transit_to_prog_delta(natal_payload, transit_name, prog_name, aspect_angle, cursor)
        if abs(value) < best_abs:
            best_abs = abs(value)
            best_time = cursor
        if _crossed_zero(previous_value, value):
            return _bisect_transit_to_prog(natal_payload, transit_name, prog_name, aspect_angle, previous_time, cursor)
        previous_time = cursor
        previous_value = value
        cursor += step
    if best_time is not None and best_abs <= CONTACT_ORB:
        return best_time
    return None

def _transit_to_prog_delta(natal_payload: dict, transit_name: str, prog_name: str, aspect_angle: float, moment: datetime) -> float:
    t_lon = _transit_longitude(transit_name, moment)
    p_lon = progressed_longitude(natal_payload, prog_name, moment)
    if t_lon is None or p_lon is None:
        return 999.0
    return _aspect_delta(t_lon, p_lon, aspect_angle)

def _bisect_transit_to_prog(natal_payload: dict, transit_name: str, prog_name: str, aspect_angle: float, low: datetime, high: datetime) -> datetime:
    low_value = _transit_to_prog_delta(natal_payload, transit_name, prog_name, aspect_angle, low)
    for _ in range(48):
        midpoint = low + (high - low) / 2
        mid_value = _transit_to_prog_delta(natal_payload, transit_name, prog_name, aspect_angle, midpoint)
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
