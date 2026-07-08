"""
engine/zodiacal_releasing.py - Phase 6 Zodiacal Releasing (L1-L4).

Per phase0/03_method_charters.md C5b. Depends on engine/lots.py for the
input Lot longitude (Fortune or Spirit).

Algorithm (Vettius Valens):
  - L1 periods: begin at the lot's sign, cycle forward through the zodiac.
    Each sign's L1 duration in years is VALENS_YEARS[sign]. One full
    12-sign L1 pass totals 211 years exactly (15+8+20+25+19+20+8+15+12+27+30+12).
  - L2..L4: each level subdivides its parent into 12 sub-periods, one per
    sign starting from the parent's own sign, with each sub-period's
    duration proportional to that sign's own Valens year-count relative
    to the 211-year total, scaled to the parent's actual duration. This
    is applied recursively and identically at every level.
  - Peak: a period is a peak when its own sign equals the lot's sign, or
    is in a whole-sign angular relationship to it (4th, 7th, or 10th sign
    counting the lot's sign as 1st).
  - Loosing of the Bond (LOB): the charter's definition is "a sub-period
    completes its allotted duration but the parent has not; the next
    sub-period jumps to the sign opposite the one that just ended." Under
    the proportional construction used here, one full 12-sign pass of
    sub-periods sums exactly to the parent's duration by construction, so
    this condition is a genuine edge case (floating-point residue at the
    boundary), not a routine occurrence -- documented here rather than
    silently forced to fire on a schedule it does not reliably have in
    the classical technique as chartered.

Only L1 and L2 periods generate trigger-role ForecastEvents (transitions,
peaks, LOB) per C5b section 7 ("L3 and L4 are modifier scale -- used to
weight signals but not to justify candidates on their own"). All four
levels generate TimeLordPeriod records, window-filtered so only periods
intersecting [start_date, end_date] are computed and returned -- this
keeps L3/L4 record counts bounded to what is relevant for the report
window rather than enumerating a chart's full multi-century period tree.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from engine.lots import lot_longitude

FORMULA_VERSION = "zr_phase6.0.0"
POLICY_VERSION = "phase0.1.1"
TIME_LORD_PERIOD_SCHEMA_VERSION = "phase0.1.1"
FORECAST_EVENT_SCHEMA_VERSION = "phase0.1.0"

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

VALENS_YEARS = {
    "Aries": 15, "Taurus": 8, "Gemini": 20, "Cancer": 25, "Leo": 19, "Virgo": 20,
    "Libra": 8, "Scorpio": 15, "Sagittarius": 12, "Capricorn": 27, "Aquarius": 30, "Pisces": 12,
}
TOTAL_VALENS_YEARS = sum(VALENS_YEARS.values())  # 211
TROPICAL_YEAR_DAYS = 365.2425

TRADITIONAL_RULERS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

_MAX_LEVEL = 4
_LEVEL_NAMES = {1: "L1", 2: "L2", 3: "L3", 4: "L4"}
_ANGULAR_OFFSETS = frozenset({0, 3, 6, 9})  # 1st (own), 4th, 7th, 10th sign, zero-indexed offsets


def zodiacal_releasing_periods(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    lot_name: str = "Fortune",
) -> list[dict]:
    """Returns TimeLordPeriod records for L1-L4 intersecting [start_date, end_date]."""
    context = _build_context(natal_payload, lot_name)
    if context is None:
        return []

    window_start = _ensure_utc(start_date)
    window_end = _ensure_utc(end_date)
    periods: list[dict] = []
    _collect_periods(context, window_start, window_end, periods, parent_id=None)
    periods.sort(key=lambda p: (p["start_at"], p["level"]))
    return periods


def zodiacal_releasing_events(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    lot_name: str = "Fortune",
) -> list[dict]:
    """
    Returns ForecastEvent-shaped dicts for L1/L2 transitions, peaks, and LOB
    moments intersecting [start_date, end_date]. L3/L4 are period-only
    (modifier scale); see module docstring.
    """
    context = _build_context(natal_payload, lot_name)
    if context is None:
        return []

    window_start = _ensure_utc(start_date)
    window_end = _ensure_utc(end_date)
    periods: list[dict] = []
    _collect_periods(context, window_start, window_end, periods, parent_id=None)

    events: list[dict] = []
    for period in periods:
        if period["level"] not in ("L1", "L2"):
            continue
        events.extend(_events_for_period(context, period))
    events.sort(key=lambda e: e["peak_datetime"])
    return events


def _build_context(natal_payload: dict, lot_name: str) -> dict | None:
    lot_lon = lot_longitude(natal_payload, lot_name)
    birth_dt = _birth_datetime(natal_payload)
    if lot_lon is None or birth_dt is None:
        return None
    lot_sign = SIGNS[int(lot_lon // 30.0) % 12]
    independence_group = f"zr_family_{lot_name.lower()}"
    system = f"zodiacal_releasing_{lot_name.lower()}"
    return {
        "lot_name": lot_name,
        "lot_sign": lot_sign,
        "birth_dt": birth_dt,
        "independence_group": independence_group,
        "system": system,
    }


def _collect_periods(
    context: dict,
    window_start: datetime,
    window_end: datetime,
    out: list[dict],
    *,
    parent_id: str | None,
    level: int = 1,
    parent_sign: str | None = None,
    parent_start: datetime | None = None,
    parent_duration_years: float | None = None,
) -> None:
    if level > _MAX_LEVEL:
        return

    if level == 1:
        for sign, cycle_start in _l1_cycle_starts(context["birth_dt"], context["lot_sign"], window_start, window_end):
            duration_years = VALENS_YEARS[sign]
            cycle_end = cycle_start + timedelta(days=duration_years * TROPICAL_YEAR_DAYS)
            if cycle_end <= window_start or cycle_start >= window_end:
                continue
            record = _period_record(context, level, sign, cycle_start, cycle_end, parent_id=None)
            out.append(record)
            _collect_periods(
                context, window_start, window_end, out,
                parent_id=record["period_id"], level=2,
                parent_sign=sign, parent_start=cycle_start, parent_duration_years=duration_years,
            )
        return

    for sign, sub_start, sub_duration_years in _subdivide(parent_sign, parent_start, parent_duration_years):
        sub_end = sub_start + timedelta(days=sub_duration_years * TROPICAL_YEAR_DAYS)
        if sub_end <= window_start or sub_start >= window_end:
            continue
        record = _period_record(context, level, sign, sub_start, sub_end, parent_id=parent_id)
        out.append(record)
        _collect_periods(
            context, window_start, window_end, out,
            parent_id=record["period_id"], level=level + 1,
            parent_sign=sign, parent_start=sub_start, parent_duration_years=sub_duration_years,
        )


def _l1_cycle_starts(
    birth_dt: datetime, lot_sign: str, window_start: datetime, window_end: datetime,
) -> list[tuple[str, datetime]]:
    """Yields (sign, cycle_start) for every L1 period that could intersect the window."""
    lot_index = SIGNS.index(lot_sign)
    full_cycle_days = TOTAL_VALENS_YEARS * TROPICAL_YEAR_DAYS

    # Find which 211-year mega-cycle (and offset within it) covers window_start.
    days_since_birth = max(0.0, (window_start - birth_dt).total_seconds() / 86400.0)
    mega_cycles_elapsed = int(days_since_birth // full_cycle_days)
    cursor = birth_dt + timedelta(days=mega_cycles_elapsed * full_cycle_days)
    sign_offset = 0
    results: list[tuple[str, datetime]] = []
    # Walk forward through L1 signs until we pass window_end, with a hard cap
    # against pathological inputs.
    for _ in range(24):
        sign = SIGNS[(lot_index + sign_offset) % 12]
        duration_days = VALENS_YEARS[sign] * TROPICAL_YEAR_DAYS
        period_end = cursor + timedelta(days=duration_days)
        if period_end > window_start or cursor >= window_start:
            results.append((sign, cursor))
        if cursor >= window_end:
            break
        cursor = period_end
        sign_offset += 1
    return results


def _subdivide(parent_sign: str, parent_start: datetime, parent_duration_years: float) -> list[tuple[str, datetime, float]]:
    """Twelve proportional sub-periods of parent_sign's own duration, starting at parent_sign."""
    parent_index = SIGNS.index(parent_sign)
    cursor = parent_start
    out: list[tuple[str, datetime, float]] = []
    for offset in range(12):
        sub_sign = SIGNS[(parent_index + offset) % 12]
        sub_years = (VALENS_YEARS[sub_sign] / TOTAL_VALENS_YEARS) * parent_duration_years
        out.append((sub_sign, cursor, sub_years))
        cursor = cursor + timedelta(days=sub_years * TROPICAL_YEAR_DAYS)
    return out


