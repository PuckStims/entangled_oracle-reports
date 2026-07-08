"""
engine/predictive_engine.py — Entangled Oracle Predictive Engine
Formula version: predictive_v0.3.1

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

v0.3 changes (method normalization + memory):
  - Predictive signals normalize method_family vs event_kind vs
    independence_group vs activation_route.
  - Windows now compute episode-based memory charge when active signals
    are present instead of leaving the field empty.
  - Windows expose pass_state, lifecycle_route, memory_state, and
    activation_key as sandbox diagnostics.

v0.3.1 changes (semantic atomic layer scaffolding):
  - Predictive signals now carry bounded operation profiles.
  - Aspect geometry biases those operation vectors without computing
    higher-order coherence yet.
  - Signals also carry epistemic confidence scaffolding, including
    angle-eligibility gating and explicit confidence components.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone, date
from typing import Any


_PREDICTIVE_FORMULA_VERSION = "predictive_v0.3.1"


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

_ANGLE_TARGETS: frozenset[str] = frozenset({
    "ASC", "Ascendant",
    "MC", "Midheaven",
    "IC", "Imum Coeli",
    "DSC", "Descendant",
    "Vertex",
})

_METHOD_WEIGHT_BY_GROUP: dict[str, float] = {
    "transit_clock": 1.00,
    "proprietary_transit_family": 0.95,
    "lunar_phase_clock": 0.92,
    "return_clock": 0.88,
    "progression_clock": 0.94,
    "solar_arc_clock": 0.96,
    "unknown_clock": 0.80,
}

_OPERATION_AXES: tuple[str, ...] = (
    "stabilize",
    "amplify",
    "activate",
    "disrupt",
    "dissolve",
    "reveal",
)

_SOURCE_OPERATION_BASE: dict[str, dict[str, float]] = {
    "Saturn":  {"stabilize": 0.92, "amplify": 0.12, "activate": 0.18, "disrupt": 0.28, "dissolve": 0.12, "reveal": 0.44},
    "Uranus":  {"stabilize": 0.12, "amplify": 0.30, "activate": 0.74, "disrupt": 0.94, "dissolve": 0.18, "reveal": 0.48},
    "Neptune": {"stabilize": 0.10, "amplify": 0.32, "activate": 0.20, "disrupt": 0.18, "dissolve": 0.96, "reveal": 0.54},
    "Pluto":   {"stabilize": 0.22, "amplify": 0.34, "activate": 0.26, "disrupt": 0.68, "dissolve": 0.58, "reveal": 0.90},
    "Jupiter": {"stabilize": 0.30, "amplify": 0.96, "activate": 0.42, "disrupt": 0.16, "dissolve": 0.10, "reveal": 0.38},
    "Mars":    {"stabilize": 0.10, "amplify": 0.28, "activate": 0.96, "disrupt": 0.62, "dissolve": 0.08, "reveal": 0.26},
}
_DEFAULT_SOURCE_OPERATION_BASE = {
    "stabilize": 0.22,
    "amplify": 0.22,
    "activate": 0.22,
    "disrupt": 0.22,
    "dissolve": 0.22,
    "reveal": 0.22,
}

_TARGET_SUBSTRATE_BIAS: dict[str, dict[str, float]] = {
    "angle": {"stabilize": -0.05, "amplify": 0.10, "activate": 0.25, "disrupt": 0.08, "dissolve": -0.05, "reveal": 0.20},
    "luminary": {"stabilize": 0.05, "amplify": 0.10, "activate": 0.10, "disrupt": 0.00, "dissolve": 0.05, "reveal": 0.16},
    "personal": {"stabilize": 0.00, "amplify": 0.05, "activate": 0.14, "disrupt": 0.05, "dissolve": 0.00, "reveal": 0.08},
    "social_outer": {"stabilize": 0.08, "amplify": 0.00, "activate": -0.02, "disrupt": 0.08, "dissolve": 0.04, "reveal": 0.10},
    "specialist": {"stabilize": -0.04, "amplify": 0.06, "activate": 0.08, "disrupt": 0.10, "dissolve": 0.08, "reveal": 0.24},
    "house": {"stabilize": 0.02, "amplify": 0.00, "activate": 0.06, "disrupt": 0.02, "dissolve": 0.00, "reveal": 0.02},
    "generic": {"stabilize": 0.00, "amplify": 0.00, "activate": 0.00, "disrupt": 0.00, "dissolve": 0.00, "reveal": 0.00},
}

_ASPECT_OPERATION_BIAS: dict[str, dict[str, float]] = {
    "CONJUNCTION": {"stabilize": 0.08, "amplify": 0.12, "activate": 0.16, "disrupt": 0.02, "dissolve": 0.02, "reveal": 0.10},
    "TRINE": {"stabilize": 0.16, "amplify": 0.10, "activate": 0.04, "disrupt": -0.14, "dissolve": -0.06, "reveal": 0.02},
    "SEXTILE": {"stabilize": 0.08, "amplify": 0.08, "activate": 0.06, "disrupt": -0.08, "dissolve": -0.04, "reveal": 0.02},
    "SQUARE": {"stabilize": -0.18, "amplify": 0.04, "activate": 0.10, "disrupt": 0.22, "dissolve": 0.06, "reveal": 0.08},
    "OPPOSITION": {"stabilize": -0.12, "amplify": 0.06, "activate": 0.10, "disrupt": 0.18, "dissolve": 0.08, "reveal": 0.12},
    "GENERIC": {"stabilize": 0.00, "amplify": 0.00, "activate": 0.00, "disrupt": 0.00, "dissolve": 0.00, "reveal": 0.00},
}

_METHOD_OPERATION_MULTIPLIER: dict[str, dict[str, float]] = {
    "TRANSIT": {"stabilize": 1.00, "amplify": 1.00, "activate": 1.00, "disrupt": 1.00, "dissolve": 1.00, "reveal": 1.00},
    "PROPRIETARY_TRANSIT": {"stabilize": 0.96, "amplify": 1.00, "activate": 1.04, "disrupt": 1.04, "dissolve": 1.00, "reveal": 1.08},
    "LUNATION": {"stabilize": 0.92, "amplify": 1.06, "activate": 0.96, "disrupt": 0.96, "dissolve": 1.06, "reveal": 1.02},
    "RETURN": {"stabilize": 1.02, "amplify": 0.98, "activate": 0.94, "disrupt": 0.92, "dissolve": 0.94, "reveal": 1.06},
    "PROGRESSION": {"stabilize": 0.96, "amplify": 0.96, "activate": 0.90, "disrupt": 0.90, "dissolve": 1.04, "reveal": 1.08},
    "SOLAR_ARC": {"stabilize": 0.98, "amplify": 0.96, "activate": 0.94, "disrupt": 0.96, "dissolve": 0.96, "reveal": 1.06},
    "UNKNOWN": {"stabilize": 1.00, "amplify": 1.00, "activate": 1.00, "disrupt": 1.00, "dissolve": 1.00, "reveal": 1.00},
}

_CONSTRUCTIVE_OPERATIONS: frozenset[str] = frozenset({"stabilize", "amplify", "activate"})
_DISSOLVING_OPERATIONS: frozenset[str] = frozenset({"disrupt", "dissolve"})

_MEMORY_DECAY_YEARS = 1.5
_FSM_EXACTNESS_THRESHOLD = 0.5
ALLOWED_STATES: frozenset[str] = frozenset({
    "PRELUDE",
    "APPROACH",
    "EXACTNESS",
    "AFTERMATH",
    "RETROGRADE_REVIEW",
    "RESOLUTION",
    "RESIDUAL_FIELD",
})


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
            "formula_version": _PREDICTIVE_FORMULA_VERSION,
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
        print(f"[Predictive] Transit signal collection failed (non-fatal, report continues with 0 signals): {exc}")

    if _proprietary_asteroid_rd_enabled(options):
        try:
            proprietary_signals = _collect_proprietary_asteroid_signals(
                natal_payload,
                start_date,
                end_date,
                debug,
                start_index=len(signals),
            )
            signals.extend(proprietary_signals)
        except Exception as exc:
            debug["proprietary_asteroid_signal_error"] = str(exc)
            print(f"[Predictive] Proprietary asteroid signal collection failed (non-fatal): {exc}")
    else:
        debug["proprietary_asteroid_rd_enabled"] = False
        debug["scan_proprietary_forecast_windows"] = "rd_gate_disabled"

    try:
        return_signals = _collect_return_signals(
            natal_payload,
            start_date,
            end_date,
            debug,
            start_index=len(signals),
        )
        signals.extend(return_signals)
    except Exception as exc:
        debug["return_signal_error"] = str(exc)
        print(f"[Predictive] Return signal collection failed (non-fatal): {exc}")

    try:
        solar_arc_signals = _collect_solar_arc_signals(
            natal_payload,
            start_date,
            end_date,
            debug,
            start_index=len(signals),
        )
        signals.extend(solar_arc_signals)
    except Exception as exc:
        debug["solar_arc_signal_error"] = str(exc)
        print(f"[Predictive] Solar Arc signal collection failed (non-fatal): {exc}")

    try:
        progression_signals = _collect_progression_signals(
            natal_payload,
            start_date,
            end_date,
            debug,
            start_index=len(signals),
        )
        signals.extend(progression_signals)
    except Exception as exc:
        debug["progression_signal_error"] = str(exc)
        print(f"[Predictive] Progression signal collection failed (non-fatal): {exc}")

    try:
        lots_signals = _collect_zr_signals(
            natal_payload,
            start_date,
            end_date,
            debug,
            start_index=len(signals),
        )
        signals.extend(lots_signals)
    except Exception as exc:
        debug["zodiacal_releasing_signal_error"] = str(exc)
        print(f"[Predictive] Zodiacal Releasing signal collection failed (non-fatal): {exc}")

    time_lord_periods: list[dict] = []
    try:
        time_lord_periods = _collect_time_lord_periods(natal_payload, start_date, end_date, debug)
    except Exception as exc:
        debug["time_lord_period_error"] = str(exc)
        print(f"[Predictive] Time-lord period collection failed (non-fatal): {exc}")

    # ── Phase 4a: Daily resonance series ──────────────────────
    daily_series: list[dict] = []
    try:
        daily_series = _build_daily_series(signals, start_date, end_date)
    except Exception as exc:
        debug["daily_series_error"] = str(exc)
        print(f"[Predictive] Daily series build failed (non-fatal, report continues with 0 windows): {exc}")

    # ── Phase 4b: Window detection ─────────────────────────────
    windows: list[dict] = []
    try:
        windows = _detect_windows(daily_series, signals, index_results, debug)
    except Exception as exc:
        debug["window_detection_error"] = str(exc)
        print(f"[Predictive] Window detection failed (non-fatal, report continues with 0 windows): {exc}")

    debug["signal_count"] = len(signals)
    debug["window_count"] = len(windows)

    return {
        "formula_version": _PREDICTIVE_FORMULA_VERSION,
        "start_date":      _fmt_date(start_date),
        "end_date":        _fmt_date(end_date),
        "windows":         windows,
        "daily_series":    daily_series,
        "signals":         signals,
        "time_lord_periods": time_lord_periods,
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

    birth_time_status = _predictive_birth_time_status(natal_payload)
    signals = []
    for i, event in enumerate(all_events):
        sig = _event_to_signal(event, i, birth_time_status=birth_time_status)
        if sig is not None:
            signals.append(sig)

    return signals


def _collect_proprietary_asteroid_signals(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    debug: dict,
    *,
    start_index: int = 0,
) -> list[dict]:
    """
    Adapts the existing proprietary forecast scanner into internal evidence.

    The scanner's own trigger definitions, orbs, weights, and final scores are
    preserved. This function only normalizes emitted windows into the shared
    PredictiveSignal shape when the R&D gate is enabled.
    """
    from engine.asteroid_policy import load_asteroid_policy
    from engine.transit_engine import scan_proprietary_forecast_windows

    policy = load_asteroid_policy()
    debug["proprietary_asteroid_rd_enabled"] = True
    debug["asteroid_registry_version"] = policy.policy_version
    debug["asteroid_registry_count"] = policy.asteroid_count

    windows_by_formula = scan_proprietary_forecast_windows(
        natal_payload,
        start_date=start_date,
        end_date=end_date,
    )
    signals: list[dict] = []
    skipped: list[dict] = []
    index = start_index

    for formula_name, formula_events in windows_by_formula.items():
        for event in formula_events:
            signal = _proprietary_event_to_signal(event, index, policy)
            index += 1
            if signal is None:
                skipped.append({
                    "formula_name": formula_name,
                    "source_body": event.get("transit_planet"),
                    "target_body": event.get("natal_target"),
                    "reason": "missing_peak_datetime_or_policy_rejection",
                })
                continue
            signals.append(signal)

    debug["scan_proprietary_forecast_windows"] = "wired_phase3_rd_gate"
    debug["proprietary_asteroid_signal_count"] = len(signals)
    debug["proprietary_asteroid_skipped"] = skipped
    return signals


def _collect_return_signals(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    debug: dict,
    *,
    start_index: int = 0,
) -> list[dict]:
    from engine.returns import scan_return_events

    events = scan_return_events(natal_payload, start_date, end_date)
    debug["return_event_count"] = len(events)
    signals: list[dict] = []
    for offset, event in enumerate(events):
        signal = _event_to_signal(event, start_index + offset, birth_time_status="exact")
        if signal is not None:
            signals.append(signal)
    debug["return_signal_count"] = len(signals)
    return signals


def _collect_time_lord_periods(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    debug: dict,
) -> list[dict]:
    from engine.profections import annual_profection_periods

    periods = annual_profection_periods(natal_payload, start_date, end_date)
    debug["annual_profection_period_count"] = len(periods)

    try:
        from engine.zodiacal_releasing import zodiacal_releasing_periods

        fortune_periods = zodiacal_releasing_periods(natal_payload, start_date, end_date, lot_name="Fortune")
        spirit_periods = zodiacal_releasing_periods(natal_payload, start_date, end_date, lot_name="Spirit")
        debug["zr_fortune_period_count"] = len(fortune_periods)
        debug["zr_spirit_period_count"] = len(spirit_periods)
        periods = periods + fortune_periods + spirit_periods
    except Exception as exc:
        debug["zr_period_error"] = str(exc)
        print(f"[Predictive] Zodiacal Releasing period collection failed (non-fatal): {exc}")

    return periods


def _collect_zr_signals(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    debug: dict,
    *,
    start_index: int = 0,
) -> list[dict]:
    from engine.zodiacal_releasing import zodiacal_releasing_events

    fortune_events = zodiacal_releasing_events(natal_payload, start_date, end_date, lot_name="Fortune")
    spirit_events = zodiacal_releasing_events(natal_payload, start_date, end_date, lot_name="Spirit")
    events = fortune_events + spirit_events
    debug["zr_event_count"] = len(events)

    signals: list[dict] = []
    for offset, event in enumerate(events):
        signal = _event_to_signal(event, start_index + offset, birth_time_status=_predictive_birth_time_status(natal_payload))
        if signal is not None:
            signals.append(signal)
    debug["zr_signal_count"] = len(signals)
    return signals


def _collect_solar_arc_signals(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    debug: dict,
    *,
    start_index: int = 0,
) -> list[dict]:
    from engine.solar_arc import scan_solar_arc_events

    events = scan_solar_arc_events(natal_payload, start_date, end_date)
    debug["solar_arc_event_count"] = len(events)
    signals: list[dict] = []
    for offset, event in enumerate(events):
        signal = _event_to_signal(event, start_index + offset, birth_time_status=_predictive_birth_time_status(natal_payload))
        if signal is not None:
            signals.append(signal)
    debug["solar_arc_signal_count"] = len(signals)
    return signals


def _collect_progression_signals(
    natal_payload: dict,
    start_date: datetime,
    end_date: datetime,
    debug: dict,
    *,
    start_index: int = 0,
) -> list[dict]:
    from engine.progressions import scan_progression_events

    events = scan_progression_events(natal_payload, start_date, end_date)
    debug["progression_event_count"] = len(events)
    signals: list[dict] = []
    for offset, event in enumerate(events):
        signal = _event_to_signal(event, start_index + offset, birth_time_status=_predictive_birth_time_status(natal_payload))
        if signal is not None:
            signals.append(signal)
    debug["progression_signal_count"] = len(signals)
    return signals


def _event_to_signal(event: dict, index: int, birth_time_status: str = "unknown") -> dict | None:
    """
    Converts one transit engine event dict to a PredictiveSignal node.

    Returns None when the event lacks the minimum data needed to score
    (e.g., a station event with no natal target and no peak datetime).
    """
    event_type    = str(event.get("event_type", "transit") or "transit").strip().lower()
    source_body   = str(event.get("transit_planet") or event.get("planet") or "")
    target_body   = str(event.get("natal_target") or event.get("house_number") or "")
    aspect        = str(event.get("aspect") or event.get("aspect_name") or "")
    peak_orb      = _safe_float(event.get("peak_orb") or event.get("orb"), default=0.0)
    allowed_orb   = _safe_float(event.get("orb_limit"), _TRANSIT_ORB.get(source_body, _DEFAULT_ORB))

    computed_exactness = max(0.0, 1.0 - peak_orb / allowed_orb) if allowed_orb > 0 else 0.0
    exactness = _safe_float(event.get("exactness"), computed_exactness)

    event_weight = _safe_float(event.get("weight"), _PLANET_WEIGHT.get(source_body, _DEFAULT_PLANET_WEIGHT))
    target_relevance = max(
        _target_relevance_for_body(target_body),
        _safe_float(event.get("natal_relevance"), default=0.0),
    )
    structural_importance = _safe_float(
        event.get("structural_importance", event.get("structural_score")),
        default=0.0,
    )
    theme_convergence = _safe_float(event.get("theme_convergence"), default=0.0)
    computed_trigger_strength = round(exactness * event_weight * target_relevance, 5)
    trigger_strength = _safe_float(event.get("trigger_strength"), computed_trigger_strength)
    computed_signal_strength = round(
        trigger_strength
        * (1.0 + min(0.20, structural_importance * 0.20))
        * (1.0 + min(0.12, theme_convergence * 0.12)),
        5,
    )
    signal_strength = _safe_float(event.get("signal_strength"), computed_signal_strength)

    start_dt = _coerce_datetime(event.get("entry_datetime") or event.get("start_datetime"))
    peak_dt  = _coerce_datetime(event.get("peak_datetime"))
    end_dt   = _coerce_datetime(event.get("leave_datetime") or event.get("end_datetime"))

    if peak_dt is None:
        return None

    if start_dt is None:
        start_dt = peak_dt
    if end_dt is None:
        end_dt = peak_dt

    method_family = _normalize_method_family(event_type)
    event_kind = _normalize_event_kind(event_type, event)
    independence_group = str(event.get("independence_group") or _independence_group_for_family(method_family))
    activation_route = str(event.get("activation_route") or _activation_route_for_signal(method_family, event_kind, target_body))

    signal = {
        "signal_id":         f"sig_{event_type[:3]}_{index:04d}",
        "method_family":     method_family,
        "event_kind":        event_kind,
        "independence_group": independence_group,
        "activation_route":  activation_route,
        "source_event_type": event_type,
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
        "cycle_id":          str(event.get("cycle_id") or "").strip(),
        "contact_count":     int(event.get("contact_count", 0) or 0),
        "multiple_exact_passes": bool(event.get("multiple_exact_passes")),
        "start_date":        _to_date(start_dt),
        "peak_date":         _to_date(peak_dt),
        "end_date":          _to_date(end_dt),
        "clock_role":        str(event.get("clock_role") or ""),
        "temporal_precision": str(event.get("temporal_precision") or ""),
        "exact_dates":       [_to_date(dt) for dt in event.get("exact_datetimes", []) if isinstance(dt, datetime)],
        "report_surface_visibility": event.get("report_surface_visibility") or [],
        "calculation_trace": {
            "natal_longitude": event.get("natal_longitude"),
            "formula_version": event.get("formula_version"),
            "policy_version": event.get("policy_version"),
        },
    }
    operation_profile, operation_basis, dominant_operation = _compute_signal_operation_profile(signal)
    epistemic_confidence, confidence_components, confidence_state, angle_eligibility = _compute_signal_epistemic_confidence(
        signal,
        birth_time_status=birth_time_status,
    )
    signal.update({
        "operation_profile": operation_profile,
        "operation_basis": operation_basis,
        "dominant_operation": dominant_operation,
        "epistemic_confidence": _safe_float(event.get("confidence"), epistemic_confidence),
        "confidence_components": event.get("confidence_components") or confidence_components,
        "confidence_state": confidence_state,
        "angle_eligibility": angle_eligibility,
    })
    return signal


def _proprietary_event_to_signal(event: dict, index: int, policy: Any) -> dict | None:
    formula_name = str(event.get("formula_name") or "").strip().upper()
    source_body = str(event.get("transit_planet") or "")
    target_body = str(event.get("natal_target") or "")
    aspect = str(event.get("aspect") or "")
    peak_dt = _coerce_datetime(event.get("peak_datetime"))
    start_dt = _coerce_datetime(event.get("entry_datetime")) or peak_dt
    end_dt = _coerce_datetime(event.get("leave_datetime")) or peak_dt
    if peak_dt is None:
        return None

    source_record = policy.record_for(source_body)
    target_record = policy.record_for(target_body)
    if source_record is not None and not policy.source_eligible(
        source_body,
        "transit",
        aspect=aspect,
        target_body=target_body,
    ):
        return None
    if target_record is not None and not policy.target_eligible(target_body, "transit"):
        return None

    exactness = max(
        0.0,
        1.0 - _safe_float(event.get("orb"), 0.0) / _safe_float(event.get("orb_limit"), _DEFAULT_ORB),
    )
    event_weight = _safe_float(event.get("weight"), 1.0)
    target_relevance = max(
        _target_relevance_for_body(target_body),
        policy.target_weight(target_body) if target_record is not None else 0.0,
    )
    trigger_strength = _bounded(_safe_float(event.get("combined_intensity_score", event.get("score", 0.0)), 0.0))
    if trigger_strength == 0.0:
        trigger_strength = round(exactness * min(1.0, event_weight) * target_relevance, 5)

    topic_keys = _merged_policy_list(policy, "topic_keys", source_body, target_body)
    domain_keys = _merged_policy_list(policy, "domain_keys", source_body, target_body)
    participants = [
        name for name in (source_body, target_body)
        if policy.record_for(name) is not None
    ]
    report_surfaces = []
    for name in participants:
        for surface in policy.report_surface_permissions(name):
            if surface not in report_surfaces:
                report_surfaces.append(surface)

    signal = {
        "signal_id": f"sig_prp_{index:04d}",
        "method_family": "PROPRIETARY_TRANSIT",
        "event_kind": formula_name.lower() if formula_name else "proprietary_transit",
        "independence_group": "proprietary_transit_family",
        "activation_route": _proprietary_activation_route(target_body),
        "source_event_type": "proprietary_transit",
        "source_body": source_body,
        "target_body": target_body,
        "aspect": aspect,
        "orb": _safe_float(event.get("orb"), 0.0),
        "allowed_orb": _safe_float(event.get("orb_limit"), _DEFAULT_ORB),
        "exactness": round(exactness, 5),
        "event_weight": event_weight,
        "target_relevance": target_relevance,
        "trigger_strength": trigger_strength,
        "signal_strength": trigger_strength,
        "structural_importance": 0.0,
        "theme_convergence": 0.0,
        "routing_state": "",
        "pass_sequence": "",
        "cycle_id": str(event.get("formula_name") or ""),
        "contact_count": 1,
        "multiple_exact_passes": False,
        "start_date": _to_date(start_dt),
        "peak_date": _to_date(peak_dt),
        "end_date": _to_date(end_dt),
        "topic_keys": topic_keys,
        "domain_keys": domain_keys,
        "asteroid_registry_version": policy.policy_version,
        "asteroid_policy": {
            "participants": participants,
            "source_validation_category": policy.validation_category(source_body) if source_record is not None else "",
            "target_validation_category": policy.validation_category(target_body) if target_record is not None else "",
            "report_surface_visibility": report_surfaces or ["internal_rd"],
            "formula_group": formula_name,
            "formula_label": event.get("formula_label") or "",
            "raw_score": _safe_float(event.get("raw_score"), 0.0),
            "combined_intensity_score": trigger_strength,
        },
    }
    operation_profile, operation_basis, dominant_operation = _compute_signal_operation_profile(signal)
    signal.update({
        "operation_profile": operation_profile,
        "operation_basis": operation_basis,
        "dominant_operation": dominant_operation,
        "epistemic_confidence": 0.75,
        "confidence_components": {
            "calculation_integrity": 1.0,
            "birth_time_support": 1.0,
            "orb_support": round(exactness, 5),
            "method_maturity": 0.75,
            "report_surface_gated": 1.0,
        },
        "confidence_state": "moderate",
        "angle_eligibility": target_body in _ANGLE_TARGETS,
    })
    return signal


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

        memory_charge, memory_state = _window_memory(active_sigs, signals, peak_d, gradient)
        coherence, semantic_profile, dominant_operation, semantic_state, semantic_diagnostics = _window_semantic_metrics(active_sigs)
        interpretive_tags = []
        if semantic_state:
            interpretive_tags.append(f"semantic_{semantic_state}")
        if dominant_operation:
            interpretive_tags.append(f"op_{dominant_operation}")

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
            # Phase 3+ diagnostics
            "coherence":                    coherence,
            "semantic_profile":             semantic_profile,
            "dominant_operation":           dominant_operation,
            "semantic_state":               semantic_state,
            "semantic_diagnostics":         semantic_diagnostics,
            "memory":                       memory_charge,
            "memory_state":                 memory_state,
            "activation_key":               memory_state.get("activation_key", ""),
            "pass_state":                   memory_state.get("pass_state", ""),
            "lifecycle_route":              memory_state.get("lifecycle_route", ""),
            "interpretive_tags":            interpretive_tags,
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


def _normalize_method_family(event_type: str) -> str:
    if event_type in {"transit", "station", "ingress"}:
        return "TRANSIT"
    if event_type == "proprietary_transit":
        return "PROPRIETARY_TRANSIT"
    if event_type in {"eclipse", "lunation", "new_moon", "full_moon"}:
        return "LUNATION"
    if event_type == "return":
        return "RETURN"
    if event_type == "progression":
        return "PROGRESSION"
    if event_type == "solar_arc":
        return "SOLAR_ARC"
    return event_type.upper() if event_type else "UNKNOWN"


def _predictive_birth_time_status(natal_payload: dict) -> str:
    user_profile = natal_payload.get("user_profile") or {}
    if bool(natal_payload.get("simple_mode") or user_profile.get("simple_mode")):
        return "unknown"

    raw_state = str(
        user_profile.get("birth_time_state")
        or user_profile.get("birth_time_confidence")
        or natal_payload.get("birth_time_state")
        or ""
    ).strip().lower()
    if "approx" in raw_state:
        return "approximate"
    if "unknown" in raw_state:
        return "unknown"
    return "exact"


def _normalize_event_kind(event_type: str, event: dict) -> str:
    if event_type == "transit":
        return "ASPECT"
    if event_type == "station":
        return "STATION"
    if event_type == "ingress":
        return "INGRESS"
    if event_type == "eclipse":
        return "ECLIPSE"
    if event_type == "return":
        return str(event.get("method_variant") or "exact_return")
    if event_type == "solar_arc":
        return str(event.get("method_variant") or "solar_arc_body_aspect")
    if event_type == "progression":
        return str(event.get("method_variant") or "progression_body_aspect")
    if event_type == "lunation":
        subtype = str(event.get("lunation_type") or "").strip().upper()
        return subtype or "LUNATION"
    return event_type.upper() if event_type else "UNKNOWN"


def _independence_group_for_family(method_family: str) -> str:
    return {
        "TRANSIT": "transit_clock",
        "PROPRIETARY_TRANSIT": "proprietary_transit_family",
        "LUNATION": "lunar_phase_clock",
        "RETURN": "return_clock",
        "PROGRESSION": "progression_clock",
        "SOLAR_ARC": "solar_arc_clock",
    }.get(method_family, "unknown_clock")


def _activation_route_for_signal(method_family: str, event_kind: str, target_body: str) -> str:
    if method_family == "TRANSIT":
        if event_kind == "STATION":
            return "stationary_transit"
        if event_kind == "INGRESS":
            return "ingress_to_house"
        if target_body in _ANGLE_TARGETS:
            return "transit_to_angle"
        if target_body.isdigit():
            return "house_context"
        return "transit_to_body"

    if method_family == "PROPRIETARY_TRANSIT":
        return _proprietary_activation_route(target_body)

    if method_family == "LUNATION":
        if target_body in _ANGLE_TARGETS:
            return "lunation_to_angle"
        return "lunation_to_body"

    if method_family == "RETURN":
        return "return_moment"

    if method_family == "PROGRESSION":
        if target_body in _ANGLE_TARGETS:
            return "progression_to_angle"
        return "progression_to_body"

    if method_family == "SOLAR_ARC":
        if target_body in _ANGLE_TARGETS:
            return "solar_arc_to_angle"
        return "solar_arc_to_body"

    return "unspecified_route"


def _proprietary_asteroid_rd_enabled(options: dict | None) -> bool:
    if isinstance(options, dict):
        for key in ("enable_asteroid_rd", "include_proprietary_asteroids", "include_proprietary_transits"):
            if key in options:
                return _truthy(options.get(key))
    return _truthy(os.environ.get("EO_ASTEROID_RD")) or _truthy(os.environ.get("EO_PREDICTIVE_ASTEROID_RD"))


def _proprietary_activation_route(target_body: str) -> str:
    if target_body in _ANGLE_TARGETS:
        return "proprietary_transit_to_angle"
    if str(target_body).isdigit():
        return "proprietary_transit_to_house"
    return "proprietary_transit_to_body"


def _target_relevance_for_body(target_body: str) -> float:
    if target_body in _TARGET_RELEVANCE:
        return _TARGET_RELEVANCE[target_body]
    try:
        from engine.asteroid_policy import load_asteroid_policy

        policy = load_asteroid_policy()
        if policy.record_for(target_body) is not None:
            return policy.target_weight(target_body)
    except Exception:
        pass
    return _DEFAULT_RELEVANCE


def _merged_policy_list(policy: Any, accessor_name: str, *body_names: str) -> list[str]:
    merged: list[str] = []
    accessor = getattr(policy, accessor_name)
    for body_name in body_names:
        if policy.record_for(body_name) is None:
            continue
        for item in accessor(body_name):
            if item not in merged:
                merged.append(item)
    return merged


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _bounded(value: float, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def apply_signed_bias(base: float, bias: float, influence: float = 0.35) -> float:
    """Apply bounded bias without letting an operation axis leave [0, 1]."""
    safe_base = min(1.0, max(0.0, base))
    safe_bias = min(1.0, max(-1.0, bias))
    if safe_bias >= 0:
        return safe_base + influence * safe_bias * (1.0 - safe_base)
    return safe_base + influence * safe_bias * safe_base


def _target_substrate(target_body: str) -> str:
    if target_body in _ANGLE_TARGETS:
        return "angle"
    if target_body in {"Sun", "Moon"}:
        return "luminary"
    if target_body in {"Mercury", "Venus", "Mars"}:
        return "personal"
    if target_body in {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron"}:
        return "social_outer"
    if target_body.isdigit():
        return "house"
    if target_body in {"North_Node", "Lilith_BML", "Vertex"}:
        return "specialist"
    try:
        from engine.asteroid_policy import load_asteroid_policy

        if load_asteroid_policy().record_for(target_body) is not None:
            return "specialist"
    except Exception:
        pass
    if target_body in {"Kassandra", "Aletheia", "Destinn", "Karma", "Kaali", "Medea", "Hermes", "Chaos"}:
        return "specialist"
    return "generic"


def _aspect_family(aspect: str) -> str:
    label = str(aspect or "").strip().upper()
    return label if label in _ASPECT_OPERATION_BIAS else "GENERIC"


def _compute_signal_operation_profile(signal: dict) -> tuple[dict[str, float], dict[str, str], str]:
    base_profile = _SOURCE_OPERATION_BASE.get(signal.get("source_body", ""), _DEFAULT_SOURCE_OPERATION_BASE)
    target_class = _target_substrate(str(signal.get("target_body") or ""))
    target_bias = _TARGET_SUBSTRATE_BIAS.get(target_class, _TARGET_SUBSTRATE_BIAS["generic"])
    aspect_family = _aspect_family(str(signal.get("aspect") or ""))
    aspect_bias = _ASPECT_OPERATION_BIAS.get(aspect_family, _ASPECT_OPERATION_BIAS["GENERIC"])
    method_family = str(signal.get("method_family") or "UNKNOWN")
    method_multiplier = _METHOD_OPERATION_MULTIPLIER.get(method_family, _METHOD_OPERATION_MULTIPLIER["UNKNOWN"])
    magnitude = float(signal.get("signal_strength", signal.get("trigger_strength", 0.0)) or 0.0)

    operation_profile: dict[str, float] = {}
    for op in _OPERATION_AXES:
        biased = apply_signed_bias(float(base_profile.get(op, 0.0)), float(aspect_bias.get(op, 0.0)))
        biased = apply_signed_bias(biased, float(target_bias.get(op, 0.0)), influence=0.28)
        weighted = magnitude * biased * float(method_multiplier.get(op, 1.0))
        operation_profile[op] = round(weighted, 5)

    dominant_operation = max(operation_profile, key=operation_profile.get) if operation_profile else ""
    operation_basis = {
        "source_profile": str(signal.get("source_body") or "generic"),
        "target_substrate": target_class,
        "aspect_family": aspect_family,
        "method_behavior": method_family,
    }
    return operation_profile, operation_basis, dominant_operation


def compute_epistemic_confidence(
    availability_gate: float,
    record_integrity: float,
    calculation_integrity: float,
    relation_robustness: float,
) -> float:
    """Bounded scaffold for whether a predictive edge is trustworthy enough to inspect."""
    safe = lambda value: min(1.0, max(0.0, float(value)))
    return round(safe(availability_gate) * safe(record_integrity) * safe(calculation_integrity) * safe(relation_robustness), 4)


def _simulate_target_uncertainty(target_body: str, birth_time_status: str, allowed_orb: float) -> tuple[float, str]:
    """
    Provisional sampling heuristic for natal-address uncertainty.
    Estimates whether a signal's required orb window is larger than the 
    positional uncertainty of its target.
    """
    if birth_time_status == "exact":
        return 1.0, "exact_target_known"
        
    uncertainty_hours = 1.0 if birth_time_status == "approximate" else 24.0
    
    if target_body in _ANGLE_TARGETS:
        shift_per_hour = 15.0
    elif target_body == "Moon":
        shift_per_hour = 0.55
    else:
        shift_per_hour = 0.05  # Sun, etc.
        
    positional_uncertainty = shift_per_hour * uncertainty_hours
    
    # If the target could be anywhere in a 15-degree band, but the orb is 3 degrees,
    # the robustness of the transit claim is severely degraded.
    # We use a simple ratio of (aspect band) / (uncertainty band), capped at 1.0.
    aspect_band = max(0.1, allowed_orb * 2.0)
    
    if positional_uncertainty <= aspect_band * 0.25:
        return 1.0, "uncertainty_negligible"
        
    robustness = aspect_band / positional_uncertainty
    return float(max(0.0, min(1.0, robustness))), "interval_sampled_uncertainty"


def _compute_signal_epistemic_confidence(signal: dict, birth_time_status: str) -> tuple[float, dict[str, float | str], str, str]:
    target_body = str(signal.get("target_body") or "")
    is_angle_target = target_body in _ANGLE_TARGETS
    exactness = min(1.0, max(0.0, float(signal.get("exactness", 0.0) or 0.0)))
    allowed_orb = float(signal.get("allowed_orb", 3.0) or 3.0)

    if is_angle_target and birth_time_status == "unknown":
        availability_gate = 0.0
        angle_eligibility = "withheld_without_exact_birth_time"
    else:
        availability_gate = 1.0
        angle_eligibility = "eligible"

    record_integrity = {
        "exact": 1.0,
        "approximate": 0.78,
        "unknown": 0.64,
    }.get(birth_time_status, 0.64)
    calculation_integrity = 1.0 if str(signal.get("method_family") or "") in {"TRANSIT", "LUNATION", "RETURN", "PROGRESSION", "SOLAR_ARC"} else 0.90
    
    uncertainty_modifier, sampling_state = _simulate_target_uncertainty(target_body, birth_time_status, allowed_orb)
    relation_robustness = round(min(1.0, 0.55 + exactness * 0.45) * uncertainty_modifier, 4)
    
    confidence = compute_epistemic_confidence(
        availability_gate=availability_gate,
        record_integrity=record_integrity,
        calculation_integrity=calculation_integrity,
        relation_robustness=relation_robustness,
    )

    if availability_gate == 0.0:
        confidence_state = "withheld_angle_target"
    elif confidence >= 0.85:
        confidence_state = "supported"
    elif confidence >= 0.60:
        confidence_state = "provisional"
    else:
        confidence_state = "weak"

    components: dict[str, float | str] = {
        "availability_gate": availability_gate,
        "record_integrity": record_integrity,
        "calculation_integrity": calculation_integrity,
        "relation_robustness": relation_robustness,
        "sampling_state": sampling_state,
    }
    return confidence, components, confidence_state, angle_eligibility


def _operation_compatibility(op_a: str, op_b: str) -> float:
    if not op_a or not op_b:
        return 0.50
    if op_a == op_b:
        return 1.0
    if op_a == "reveal" or op_b == "reveal":
        counterpart = op_b if op_a == "reveal" else op_a
        return 0.72 if counterpart in _CONSTRUCTIVE_OPERATIONS else 0.58
    if op_a in _CONSTRUCTIVE_OPERATIONS and op_b in _CONSTRUCTIVE_OPERATIONS:
        return 0.82
    if op_a in _DISSOLVING_OPERATIONS and op_b in _DISSOLVING_OPERATIONS:
        return 0.74
    return 0.24


def _window_semantic_metrics(active_sigs: list[dict]) -> tuple[float | None, dict[str, float], str, str, dict[str, Any]]:
    semantic_sigs = [sig for sig in active_sigs if isinstance(sig.get("operation_profile"), dict) and sig.get("operation_profile")]
    if not semantic_sigs:
        return None, {}, "", "", {}

    profile_totals = {op: 0.0 for op in _OPERATION_AXES}
    confidence_sum = 0.0
    for sig in semantic_sigs:
        for op in _OPERATION_AXES:
            profile_totals[op] += float((sig.get("operation_profile") or {}).get(op, 0.0) or 0.0)
        confidence_sum += float(sig.get("epistemic_confidence", 0.0) or 0.0)

    dominant_operation = max(profile_totals, key=profile_totals.get) if profile_totals else ""
    total_mass = sum(profile_totals.values())
    semantic_profile = {
        op: round((value / total_mass), 5) if total_mass > 0 else 0.0
        for op, value in profile_totals.items()
    }

    if len(semantic_sigs) == 1:
        coherence = 1.0
        compatible_pairs = 0
        conflicting_pairs = 0
        pair_count = 0
    else:
        compatibility_sum = 0.0
        weight_sum = 0.0
        compatible_pairs = 0
        conflicting_pairs = 0
        pair_count = 0
        for idx, sig_a in enumerate(semantic_sigs):
            for sig_b in semantic_sigs[idx + 1:]:
                op_a = str(sig_a.get("dominant_operation") or "")
                op_b = str(sig_b.get("dominant_operation") or "")
                compatibility = _operation_compatibility(op_a, op_b)
                weight = max(
                    0.0001,
                    float(sig_a.get("signal_strength", sig_a.get("trigger_strength", 0.0)) or 0.0)
                    * float(sig_b.get("signal_strength", sig_b.get("trigger_strength", 0.0)) or 0.0),
                )
                compatibility_sum += compatibility * weight
                weight_sum += weight
                pair_count += 1
                if compatibility >= 0.65:
                    compatible_pairs += 1
                elif compatibility <= 0.35:
                    conflicting_pairs += 1
        coherence = round((compatibility_sum / weight_sum), 4) if weight_sum > 0 else 0.5

    constructive_mass = sum(profile_totals.get(op, 0.0) for op in _CONSTRUCTIVE_OPERATIONS)
    dissolving_mass = sum(profile_totals.get(op, 0.0) for op in _DISSOLVING_OPERATIONS)
    
    if total_mass > 0:
        polarity = round((2.0 * min(constructive_mass, dissolving_mass)) / total_mass, 4)
    else:
        polarity = 0.0
        
    if dominant_operation in _CONSTRUCTIVE_OPERATIONS:
        coalition = constructive_mass
        counterforce = dissolving_mass
    elif dominant_operation in _DISSOLVING_OPERATIONS:
        coalition = dissolving_mass
        counterforce = constructive_mass
    else:
        coalition = profile_totals.get(dominant_operation, 0.0)
        counterforce = total_mass - coalition
        
    coalition_ratio = round(coalition / total_mass, 4) if total_mass > 0 else 0.0
    counterforce_ratio = round(counterforce / total_mass, 4) if total_mass > 0 else 0.0
    
    complexity = 0.0
    for p in semantic_profile.values():
        if p > 0:
            complexity -= p * math.log(p)
    complexity = round(complexity, 4)

    if polarity >= 0.60 or counterforce_ratio >= 0.40:
        semantic_state = "opposed"
    elif coherence >= 0.75 and counterforce_ratio < 0.20:
        semantic_state = "reinforcing"
    elif coherence < 0.45:
        semantic_state = "frictional"
    else:
        semantic_state = "mixed"

    diagnostics = {
        "participating_signal_count": len(semantic_sigs),
        "pair_count": pair_count,
        "compatible_pairs": compatible_pairs,
        "conflicting_pairs": conflicting_pairs,
        "average_signal_confidence": round(confidence_sum / len(semantic_sigs), 4),
        "polarity": polarity,
        "coalition": coalition_ratio,
        "counterforce": counterforce_ratio,
        "complexity": complexity,
    }
    return coherence, semantic_profile, dominant_operation, semantic_state, diagnostics


def _episode_activation_key(signal: dict) -> str:
    return ":".join(
        (
            str(signal.get("independence_group") or ""),
            str(signal.get("method_family") or ""),
            str(signal.get("event_kind") or ""),
            str(signal.get("source_body") or ""),
            str(signal.get("target_body") or ""),
            str(signal.get("aspect") or ""),
            str(signal.get("activation_route") or ""),
        )
    )


def calculate_exit_orb(enter_orb: float) -> float:
    """Hysteresis constraint: exit orb is always slightly larger than entry orb."""
    safe_enter_orb = max(0.0, enter_orb)
    return safe_enter_orb + max(0.10, safe_enter_orb * 0.08)


def compute_next_phase_state(
    current_state: str,
    current_orb: float,
    enter_orb: float,
    is_retrograde: bool,
    prior_exact_hit: bool,
    exactness_threshold: float = _FSM_EXACTNESS_THRESHOLD,
) -> str:
    """
    Strict Finite State Machine for transit-like predictive episodes.

    Once a signal breaches APPROACH, it cannot flicker back to PRELUDE while
    still inside the hysteresis band. Residual field is only reachable after a
    post-exactness state has been achieved.
    """
    state = (current_state or "PRELUDE").upper()
    if state not in ALLOWED_STATES:
        state = "PRELUDE"

    safe_orb = max(0.0, current_orb)
    safe_enter_orb = max(0.0, enter_orb)
    safe_exactness = max(0.0, exactness_threshold)
    exit_orb = calculate_exit_orb(safe_enter_orb)

    if safe_orb > exit_orb:
        if state in {"RESOLUTION", "AFTERMATH", "RESIDUAL_FIELD"}:
            return "RESIDUAL_FIELD"
        return "PRELUDE"

    if safe_orb <= safe_exactness:
        return "EXACTNESS"

    if safe_orb <= safe_enter_orb and state == "PRELUDE":
        return "APPROACH"

    if state == "EXACTNESS" and safe_orb > safe_exactness:
        return "AFTERMATH"

    if is_retrograde and prior_exact_hit and safe_orb <= exit_orb:
        return "RETROGRADE_REVIEW"

    if not is_retrograde and prior_exact_hit and state in {"AFTERMATH", "RETROGRADE_REVIEW"}:
        return "RESOLUTION"

    return state


def _signal_is_retrograde(signal: dict, position: int, total: int) -> bool:
    """Infer whether a historical pass should be treated as retrograde."""
    explicit = signal.get("is_retrograde", signal.get("retrograde"))
    if explicit is not None:
        return bool(explicit)

    routing_state = str(signal.get("routing_state") or "").strip().lower()
    if "retro" in routing_state:
        return True

    pass_sequence = str(signal.get("pass_sequence") or "").strip().lower()
    if pass_sequence == "retrograde_three_pass":
        return total >= 3 and position == 1

    return False


def _phase_state_for_history(history: list[dict]) -> str:
    """Resolve the current phase state by replaying signal history chronologically."""
    state = "PRELUDE"
    prior_exact_hit = False

    for idx, sig in enumerate(history):
        current_orb = _safe_float(sig.get("orb"), _safe_float(sig.get("peak_orb"), _safe_float(sig.get("allowed_orb"), 0.0)))
        enter_orb = _safe_float(sig.get("allowed_orb"), max(current_orb, 0.0))
        state = compute_next_phase_state(
            current_state=state,
            current_orb=current_orb,
            enter_orb=enter_orb,
            is_retrograde=_signal_is_retrograde(sig, idx, len(history)),
            prior_exact_hit=prior_exact_hit,
        )
        if state == "EXACTNESS":
            prior_exact_hit = True

    return state


def _lifecycle_route(memory_charge: float, prior_episode_count: int, gradient: str) -> str:
    if memory_charge < 0.35 and prior_episode_count == 0 and gradient == "rising":
        return "emergent"
    if prior_episode_count > 0 and gradient == "rising":
        return "reactivation"
    if memory_charge >= 0.75 and gradient == "plateau":
        return "culminating"
    if memory_charge >= 0.55 and gradient == "releasing":
        return "integrative"
    if memory_charge >= 0.35 and gradient == "releasing":
        return "residual"
    return "active"


def _window_memory(
    active_sigs: list[dict],
    all_signals: list[dict],
    peak_date: date,
    gradient: str,
) -> tuple[float | None, dict[str, Any]]:
    if not active_sigs:
        return None, {}

    anchor = max(
        active_sigs,
        key=lambda sig: (
            sig.get("signal_strength", sig.get("trigger_strength", 0.0)),
            sig.get("trigger_strength", 0.0),
        ),
    )
    activation_key = _episode_activation_key(anchor)
    related = [
        sig for sig in all_signals
        if _episode_activation_key(sig) == activation_key
    ]
    related.sort(key=lambda sig: (sig.get("peak_date", date.min), sig.get("signal_id", "")))

    history = [sig for sig in related if sig.get("peak_date", date.min) <= peak_date]
    prior_episode_count = max(0, len(history) - 1)
    method_weight = _METHOD_WEIGHT_BY_GROUP.get(anchor.get("independence_group", ""), 0.80)

    charge = 0.0
    for sig in history:
        event_peak = sig.get("peak_date", peak_date)
        age_years = max(0.0, (peak_date - event_peak).days / 365.25)
        episode_strength = float(sig.get("signal_strength", sig.get("trigger_strength", 0.0)) or 0.0)
        charge += episode_strength * method_weight * math.exp(-age_years / _MEMORY_DECAY_YEARS)

    memory_charge = round(min(1.0, charge), 4)
    pass_state = _phase_state_for_history(history)
    lifecycle_route = _lifecycle_route(memory_charge, prior_episode_count, gradient)

    return memory_charge, {
        "activation_key": activation_key,
        "first_seen_date": history[0]["peak_date"].isoformat() if history else "",
        "episode_count": len(related),
        "prior_episode_count": prior_episode_count,
        "current_episode_id": f"{activation_key}:episode_{len(history):02d}" if history else "",
        "pass_state": pass_state,
        "component_charge": memory_charge,
        "lifecycle_route": lifecycle_route,
        "formula_version": _PREDICTIVE_FORMULA_VERSION,
    }


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
