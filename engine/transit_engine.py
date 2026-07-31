"""
engine/transit_engine.py — Entangled Oracle Year-Ahead Transit Engine

Provides two compatible layers:
- compute_current_transits(...): current-sky snapshot used by the legacy report
- compute_year_ahead_events(...): 12-month event timeline for the Year Ahead report

The forecast scanner produces structured events for:
- natal transits (Saturn through Mars)
- Whole Sign house ingresses (Jupiter through Pluto)
- planetary stations (Mercury through Pluto)
- solar and lunar eclipses that contact natal targets

All calendar times are calculated in UTC. The report layer formats dates for display.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import swisseph as swe

from engine.forecast_event_adapter import normalize_to_forecast_event
from formulas.standard.forecast_activation import (
    build_forecast_activation_profile,
    enrich_forecast_event,
    link_related_forecast_events,
)

# ── Swiss Ephemeris Setup ──────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")
swe.set_ephe_path(EPHE_PATH)

CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED
UTC = ZoneInfo("UTC")


# ── Refinement Precision Constants ────────────────────────────
#
# All tolerances are in ecliptic degrees.
#
# _REFINE_TOLERANCE   — bisection terminates when the angular error is smaller
#                       than this value.  0.01° ≈ 36 arc-seconds, which is
#                       well below the precision of any publicly visible date.
#
# _BISECT_MAX_ITER    — hard iteration ceiling.  53 iterations halve a 12-hour
#                       bracket 53 times → sub-millisecond residual.  In
#                       practice the angular test terminates far sooner.
#
# _CYCLE_MERGE_GAP    — consecutive orb windows for the same (planet, aspect,
#                       target) separated by fewer than this many days are
#                       treated as one retrograde cycle rather than independent
#                       activations.  120 days covers the maximum retrograde
#                       loop of any outer planet within one synodic cycle.

_REFINE_TOLERANCE = 0.01    # degrees
_BISECT_MAX_ITER  = 53
_CYCLE_MERGE_GAP  = 120     # days


# ── Transit Configuration ─────────────────────────────────────

TRANSIT_PLANETS = {
    swe.SATURN: "Saturn",
    swe.URANUS: "Uranus",
    swe.NEPTUNE: "Neptune",
    swe.PLUTO: "Pluto",
    swe.JUPITER: "Jupiter",
    swe.MARS: "Mars",
}

STATION_PLANETS = {
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
    swe.URANUS: "Uranus",
    swe.NEPTUNE: "Neptune",
    swe.PLUTO: "Pluto",
}

INGRESS_PLANETS = {
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
    swe.URANUS: "Uranus",
    swe.NEPTUNE: "Neptune",
    swe.PLUTO: "Pluto",
}

STANDARD_TARGETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "ASC", "MC", "Vertex",
]

# The Year Ahead block library has Mars copy for all natal targets.  The report
# priority filter later restricts Mars to the more meaningful personal points.
MARS_TARGETS = ["Sun", "Moon", "ASC", "MC", "Vertex"]

TRANSIT_ORB = {
    "Saturn": 3.0,
    "Uranus": 3.0,
    "Neptune": 3.0,
    "Pluto": 3.0,
    "Jupiter": 4.0,
    "Mars": 2.0,
}

# These values rank forecast-event salience only.
# They are intentionally distinct from config.PLANET_WEIGHTS, which ranks
# natal dominant aspects. Do not reconcile the two tables.
PLANET_SIGNIFICANCE = {
    "Pluto": 1.00,
    "Neptune": 0.95,
    "Uranus": 0.90,
    "Saturn": 0.85,
    "Jupiter": 0.75,
    "Mars": 0.55,
}

# ── Daily Activation Set (same-day scan, all planets but the Moon) ──
#
# Separate from TRANSIT_PLANETS/TRANSIT_ORB above on purpose. Those are
# sized for Year Ahead's week/month-scale forecasting, where a 3-4 degree
# orb is correct: a Saturn transit genuinely unfolds over weeks and the
# report wants to name it early. Daily Horoscope's "today's activation"
# selection is a fundamentally different question — not "what transit is
# broadly active this season" but "what feels specifically true today" —
# and reusing week/month orbs for that day-scale question was tried and
# empirically failed: a 120-day sweep against a real chart showed Neptune
# (orb 3.0, significance 0.95) winning 62% of days outright, because at
# Neptune's near-standstill daily motion, a 3-degree orb keeps it "in
# range" for weeks or months at a time. The Moon-house fallback never
# fired once in the entire sweep.
#
# The fix is graduated, tight, same-day-appropriate orbs, tightened
# further for slower bodies specifically because they linger longer at
# any given orb width — the goal is roughly comparable "days spent near
# exactness" across planets, not a flat orb regardless of speed. This
# matches standard transit-astrology convention for reading transits at
# daily granularity (roughly 1-2 degrees for personal planets, tighter
# still is common practice for transiting aspects read day to day — see
# Cafe Astrology's and Ruby Slipper Astrology's transit guides) and
# extends the same logic to the outer planets, which the wider Year
# Ahead orbs were never meant to answer this specific question with.
DAILY_ACTIVATION_PLANETS = {
    swe.SUN: "Sun",
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
    swe.URANUS: "Uranus",
    swe.NEPTUNE: "Neptune",
    swe.PLUTO: "Pluto",
}

DAILY_ACTIVATION_ORB = {
    "Sun": 1.0,
    "Mercury": 1.0,
    "Venus": 1.0,
    "Mars": 1.0,
    "Jupiter": 0.6,
    "Saturn": 0.4,
    "Uranus": 0.3,
    "Neptune": 0.2,
    "Pluto": 0.15,
}

DAILY_ACTIVATION_SIGNIFICANCE = {
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

ASPECT_ANGLES = [
    ("Conjunction", 0),
    ("Opposition", 180),
    ("Square", 90),
    ("Trine", 120),
    ("Sextile", 60),
    ("Quintile", 72),
    ("Biquintile", 144),
]

ASPECT_CHARACTERS = {
    "Conjunction": "flowing",
    "Trine": "flowing",
    "Sextile": "flowing",
    "Square": "challenging",
    "Opposition": "challenging",
    "Quintile": "creative",
    "Biquintile": "creative",
}

ANGLE_HOUSES = {
    "ASC": 1,
    "MC": 10,
    "DSC": 7,
    "IC": 4,
}

ECLIPSE_TARGET_KEYS = {
    "Sun": "1",
    "Moon": "2",
    "Mercury": "3",
    "Venus": "4",
    "Mars": "5",
    "Jupiter": "6",
    "Saturn": "7",
    "Uranus": "8",
    "Neptune": "9",
    "Pluto": "10",
    "ASC": "11",
    "MC": "12",
    "Vertex": "13",
}

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


# ── Time / Geometry Helpers ────────────────────────────────────


def _ensure_utc(value: datetime | None) -> datetime:
    """Returns a timezone-aware UTC datetime, defaulting to now."""
    if value is None:
        return datetime.now(tz=UTC)

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def _julian_day(moment: datetime) -> float:
    """Converts an aware datetime to a Swiss Ephemeris UT Julian day."""
    moment = _ensure_utc(moment)
    decimal_hour = (
        moment.hour
        + (moment.minute / 60.0)
        + (moment.second / 3600.0)
        + (moment.microsecond / 3_600_000_000.0)
    )
    return swe.julday(moment.year, moment.month, moment.day, decimal_hour)


def _datetime_from_julian_day(julian_day: float) -> datetime:
    """Converts a Swiss Ephemeris UT Julian day to an aware UTC datetime."""
    year, month, day, decimal_hour = swe.revjul(julian_day)
    hour = int(decimal_hour)
    minutes_float = (decimal_hour - hour) * 60.0
    minute = int(minutes_float)
    seconds_float = (minutes_float - minute) * 60.0
    second = int(seconds_float)
    microsecond = int(round((seconds_float - second) * 1_000_000))

    if microsecond >= 1_000_000:
        microsecond = 0
        second += 1

    base = datetime(year, month, day, hour, minute, 0, tzinfo=UTC)
    return base + timedelta(seconds=second, microseconds=microsecond)


def _add_year_window(start: datetime) -> datetime:
    """Returns the same calendar date one year later, with leap-day safety."""
    try:
        return start.replace(year=start.year + 1)
    except ValueError:
        # February 29 becomes February 28 in a non-leap following year.
        return start.replace(year=start.year + 1, month=2, day=28)


def _angle_difference(longitude_a: float, longitude_b: float) -> float:
    """Shortest angular distance between two ecliptic longitudes."""
    difference = abs((longitude_a - longitude_b) % 360)
    return min(difference, 360 - difference)


def _detect_aspect(
    transit_longitude: float,
    natal_longitude: float,
    maximum_orb: float,
) -> tuple[str | None, float | None]:
    """Returns the nearest in-orb major aspect and its orb."""
    distance = _angle_difference(transit_longitude, natal_longitude)

    matches: list[tuple[str, float]] = []
    for aspect_name, aspect_angle in ASPECT_ANGLES:
        orb = abs(distance - aspect_angle)
        if orb <= maximum_orb:
            matches.append((aspect_name, orb))

    if not matches:
        return None, None

    aspect_name, orb = min(matches, key=lambda item: item[1])
    return aspect_name, round(orb, 4)


def _planet_state(body_id: int, moment: datetime) -> dict:
    """Returns longitude, speed, and cazimi state for a transiting body."""
    jd = _julian_day(moment)
    coordinates, _flags = swe.calc_ut(jd, body_id, CALC_FLAGS)
    lon = float(coordinates[0] % 360)
    # Cazimi: transiting planet within 1° of transiting Sun
    cazimi = False
    if body_id != swe.SUN:
        sun_lon = float(swe.calc_ut(jd, swe.SUN, CALC_FLAGS)[0][0] % 360)
        sep = abs(lon - sun_lon)
        if sep > 180:
            sep = 360 - sep
        cazimi = sep <= 1.0
    return {
        "longitude": lon,
        "speed": float(coordinates[3]),
        "cazimi": cazimi,
    }


def _whole_sign_house(longitude: float, ascendant_longitude: float) -> int:
    """Returns Whole Sign house number for a transit longitude."""
    body_sign = int((longitude % 360) // 30)
    asc_sign = int((ascendant_longitude % 360) // 30)
    return ((body_sign - asc_sign) % 12) + 1


def _ordinal(number: int) -> str:
    """Formats ordinal house labels such as 1st, 2nd, 3rd, 4th."""
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _format_event_date(moment: datetime) -> str:
    """Consistent user-facing date format for report contexts."""
    return _ensure_utc(moment).strftime("%B %d, %Y")


def _duration_modifier(duration_days: float) -> float:
    """Duration weighting from the Year Ahead specification/config."""
    if duration_days > 90:
        return 1.35
    if duration_days > 42:
        return 1.15
    if duration_days > 14:
        return 1.00
    return 0.75


def _intensity_label(score: float) -> tuple[str, str]:
    """Returns the reader label and symbol for a normalized intensity score."""
    from config import INTENSITY_LEVELS
    for threshold, label, symbol in INTENSITY_LEVELS:
        if score >= threshold:
            return label, symbol
    return "Passing", "○"


# ── Transit Refinement Helpers ────────────────────────────────


def _compute_aspect_orb(
    body_id: int,
    natal_lon: float,
    aspect_angle: float,
    moment: datetime,
) -> float:
    """
    Returns the current angular distance from the exact aspect angle.

    A value of 0.0 means the transit is exactly on the aspect; positive values
    are the number of degrees away from perfection.  Uses the same
    _angle_difference() as the coarse scanner so geometry is consistent.
    """
    dist = _angle_difference(_planet_state(body_id, moment)["longitude"], natal_lon)
    return abs(dist - aspect_angle)


def _motion_direction_at(
    body_id: int,
    moment: datetime,
    stationary_threshold: float = 0.0005,
) -> str:
    """
    Returns 'direct', 'retrograde', or 'stationary' for a body at a moment.

    The stationary threshold (degrees/day) is intentionally tight — genuine
    stations are identified by scan_stations(); this is only used to label
    a contact that happens to fall near a station point.
    """
    speed = _planet_state(body_id, moment)["speed"]
    if abs(speed) < stationary_threshold:
        return "stationary"
    return "direct" if speed > 0 else "retrograde"


def _bisect_orb_boundary(
    body_id: int,
    natal_lon: float,
    aspect_angle: float,
    configured_orb: float,
    t_in: datetime,
    t_out: datetime,
) -> datetime:
    """
    Bisects to find the moment when orb equals configured_orb.

    Pre-conditions (verified by the caller):
      t_in  — moment where orb < configured_orb (inside the window)
      t_out — moment where orb > configured_orb (outside the window)

    Terminates when the angular residual < _REFINE_TOLERANCE or the time
    bracket shrinks below 60 seconds.  Returns the midpoint of the final
    bracket.
    """
    for _ in range(_BISECT_MAX_ITER):
        mid = t_in + (t_out - t_in) / 2
        mid_orb = _compute_aspect_orb(body_id, natal_lon, aspect_angle, mid)

        if abs(mid_orb - configured_orb) < _REFINE_TOLERANCE:
            return mid
        if (t_out - t_in).total_seconds() < 60:
            return mid

        if mid_orb < configured_orb:
            t_in = mid   # mid is inside orb; tighten lower bound
        else:
            t_out = mid  # mid is outside orb; tighten upper bound

    return t_in + (t_out - t_in) / 2


def _golden_section_minimum(
    body_id: int,
    natal_lon: float,
    aspect_angle: float,
    t_left: datetime,
    t_right: datetime,
) -> datetime:
    """
    Locates the minimum of the orb function in [t_left, t_right] using
    golden-section search.  Returns the datetime of closest approach.

    Terminates when the bracket is narrower than 60 seconds.
    """
    # golden-ratio conjugate
    phi = (5.0 ** 0.5 - 1.0) / 2.0

    a, b = t_left, t_right
    span_s = (b - a).total_seconds()
    c = a + timedelta(seconds=span_s * (1.0 - phi))
    d = a + timedelta(seconds=span_s * phi)

    for _ in range(_BISECT_MAX_ITER):
        if (b - a).total_seconds() < 60:
            break
        fc = _compute_aspect_orb(body_id, natal_lon, aspect_angle, c)
        fd = _compute_aspect_orb(body_id, natal_lon, aspect_angle, d)

        if fc < fd:
            b = d
        else:
            a = c

        span_s = (b - a).total_seconds()
        c = a + timedelta(seconds=span_s * (1.0 - phi))
        d = a + timedelta(seconds=span_s * phi)

    return a + (b - a) / 2


def _find_exact_contacts(
    body_id: int,
    natal_lon: float,
    aspect_angle: float,
    t_start: datetime,
    t_end: datetime,
    fine_step_hours: int = 6,
) -> list[dict]:
    """
    Finds all local orb minima (exact contacts) within [t_start, t_end].

    Each local minimum is refined with golden-section search.  The function
    records the motion direction at the refined contact datetime.

    A transit may have zero contacts (orb never reversed direction inside the
    window), one contact (simple direct pass), or multiple contacts (retrograde
    loop).  No contact is fabricated beyond what the ephemeris supports.
    """
    # Sample orb on a fine grid so retrograde reversals are not missed.
    samples: list[tuple[datetime, float]] = []
    t = t_start
    while t <= t_end:
        samples.append((t, _compute_aspect_orb(body_id, natal_lon, aspect_angle, t)))
        t += timedelta(hours=fine_step_hours)

    contacts: list[dict] = []

    if len(samples) < 3:
        # Window too short to detect a reversal; use the minimum sample.
        if samples:
            best_t, best_orb_val = min(samples, key=lambda s: s[1])
            contacts.append({
                "contact_datetime": best_t,
                "contact_date": _format_event_date(best_t),
                "motion_direction": _motion_direction_at(body_id, best_t),
                "sequence_index": 1,
                "contact_orb": round(best_orb_val, 4),
                "is_exact": best_orb_val <= _REFINE_TOLERANCE,
            })
        return contacts

    for i in range(1, len(samples) - 1):
        t_prev, orb_prev = samples[i - 1]
        t_curr, orb_curr = samples[i]
        t_next, orb_next = samples[i + 1]

        # Strict local minimum: both neighbours are larger.
        if orb_curr < orb_prev and orb_curr < orb_next:
            refined = _golden_section_minimum(
                body_id, natal_lon, aspect_angle, t_prev, t_next,
            )
            refined_orb = _compute_aspect_orb(body_id, natal_lon, aspect_angle, refined)
            contacts.append({
                "contact_datetime": refined,
                "contact_date": _format_event_date(refined),
                "motion_direction": _motion_direction_at(body_id, refined),
                "sequence_index": 0,  # filled in below
                "contact_orb": round(refined_orb, 4),
                "is_exact": refined_orb <= _REFINE_TOLERANCE,
            })

    # Edge case: minimum lies at the very start or end of the window.
    if not contacts:
        best_t, best_orb_val = min(samples, key=lambda s: s[1])
        contacts.append({
            "contact_datetime": best_t,
            "contact_date": _format_event_date(best_t),
            "motion_direction": _motion_direction_at(body_id, best_t),
            "sequence_index": 1,
            "contact_orb": round(best_orb_val, 4),
            "is_exact": best_orb_val <= _REFINE_TOLERANCE,
        })
    else:
        for idx, c in enumerate(contacts):
            c["sequence_index"] = idx + 1

    return contacts


def _refine_transit_window(
    body_id: int,
    transit_planet: str,
    natal_lon: float,
    aspect_angle: float,
    configured_orb: float,
    working: dict,
    active_at_start: bool,
    active_at_end: bool,
    step_hours: int = 12,
) -> dict:
    """
    Refines a single coarse transit window produced by the 12-hour scanner.

    Returns an updated copy of `working` with:
      - refined_entry / refined_exit  (replaced in-place as entry/last_active)
      - contacts list
      - peak_orb updated from the best refined contact
    """
    out = dict(working)
    entry  = working["entry"]
    exit_  = working["last_active"]

    # ── Refine entry boundary ──────────────────────────────────
    if not active_at_start:
        t_before = entry - timedelta(hours=step_hours)
        # Verify the pre-entry sample is genuinely out-of-orb before bisecting.
        orb_before = _compute_aspect_orb(body_id, natal_lon, aspect_angle, t_before)
        if orb_before > configured_orb:
            entry = _bisect_orb_boundary(
                body_id, natal_lon, aspect_angle, configured_orb,
                t_in=working["entry"], t_out=t_before,
            )
            out["entry"] = entry

    # ── Refine exit boundary ───────────────────────────────────
    if not active_at_end:
        t_after = exit_ + timedelta(hours=step_hours)
        orb_after = _compute_aspect_orb(body_id, natal_lon, aspect_angle, t_after)
        if orb_after > configured_orb:
            exit_ = _bisect_orb_boundary(
                body_id, natal_lon, aspect_angle, configured_orb,
                t_in=working["last_active"], t_out=t_after,
            )
            out["last_active"] = exit_

    # ── Detect exact contacts ──────────────────────────────────
    contacts = _find_exact_contacts(
        body_id, natal_lon, aspect_angle, entry, exit_,
    )
    out["contacts"] = contacts

    # Update peak_orb from the refined contacts.
    if contacts:
        best_orb = min(
            _compute_aspect_orb(body_id, natal_lon, aspect_angle, c["contact_datetime"])
            for c in contacts
        )
        out["peak_orb"] = best_orb
        out["peak"] = contacts[0]["contact_datetime"]  # first contact for sort anchor

    return out


# ── Transit Cycle Merger ───────────────────────────────────────


def _build_transit_cycle(
    windows: list[dict],
    report_start: datetime,
    report_end: datetime,
    activation_profile: dict | None = None,
) -> dict:
    """
    Consolidates one or more consecutive transit windows into a single cycle
    event.  The cycle carries:
      - all contacts from every window, re-sequenced
      - entry/exit spanning the full first-to-last orb bracket
      - a cycle_id deterministic on (planet, aspect, target, cycle_start_month)
      - display_anchor_datetime = first contact (or cycle start if no contacts)
      - score recomputed from best contact orb × full-cycle duration

    All existing fields from the primary window are preserved so downstream
    selectors and filters continue to work without modification.
    """
    primary = windows[0]
    planet = primary["transit_planet"]

    # Merge and re-sequence contacts.
    all_contacts: list[dict] = []
    for w in windows:
        all_contacts.extend(w.get("contacts", []))
    all_contacts.sort(key=lambda c: c["contact_datetime"])
    for idx, c in enumerate(all_contacts):
        c["sequence_index"] = idx + 1

    cycle_start = primary["entry"]
    last_window = windows[-1]
    cycle_end   = last_window["last_active"]   # None if active_at_end

    active_at_end = any(w.get("_active_at_end", False) for w in windows)

    # Full cycle duration for the score modifier.
    if cycle_end is not None:
        duration_days = max(
            0.5,
            (cycle_end - cycle_start).total_seconds() / 86_400.0,
        )
    else:
        duration_days = max(
            0.5,
            (report_end - cycle_start).total_seconds() / 86_400.0,
        )

    # Best (tightest) orb across all windows.
    best_orb = min(w["peak_orb"] for w in windows)

    # ── Two-concept scoring ───────────────────────────────────
    # concentration_score  — how intensely active is this transit at its
    #                        tightest point?  Drives reader-facing tier labels.
    #                        Pure function of planet weight × orb proximity.
    # structural_score     — how developmentally significant is this transit
    #                        over the forecast period?  Used for landmark
    #                        selection and year-overview block routing.
    #                        Applies the duration modifier to amplify sustained
    #                        themes without inflating the visible tier label.
    concentration_score = PLANET_SIGNIFICANCE[planet] * (1.0 - best_orb / primary["maximum_orb"])
    dur_mod             = _duration_modifier(duration_days)
    structural_score    = min(1.0, concentration_score * dur_mod)

    # combined_intensity_score is the public-facing score that drives tier
    # labels, monthly maps, and EAS index contributions.
    combined_score = concentration_score
    label, bar     = _intensity_label(combined_score)

    # Display anchor = first refined contact, else cycle start.
    anchor_dt = all_contacts[0]["contact_datetime"] if all_contacts else cycle_start

    cycle_id = (
        f"{planet}_{primary['aspect']}_{primary['target_name']}_"
        f"{cycle_start.strftime('%Y%m')}"
    )

    cycle_end_for_display = cycle_end if cycle_end is not None else None

    event = {
        "event_type":   "transit",
        "transit_planet": planet,
        "aspect":         primary["aspect"],
        "natal_target":   primary["target_name"],
        "natal_target_display": _target_display(primary["target_name"], primary["target"]),
        "natal_house":    primary["target"]["house"],
        "maximum_orb":    primary["maximum_orb"],
        "orb":            round(best_orb, 3),
        "raw_score":            round(concentration_score, 4),
        "concentration_score":  round(concentration_score, 4),
        "structural_score":     round(structural_score, 4),
        "combined_intensity_score": round(combined_score, 4),
        "score":                round(combined_score, 4),
        # Scoring debug fields (used by EO_SCORE_TRACE; not rendered to HTML).
        "_duration_days":       round(duration_days, 1),
        "_duration_modifier":   round(dur_mod, 4),
        "_best_orb":            round(best_orb, 4),
        "intensity_label": label,
        "intensity_bar":   bar,
        "aspect_character": ASPECT_CHARACTERS[primary["aspect"]],
        "priority":        "A" if planet != "Mars" else "B",
        # Cycle identity.
        "cycle_id":              cycle_id,
        "cycle_start_datetime":  cycle_start,
        "cycle_end_datetime":    cycle_end_for_display,
        "cycle_start_date":      _format_event_date(cycle_start),
        "cycle_end_date":        _format_event_date(cycle_end_for_display) if cycle_end_for_display else "",
        "contacts":              all_contacts,
        "contact_count":         len(all_contacts),
        "display_anchor_datetime": anchor_dt,
        "display_anchor_date":     _format_event_date(anchor_dt),
        # Compatibility fields — downstream code (scoring, filtering, display)
        # reads these keys; keep them aligned with the cycle anchor.
        "entry_datetime": cycle_start,
        "peak_datetime":  anchor_dt,
        "leave_datetime": cycle_end_for_display,
        "entry_date":     _format_event_date(cycle_start),
        "peak_date":      _format_event_date(anchor_dt),
        "leave_date":     _format_event_date(cycle_end_for_display) if cycle_end_for_display else "",
        "duration_days":  round(duration_days, 1),
        "active_at_report_start":      primary.get("_active_at_start", False),
        "active_at_report_end":        active_at_end,
        "in_orb_at_forecast_start":    primary.get("_active_at_start", False),
        "continues_after_forecast_end": active_at_end,
        "peak_month": (anchor_dt.year, anchor_dt.month),
        "_window_count": len(windows),
        "multiple_exact_passes": len(all_contacts) > 1,
    }
    if activation_profile:
        return enrich_forecast_event(event, activation_profile)
    return event


def _merge_into_transit_cycles(
    windows: list[dict],
    report_start: datetime,
    report_end: datetime,
    activation_profile: dict | None = None,
) -> list[dict]:
    """
    Groups the flat list of refined transit windows into cycles.

    Windows for the same (planet, aspect, target) separated by no more than
    _CYCLE_MERGE_GAP days are considered one retrograde cycle.  Windows with
    a larger gap are treated as independent activations.
    """
    if not windows:
        return []

    # Sort globally by entry then group.
    windows = sorted(windows, key=lambda w: w["entry"])

    groups: dict[tuple, list[dict]] = {}
    for w in windows:
        key = (w["transit_planet"], w["aspect"], w["target_name"])
        groups.setdefault(key, []).append(w)

    cycles: list[dict] = []
    for _key, group in groups.items():
        cluster: list[dict] = [group[0]]

        for w in group[1:]:
            prev_exit = cluster[-1]["last_active"]
            curr_entry = w["entry"]

            if prev_exit is None:
                # Previous window has no exit (continues beyond report end).
                cycles.append(_build_transit_cycle(cluster, report_start, report_end, activation_profile))
                cluster = [w]
                continue

            gap_days = (curr_entry - prev_exit).total_seconds() / 86_400.0
            if gap_days <= _CYCLE_MERGE_GAP:
                cluster.append(w)
            else:
                cycles.append(_build_transit_cycle(cluster, report_start, report_end, activation_profile))
                cluster = [w]

        cycles.append(_build_transit_cycle(cluster, report_start, report_end, activation_profile))

    cycles.sort(
        key=lambda c: (c["peak_datetime"], -c["combined_intensity_score"])
    )
    return cycles


# ── Natal Target Map ───────────────────────────────────────────


def _natal_targets(natal_payload: dict) -> dict[str, dict]:
    """Builds a normalized natal longitude/house map for forecast matching."""
    targets: dict[str, dict] = {}

    standard_planets = natal_payload.get("standard_planets", {})
    for name in [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    ]:
        data = standard_planets.get(name)
        if not isinstance(data, dict):
            continue
        longitude = data.get("longitude")
        if not isinstance(longitude, (int, float)):
            continue
        targets[name] = {
            "longitude": float(longitude),
            "house": int(data.get("house") or 0),
            "kind": "planet",
        }

    angles = natal_payload.get("angles", {})
    angle_map = {
        "ASC":    "Ascendant",
        "MC":     "Midheaven",
        "DSC":    "Descendant",
        "IC":     "Imum_Coeli",
        "Vertex": "Vertex",
    }

    for label, payload_key in angle_map.items():
        data = angles.get(payload_key)
        if not isinstance(data, dict):
            continue
        longitude = data.get("longitude")
        if not isinstance(longitude, (int, float)):
            continue
        # Vertex house is computed from its sign at chart time; the others
        # are fixed in Whole Sign (ASC=1, IC=4, DSC=7, MC=10).
        house = int(data.get("house") or 0) or ANGLE_HOUSES.get(label, 0)
        targets[label] = {
            "longitude": float(longitude),
            "house": house,
            "kind": "angle",
        }

    return targets


# ── Proprietary Forecast Target Map ───────────────────────────

PROPRIETARY_ASTEROID_TARGETS = [
    "Kassandra", "Aletheia", "Destinn", "Karma",
    "Kaali", "Medea", "Hermes", "Chaos",
]

def _proprietary_targets(natal_payload: dict) -> dict[str, dict]:
    """
    Extends the standard natal target map with asteroids required by the
    proprietary forecast formulas (Disruption & Revelation, Sovereignty
    Reclamation, Catalytic Encounter).

    Standard targets are included so callers can use this map exclusively
    without also calling _natal_targets().
    """
    targets = _natal_targets(natal_payload)

    custom = natal_payload.get("custom_asteroids", {})
    for name in PROPRIETARY_ASTEROID_TARGETS:
        data = custom.get(name)
        if not isinstance(data, dict):
            continue
        longitude = data.get("longitude")
        if not isinstance(longitude, (int, float)):
            continue
        targets[name] = {
            "longitude": float(longitude),
            "house": int(data.get("house") or 0),
            "kind": "asteroid",
        }

    return targets


# ── Proprietary Forecast Scanner ──────────────────────────────

# Weights for each formula's triggers. These are multipliers applied to
# the normalized orb score before the formula sums its total.
PROPRIETARY_FORMULA_CONFIG = {
    "DISRUPTION": {
        "label": "Disruption & Revelation",
        "triggers": [
            # (transiting_body_swe_id, transiting_name, natal_target, allowed_aspects, weight)
            (swe.URANUS,  "Uranus", "ASC",       ["Conjunction", "Square", "Opposition"], 3.0),
            (swe.URANUS,  "Uranus", "MC",        ["Conjunction", "Square", "Opposition"], 3.0),
            (19521,       "Chaos",  "Kassandra", ["Conjunction"],                         2.5),
            (69230,       "Hermes", "Kassandra", ["Conjunction"],                         2.5),
            (259,         "Aletheia", "Sun",     ["Conjunction", "Trine", "Square"],      2.0),
        ],
        "orb": 2.0,
    },
    "SOVEREIGNTY": {
        "label": "Sovereignty Reclamation",
        "triggers": [
            # BML is in standard_planets under "Lilith_BML"
            (swe.MEAN_APOG, "Lilith_BML", "ASC", ["Conjunction"], 4.0),
            (swe.MEAN_APOG, "Lilith_BML", "MC",  ["Conjunction"], 4.0),
            (swe.MEAN_APOG, "Lilith_BML", "DSC", ["Conjunction"], 4.0),
            (swe.MEAN_APOG, "Lilith_BML", "IC",  ["Conjunction"], 4.0),
            (212,           "Medea",  "Mars",     ["Conjunction", "Square", "Opposition"], 2.0),
            (4227,          "Kaali",  "Mars",     ["Conjunction", "Square", "Opposition"], 2.0),
        ],
        "orb": 1.5,
    },
    "CATALYST": {
        "label": "Catalytic Encounter",
        "triggers": [
            (6583,       "Destinn", "DSC",    ["Conjunction"],                         3.5),
            (3811,       "Karma",   "DSC",    ["Conjunction"],                         3.5),
            (swe.CHIRON, "Chiron",  "DSC",    ["Conjunction"],                         3.0),
            (swe.TRUE_NODE, "North_Node", "Destinn", ["Conjunction"],                  2.0),
        ],
        "orb": 1.5,
    },
}


def _proprietary_transit_state(body_id: int, moment: datetime) -> dict | None:
    """
    Returns longitude and speed for a proprietary transiting body.
    Returns None on ephemeris failure so a missing asteroid file
    doesn't crash the scanner.
    """
    try:
        coordinates, _flags = swe.calc_ut(_julian_day(moment), body_id, CALC_FLAGS)
        return {
            "longitude": float(coordinates[0] % 360),
            "speed": float(coordinates[3]),
        }
    except Exception:
        return None


def scan_proprietary_forecast_windows(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    step_hours: int = 12,
) -> dict[str, list[dict]]:
    """
    Scans the report window for proprietary forecast formula activations.

    Returns a dict keyed by formula name (DISRUPTION, SOVEREIGNTY, CATALYST),
    each containing a list of finalized event dicts matching the standard
    transit event contract so the report layer can handle them uniformly.

    Uses _proprietary_targets() so asteroid natal positions are visible
    alongside standard planets and angles.
    """
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else _add_year_window(report_start)

    targets = _proprietary_targets(natal_payload)
    if not targets:
        return {key: [] for key in PROPRIETARY_FORMULA_CONFIG}

    # open_events keyed by (formula_name, transiting_name, natal_target, aspect)
    open_events: dict[tuple, dict] = {}
    results: dict[str, list[dict]] = {key: [] for key in PROPRIETARY_FORMULA_CONFIG}

    moment = report_start

    while moment <= report_end:
        seen_keys: set[tuple] = set()

        for formula_name, config in PROPRIETARY_FORMULA_CONFIG.items():
            orb_limit = config["orb"]

            for (body_id, transiting_name, natal_target_name, allowed_aspects, weight) in config["triggers"]:

                state = _proprietary_transit_state(body_id, moment)
                if state is None:
                    continue

                target = targets.get(natal_target_name)
                if not target:
                    continue

                aspect, orb = _detect_aspect(
                    state["longitude"],
                    target["longitude"],
                    orb_limit,
                )

                if not aspect or orb is None:
                    continue
                if aspect not in allowed_aspects:
                    continue

                key = (formula_name, transiting_name, natal_target_name, aspect)
                seen_keys.add(key)

                if key not in open_events:
                    open_events[key] = {
                        "formula_name": formula_name,
                        "formula_label": config["label"],
                        "transit_planet": transiting_name,
                        "target_name": natal_target_name,
                        "target": target,
                        "aspect": aspect,
                        "weight": weight,
                        "orb_limit": orb_limit,
                        "entry": moment,
                        "last_active": moment,
                        "peak": moment,
                        "peak_orb": orb,
                    }
                else:
                    open_events[key]["last_active"] = moment
                    if orb < open_events[key]["peak_orb"]:
                        open_events[key]["peak_orb"] = orb
                        open_events[key]["peak"] = moment

        # Close events that dropped out of orb this step
        for key in list(open_events.keys()):
            if key not in seen_keys:
                event = open_events.pop(key)
                finalized = _finalize_proprietary_event(event, report_start, report_end, active_at_end=False)
                results[event["formula_name"]].append(finalized)

        moment += timedelta(hours=step_hours)

    # Close anything still open at the horizon
    for key, event in open_events.items():
        finalized = _finalize_proprietary_event(event, report_start, report_end, active_at_end=True)
        results[event["formula_name"]].append(finalized)

    # Sort each formula's events chronologically
    for formula_name in results:
        results[formula_name].sort(key=lambda e: e["peak_datetime"])

    return results


def _finalize_proprietary_event(
    working: dict,
    report_start: datetime,
    report_end: datetime,
    active_at_end: bool,
) -> dict:
    """Converts an open proprietary transit window into a finalized event dict."""
    duration_days = max(
        0.5,
        (working["last_active"] - working["entry"]).total_seconds() / 86_400.0,
    )
    # Weighted orb score: tighter orb = higher base, then scaled by trigger weight
    base_score = (1.0 - working["peak_orb"] / working["orb_limit"]) * working["weight"]
    combined_score = min(1.0, base_score * _duration_modifier(duration_days))
    label, bar = _intensity_label(combined_score)
    peak_date = working["peak"]

    return {
        "event_type": "proprietary_transit",
        "formula_name": working["formula_name"],
        "formula_label": working["formula_label"],
        "transit_planet": working["transit_planet"],
        "aspect": working["aspect"],
        "natal_target": working["target_name"],
        "natal_target_display": _target_display(working["target_name"], working["target"]),
        "natal_house": working["target"]["house"],
        "orb": round(working["peak_orb"], 3),
        "weight": working["weight"],
        "raw_score": round(base_score, 4),
        "combined_intensity_score": round(combined_score, 4),
        "score": round(combined_score, 4),
        "intensity_label": label,
        "intensity_bar": bar,
        "aspect_character": ASPECT_CHARACTERS.get(working["aspect"], "neutral"),
        "entry_datetime": working["entry"],
        "peak_datetime": peak_date,
        "leave_datetime": working["last_active"],
        "entry_date": _format_event_date(working["entry"]),
        "peak_date": _format_event_date(peak_date),
        "leave_date": _format_event_date(working["last_active"]),
        "duration_days": round(duration_days, 1),
        "active_at_report_start": working["entry"] <= report_start,
        "active_at_report_end": active_at_end,
        "peak_month": (peak_date.year, peak_date.month),
    }


def _target_display(target_name: str, target_data: dict) -> str:
    """Creates the report-friendly natal target label."""
    if target_name == "ASC":
        return "your Ascendant"
    if target_name == "MC":
        return "your Midheaven"
    if target_name == "DSC":
        return "your Descendant"
    if target_name == "IC":
        return "your Imum Coeli"
    if target_name == "Vertex":
        return "your Vertex"

    house = int(target_data.get("house") or 0)
    if house:
        return f"your {target_name} in the {_ordinal(house)} house"
    return f"your {target_name}"


# ── Current Snapshot Compatibility ─────────────────────────────


def compute_current_transits(
    natal_payload: dict,
    as_of_date: datetime | None = None,
) -> list[dict]:
    """
    Returns current active transit cards for the legacy template.

    This function is deliberately retained so the current report continues to
    run during the Year Ahead template migration.
    """
    moment = _ensure_utc(as_of_date)
    targets = _natal_targets(natal_payload)
    transits: list[dict] = []

    for body_id, transit_planet in TRANSIT_PLANETS.items():
        state = _planet_state(body_id, moment)
        maximum_orb = TRANSIT_ORB[transit_planet]
        target_names = MARS_TARGETS if transit_planet == "Mars" else STANDARD_TARGETS

        for target_name in target_names:
            target = targets.get(target_name)
            if not target:
                continue

            aspect, orb = _detect_aspect(
                state["longitude"],
                target["longitude"],
                maximum_orb,
            )
            if not aspect or orb is None:
                continue

            score = PLANET_SIGNIFICANCE[transit_planet] * (1.0 - orb / maximum_orb)
            label, bar = _intensity_label(score)

            transits.append({
                "event_type": "transit",
                "transit_planet": transit_planet,
                "aspect": aspect,
                "natal_target": target_name,
                "natal_target_display": _target_display(target_name, target),
                "natal_house": target["house"],
                "orb": round(orb, 3),
                "score": round(score, 4),
                "raw_score": round(score, 4),
                "combined_intensity_score": round(score, 4),
                "intensity_label": label,
                "intensity_bar": bar,
                "aspect_character": ASPECT_CHARACTERS[aspect],
                "priority": "A" if transit_planet != "Mars" else "B",
            })

    transits.sort(key=lambda event: event["score"], reverse=True)
    return transits


def compute_daily_activation_transits(
    natal_payload: dict,
    as_of_date: datetime | None = None,
    include_angles: bool = True,
) -> list[dict]:
    """
    Same-day transit-to-natal-point scan across all planets but the Moon
    (which has its own always-available house-based fallback rather than
    an orb-gated aspect check).

    Sibling of compute_current_transits() above, but scoped and orbed for
    Daily Horoscope's "today's activation" selection rather than Year
    Ahead's week/month-scale forecasting. See DAILY_ACTIVATION_ORB for
    why the orbs are tight and graduated by planet speed rather than
    reusing TRANSIT_ORB.

    include_angles=False excludes Ascendant/Midheaven/Vertex from the
    natal target pool — those depend on exact birth time. Pass False when
    the querent's birth time isn't exact; this narrows the target pool,
    it does not turn the function off (Sun through Pluto stay eligible).
    """
    moment = _ensure_utc(as_of_date)
    targets = _natal_targets(natal_payload)
    target_names = [
        name for name in STANDARD_TARGETS
        if include_angles or targets.get(name, {}).get("kind") != "angle"
    ]
    transits: list[dict] = []

    for body_id, transit_planet in DAILY_ACTIVATION_PLANETS.items():
        state = _planet_state(body_id, moment)
        maximum_orb = DAILY_ACTIVATION_ORB[transit_planet]

        for target_name in target_names:
            target = targets.get(target_name)
            if not target:
                continue

            aspect, orb = _detect_aspect(
                state["longitude"],
                target["longitude"],
                maximum_orb,
            )
            if not aspect or orb is None:
                continue

            score = DAILY_ACTIVATION_SIGNIFICANCE[transit_planet] * (1.0 - orb / maximum_orb)
            label, bar = _intensity_label(score)

            transits.append({
                "event_type": "transit",
                "transit_planet": transit_planet,
                "aspect": aspect,
                "natal_target": target_name,
                "natal_target_display": _target_display(target_name, target),
                "natal_house": target["house"],
                "orb": round(orb, 3),
                "score": round(score, 4),
                "raw_score": round(score, 4),
                "combined_intensity_score": round(score, 4),
                "intensity_label": label,
                "intensity_bar": bar,
                "aspect_character": ASPECT_CHARACTERS[aspect],
                "priority": "C",
            })

    transits.sort(key=lambda event: event["score"], reverse=True)
    return transits


#: Moon moves fast enough (~13 degrees/day) to fully approach and
#: separate from an aspect within a single day, so it can have a
#: genuine "peaks at this hour" moment. Nothing else in
#: DAILY_ACTIVATION_PLANETS can, in general — see compute_daily_timeline()'s
#: docstring for the empirical evidence. Orb follows the same
#: standard-convention reasoning as DAILY_ACTIVATION_ORB (roughly 1-2
#: degrees for personal-planet-speed transits read at daily granularity).
MOON_TIMELINE_ORB = 2.0
MOON_TIMELINE_SIGNIFICANCE = 0.55

#: Separate from the shared ASPECT_ANGLES (5 majors, used by Year Ahead's
#: week/month-scale scanning) on purpose — widening orb alone did not
#: increase how many genuine daily peaks the Moon scan found (tested
#: 2.0 through 4.5 degrees, identical results every time), because the
#: real constraint was how many fixed aspect points exist to cross, not
#: how close counts as "close enough." Adding the three hard minor
#: aspects closed that gap empirically: a 14-day sweep went from
#: averaging 2.6 genuine peaks/day (7/14 days short of even 3) to 5.0/day
#: (0/14 days short of 3). Kept Moon-scan-only rather than added to the
#: shared ASPECT_ANGLES so Year Ahead's major-aspect-only scanning is
#: unaffected.
TIMELINE_ASPECT_ANGLES = ASPECT_ANGLES + [
    ("Semisquare", 45),
    ("Sesquiquadrate", 135),
    ("Quincunx", 150),
]

TIMELINE_ASPECT_CHARACTERS = {
    **ASPECT_CHARACTERS,
    "Semisquare": "challenging",
    "Sesquiquadrate": "challenging",
    "Quincunx": "challenging",
}

#: A refined contact landing within this many minutes of the scan
#: window's start or end is almost certainly a boundary-fallback
#: artifact from _find_exact_contacts() (no true interior local minimum
#: existed inside the window), not a genuine peak. See
#: compute_daily_timeline()'s docstring.
_BOUNDARY_ARTIFACT_TOLERANCE_MINUTES = 5


def _is_boundary_artifact(contact_datetime: datetime, day_start: datetime, day_end: datetime) -> bool:
    tolerance = timedelta(minutes=_BOUNDARY_ARTIFACT_TOLERANCE_MINUTES)
    return (
        abs(contact_datetime - day_start) <= tolerance
        or abs(contact_datetime - day_end) <= tolerance
    )


def compute_daily_timeline(
    natal_payload: dict,
    day_start: datetime,
    day_end: datetime,
    count: int = 3,
    include_angles: bool = True,
    include_slow_planet_peaks: bool = True,
) -> list[dict]:
    """
    Finds the top `count` dated moments within [day_start, day_end] for a
    "today's timeline" feature — genuinely timed events, not a same-day
    snapshot of what's broadly in orb.

    Primary source is the Moon against every natal target: the Moon is
    the only body in DAILY_ACTIVATION_PLANETS fast enough to fully
    approach and separate from an aspect inside a single day, so it's
    the only one that reliably produces a real interior peak rather than
    a boundary artifact. This was verified directly during development:
    even at 1-hour sampling, a Sun-square-natal-Mercury check returned
    its "peak" sitting exactly on the scan window's boundary (an orb
    that was simply drifting all day, never turning), while a same-day
    Moon-square-natal-Moon check returned a genuine interior peak at
    12:24:52 UTC. _is_boundary_artifact() filters out the former case
    for every body scanned here, Moon included.

    include_slow_planet_peaks=True also checks the slower
    DAILY_ACTIVATION_PLANETS bodies (Sun through Pluto) for the rare day
    they do have a genuine interior peak, so those aren't structurally
    excluded — just not relied on, since most days they won't have one.

    include_angles=False excludes Ascendant/Midheaven/Vertex from the
    natal target pool, matching compute_daily_activation_transits().
    Time-of-day labeling (band or clock time) is left to the caller —
    this function only returns UTC datetimes.

    Void-of-course windows and stations are NOT computed here — they're
    already their own genuinely-timed scanners (detect_void_of_course_windows,
    scan_stations) with their own authored content. Merge their results
    into this function's output at the call site rather than duplicating
    that scanning here.
    """
    day_start = _ensure_utc(day_start)
    day_end = _ensure_utc(day_end)
    targets = _natal_targets(natal_payload)
    target_names = [
        name for name in STANDARD_TARGETS
        if include_angles or targets.get(name, {}).get("kind") != "angle"
    ]

    def _scan_body(body_id, transit_planet, maximum_orb, significance):
        found = []
        for target_name in target_names:
            target = targets.get(target_name)
            if not target:
                continue

            for aspect_name, aspect_angle in TIMELINE_ASPECT_ANGLES:
                contacts = _find_exact_contacts(
                    body_id, target["longitude"], aspect_angle, day_start, day_end,
                )
                for contact in contacts:
                    if contact["contact_orb"] > maximum_orb:
                        continue
                    if _is_boundary_artifact(contact["contact_datetime"], day_start, day_end):
                        continue

                    score = significance * (1.0 - contact["contact_orb"] / maximum_orb)
                    found.append({
                        "event_type": "timeline",
                        "transit_planet": transit_planet,
                        "aspect": aspect_name,
                        "aspect_character": TIMELINE_ASPECT_CHARACTERS[aspect_name],
                        "natal_target": target_name,
                        "natal_target_display": _target_display(target_name, target),
                        "natal_house": target["house"],
                        "peak_datetime": contact["contact_datetime"],
                        "orb": round(contact["contact_orb"], 3),
                        "score": round(score, 4),
                    })
        return found

    candidates = _scan_body(swe.MOON, "Moon", MOON_TIMELINE_ORB, MOON_TIMELINE_SIGNIFICANCE)

    if include_slow_planet_peaks:
        for body_id, transit_planet in DAILY_ACTIVATION_PLANETS.items():
            candidates += _scan_body(
                body_id,
                transit_planet,
                DAILY_ACTIVATION_ORB[transit_planet],
                DAILY_ACTIVATION_SIGNIFICANCE[transit_planet],
            )

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:count]


# ── Forecast Transit Scanner ───────────────────────────────────


def _finalize_transit_event(
    working: dict,
    report_start: datetime,
    report_end: datetime,
    active_at_end: bool,
) -> dict:
    """Converts a sampled in-orb transit window to a report event."""
    duration_days = max(
        0.5,
        (working["last_active"] - working["entry"]).total_seconds() / 86_400.0,
    )
    base_score = PLANET_SIGNIFICANCE[working["transit_planet"]] * (
        1.0 - working["peak_orb"] / working["maximum_orb"]
    )
    combined_score = min(1.0, base_score * _duration_modifier(duration_days))
    label, bar = _intensity_label(combined_score)

    target = working["target"]
    peak_date = working["peak"]

    return {
        "event_type": "transit",
        "transit_planet": working["transit_planet"],
        "aspect": working["aspect"],
        "natal_target": working["target_name"],
        "natal_target_display": _target_display(working["target_name"], target),
        "natal_house": target["house"],
        "orb": round(working["peak_orb"], 3),
        "maximum_orb": working["maximum_orb"],
        "raw_score": round(base_score, 4),
        "combined_intensity_score": round(combined_score, 4),
        "score": round(combined_score, 4),
        "intensity_label": label,
        "intensity_bar": bar,
        "aspect_character": ASPECT_CHARACTERS[working["aspect"]],
        "priority": "A" if working["transit_planet"] != "Mars" else "B",
        "entry_datetime": working["entry"],
        "peak_datetime": peak_date,
        "leave_datetime": working["last_active"],
        "entry_date": _format_event_date(working["entry"]),
        "peak_date": _format_event_date(peak_date),
        "leave_date": _format_event_date(working["last_active"]),
        "duration_days": round(duration_days, 1),
        "active_at_report_start": working["entry"] <= report_start,
        "active_at_report_end": active_at_end,
        # Semantic aliases used by the display layer — clearer than the raw flags above.
        "in_orb_at_forecast_start": working["entry"] <= report_start,
        "continues_after_forecast_end": active_at_end,
        # Whether the transit reached a true exact aspect or only a closest approach.
        # Threshold of 0.25° reflects the ~12-hour sampling grid's resolution for
        # the slowest outer planets; refine if the scanner step is ever tightened.
        "perfection_type": "exact" if working["peak_orb"] < 0.25 else "closest_approach",
        "peak_month": (peak_date.year, peak_date.month),
    }


def scan_transit_windows(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    step_hours: int = 12,
    activation_profile: dict | None = None,
) -> list[dict]:
    """
    Scans the report window for natal transit cycles.

    Phase 1 — Coarse scan (12-hour grid):
        Locates candidate orb-entry and orb-exit brackets for every
        (transit_planet, natal_target, aspect) combination.

    Phase 2 — Refinement:
        For each candidate window, bisects the entry and exit boundaries
        to _REFINE_TOLERANCE precision, then runs golden-section search
        inside the window to locate every exact contact (local orb minimum).

    Phase 3 — Cycle merging:
        Consecutive windows of the same (planet, aspect, target) separated
        by ≤ _CYCLE_MERGE_GAP days are merged into one transit cycle event.
        The cycle carries all contacts from every constituent window.

    Scoring uses the tightest contact orb and the full cycle duration so
    that multi-pass retrograde events score appropriately.
    """
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else _add_year_window(report_start)

    if report_end <= report_start:
        raise ValueError("end_date must be later than start_date")
    if step_hours <= 0:
        raise ValueError("step_hours must be greater than zero")

    targets = _natal_targets(natal_payload)
    if not targets:
        return []

    # Build a map from (transit_planet, natal_target, aspect) → body_id so
    # the refinement layer can call _planet_state() without an extra lookup.
    planet_body_ids: dict[str, int] = {v: k for k, v in TRANSIT_PLANETS.items()}

    open_events: dict[tuple[str, str, str], dict] = {}
    raw_windows: list[dict] = []

    moment = report_start

    while moment <= report_end:
        seen_keys: set[tuple[str, str, str]] = set()

        for body_id, transit_planet in TRANSIT_PLANETS.items():
            state = _planet_state(body_id, moment)
            maximum_orb = TRANSIT_ORB[transit_planet]
            target_names = MARS_TARGETS if transit_planet == "Mars" else STANDARD_TARGETS

            for target_name in target_names:
                target = targets.get(target_name)
                if not target:
                    continue

                aspect, orb = _detect_aspect(
                    state["longitude"],
                    target["longitude"],
                    maximum_orb,
                )

                if not aspect or orb is None:
                    continue

                key = (transit_planet, target_name, aspect)
                seen_keys.add(key)

                if key not in open_events:
                    open_events[key] = {
                        "transit_planet": transit_planet,
                        "target_name":    target_name,
                        "target":         target,
                        "aspect":         aspect,
                        "maximum_orb":    maximum_orb,
                        "entry":          moment,
                        "last_active":    moment,
                        "peak":           moment,
                        "peak_orb":       orb,
                        "_body_id":       body_id,
                    }
                else:
                    open_events[key]["last_active"] = moment
                    if orb < open_events[key]["peak_orb"]:
                        open_events[key]["peak_orb"] = orb
                        open_events[key]["peak"]     = moment

        for key in list(open_events.keys()):
            if key not in seen_keys:
                w = open_events.pop(key)
                w["_active_at_start"] = w["entry"] <= report_start
                w["_active_at_end"]   = False
                raw_windows.append(w)

        moment += timedelta(hours=step_hours)

    for w in open_events.values():
        w["_active_at_start"] = w["entry"] <= report_start
        w["_active_at_end"]   = True
        raw_windows.append(w)

    # ── Phase 2: refine each coarse window ────────────────────
    aspect_angle_map: dict[str, float] = dict(ASPECT_ANGLES)
    refined_windows: list[dict] = []

    for w in raw_windows:
        body_id      = w["_body_id"]
        natal_lon    = w["target"]["longitude"]
        asp_angle    = aspect_angle_map.get(w["aspect"], 0.0)
        configured   = w["maximum_orb"]
        active_start = w["_active_at_start"]
        active_end   = w["_active_at_end"]

        refined = _refine_transit_window(
            body_id, w["transit_planet"], natal_lon, asp_angle,
            configured, w, active_start, active_end, step_hours,
        )
        refined_windows.append(refined)

    # ── Phase 3: merge windows into cycles ────────────────────
    activation_profile = activation_profile or build_forecast_activation_profile(natal_payload)
    return _merge_into_transit_cycles(refined_windows, report_start, report_end, activation_profile)


# ── Whole Sign House Ingress Scanner ───────────────────────────


def scan_house_ingresses(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    step_hours: int = 12,
    activation_profile: dict | None = None,
) -> list[dict]:
    """Finds Jupiter-through-Pluto Whole Sign house ingresses."""
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else _add_year_window(report_start)

    ascendant = natal_payload.get("angles", {}).get("Ascendant", {})
    asc_longitude = ascendant.get("longitude") if isinstance(ascendant, dict) else None
    if not isinstance(asc_longitude, (int, float)):
        return []

    activation_profile = activation_profile or build_forecast_activation_profile(natal_payload)
    events: list[dict] = []

    for body_id, transit_planet in INGRESS_PLANETS.items():
        previous_moment = report_start
        previous_state = _planet_state(body_id, previous_moment)
        previous_house = _whole_sign_house(previous_state["longitude"], asc_longitude)

        moment = report_start + timedelta(hours=step_hours)
        while moment <= report_end:
            state = _planet_state(body_id, moment)
            current_house = _whole_sign_house(state["longitude"], asc_longitude)

            if current_house != previous_house:
                # Calendar-day precision is sufficient for this version.
                score = min(1.0, PLANET_SIGNIFICANCE[transit_planet] * 0.72)
                label, bar = _intensity_label(score)
                house_data = natal_payload.get("houses", {}).get(f"House_{current_house}", {})
                previous_house_data = natal_payload.get("houses", {}).get(f"House_{previous_house}", {})
                event = {
                    "event_type": "ingress",
                    "transit_planet": transit_planet,
                    "house_number": current_house,
                    "house_ordinal": _ordinal(current_house),
                    "previous_house_number": previous_house,
                    "whole_sign_house": current_house,
                    "entered_house_sign": str(house_data.get("sign") or ""),
                    "previous_house_sign": str(previous_house_data.get("sign") or ""),
                    "entry_datetime": moment,
                    "peak_datetime": moment,
                    "leave_datetime": None,
                    "entry_date": _format_event_date(moment),
                    "peak_date": _format_event_date(moment),
                    "leave_date": "",
                    "duration_days": 0.0,
                    "raw_score": round(score, 4),
                    "combined_intensity_score": round(score, 4),
                    "score": round(score, 4),
                    "intensity_label": label,
                    "intensity_bar": bar,
                    "priority": "A",
                    "peak_month": (moment.year, moment.month),
                }
                events.append(enrich_forecast_event(event, activation_profile))

            previous_moment = moment
            previous_house = current_house
            moment += timedelta(hours=step_hours)

    events.sort(key=lambda event: event["peak_datetime"])
    return events


# ── Station Scanner ────────────────────────────────────────────


def _station_datetime(
    body_id: int,
    earlier: datetime,
    later: datetime,
) -> datetime:
    """Uses bisection to locate the speed-zero station time inside a sample interval."""
    low = earlier
    high = later
    low_speed = _planet_state(body_id, low)["speed"]

    for _ in range(18):
        midpoint = low + (high - low) / 2
        midpoint_speed = _planet_state(body_id, midpoint)["speed"]

        if (low_speed >= 0 and midpoint_speed >= 0) or (
            low_speed < 0 and midpoint_speed < 0
        ):
            low = midpoint
            low_speed = midpoint_speed
        else:
            high = midpoint

    return low + (high - low) / 2


def scan_stations(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    step_hours: int = 12,
    activation_profile: dict | None = None,
) -> list[dict]:
    """Finds planetary direct/retrograde stations relevant to the report window."""
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else _add_year_window(report_start)
    targets = _natal_targets(natal_payload)
    activation_profile = activation_profile or build_forecast_activation_profile(natal_payload)

    events: list[dict] = []

    for body_id, transit_planet in STATION_PLANETS.items():
        earlier = report_start
        earlier_state = _planet_state(body_id, earlier)
        earlier_speed = earlier_state["speed"]

        later = earlier + timedelta(hours=step_hours)
        while later <= report_end:
            later_state = _planet_state(body_id, later)
            later_speed = later_state["speed"]

            crosses_station = (
                (earlier_speed > 0 and later_speed <= 0)
                or (earlier_speed < 0 and later_speed >= 0)
            )

            if crosses_station:
                station_datetime = _station_datetime(body_id, earlier, later)
                station_state = _planet_state(body_id, station_datetime)
                station_type = "Retrograde" if earlier_speed > 0 else "Direct"

                nearest_name = ""
                nearest_target: dict | None = None
                nearest_distance = 999.0
                for target_name, target in targets.items():
                    distance = _angle_difference(
                        station_state["longitude"],
                        target["longitude"],
                    )
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_name = target_name
                        nearest_target = target

                # Stations with immediate natal contact are meaningful. The
                # product spec additionally keeps Mars retrograde and Venus
                # retrograde even without a natal hit.
                include = nearest_distance <= 5.0
                if station_type == "Retrograde" and transit_planet in {"Mars", "Venus"}:
                    include = True
                if transit_planet == "Mercury":
                    include = nearest_distance <= 5.0

                if include:
                    base = PLANET_SIGNIFICANCE.get(transit_planet, 0.45)
                    proximity = max(0.0, 1.0 - min(nearest_distance, 5.0) / 5.0)
                    score = min(1.0, 0.30 + (base * 0.45) + (proximity * 0.25))
                    label, bar = _intensity_label(score)
                    event = {
                        "event_type": "station",
                        "transit_planet": transit_planet,
                        "station_type": station_type,
                        "natal_target": nearest_name if nearest_target else "",
                        "natal_target_display": (
                            _target_display(nearest_name, nearest_target)
                            if nearest_target else ""
                        ),
                        "natal_house": nearest_target.get("house", 0) if nearest_target else 0,
                        "distance_to_natal_target": round(nearest_distance, 3),
                        "entry_datetime": station_datetime,
                        "peak_datetime": station_datetime,
                        "leave_datetime": None,
                        "entry_date": _format_event_date(station_datetime),
                        "peak_date": _format_event_date(station_datetime),
                        "leave_date": "",
                        "duration_days": 0.0,
                        "raw_score": round(score, 4),
                        "combined_intensity_score": round(score, 4),
                        "score": round(score, 4),
                        "intensity_label": label,
                        "intensity_bar": bar,
                        "priority": "A" if nearest_distance <= 2.0 else "B",
                        "peak_month": (station_datetime.year, station_datetime.month),
                    }
                    events.append(enrich_forecast_event(event, activation_profile))

            earlier = later
            earlier_speed = later_speed
            later += timedelta(hours=step_hours)

    events.sort(key=lambda event: event["peak_datetime"])
    return events


# ── Retrograde Cluster Detection ────────────────────────────────
#
# Independent of scan_stations() above, which only reports the moment a
# planet turns and filters to natal significance. This instead samples each
# STATION_PLANETS body's retrograde status directly across the window to
# find stretches where two or more are simultaneously retrograde —
# regardless of whether any individual station has natal contact.


def current_retrograde_planets(moment: datetime | None = None) -> set:
    """
    Returns the set of STATION_PLANETS names retrograde by transit at a
    single moment (default: now). A lighter-weight sibling of
    detect_retrograde_clusters() for callers that just need a snapshot
    (e.g. flagging a natal chart wheel with which placements a current
    transit retrograde touches) rather than a scan across a date range.
    """
    check_moment = _ensure_utc(moment)
    return {
        name for body_id, name in STATION_PLANETS.items()
        if _planet_state(body_id, check_moment)["speed"] < 0
    }


def detect_retrograde_clusters(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    step_hours: int = 24,
) -> list[dict]:
    """
    Finds stretches within [start_date, end_date] where two or more
    STATION_PLANETS bodies are simultaneously retrograde.

    Returns a list of cluster windows, each:
        {"start": datetime, "end": datetime, "planets": [str, ...], "tier": str}
    "tier" is "two_retrograde" when exactly two planets peak together, or
    "three_plus_retrograde" when three or more do. "planets" lists the
    bodies retrograde at that peak moment (not the union across the whole
    window, since membership can shift while the count stays >= 2).

    A cluster already under way at start_date, or still active at end_date,
    is reported clipped to the report boundary rather than its true
    astronomical start/end.
    """
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else report_start + timedelta(days=90)

    samples: list[tuple[datetime, set]] = []
    cursor = report_start
    while cursor <= report_end:
        retrograde_planets = {
            name for body_id, name in STATION_PLANETS.items()
            if _planet_state(body_id, cursor)["speed"] < 0
        }
        samples.append((cursor, retrograde_planets))
        cursor += timedelta(hours=step_hours)

    clusters: list[dict] = []
    active_start: datetime | None = None
    peak_count = 0
    peak_planets: set = set()

    def _flush(end_moment: datetime) -> None:
        nonlocal active_start, peak_count, peak_planets
        if active_start is not None and peak_count >= 2:
            tier = "two_retrograde" if peak_count == 2 else "three_plus_retrograde"
            clusters.append({
                "start": active_start,
                "end": end_moment,
                "planets": sorted(peak_planets),
                "tier": tier,
            })
        active_start = None
        peak_count = 0
        peak_planets = set()

    for moment, planets in samples:
        if len(planets) >= 2:
            if active_start is None:
                active_start = moment
            if len(planets) > peak_count:
                peak_count = len(planets)
                peak_planets = set(planets)
        else:
            _flush(moment)

    _flush(report_end)

    return clusters


# ── Void-of-Course Moon Detection ───────────────────────────────
#
# Purely transit-based, independent of any natal payload. Uses the
# traditional/mainstream Void-of-Course definition: the Moon is void from
# the moment of its last major aspect to one of the seven classical bodies
# (Sun through Saturn) until it enters its next zodiac sign. Modern
# variants that also count the outer planets exist, but this matches
# standard published Void-of-Course convention.

VOC_ASPECT_BODIES = {
    swe.SUN: "Sun",
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
}

VOC_EXTENDED_THRESHOLD_HOURS = 6.0


def _voc_signed_orbs(moment: datetime) -> dict:
    """Signed angular distance from exactness, for the Moon against each
    classical body/aspect-angle pair. Sign changes between two samples mean
    an aspect perfected somewhere in that interval."""
    moon_longitude = _planet_state(swe.MOON, moment)["longitude"]
    orbs = {}
    for body_id, name in VOC_ASPECT_BODIES.items():
        body_longitude = _planet_state(body_id, moment)["longitude"]
        for aspect_name, aspect_angle in ASPECT_ANGLES:
            orbs[(name, aspect_name)] = (
                (moon_longitude - body_longitude - aspect_angle + 180) % 360
            ) - 180
    return orbs


def detect_void_of_course_windows(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    step_hours: float = 1.0,
) -> list[dict]:
    """
    Finds Void-of-Course Moon windows within [start_date, end_date].

    Returns a list of windows, each:
        {"start": datetime, "end": datetime, "duration_hours": float, "tier": str}
    "start" is the Moon's last exact classical aspect before it changes
    sign (or the report's start boundary, if the Moon was already void when
    scanning began). "end" is the sign-ingress moment. "tier" is
    "extended_void" when the window is 6+ hours or crosses a calendar day,
    otherwise "brief_void" — matching the published editorial thresholds
    for this content set.

    A window already under way at start_date, or still open at end_date, is
    reported clipped to that report boundary rather than its true
    astronomical start/end.
    """
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else report_start + timedelta(days=90)

    windows: list[dict] = []
    cursor = report_start
    previous_moon_sign = int(_planet_state(swe.MOON, cursor)["longitude"] // 30)
    previous_orbs = _voc_signed_orbs(cursor)
    last_exact_aspect: datetime | None = None
    sign_entry_time = report_start

    def _record_window(void_start: datetime, void_end: datetime) -> None:
        duration_hours = (void_end - void_start).total_seconds() / 3600.0
        if duration_hours <= 0:
            return
        crosses_day = void_start.date() != void_end.date()
        tier = (
            "extended_void"
            if (duration_hours >= VOC_EXTENDED_THRESHOLD_HOURS or crosses_day)
            else "brief_void"
        )
        windows.append({
            "start": void_start,
            "end": void_end,
            "duration_hours": round(duration_hours, 2),
            "tier": tier,
        })

    while cursor < report_end:
        next_moment = min(cursor + timedelta(hours=step_hours), report_end)
        current_sign = int(_planet_state(swe.MOON, next_moment)["longitude"] // 30)
        current_orbs = _voc_signed_orbs(next_moment)

        if any(
            (prev_value == 0 or (prev_value > 0) != (current_orbs[key] > 0))
            for key, prev_value in previous_orbs.items()
        ):
            last_exact_aspect = next_moment

        if current_sign != previous_moon_sign:
            _record_window(last_exact_aspect or sign_entry_time, next_moment)
            previous_moon_sign = current_sign
            last_exact_aspect = None
            sign_entry_time = next_moment

        previous_orbs = current_orbs
        cursor = next_moment

    if last_exact_aspect is not None:
        _record_window(last_exact_aspect, report_end)

    return windows


# ── Eclipse Scanner ────────────────────────────────────────────


def _eclipse_events_of_type(
    eclipse_type: str,
    start_julian_day: float,
    end_julian_day: float,
) -> list[tuple[datetime, float]]:
    """Returns (maximum UTC datetime, eclipse longitude) pairs in the report window."""
    events: list[tuple[datetime, float]] = []
    cursor = start_julian_day - 1.0

    while True:
        if eclipse_type == "Solar":
            _flags, times = swe.sol_eclipse_when_glob(cursor, CALC_FLAGS)
            body_id = swe.SUN
        else:
            _flags, times = swe.lun_eclipse_when(cursor, CALC_FLAGS)
            body_id = swe.MOON

        maximum_jd = times[0]
        if maximum_jd > end_julian_day:
            break

        maximum_datetime = _datetime_from_julian_day(maximum_jd)
        coordinates, _calc_flags = swe.calc_ut(maximum_jd, body_id, CALC_FLAGS)
        events.append((maximum_datetime, float(coordinates[0] % 360)))

        # Move beyond this eclipse before asking Swiss Ephemeris for the next.
        cursor = maximum_jd + 1.0

    return events


def scan_eclipses(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    activation_profile: dict | None = None,
) -> list[dict]:
    """Finds solar/lunar eclipses and records closer natal contacts when present."""
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else _add_year_window(report_start)
    targets = _natal_targets(natal_payload)
    activation_profile = activation_profile or build_forecast_activation_profile(natal_payload)

    ascendant = natal_payload.get("angles", {}).get("Ascendant", {})
    asc_longitude = ascendant.get("longitude") if isinstance(ascendant, dict) else None

    events: list[dict] = []
    start_jd = _julian_day(report_start)
    end_jd = _julian_day(report_end)

    for eclipse_type in ("Solar", "Lunar"):
        for eclipse_datetime, eclipse_longitude in _eclipse_events_of_type(
            eclipse_type,
            start_jd,
            end_jd,
        ):
            sign_index = int(eclipse_longitude // 30)
            degree = eclipse_longitude % 30
            eclipse_house = (
                _whole_sign_house(eclipse_longitude, float(asc_longitude))
                if isinstance(asc_longitude, (int, float))
                else 0
            )

            matches: list[tuple[str, dict, float]] = []
            for target_name, target in targets.items():
                if target_name not in ECLIPSE_TARGET_KEYS:
                    continue
                distance = _angle_difference(eclipse_longitude, target["longitude"])
                if distance <= 3.0:
                    matches.append((target_name, target, distance))

            if not matches:
                score = 0.34
                label, bar = _intensity_label(score)
                event = {
                    "event_type": "eclipse",
                    "eclipse_type": eclipse_type,
                    "eclipse_sign": ZODIAC_SIGNS[sign_index],
                    "eclipse_degree": round(degree, 2),
                    "eclipse_longitude": round(eclipse_longitude, 4),
                    "transit_planet": eclipse_type,
                    "natal_target": "",
                    "natal_target_key": "",
                    "natal_target_display": "",
                    "natal_house": eclipse_house,
                    "whole_sign_house": eclipse_house,
                    "natal_contact": "",
                    "natal_contact_house": eclipse_house,
                    "distance_to_natal_target": None,
                    "entry_datetime": eclipse_datetime,
                    "peak_datetime": eclipse_datetime,
                    "leave_datetime": None,
                    "entry_date": _format_event_date(eclipse_datetime),
                    "peak_date": _format_event_date(eclipse_datetime),
                    "leave_date": "",
                    "duration_days": 0.0,
                    "raw_score": round(score, 4),
                    "combined_intensity_score": round(score, 4),
                    "score": round(score, 4),
                    "intensity_label": label,
                    "intensity_bar": bar,
                    "priority": "B",
                    "peak_month": (eclipse_datetime.year, eclipse_datetime.month),
                }
                events.append(enrich_forecast_event(event, activation_profile))
                continue

            for target_name, target, distance in matches:
                score = min(1.0, 0.54 + ((3.0 - distance) / 3.0) * 0.30)
                label, bar = _intensity_label(score)
                event = {
                    "event_type": "eclipse",
                    "eclipse_type": eclipse_type,
                    "eclipse_sign": ZODIAC_SIGNS[sign_index],
                    "eclipse_degree": round(degree, 2),
                    "eclipse_longitude": round(eclipse_longitude, 4),
                    "transit_planet": eclipse_type,
                    "natal_target": target_name,
                    "natal_target_key": ECLIPSE_TARGET_KEYS[target_name],
                    "natal_target_display": _target_display(target_name, target),
                    "natal_house": target["house"],
                    # Canonical fields for content-pack routing and testing.
                    "whole_sign_house": eclipse_house or target["house"],
                    "natal_contact": target_name,
                    "natal_contact_house": target["house"],
                    "distance_to_natal_target": round(distance, 3),
                    "entry_datetime": eclipse_datetime,
                    "peak_datetime": eclipse_datetime,
                    "leave_datetime": None,
                    "entry_date": _format_event_date(eclipse_datetime),
                    "peak_date": _format_event_date(eclipse_datetime),
                    "leave_date": "",
                    "duration_days": 0.0,
                    "raw_score": round(score, 4),
                    "combined_intensity_score": round(score, 4),
                    "score": round(score, 4),
                    "intensity_label": label,
                    "intensity_bar": bar,
                    "priority": "A",
                    "peak_month": (eclipse_datetime.year, eclipse_datetime.month),
                }
                events.append(enrich_forecast_event(event, activation_profile))

    events.sort(key=lambda event: event["peak_datetime"])
    return events


def _find_lunations(start_jd: float, end_jd: float) -> list[tuple[datetime, float, str]]:
    """Returns (peak_datetime, longitude, lunation_type) for New and Full Moons in the window."""
    lunations = []
    cursor = start_jd
    
    def _phase_diff(jd: float) -> float:
        sun_lon = swe.calc_ut(jd, swe.SUN, CALC_FLAGS)[0][0]
        moon_lon = swe.calc_ut(jd, swe.MOON, CALC_FLAGS)[0][0]
        return (moon_lon - sun_lon) % 360.0

    while cursor <= end_jd:
        diff1 = _phase_diff(cursor)
        diff2 = _phase_diff(cursor + 1.0)
        
        # New Moon (crossing 0/360)
        if diff1 > 340 and diff2 < 20:
            left, right = cursor, cursor + 1.0
            for _ in range(15):
                mid = (left + right) / 2.0
                if _phase_diff(mid) > 180:
                    left = mid
                else:
                    right = mid
            exact_jd = (left + right) / 2.0
            lon = swe.calc_ut(exact_jd, swe.SUN, CALC_FLAGS)[0][0]
            lunations.append((_datetime_from_julian_day(exact_jd), float(lon), "NEW_MOON"))
            
        # Full Moon (crossing 180)
        if diff1 < 180 and diff2 > 180:
            left, right = cursor, cursor + 1.0
            for _ in range(15):
                mid = (left + right) / 2.0
                if _phase_diff(mid) < 180:
                    left = mid
                else:
                    right = mid
            exact_jd = (left + right) / 2.0
            lon = swe.calc_ut(exact_jd, swe.MOON, CALC_FLAGS)[0][0]
            lunations.append((_datetime_from_julian_day(exact_jd), float(lon), "FULL_MOON"))
            
        cursor += 1.0
        
    return lunations

def scan_lunations(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    activation_profile: dict | None = None,
    eclipse_events: list[dict] | None = None,
) -> list[dict]:
    """Finds new/full moons and records closer natal contacts when present, filtering out eclipses."""
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else _add_year_window(report_start)
    targets = _natal_targets(natal_payload)
    activation_profile = activation_profile or build_forecast_activation_profile(natal_payload)

    ascendant = natal_payload.get("angles", {}).get("Ascendant", {})
    asc_longitude = ascendant.get("longitude") if isinstance(ascendant, dict) else None

    events: list[dict] = []
    start_jd = _julian_day(report_start)
    end_jd = _julian_day(report_end)
    
    eclipse_dates = set()
    if eclipse_events:
        for e in eclipse_events:
            eclipse_dates.add(e.get("peak_date"))

    for lunation_datetime, lunation_longitude, lunation_type in _find_lunations(start_jd, end_jd):
        if _format_event_date(lunation_datetime) in eclipse_dates:
            continue
            
        sign_index = int(lunation_longitude // 30)
        degree = lunation_longitude % 30
        lunation_house = (
            _whole_sign_house(lunation_longitude, float(asc_longitude))
            if isinstance(asc_longitude, (int, float))
            else 0
        )

        matches: list[tuple[str, dict, float]] = []
        for target_name, target in targets.items():
            if target_name not in ECLIPSE_TARGET_KEYS:
                continue
            distance = _angle_difference(lunation_longitude, target["longitude"])
            if distance <= 2.0:
                matches.append((target_name, target, distance))

        if not matches:
            score = 0.15
            label, bar = _intensity_label(score)
            event = {
                "event_type": "lunation",
                "lunation_type": lunation_type,
                "eclipse_sign": ZODIAC_SIGNS[sign_index],
                "lunation_sign": ZODIAC_SIGNS[sign_index],
                "eclipse_degree": round(degree, 2),
                "lunation_degree": round(degree, 2),
                "eclipse_longitude": round(lunation_longitude, 4),
                "lunation_longitude": round(lunation_longitude, 4),
                "transit_planet": "Moon",
                "natal_target": "",
                "natal_target_key": "",
                "natal_target_display": "",
                "natal_house": lunation_house,
                "whole_sign_house": lunation_house,
                "natal_contact": "",
                "natal_contact_house": lunation_house,
                "distance_to_natal_target": None,
                "entry_datetime": lunation_datetime,
                "peak_datetime": lunation_datetime,
                "leave_datetime": None,
                "entry_date": _format_event_date(lunation_datetime),
                "peak_date": _format_event_date(lunation_datetime),
                "leave_date": "",
                "duration_days": 0.0,
                "raw_score": round(score, 4),
                "combined_intensity_score": round(score, 4),
                "score": round(score, 4),
                "intensity_label": label,
                "intensity_bar": bar,
                "priority": "C",
                "peak_month": (lunation_datetime.year, lunation_datetime.month),
            }
            events.append(enrich_forecast_event(event, activation_profile))
            continue

        for target_name, target, distance in matches:
            score = min(1.0, 0.44 + ((2.0 - distance) / 2.0) * 0.20)
            label, bar = _intensity_label(score)
            event = {
                "event_type": "lunation",
                "lunation_type": lunation_type,
                "eclipse_sign": ZODIAC_SIGNS[sign_index],
                "lunation_sign": ZODIAC_SIGNS[sign_index],
                "eclipse_degree": round(degree, 2),
                "lunation_degree": round(degree, 2),
                "eclipse_longitude": round(lunation_longitude, 4),
                "lunation_longitude": round(lunation_longitude, 4),
                "transit_planet": "Moon",
                "natal_target": target_name,
                "natal_target_key": ECLIPSE_TARGET_KEYS[target_name],
                "natal_target_display": _target_display(target_name, target),
                "natal_house": target["house"],
                "whole_sign_house": lunation_house or target["house"],
                "natal_contact": target_name,
                "natal_contact_house": target["house"],
                "distance_to_natal_target": round(distance, 3),
                "entry_datetime": lunation_datetime,
                "peak_datetime": lunation_datetime,
                "leave_datetime": None,
                "entry_date": _format_event_date(lunation_datetime),
                "peak_date": _format_event_date(lunation_datetime),
                "leave_date": "",
                "duration_days": 0.0,
                "raw_score": round(score, 4),
                "combined_intensity_score": round(score, 4),
                "score": round(score, 4),
                "intensity_label": label,
                "intensity_bar": bar,
                "priority": "B",
                "peak_month": (lunation_datetime.year, lunation_datetime.month),
            }
            events.append(enrich_forecast_event(event, activation_profile))

    events.sort(key=lambda event: event["peak_datetime"])
    return events


def _filter_moon_progression_events(progression_events: list[dict]) -> list[dict]:
    """
    Keeps only progressed-Moon-involved contacts/ingresses (clock_role
    "modifier", ~2-4 week orb window per engine/progressions.py) -- the one
    progression-family technique fast enough to fit a 90-day report.
    Explicitly excludes progression_lunation_phase: that's the progressed
    Sun-Moon phase cycle (~29.5 years per full cycle, quarter events roughly
    every 7 years), a different and much slower phenomenon that happens to
    also carry transit_planet == "Moon".
    """
    kept = []
    for event in progression_events:
        if event.get("method_variant") == "progression_lunation_phase":
            continue
        if event.get("transit_planet") == "Moon":
            kept.append(event)
            continue
        if event.get("method_variant") in ("progressed_to_progressed", "transit_to_progressed") and event.get("natal_target") == "Moon":
            kept.append(event)
    return kept


def _filter_texture_progression_events(progression_events: list[dict]) -> list[dict]:
    """
    Keeps only progression events scoped as season-scale "texture" (clock_role == "chapter").
    Explicitly excludes the progressed Moon / modifier events which are handled by the 
    Personal Forecast.
    """
    return [e for e in progression_events if e.get("clock_role") == "chapter"]


# ── Public Year-Ahead API ──────────────────────────────────────
def compute_year_ahead_events(
    natal_payload: dict,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    step_hours: int = 12,
    include_moon_progressions: bool = False,
    include_year_texture: bool = False,
) -> dict:
    """
    Builds the structured event timeline for the full Year Ahead report.

    Returns a dictionary rather than a bare list so the report-builder layer
    can access each event family separately as well as a combined chronology.

    include_moon_progressions: opt-in only (Personal Forecast passes True).
    Progressed Moon contacts run on a ~2-4 week orb window (clock_role
    "modifier" per engine/progressions.py), fast enough to fit a 90-day
    report. Slower progressed bodies (clock_role "chapter", ~2-4 month
    windows) are deliberately excluded here -- that's a separate, still-
    undecided placement question for Year Ahead, not something this flag
    should default into for every caller.
    """
    report_start = _ensure_utc(start_date)
    report_end = _ensure_utc(end_date) if end_date else _add_year_window(report_start)
    activation_profile = build_forecast_activation_profile(natal_payload)

    transit_events = scan_transit_windows(
        natal_payload,
        report_start,
        report_end,
        step_hours,
        activation_profile,
    )
    ingress_events = scan_house_ingresses(
        natal_payload,
        report_start,
        report_end,
        step_hours,
        activation_profile,
    )
    station_events = scan_stations(
        natal_payload,
        report_start,
        report_end,
        step_hours,
        activation_profile,
    )
    eclipse_events = scan_eclipses(
        natal_payload,
        report_start,
        report_end,
        activation_profile,
    )
    lunation_events = scan_lunations(
        natal_payload,
        report_start,
        report_end,
        activation_profile,
        eclipse_events=eclipse_events,
    )

    from engine.profections import annual_profection_periods
    profection_periods = annual_profection_periods(natal_payload, report_start, report_end)

    return_events = []
    try:
        from engine.returns import scan_return_events
        return_events = scan_return_events(natal_payload, report_start, report_end)
    except Exception:
        return_events = []

    zodiacal_releasing_events = []
    zodiacal_releasing_periods = []
    try:
        from engine.zodiacal_releasing import (
            zodiacal_releasing_events as _scan_zodiacal_releasing_events,
            zodiacal_releasing_periods as _scan_zodiacal_releasing_periods,
        )
        for lot_name in ("Fortune", "Spirit"):
            zodiacal_releasing_events.extend(
                _scan_zodiacal_releasing_events(natal_payload, report_start, report_end, lot_name=lot_name)
            )
            zodiacal_releasing_periods.extend(
                _scan_zodiacal_releasing_periods(natal_payload, report_start, report_end, lot_name=lot_name)
            )
    except Exception:
        zodiacal_releasing_events = []
        zodiacal_releasing_periods = []

    moon_progression_events = []
    if include_moon_progressions:
        from engine.progressions import scan_progression_events
        moon_progression_events = _filter_moon_progression_events(
            scan_progression_events(natal_payload, report_start, report_end)
        )

    year_texture_progressions = []
    year_texture_solar_arc = []
    if include_year_texture:
        from engine.progressions import scan_progression_events
        from engine.solar_arc import scan_solar_arc_events
        
        year_texture_progressions = _filter_texture_progression_events(
            scan_progression_events(natal_payload, report_start, report_end)
        )
        for e in year_texture_progressions:
            e["_is_year_texture"] = True
            
        year_texture_solar_arc = scan_solar_arc_events(natal_payload, report_start, report_end)

    linked_events = link_related_forecast_events(
        transit_events,
        ingress_events,
        station_events,
        eclipse_events,
        activation_profile,
        lunation_events=lunation_events,
        progression_events=moon_progression_events + year_texture_progressions,
        solar_arc_events=year_texture_solar_arc,
        time_lord_periods=profection_periods,
    )
    transit_events = linked_events["transit_events"]
    ingress_events = linked_events["ingress_events"]
    station_events = linked_events["station_events"]
    eclipse_events = linked_events["eclipse_events"]
    lunation_events = linked_events["lunation_events"]
    
    progression_events = []
    year_texture_progressions_enriched = []
    for e in linked_events["progression_events"]:
        if e.pop("_is_year_texture", False):
            year_texture_progressions_enriched.append(e)
        else:
            progression_events.append(e)
            
    year_texture_solar_arc_enriched = linked_events["solar_arc_events"]

    # progression_events and year_texture_solar_arc_enriched already passed
    # through normalize_to_forecast_event inside scan_progression_events() /
    # scan_solar_arc_events(); re-normalizing here would silently redo that
    # work every call. Only the five families whose scanners predate the
    # adapter need it applied at this seam.
    transit_events = [normalize_to_forecast_event(e) for e in transit_events]
    ingress_events = [normalize_to_forecast_event(e) for e in ingress_events]
    station_events = [normalize_to_forecast_event(e) for e in station_events]
    eclipse_events = [normalize_to_forecast_event(e) for e in eclipse_events]
    lunation_events = [normalize_to_forecast_event(e) for e in lunation_events]

    all_events = transit_events + ingress_events + station_events + eclipse_events + lunation_events + progression_events
    all_events.sort(
        key=lambda event: (
            event["peak_datetime"],
            -event.get("combined_intensity_score", 0.0),
        )
    )

    return {
        "report_start": report_start,
        "report_end": report_end,
        "transits": transit_events,
        "ingresses": ingress_events,
        "stations": station_events,
        "eclipses": eclipse_events,
        "lunations": lunation_events,
        "progressions": progression_events,
        "return_events": return_events,
        "zodiacal_releasing_events": sorted(
            zodiacal_releasing_events,
            key=lambda event: event.get("peak_datetime") or report_end,
        ),
        "time_lord_periods": linked_events["time_lord_periods"],
        "zodiacal_releasing_periods": sorted(
            zodiacal_releasing_periods,
            key=lambda period: (period.get("start_at") or "", period.get("level") or ""),
        ),
        "year_texture_progressions": year_texture_progressions_enriched,
        "year_texture_solar_arc": year_texture_solar_arc_enriched,
        "all_events": all_events,
    }
