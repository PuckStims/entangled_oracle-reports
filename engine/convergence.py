"""
engine/convergence.py - Phase 7 chapters and cross-clock composition.

This module implements the graph/scoring layer that Phase 8 will later use for
MicroCandidate assembly. It does not emit candidates or client-facing prose.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from itertools import combinations
from typing import Any

from engine.natal_promise import HOUSE_DOMAINS, TRADITIONAL_RULERS


CHAPTER_SCHEMA_VERSION = "phase0.1.0"
CONVERGENCE_PROTOCOL_VERSION = "phase0.1.1"
POLICY_VERSION = "phase7_convergence_v1"
OPERATION_AXES = ("stabilize", "amplify", "activate", "disrupt", "dissolve", "reveal")
CONSTRUCTIVE = {"stabilize", "amplify", "activate"}
DISSOLVING = {"disrupt", "dissolve"}
COMPONENT_WEIGHTS = {
    "natal_promise_strength": 0.14,
    "long_clock_support": 0.14,
    "trigger_precision": 0.14,
    "method_family_diversity": 0.12,
    "topic_coherence": 0.12,
    "temporal_convergence": 0.08,
    "asteroid_specificity": 0.06,
    "confidence": 0.10,
    "counterforce": -0.05,
    "complexity": 0.02,
    "window_width": 0.03,
}


def build_chapter_states(
    signals: list[dict],
    time_lord_periods: list[dict] | None,
    anchors: list[dict],
    payload: dict | None = None,
    *,
    emitted_at: datetime | None = None,
) -> list[dict]:
    """Promote long-clock and top-level TimeLordPeriod records into ChapterState."""
    payload = payload or {}
    emitted_at = emitted_at or datetime.now(timezone.utc)
    signal_map = {str(sig.get("signal_id")): sig for sig in signals if isinstance(sig, dict) and sig.get("signal_id")}
    chapters: list[dict] = []
    lookups = _ensure_lookups(anchors, payload, None)

    for period in time_lord_periods or []:
        if not isinstance(period, dict) or not _is_root_period(period):
            continue
        start = _parse_datetime(period.get("start_at"))
        end = _parse_datetime(period.get("end_at"))
        if not start or not end:
            continue
        period_signals = _signals_in_window(signals, start.date(), end.date(), max_gap_days=30)
        anchor_ids = sorted(set(_string_list(period.get("natal_anchor_ids"))) | set(_period_anchor_ids(period, anchors)))
        for sig in period_signals:
            if set(_string_list(sig.get("natal_anchor_ids"))) & set(anchor_ids):
                continue
            if str(sig.get("source_body") or "") == str(period.get("period_lord") or ""):
                anchor_ids.extend(_string_list(sig.get("natal_anchor_ids")))
        anchor_ids = sorted(set(anchor_ids))
        contributing = _coherent_subset(period_signals, anchor_ids, anchors, payload, lookups=lookups)
        if not contributing and anchor_ids:
            contributing = [sig for sig in period_signals if _string_list(sig.get("natal_anchor_ids"))]
        chapter = _chapter_from_parts(
            chapter_kind=_chapter_kind_for_period(period),
            start_at=start,
            end_at=end,
            signals=contributing,
            anchors=anchors,
            anchor_ids=anchor_ids,
            period=period,
            payload=payload,
            emitted_at=emitted_at,
            lookups=lookups,
        )
        if chapter:
            chapters.append(chapter)

    for sig in signals:
        if not isinstance(sig, dict):
            continue
        if not _is_long_clock_signal(sig):
            continue
        start = _parse_date(sig.get("start_date"))
        end = _parse_date(sig.get("end_date"))
        if not start or not end:
            continue
        anchor_ids = _string_list(sig.get("natal_anchor_ids"))
        if not anchor_ids:
            continue
        cluster = _signals_in_window(signals, start, end, max_gap_days=30)
        cluster = _coherent_subset(cluster, anchor_ids, anchors, payload, lookups=lookups)
        chapter = _chapter_from_parts(
            chapter_kind=_chapter_kind_for_signal(sig),
            start_at=_date_start(start),
            end_at=_date_end(end),
            signals=cluster or [sig],
            anchors=anchors,
            anchor_ids=anchor_ids,
            period=None,
            payload=payload,
            emitted_at=emitted_at,
            lookups=lookups,
        )
        if chapter:
            chapters.append(chapter)

    return _dedupe_chapters(chapters)


def build_convergence_composition(
    signals: list[dict],
    chapters: list[dict],
    anchors: list[dict],
    payload: dict | None = None,
) -> list[dict]:
    """Build transparent convergence clusters without emitting MicroCandidate."""
    payload = payload or {}
    lookups = _ensure_lookups(anchors, payload, None)
    compositions: list[dict] = []
    used_keys: set[str] = set()

    for chapter in chapters:
        cluster = [
            sig for sig in signals
            if str(sig.get("signal_id") or "") in set(_string_list(chapter.get("contributing_signal_ids")))
        ]
        if not cluster:
            continue
        key = _cluster_key(cluster)
        if key in used_keys:
            continue
        used_keys.add(key)
        compositions.append(_composition_record(cluster, anchors, payload, chapter=chapter, lookups=lookups))

    by_anchor: dict[str, list[dict]] = {}
    for sig in signals:
        for anchor_id in _string_list(sig.get("natal_anchor_ids")):
            by_anchor.setdefault(anchor_id, []).append(sig)

    for anchor_id, anchor_signals in sorted(by_anchor.items()):
        if len(anchor_signals) < 2:
            continue
        families = method_family_diversity(anchor_signals)
        if families["count"] < 2:
            continue
        key = _cluster_key(anchor_signals)
        if key in used_keys:
            continue
        used_keys.add(key)
        compositions.append(_composition_record(anchor_signals, anchors, payload, anchor_id=anchor_id, lookups=lookups))

    compositions.sort(key=lambda item: item.get("convergence_score", 0.0), reverse=True)
    return compositions


def method_family_diversity(signals: list[dict]) -> dict:
    """Composite-dedup method-family diversity per phase0/04 section 2.2."""
    winners: dict[tuple[str, str, str], dict] = {}
    suppressed: list[str] = []
    for sig in signals:
        group = _normalized_group(sig)
        source = str(sig.get("source_body") or "")
        target = str(sig.get("target_body") or "")
        if group in {"transit_family", "proprietary_transit_family"}:
            key = ("transit_composite", source, target)
        else:
            key = (group, source if group.endswith("_family") else "", target if group.endswith("_family") else "")
        current = winners.get(key)
        if current is None or _strength(sig) > _strength(current):
            if current and current.get("signal_id"):
                suppressed.append(str(current["signal_id"]))
            winners[key] = sig
        elif sig.get("signal_id"):
            suppressed.append(str(sig["signal_id"]))
    groups = sorted({_normalized_group(sig) for sig in winners.values()})
    return {
        "count": len(winners),
        "independent_method_families": groups,
        "dedup_keys": ["|".join(key) for key in sorted(winners)],
        "suppressed_signal_ids": sorted(suppressed),
        "anti_stacking_ratio": round(len(winners) / max(1, len(signals)), 4),
    }


def _build_signal_derived(sig: dict, anchors: list[dict], payload: dict, lookups: dict) -> dict:
    target_body = str(sig.get("target_body") or "")
    return {
        "anchor_ids": frozenset(_string_list(sig.get("natal_anchor_ids"))),
        "topic_keys": frozenset(_string_list(sig.get("topic_keys"))),
        "domain_keys": frozenset(_string_list(sig.get("domain_keys"))),
        "target_body": target_body,
        "target_house": _target_house(payload, target_body),
        "index_drivers": frozenset(_index_driver_sets(sig, anchors, lookups=lookups)),
    }


def _ensure_signal_derived(signals: list[dict], anchors: list[dict], payload: dict, lookups: dict) -> dict[str, dict]:
    """
    Precomputes each signal's coherence-relevant derived data (anchor/topic/
    domain sets, target house, index-driver set) once per signal_id, cached
    on the shared `lookups` dict so it survives across every coherence_graph
    call within one report run (911 calls observed on a real report) instead
    of being recomputed from raw signal dicts on every pairwise comparison
    inside every one of those calls -- that redundant recomputation was the
    second half of the performance bug fixed alongside the aspect-orb and
    anchor-index-link caches above (profiled: 8.6M redundant _string_list
    calls, ~31s, on a single real personal_forecast report before this fix).
    """
    cache = lookups.setdefault("signal_derived", {})
    for sig in signals:
        sig_id = str(sig.get("signal_id") or "")
        if sig_id and sig_id not in cache:
            cache[sig_id] = _build_signal_derived(sig, anchors, payload, lookups)
    return cache


def coherence_graph(signals: list[dict], anchors: list[dict], payload: dict | None = None, *, lookups: dict | None = None) -> dict:
    """Build the seven-rule topic coherence graph from phase0/04 section 3.1."""
    payload = payload or {}
    lookups = _ensure_lookups(anchors, payload, lookups)
    derived = _ensure_signal_derived(signals, anchors, payload, lookups)
    pair_cache: dict[tuple[str, str], list[str]] = lookups.setdefault("coherence_pair_cache", {})
    nodes = [str(sig.get("signal_id") or "") for sig in signals if sig.get("signal_id")]
    edges = []
    for sig_a, sig_b in combinations([sig for sig in signals if sig.get("signal_id")], 2):
        pair_key = tuple(sorted((str(sig_a["signal_id"]), str(sig_b["signal_id"]))))
        if pair_key in pair_cache:
            reasons = pair_cache[pair_key]
        else:
            reasons = coherence_reasons(sig_a, sig_b, anchors, payload, lookups=lookups, derived=derived)
            pair_cache[pair_key] = reasons
        if reasons:
            edges.append({
                "source": sig_a["signal_id"],
                "target": sig_b["signal_id"],
                "rules": reasons,
            })
    possible = len(nodes) * (len(nodes) - 1) / 2
    score = round(len(edges) / possible, 4) if possible else 1.0 if nodes else 0.0
    return {
        "nodes": nodes,
        "edges": edges,
        "edges_present": len(edges),
        "edges_possible": int(possible),
        "score": score,
        "connected": _is_connected(nodes, edges),
    }


def coherence_reasons(
    sig_a: dict, sig_b: dict, anchors: list[dict], payload: dict, *, lookups: dict | None = None, derived: dict | None = None,
) -> list[str]:
    lookups = _ensure_lookups(anchors, payload, lookups)
    sig_a_id = str(sig_a.get("signal_id") or "")
    sig_b_id = str(sig_b.get("signal_id") or "")
    derived = derived if derived is not None else lookups.get("signal_derived")
    if derived is not None and sig_a_id in derived and sig_b_id in derived:
        d_a, d_b = derived[sig_a_id], derived[sig_b_id]
    else:
        # Fallback for direct/standalone calls without a precomputed cache
        # (e.g. a unit test calling coherence_reasons in isolation).
        d_a = _build_signal_derived(sig_a, anchors, payload, lookups)
        d_b = _build_signal_derived(sig_b, anchors, payload, lookups)

    reasons: list[str] = []
    if d_a["anchor_ids"] & d_b["anchor_ids"]:
        reasons.append("shared_natal_anchor")

    if d_a["target_house"] and d_a["target_house"] == d_b["target_house"]:
        reasons.append("target_bodies_share_house")

    if _jaccard(d_a["topic_keys"], d_b["topic_keys"]) >= 0.34:
        reasons.append("topic_jaccard_ge_0_34")

    if d_a["domain_keys"] & d_b["domain_keys"]:
        reasons.append("domain_overlap")

    if d_a["index_drivers"] & d_b["index_drivers"]:
        reasons.append("shared_proprietary_index_driver_set")

    if _natal_aspect_orb(payload, d_a["target_body"], d_b["target_body"], lookups=lookups) <= 3.0:
        reasons.append("natal_aspect_orb_le_3")

    if _same_rulership_chain(payload, d_a["target_body"], d_b["target_body"]):
        reasons.append("same_rulership_chain")

    return reasons


def component_scores(signals: list[dict], anchors: list[dict], payload: dict | None = None, *, lookups: dict | None = None) -> dict:
    payload = payload or {}
    lookups = _ensure_lookups(anchors, payload, lookups)
    graph = coherence_graph(signals, anchors, payload, lookups=lookups)
    diversity = method_family_diversity(signals)
    relevant_anchor_ids = sorted({anchor_id for sig in signals for anchor_id in _string_list(sig.get("natal_anchor_ids"))})
    anchor_by_id = {anchor.get("anchor_id"): anchor for anchor in anchors}
    anchor_strength = 0.0
    for anchor_id in relevant_anchor_ids:
        anchor = anchor_by_id.get(anchor_id)
        if anchor:
            anchor_strength = max(anchor_strength, _bounded(anchor.get("strength")) * _bounded(anchor.get("confidence")))
    long_support = max((_strength(sig) for sig in signals if _is_long_clock_signal(sig)), default=0.0)
    trigger_precision = _trigger_precision(signals)
    temporal_convergence = _temporal_convergence(signals)
    asteroid_specificity = _asteroid_specificity(signals)
    confidence = _confidence(signals)
    counterforce = _counterforce(signals)
    complexity = _complexity(signals)
    window_width = _window_width(signals)
    diversity_score = min(1.0, diversity["count"] / 3.0)
    return {
        "natal_promise_strength": round(anchor_strength, 4),
        "long_clock_support": round(long_support, 4),
        "trigger_precision": round(trigger_precision, 4),
        "method_family_diversity": round(diversity_score, 4),
        "method_family_diversity_count": diversity["count"],
        "topic_coherence": graph["score"],
        "temporal_convergence": round(temporal_convergence, 4),
        "asteroid_specificity": round(asteroid_specificity, 4),
        "confidence": round(confidence, 4),
        "counterforce": round(counterforce, 4),
        "complexity": round(complexity, 4),
        "window_width": round(window_width, 4),
    }


def convergence_score(components: dict) -> float:
    weighted = 0.0
    positive_weight = 0.0
    for key, weight in COMPONENT_WEIGHTS.items():
        value = _bounded(components.get(key, 0.0))
        weighted += value * weight
        if weight > 0:
            positive_weight += weight
    return round(max(0.0, min(1.0, weighted / positive_weight if positive_weight else 0.0)), 4)


def _chapter_from_parts(
    *,
    chapter_kind: str,
    start_at: datetime,
    end_at: datetime,
    signals: list[dict],
    anchors: list[dict],
    anchor_ids: list[str],
    period: dict | None,
    payload: dict,
    emitted_at: datetime,
    lookups: dict | None = None,
) -> dict | None:
    if not anchor_ids:
        return None
    lookups = _ensure_lookups(anchors, payload, lookups)
    graph = coherence_graph(signals, anchors, payload, lookups=lookups)
    if signals and not _chapter_coherence_allowed(graph, len(signals)):
        return None
    comps = component_scores(signals, anchors, payload, lookups=lookups) if signals else {
        "confidence": _bounded((period or {}).get("confidence", 0.7)),
        "counterforce": 0.0,
        "complexity": 0.0,
    }
    signal_ids = [sig["signal_id"] for sig in signals if sig.get("signal_id")]
    event_ids = sorted({event_id for sig in signals for event_id in _string_list(sig.get("source_event_ids"))})
    topic_keys = sorted({item for sig in signals for item in _string_list(sig.get("topic_keys"))})
    domain_keys = sorted({item for sig in signals for item in _string_list(sig.get("domain_keys"))})
    asteroid_participants = sorted({item for sig in signals for item in _string_list(sig.get("asteroid_participants"))})
    peak_dates = [_parse_date(sig.get("peak_date")) for sig in signals]
    peak_dates = [item for item in peak_dates if item]
    if peak_dates:
        peak_start = _date_start(min(peak_dates))
        peak_end = _date_end(max(peak_dates))
    else:
        peak_start = start_at
        peak_end = end_at
    polarity = _polarity(signals)
    confidence_components = _merged_confidence_components(signals)
    if period:
        confidence_components.update(period.get("confidence_components") or {})
    record = {
        "schema_version": CHAPTER_SCHEMA_VERSION,
        "chapter_id": "",
        "start_at": _iso_datetime(start_at),
        "peak_range": [_iso_datetime(peak_start), _iso_datetime(peak_end)],
        "end_at": _iso_datetime(end_at),
        "chapter_kind": chapter_kind,
        "active_long_clocks": sorted({str(sig.get("method_family") or "") for sig in signals if _is_long_clock_signal(sig)}),
        "active_structural_transits": [sig["signal_id"] for sig in signals if str(sig.get("source_body") or "") in {"Saturn", "Uranus", "Neptune", "Pluto"} and sig.get("signal_id")],
        "contributing_signal_ids": signal_ids,
        "contributing_event_ids": event_ids,
        "natal_anchor_ids": sorted(set(anchor_ids) | {item for sig in signals for item in _string_list(sig.get("natal_anchor_ids"))}),
        "topic_keys": topic_keys,
        "domain_keys": domain_keys,
        "asteroid_participants": asteroid_participants,
        "coherence": graph["score"],
        "counterforce": round(_bounded(comps.get("counterforce", 0.0)), 4),
        "complexity": round(_bounded(comps.get("complexity", 0.0)), 4),
        "polarity": polarity,
        "confidence": round(_bounded(comps.get("confidence", (period or {}).get("confidence", 0.7))), 4),
        "confidence_components": confidence_components,
        "birth_time_dependency": _chapter_birth_time_dependency(signals, period),
        "chapter_summary_score": convergence_score({**comps, "topic_coherence": graph["score"]}),
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "provenance": {
            "builder": "engine.convergence.build_chapter_states",
            "builder_version": POLICY_VERSION,
            "emitted_at": _iso_datetime(emitted_at),
            "source_period_id": (period or {}).get("period_id"),
        },
    }
    record["chapter_id"] = _hash_id("chap", {
        "chapter_kind": chapter_kind,
        "start_at": record["start_at"],
        "end_at": record["end_at"],
        "natal_anchor_ids": record["natal_anchor_ids"],
        "signal_ids": signal_ids,
        "period_id": (period or {}).get("period_id"),
    })
    return record


def _composition_record(
    signals: list[dict],
    anchors: list[dict],
    payload: dict,
    *,
    chapter: dict | None = None,
    anchor_id: str | None = None,
    lookups: dict | None = None,
) -> dict:
    lookups = _ensure_lookups(anchors, payload, lookups)
    graph = coherence_graph(signals, anchors, payload, lookups=lookups)
    diversity = method_family_diversity(signals)
    comps = component_scores(signals, anchors, payload, lookups=lookups)
    score = convergence_score(comps)
    start_dates = [_parse_date(sig.get("start_date")) for sig in signals]
    peak_dates = [_parse_date(sig.get("peak_date")) for sig in signals]
    end_dates = [_parse_date(sig.get("end_date")) for sig in signals]
    start_dates = [item for item in start_dates if item]
    peak_dates = [item for item in peak_dates if item]
    end_dates = [item for item in end_dates if item]
    anchor_ids = sorted({item for sig in signals for item in _string_list(sig.get("natal_anchor_ids"))})
    if anchor_id and anchor_id not in anchor_ids:
        anchor_ids.append(anchor_id)
    record = {
        "composition_id": _hash_id("conv", {
            "chapter_id": (chapter or {}).get("chapter_id"),
            "anchor_id": anchor_id,
            "signals": sorted(str(sig.get("signal_id") or "") for sig in signals),
        }),
        "schema_version": "phase7.0.0",
        "composition_kind": "chapter_support" if chapter else "anchor_convergence",
        "chapter_id": (chapter or {}).get("chapter_id"),
        "natal_anchor_ids": sorted(anchor_ids),
        "source_signal_ids": sorted(str(sig.get("signal_id") or "") for sig in signals if sig.get("signal_id")),
        "source_event_ids": sorted({event_id for sig in signals for event_id in _string_list(sig.get("source_event_ids"))}),
        "method_families": sorted({str(sig.get("method_family") or "") for sig in signals}),
        "independence_groups": sorted({str(sig.get("independence_group") or "") for sig in signals}),
        "independent_method_families": diversity["independent_method_families"],
        "method_family_diversity_count": diversity["count"],
        "anti_stacking": {
            "dedup_keys": diversity["dedup_keys"],
            "suppressed_signal_ids": diversity["suppressed_signal_ids"],
            "ratio": diversity["anti_stacking_ratio"],
        },
        "topic_keys": sorted({item for sig in signals for item in _string_list(sig.get("topic_keys"))}),
        "domain_keys": sorted({item for sig in signals for item in _string_list(sig.get("domain_keys"))}),
        "asteroid_participants": sorted({item for sig in signals for item in _string_list(sig.get("asteroid_participants"))}),
        "start_date": min(start_dates).isoformat() if start_dates else "",
        "peak_date": max(peak_dates, key=lambda d: sum(1 for sig in signals if _parse_date(sig.get("peak_date")) == d)).isoformat() if peak_dates else "",
        "end_date": max(end_dates).isoformat() if end_dates else "",
        "coherence_graph": graph,
        "component_scores": comps,
        "counterforce_high": _bounded(comps.get("counterforce", 0.0)) >= 0.5,
        "convergence_score": score,
        "policy_version": POLICY_VERSION,
    }
    return record


def _coherent_subset(signals: list[dict], anchor_ids: list[str], anchors: list[dict], payload: dict, *, lookups: dict | None = None) -> list[dict]:
    if not signals:
        return []
    lookups = _ensure_lookups(anchors, payload, lookups)
    anchor_set = set(anchor_ids)
    selected = [
        sig for sig in signals
        if anchor_set & set(_string_list(sig.get("natal_anchor_ids")))
    ]
    if not selected:
        selected = list(signals)
    graph = coherence_graph(selected, anchors, payload, lookups=lookups)
    if _chapter_coherence_allowed(graph, len(selected)):
        return selected
    connected_ids = _largest_connected_component(graph)
    return [sig for sig in selected if sig.get("signal_id") in connected_ids]


def _is_root_period(period: dict) -> bool:
    system = str(period.get("system") or "")
    level = str(period.get("level") or "")
    if system == "annual_profection":
        return level == "year"
    if system.startswith("zodiacal_releasing"):
        return level == "L1" and not period.get("parent_period_id")
    return not period.get("parent_period_id")


def _period_anchor_ids(period: dict, anchors: list[dict]) -> list[str]:
    lord = str(period.get("period_lord") or "")
    house = _int_or_none(period.get("period_house"))
    result = []
    for anchor in anchors:
        if lord and lord in _string_list(anchor.get("natal_bodies")) + _string_list(anchor.get("rulers")):
            result.append(str(anchor.get("anchor_id")))
        if house and house in [_int_or_none(item) for item in anchor.get("houses", [])]:
            result.append(str(anchor.get("anchor_id")))
    return sorted({item for item in result if item})


def _signals_in_window(signals: list[dict], start: date, end: date, *, max_gap_days: int) -> list[dict]:
    low = start - timedelta(days=max_gap_days)
    high = end + timedelta(days=max_gap_days)
    result = []
    for sig in signals:
        sig_start = _parse_date(sig.get("start_date"))
        sig_end = _parse_date(sig.get("end_date"))
        if sig_start and sig_end and sig_start <= high and sig_end >= low:
            result.append(sig)
    return result


def _is_long_clock_signal(sig: dict) -> bool:
    family = str(sig.get("method_family") or "")
    role = str(sig.get("signal_role") or sig.get("clock_role") or "")
    precision = str(sig.get("temporal_precision") or "")
    if role in {"chapter", "chapter_evidence", "time_lord"}:
        return True
    if family in {"RETURN", "PROGRESSION", "SOLAR_ARC", "PROFECTION", "ZODIACAL_RELEASING", "TIME_LORD"} and precision in {"month", "season", "year_or_longer", ""}:
        return True
    start = _parse_date(sig.get("start_date"))
    end = _parse_date(sig.get("end_date"))
    return bool(start and end and (end - start).days > 90)


def _chapter_kind_for_period(period: dict) -> str:
    system = str(period.get("system") or "")
    if system == "annual_profection":
        return "profection_year"
    if system.startswith("zodiacal_releasing"):
        return "zr_period"
    return "long_transit_cycle"


def _chapter_kind_for_signal(sig: dict) -> str:
    family = str(sig.get("method_family") or "")
    variant = str(sig.get("event_kind") or sig.get("method_variant") or "")
    if family == "RETURN":
        return "return_year" if "solar" in variant else "long_transit_cycle"
    if family == "SOLAR_ARC":
        return "solar_arc_chapter"
    if family == "PROGRESSION":
        return "progressed_lunation_phase" if "lunation" in variant or "phase" in variant else "long_transit_cycle"
    if family == "ZODIACAL_RELEASING":
        return "zr_period"
    if family == "PROFECTION":
        return "profection_year"
    return "sustained_transit_chapter"


def _chapter_coherence_allowed(graph: dict, count: int) -> bool:
    if count <= 1:
        return True
    if graph.get("connected"):
        return True
    components = _connected_components(graph)
    return bool(components) and all(len(component) >= 2 for component in components)


def _trigger_precision(signals: list[dict]) -> float:
    trigger_orbs = []
    for sig in signals:
        precision = str(sig.get("temporal_precision") or "")
        role = str(sig.get("signal_role") or sig.get("clock_role") or "")
        if precision in {"instant", "day"} or role in {"trigger_evidence", "trigger", "return"}:
            orb = _float(sig.get("orb"), None)
            allowed = max(0.01, _float(sig.get("allowed_orb"), 3.0))
            if orb is not None:
                trigger_orbs.append(max(0.0, 1.0 - abs(orb) / allowed))
    return max(trigger_orbs, default=0.0)


def _temporal_convergence(signals: list[dict]) -> float:
    peaks = [_parse_date(sig.get("peak_date")) for sig in signals]
    peaks = [item for item in peaks if item]
    if len(peaks) <= 1:
        return 1.0 if peaks else 0.0
    span = (max(peaks) - min(peaks)).days
    return math.exp(-span / 30.0)


def _asteroid_specificity(signals: list[dict]) -> float:
    values = []
    for sig in signals:
        participants = _string_list(sig.get("asteroid_participants"))
        policy = sig.get("asteroid_policy") if isinstance(sig.get("asteroid_policy"), dict) else {}
        if participants or policy.get("participants"):
            exactness = _bounded(sig.get("exactness", 0.7))
            values.append(min(1.0, 0.55 + 0.15 * len(participants) + 0.30 * exactness))
    return max(values, default=0.0)


def _confidence(signals: list[dict]) -> float:
    values = [_bounded(sig.get("epistemic_confidence", sig.get("confidence", 0.7))) for sig in signals]
    if not values:
        return 0.0
    product = 1.0
    for value in values:
        product *= max(0.01, value)
    return product ** (1.0 / len(values))


def _counterforce(signals: list[dict]) -> float:
    if not signals:
        return 0.0
    totals = {axis: 0.0 for axis in OPERATION_AXES}
    for sig in signals:
        profile = sig.get("operation_profile") if isinstance(sig.get("operation_profile"), dict) else {}
        for axis in OPERATION_AXES:
            totals[axis] += _float(profile.get(axis), 0.0)
    dominant = max(totals, key=totals.get) if totals else ""
    if dominant in CONSTRUCTIVE:
        opposed = DISSOLVING
    elif dominant in DISSOLVING:
        opposed = CONSTRUCTIVE
    else:
        opposed = set(OPERATION_AXES) - {dominant}
    opposition = 0.0
    count = 0
    for sig in signals:
        profile = sig.get("operation_profile") if isinstance(sig.get("operation_profile"), dict) else {}
        mass = sum(max(0.0, _float(profile.get(axis), 0.0)) for axis in OPERATION_AXES)
        if mass <= 0:
            continue
        opposition += sum(max(0.0, _float(profile.get(axis), 0.0)) for axis in opposed) / mass
        count += 1
    return opposition / count if count else 0.0


def _complexity(signals: list[dict]) -> float:
    totals = {axis: 0.0 for axis in OPERATION_AXES}
    for sig in signals:
        profile = sig.get("operation_profile") if isinstance(sig.get("operation_profile"), dict) else {}
        for axis in OPERATION_AXES:
            totals[axis] += max(0.0, _float(profile.get(axis), 0.0))
    total = sum(totals.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in totals.values():
        if value > 0:
            p = value / total
            entropy -= p * math.log(p)
    return min(1.0, entropy / math.log(len(OPERATION_AXES)))


def _window_width(signals: list[dict]) -> float:
    starts = [_parse_date(sig.get("start_date")) for sig in signals]
    ends = [_parse_date(sig.get("end_date")) for sig in signals]
    starts = [item for item in starts if item]
    ends = [item for item in ends if item]
    if not starts or not ends:
        return 0.0
    days = max(1, (max(ends) - min(starts)).days + 1)
    return math.exp(-days / 3.0)


def _polarity(signals: list[dict]) -> float:
    constructive = 0.0
    dissolving = 0.0
    for sig in signals:
        profile = sig.get("operation_profile") if isinstance(sig.get("operation_profile"), dict) else {}
        constructive += sum(_float(profile.get(axis), 0.0) for axis in CONSTRUCTIVE)
        dissolving += sum(_float(profile.get(axis), 0.0) for axis in DISSOLVING)
    total = constructive + dissolving
    if total <= 0:
        return 0.0
    return round((constructive - dissolving) / total, 4)


def _same_rulership_chain(payload: dict, body_a: str, body_b: str) -> bool:
    if not body_a or not body_b:
        return False
    ruler_a = _ruler_for_body(payload, body_a)
    ruler_b = _ruler_for_body(payload, body_b)
    return bool(ruler_a and (ruler_a == body_b or ruler_a == ruler_b or ruler_b == body_a))


def _ruler_for_body(payload: dict, body: str) -> str:
    sign = _body_sign(payload, body)
    return TRADITIONAL_RULERS.get(sign, "")


def _body_sign(payload: dict, body: str) -> str:
    for collection_name in ("standard_planets", "angles", "custom_asteroids"):
        collection = payload.get(collection_name) if isinstance(payload.get(collection_name), dict) else {}
        data = collection.get(body)
        if isinstance(data, dict):
            return str(data.get("sign") or "")
    return ""


def _target_house(payload: dict, body: str) -> int | None:
    if not body:
        return None
    if body.isdigit():
        house = int(body)
        return house if 1 <= house <= 12 else None
    aliases = {"ASC": "Ascendant", "MC": "Midheaven", "DSC": "Descendant", "IC": "Imum_Coeli"}
    names = [body, aliases.get(body, "")]
    for collection_name in ("standard_planets", "angles", "custom_asteroids"):
        collection = payload.get(collection_name) if isinstance(payload.get(collection_name), dict) else {}
        for name in names:
            data = collection.get(name)
            if isinstance(data, dict):
                return _int_or_none(data.get("house"))
    return None


def _build_aspect_orb_lookup(payload: dict) -> dict[frozenset, float]:
    """
    Precomputes a {frozenset({body_a, body_b}): tightest_orb} map from the
    natal aspect matrix once, so _natal_aspect_orb becomes an O(1) lookup
    instead of an O(len(aspects)) rescan on every call. Performance fix:
    coherence_graph is invoked once per chapter/anchor-group (potentially
    100+ times per report), each internally checking every signal pair --
    without this cache, that means re-scanning the full ~500+ entry aspect
    list on every pair on every group, which measured multiple minutes of
    wall-clock time on a real personal_forecast report before this fix.
    """
    lookup: dict[frozenset, float] = {}
    for aspect in payload.get("aspects", []) if isinstance(payload.get("aspects"), list) else []:
        if not isinstance(aspect, dict):
            continue
        body_a = str(aspect.get("body_1") or aspect.get("body_a") or "")
        body_b = str(aspect.get("body_2") or aspect.get("body_b") or "")
        if not body_a or not body_b:
            continue
        pair = frozenset({body_a, body_b})
        orb = abs(_float(aspect.get("orb"), 999.0))
        if pair not in lookup or orb < lookup[pair]:
            lookup[pair] = orb
    return lookup


def _build_anchor_index_lookup(anchors: list[dict]) -> dict[str, set[str]]:
    """Precomputes {anchor_id: {index_names}} once instead of rescanning the
    full anchors list (up to ~70+ entries) on every _index_driver_sets call."""
    lookup: dict[str, set[str]] = {}
    for anchor in anchors:
        anchor_id = anchor.get("anchor_id")
        if not anchor_id:
            continue
        links = set()
        for link in anchor.get("proprietary_index_links", []) or []:
            if isinstance(link, dict):
                idx = str(link.get("index") or "")
                if idx:
                    links.add(idx)
        lookup[anchor_id] = links
    return lookup


def _ensure_lookups(anchors: list[dict], payload: dict, lookups: dict | None) -> dict:
    if lookups is not None:
        return lookups
    return {
        "aspect_orb": _build_aspect_orb_lookup(payload),
        "anchor_index_links": _build_anchor_index_lookup(anchors),
    }


def _natal_aspect_orb(payload: dict, body_a: str, body_b: str, *, lookups: dict | None = None) -> float:
    if not body_a or not body_b or body_a == body_b:
        return 999.0
    if lookups is not None:
        return lookups["aspect_orb"].get(frozenset({body_a, body_b}), 999.0)
    for aspect in payload.get("aspects", []) if isinstance(payload.get("aspects"), list) else []:
        if not isinstance(aspect, dict):
            continue
        pair = {str(aspect.get("body_1") or aspect.get("body_a") or ""), str(aspect.get("body_2") or aspect.get("body_b") or "")}
        if {body_a, body_b} == pair:
            return abs(_float(aspect.get("orb"), 999.0))
    return 999.0


def _index_driver_sets(sig: dict, anchors: list[dict], *, lookups: dict | None = None) -> set[str]:
    anchor_ids = set(_string_list(sig.get("natal_anchor_ids")))
    if lookups is not None:
        result: set[str] = set()
        for anchor_id in anchor_ids:
            result.update(lookups["anchor_index_links"].get(anchor_id, set()))
        return {item for item in result if item}
    result = set()
    for anchor in anchors:
        if anchor.get("anchor_id") not in anchor_ids:
            continue
        for link in anchor.get("proprietary_index_links", []) or []:
            if isinstance(link, dict):
                result.add(str(link.get("index") or ""))
    return {item for item in result if item}


def _normalized_group(sig: dict) -> str:
    group = str(sig.get("independence_group") or "")
    mapping = {
        "transit_clock": "transit_family",
        "lunar_phase_clock": "lunation_family",
        "return_clock": "return_family_generic",
        "progression_clock": "progression_family",
        "solar_arc_clock": "solar_arc_family",
    }
    if group in mapping:
        return mapping[group]
    family = str(sig.get("method_family") or "")
    if not group or group == "unknown_clock":
        return {
            "TRANSIT": "transit_family",
            "PROPRIETARY_TRANSIT": "proprietary_transit_family",
            "LUNATION": "lunation_family",
            "RETURN": "return_family_generic",
            "PROGRESSION": "progression_family",
            "SOLAR_ARC": "solar_arc_family",
            "PROFECTION": "profection_family",
            "ZODIACAL_RELEASING": "zr_family_generic",
        }.get(family, "unknown_family")
    return group


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _is_connected(nodes: list[str], edges: list[dict]) -> bool:
    if len(nodes) <= 1:
        return True
    components = _connected_components({"nodes": nodes, "edges": edges})
    return len(components) == 1


def _connected_components(graph: dict) -> list[set[str]]:
    nodes = set(graph.get("nodes") or [])
    adjacency = {node: set() for node in nodes}
    for edge in graph.get("edges") or []:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source in adjacency and target in adjacency:
            adjacency[source].add(target)
            adjacency[target].add(source)
    components: list[set[str]] = []
    while nodes:
        start = nodes.pop()
        stack = [start]
        component = {start}
        while stack:
            node = stack.pop()
            for neighbor in adjacency.get(node, set()):
                if neighbor in nodes:
                    nodes.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _largest_connected_component(graph: dict) -> set[str]:
    components = _connected_components(graph)
    return max(components, key=len) if components else set()


def _dedupe_chapters(chapters: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for chapter in sorted(chapters, key=lambda item: (item.get("start_at", ""), item.get("chapter_id", ""))):
        chapter_id = str(chapter.get("chapter_id") or "")
        if chapter_id and chapter_id not in seen:
            seen.add(chapter_id)
            result.append(chapter)
    return result


def _merged_confidence_components(signals: list[dict]) -> dict:
    totals: dict[str, list[float]] = {}
    text_values: dict[str, str] = {}
    for sig in signals:
        comps = sig.get("confidence_components") if isinstance(sig.get("confidence_components"), dict) else {}
        for key, value in comps.items():
            try:
                totals.setdefault(key, []).append(float(value))
            except (TypeError, ValueError):
                text_values[key] = str(value)
    result = {key: round(sum(values) / len(values), 4) for key, values in totals.items() if values}
    result.update(text_values)
    return result


def _chapter_birth_time_dependency(signals: list[dict], period: dict | None) -> str:
    values = [str(sig.get("birth_time_dependency") or "") for sig in signals]
    if period:
        values.append(str(period.get("birth_time_dependency") or ""))
    if "hard" in values:
        return "hard"
    if "soft" in values:
        return "soft"
    if any("angle" in str(sig.get("angle_eligibility") or "") for sig in signals):
        return "hard"
    return "none"


def _cluster_key(signals: list[dict]) -> str:
    return "|".join(sorted(str(sig.get("signal_id") or "") for sig in signals))


def _strength(sig: dict) -> float:
    return _bounded(sig.get("signal_strength", sig.get("trigger_strength", 0.0)))


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


def _hash_id(prefix: str, value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:8]}"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, numeric))
