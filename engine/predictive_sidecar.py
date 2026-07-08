"""
engine/predictive_sidecar.py - Phase 2 predictive evidence sidecar.

Serializes the current transit-backed predictive evidence into the
`.eo_predictive.json` artifact defined by `phase0/06_sidecar_and_export_contract.md`.
This module is additive: it does not change rendered report prose.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import uuid
from datetime import date, datetime, time, timezone
from typing import Any

from product_versions import write_json


SIDECAR_SCHEMA_VERSION = "phase0.1.1"
FORECAST_EVENT_SCHEMA_VERSION = "phase0.1.0"
PREDICTIVE_SIGNAL_SCHEMA_VERSION = "phase0.1.0"
SIDECAR_WRITER_VERSION = "phase2.0.1"

_POLICY_VERSIONS = {
    "predictive_object_schemas": SIDECAR_SCHEMA_VERSION,
    "asteroid_registry": SIDECAR_SCHEMA_VERSION,
    "method_charters": SIDECAR_SCHEMA_VERSION,
    "convergence_protocol": SIDECAR_SCHEMA_VERSION,
    "candidate_protocol": SIDECAR_SCHEMA_VERSION,
    "component_score_weights": SIDECAR_SCHEMA_VERSION,
    "detector_thresholds": SIDECAR_SCHEMA_VERSION,
}

_METHOD_POLICY_VERSIONS = {
    "returns": SIDECAR_SCHEMA_VERSION,
    "solar_arc": SIDECAR_SCHEMA_VERSION,
    "progressions": SIDECAR_SCHEMA_VERSION,
    "profections": SIDECAR_SCHEMA_VERSION,
    "lots": SIDECAR_SCHEMA_VERSION,
    "zodiacal_releasing": SIDECAR_SCHEMA_VERSION,
}

_STRUCTURAL_BODIES = frozenset({"Saturn", "Uranus", "Neptune", "Pluto"})
_ANGLE_TARGETS = frozenset({"ASC", "Ascendant", "MC", "Midheaven", "IC", "Imum Coeli", "DSC", "Descendant", "Vertex"})
_LUMINARIES = frozenset({"Sun", "Moon"})
_PLANETS = frozenset({"Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron"})
_NODES = frozenset({"North_Node", "South_Node"})
_CALCULATED_POINTS = frozenset({"Lilith_BML"})


def write_predictive_sidecar_for_report(
    *,
    output_path: str,
    report_type: str,
    birth_data: dict,
    payload: dict,
    predictive_results: dict,
    report_start: datetime,
    report_end: datetime,
    engine_command: str | None = None,
) -> str:
    """Builds and writes the predictive sidecar next to the rendered report."""
    sidecar_path = _sidecar_path_for_output(output_path)
    sidecar = build_predictive_sidecar(
        report_type=report_type,
        birth_data=birth_data,
        payload=payload,
        predictive_results=predictive_results,
        report_start=report_start,
        report_end=report_end,
        engine_command=engine_command,
    )
    write_json(sidecar_path, _json_safe(sidecar))
    return sidecar_path


def build_predictive_sidecar(
    *,
    report_type: str,
    birth_data: dict,
    payload: dict,
    predictive_results: dict,
    report_start: datetime,
    report_end: datetime,
    engine_command: str | None = None,
) -> dict:
    """Returns a Phase 0-shaped predictive sidecar dictionary."""
    generated_at = _utc_now()
    report_run_id = f"run_{uuid.uuid4().hex[:8]}"
    policy_versions = dict(_POLICY_VERSIONS)
    natal_snapshot_id = _natal_snapshot_id(payload, birth_data, policy_versions)
    formula_version = str(predictive_results.get("formula_version") or "")

    source_signals = [
        signal for signal in predictive_results.get("signals", [])
        if isinstance(signal, dict)
    ]
    asteroid_names = _custom_asteroid_names(payload)
    raw_events = [
        _forecast_event_from_signal(signal, index, generated_at, asteroid_names)
        for index, signal in enumerate(source_signals)
    ]
    event_id_by_signal_id = {
        signal.get("signal_id"): event["event_id"]
        for signal, event in zip(source_signals, raw_events)
        if signal.get("signal_id")
    }
    predictive_signals = [
        _predictive_signal_from_signal(signal, event_id_by_signal_id, formula_version, asteroid_names)
        for signal in source_signals
    ]

    daily_series = _daily_series_with_provenance(
        predictive_results.get("daily_series", []),
        predictive_signals,
        event_id_by_signal_id,
    )

    return {
        "sidecar_version": SIDECAR_SCHEMA_VERSION,
        "sidecar_schema_version": SIDECAR_SCHEMA_VERSION,
        "report_run": {
            "report_run_id": report_run_id,
            "report_type": report_type,
            "report_start": _iso_datetime(report_start),
            "report_end": _iso_datetime(report_end),
            "generated_at": _iso_datetime(generated_at),
            "engine_version": "eo_generator_phase2",
            "git_commit": _git_commit(),
            "engine_command": engine_command or "",
        },
        "natal_snapshot": _natal_snapshot(payload, birth_data, natal_snapshot_id),
        "environment": _environment(formula_version),
        "policy_versions": policy_versions,
        "natal_promise_anchors": [],
        "raw_events": raw_events,
        "predictive_signals": predictive_signals,
        "daily_series": daily_series,
        "time_lord_periods": _json_safe(predictive_results.get("time_lord_periods", [])),
        "chapters": [],
        "candidates": [],
        "rejected_candidates": [],
        "convergence_composition": [],
        "detector_thresholds": _detector_thresholds(),
        "asteroid_diagnostics": _asteroid_diagnostics(payload, raw_events, predictive_signals),
        "debug": {
            "predictive_engine": predictive_results.get("debug") or {},
            "phase2_note": "Phase 2 serializes current transit-backed predictive evidence only; advanced clocks are not implemented here.",
        },
        "provenance": {
            "scanner_versions": {
                "compute_predictive_windows": formula_version,
                "scan_transit_windows": "current_runtime",
                "scan_house_ingresses": "current_runtime",
                "scan_stations": "current_runtime",
                "scan_eclipses": "current_runtime",
                "scan_lunations": "current_runtime",
                "scan_proprietary_forecast_windows": _proprietary_scanner_state(predictive_results),
                "scan_return_moments": _debug_scanner_state(predictive_results, "return_signal_count", "wired_phase4"),
                "annual_profections": _debug_scanner_state(predictive_results, "annual_profection_period_count", "wired_phase4"),
                "scan_solar_arc": _debug_scanner_state(predictive_results, "solar_arc_signal_count", "wired_phase5"),
                "scan_secondary_progressions": _debug_scanner_state(predictive_results, "progression_signal_count", "wired_phase5"),
                "compute_lots": _debug_scanner_state(predictive_results, "zr_signal_count", "wired_phase6"),
                "zodiacal_releasing": _debug_scanner_state(predictive_results, "zr_signal_count", "wired_phase6"),
            },
            "sidecar_writer_version": SIDECAR_WRITER_VERSION,
            "sidecar_written_at": _iso_datetime(generated_at),
        },
    }


def _forecast_event_from_signal(signal: dict, index: int, emitted_at: datetime, asteroid_names: set[str]) -> dict:
    method_family = str(signal.get("method_family") or "UNKNOWN")
    method_variant = str(signal.get("event_kind") or signal.get("source_event_type") or "unknown")
    source_body = str(signal.get("source_body") or "")
    target_body = str(signal.get("target_body") or "")
    peak_at = _signal_datetime(signal.get("peak_date"))
    start_at = _signal_datetime(signal.get("start_date")) or peak_at
    end_at = _signal_datetime(signal.get("end_date")) or peak_at
    peak_at = peak_at or start_at or emitted_at
    event_id = _forecast_event_id(method_family, source_body, target_body, method_variant, peak_at, index)
    missing_fields = []
    if not source_body:
        missing_fields.append("source_body")
    if not peak_at:
        missing_fields.append("peak_at")

    orb = _optional_float(signal.get("orb"))
    phase = str(signal.get("pass_sequence") or signal.get("routing_state") or method_variant or "").strip() or None

    return {
        "schema_version": FORECAST_EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "method_family": method_family,
        "method_variant": method_variant,
        "clock_role": _clock_role_for_signal(signal),
        "source_body": source_body,
        "source_kind": _body_kind(source_body, asteroid_names),
        "target_body": target_body or None,
        "target_kind": _target_kind(target_body, asteroid_names),
        "natal_anchor_ids": [],
        "topic_keys": _string_list(signal.get("topic_keys")),
        "domain_keys": _string_list(signal.get("domain_keys")),
        "start_at": _iso_datetime(start_at),
        "peak_at": _iso_datetime(peak_at),
        "end_at": _iso_datetime(end_at),
        "exact_at": [_iso_datetime(_signal_datetime(value)) for value in signal.get("exact_dates", []) if _signal_datetime(value)],
        "orb": orb,
        "distance": None,
        "phase": phase,
        "event_strength": _bounded_float(signal.get("signal_strength", signal.get("trigger_strength", 0.0))),
        "strength_components": {
            "exactness": _bounded_float(signal.get("exactness", 0.0)),
            "event_weight": _bounded_float(signal.get("event_weight", 0.0)),
            "target_relevance": _bounded_float(signal.get("target_relevance", 0.0)),
            "structural_importance": _bounded_float(signal.get("structural_importance", 0.0)),
            "theme_convergence": _bounded_float(signal.get("theme_convergence", 0.0)),
            "method_multiplier": 1.0,
            "asteroid_specificity": 1.0 if _is_asteroid_participant(source_body, target_body, asteroid_names) else 0.0,
        },
        "temporal_precision": str(signal.get("temporal_precision") or "") or _temporal_precision(start_at, peak_at, end_at),
        "independence_group": str(signal.get("independence_group") or "transit_family"),
        "activation_route": str(signal.get("activation_route") or "transit_to_body"),
        "asteroid_participants": _asteroid_participants(source_body, target_body, asteroid_names),
        "confidence": _bounded_float(signal.get("epistemic_confidence", 0.0)),
        "confidence_components": _dict_float(signal.get("confidence_components") or {}),
        "calculation_trace": {
            "adapter": "engine.predictive_sidecar._forecast_event_from_signal",
            "source_signal_id": signal.get("signal_id"),
            "source_event_type": signal.get("source_event_type"),
            "allowed_orb": signal.get("allowed_orb"),
            "missing_fields": missing_fields,
            "asteroid_policy": signal.get("asteroid_policy") or {},
            "method_trace": signal.get("calculation_trace") or {},
            "notes": "Phase 2 adapts current predictive signals into ForecastEvent shape; raw scanner-event retention deepens in later phases.",
        },
        "report_surface_visibility": _signal_report_surface_visibility(signal, source_body, target_body, asteroid_names),
        "provenance": {
            "scanner": "engine.predictive_engine",
            "scanner_version": str(signal.get("formula_version") or ""),
            "emitted_at": _iso_datetime(emitted_at),
        },
    }


def _predictive_signal_from_signal(
    signal: dict,
    event_id_by_signal_id: dict[str, str],
    formula_version: str,
    asteroid_names: set[str],
) -> dict:
    signal_id = str(signal.get("signal_id") or _hash_id("sig", signal))
    source_event_id = event_id_by_signal_id.get(signal_id)
    method_family = str(signal.get("method_family") or "UNKNOWN")
    source_body = str(signal.get("source_body") or "")
    target_body = str(signal.get("target_body") or "")

    return {
        "schema_version": PREDICTIVE_SIGNAL_SCHEMA_VERSION,
        "signal_id": signal_id,
        "source_event_ids": [source_event_id] if source_event_id else [],
        "method_family": method_family,
        "independence_group": str(signal.get("independence_group") or "transit_family"),
        "activation_route": str(signal.get("activation_route") or "transit_to_body"),
        "signal_role": _signal_role(signal),
        "source_body": source_body,
        "target_body": target_body or None,
        "aspect": signal.get("aspect") or None,
        "natal_anchor_ids": [],
        "topic_keys": _string_list(signal.get("topic_keys")),
        "domain_keys": _string_list(signal.get("domain_keys")),
        "asteroid_participants": _asteroid_participants(source_body, target_body, asteroid_names),
        "start_date": _iso_date(signal.get("start_date")),
        "peak_date": _iso_date(signal.get("peak_date")),
        "end_date": _iso_date(signal.get("end_date")),
        "trigger_strength": _bounded_float(signal.get("trigger_strength", 0.0)),
        "signal_strength": _bounded_float(signal.get("signal_strength", signal.get("trigger_strength", 0.0))),
        "structural_importance": _bounded_float(signal.get("structural_importance", 0.0)),
        "theme_convergence": _bounded_float(signal.get("theme_convergence", 0.0)),
        "operation_profile": _dict_float(signal.get("operation_profile") or {}),
        "operation_basis": signal.get("operation_basis") or {},
        "dominant_operation": str(signal.get("dominant_operation") or ""),
        "epistemic_confidence": _bounded_float(signal.get("epistemic_confidence", 0.0)),
        "confidence_components": _dict_float(signal.get("confidence_components") or {}),
        "confidence_state": str(signal.get("confidence_state") or "low"),
        "angle_eligibility": bool(signal.get("angle_eligibility", False)),
        "asteroid_policy": signal.get("asteroid_policy") or {},
        "routing_state": str(signal.get("routing_state") or ""),
        "pass_sequence": str(signal.get("pass_sequence") or ""),
        "cycle_id": str(signal.get("cycle_id") or ""),
        "contact_count": int(signal.get("contact_count") or 0),
        "multiple_exact_passes": bool(signal.get("multiple_exact_passes", False)),
        "formula_version": formula_version,
        "policy_version": SIDECAR_SCHEMA_VERSION,
    }


def _daily_series_with_provenance(
    daily_series: list,
    predictive_signals: list[dict],
    event_id_by_signal_id: dict[str, str],
) -> list[dict]:
    rows = []
    for row in daily_series if isinstance(daily_series, list) else []:
        if not isinstance(row, dict):
            continue
        day = _parse_date(row.get("date"))
        contributors = []
        if day:
            for signal in predictive_signals:
                start = _parse_date(signal.get("start_date"))
                end = _parse_date(signal.get("end_date"))
                if start and end and start <= day <= end:
                    contributors.append(signal)

        contributors.sort(key=lambda sig: sig.get("signal_strength", sig.get("trigger_strength", 0.0)), reverse=True)
        structural = [_contributor(sig) for sig in contributors if sig.get("source_body") in _STRUCTURAL_BODIES]
        trigger = [_contributor(sig) for sig in contributors if sig.get("source_body") not in _STRUCTURAL_BODIES]
        signal_ids = [sig["signal_id"] for sig in contributors if sig.get("signal_id")]
        event_ids = [
            event_id_by_signal_id[sig_id]
            for sig_id in signal_ids
            if sig_id in event_id_by_signal_id
        ]

        enriched = {
            "date": row.get("date"),
            "raw_score": _rounded(row.get("raw_score")),
            "smooth_score": _rounded(row.get("smooth_score")),
            "baseline_score": _rounded(row.get("baseline_score")),
            "residual_score": _rounded(row.get("residual_score")),
            "structural_raw": _rounded(row.get("structural_raw")),
            "trigger_raw": _rounded(row.get("trigger_raw")),
            "contributing_signal_ids": signal_ids,
            "contributing_event_ids": event_ids,
            "structural_contributors": structural,
            "trigger_contributors": trigger,
        }
        rows.append(enriched)
    return rows


def _contributor(signal: dict) -> dict:
    return {
        "signal_id": signal.get("signal_id", ""),
        "strength": _bounded_float(signal.get("signal_strength", signal.get("trigger_strength", 0.0))),
        "source_body": signal.get("source_body", ""),
    }


def _natal_snapshot(payload: dict, birth_data: dict, natal_snapshot_id: str) -> dict:
    user_profile = payload.get("user_profile") if isinstance(payload.get("user_profile"), dict) else {}
    methodology = user_profile.get("methodology") if isinstance(user_profile.get("methodology"), dict) else {}
    return {
        "natal_snapshot_id": natal_snapshot_id,
        "birth_data": {
            "name": birth_data.get("name") or payload.get("name") or "",
            "date": birth_data.get("date") or payload.get("birth_date") or "",
            "time": birth_data.get("time") or payload.get("birth_time") or "",
            "time_state": user_profile.get("birth_time_state") or payload.get("birth_time_state") or "",
            "location_input": birth_data.get("location") or payload.get("birth_location") or payload.get("location") or "",
            "resolved_location": payload.get("birth_location") or payload.get("location") or "",
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "timezone": payload.get("timezone") or "",
            "julian_day": payload.get("julian_day"),
            "local_datetime": payload.get("local_datetime") or "",
            "utc_datetime": payload.get("utc_datetime") or "",
        },
        "methodology": {
            "zodiac": methodology.get("zodiac") or user_profile.get("zodiac") or "",
            "house_system": methodology.get("house_system") or user_profile.get("house_system") or "",
            "ephemeris": "swiss_ephemeris",
            "ephemeris_version": _module_version("swisseph"),
            "ephemeris_files_hash": "",
        },
        "angles": payload.get("angles") or {},
        "houses": payload.get("houses") or {},
        "lots": _computed_lots(payload),
        "standard_planets": payload.get("standard_planets") or {},
        "custom_asteroids": payload.get("custom_asteroids") or {},
        "aspects": payload.get("aspects") or [],
        "user_profile": user_profile,
    }


def _environment(formula_version: str) -> dict:
    return {
        "python_version": platform.python_version(),
        "swisseph_version": _module_version("swisseph"),
        "jinja2_version": _module_version("jinja2"),
        "asteroid_registry_version": SIDECAR_SCHEMA_VERSION,
        "method_policy_versions": dict(_METHOD_POLICY_VERSIONS),
        "predictive_engine_formula_version": formula_version,
        "transit_engine_version": "current_runtime",
    }


def _detector_thresholds() -> dict:
    return {
        "predictive_engine": {
            "formula_version": "runtime",
            "note": "Phase 2 captures stable sidecar shape; full private-threshold export is expanded in later validation phases.",
        },
        "transit_engine": {
            "version": "current_runtime",
        },
        "candidate_protocol": {
            "window_rule": "trigger_derived_no_fixed_maximum",
            "sandbox_research_cap_days": 6.0,
            "sandbox_research_cap_applies_to_this_run": False,
            "minimum_method_family_diversity": 2,
        },
    }


def _asteroid_diagnostics(payload: dict, raw_events: list[dict], predictive_signals: list[dict]) -> dict:
    custom = payload.get("custom_asteroids") if isinstance(payload.get("custom_asteroids"), dict) else {}
    present = sorted(custom.keys())
    registry = _asteroid_registry_summary()
    declared = registry.get("asteroid_names", [])
    event_counts = {
        name: sum(1 for event in raw_events if name in event.get("asteroid_participants", []))
        for name in present
    }
    signal_counts = {
        name: sum(1 for signal in predictive_signals if name in signal.get("asteroid_participants", []))
        for name in present
    }
    return {
        "asteroid_registry_version": registry.get("policy_version") or SIDECAR_SCHEMA_VERSION,
        "registry_asteroids_declared_count": registry.get("asteroid_count", 0),
        "registry_asteroids_declared": declared,
        "asteroids_present": present,
        "asteroids_absent": [name for name in declared if name not in present],
        "ephemeris_missing": [name for name, value in custom.items() if isinstance(value, str)],
        "asteroids_active_as_target": sorted({
            event.get("target_body")
            for event in raw_events
            if event.get("target_body") in present
        }),
        "asteroids_active_as_source": sorted({
            event.get("source_body")
            for event in raw_events
            if event.get("source_body") in present
        }),
        "asteroid_events_count": sum(1 for event in raw_events if event.get("asteroid_participants")),
        "asteroid_signals_count": sum(1 for signal in predictive_signals if signal.get("asteroid_participants")),
        "per_asteroid_contact_counts": {
            name: event_counts.get(name, 0) + signal_counts.get(name, 0)
            for name in present
        },
    }


def _sidecar_path_for_output(output_path: str) -> str:
    if output_path.endswith(".html"):
        return output_path[:-5] + ".eo_predictive.json"
    return output_path + ".eo_predictive.json"


def _natal_snapshot_id(payload: dict, birth_data: dict, policy_versions: dict) -> str:
    source = {
        "birth_data": birth_data,
        "methodology": (payload.get("user_profile") or {}).get("methodology") if isinstance(payload.get("user_profile"), dict) else {},
        "standard_planets": payload.get("standard_planets") or {},
        "angles": payload.get("angles") or {},
        "policy_versions": policy_versions,
    }
    return _hash_id("natal", source, length=16)


def _forecast_event_id(method_family: str, source_body: str, target_body: str, method_variant: str, peak_at: datetime, index: int) -> str:
    return _hash_id(
        f"fe_{_method_code(method_family)}",
        {
            "method_family": method_family,
            "source_body": source_body,
            "target_body": target_body,
            "method_variant": method_variant,
            "peak_at": _iso_datetime(peak_at),
            "index": index,
        },
    )


def _hash_id(prefix: str, value: Any, length: int = 8) -> str:
    payload = json.dumps(_json_safe(value), sort_keys=True, ensure_ascii=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def _method_code(method_family: str) -> str:
    code = "".join(ch for ch in str(method_family or "unknown").lower() if ch.isalnum())
    return code[:4] or "unk"


def _signal_role(signal: dict) -> str:
    explicit = str(signal.get("clock_role") or "").strip()
    if explicit:
        return explicit
    source_body = signal.get("source_body")
    if source_body in _STRUCTURAL_BODIES:
        return "chapter_evidence"
    event_kind = str(signal.get("event_kind") or "").upper()
    if event_kind in {"STATION", "INGRESS"}:
        return "trigger_evidence"
    return "trigger_evidence"


def _clock_role_for_signal(signal: dict) -> str:
    explicit = str(signal.get("clock_role") or "").strip()
    if explicit:
        return explicit
    role = _signal_role(signal)
    if role == "chapter_evidence":
        return "chapter"
    if str(signal.get("event_kind") or "").upper() == "STATION":
        return "overlay"
    return "trigger"


def _custom_asteroid_names(payload: dict) -> set[str]:
    custom = payload.get("custom_asteroids") if isinstance(payload.get("custom_asteroids"), dict) else {}
    return {str(name) for name in custom.keys() if str(name)}


def _body_kind(body: str, asteroid_names: set[str]) -> str:
    if not body:
        return "unknown"
    if body in asteroid_names:
        return "asteroid"
    if body in _LUMINARIES:
        return "luminary"
    if body in _PLANETS:
        return "planet"
    if body in _NODES:
        return "node"
    if body in _ANGLE_TARGETS:
        return "angle"
    if body in _CALCULATED_POINTS:
        return "calculated_point"
    return "unknown"


def _target_kind(target: str, asteroid_names: set[str]) -> str | None:
    if not target:
        return None
    if str(target).isdigit():
        return "house"
    return _body_kind(target, asteroid_names)


def _is_asteroid_participant(source_body: str, target_body: str, asteroid_names: set[str]) -> bool:
    return source_body in asteroid_names or target_body in asteroid_names


def _asteroid_participants(source_body: str, target_body: str, asteroid_names: set[str]) -> list[str]:
    participants = []
    for body in (source_body, target_body):
        if body and body in asteroid_names:
            participants.append(body)
    return sorted(set(participants))


def _report_surface_visibility(source_body: str, target_body: str, asteroid_names: set[str]) -> list[str]:
    if _is_asteroid_participant(source_body, target_body, asteroid_names):
        return ["internal_rd", "predictive_sandbox", "soul_ecosystem"]
    return ["internal_rd"]


def _signal_report_surface_visibility(signal: dict, source_body: str, target_body: str, asteroid_names: set[str]) -> list[str]:
    policy = signal.get("asteroid_policy") if isinstance(signal.get("asteroid_policy"), dict) else {}
    surfaces = _string_list(policy.get("report_surface_visibility"))
    if surfaces:
        return surfaces
    surfaces = _string_list(signal.get("report_surface_visibility"))
    if surfaces:
        return surfaces
    return _report_surface_visibility(source_body, target_body, asteroid_names)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _proprietary_scanner_state(predictive_results: dict) -> str:
    debug = predictive_results.get("debug") if isinstance(predictive_results.get("debug"), dict) else {}
    return str(debug.get("scan_proprietary_forecast_windows") or "rd_gate_disabled")


def _debug_scanner_state(predictive_results: dict, count_key: str, wired_label: str) -> str:
    debug = predictive_results.get("debug") if isinstance(predictive_results.get("debug"), dict) else {}
    if count_key in debug:
        return f"{wired_label}:{int(debug.get(count_key) or 0)}"
    return "not_run"


def _computed_lots(payload: dict) -> dict:
    try:
        from engine.lots import compute_lots

        return compute_lots(payload)
    except Exception:
        return {}


def _asteroid_registry_summary() -> dict:
    try:
        from engine.asteroid_policy import asteroid_registry_summary

        return asteroid_registry_summary()
    except Exception as exc:
        return {
            "policy_version": SIDECAR_SCHEMA_VERSION,
            "asteroid_count": 0,
            "asteroid_names": [],
            "error": str(exc),
        }


def _temporal_precision(start_at: datetime | None, peak_at: datetime | None, end_at: datetime | None) -> str:
    if not start_at or not end_at:
        return "day"
    days = abs((end_at - start_at).total_seconds()) / 86400
    if days < 1:
        return "instant"
    if days <= 7:
        return "week"
    if days <= 45:
        return "month"
    if days <= 120:
        return "season"
    return "year_or_longer"


def _signal_datetime(value: Any) -> datetime | None:
    parsed_date = _parse_date(value)
    if parsed_date:
        return datetime.combine(parsed_date, time.min, tzinfo=timezone.utc)
    if isinstance(value, datetime):
        return _ensure_utc(value)
    return None


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return _ensure_utc(value).date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
    return None


def _iso_date(value: Any) -> str:
    parsed = _parse_date(value)
    return parsed.isoformat() if parsed else ""


def _iso_datetime(value: Any) -> str:
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min, tzinfo=timezone.utc)
    if isinstance(value, datetime):
        value = _ensure_utc(value)
        return value.isoformat().replace("+00:00", "Z")
    return str(value or "")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _bounded_float(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, min(1.0, numeric)), 5)


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rounded(value: Any) -> float:
    try:
        return round(float(value), 5)
    except (TypeError, ValueError):
        return 0.0


def _dict_float(value: dict) -> dict:
    result = {}
    for key, item in value.items():
        try:
            result[str(key)] = round(float(item), 5)
        except (TypeError, ValueError):
            continue
    return result


def _module_version(module_name: str) -> str:
    try:
        module = __import__(module_name)
        return str(getattr(module, "__version__", "available"))
    except Exception:
        return "unavailable"


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime):
        return _iso_datetime(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    return value
