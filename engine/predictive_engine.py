"""
engine/predictive_engine.py — Entangled Oracle Predictive Engine
Formula version: predictive_v0.2

Architecture notes:
  - Phases 1–4 live here: skeleton, signal extraction, registry, window detection.
  - Phase 5 (generator integration) is in generate.py.
  - This engine does NOT replace the transit engine. It consumes transit event
    output as its first signal source, then layers predictive scoring on top.
  - No prose is generated here. All output is structured data.
  - All sub-phases are wrapped in try/except so the contract shape is always
    returned even when the transit engine or ephemeris is unavailable.

v0.2 changes (window detection redesign):
  - Two-layer signal model: structural (slow outer planets) vs fast triggers.
  - Wide rolling baseline (35 days) extracts the structural-chapter field.
  - Residual series (7-day smooth − baseline) captures local activations.
  - Prominence-based peak detection replaces the global-threshold run grouper.
  - Window boundaries derived from residual zero-crossings and inter-peak valleys.
  - Windows expose local_peak_intensity, structural_field_intensity, total_intensity,
    prominence, active_slow_chapter_signals, active_fast_trigger_signals.
  - Daily series exposes baseline_score and residual_score for diagnostics.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, date
from typing import Any


# ── Phase 2: Signal source configuration ──────────────────────

# Allowed transit orb per source planet (degrees).
_TRANSIT_ORB: dict[str, float] = {
    "Saturn":  3.0,
    "Uranus":  3.0,
    "Neptune": 3.0,
    "Pluto":   3.0,
    "Jupiter": 4.0,
    "Mars":    2.0,
}
_DEFAULT_ORB = 3.0

# Planet weight: contribution ceiling for a single transit signal.
_PLANET_WEIGHT: dict[str, float] = {
    "Pluto":   0.95,
    "Uranus":  0.90,
    "Saturn":  0.85,
    "Neptune": 0.80,
    "Jupiter": 0.70,
    "Mars":    0.60,
}
_DEFAULT_PLANET_WEIGHT = 0.50

# Target relevance: importance of the natal body being transited.
_TARGET_RELEVANCE: dict[str, float] = {
    # Angles
    "ASC": 1.00, "Ascendant": 1.00,
    "MC":  1.00, "Midheaven": 1.00,
    "IC":  0.90, "Imum Coeli": 0.90,
    "DSC": 0.85, "Descendant": 0.85,
    "Vertex": 0.85,
    # Luminaries
    "Sun":  0.90,
    "Moon": 0.90,
    # Personal planets
    "Mercury": 0.70,
    "Venus":   0.75,
    "Mars":    0.70,
    # Social / outer
    "Jupiter": 0.65,
    "Saturn":  0.70,
    "Uranus":  0.65,
    "Neptune": 0.65,
    "Pluto":   0.70,
    "Chiron":  0.65,
    # Proprietary asteroids
    "Kassandra": 0.85,
    "Aletheia":  0.80,
    "Destinn":   0.80,
    "Karma":     0.80,
    "Kaali":     0.75,
    "Medea":     0.75,
    "Hermes":    0.70,
    "Chaos":     0.70,
}
_DEFAULT_RELEVANCE = 0.60

# Source planets whose transits are treated as structural-chapter contributors.
# Their activation spans months to years and form the baseline field rather
# than constituting discrete predictive windows on their own.
_STRUCTURAL_BODIES: frozenset[str] = frozenset({"Saturn", "Uranus", "Neptune", "Pluto"})


# ── Phase 3: Predictive Component Registry ────────────────────
#
# Maps EAS dimensions to eligible natal targets and activation modes.
# Used by _leading_index() to score which dimension's signature is most
# active during a predictive window.

PREDICTIVE_COMPONENT_REGISTRY: dict[str, dict] = {
    "KVQ": {
        "kass_angle": {
            "targets": ["Kassandra", "ASC", "MC", "IC"],
            "weight": 3.0,
            "activation_modes": ["transit_to_body", "transit_to_angle"],
        },
    },
    "MKI": {
        "mythkeeper_core": {
            "targets": ["Moon", "Saturn", "Chiron", "ASC"],
            "weight": 2.5,
            "activation_modes": ["transit_to_body"],
        },
    },
    "RWI": {
        "reality_anchor": {
            "targets": ["Sun", "MC", "Saturn", "Pluto"],
            "weight": 2.5,
            "activation_modes": ["transit_to_body", "transit_to_angle"],
        },
    },
    "DFIS": {
        "dfis_core": {
            "targets": ["Medea", "Kaali", "Moon", "Pluto"],
            "weight": 2.5,
            "activation_modes": ["transit_to_body"],
        },
    },
    "CATALYST": {
        "catalyst_node": {
            "targets": ["Destinn", "Karma", "Vertex", "Sun"],
            "weight": 2.5,
            "activation_modes": ["transit_to_body", "transit_to_angle"],
        },
    },
    # NGE and AHL reserved for a future phase.
    # "NGE": {},
    # "AHL": {},
}


# ── Window detection parameters ────────────────────────────────
#
# These constants calibrate the segmentation algorithm. Adjust to taste
# after inspecting sandbox output for a representative set of charts.
#
# Target operating range: 8–14 windows per year (center ~10).
# A quiet year may produce 6–8; a highly activated year 12–14.

_BASELINE_WINDOW_DAYS = 35   # wide rolling window for structural-chapter baseline
_SMOOTH_WINDOW_DAYS   = 7    # narrow smoothing for signal sharpening
_MIN_PEAK_DISTANCE    = 14   # minimum days separating two window peaks
_MIN_PROMINENCE       = 0.05 # minimum residual prominence to register a window


# ── Public API ─────────────────────────────────────────────────

def compute_predictive_windows(
    natal_payload: dict,
    index_results: dict,
    start_date: datetime,
    end_date: datetime,
    options: dict | None = None,
) -> dict:
    """
    Main entry point for the predictive engine.

    Collects transit-derived signals, scores them with TriggerStrength,
    builds a two-layer daily resonance series (structural baseline + local
    residual), detects prominence-based peaks in the residual, and returns
    localized predictive windows.

    Returns the Phase 1/v0.2 contract shape regardless of sub-phase failures:

        {
            "formula_version": "predictive_v0.2",
            "start_date":      "YYYY-MM-DD",
            "end_date":        "YYYY-MM-DD",
            "windows":         [...],
            "daily_series":    [...],
            "signals":         [...],
            "debug":           {...},
        }

    TriggerStrength = Exactness × EventWeight × TargetRelevance
    Exactness       = max(0, 1 − actual_orb / allowed_orb)
    """
    debug: dict[str, Any] = {}

    # ── Phase 2: Collect transit signals ──────────────────────
    signals: list[dict] = []
    try:
        signals = _collect_transit_signals(natal_payload, start_date, end_date, debug)
    except Exception as exc:
        debug["transit_signal_error"] = str(exc)

    # ── Phase 4a: Daily resonance series ──────────────────────
    daily_series: list[dict] = []
    try:
        daily_series = _build_daily_series(signals, start_date, end_date)
    except Exception as exc:
        debug["daily_series_error"] = str(exc)

    # ── Phase 4b: Window detection ─────────────────────────────
    windows: list[dict] = []
    try:
        windows = _detect_windows(daily_series, signals, index_results, debug)
    except Exception as exc:
        debug["window_detection_error"] = str(exc)

    debug["signal_count"] = len(signals)
    debug["window_count"] = len(windows)

    return {
        "formula_version": "predictive_v0.2",
        "start_date":      _fmt_date(start_date),
        "end_date":        _fmt_date(end_date),
        "windows":         windows,
        "daily_series":    daily_series,
        "signals":         signals,
        "debug":           debug,
    }


# ── Phase 2: Signal extraction ─────────────────────────────────

def _collect_transit_signals(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    debug: dict,
) -> list[dict]:
    """
    Calls the existing transit engine and converts each event to a
    PredictiveSignal node.
    """
    from engine.transit_engine import compute_year_ahead_events

    timeline = compute_year_ahead_events(
        natal_payload,
        start_date=start_date,
        end_date=end_date,
    )
    all_events = timeline.get("all_events", [])
    debug["raw_event_count"] = len(all_events)

    signals = []
    for i, event in enumerate(all_events):
        sig = _event_to_signal(event, i)
        if sig is not None:
            signals.append(sig)

    return signals


def _event_to_signal(event: dict, index: int) -> dict | None:
    """
    Converts one transit engine event dict to a PredictiveSignal node.

    Returns None when the event lacks the minimum data needed to score
    (e.g., a station event with no natal target and no peak datetime).
    """
    event_type    = event.get("event_type", "transit")
    source_body   = str(event.get("transit_planet") or event.get("planet") or "")
    target_body   = str(event.get("natal_target") or event.get("house_number") or "")
    aspect        = str(event.get("aspect") or event.get("aspect_name") or "")
    peak_orb      = _safe_float(event.get("peak_orb") or event.get("orb"), default=0.0)
    allowed_orb   = _TRANSIT_ORB.get(source_body, _DEFAULT_ORB)

    exactness = max(0.0, 1.0 - peak_orb / allowed_orb) if allowed_orb > 0 else 0.0

    event_weight = _PLANET_WEIGHT.get(source_body, _DEFAULT_PLANET_WEIGHT)
    target_relevance = max(
        _TARGET_RELEVANCE.get(target_body, _DEFAULT_RELEVANCE),
        _safe_float(event.get("natal_relevance"), default=0.0),
    )
    structural_importance = _safe_float(
        event.get("structural_importance", event.get("structural_score")),
        default=0.0,
    )
    theme_convergence = _safe_float(event.get("theme_convergence"), default=0.0)
    trigger_strength = round(exactness * event_weight * target_relevance, 5)
    signal_strength = round(
        trigger_strength
        * (1.0 + min(0.20, structural_importance * 0.20))
        * (1.0 + min(0.12, theme_convergence * 0.12)),
        5,
    )

    start_dt = _coerce_datetime(event.get("entry_datetime") or event.get("start_datetime"))
    peak_dt  = _coerce_datetime(event.get("peak_datetime"))
    end_dt   = _coerce_datetime(event.get("leave_datetime") or event.get("end_datetime"))

    if peak_dt is None:
        return None

    if start_dt is None:
        start_dt = peak_dt
    if end_dt is None:
        end_dt = peak_dt

    return {
        "signal_id":         f"sig_{event_type[:3]}_{index:04d}",
        "method_family":     event_type,
        "source_body":       source_body,
        "target_body":       target_body,
        "aspect":            aspect,
        "orb":               peak_orb,
        "allowed_orb":       allowed_orb,
        "exactness":         round(exactness, 5),
        "event_weight":      event_weight,
        "target_relevance":  target_relevance,
        "trigger_strength":  trigger_strength,
        "signal_strength":   signal_strength,
        "structural_importance": round(structural_importance, 5),
        "theme_convergence": round(theme_convergence, 5),
        "routing_state":     str(event.get("routing_state") or "").strip(),
        "pass_sequence":     str(event.get("pass_sequence") or "").strip(),
        "start_date":        _to_date(start_dt),
        "peak_date":         _to_date(peak_dt),
        "end_date":          _to_date(end_dt),
    }


# ── Phase 4a: Daily resonance series ──────────────────────────

def _build_daily_series(
    signals: list[dict],
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:
    """
    Walks every day in the forecast window and accumulates trigger_strength
    from signals whose active window includes that day, separated into
    structural (slow outer planet) and trigger (fast planet) contributions.

    Computes:
      raw_score        — sum of all signal trigger_strength active on that day
      smooth_score     — 7-day moving average of raw_score
      baseline_score   — 35-day moving average of raw_score (structural field)
      residual_score   — smooth_score − baseline_score (local activation excess)
      structural_raw   — raw contribution from structural bodies only
      trigger_raw      — raw contribution from fast trigger bodies only
    """
    start  = start_date.date()
    end    = end_date.date()
    n_days = (end - start).days + 1

    raw_total      = [0.0] * n_days
    raw_structural = [0.0] * n_days
    raw_trigger    = [0.0] * n_days

    for sig in signals:
        strength = sig.get("signal_strength", sig["trigger_strength"])
        if strength <= 0:
            continue
        is_structural = sig["source_body"] in _STRUCTURAL_BODIES
        sig_start = sig["start_date"]
        sig_end   = sig["end_date"]
        for i in range(n_days):
            d = start + timedelta(days=i)
            if sig_start <= d <= sig_end:
                raw_total[i] += strength
                if is_structural:
                    raw_structural[i] += strength
                else:
                    raw_trigger[i] += strength

    smooth   = _moving_average(raw_total, _SMOOTH_WINDOW_DAYS)
    baseline = _moving_average(raw_total, _BASELINE_WINDOW_DAYS)
    residual = [s - b for s, b in zip(smooth, baseline)]

    return [
        {
            "date":           (start + timedelta(days=i)).isoformat(),
            "raw_score":      round(raw_total[i], 5),
            "smooth_score":   round(smooth[i], 5),
            "baseline_score": round(baseline[i], 5),
            "residual_score": round(residual[i], 5),
            "structural_raw": round(raw_structural[i], 5),
            "trigger_raw":    round(raw_trigger[i], 5),
        }
        for i in range(n_days)
    ]


def _moving_average(values: list[float], window: int) -> list[float]:
    """Symmetric moving average with edge clamping (no zero-padding)."""
    n    = len(values)
    half = window // 2
    out  = []
    for i in range(n):
        lo  = max(0, i - half)
        hi  = min(n, i + half + 1)
        seg = values[lo:hi]
        out.append(sum(seg) / len(seg) if seg else 0.0)
    return out


# ── Phase 4b: Window detection (prominence-based) ──────────────
#
# Algorithm overview:
#   1. Read the residual series (smooth − wide baseline) from daily_series.
#      Falls back to smooth_score when baseline/residual are not present
#      (backward-compatible with externally constructed test series).
#   2. Find local maxima in the residual where residual > 0.
#   3. Compute prominence for each local maximum.
#      Prominence = how far the peak rises above the surrounding landscape
#      before reaching a taller neighbor — the standard signal-processing
#      definition, implemented without scipy.
#   4. Discard peaks below MIN_PROMINENCE.
#   5. Enforce minimum inter-peak distance: greedily retain the highest-
#      prominence peak, then reject any neighbor within MIN_PEAK_DISTANCE days.
#   6. Compute window boundaries: left/right via the residual zero-crossing
#      outward from each peak; internal splits at the inter-peak valley minimum.
#   7. Build window dicts with structural/trigger signal split.

def _detect_windows(
    daily_series: list[dict],
    signals: list[dict],
    index_results: dict,
    debug: dict | None = None,
) -> list[dict]:
    if not daily_series:
        return []

    dates  = [date.fromisoformat(d["date"]) for d in daily_series]
    smooth = [d.get("smooth_score", 0.0) for d in daily_series]

    # Baseline and residual — fall back to smooth/zero when not pre-computed
    # (allows tests to inject a minimal series without those fields).
    baseline = [d.get("baseline_score", 0.0) for d in daily_series]
    residual = [
        d.get("residual_score", smooth[i] - baseline[i])
        for i, d in enumerate(daily_series)
    ]

    # ── Step 1: Local maxima in residual ─────────────────────
    peak_indices = _find_local_maxima(residual)
    peak_indices = [i for i in peak_indices if residual[i] > 0]

    if debug is not None:
        debug["peaks_found_in_residual"] = len(peak_indices)

    if not peak_indices:
        return []

    # ── Step 2: Prominence ────────────────────────────────────
    prominences = _compute_peak_prominence(residual, peak_indices)

    # ── Step 3: Filter by minimum prominence ─────────────────
    qualified = [
        (idx, p) for idx, p in zip(peak_indices, prominences)
        if p >= _MIN_PROMINENCE
    ]

    if debug is not None:
        debug["peaks_after_prominence_filter"] = len(qualified)

    if not qualified:
        return []

    # ── Step 4: Enforce minimum inter-peak distance ───────────
    surviving = _filter_by_distance(qualified, _MIN_PEAK_DISTANCE)
    surviving.sort(key=lambda ip: ip[0])   # restore chronological order

    if debug is not None:
        debug["peaks_after_distance_filter"] = len(surviving)
        debug["baseline_window_days"] = _BASELINE_WINDOW_DAYS
        debug["smooth_window_days"]   = _SMOOTH_WINDOW_DAYS
        debug["min_peak_distance"]    = _MIN_PEAK_DISTANCE
        debug["min_prominence"]       = _MIN_PROMINENCE

    # ── Step 5: Window boundaries ─────────────────────────────
    peak_idx_list   = [i for i, _ in surviving]
    split_points    = _compute_split_points(residual, peak_idx_list)

    # ── Step 6: Build window objects ──────────────────────────
    windows = []
    for w_idx, (peak_i, prominence) in enumerate(surviving):
        left_bound  = split_points[w_idx]
        right_bound = split_points[w_idx + 1]

        start_d  = dates[left_bound]
        peak_d   = dates[peak_i]
        end_d    = dates[right_bound]

        local_peak_intensity       = residual[peak_i]
        structural_field_intensity = baseline[peak_i]
        total_intensity            = smooth[peak_i]

        # Signals overlapping any part of this window
        active_sigs = [
            s for s in signals
            if s["start_date"] <= end_d and s["end_date"] >= start_d
        ]
        slow_sigs    = [s for s in active_sigs if s["source_body"] in _STRUCTURAL_BODIES]
        trigger_sigs = [s for s in active_sigs if s["source_body"] not in _STRUCTURAL_BODIES]

        # Gradient: where does the peak sit within the window?
        # rising = peak in the later portion (score still climbing toward end)
        # releasing = peak in the early portion (score declining toward end)
        window_days = max(1, (end_d - start_d).days)
        peak_pos    = (peak_d - start_d).days / window_days
        if peak_pos > 0.60:
            gradient = "rising"
        elif peak_pos < 0.40:
            gradient = "releasing"
        else:
            gradient = "plateau"

        windows.append({
            "window_id":                    f"pw_{w_idx + 1:03d}",
            "start_date":                   start_d.isoformat(),
            "peak_date":                    peak_d.isoformat(),
            "end_date":                     end_d.isoformat(),
            # Intensity decomposition
            "local_peak_intensity":         round(local_peak_intensity, 4),
            "structural_field_intensity":   round(structural_field_intensity, 4),
            "total_intensity":              round(total_intensity, 4),
            "intensity":                    round(total_intensity, 4),  # backward compat
            "prominence":                   round(prominence, 4),
            # Shape
            "gradient":                     gradient,
            "leading_index":                _leading_index(active_sigs, index_results),
            # Signal breakdown
            "active_signals":               [s["signal_id"] for s in active_sigs],
            "active_slow_chapter_signals":  [s["signal_id"] for s in slow_sigs],
            "active_fast_trigger_signals":  [s["signal_id"] for s in trigger_sigs],
            # Phase 2+ placeholders
            "coherence":                    None,
            "memory":                       None,
            "interpretive_tags":            [],
        })

    return windows


# ── Peak detection helpers ──────────────────────────────────────

def _find_local_maxima(values: list[float]) -> list[int]:
    """
    Returns indices of strict local maxima.
    A value is a local maximum when it is strictly greater than both neighbors.
    Edge elements are compared against their single existing neighbor.
    """
    n = len(values)
    result = []
    for i in range(n):
        left  = values[i - 1] if i > 0     else float('-inf')
        right = values[i + 1] if i < n - 1 else float('-inf')
        if values[i] > left and values[i] > right:
            result.append(i)
    return result


def _compute_peak_prominence(
    values: list[float],
    peak_indices: list[int],
) -> list[float]:
    """
    Computes the prominence of each peak.

    For each peak P at index p_i:
      - Search left until a value >= P is found (or the series start).
        Record the minimum of values encountered along the way (left_min).
      - Search right similarly (right_min).
      - prominence = P − max(left_min, right_min)

    When only one side has a finite base (e.g., boundary peak), that side
    alone constrains the prominence, giving edge peaks their natural height.

    This matches scipy.signal.peak_prominences semantics without the
    scipy dependency.
    """
    n = len(values)
    prominences = []

    for p_i in peak_indices:
        p_val = values[p_i]

        left_min = float('inf')
        for j in range(p_i - 1, -1, -1):
            if values[j] >= p_val:
                break  # higher neighbor stops the search; don't include it
            if values[j] < left_min:
                left_min = values[j]

        right_min = float('inf')
        for j in range(p_i + 1, n):
            if values[j] >= p_val:
                break
            if values[j] < right_min:
                right_min = values[j]

        if left_min == float('inf') and right_min == float('inf'):
            prominence = p_val          # isolated peak with no surrounding data
        elif left_min == float('inf'):
            prominence = p_val - right_min
        elif right_min == float('inf'):
            prominence = p_val - left_min
        else:
            prominence = p_val - max(left_min, right_min)

        prominences.append(max(0.0, prominence))

    return prominences


def _filter_by_distance(
    qualified: list[tuple[int, float]],
    min_distance: int,
) -> list[tuple[int, float]]:
    """
    Greedily retains peaks in order of decreasing prominence, discarding
    any peak within min_distance samples of an already-retained peak.

    Produces 8–14 windows/year for typical transit data when min_distance=14.
    """
    by_prominence = sorted(qualified, key=lambda ip: ip[1], reverse=True)
    retained: list[tuple[int, float]] = []
    kept_indices: list[int] = []

    for peak_i, prominence in by_prominence:
        if any(abs(peak_i - r) < min_distance for r in kept_indices):
            continue
        retained.append((peak_i, prominence))
        kept_indices.append(peak_i)

    return retained


def _compute_split_points(
    residual: list[float],
    peak_indices: list[int],   # must be sorted ascending
) -> list[int]:
    """
    Returns len(peak_indices) + 1 boundary indices that define window extents.

    boundaries[i]     — start of window i
    boundaries[i + 1] — end   of window i

    Left/right outer boundaries use the residual zero-crossing outward from
    the first/last peak (or series edge if the residual never returns to zero).
    Internal boundaries are placed at the minimum-residual valley between
    adjacent peaks.
    """
    n = len(residual)
    if not peak_indices:
        return []

    boundaries: list[int] = []

    # Left boundary of first window: last zero-crossing before first peak
    p0 = peak_indices[0]
    left_bound = 0
    for j in range(p0 - 1, -1, -1):
        if residual[j] <= 0:
            left_bound = j + 1
            break
    boundaries.append(left_bound)

    # Internal splits: valley minimum between adjacent peaks
    for i in range(len(peak_indices) - 1):
        pi = peak_indices[i]
        pj = peak_indices[i + 1]
        if pj - pi > 1:
            valley_idx = min(range(pi + 1, pj), key=lambda k: residual[k])
        else:
            valley_idx = pi
        boundaries.append(valley_idx)

    # Right boundary of last window: first zero-crossing after last peak
    pN = peak_indices[-1]
    right_bound = n - 1
    for j in range(pN + 1, n):
        if residual[j] <= 0:
            right_bound = j - 1
            break
    boundaries.append(right_bound)

    return boundaries


# ── Phase 3: Leading index ──────────────────────────────────────

def _leading_index(active_sigs: list[dict], index_results: dict) -> str:
    """
    Scores each EAS dimension by how strongly its registry targets appear
    in the active signal set. Returns the highest-scoring dimension name.

    Falls back to the highest-scoring natal EAS dimension when no registry
    targets match, then to "KVQ" as a final default.
    """
    dim_scores: dict[str, float] = {}

    for dim, components in PREDICTIVE_COMPONENT_REGISTRY.items():
        total = 0.0
        for _comp_key, comp in components.items():
            targets = set(comp.get("targets", []))
            weight  = float(comp.get("weight", 1.0))
            for sig in active_sigs:
                if sig.get("target_body") in targets or sig.get("source_body") in targets:
                    total += sig.get("trigger_strength", 0.0) * weight
        if total > 0:
            dim_scores[dim] = total

    if dim_scores:
        return max(dim_scores, key=dim_scores.__getitem__)

    _legacy = {"AHL", "MAGNETIC", "MCQ", "SIREN"}
    ranked = [
        (k, v.get("score", 0.0))
        for k, v in index_results.items()
        if k not in _legacy and isinstance(v, dict)
    ]
    if ranked:
        return max(ranked, key=lambda kv: kv[1])[0]

    return "KVQ"


# ── Utilities ──────────────────────────────────────────────────

def _coerce_datetime(value: Any) -> datetime | None:
    """Normalize any date/datetime value to a UTC-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    return None


def _to_date(dt: datetime) -> date:
    """Extract a calendar date from a datetime."""
    return dt.date() if isinstance(dt, datetime) else dt


def _fmt_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