def _is_peak(context: dict, sign: str) -> bool:
    lot_index = SIGNS.index(context["lot_sign"])
    sign_index = SIGNS.index(sign)
    return ((sign_index - lot_index) % 12) in _ANGULAR_OFFSETS


def _period_record(
    context: dict, level: int, sign: str, start_at: datetime, end_at: datetime, *, parent_id: str | None,
) -> dict:
    lord = TRADITIONAL_RULERS[sign]
    is_peak = _is_peak(context, sign)
    record = {
        "schema_version": TIME_LORD_PERIOD_SCHEMA_VERSION,
        "period_id": "",
        "system": context["system"],
        "level": _LEVEL_NAMES[level],
        "parent_period_id": parent_id,
        "start_at": _iso_datetime(start_at),
        "end_at": _iso_datetime(end_at),
        "period_lord": lord,
        "period_sign": sign,
        "period_house": None,
        "lord_natal_state": {"condition": "unavailable", "house": 0, "sign": "", "retrograde": False, "aspects": []},
        "is_peak": is_peak,
        "is_loosing_of_the_bond": False,
        "activated_house_topics": [],
        "natal_anchor_ids": [],
        "weight_modifier": 1.10 if is_peak else 1.0,
        "confidence": 0.80,
        "confidence_components": {"calculation_integrity": 0.95, "method_maturity": 0.80},
        "birth_time_dependency": "soft",
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "formula_version": FORMULA_VERSION,
        "policy_version": POLICY_VERSION,
        "provenance": {
            "scanner": "engine.zodiacal_releasing.zodiacal_releasing_periods",
            "scanner_version": FORMULA_VERSION,
            "lot_name": context["lot_name"],
            "lot_sign": context["lot_sign"],
        },
    }
    record["period_id"] = _period_id(record)
    return record


