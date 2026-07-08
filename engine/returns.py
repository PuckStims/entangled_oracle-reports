"""
engine/returns.py - Phase 4 exact return-moment scanner.

Computes event-level Solar, Lunar, Jupiter, and Saturn returns as internal
predictive evidence. Return-chart interpretation is intentionally deferred.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import swisseph as swe
except ImportError:  # pragma: no cover - exercised by no-ephemeris test environments
    swe = None


FORMULA_VERSION = "returns_phase4.0.0"
POLICY_VERSION = "phase0.1.1"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")
if swe is not None:
    swe.set_ephe_path(EPHE_PATH)

CALC_FLAGS = (swe.FLG_SWIEPH | swe.FLG_SPEED) if swe is not None else 0
RETURN_TOLERANCE_DEGREES = 0.01

RETURN_BODIES = {
    "Sun": swe.SUN if swe is not None else 0,
    "Moon": swe.MOON if swe is not None else 1,
    "Jupiter": swe.JUPITER if swe is not None else 5,
    "Saturn": swe.SATURN if swe is not None else 6,
}

RETURN_VARIANTS = {
    "Sun": "solar_return",
    "Moon": "lunar_return",
    "Jupiter": "jupiter_return",
    "Saturn": "saturn_return",
}

RETURN_STEP_HOURS = {
    "Sun": 12,
    "Moon": 6,
    "Jupiter": 24,
    "Saturn": 24,
}

RETURN_WINDOW_HOURS = {
    "Sun": 12,
    "Moon": 12,
    "Jupiter": 24,
    "Saturn": 24,
}

RETURN_TEMPORAL_PRECISION = {
    "Sun": "instant",
    "Moon": "instant",
    "Jupiter": "day",
    "Saturn": "day",
}


def scan_return_events(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    *,
    bodies: tuple[str, ...] = ("Sun", "Moon", "Jupiter", "Saturn"),
) -> list[dict]:
    """Return normalized scanner events for exact body returns in the window."""
    start = _ensure_utc(start_date)
    end = _ensure_utc(end_date)
    events: list[dict] = []

    for body in bodies:
        natal_longitude = _natal_longitude(natal_payload, body)
        if natal_longitude is None:
            continue
        for exact_at in _find_return_moments(body, natal_longitude, start, end):
            events.append(_return_event(body, natal_longitude, exact_at))

    events.sort(key=lambda event: (event["peak_datetime"], event["return_body"]))
    return events


def _find_return_moments(
    body: str,
    natal_longitude: float,
    start: datetime,
    end: datetime,
) -> list[datetime]:
    step = timedelta(hours=RETURN_STEP_HOURS.get(body, 12))
    cursor = start
    prev_time = cursor
    prev_diff = _return_difference(body, natal_longitude, prev_time)
    moments: list[datetime] = []

    if abs(prev_diff) <= RETURN_TOLERANCE_DEGREES:
        moments.append(prev_time)

    cursor += step
    while cursor <= end + step:
        current_time = min(cursor, end)
        current_diff = _return_difference(body, natal_longitude, current_time)

        if _crossed_zero(prev_diff, current_diff):
            exact = _bisect_return(body, natal_longitude, prev_time, current_time)
            if start <= exact <= end:
                moments.append(exact)
        elif abs(current_diff) <= RETURN_TOLERANCE_DEGREES:
            if start <= current_time <= end:
                moments.append(current_time)

        if current_time >= end:
            break
        prev_time = current_time
        prev_diff = current_diff
        cursor = current_time + step

    return _dedupe_moments(moments)


def _return_event(body: str, natal_longitude: float, exact_at: datetime) -> dict:
    window = timedelta(hours=RETURN_WINDOW_HOURS.get(body, 12))
    exact_at = _ensure_utc(exact_at)
    return {
        "event_type": "return",
        "return_body": body,
        "transit_planet": body,
        "natal_target": body,
        "aspect": "Return",
        "method_variant": RETURN_VARIANTS[body],
        "clock_role": "return",
        "activation_route": "return_moment",
        "independence_group": f"return_family_{body.lower()}",
        "temporal_precision": RETURN_TEMPORAL_PRECISION[body],
        "orb": 0.0,
        "allowed_orb": RETURN_TOLERANCE_DEGREES,
        "exactness": 1.0,
        "event_weight": 0.85,
        "target_relevance": 0.9 if body in {"Sun", "Moon"} else 0.7,
        "trigger_strength": 0.85 if body in {"Sun", "Moon"} else 0.65,
        "signal_strength": 0.85 if body in {"Sun", "Moon"} else 0.65,
        "entry_datetime": exact_at - window,
        "peak_datetime": exact_at,
        "leave_datetime": exact_at + window,
        "exact_datetimes": [exact_at],
        "natal_longitude": round(natal_longitude % 360.0, 6),
        "confidence": 0.833,
        "confidence_components": {
            "calculation_integrity": 0.98,
            "method_maturity": 0.85,
            "exactness_support": 1.0,
        },
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "formula_version": FORMULA_VERSION,
        "policy_version": POLICY_VERSION,
    }


def _bisect_return(body: str, natal_longitude: float, low: datetime, high: datetime) -> datetime:
    low_diff = _return_difference(body, natal_longitude, low)
    high_diff = _return_difference(body, natal_longitude, high)
    for _ in range(64):
        midpoint = low + (high - low) / 2
        mid_diff = _return_difference(body, natal_longitude, midpoint)
        if abs(mid_diff) <= RETURN_TOLERANCE_DEGREES:
            return midpoint
        if _crossed_zero(low_diff, mid_diff):
            high = midpoint
            high_diff = mid_diff
        else:
            low = midpoint
            low_diff = mid_diff
        if abs((high - low).total_seconds()) <= 1:
            break
    return low + (high - low) / 2


def _return_difference(body: str, natal_longitude: float, moment: datetime) -> float:
    return _signed_angle_delta(_body_longitude(body, moment), natal_longitude)


def _body_longitude(body: str, moment: datetime) -> float:
    if swe is None:
        raise RuntimeError("swisseph is unavailable; return scanner cannot compute live return moments")
    body_id = RETURN_BODIES[body]
    coordinates, _flags = swe.calc_ut(_julian_day(moment), body_id, CALC_FLAGS)
    return float(coordinates[0] % 360.0)


def _natal_longitude(natal_payload: dict, body: str) -> float | None:
    standard = natal_payload.get("standard_planets") if isinstance(natal_payload.get("standard_planets"), dict) else {}
    data = standard.get(body)
    if not isinstance(data, dict):
        return None
    value = data.get("longitude")
    if not isinstance(value, (int, float)):
        return None
    return float(value % 360.0)


def _crossed_zero(left: float, right: float) -> bool:
    if left == 0 or right == 0:
        return True
    return (left < 0 < right) or (right < 0 < left)


def _dedupe_moments(moments: list[datetime]) -> list[datetime]:
    ordered = sorted(_ensure_utc(moment) for moment in moments)
    deduped: list[datetime] = []
    for moment in ordered:
        if deduped and abs((moment - deduped[-1]).total_seconds()) < 6 * 3600:
            if abs(moment.second) < abs(deduped[-1].second):
                deduped[-1] = moment
            continue
        deduped.append(moment)
    return deduped


def _signed_angle_delta(longitude: float, target: float) -> float:
    return ((float(longitude) - float(target) + 180.0) % 360.0) - 180.0


def _julian_day(moment: datetime) -> float:
    if swe is None:
        raise RuntimeError("swisseph is unavailable; return scanner cannot compute Julian day")
    moment = _ensure_utc(moment)
    hour = moment.hour + moment.minute / 60.0 + moment.second / 3600.0 + moment.microsecond / 3_600_000_000.0
    return swe.julday(moment.year, moment.month, moment.day, hour)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
