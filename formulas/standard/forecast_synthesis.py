"""
Forecast synthesis objects for Tier 4.

This layer consumes normalized event-like evidence and returns structured
terrain objects. It does not render prose, choose templates, or collapse
disagreement into a single mood field.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any


SYNTHESIS_SCHEMA_VERSION = "tier4.forecast_synthesis.v1"
CLUSTER_PROXIMITY_DAYS = 14

EVENT_METHOD_FAMILY = {
    "transit": "TRANSIT",
    "natal_transit": "TRANSIT",
    "station": "TRANSIT_STATION",
    "planetary_station": "TRANSIT_STATION",
    "ingress": "INGRESS",
    "house_ingress": "INGRESS",
    "eclipse": "LUNATION",
    "lunation": "LUNATION",
    "convergence": "CONVERGENCE",
    "convergence_window": "CONVERGENCE",
    "progression": "PROGRESSION",
    "solar_arc": "SOLAR_ARC",
    "return": "RETURN",
    "annual_profection": "TIME_LORD",
    "zodiacal_releasing": "TIME_LORD",
    "zodiacal_releasing_fortune": "ZODIACAL_RELEASING_FORTUNE",
    "zodiacal_releasing_spirit": "ZODIACAL_RELEASING_SPIRIT",
}

SUPPORTIVE_OPERATIONS = {"support", "stabilize", "amplify", "reveal", "flow"}
PRESSURE_OPERATIONS = {"challenge", "disrupt", "dissolve", "activate", "friction"}
CONFLICTING_OPERATION_PAIRS = {
    frozenset(("stabilize", "disrupt")),
    frozenset(("stabilize", "dissolve")),
    frozenset(("support", "disrupt")),
    frozenset(("support", "dissolve")),
    frozenset(("flow", "friction")),
    frozenset(("amplify", "dissolve")),
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                return datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                return None
    return None


def _iso_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def _event_type(event: dict) -> str:
    value = str(
        event.get("event_type")
        or event.get("legacy_event_type")
        or event.get("source_event_type")
        or event.get("system")
        or ""
    ).strip().lower()
    if value.startswith("zodiacal_releasing_"):
        return value
    return value


def _method_family(event: dict) -> str:
    explicit = str(event.get("method_family") or "").strip().upper()
    if explicit:
        if explicit == "RETURN":
            body = str(event.get("return_body") or event.get("transit_planet") or "").strip().upper()
            if body in {"SUN", "MOON", "JUPITER", "SATURN"}:
                return f"RETURN_{body}"
        if explicit == "ZODIACAL_RELEASING":
            system = str(event.get("system") or "").strip().upper()
            if system.endswith("_FORTUNE"):
                return "ZODIACAL_RELEASING_FORTUNE"
            if system.endswith("_SPIRIT"):
                return "ZODIACAL_RELEASING_SPIRIT"
        return explicit
    return EVENT_METHOD_FAMILY.get(_event_type(event), _event_type(event).upper() or "UNKNOWN")


def _event_id(event: dict, index: int) -> str:
    explicit = str(
        event.get("event_id")
        or event.get("cycle_id")
        or event.get("convergence_id")
        or event.get("signal_id")
        or ""
    ).strip()
    if explicit:
        return explicit
    parts = [
        _method_family(event),
        str(event.get("transit_planet") or event.get("source_body") or ""),
        str(event.get("aspect") or ""),
        str(event.get("natal_target") or event.get("target_body") or ""),
        str(event.get("peak_date") or event.get("peak_datetime") or ""),
        str(index),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"synth_ev_{digest}"


def _operation_from_event(event: dict) -> str:
    explicit = str(event.get("dominant_operation") or event.get("operation") or "").strip().lower()
    if explicit:
        return explicit
    profile = event.get("operation_profile")
    if isinstance(profile, dict) and profile:
        return max(profile.items(), key=lambda item: _safe_float(item[1]))[0].lower()
    conflict = _safe_float(
        event.get("counterforce_conflict", event.get("conflict_score", event.get("counterforce_score"))),
        default=0.0,
    )
    if conflict > 0:
        return "friction"
    character = str(event.get("aspect_character") or event.get("tone") or "").strip().lower()
    if character in {"flowing", "supportive"}:
        return "flow"
    if character in {"challenging", "hard"}:
        return "friction"
    etype = _event_type(event)
    if etype in {"station", "planetary_station", "eclipse", "lunation"}:
        return "activate"
    return "unknown"


def _topics_for_event(event: dict, house_domains: dict[int, str] | dict[str, str]) -> list[str]:
    topics: list[str] = []
    for key in ("topic_keys", "domain_keys", "shared_life_domains"):
        values = event.get(key)
        if isinstance(values, (list, tuple, set)):
            topics.extend(str(value).strip() for value in values if str(value).strip())
    for key in ("natal_house", "house_number", "whole_sign_house", "transit_house"):
        try:
            house = int(event.get(key) or 0)
        except (TypeError, ValueError):
            house = 0
        if house:
            domain = house_domains.get(house) or house_domains.get(str(house)) if house_domains else ""
            if domain:
                topics.append(str(domain))
            topics.append(f"house:{house}")
    target = str(event.get("natal_target") or event.get("target_body") or "").strip()
    if target:
        topics.append(f"target:{target}")
    return sorted({topic for topic in topics if topic})


def _source_ref(event: dict, event_id: str) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "method_family": _method_family(event),
        "event_type": _event_type(event),
        "peak_at": _iso_datetime(_safe_datetime(event.get("peak_datetime") or event.get("peak_at") or event.get("peak_date"))),
        "score": round(_safe_float(event.get("combined_intensity_score", event.get("score"))), 4),
    }


def normalize_synthesis_evidence(
    events: list[dict],
    house_domains: dict[int, str] | dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Normalize heterogeneous event dicts into synthesis evidence records."""
    normalized: list[dict[str, Any]] = []
    house_domains = house_domains or {}
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        event_id = _event_id(event, index)
        peak = _safe_datetime(event.get("peak_datetime") or event.get("peak_at") or event.get("peak_date"))
        start = _safe_datetime(event.get("entry_datetime") or event.get("start_at") or event.get("entry_date")) or peak
        end = _safe_datetime(event.get("leave_datetime") or event.get("end_at") or event.get("leave_date")) or peak
        operation = _operation_from_event(event)
        method_family = _method_family(event)
        score = _clamp(
            _safe_float(event.get("combined_intensity_score", event.get("score", event.get("raw_score"))))
        )
        conflict = _clamp(
            abs(
                _safe_float(
                    event.get(
                        "counterforce_conflict",
                        event.get("conflict_score", event.get("counterforce_score")),
                    )
                )
            )
        )
        normalized.append(
            {
                "evidence_id": f"evd_{event_id}",
                "event_id": event_id,
                "method_family": method_family,
                "independence_group": str(event.get("independence_group") or method_family.lower()),
                "event_type": _event_type(event),
                "operation": operation,
                "operation_source": (
                    "declared"
                    if event.get("dominant_operation") or event.get("operation") or event.get("operation_profile")
                    else "derived_from_structured_event_fields"
                ),
                "score": round(score, 4),
                "structural_score": round(
                    _clamp(_safe_float(event.get("structural_score", event.get("structural_importance", score)))),
                    4,
                ),
                "confidence": round(_clamp(_safe_float(event.get("confidence", event.get("epistemic_confidence", 0.0)))), 4),
                "conflict_score": round(conflict, 4),
                "start_at": start,
                "peak_at": peak,
                "end_at": end,
                "topics": _topics_for_event(event, house_domains),
                "source_ref": _source_ref(event, event_id),
                "score_components": event.get("score_components") if isinstance(event.get("score_components"), dict) else {},
                "ranking_diagnostics": event.get("ranking_diagnostics") if isinstance(event.get("ranking_diagnostics"), dict) else {},
            }
        )
    normalized.sort(key=lambda item: (item.get("peak_at") or datetime.max.replace(tzinfo=timezone.utc), item["event_id"]))
    return normalized