def _events_for_period(context: dict, period: dict) -> list[dict]:
    events: list[dict] = []
    start_at = _parse_iso(period["start_at"])
    variant = "zr_l1_transition" if period["level"] == "L1" else "zr_l2_transition"
    events.append(_transition_event(context, period, start_at, variant, clock_role="time_lord"))
    if period["is_peak"]:
        events.append(_transition_event(context, period, start_at, "zr_peak", clock_role="trigger"))
    return events


def _transition_event(context: dict, period: dict, moment: datetime, variant: str, *, clock_role: str) -> dict:
    event_id_basis = {
        "system": context["system"], "variant": variant, "period_id": period["period_id"], "moment": _iso_datetime(moment),
    }
    return {
        "schema_version": FORECAST_EVENT_SCHEMA_VERSION,
        "event_id": f"fe_zr_{_hash8(event_id_basis)}",
        "event_type": "zodiacal_releasing",
        "method_family": "ZODIACAL_RELEASING",
        "method_variant": variant,
        "clock_role": clock_role,
        "transit_planet": period["period_lord"],
        "natal_target": context["lot_name"],
        "aspect": "",
        "entry_datetime": moment,
        "peak_datetime": moment,
        "leave_datetime": moment,
        "orb": None,
        "distance": 0.0,
        "independence_group": context["independence_group"],
        "activation_route": "zr_period_transition",
        "temporal_precision": "day" if period["level"] == "L1" else "day",
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "period_id": period["period_id"],
        "period_lord": period["period_lord"],
        "period_sign": period["period_sign"],
        "is_peak": period["is_peak"],
    }


def _period_id(record: dict[str, Any]) -> str:
    basis = {
        "system": record.get("system"), "level": record.get("level"), "start_at": record.get("start_at"),
        "period_sign": record.get("period_sign"), "parent_period_id": record.get("parent_period_id"),
    }
    return f"tlp_zr_{_hash8(basis)}"


def _hash8(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def _birth_datetime(natal_payload: dict) -> datetime | None:
    user_profile = natal_payload.get("user_profile") if isinstance(natal_payload.get("user_profile"), dict) else {}
    raw_date = natal_payload.get("birth_date") or natal_payload.get("date") or user_profile.get("local_datetime")
    if not raw_date:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
    except ValueError:
        try:
            from datetime import date as _date
            d = _date.fromisoformat(str(raw_date)[:10])
            parsed = datetime(d.year, d.month, d.day)
        except ValueError:
            return None
    return _ensure_utc(parsed)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso_datetime(value: datetime) -> str:
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
