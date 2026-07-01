"""
Structured detection for named natal configurations.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from typing import Any

from formulas.standard.aspect_architecture import evaluate_aspect_architecture
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from selectors.utils import angular_distance
from selectors.utils import get_body_data

MethodRegistry.register(
    method_id="named_configurations",
    category="core_standard",
    lineage_tags=["traditional", "modern_pattern_detection"],
    requires_exact_time=False,
    required_data=["standard_planets", "houses", "aspects"],
)

PATTERN_BODIES = (
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
)


def _planet_connections(payload: dict) -> list[dict[str, Any]]:
    return [
        item
        for item in evaluate_aspect_architecture(payload)["connections"]
        if item.get("connection_type") == "planet_planet"
    ]


def _aspect_lookup(connections: list[dict[str, Any]]) -> dict[frozenset[str], dict[str, Any]]:
    return {frozenset((item["body_1"], item["body_2"])): item for item in connections}


def _is_connected(lookup: dict[frozenset[str], dict[str, Any]], body_a: str, body_b: str, aspect_types: set[str]) -> bool:
    aspect = lookup.get(frozenset((body_a, body_b)))
    return bool(aspect and aspect.get("aspect") in aspect_types)


def _is_quincunx(payload: dict, body_a: str, body_b: str, orb: float = 3.0) -> bool:
    data_a = get_body_data(payload, body_a)
    data_b = get_body_data(payload, body_b)
    if not data_a or not data_b:
        return False
    lon_a = data_a.get("longitude")
    lon_b = data_b.get("longitude")
    if not isinstance(lon_a, (int, float)) or not isinstance(lon_b, (int, float)):
        return False
    return abs(angular_distance(float(lon_a), float(lon_b)) - 150.0) <= orb


def evaluate_named_configurations(payload: dict) -> dict[str, Any]:
    methodology = get_active_methodology_metadata()
    connections = _planet_connections(payload)
    lookup = _aspect_lookup(connections)
    configurations: list[dict[str, Any]] = []

    sign_counter = Counter()
    house_counter = Counter()
    for body_name in PATTERN_BODIES:
        body_data = get_body_data(payload, body_name)
        if not body_data:
            continue
        sign_counter[body_data.get("sign", "")] += 1
        house_counter[body_data.get("house", 0)] += 1

    for sign, count in sign_counter.items():
        if sign and count >= 3:
            bodies = [
                body_name
                for body_name in PATTERN_BODIES
                if get_body_data(payload, body_name).get("sign") == sign
            ]
            configurations.append(
                {
                    "type": "stellium",
                    "subtype": "sign",
                    "anchor": sign,
                    "bodies": bodies,
                    "evidence": {"count": count},
                }
            )

    for house, count in house_counter.items():
        if house and count >= 3:
            bodies = [
                body_name
                for body_name in PATTERN_BODIES
                if get_body_data(payload, body_name).get("house") == house
            ]
            configurations.append(
                {
                    "type": "stellium",
                    "subtype": "house",
                    "anchor": house,
                    "bodies": bodies,
                    "evidence": {"count": count},
                }
            )

    for trio in combinations([body for body in PATTERN_BODIES if get_body_data(payload, body)], 3):
        if all(_is_connected(lookup, a, b, {"Trine"}) for a, b in combinations(trio, 2)):
            configurations.append(
                {
                    "type": "grand_trine",
                    "bodies": list(trio),
                    "focal_points": list(trio),
                    "evidence": {"edge_count": 3},
                }
            )

    for quad in combinations([body for body in PATTERN_BODIES if get_body_data(payload, body)], 4):
        oppositions = [
            pair for pair in combinations(quad, 2)
            if _is_connected(lookup, pair[0], pair[1], {"Opposition"})
        ]
        squares = [
            pair for pair in combinations(quad, 2)
            if _is_connected(lookup, pair[0], pair[1], {"Square"})
        ]
        if len(oppositions) >= 2 and len(squares) >= 4:
            configurations.append(
                {
                    "type": "grand_cross",
                    "bodies": list(quad),
                    "focal_points": list({body for pair in oppositions for body in pair}),
                    "evidence": {
                        "oppositions": [list(pair) for pair in oppositions],
                        "squares": [list(pair) for pair in squares],
                    },
                }
            )

    for trio in combinations([body for body in PATTERN_BODIES if get_body_data(payload, body)], 3):
        opposition_pairs = [
            pair for pair in combinations(trio, 2)
            if _is_connected(lookup, pair[0], pair[1], {"Opposition"})
        ]
        if not opposition_pairs:
            continue
        apex = next(body for body in trio if body not in opposition_pairs[0])
        if all(_is_connected(lookup, apex, other, {"Square"}) for other in opposition_pairs[0]):
            configurations.append(
                {
                    "type": "t_square",
                    "bodies": list(trio),
                    "focal_points": [apex],
                    "evidence": {"opposition": list(opposition_pairs[0])},
                }
            )

    for trio in combinations([body for body in PATTERN_BODIES if get_body_data(payload, body)], 3):
        sextile_pairs = [
            pair for pair in combinations(trio, 2)
            if _is_connected(lookup, pair[0], pair[1], {"Sextile"})
        ]
        if not sextile_pairs:
            continue
        apex = next(body for body in trio if body not in sextile_pairs[0])
        if all(_is_quincunx(payload, apex, other) for other in sextile_pairs[0]):
            configurations.append(
                {
                    "type": "yod",
                    "bodies": list(trio),
                    "focal_points": [apex],
                    "evidence": {"sextile": list(sextile_pairs[0])},
                }
            )

    grand_trines = [item for item in configurations if item["type"] == "grand_trine"]
    for grand_trine in grand_trines:
        for body_name in [body for body in PATTERN_BODIES if get_body_data(payload, body)]:
            if body_name in grand_trine["bodies"]:
                continue
            trine_bodies = [
                other for other in grand_trine["bodies"]
                if _is_connected(lookup, body_name, other, {"Opposition"})
            ]
            sextile_bodies = [
                other for other in grand_trine["bodies"]
                if _is_connected(lookup, body_name, other, {"Sextile"})
            ]
            if len(trine_bodies) == 1 and len(sextile_bodies) == 2:
                configurations.append(
                    {
                        "type": "kite",
                        "bodies": list(grand_trine["bodies"]) + [body_name],
                        "focal_points": [body_name],
                        "evidence": {"grand_trine": list(grand_trine["bodies"])},
                    }
                )

    rectangles_seen: set[tuple[str, ...]] = set()
    for quad in combinations([body for body in PATTERN_BODIES if get_body_data(payload, body)], 4):
        sextiles = [
            pair for pair in combinations(quad, 2)
            if _is_connected(lookup, pair[0], pair[1], {"Sextile"})
        ]
        trines = [
            pair for pair in combinations(quad, 2)
            if _is_connected(lookup, pair[0], pair[1], {"Trine"})
        ]
        oppositions = [
            pair for pair in combinations(quad, 2)
            if _is_connected(lookup, pair[0], pair[1], {"Opposition"})
        ]
        if len(sextiles) >= 2 and len(trines) >= 2 and len(oppositions) >= 2:
            key = tuple(sorted(quad))
            if key in rectangles_seen:
                continue
            rectangles_seen.add(key)
            configurations.append(
                {
                    "type": "mystic_rectangle",
                    "bodies": list(quad),
                    "focal_points": list({body for pair in oppositions for body in pair}),
                    "evidence": {
                        "sextiles": [list(pair) for pair in sextiles],
                        "trines": [list(pair) for pair in trines],
                        "oppositions": [list(pair) for pair in oppositions],
                    },
                }
            )

    return {
        "methodology": methodology,
        "formula_version": "2.0.0",
        "configurations": configurations,
    }