def _operations_compatible(operation_a: str, operation_b: str) -> str:
    if "unknown" in {operation_a, operation_b}:
        return "ambiguous"
    if frozenset((operation_a, operation_b)) in CONFLICTING_OPERATION_PAIRS:
        return "contradictory"
    if operation_a == operation_b:
        return "supportive"
    if operation_a in SUPPORTIVE_OPERATIONS and operation_b in SUPPORTIVE_OPERATIONS:
        return "supportive"
    if operation_a in PRESSURE_OPERATIONS and operation_b in PRESSURE_OPERATIONS:
        return "supportive"
    if {operation_a, operation_b} & SUPPORTIVE_OPERATIONS and {operation_a, operation_b} & PRESSURE_OPERATIONS:
        return "ambiguous"
    return "ambiguous"


def _evidence_overlap(a: dict, b: dict, proximity_days: int = CLUSTER_PROXIMITY_DAYS) -> bool:
    a_peak = a.get("peak_at")
    b_peak = b.get("peak_at")
    if a_peak is not None and b_peak is not None:
        return abs((a_peak - b_peak).days) <= proximity_days
    a_start = a.get("start_at")
    a_end = a.get("end_at") or a_start
    b_start = b.get("start_at")
    b_end = b.get("end_at") or b_start
    if a_start is None or a_end is None or b_start is None or b_end is None:
        return False
    return a_start <= b_end + timedelta(days=proximity_days) and b_start <= a_end + timedelta(days=proximity_days)


