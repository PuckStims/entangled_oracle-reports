"""
Rulership, dispositorship, and reception architecture for the standard natal layer.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.dignity import MODERN_DOMICILE, TRADITIONAL_DOMICILE
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from selectors.utils import get_body_data

MethodRegistry.register(
    method_id="rulership_network",
    category="core_standard",
    lineage_tags=["hellenistic", "traditional", "modern_secondary_modifier"],
    requires_exact_time=False,
    required_data=["standard_planets", "houses"],
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

HOUSE_LABELS = {
    1: "identity / personal growth",
    2: "resource / material",
    3: "learning / communication",
    4: "inner-life / home / roots",
    5: "creative / pleasure",
    6: "work / health / routine",
    7: "relational / partnership",
    8: "shared resources / transformation",
    9: "learning / meaning / worldview",
    10: "vocational / public structure",
    11: "community / goals",
    12: "inner-life / restoration",
}


def _traditional_ruler_for_sign(sign: str) -> str | None:
    return TRADITIONAL_DOMICILE.get(sign)


def _modern_ruler_for_sign(sign: str) -> str | None:
    return MODERN_DOMICILE.get(sign)


def _house_sign_map(payload: dict) -> dict[int, str]:
    houses = payload.get("houses", {})
    return {
        house_number: houses.get(f"House_{house_number}", {}).get("sign", "")
        for house_number in range(1, 13)
    }


def _build_house_rulers(payload: dict) -> dict[int, dict[str, Any]]:
    house_signs = _house_sign_map(payload)
    house_rulers: dict[int, dict[str, Any]] = {}
    for house_number, sign in house_signs.items():
        house_rulers[house_number] = {
            "house": house_number,
            "house_label": HOUSE_LABELS.get(house_number, ""),
            "sign": sign,
            "traditional_ruler": _traditional_ruler_for_sign(sign),
            "modern_secondary_ruler": _modern_ruler_for_sign(sign),
        }
    return house_rulers


def _trace_dispositor_chain(payload: dict, body_name: str) -> dict[str, Any]:
    visited_order: list[str] = []
    visited_positions: dict[str, int] = {}
    current = body_name

    while current:
        if current in visited_positions:
            loop_start = visited_positions[current]
            return {
                "body": body_name,
                "chain": visited_order,
                "terminates": False,
                "final_dispositor": None,
                "loop": visited_order[loop_start:],
                "loop_entry": current,
            }

        visited_positions[current] = len(visited_order)
        visited_order.append(current)

        current_data = get_body_data(payload, current)
        if not current_data:
            return {
                "body": body_name,
                "chain": visited_order,
                "terminates": False,
                "final_dispositor": None,
                "loop": [],
                "missing_inputs": [current],
            }

        sign = current_data.get("sign", "")
        next_body = _traditional_ruler_for_sign(sign)
        if not next_body:
            return {
                "body": body_name,
                "chain": visited_order,
                "terminates": False,
                "final_dispositor": None,
                "loop": [],
                "missing_inputs": [f"Traditional ruler for {sign}"],
            }

        if next_body == current:
            return {
                "body": body_name,
                "chain": visited_order,
                "terminates": True,
                "final_dispositor": current,
                "loop": [],
            }

        current = next_body

    return {
        "body": body_name,
        "chain": visited_order,
        "terminates": False,
        "final_dispositor": None,
        "loop": [],
    }


def _mutual_receptions(payload: dict) -> list[dict[str, Any]]:
    receptions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for body_name in STANDARD_BODIES:
        body_data = get_body_data(payload, body_name)
        if not body_data:
            continue
        other = _traditional_ruler_for_sign(body_data.get("sign", ""))
        if not other or other == body_name:
            continue
        other_data = get_body_data(payload, other)
        if not other_data:
            continue
        if _traditional_ruler_for_sign(other_data.get("sign", "")) != body_name:
            continue
        key = tuple(sorted((body_name, other)))
        if key in seen:
            continue
        seen.add(key)
        receptions.append(
            {
                "bodies": list(key),
                "rule": "mutual_reception_by_domicile",
                "signs": {
                    body_name: body_data.get("sign", ""),
                    other: other_data.get("sign", ""),
                },
            }
        )
    return receptions


def evaluate_rulership_network(payload: dict) -> dict[str, Any]:
    methodology = get_active_methodology_metadata()
    house_rulers = _build_house_rulers(payload)
    chains = {
        body_name: _trace_dispositor_chain(payload, body_name)
        for body_name in STANDARD_BODIES
        if get_body_data(payload, body_name)
    }

    final_dispositors = sorted(
        {
            chain["final_dispositor"]
            for chain in chains.values()
            if chain.get("terminates") and chain.get("final_dispositor")
        }
    )

    loop_records: list[dict[str, Any]] = []
    seen_loops: set[tuple[str, ...]] = set()
    for chain in chains.values():
        loop = tuple(chain.get("loop", []))
        if not loop:
            continue
        canonical_loop = tuple(sorted(loop))
        if canonical_loop in seen_loops:
            continue
        seen_loops.add(canonical_loop)
        loop_records.append(
            {
                "members": list(loop),
                "type": "closed_dispositor_loop",
                "entry_points": sorted(
                    body
                    for body, record in chains.items()
                    if tuple(record.get("loop", [])) == loop
                ),
            }
        )

    houses_by_ruler: dict[str, list[int]] = defaultdict(list)
    for house_number, record in house_rulers.items():
        ruler = record.get("traditional_ruler")
        if ruler:
            houses_by_ruler[ruler].append(house_number)

    chart_ruler = evaluate_chart_ruler(payload)
    central_routing = []
    for ruler, houses in houses_by_ruler.items():
        if len(houses) < 2:
            continue
        central_routing.append(
            {
                "planet": ruler,
                "houses": sorted(houses),
                "house_labels": [HOUSE_LABELS.get(house, "") for house in sorted(houses)],
                "is_chart_ruler": chart_ruler.get("primary_ruler") == ruler,
            }
        )
    central_routing.sort(key=lambda item: (-len(item["houses"]), item["planet"]))

    return {
        "methodology": methodology,
        "modern_rulership_policy": {
            "traditional_rulers_primary": True,
            "modern_rulers_secondary_only": True,
            "modern_rulers_replace_traditional": False,
        },
        "house_rulers": house_rulers,
        "houses_by_traditional_ruler": {key: value for key, value in houses_by_ruler.items()},
        "dispositor_chains": chains,
        "final_dispositors": final_dispositors,
        "closed_loops": loop_records,
        "mutual_receptions": _mutual_receptions(payload),
        "central_routing_planets": central_routing,
        "formula_version": "2.0.0",
    }
