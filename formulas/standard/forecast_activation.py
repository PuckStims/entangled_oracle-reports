"""
Shared natal-activation helpers for the transit and predictive forecast layers.

This module translates the Phase 2 natal-architecture outputs into reusable
weights so forecast events can distinguish:
  - concentration
  - reader-facing activity
  - structural importance
  - natal relevance
  - theme convergence
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from formulas.standard.aspect_architecture import evaluate_aspect_architecture
from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.house_emphasis import evaluate_house_emphasis
from formulas.standard.named_configurations import evaluate_named_configurations
from formulas.standard.natal_convergence import evaluate_standard_natal_convergence
from formulas.standard.planetary_prominence import evaluate_prominence
from formulas.standard.rulership_network import evaluate_rulership_network

ANGLE_ALIASES = {
    "ASC": "Ascendant",
    "MC": "Midheaven",
    "DSC": "Descendant",
    "IC": "Imum_Coeli",
    "Ascendant": "Ascendant",
    "Midheaven": "Midheaven",
    "Descendant": "Descendant",
    "Imum Coeli": "Imum_Coeli",
    "Imum_Coeli": "Imum_Coeli",
    "Vertex": "Vertex",
}

CANONICAL_TO_SHORT = {
    "Ascendant": "ASC",
    "Midheaven": "MC",
    "Descendant": "DSC",
    "Imum_Coeli": "IC",
    "Vertex": "Vertex",
}

BASE_TARGET_WEIGHTS = {
    "Sun": 0.72,
    "Moon": 0.72,
    "Ascendant": 0.82,
    "Midheaven": 0.82,
    "Descendant": 0.70,
    "Imum_Coeli": 0.70,
    "Vertex": 0.66,
}

PROMINENCE_BONUS = {
    "DOMINANT": 0.26,
    "PROMINENT": 0.20,
    "PRESENT": 0.10,
    "BACKGROUND": 0.0,
}

CONNECTIVITY_BONUS = {
    "hub": 0.14,
    "high_connectivity": 0.10,
    "low_connectivity": 0.04,
    "isolated": 0.0,
}

EVENT_TYPE_BASELINES = {
    "transit": 0.34,
    "station": 0.30,
    "eclipse": 0.30,
    "ingress": 0.14,
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalize_forecast_target_name(name: str | None) -> str:
    text = str(name or "").strip()
    if not text:
        return ""
    return ANGLE_ALIASES.get(text, text)


def _all_target_aliases(name: str) -> set[str]:
    canonical = normalize_forecast_target_name(name)
    aliases = {canonical}
    short = CANONICAL_TO_SHORT.get(canonical)
    if short:
        aliases.add(short)
    for key, value in ANGLE_ALIASES.items():
        if value == canonical:
            aliases.add(key)
    return {alias for alias in aliases if alias}


def _base_target_weight(body_name: str) -> float:
    canonical = normalize_forecast_target_name(body_name)
    if canonical in BASE_TARGET_WEIGHTS:
        return BASE_TARGET_WEIGHTS[canonical]
    return 0.34


def _extract_pattern_focal_points(configurations: list[dict[str, Any]]) -> dict[str, float]:
    focal_points: dict[str, float] = {}
    for config in configurations:
        bodies = config.get("focal_points") or config.get("bodies") or []
        if not isinstance(bodies, list):
            continue
        if config.get("type") in {"stellium", "grand_trine", "kite", "t_square", "grand_cross", "yod"}:
            bonus = 0.12
        else:
            bonus = 0.08
        for body in bodies:
            if isinstance(body, str):
                canonical = normalize_forecast_target_name(body)
                focal_points[canonical] = max(focal_points.get(canonical, 0.0), bonus)
    return focal_points


def build_forecast_activation_profile(payload: dict) -> dict[str, Any]:
    """
    Build one reusable natal-priority profile for the full forecast pass.
    """
    chart_ruler = evaluate_chart_ruler(payload)
    prominence = evaluate_prominence(payload)
    house_emphasis = evaluate_house_emphasis(payload)
    aspect_architecture = evaluate_aspect_architecture(payload)
    named_configurations = evaluate_named_configurations(payload)
    natal_convergence = evaluate_standard_natal_convergence(payload)
    rulership_network = evaluate_rulership_network(payload)

    target_weights: dict[str, float] = {}
    central_planets: dict[str, float] = {}
    for item in natal_convergence.get("central_planets", []):
        label = normalize_forecast_target_name(item.get("label"))
        central_planets[label] = max(
            central_planets.get(label, 0.0),
            float(item.get("normalized_relevance_score", 0.0) or 0.0),
        )

    focal_points = _extract_pattern_focal_points(named_configurations.get("configurations", []))
    chart_ruler_name = normalize_forecast_target_name(chart_ruler.get("primary_ruler"))

    prominence_map = {
        normalize_forecast_target_name(item.get("body")): item
        for item in prominence.get("rankings", [])
    }
    connectivity_map = {
        normalize_forecast_target_name(body): record
        for body, record in aspect_architecture.get("connectivity", {}).items()
    }

    bodies_to_score: set[str] = set(prominence_map) | set(connectivity_map) | set(central_planets)
    bodies_to_score.update({"Sun", "Moon", "Ascendant", "Midheaven", "Descendant", "Imum_Coeli", "Vertex"})
    if chart_ruler_name:
        bodies_to_score.add(chart_ruler_name)

    for body_name in bodies_to_score:
        canonical = normalize_forecast_target_name(body_name)
        score = _base_target_weight(canonical)
        if canonical == chart_ruler_name and canonical:
            score += 0.22
        prominence_record = prominence_map.get(canonical, {})
        score += PROMINENCE_BONUS.get(str(prominence_record.get("tier") or "BACKGROUND"), 0.0)
        connectivity_record = connectivity_map.get(canonical, {})
        score += CONNECTIVITY_BONUS.get(str(connectivity_record.get("state") or "isolated"), 0.0)
        score += min(0.18, central_planets.get(canonical, 0.0) * 0.22)
        score += focal_points.get(canonical, 0.0)
        for alias in _all_target_aliases(canonical):
            target_weights[alias] = round(_clamp(score), 4)

    house_weights: dict[int, float] = {}
    for item in house_emphasis.get("rankings", []):
        house_number = int(item.get("house") or 0)
        if not house_number:
            continue
        emphasis = float(item.get("house_emphasis_normalized", 0.0) or 0.0)
        score = emphasis * 0.72
        ruler = normalize_forecast_target_name(item.get("ruler"))
        if ruler:
            score += min(0.16, target_weights.get(ruler, 0.0) * 0.18)
        house_weights[house_number] = round(_clamp(score), 4)

    theme_records: list[dict[str, Any]] = []
    for item in natal_convergence.get("central_life_domains", []):
        label = str(item.get("label") or "").strip()
        if not label:
            continue
        theme_records.append(
            {
                "label": label,
                "score": float(item.get("normalized_relevance_score", 0.0) or 0.0),
                "houses": {int(value) for value in item.get("supporting_houses", []) if int(value or 0)},
                "planets": {normalize_forecast_target_name(value) for value in item.get("supporting_planets", []) if str(value or "").strip()},
            }
        )

    house_rulers = {
        int(house): normalize_forecast_target_name(record.get("traditional_ruler"))
        for house, record in rulership_network.get("house_rulers", {}).items()
        if int(house or 0)
    }

    central_house_rulers = {
        normalize_forecast_target_name(item.get("planet"))
        for item in rulership_network.get("central_routing_planets", [])
        if isinstance(item, dict)
    }

    return {
        "chart_ruler": chart_ruler_name,
        "target_weights": target_weights,
        "house_weights": house_weights,
        "house_rulers": house_rulers,
        "central_house_rulers": central_house_rulers,
        "prominence_map": prominence_map,
        "theme_records": theme_records,
        "focal_points": focal_points,
        "central_planets": central_planets,
    }


def _event_target_name(event: dict) -> str:
    return normalize_forecast_target_name(
        event.get("natal_target")
        or event.get("natal_contact")
        or ""
    )


def _event_house_number(event: dict) -> int:
    raw = event.get("natal_house")
    if not raw:
        raw = event.get("house_number") or event.get("whole_sign_house")
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _parse_period_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _covering_period(periods: list[dict], moment: Any) -> dict | None:
    if not isinstance(moment, datetime):
        return None
    for period in periods:
        start_at = _parse_period_datetime(period.get("start_at"))
        end_at = _parse_period_datetime(period.get("end_at"))
        if start_at is None or end_at is None:
            continue
        if start_at <= moment < end_at:
            return period
    return None


def _event_exactness(event: dict, event_type: str) -> float:
    if event_type == "transit":
        maximum_orb = float(event.get("maximum_orb", 0.0) or 0.0)
        peak_orb = abs(float(event.get("orb", event.get("peak_orb", 0.0)) or 0.0))
        if maximum_orb <= 0:
            return 0.0
        return _clamp(1.0 - (peak_orb / maximum_orb))
    if event_type == "station":
        distance = abs(float(event.get("distance_to_natal_target", 5.0) or 5.0))
        return _clamp(1.0 - min(distance, 5.0) / 5.0)
    if event_type == "eclipse":
        distance = abs(float(event.get("distance_to_natal_target", 3.0) or 3.0))
        return _clamp(1.0 - min(distance, 3.0) / 3.0)
    if event_type == "ingress":
        return 0.42
    return 0.0


def _event_duration_factor(event: dict) -> float:
    duration = max(0.0, float(event.get("duration_days", 0.0) or 0.0))
    if duration >= 90:
        return 1.0
    if duration >= 42:
        return 0.82
    if duration >= 14:
        return 0.55
    if duration > 0:
        return 0.24
    return 0.10


def _event_pass_sequence(event: dict) -> str:
    contact_count = int(event.get("contact_count", 0) or 0)
    if bool(event.get("near_active_transit_cycle")):
        return "station_linked"
    if contact_count >= 3:
        return "retrograde_three_pass"
    if contact_count == 2:
        return "multi_pass"
    if contact_count == 1:
        return "single_pass"
    return "standalone"


def _theme_matches(profile: dict[str, Any], target_name: str, house_number: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for theme in profile.get("theme_records", []):
        if house_number and house_number in theme["houses"]:
            matches.append(theme)
            continue
        if target_name and target_name in theme["planets"]:
            matches.append(theme)
    return matches


def _routing_state(event_type: str, activity_score: float, structural_importance: float, theme_convergence: float) -> str:
    if event_type in {"annual_profection", "zodiacal_releasing"}:
        return "long-term era evidence"
    if event_type in {"progression", "solar_arc"}:
        return "chapter backdrop"
    if event_type == "convergence_window":
        return "convergence evidence"
    if activity_score >= 0.82 and structural_importance >= 0.66:
        return "headline pattern"
    if event_type in {"station", "eclipse"} and activity_score >= 0.58:
        return "dated event card"
    if activity_score >= 0.58:
        return "monthly chapter input"
    if theme_convergence >= 0.52:
        return "convergence evidence"
    if structural_importance >= 0.56:
        return "annual-rhythm evidence"
    if activity_score >= 0.28:
        return "supporting event"
    return "technical reference"


def _reader_activity_score(
    event_type: str,
    concentration: float,
    exactness: float,
    natal_relevance: float,
    theme_convergence: float,
) -> float:
    if event_type == "transit":
        return _clamp(
            concentration * 0.70
            + exactness * 0.10
            + natal_relevance * 0.15
            + theme_convergence * 0.05
        )
    if event_type == "station":
        return _clamp(
            concentration * 0.42
            + exactness * 0.10
            + natal_relevance * 0.30
            + theme_convergence * 0.18
        )
    if event_type == "eclipse":
        return _clamp(
            concentration * 0.36
            + exactness * 0.08
            + natal_relevance * 0.34
            + theme_convergence * 0.22
        )
    if event_type == "ingress":
        return _clamp(
            concentration * 0.28
            + exactness * 0.10
            + natal_relevance * 0.36
            + theme_convergence * 0.26,
            high=0.62,
        )
    return _clamp(concentration)


def enrich_forecast_event(event: dict, profile: dict[str, Any]) -> dict[str, Any]:
    """
    Add natal-priority, timing, and routing metadata to one forecast event.
    """
    enriched = dict(event)
    event_type = str(enriched.get("event_type") or "").strip().lower()
    target_name = _event_target_name(enriched)
    house_number = _event_house_number(enriched)
    concentration = float(
        enriched.get("concentration_score", enriched.get("combined_intensity_score", enriched.get("raw_score", 0.0)))
        or 0.0
    )
    concentration = _clamp(concentration)

    target_weight = float(profile.get("target_weights", {}).get(target_name, 0.0) or 0.0)
    house_weight = float(profile.get("house_weights", {}).get(house_number, 0.0) or 0.0)
    house_ruler = normalize_forecast_target_name(profile.get("house_rulers", {}).get(house_number))
    house_ruler_weight = float(profile.get("target_weights", {}).get(house_ruler, 0.0) or 0.0)
    if house_ruler and house_ruler in profile.get("central_house_rulers", set()):
        house_ruler_weight = _clamp(house_ruler_weight + 0.08)

    theme_matches = _theme_matches(profile, target_name, house_number)
    matched_theme_labels = [theme["label"] for theme in theme_matches]
    theme_peak = max((theme["score"] for theme in theme_matches), default=0.0)
    theme_convergence = _clamp(min(1.0, theme_peak * 0.58 + len(matched_theme_labels) * 0.16))

    natal_relevance = _clamp(
        max(
            target_weight,
            house_weight * 0.94,
            house_ruler_weight * 0.82,
            theme_peak * 0.76,
        )
    )
    exactness = _event_exactness(enriched, event_type)
    duration_factor = _event_duration_factor(enriched)
    pass_sequence = _event_pass_sequence(enriched)
    pass_bonus = {
        "retrograde_three_pass": 0.14,
        "multi_pass": 0.08,
        "station_linked": 0.09,
        "single_pass": 0.03,
        "standalone": 0.0,
    }.get(pass_sequence, 0.0)

    baseline = EVENT_TYPE_BASELINES.get(event_type, 0.24)
    structural_importance = _clamp(
        max(
            float(enriched.get("structural_importance", 0.0) or 0.0),
            float(enriched.get("structural_score", 0.0) or 0.0),
            baseline
            + concentration * 0.18
            + natal_relevance * 0.24
            + theme_convergence * 0.16
            + duration_factor * 0.16
            + pass_bonus,
        )
    )

    activity_score = _reader_activity_score(
        event_type,
        concentration,
        exactness,
        natal_relevance,
        theme_convergence,
    )

    enriched["natal_relevance"] = round(natal_relevance, 4)
    enriched["theme_convergence"] = round(theme_convergence, 4)
    enriched["structural_importance"] = round(structural_importance, 4)
    enriched["structural_score"] = round(structural_importance, 4)
    enriched["reader_facing_activity_score"] = round(activity_score, 4)
    enriched["combined_intensity_score"] = round(activity_score, 4)
    enriched["score"] = round(activity_score, 4)
    enriched["exactness"] = round(exactness, 4)
    enriched["duration_factor"] = round(duration_factor, 4)
    enriched["pass_sequence"] = pass_sequence
    enriched["routing_state"] = _routing_state(
        event_type,
        activity_score,
        structural_importance,
        theme_convergence,
    )
    enriched["shared_life_domains"] = matched_theme_labels[:3]
    enriched["activated_house_ruler"] = house_ruler or ""
    enriched["activated_structures"] = [
        label
        for label, is_active in [
            ("target", bool(target_name)),
            ("house", bool(house_number)),
            ("house_ruler", bool(house_ruler)),
            ("theme", bool(matched_theme_labels)),
            ("chart_ruler", target_name == profile.get("chart_ruler") or house_ruler == profile.get("chart_ruler")),
        ]
        if is_active
    ]
    return enriched


def link_related_forecast_events(
    transit_events: list[dict],
    ingress_events: list[dict],
    station_events: list[dict],
    eclipse_events: list[dict],
    profile: dict[str, Any],
    lunation_events: list[dict] = None,
    progression_events: list[dict] = None,
    solar_arc_events: list[dict] = None,
    time_lord_periods: list[dict] = None,
) -> dict[str, list[dict]]:
    """
    Add cross-event context such as station-linked cycles and house-based clusters.
    """
    transits = [dict(event) for event in transit_events]
    ingresses = [dict(event) for event in ingress_events]
    stations = [dict(event) for event in station_events]
    eclipses = [dict(event) for event in eclipse_events]
    lunations = [dict(event) for event in (lunation_events or [])]
    progressions = [dict(event) for event in (progression_events or [])]
    solar_arcs = [dict(event) for event in (solar_arc_events or [])]
    time_lords = [dict(event) for event in (time_lord_periods or [])]

    for station in stations:
        peak_dt = station.get("peak_datetime")
        planet = str(station.get("transit_planet") or "").strip()
        related_cycles: list[str] = []
        if peak_dt is not None and planet:
            for transit in transits:
                if str(transit.get("transit_planet") or "").strip() != planet:
                    continue
                start_dt = transit.get("entry_datetime")
                end_dt = transit.get("leave_datetime") or transit.get("cycle_end_datetime")
                if start_dt is None:
                    continue
                if end_dt is None:
                    end_dt = peak_dt
                if start_dt <= peak_dt <= end_dt:
                    cycle_id = str(transit.get("cycle_id") or "").strip()
                    if cycle_id:
                        related_cycles.append(cycle_id)
        if related_cycles:
            station["related_cycle_ids"] = related_cycles
            station["near_active_transit_cycle"] = True
            station["_linked_station_softening"] = 0.08

    related_sources = transits + stations + eclipses + lunations
    for ingress in ingresses:
        peak_dt = ingress.get("peak_datetime")
        house_number = _event_house_number(ingress)
        support_ids: list[str] = []
        if peak_dt is not None and house_number:
            for related in related_sources:
                related_house = _event_house_number(related)
                related_peak = related.get("peak_datetime")
                if related_house != house_number or related_peak is None:
                    continue
                delta_days = abs((related_peak - peak_dt).days)
                if delta_days <= 30:
                    identity = str(related.get("cycle_id") or related.get("transit_planet") or related.get("event_type") or "").strip()
                    if identity:
                        support_ids.append(identity)
        if support_ids:
            ingress["supporting_event_ids"] = support_ids
            ingress["theme_convergence"] = round(
                _clamp(float(ingress.get("theme_convergence", 0.0) or 0.0) + min(0.20, len(support_ids) * 0.06)),
                4,
            )
            ingress["structural_importance"] = round(
                _clamp(float(ingress.get("structural_importance", 0.0) or 0.0) + min(0.12, len(support_ids) * 0.04)),
                4,
            )
            ingress["structural_score"] = ingress["structural_importance"]
            ingress["routing_state"] = "supporting event"

    for eclipse in eclipses:
        peak_dt = eclipse.get("peak_datetime")
        if peak_dt is None:
            continue
        target_name = _event_target_name(eclipse)
        house_number = _event_house_number(eclipse)
        related_hits = 0
        for related in transits + stations:
            related_peak = related.get("peak_datetime")
            if related_peak is None:
                continue
            if abs((related_peak - peak_dt).days) > 21:
                continue
            same_target = target_name and target_name == _event_target_name(related)
            same_house = house_number and house_number == _event_house_number(related)
            if same_target or same_house:
                related_hits += 1
        if related_hits:
            eclipse["theme_convergence"] = round(
                _clamp(float(eclipse.get("theme_convergence", 0.0) or 0.0) + min(0.22, related_hits * 0.07)),
                4,
            )
            eclipse["structural_importance"] = round(
                _clamp(float(eclipse.get("structural_importance", 0.0) or 0.0) + min(0.12, related_hits * 0.04)),
                4,
            )
            eclipse["structural_score"] = eclipse["structural_importance"]
            if str(eclipse.get("routing_state") or "").strip() == "technical reference":
                eclipse["routing_state"] = "supporting event"

    transits = [enrich_forecast_event(event, profile) for event in transits]
    ingresses = [enrich_forecast_event(event, profile) for event in ingresses]
    stations = [enrich_forecast_event(event, profile) for event in stations]
    eclipses = [enrich_forecast_event(event, profile) for event in eclipses]
    lunations = [enrich_forecast_event(event, profile) for event in lunations]
    progressions = [enrich_forecast_event(event, profile) for event in progressions]
    solar_arcs = [enrich_forecast_event(event, profile) for event in solar_arcs]
    
    # Do not force time_lord_periods into the point-event scoring shape.
    for tl in time_lords:
        tl["routing_state"] = _routing_state(str(tl.get("system") or ""), 0.0, 0.0, 0.0)

    # Annual Profections: weight modifier for transits active during a
    # profection year, per phase0/03_method_charters.md C4 §7 ("Annual
    # profection is a weight modifier for its year. It elevates signals
    # whose anchors involve the time lord, its ruled houses, or its natal
    # aspects."). Deterministic multiplicative adjustment using the period's
    # own declared weight_modifier -- not the quarantined statistical
    # convergence apparatus.
    annual_profections = [tl for tl in time_lords if str(tl.get("system") or "") == "annual_profection"]
    if annual_profections:
        for transit in transits:
            peak_dt = transit.get("peak_datetime")
            if peak_dt is None:
                continue
            active_period = _covering_period(annual_profections, peak_dt)
            if active_period is None:
                continue
            period_lord = str(active_period.get("period_lord") or "").strip()
            period_house = active_period.get("period_house")
            transit_planet = str(transit.get("transit_planet") or "").strip()
            target_name = _event_target_name(transit)
            house_number = _event_house_number(transit)
            is_time_lord_transit = bool(period_lord) and transit_planet == period_lord
            is_aspect_to_lord = bool(period_lord) and target_name == period_lord
            is_profected_house = bool(period_house) and house_number == period_house
            if not (is_time_lord_transit or is_aspect_to_lord or is_profected_house):
                continue
            weight_modifier = float(active_period.get("weight_modifier", 1.0) or 1.0)
            transit["structural_importance"] = round(
                _clamp(float(transit.get("structural_importance", 0.0) or 0.0) * weight_modifier), 4,
            )
            transit["structural_score"] = transit["structural_importance"]
            transit["theme_convergence"] = round(
                _clamp(float(transit.get("theme_convergence", 0.0) or 0.0) * weight_modifier), 4,
            )
            transit["annual_profection_linkage"] = [
                label
                for label, is_active in [
                    ("time_lord_transit", is_time_lord_transit),
                    ("aspect_to_time_lord", is_aspect_to_lord),
                    ("profected_house", is_profected_house),
                ]
                if is_active
            ]

    for station in stations:
        if not bool(station.get("near_active_transit_cycle")):
            continue
        softened = max(
            0.0,
            float(station.get("reader_facing_activity_score", station.get("combined_intensity_score", 0.0)) or 0.0)
            - float(station.get("_linked_station_softening", 0.0) or 0.0),
        )
        station["reader_facing_activity_score"] = round(softened, 4)
        station["combined_intensity_score"] = round(softened, 4)
        station["score"] = round(softened, 4)
        station["theme_convergence"] = round(
            _clamp(float(station.get("theme_convergence", 0.0) or 0.0) + 0.10),
            4,
        )
        station["structural_importance"] = round(
            _clamp(float(station.get("structural_importance", 0.0) or 0.0) + 0.05),
            4,
        )
        station["structural_score"] = station["structural_importance"]
        station["routing_state"] = "supporting event"
        station["pass_sequence"] = "station_linked"

    return {
        "transit_events": transits,
        "ingress_events": ingresses,
        "station_events": stations,
        "eclipse_events": eclipses,
        "lunation_events": lunations,
        "progression_events": progressions,
        "solar_arc_events": solar_arcs,
        "time_lord_periods": time_lords,
    }