def _shared_topics(a: dict, b: dict) -> set[str]:
    return set(a.get("topics") or []) & set(b.get("topics") or [])


def _cluster_label(items: list[dict]) -> str:
    if not items:
        return "background"
    method_count = len({item["method_family"] for item in items})
    if method_count <= 1:
        return "isolated" if len(items) == 1 else "supportive"
    pair_states = []
    for index, item in enumerate(items):
        for other in items[index + 1:]:
            pair_states.append(_operations_compatible(item["operation"], other["operation"]))
    if "contradictory" in pair_states or any(item["conflict_score"] >= 0.45 for item in items):
        return "contradictory"
    if pair_states and all(state == "supportive" for state in pair_states):
        return "convergent"
    return "ambiguous"


def build_peak_window_clusters(evidence: list[dict]) -> list[dict[str, Any]]:
    clusters: list[list[dict]] = []
    for item in evidence:
        placed = False
        for cluster in clusters:
            if any(_evidence_overlap(item, existing) and (_shared_topics(item, existing) or item["method_family"] != existing["method_family"]) for existing in cluster):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])

    result: list[dict[str, Any]] = []
    for cluster in clusters:
        cluster.sort(key=lambda item: (item.get("peak_at") or datetime.max.replace(tzinfo=timezone.utc), item["event_id"]))
        start_values = [item.get("start_at") or item.get("peak_at") for item in cluster if item.get("start_at") or item.get("peak_at")]
        end_values = [item.get("end_at") or item.get("peak_at") for item in cluster if item.get("end_at") or item.get("peak_at")]
        topic_counts: dict[str, int] = {}
        for item in cluster:
            for topic in item.get("topics") or []:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        label = _cluster_label(cluster)
        digest = hashlib.sha256("|".join(item["event_id"] for item in cluster).encode("utf-8")).hexdigest()[:12]
        result.append(
            {
                "cluster_id": f"terrain_cluster_{digest}",
                "label": label,
                "start_at": _iso_datetime(min(start_values) if start_values else None),
                "end_at": _iso_datetime(max(end_values) if end_values else None),
                "peak_at": _iso_datetime(max(cluster, key=lambda item: item["score"]).get("peak_at")),
                "method_families": sorted({item["method_family"] for item in cluster}),
                "operations": sorted({item["operation"] for item in cluster}),
                "topic_keys": sorted(topic_counts, key=lambda key: (topic_counts[key], key), reverse=True)[:6],
                "source_event_ids": [item["event_id"] for item in cluster],
                "supporting_methods": sorted({item["method_family"] for item in cluster if item["conflict_score"] < 0.45}),
                "complicating_methods": sorted({item["method_family"] for item in cluster if item["conflict_score"] >= 0.45}),
                "provenance": [item["source_ref"] for item in cluster],
            }
        )
    result.sort(key=lambda item: (item.get("start_at") or datetime.max.replace(tzinfo=timezone.utc), item["cluster_id"]))
    return result


def detect_method_contradictions(evidence: list[dict]) -> list[dict[str, Any]]:
    contradictions: list[dict[str, Any]] = []
    for index, item in enumerate(evidence):
        for other in evidence[index + 1:]:
            if item["method_family"] == other["method_family"]:
                continue
            if not _evidence_overlap(item, other):
                continue
            shared = sorted(_shared_topics(item, other))
            compatibility = _operations_compatible(item["operation"], other["operation"])
            explicit_conflict = max(item["conflict_score"], other["conflict_score"]) >= 0.45
            if compatibility != "contradictory" and not explicit_conflict:
                continue
            digest = hashlib.sha256(f"{item['event_id']}|{other['event_id']}".encode("utf-8")).hexdigest()[:12]
            contradictions.append(
                {
                    "contradiction_id": f"terrain_contra_{digest}",
                    "label": "contradictory",
                    "method_families": [item["method_family"], other["method_family"]],
                    "operations": [item["operation"], other["operation"]],
                    "shared_topics": shared,
                    "compatibility_basis": "declared_operation_compatibility",
                    "supporting_event_ids": [item["event_id"]],
                    "complicating_event_ids": [other["event_id"]],
                    "provenance": [item["source_ref"], other["source_ref"]],
                }
            )
    return contradictions


