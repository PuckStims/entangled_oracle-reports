"""
engine/candidates.py - Phase 8 internal MicroCandidate assembly.

Candidates are evidence-sidecar objects only. This module does not write an
outcome ledger, does not inspect outcomes, and does not surface predictions in
report prose.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any

from engine.convergence import (
    COMPONENT_WEIGHTS,
    coherence_graph,
    component_scores,
    convergence_score,
    method_family_diversity,
)


MICRO_CANDIDATE_SCHEMA_VERSION = "phase0.1.0"
POLICY_VERSION = "phase8_candidates_v1"
DISCOVERY_BUFFER_DAYS = 3
WINDOW_WIDTH_REFERENCE_SCALE_DAYS = 3.0
TRIGGER_PRECISIONS = {"instant", "day"}
VALID_FILTER_REASONS = {
    "residual_below_min",
    "prominence_below_min",
    "distance_too_close",
    "no_natal_anchor_match",
    "no_chapter_support",
    "no_trigger_support",
    "insufficient_method_family_diversity",
    "coherence_graph_disconnected",
    "anti_double_counting_violation",
    "confidence_withheld",
    "voided_calculation_error",
    "superseded_by_later_candidate",
    "other",
}
DOMAIN_KEYS = {
    "identity",
    "resources",
    "communication",
    "home",
    "creativity",
    "work",
    "partnership",
    "transformation",
    "meaning",
    "vocation",
    "community",
    "spirit",
}


def build_candidate_registry(
    *,
    report_run_id: str,
    natal_snapshot_id: str,
    signals: list[dict],
    chapters: list[dict],
    anchors: list[dict],
    daily_series: list[dict] | None = None,
    payload: dict | None = None,
    pre_registered_at: datetime | None = None,
) -> dict:
    """Build accepted/rejected Phase 8 candidate evidence."""
    emitted_at = _ensure_utc(pre_registered_at or datetime.now(timezone.utc))
    payload = payload or {}
    daily_index = _daily_series_index(daily_series or [])
    signal_by_id = {str(sig.get("signal_id")): sig for sig in signals if isinstance(sig, dict) and sig.get("signal_id")}
    anchor_by_id = {str(anchor.get("anchor_id")): anchor for anchor in anchors if isinstance(anchor, dict) and anchor.get("anchor_id")}
    trigger_signals = [
        sig for sig in signals
        if _is_qualifying_trigger(sig)
    ]
    trigger_signals.sort(key=lambda sig: (_date_start(_signal_peak_date(sig)), str(sig.get("signal_id") or "")))

    candidates: list[dict] = []
    rejected: list[dict] = []
    convergence_records: list[dict] = []
    consumed_trigger_ids: set[str] = set()

    for seed in trigger_signals:
        seed_id = str(seed.get("signal_id") or "")
        if seed_id in consumed_trigger_ids:
            continue

        attempt = _assemble_attempt(
            seed,
            trigger_signals,
            signals,
            chapters,
            anchors,
            anchor_by_id,
            signal_by_id,
            payload,
        )
        if attempt["candidate"] is None:
            rejected.append(_rejection_record(seed, attempt, daily_index))
            consumed_trigger_ids.add(seed_id)
            continue

        candidate = _candidate_record(
            report_run_id=report_run_id,
            natal_snapshot_id=natal_snapshot_id,
            pre_registered_at=emitted_at,
            attempt=attempt,
            anchor_by_id=anchor_by_id,
        )
        candidates.append(candidate)
        convergence_records.append(_candidate_convergence_record(candidate, attempt, signal_by_id))
        for merged_trigger in attempt["trigger_support"]:
            merged_id = str(merged_trigger.get("signal_id") or "")
            if merged_id and merged_id != seed_id:
                rejected.append(_superseded_record(merged_trigger, candidate, seed, daily_index))
        consumed_trigger_ids.update(candidate["trigger_support"])

    return {
        "candidates": candidates,
        "rejected_candidates": rejected,
        "convergence_composition": convergence_records,
        "debug": {
            "candidate_count": len(candidates),
            "rejected_candidate_count": len(rejected),
            "qualifying_trigger_count": len(trigger_signals),
            "candidate_policy_version": POLICY_VERSION,
        },
    }


def _assemble_attempt(
    seed: dict,
    trigger_signals: list[dict],
    all_signals: list[dict],
    chapters: list[dict],
    anchors: list[dict],
    anchor_by_id: dict[str, dict],
    signal_by_id: dict[str, dict],
    payload: dict,
) -> dict:
    seed_peak = _signal_peak_date(seed)
    seed_anchors = set(_string_list(seed.get("natal_anchor_ids")))
    if not seed_anchors:
        return _failed_attempt(seed, "no_natal_anchor_match", "|natal_promise_links| >= 1")

    trigger_support = _trigger_cluster(seed, trigger_signals)
    if not trigger_support:
        return _failed_attempt(seed, "no_trigger_support", "|trigger_support| >= 1")

    start_date = min(_signal_start_date(sig) for sig in trigger_support)
    end_date = max(_signal_end_date(sig) for sig in trigger_support)
    peak_signal = max(trigger_support, key=lambda sig: _strength(sig))
    peak_date = _signal_peak_date(peak_signal)
    trigger_anchor_ids = sorted({anchor_id for sig in trigger_support for anchor_id in _string_list(sig.get("natal_anchor_ids"))})
    if not trigger_anchor_ids:
        return _failed_attempt(seed, "no_natal_anchor_match", "|natal_promise_links| >= 1", trigger_support=trigger_support)

    chapter_support, chapter_signals = _chapter_support(
        chapters,
        signal_by_id,
        trigger_anchor_ids,
        start_date,
        end_date,
    )
    if not chapter_support:
        long_support = _long_clock_support(all_signals, trigger_anchor_ids, start_date, end_date)
        chapter_support = [str(sig.get("signal_id")) for sig in long_support if sig.get("signal_id")]
        chapter_signals = long_support
    if not chapter_support:
        return _failed_attempt(
            seed,
            "no_chapter_support",
            "|chapter_support| >= 1",
            trigger_support=trigger_support,
            window=(start_date, peak_date, end_date),
        )

    contributing = _dedupe_signals(trigger_support + chapter_signals)
    diversity = method_family_diversity(contributing)
    if diversity["count"] < 2:
        raw_groups = {str(sig.get("independence_group") or sig.get("method_family") or "") for sig in contributing}
        reason = "anti_double_counting_violation" if len(raw_groups) >= 2 else "insufficient_method_family_diversity"
        return _failed_attempt(
            seed,
            reason,
            "|independent_method_families| >= 2",
            trigger_support=trigger_support,
            chapter_support=chapter_support,
            chapter_signals=chapter_signals,
            window=(start_date, peak_date, end_date),
            diversity=diversity,
        )

    graph = coherence_graph(contributing, anchors, payload)
    if not graph.get("connected"):
        return _failed_attempt(
            seed,
            "coherence_graph_disconnected",
            "coherence graph must be one connected component",
            trigger_support=trigger_support,
            chapter_support=chapter_support,
            chapter_signals=chapter_signals,
            window=(start_date, peak_date, end_date),
            diversity=diversity,
            graph=graph,
        )

    birth_time_dependency = _birth_time_dependency(contributing)
    withheld = any("withheld" in str(sig.get("confidence_state") or "") for sig in contributing)
    if withheld and birth_time_dependency != "hard":
        return _failed_attempt(
            seed,
            "confidence_withheld",
            "confidence state cannot be withheld unless candidate is hard birth-time dependent",
            trigger_support=trigger_support,
            chapter_support=chapter_support,
            chapter_signals=chapter_signals,
            window=(start_date, peak_date, end_date),
            diversity=diversity,
            graph=graph,
        )

    components = component_scores(contributing, anchors, payload)
    window_days = _window_days(start_date, end_date)
    components["window_width"] = round(math.exp(-window_days / WINDOW_WIDTH_REFERENCE_SCALE_DAYS), 4)
    components["temporal_convergence"] = _trigger_temporal_convergence(trigger_support)
    components["trigger_precision"] = _trigger_precision(trigger_support)
    components["method_family_diversity"] = round(min(1.0, diversity["count"] / 3.0), 4)
    components["method_family_diversity_count"] = diversity["count"]
    score = convergence_score(components)
    alternative_evidence = _alternative_evidence(
        all_signals,
        trigger_support,
        contributing,
        start_date,
        end_date,
        diversity,
    )
    topics, domains = _candidate_topics_domains(contributing, trigger_anchor_ids, anchor_by_id)
    if not topics:
        topics = ["situational"]
    if not domains:
        domains = ["identity"]

    return {
        "candidate": True,
        "seed": seed,
        "trigger_support": trigger_support,
        "chapter_support": chapter_support,
        "chapter_signals": chapter_signals,
        "contributing_signals": contributing,
        "natal_promise_links": trigger_anchor_ids,
        "start_date": start_date,
        "peak_date": peak_date,
        "end_date": end_date,
        "window_days": window_days,
        "component_scores": components,
        "convergence_score": score,
        "coherence_graph": graph,
        "diversity": diversity,
        "candidate_topic_keys": topics,
        "candidate_domain": domains,
        "asteroid_participants": sorted({item for sig in contributing for item in _string_list(sig.get("asteroid_participants"))}),
        "alternative_evidence": alternative_evidence,
        "birth_time_dependency": birth_time_dependency,
        "candidate_status": "withheld" if withheld and birth_time_dependency == "hard" else "pre_registered",
    }


def _candidate_record(
    *,
    report_run_id: str,
    natal_snapshot_id: str,
    pre_registered_at: datetime,
    attempt: dict,
    anchor_by_id: dict[str, dict],
) -> dict:
    start_at = _date_start(attempt["start_date"])
    peak_at = _date_start(attempt["peak_date"])
    end_at = _date_end(attempt["end_date"])
    trigger_ids = [str(sig.get("signal_id")) for sig in attempt["trigger_support"] if sig.get("signal_id")]
    candidate_id = _candidate_id(natal_snapshot_id, peak_at, trigger_ids)
    components = dict(attempt["component_scores"])
    confidence_components = _confidence_components(attempt["contributing_signals"])
    return {
        "schema_version": MICRO_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "report_run_id": report_run_id,
        "start_at": _iso_datetime(start_at),
        "peak_at": _iso_datetime(peak_at),
        "end_at": _iso_datetime(end_at),
        "window_days": attempt["window_days"],
        "maximum_window_days": None,
        "candidate_domain": attempt["candidate_domain"],
        "candidate_topic_keys": attempt["candidate_topic_keys"],
        "natal_promise_links": attempt["natal_promise_links"],
        "chapter_support": attempt["chapter_support"],
        "trigger_support": trigger_ids,
        "independent_method_families": attempt["diversity"]["independent_method_families"],
        "asteroid_participants": attempt["asteroid_participants"],
        "component_scores": components,
        "convergence_score": attempt["convergence_score"],
        "counterforce": components.get("counterforce", 0.0),
        "counterforce_notes": _counterforce_notes(attempt["contributing_signals"], components),
        "complexity": components.get("complexity", 0.0),
        "confidence": components.get("confidence", 0.0),
        "confidence_components": confidence_components,
        "birth_time_dependency": attempt["birth_time_dependency"],
        "candidate_status": attempt["candidate_status"],
        "pre_registered_at": _iso_datetime(pre_registered_at),
        "alternative_evidence": attempt["alternative_evidence"],
        "report_surface_visibility": ["internal_rd"],
        "provenance": {
            "builder": "engine.candidates.build_candidate_registry",
            "builder_version": POLICY_VERSION,
            "emitted_at": _iso_datetime(pre_registered_at),
            "candidate_id_basis": "hash(natal_snapshot_id, policy_version, peak_at, trigger_signal_ids)",
        },
    }


def _candidate_convergence_record(candidate: dict, attempt: dict, signal_by_id: dict[str, dict]) -> dict:
    groups: dict[str, int] = {}
    for sig in attempt["contributing_signals"]:
        group = str(sig.get("independence_group") or sig.get("method_family") or "unknown")
        groups[group] = groups.get(group, 0) + 1
    return {
        "candidate_id": candidate["candidate_id"],
        "coherence_graph": attempt["coherence_graph"],
        "independence_group_composition": groups,
        "method_family_dedup_trace": [
            {
                "suppressed_signal_id": signal_id,
                "reason": "composite_key_match",
            }
            for signal_id in attempt["diversity"].get("suppressed_signal_ids", [])
        ],
        "component_scores": candidate["component_scores"],
        "convergence_score": candidate["convergence_score"],
    }


def _trigger_cluster(seed: dict, trigger_signals: list[dict]) -> list[dict]:
    cluster = [seed]
    cluster_ids = {str(seed.get("signal_id") or "")}
    seed_peak = _signal_peak_date(seed)
    seed_anchors = set(_string_list(seed.get("natal_anchor_ids")))
    for sig in trigger_signals:
        sig_id = str(sig.get("signal_id") or "")
        if not sig_id or sig_id in cluster_ids:
            continue
        if abs((_signal_peak_date(sig) - seed_peak).days) > DISCOVERY_BUFFER_DAYS:
            continue
        if not (seed_anchors & set(_string_list(sig.get("natal_anchor_ids")))):
            continue
        if not _windows_adjacent_or_overlapping(cluster, sig):
            continue
        cluster.append(sig)
        cluster_ids.add(sig_id)
    return sorted(cluster, key=lambda sig: (_signal_peak_date(sig), str(sig.get("signal_id") or "")))


def _chapter_support(
    chapters: list[dict],
    signal_by_id: dict[str, dict],
    anchor_ids: list[str],
    start_date: date,
    end_date: date,
) -> tuple[list[str], list[dict]]:
    anchor_set = set(anchor_ids)
    support_ids: list[str] = []
    support_signals: list[dict] = []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        if not (anchor_set & set(_string_list(chapter.get("natal_anchor_ids")))):
            continue
        chapter_start = _parse_datetime(chapter.get("start_at"))
        chapter_end = _parse_datetime(chapter.get("end_at"))
        if not chapter_start or not chapter_end:
            continue
        if chapter_start.date() > end_date or chapter_end.date() < start_date:
            continue
        chapter_id = str(chapter.get("chapter_id") or "")
        if chapter_id:
            support_ids.append(chapter_id)
        for signal_id in _string_list(chapter.get("contributing_signal_ids")):
            signal = signal_by_id.get(signal_id)
            if signal:
                support_signals.append(signal)
    return sorted(set(support_ids)), _dedupe_signals(support_signals)


def _long_clock_support(all_signals: list[dict], anchor_ids: list[str], start_date: date, end_date: date) -> list[dict]:
    anchor_set = set(anchor_ids)
    result = []
    for sig in all_signals:
        if not _is_long_clock_signal(sig):
            continue
        if not (anchor_set & set(_string_list(sig.get("natal_anchor_ids")))):
            continue
        sig_start = _signal_start_date(sig)
        sig_end = _signal_end_date(sig)
        if sig_start <= end_date and sig_end >= start_date:
            result.append(sig)
    return result


def _alternative_evidence(
    all_signals: list[dict],
    trigger_support: list[dict],
    contributing_signals: list[dict],
    start_date: date,
    end_date: date,
    diversity: dict,
) -> list[str]:
    chosen = {str(sig.get("signal_id") or "") for sig in contributing_signals}
    max_strength = max((_strength(sig) for sig in contributing_signals), default=0.0)
    alternatives = set(diversity.get("suppressed_signal_ids", []))
    for sig in all_signals:
        sig_id = str(sig.get("signal_id") or "")
        if not sig_id or sig_id in chosen:
            continue
        if _signal_start_date(sig) <= end_date and _signal_end_date(sig) >= start_date:
            if max_strength == 0.0 or _strength(sig) >= 0.5 * max_strength:
                alternatives.add(sig_id)
        for event_id in _string_list(sig.get("source_event_ids")):
            if sig_id in alternatives:
                alternatives.add(event_id)
    return sorted(alternatives)


def _candidate_topics_domains(contributing: list[dict], anchor_ids: list[str], anchor_by_id: dict[str, dict]) -> tuple[list[str], list[str]]:
    topics = {item for sig in contributing for item in _string_list(sig.get("topic_keys"))}
    domains = {item for sig in contributing for item in _string_list(sig.get("domain_keys")) if item in DOMAIN_KEYS}
    for anchor_id in anchor_ids:
        anchor = anchor_by_id.get(anchor_id)
        if not anchor:
            continue
        topics.update(_string_list(anchor.get("topic_keys")))
        domains.update(item for item in _string_list(anchor.get("domain_keys")) if item in DOMAIN_KEYS)
    return sorted(topics), sorted(domains)


def _rejection_record(seed: dict, attempt: dict, daily_index: dict[str, dict]) -> dict:
    peak = _signal_peak_date(seed)
    row = daily_index.get(peak.isoformat(), {})
    window = attempt.get("window")
    width = _window_days(window[0], window[2]) if window else None
    signal_ids = _attempt_signal_ids(seed, attempt)
    reason = attempt.get("filter_reason") if attempt.get("filter_reason") in VALID_FILTER_REASONS else "other"
    return {
        "rejection_id": _hash_id("rej", {
            "peak": peak.isoformat(),
            "reason": reason,
            "signals": signal_ids,
        }),
        "candidate_date": peak.isoformat(),
        "peak_date": _iso_datetime(_date_start(peak)),
        "residual": _rounded(row.get("residual_score", 0.0)),
        "prominence": _rounded(row.get("prominence", row.get("residual_score", 0.0))),
        "candidate_width_days": width,
        "candidate_width_note": (
            "Null because the peak was rejected before a trigger-derived window could be constructed. "
            "When a rejection occurs after window construction, this field carries the natural (non-fixed) width that was computed."
            if width is None
            else "Natural trigger-derived width computed before rejection; no fixed maximum was applied."
        ),
        "filter_reason": reason,
        "requirement_that_failed": attempt.get("requirement_that_failed", ""),
        "merged_into": None,
        "suppressed_by": None,
        "signal_ids_considered": signal_ids,
        "method_families_present": sorted({str(sig.get("independence_group") or sig.get("method_family") or "") for sig in attempt.get("considered_signals", [seed])}),
        "anchor_ids_considered": sorted({anchor_id for sig in attempt.get("considered_signals", [seed]) for anchor_id in _string_list(sig.get("natal_anchor_ids"))}),
        "notes": attempt.get("notes", ""),
    }


def _superseded_record(trigger: dict, candidate: dict, seed: dict, daily_index: dict[str, dict]) -> dict:
    peak = _signal_peak_date(trigger)
    row = daily_index.get(peak.isoformat(), {})
    return {
        "rejection_id": _hash_id("rej", {
            "peak": peak.isoformat(),
            "reason": "superseded_by_later_candidate",
            "signal": trigger.get("signal_id"),
            "candidate_id": candidate.get("candidate_id"),
        }),
        "candidate_date": peak.isoformat(),
        "peak_date": _iso_datetime(_date_start(peak)),
        "residual": _rounded(row.get("residual_score", 0.0)),
        "prominence": _rounded(row.get("prominence", row.get("residual_score", 0.0))),
        "candidate_width_days": candidate.get("window_days"),
        "candidate_width_note": "Natural trigger-derived width retained on the merged candidate; no fixed maximum was applied.",
        "filter_reason": "superseded_by_later_candidate",
        "requirement_that_failed": "merged into adjacent coherent trigger-derived candidate",
        "merged_into": candidate.get("candidate_id"),
        "suppressed_by": seed.get("signal_id"),
        "signal_ids_considered": [str(trigger.get("signal_id") or "")],
        "method_families_present": [str(trigger.get("independence_group") or trigger.get("method_family") or "")],
        "anchor_ids_considered": _string_list(trigger.get("natal_anchor_ids")),
        "notes": "Trigger peak was topic-coherent and adjacent/overlapping with the accepted candidate trigger set.",
    }


def _failed_attempt(
    seed: dict,
    filter_reason: str,
    requirement: str,
    *,
    trigger_support: list[dict] | None = None,
    chapter_support: list[str] | None = None,
    chapter_signals: list[dict] | None = None,
    window: tuple[date, date, date] | None = None,
    diversity: dict | None = None,
    graph: dict | None = None,
) -> dict:
    considered = _dedupe_signals((trigger_support or [seed]) + (chapter_signals or []))
    return {
        "candidate": None,
        "seed": seed,
        "filter_reason": filter_reason,
        "requirement_that_failed": requirement,
        "trigger_support": trigger_support or [],
        "chapter_support": chapter_support or [],
        "chapter_signals": chapter_signals or [],
        "considered_signals": considered or [seed],
        "window": window,
        "diversity": diversity or {},
        "coherence_graph": graph or {},
    }


def _attempt_signal_ids(seed: dict, attempt: dict) -> list[str]:
    signals = attempt.get("considered_signals") or [seed]
    return sorted({str(sig.get("signal_id") or "") for sig in signals if sig.get("signal_id")})


def _is_qualifying_trigger(sig: dict) -> bool:
    return (
        str(sig.get("signal_role") or "") == "trigger_evidence"
        and str(sig.get("temporal_precision") or "") in TRIGGER_PRECISIONS
        and bool(sig.get("signal_id"))
        and _signal_peak_date(sig) is not None
    )


def _windows_adjacent_or_overlapping(existing: list[dict], candidate: dict) -> bool:
    candidate_start = _signal_start_date(candidate)
    candidate_end = _signal_end_date(candidate)
    for sig in existing:
        start = _signal_start_date(sig)
        end = _signal_end_date(sig)
        if candidate_start <= end + timedelta(days=1) and candidate_end >= start - timedelta(days=1):
            return True
    return False


def _is_long_clock_signal(sig: dict) -> bool:
    role = str(sig.get("signal_role") or sig.get("clock_role") or "")
    family = str(sig.get("method_family") or "")
    if role in {"chapter_evidence", "chapter", "time_lord"}:
        return True
    if family in {"RETURN", "PROGRESSION", "SOLAR_ARC", "PROFECTION", "ZODIACAL_RELEASING", "TIME_LORD"}:
        return True
    return (_signal_end_date(sig) - _signal_start_date(sig)).days > 90


def _trigger_temporal_convergence(signals: list[dict]) -> float:
    peaks = [_signal_peak_date(sig) for sig in signals if _signal_peak_date(sig)]
    if len(peaks) <= 1:
        return 1.0 if peaks else 0.0
    span = (max(peaks) - min(peaks)).days
    return round(math.exp(-span / 3.0), 4)


def _trigger_precision(signals: list[dict]) -> float:
    values = []
    for sig in signals:
        orb = _float(sig.get("orb"), None)
        allowed = max(0.01, _float(sig.get("allowed_orb"), 3.0) or 3.0)
        if orb is not None:
            values.append(max(0.0, 1.0 - abs(orb) / allowed))
    return round(max(values, default=0.0), 4)


def _birth_time_dependency(signals: list[dict]) -> str:
    if any(str(sig.get("birth_time_dependency") or "") == "hard" or "angle" in str(sig.get("angle_eligibility") or "") for sig in signals):
        return "hard"
    if any(str(sig.get("birth_time_dependency") or "") == "soft" for sig in signals):
        return "soft"
    return "none"


def _confidence_components(signals: list[dict]) -> dict:
    totals: dict[str, list[float]] = {}
    for sig in signals:
        comps = sig.get("confidence_components") if isinstance(sig.get("confidence_components"), dict) else {}
        for key, value in comps.items():
            try:
                totals.setdefault(str(key), []).append(float(value))
            except (TypeError, ValueError):
                continue
    return {key: round(sum(values) / len(values), 4) for key, values in totals.items() if values}


def _counterforce_notes(signals: list[dict], components: dict) -> list[str]:
    if _float(components.get("counterforce"), 0.0) < 0.35:
        return []
    operations = sorted({str(sig.get("dominant_operation") or "") for sig in signals if sig.get("dominant_operation")})
    return [f"conflicting_operations_retained:{','.join(operations)}"] if operations else ["counterforce_component_retained"]


def _dedupe_signals(signals: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for sig in signals:
        sig_id = str(sig.get("signal_id") or "")
        if not sig_id or sig_id in seen:
            continue
        seen.add(sig_id)
        result.append(sig)
    return result


def _daily_series_index(rows: list[dict]) -> dict[str, dict]:
    return {
        str(row.get("date")): row
        for row in rows
        if isinstance(row, dict) and row.get("date")
    }


def _candidate_id(natal_snapshot_id: str, peak_at: datetime, trigger_ids: list[str]) -> str:
    return _hash_id("cand", {
        "natal_snapshot_id": natal_snapshot_id,
        "policy_version": POLICY_VERSION,
        "peak_at": _iso_datetime(peak_at),
        "trigger_signal_ids": sorted(trigger_ids),
    })


def _hash_id(prefix: str, value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:8]}"


def _signal_start_date(sig: dict) -> date:
    return _parse_date(sig.get("start_date")) or _signal_peak_date(sig)


def _signal_peak_date(sig: dict) -> date:
    return _parse_date(sig.get("peak_date")) or _parse_date(sig.get("start_date")) or date.today()


def _signal_end_date(sig: dict) -> date:
    return _parse_date(sig.get("end_date")) or _signal_peak_date(sig)


def _window_days(start: date, end: date) -> float:
    start_at = _date_start(start)
    end_at = _date_end(end)
    return round(max(1.0 / 86400.0, (end_at - start_at).total_seconds() / 86400.0), 4)


def _strength(sig: dict) -> float:
    return _float(sig.get("signal_strength", sig.get("trigger_strength", 0.0)), 0.0) or 0.0


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if not value:
        return None
    try:
        return _ensure_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except ValueError:
        parsed = _parse_date(value)
        return _date_start(parsed) if parsed else None


def _date_start(value: date) -> datetime:
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)


def _date_end(value: date) -> datetime:
    return datetime(value.year, value.month, value.day, 23, 59, 59, tzinfo=timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso_datetime(value: datetime) -> str:
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rounded(value: Any) -> float:
    return round(_float(value, 0.0) or 0.0, 4)
