"""
Auditable natal aspect network layer for Tropical + Whole Sign charts.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from config import ASPECT_CHARACTERS, MAJOR_ASPECTS
from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.planetary_prominence import evaluate_prominence
from selectors.utils import (
    angle_exists,
    angular_distance,
    body_exists,
    get_angle_longitude,
    get_aspect_from_payload,
    get_body_data,
    get_body_longitude,
    get_max_orb,
)

MethodRegistry.register(
    method_id="aspect_architecture",
    category="core_standard",
    lineage_tags=["traditional", "modern_structural"],
    requires_exact_time=False,
    required_data=["standard_planets", "angles", "aspects"],
)

STANDARD_BODIES = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Chiron",
)
# Descendant and Imum_Coeli are derived from the Asc/MC axes, so treating them
# as independent angle targets would double every axis contact here.
ANGLE_NAMES = ("Ascendant", "Midheaven", "Vertex")
NEUTRAL_ASPECTS = {"Conjunction"}


def _aspect_angle(aspect_name: str) -> float:
    for name, angle in MAJOR_ASPECTS:
        if name == aspect_name:
            return float(angle)
    return 0.0


def _normalized_orb_strength(body_a: str, body_b: str, aspect_name: str, orb: float) -> float:
    max_orb = get_max_orb(body_a, body_b, aspect_name)
    if max_orb <= 0:
        return 0.0
    return round(max(0.0, (max_orb - orb) / max_orb), 4)


def _connection_classification(aspect_name: str) -> str:
    if aspect_name in NEUTRAL_ASPECTS:
        return "neutral"
    return "supportive" if ASPECT_CHARACTERS.get(aspect_name) == "flowing" else "tensional"


def _applying_state_body_to_body(body_a: str, body_b: str, aspect_name: str, payload: dict) -> str | None:
    data_a = get_body_data(payload, body_a)
    data_b = get_body_data(payload, body_b)
    if not data_a or not data_b:
        return None

    lon_a = data_a.get("longitude")
    lon_b = data_b.get("longitude")
    speed_a = data_a.get("speed")
    speed_b = data_b.get("speed")
    if not all(isinstance(value, (int, float)) for value in (lon_a, lon_b, speed_a, speed_b)):
        return None

    target = _aspect_angle(aspect_name)
    current_gap = angular_distance(float(lon_a), float(lon_b))
    future_gap = angular_distance(float(lon_a) + float(speed_a), float(lon_b) + float(speed_b))
    current_delta = abs(current_gap - target)
    future_delta = abs(future_gap - target)
    if abs(future_delta - current_delta) < 1e-6:
        return None
    return "applying" if future_delta < current_delta else "separating"


def _applying_state_body_to_angle(body_name: str, angle_name: str, aspect_name: str, payload: dict) -> str | None:
    body_data = get_body_data(payload, body_name)
    angle_lon = get_angle_longitude(payload, angle_name)
    if not body_data or not isinstance(angle_lon, (int, float)):
        return None
    body_lon = body_data.get("longitude")
    body_speed = body_data.get("speed")
    if not isinstance(body_lon, (int, float)) or not isinstance(body_speed, (int, float)):
        return None
    target = _aspect_angle(aspect_name)
    current_gap = angular_distance(float(body_lon), float(angle_lon))
    future_gap = angular_distance(float(body_lon) + float(body_speed), float(angle_lon))
    current_delta = abs(current_gap - target)
    future_delta = abs(future_gap - target)
    if abs(future_delta - current_delta) < 1e-6:
        return None
    return "applying" if future_delta < current_delta else "separating"


def _direct_angle_aspects(payload: dict) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for body_name in STANDARD_BODIES:
        if not body_exists(payload, body_name):
            continue
        body_lon = get_body_longitude(payload, body_name)
        if body_lon is None:
            continue
        for angle_name in ANGLE_NAMES:
            if not angle_exists(payload, angle_name):
                continue
            angle_lon = get_angle_longitude(payload, angle_name)
            if angle_lon is None:
                continue
            distance = angular_distance(body_lon, angle_lon)
            best_match: dict[str, Any] | None = None
            for aspect_name, exact_angle in MAJOR_ASPECTS:
                max_orb = 3.0
                orb = abs(distance - exact_angle)
                if orb > max_orb:
                    continue
                strength = round(max(0.0, (max_orb - orb) / max_orb), 4)
                candidate = {
                    "body_1": body_name,
                    "body_2": angle_name,
                    "aspect": aspect_name,
                    "orb": round(orb, 4),
                    "angle": round(distance, 4),
                    "normalized_strength": strength,
                    "classification": _connection_classification(aspect_name),
                    "connection_type": "planet_angle",
                    "applying_state": _applying_state_body_to_angle(body_name, angle_name, aspect_name, payload),
                }
                if best_match is None or candidate["normalized_strength"] > best_match["normalized_strength"]:
                    best_match = candidate
            if best_match:
                results.append(best_match)
    return results


def evaluate_aspect_architecture(payload: dict) -> dict[str, Any]:
    methodology = get_active_methodology_metadata()
    prominence = evaluate_prominence(payload)
    chart_ruler = evaluate_chart_ruler(payload).get("primary_ruler")
    prominence_scores = {
        record["body"]: record.get("normalized_score", 0.0)
        for record in prominence.get("rankings", [])
    }

    all_connections: list[dict[str, Any]] = []
    per_planet_network: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for aspect in payload.get("aspects", []):
        body_a = aspect.get("body_1")
        body_b = aspect.get("body_2")
        aspect_name = aspect.get("aspect")
        orb = aspect.get("orb")
        if not isinstance(body_a, str) or not isinstance(body_b, str):
            continue
        if not isinstance(orb, (int, float)) or not isinstance(aspect_name, str):
            continue
        if body_a not in STANDARD_BODIES or body_b not in STANDARD_BODIES:
            continue

        connection = {
            "body_1": body_a,
            "body_2": body_b,
            "aspect": aspect_name,
            "orb": round(float(orb), 4),
            "normalized_strength": _normalized_orb_strength(body_a, body_b, aspect_name, float(orb)),
            "classification": _connection_classification(aspect_name),
            "connection_type": "planet_planet",
            "luminary_involved": body_a in {"Sun", "Moon"} or body_b in {"Sun", "Moon"},
            "chart_ruler_involved": chart_ruler in {body_a, body_b},
            "applying_state": _applying_state_body_to_body(body_a, body_b, aspect_name, payload),
        }
        connection["structural_importance"] = round(
            min(
                1.0,
                connection["normalized_strength"] * 0.5
                + max(prominence_scores.get(body_a, 0.0), prominence_scores.get(body_b, 0.0)) * 0.3
                + (0.1 if connection["luminary_involved"] else 0.0)
                + (0.1 if connection["chart_ruler_involved"] else 0.0),
            ),
            4,
        )
        all_connections.append(connection)
        per_planet_network[body_a].append(connection)
        per_planet_network[body_b].append(connection)

    for connection in _direct_angle_aspects(payload):
        body_name = connection["body_1"]
        connection["luminary_involved"] = body_name in {"Sun", "Moon"}
        connection["chart_ruler_involved"] = body_name == chart_ruler
        connection["angle_involved"] = True
        connection["structural_importance"] = round(
            min(
                1.0,
                connection["normalized_strength"] * 0.55
                + prominence_scores.get(body_name, 0.0) * 0.25
                + 0.1
                + (0.05 if connection["luminary_involved"] else 0.0)
                + (0.05 if connection["chart_ruler_involved"] else 0.0),
            ),
            4,
        )
        all_connections.append(connection)
        per_planet_network[body_name].append(connection)

    hub_records = []
    connectivity_map = {}
    for body_name in STANDARD_BODIES:
        network = per_planet_network.get(body_name, [])
        structural_total = round(sum(item.get("structural_importance", 0.0) for item in network), 4)
        strong_links = sum(1 for item in network if item.get("structural_importance", 0.0) >= 0.45)
        if structural_total >= 2.25 or strong_links >= 4:
            connectivity_state = "hub"
        elif len(network) <= 1:
            connectivity_state = "isolated"
        elif len(network) >= 4:
            connectivity_state = "high_connectivity"
        else:
            connectivity_state = "low_connectivity"
        connectivity_map[body_name] = {
            "connection_count": len(network),
            "strong_connection_count": strong_links,
            "structural_importance_total": structural_total,
            "state": connectivity_state,
        }
        if connectivity_state in {"hub", "high_connectivity"}:
            hub_records.append(
                {
                    "body": body_name,
                    "connection_count": len(network),
                    "strong_connection_count": strong_links,
                    "structural_importance_total": structural_total,
                }
            )

    hub_records.sort(
        key=lambda item: (
            -item["structural_importance_total"],
            -item["strong_connection_count"],
            item["body"],
        )
    )

    luminary_links = [
        connection
        for connection in all_connections
        if connection.get("luminary_involved")
    ]
    supportive = [item for item in all_connections if item["classification"] == "supportive"]
    tensional = [item for item in all_connections if item["classification"] == "tensional"]
    neutral = [item for item in all_connections if item["classification"] == "neutral"]

    return {
        "methodology": methodology,
        "formula_version": "2.0.0",
        "connections": sorted(
            all_connections,
            key=lambda item: (-item["structural_importance"], item["orb"], item["body_1"], item["body_2"]),
        ),
        "per_planet_network": {key: value for key, value in per_planet_network.items()},
        "luminary_links": luminary_links,
        "supportive_connections": supportive,
        "tensional_connections": tensional,
        "neutral_connections": neutral,
        "connectivity": connectivity_map,
        "planetary_hubs": hub_records,
    }