def _period_for_month(report_start: datetime, offset: int) -> tuple[datetime, datetime]:
    month = report_start.month - 1 + offset
    year = report_start.year + month // 12
    month = month % 12 + 1
    start = report_start.replace(year=year, month=month, day=1)
    if month == 12:
        end = start.replace(year=year + 1, month=1)
    else:
        end = start.replace(month=month + 1)
    if offset == 0:
        start = report_start
    return start, end


def _active_in_period(item: dict, period_start: datetime, period_end: datetime) -> bool:
    start = item.get("start_at") or item.get("peak_at")
    end = item.get("end_at") or item.get("peak_at") or start
    if start is None or end is None:
        return False
    return start < period_end and end >= period_start


def _monthly_zone(
    active: list[dict],
    previous_score: float,
    peak_score: float,
    max_score: float,
) -> str:
    if not active or max_score <= 0:
        return "background"
    has_conflict = any(item["conflict_score"] >= 0.45 or item["operation"] in {"disrupt", "dissolve", "friction"} for item in active)
    ratio = peak_score / max_score if max_score else 0.0
    supportive = sum(1 for item in active if item["operation"] in SUPPORTIVE_OPERATIONS)
    pressure = sum(1 for item in active if item["operation"] in PRESSURE_OPERATIONS)
    if has_conflict and ratio >= 0.35:
        return "pressure"
    if ratio >= 0.65 and supportive >= pressure:
        return "opening"
    if previous_score > 0 and peak_score < previous_score * 0.72:
        return "recovery"
    if ratio >= 0.30:
        return "chapter"
    return "background"


def build_monthly_terrain(
    evidence: list[dict],
    report_start: datetime,
    months: list[dict] | None = None,
) -> list[dict[str, Any]]:
    months = months or []
    if report_start.tzinfo is None:
        report_start = report_start.replace(tzinfo=timezone.utc)
    month_periods = []
    for offset in range(max(12, len(months))):
        start, end = _period_for_month(report_start, offset)
        label = str(months[offset].get("name") or start.strftime("%B %Y")) if offset < len(months) else start.strftime("%B %Y")
        month_periods.append((offset, label, start, end))

    peak_scores = []
    active_by_month: list[tuple[int, str, datetime, datetime, list[dict], float]] = []
    for offset, label, start, end in month_periods:
        active = [item for item in evidence if _active_in_period(item, start, end)]
        peak_score = max((item["score"] for item in active), default=0.0)
        peak_scores.append(peak_score)
        active_by_month.append((offset, label, start, end, active, peak_score))

    max_score = max(peak_scores, default=0.0)
    terrain = []
    previous_score = 0.0
    for offset, label, start, end, active, peak_score in active_by_month:
        zone = _monthly_zone(active, previous_score, peak_score, max_score)
        method_families = sorted({item["method_family"] for item in active})
        topic_counts: dict[str, int] = {}
        for item in active:
            for topic in item.get("topics") or []:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        terrain.append(
            {
                "month_index": offset + 1,
                "month_name": label,
                "zone": zone,
                "synthesis_label": "trigger" if zone == "pressure" else ("aftermath" if zone == "recovery" else zone),
                "period_start": _iso_datetime(start),
                "period_end": _iso_datetime(end),
                "relative_intensity": round((peak_score / max_score) if max_score else 0.0, 4),
                "method_families": method_families,
                "dominant_topics": sorted(topic_counts, key=lambda key: (topic_counts[key], key), reverse=True)[:5],
                "source_event_ids": [item["event_id"] for item in active],
                "provenance": [item["source_ref"] for item in active[:8]],
            }
        )
        previous_score = peak_score
    return terrain


def build_repeating_themes(evidence: list[dict]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict]] = {}
    for item in evidence:
        for topic in item.get("topics") or []:
            buckets.setdefault(topic, []).append(item)
    themes = []
    for topic, items in buckets.items():
        methods = sorted({item["method_family"] for item in items})
        if len(items) < 2 and len(methods) < 2:
            continue
        themes.append(
            {
                "theme_key": topic,
                "label": "repeating_natal_theme",
                "event_count": len(items),
                "method_families": methods,
                "source_event_ids": [item["event_id"] for item in items],
                "provenance": [item["source_ref"] for item in items[:8]],
            }
        )
    themes.sort(key=lambda item: (item["event_count"], len(item["method_families"]), item["theme_key"]), reverse=True)
    return themes[:12]


