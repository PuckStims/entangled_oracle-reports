"""
Standard natal convergence layer, separate from EO proprietary indexes.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from formulas.standard.aspect_architecture import evaluate_aspect_architecture
from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.chart_structure import evaluate_chart_structure
from formulas.standard.house_emphasis import evaluate_house_emphasis
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.named_configurations import evaluate_named_configurations
from formulas.standard.planetary_condition import evaluate_all_planetary_conditions
from formulas.standard.planetary_prominence import evaluate_prominence
from formulas.standard.rulership_network import evaluate_rulership_network

MethodRegistry.register(
    method_id="standard_natal_convergence",
    category="core_standard",
    lineage_tags=["standard_synthesis", "non_proprietary"],
    requires_exact_time=False,
    required_data=["standard_planets", "angles", "houses", "aspects"],
)

DOMAIN_MAP = {
    "vocational / public structure": {10, 6, 11},
    "relational structure": {7, 5, 8},
    "inner-life / restoration structure": {4, 12},
    "resource / material structure": {2, 8},
    "learning / meaning structure": {3, 9},
    "creative / pleasure structure": {5, 11},
}


def _collect_central_planets(prominence: dict, aspect_architecture: dict, conditions: dict, rulership_network: dict) -> list[dict[str, Any]]:
    house_counts = {
        key: len(value)
        for key, value in rulership_network.get("houses_by_traditional_ruler", {}).items()
    }
    result = []
    for item in prominence.get("rankings", []):
        body = item["body"]
        connectivity = aspect_architecture.get("connectivity", {}).get(body, {})
        condition = conditions.get(body)
        evidence = []
        if item.get("normalized_score", 0.0) >= 0.45:
            evidence.append("prominence")
        if connectivity.get("state") in {"hub", "high_connectivity"}:
            evidence.append("aspect_connectivity")
        if house_counts.get(body, 0) >= 2:
            evidence.append("rulership_load")
        if condition and condition.condition_classification in {"excellent", "strong"}:
            evidence.append("condition_support")
        score = round(
            min(
                1.0,
                item.get("normalized_score", 0.0) * 0.45
                + min(connectivity.get("structural_importance_total", 0.0), 3.0) * 0.15
                + min(house_counts.get(body, 0), 4) * 0.1
                + (0.15 if condition and condition.condition_classification in {"excellent", "strong"} else 0.0)
                + (0.05 if body in rulership_network.get("final_dispositors", []) else 0.0),
            ),
            4,
        )
        if len(evidence) >= 2:
            result.append(
                {
                    "label": body,
                    "normalized_relevance_score": score,
                    "confidence_state": condition.confidence if condition else "exact_birth_time",
                    "independent_supporting_factors": evidence,
                    "supporting_planets": [body],
                    "supporting_houses": rulership_network.get("houses_by_traditional_ruler", {}).get(body, []),
                    "supporting_aspects": [
                        connection for connection in aspect_architecture.get("per_planet_network", {}).get(body, [])
                        if connection.get("structural_importance", 0.0) >= 0.45
                    ],
                    "rulership_or_dispositorship_evidence": {
                        "houses_ruled": rulership_network.get("houses_by_traditional_ruler", {}).get(body, []),
                        "final_dispositor": body in rulership_network.get("final_dispositors", []),
                    },
                    "condition_and_prominence_context": {
                        "prominence": item,
                        "condition": condition.to_dict() if condition else {},
                    },
                    "excluded_or_suppressed_evidence": [],
                    "methodology": get_active_methodology_metadata(),
                    "formula_version": "2.0.0",
                }
            )
    return result


def _build_domain_theme(
    label: str,
    houses: set[int],
    house_emphasis: dict,
    rulership_network: dict,
    prominence: dict,
    conditions: dict,
    aspect_architecture: dict,
) -> dict[str, Any]:
    prominence_map = {item["body"]: item for item in prominence.get("rankings", [])}
    house_records = {
        item["house"]: item for item in house_emphasis.get("rankings", [])
        if item["house"] in houses
    }
    supporting_houses = sorted(house_records)
    supporting_planets = set()
    evidence = []
    score = 0.0
    if supporting_houses:
        avg_house = sum(record["house_emphasis_normalized"] for record in house_records.values()) / len(house_records)
        score += avg_house * 0.35
        if avg_house >= 0.3:
            evidence.append("house_emphasis")
        for record in house_records.values():
            ruler = record.get("ruler")
            if ruler:
                supporting_planets.add(ruler)
                if prominence_map.get(ruler, {}).get("normalized_score", 0.0) >= 0.35:
                    evidence.append("ruler_prominence")
                    score += 0.15
                condition = conditions.get(ruler)
                if condition and condition.condition_classification in {"excellent", "strong"}:
                    evidence.append("ruler_condition")
                    score += 0.1
            for occupant in record.get("occupants", []):
                supporting_planets.add(occupant)
    aspect_support = []
    for connection in aspect_architecture.get("connections", []):
        if connection.get("structural_importance", 0.0) < 0.45:
            continue
        body_a = connection.get("body_1")
        body_b = connection.get("body_2")
        if body_a in supporting_planets or body_b in supporting_planets:
            aspect_support.append(connection)
    if aspect_support:
        evidence.append("aspect_support")
        score += min(0.2, len(aspect_support) * 0.04)

    supporting_planets = sorted(supporting_planets)
    evidence = sorted(set(evidence))
    if len(evidence) < 2:
        suppressed = ["insufficient_independent_support"]
        normalized = round(min(score, 1.0), 4)
    else:
        suppressed = []
        normalized = round(min(score, 1.0), 4)

    return {
        "label": label,
        "normalized_relevance_score": normalized,
        "confidence_state": "exact_birth_time",
        "independent_supporting_factors": evidence,
        "supporting_planets": supporting_planets,
        "supporting_houses": supporting_houses,
        "supporting_aspects": aspect_support,
        "rulership_or_dispositorship_evidence": {
            "shared_rulers": {
                ruler: ruled_houses
                for ruler, ruled_houses in rulership_network.get("houses_by_traditional_ruler", {}).items()
                if houses.intersection(ruled_houses)
            }
        },
        "condition_and_prominence_context": {
            body: {
                "prominence": prominence_map.get(body, {}),
                "condition": conditions.get(body).to_dict() if body in conditions else {},
            }
            for body in supporting_planets
        },
        "excluded_or_suppressed_evidence": suppressed,
        "methodology": get_active_methodology_metadata(),
        "formula_version": "2.0.0",
    }


def evaluate_standard_natal_convergence(payload: dict) -> dict[str, Any]:
    methodology = get_active_methodology_metadata()
    prominence = evaluate_prominence(payload)
    conditions = evaluate_all_planetary_conditions(payload)
    house_emphasis = evaluate_house_emphasis(payload)
    aspect_architecture = evaluate_aspect_architecture(payload)
    rulership_network = evaluate_rulership_network(payload)
    chart_structure = evaluate_chart_structure(payload)
    configurations = evaluate_named_configurations(payload)
    chart_ruler = evaluate_chart_ruler(payload).get("primary_ruler")

    central_planets = _collect_central_planets(
        prominence,
        aspect_architecture,
        conditions,
        rulership_network,
    )

    central_life_domains = []
    for label, houses in DOMAIN_MAP.items():
        theme = _build_domain_theme(
            label,
            houses,
            house_emphasis,
            rulership_network,
            prominence,
            conditions,
            aspect_architecture,
        )
        central_life_domains.append(theme)

    tensions = [
        item for item in aspect_architecture.get("tensional_connections", [])
        if item.get("structural_importance", 0.0) >= 0.45
    ]
    supports = [
        item for item in aspect_architecture.get("supportive_connections", [])
        if item.get("structural_importance", 0.0) >= 0.45
    ]

    central_life_domains.sort(key=lambda item: item["normalized_relevance_score"], reverse=True)

    return {
        "methodology": methodology,
        "formula_version": "2.0.0",
        "central_planets": central_planets,
        "central_life_domains": central_life_domains,
        "core_tension_axis": {
            "label": "core tension axis",
            "normalized_relevance_score": round(
                min(1.0, sum(item.get("structural_importance", 0.0) for item in tensions[:3]) / 2.0),
                4,
            ),
            "confidence_state": "exact_birth_time",
            "independent_supporting_factors": ["tensional_aspects"] if tensions else [],
            "supporting_planets": sorted({body for item in tensions[:3] for body in (item["body_1"], item["body_2"])}),
            "supporting_houses": [],
            "supporting_aspects": tensions[:3],
            "rulership_or_dispositorship_evidence": {},
            "condition_and_prominence_context": {},
            "excluded_or_suppressed_evidence": [] if tensions else ["no_high_weight_tensional_axis"],
            "methodology": methodology,
            "formula_version": "2.0.0",
        },
        "core_support_axis": {
            "label": "core support axis",
            "normalized_relevance_score": round(
                min(1.0, sum(item.get("structural_importance", 0.0) for item in supports[:3]) / 2.0),
                4,
            ),
            "confidence_state": "exact_birth_time",
            "independent_supporting_factors": ["supportive_aspects"] if supports else [],
            "supporting_planets": sorted({body for item in supports[:3] for body in (item["body_1"], item["body_2"])}),
            "supporting_houses": [],
            "supporting_aspects": supports[:3],
            "rulership_or_dispositorship_evidence": {},
            "condition_and_prominence_context": {},
            "excluded_or_suppressed_evidence": [] if supports else ["no_high_weight_support_axis"],
            "methodology": methodology,
            "formula_version": "2.0.0",
        },
        "vocational / public structure": next((item for item in central_life_domains if item["label"] == "vocational / public structure"), {}),
        "relational structure": next((item for item in central_life_domains if item["label"] == "relational structure"), {}),
        "inner-life / restoration structure": next((item for item in central_life_domains if item["label"] == "inner-life / restoration structure"), {}),
        "resource / material structure": next((item for item in central_life_domains if item["label"] == "resource / material structure"), {}),
        "learning / meaning structure": next((item for item in central_life_domains if item["label"] == "learning / meaning structure"), {}),
        "creative / pleasure structure": next((item for item in central_life_domains if item["label"] == "creative / pleasure structure"), {}),
        "trace": {
            "chart_ruler": chart_ruler,
            "rulership_network": rulership_network,
            "aspect_architecture": aspect_architecture,
            "house_emphasis": house_emphasis,
            "chart_structure": chart_structure,
            "named_configurations": configurations,
        },
    }
