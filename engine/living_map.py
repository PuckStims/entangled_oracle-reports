from __future__ import annotations

import copy
import math
import os
from datetime import date, datetime, timedelta
from typing import List, TypedDict

import swisseph as swe

from engine.location_services import build_location_evidence_record


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")
swe.set_ephe_path(EPHE_PATH)

CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED
FORMULA_VERSION = "living_map_v0.2.0"

TRANSIT_BODIES = {
    "Sun": (swe.SUN, 1.0),
    "Mercury": (swe.MERCURY, 1.0),
    "Venus": (swe.VENUS, 1.0),
    "Mars": (swe.MARS, 1.5),
    "Jupiter": (swe.JUPITER, 2.0),
    "Saturn": (swe.SATURN, 1.5),
    "Uranus": (swe.URANUS, 1.0),
    "Neptune": (swe.NEPTUNE, 1.0),
    "Pluto": (swe.PLUTO, 1.0),
}
TARGET_ANGLES = ("Ascendant", "Midheaven", "Descendant", "Imum_Coeli")


class TimingWindow(TypedDict):
    id: str
    active_planet: str
    event_type: str
    target: str
    target_evidence_id: str
    start_date: str
    exact_date: str
    end_date: str
    strength: str
    minimum_orb: float
    temporary_weather_note: str


class LivingMapEvidenceRecord(TypedDict):
    formula_version: str
    destination: dict
    date_range: dict
    static_baseline: dict
    timing_windows: List[TimingWindow]
    unsupported_methods: List[str]
    warnings: List[str]
    appendix_trace: dict


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _julian_day(day: date) -> float:
    return swe.julday(day.year, day.month, day.day, 12.0)


def _longitude(body_id: int, day: date) -> float:
    coords, _flags = swe.calc_ut(_julian_day(day), body_id, CALC_FLAGS)
    return float(coords[0] % 360.0)


def _angle_difference(a: float, b: float) -> float:
    diff = abs((a - b) % 360.0)
    return min(diff, 360.0 - diff)


def _strength(minimum_orb: float, configured_orb: float) -> str:
    ratio = minimum_orb / configured_orb if configured_orb else 1.0
    if ratio <= 0.2:
        return "high"
    if ratio <= 0.6:
        return "medium"
    return "low"


def _date_range(start: date, end: date) -> list[date]:
    days: list[date] = []
    cursor = start
    while cursor <= end:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _angle_targets(static_baseline: dict) -> dict[str, float]:
    angles = ((static_baseline.get("relocated_chart") or {}).get("angles") or {})
    targets: dict[str, float] = {}
    for angle in TARGET_ANGLES:
        record = angles.get(angle) or {}
        longitude = record.get("longitude")
        if isinstance(longitude, (int, float)):
            targets[angle] = float(longitude)
    return targets


def _scan_windows(start: date, end: date, targets: dict[str, float]) -> list[TimingWindow]:
    windows: list[TimingWindow] = []
    days = _date_range(start, end)

    for body, (body_id, orb) in TRANSIT_BODIES.items():
        for angle, target_longitude in targets.items():
            active: list[tuple[date, float]] = []
            for day in days:
                distance = _angle_difference(_longitude(body_id, day), target_longitude)
                if distance <= orb:
                    active.append((day, distance))
                elif active:
                    windows.append(_build_window(body, angle, orb, active))
                    active = []
            if active:
                windows.append(_build_window(body, angle, orb, active))

    windows.sort(key=lambda item: (item["exact_date"], item["active_planet"], item["target"]))
    return windows[:24]


def _build_window(body: str, angle: str, configured_orb: float, active_days: list[tuple[date, float]]) -> TimingWindow:
    exact_day, minimum_orb = min(active_days, key=lambda item: item[1])
    start_day = active_days[0][0]
    end_day = active_days[-1][0]
    min_orb = round(minimum_orb, 3)
    strength = _strength(min_orb, configured_orb)
    return {
        "id": f"transit:{body}:{angle}:{exact_day.isoformat()}",
        "active_planet": body,
        "event_type": "transit_to_relocated_angle",
        "target": angle,
        "target_evidence_id": f"relocated_angle:{angle}",
        "start_date": start_day.isoformat(),
        "exact_date": exact_day.isoformat(),
        "end_date": end_day.isoformat(),
        "strength": strength,
        "minimum_orb": min_orb,
        "temporary_weather_note": (
            f"{body} is temporarily within {configured_orb} degrees of the relocated {angle}. "
            "This is timing weather layered over the static place baseline, not a permanent location feature."
        ),
    }


def build_living_map_evidence(
    natal_payload: dict,
    destination: dict,
    start_date: str,
    end_date: str,
) -> LivingMapEvidenceRecord:
    """
    Build v1 Living Map timing evidence: date-bounded transits to relocated
    angles, linked back to the static LocationEvidenceRecord baseline.
    """
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if end < start:
        raise ValueError("Living Map end_date must be on or after start_date.")

    static_baseline = build_location_evidence_record(natal_payload, destination)
    targets = _angle_targets(static_baseline)
    warnings: list[str] = []
    if not targets:
        warnings.append("No relocated angle targets were available for timing overlay.")

    windows = _scan_windows(start, end, targets) if targets else []
    if not windows:
        warnings.append("No transits to relocated angles were found within configured v1 orbs for this date range.")

    destination_context = static_baseline.get("destination_context") or dict(destination)
    return {
        "formula_version": FORMULA_VERSION,
        "destination": copy.deepcopy(destination_context),
        "date_range": {"start_date": start_date, "end_date": end_date},
        "static_baseline": copy.deepcopy(static_baseline),
        "timing_windows": windows,
        "unsupported_methods": ["relocated_returns", "dynamic_astrocartography", "parans"],
        "warnings": warnings,
        "appendix_trace": {
            "methodology": "Daily noon UTC scan of transiting planets to relocated chart angles.",
            "transit_bodies": list(TRANSIT_BODIES),
            "target_angles": list(targets),
            "orb_policy_degrees": {body: orb for body, (_id, orb) in TRANSIT_BODIES.items()},
            "unsupported_methods": ["relocated_returns", "dynamic_astrocartography", "parans"],
            "warnings": warnings,
        },
    }