def build_evidence_chapters(
    monthly_terrain: list[dict],
    repeating_themes: list[dict],
    contradictions: list[dict],
) -> list[dict[str, Any]]:
    chapters = []
    contradiction_event_ids = {
        event_id
        for item in contradictions
        for event_id in item.get("supporting_event_ids", []) + item.get("complicating_event_ids", [])
    }
    for month in monthly_terrain:
        if month["zone"] == "background" and not month["source_event_ids"]:
            continue
        source_ids = month["source_event_ids"]
        chapters.append(
            {
                "chapter_id": f"terrain_chapter_month_{month['month_index']}",
                "chapter_type": "monthly_terrain",
                "label": month["synthesis_label"],
                "time_scope": month["month_name"],
                "topic_keys": month["dominant_topics"],
                "supporting_event_ids": [event_id for event_id in source_ids if event_id not in contradiction_event_ids],
                "complicating_event_ids": [event_id for event_id in source_ids if event_id in contradiction_event_ids],
                "provenance": month["provenance"],
            }
        )
    for theme in repeating_themes[:6]:
        chapters.append(
            {
                "chapter_id": "terrain_chapter_theme_" + hashlib.sha256(theme["theme_key"].encode("utf-8")).hexdigest()[:10],
                "chapter_type": "repeating_theme",
                "label": "chapter",
                "time_scope": "annual",
                "topic_keys": [theme["theme_key"]],
                "supporting_event_ids": theme["source_event_ids"],
                "complicating_event_ids": [],
                "provenance": theme["provenance"],
            }
        )
    return chapters


def build_annual_terrain_map(
    evidence: list[dict],
    monthly_terrain: list[dict],
    clusters: list[dict],
    contradictions: list[dict],
    repeating_themes: list[dict],
) -> dict[str, Any]:
    topic_counts: dict[str, int] = {}
    for item in evidence:
        for topic in item.get("topics") or []:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    method_families = sorted({item["method_family"] for item in evidence})
    if contradictions:
        agreement_label = "contradictory"
    elif any(cluster["label"] == "convergent" for cluster in clusters):
        agreement_label = "convergent"
    elif len(method_families) > 1:
        agreement_label = "supportive"
    elif evidence:
        agreement_label = "isolated"
    else:
        agreement_label = "background"
    zone_counts: dict[str, int] = {}
    for month in monthly_terrain:
        zone_counts[month["zone"]] = zone_counts.get(month["zone"], 0) + 1
    return {
        "label": agreement_label,
        "method_families": method_families,
        "dominant_topics": sorted(topic_counts, key=lambda key: (topic_counts[key], key), reverse=True)[:8],
        "monthly_zone_counts": zone_counts,
        "cluster_count": len(clusters),
        "contradiction_count": len(contradictions),
        "repeating_theme_count": len(repeating_themes),
        "source_event_ids": [item["event_id"] for item in evidence],
        "provenance": [item["source_ref"] for item in evidence[:20]],
    }


def build_forecast_synthesis(
    events: list[dict],
    *,
    report_start: datetime,
    report_end: datetime | None = None,
    months: list[dict] | None = None,
    house_domains: dict[int, str] | dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build Tier 4 forecast terrain objects from normalized evidence."""
    evidence = normalize_synthesis_evidence(events, house_domains)
    clusters = build_peak_window_clusters(evidence)
    contradictions = detect_method_contradictions(evidence)
    monthly_terrain = build_monthly_terrain(evidence, report_start, months)
    repeating_themes = build_repeating_themes(evidence)
    chapters = build_evidence_chapters(monthly_terrain, repeating_themes, contradictions)
    annual = build_annual_terrain_map(
        evidence,
        monthly_terrain,
        clusters,
        contradictions,
        repeating_themes,
    )
    return {
        "schema_version": SYNTHESIS_SCHEMA_VERSION,
        "report_start": _iso_datetime(report_start),
        "report_end": _iso_datetime(report_end),
        "annual_terrain_map": annual,
        "monthly_terrain": monthly_terrain,
        "peak_window_clusters": clusters,
        "contradictions": contradictions,
        "repeating_natal_themes": repeating_themes,
        "evidence_chapters": chapters,
        "debug_trace": {
            "normalized_evidence_count": len(evidence),
            "source_event_ids": [item["event_id"] for item in evidence],
            "synthesis_labels_used": sorted(
                {
                    annual["label"],
                    *(month["synthesis_label"] for month in monthly_terrain),
                    *(cluster["label"] for cluster in clusters),
                }
            ),
        },
    }
