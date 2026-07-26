"""
Between Places comparison engine.

This module implements the core comparison logic for two destinations,
identifying shared themes, divergent themes, strongest differences, and
goal-level tradeoffs without collapsing the comparison into a universal rank.
"""
from __future__ import annotations

from typing import Any

COMPARISON_VERSION = "between_places_comparison_v0.2.0"
MAX_STRONGEST_DIFFERENCES = 8
MAX_TRADEOFFS = 8


def _extract_themes(clusters: list[dict]) -> set[str]:
    themes = set()
    for cluster in clusters:
        if not cluster.get("omit_from_primary_report"):
            themes.update(cluster.get("theme_keys", []))
    return themes


def _extract_angles(record: dict) -> set[str]:
    angles = set()
    for contact in record.get("evidence_record", {}).get("relocated_angle_contacts", []):
        if contact.get("contact_strength") in ("defining", "tight", "moderate"):
            body = _format_label(contact.get("body"))
            angle = _format_label(contact.get("angle"))
            angles.add(f"{body} on {angle}")
    return angles


def _extract_house_changes(record: dict) -> set[str]:
    changes = set()
    for change in record.get("evidence_record", {}).get("planet_house_changes", []):
        movement_type = change.get("movement_type")
        if movement_type in ("newly_angular", "leaves_angular"):
            body = _format_label(change.get("body"))
            movement = _format_label(movement_type).lower()
            changes.add(f"{body} {movement}")
    return changes


def _format_label(value: Any) -> str:
    return str(value or "").replace("_", " ").strip()


def _location_name(location_id: str | None, dest_a: dict, dest_b: dict, name_a: str, name_b: str) -> str:
    if location_id and location_id == dest_a.get("location_id"):
        return name_a
    if location_id and location_id == dest_b.get("location_id"):
        return name_b
    return name_a


def _build_comparison_summary(
    *,
    name_a: str,
    name_b: str,
    dest_a: dict,
    dest_b: dict,
    shared_theme_keys: list[str],
    strongest_differences: list[dict[str, Any]],
    tradeoffs: list[dict[str, Any]],
) -> str:
    shared_preview = ", ".join(_format_label(theme) for theme in shared_theme_keys[:3])
    top_difference = strongest_differences[0] if strongest_differences else None
    top_tradeoff = tradeoffs[0] if tradeoffs else None

    if top_difference and top_tradeoff:
        difference_place = _location_name(top_difference.get("location_id"), dest_a, dest_b, name_a, name_b)
        tradeoff_place = _location_name(top_tradeoff.get("stronger_location_id"), dest_a, dest_b, name_a, name_b)
        return (
            f"Both places activate overlapping chart material"
            f"{f' such as {shared_preview}' if shared_preview else ''}, "
            f"but the comparison is not evenly weighted. {difference_place} separates itself through "
            f"{top_difference['description'].rstrip('.')}, while the clearest goal-level edge currently runs through "
            f"{_format_label(top_tradeoff['goal_key'])} in {tradeoff_place}."
        )
    if top_difference:
        difference_place = _location_name(top_difference.get("location_id"), dest_a, dest_b, name_a, name_b)
        return (
            f"The core contrast is structural rather than general-purpose: {difference_place} stands apart because "
            f"{top_difference['description'].rstrip('.').lower()}."
        )
    if top_tradeoff:
        tradeoff_place = _location_name(top_tradeoff.get("stronger_location_id"), dest_a, dest_b, name_a, name_b)
        return (
            f"The chart reads these places as closer than a simple ranking would suggest, so the most useful distinction is goal-specific: "
            f"{tradeoff_place} currently shows the clearer edge for {_format_label(top_tradeoff['goal_key'])}."
        )
    if shared_preview:
        return (
            f"The strongest message is overlap rather than separation: both places keep returning to chart material such as {shared_preview}."
        )
    return (
        "Neither place dominates this comparison on current evidence, so lived testing and practical constraints may matter more than symbolic separation alone."
    )


def build_comparison_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compare exactly two destination records built from the shared locational grammar.
    """
    if len(records) != 2:
        raise ValueError("Between Places currently requires exactly two destinations for comparison.")

    record_a, record_b = records

    dest_a = record_a.get("destination_context", {})
    dest_b = record_b.get("destination_context", {})
    name_a = dest_a.get("display_name", "Location A")
    name_b = dest_b.get("display_name", "Location B")

    clusters_a = record_a.get("theme_clusters", {}).get("clusters", [])
    clusters_b = record_b.get("theme_clusters", {}).get("clusters", [])

    themes_a = _extract_themes(clusters_a)
    themes_b = _extract_themes(clusters_b)

    shared_theme_keys = sorted(themes_a & themes_b)
    divergent_theme_keys = sorted(themes_a ^ themes_b)

    angles_a = _extract_angles(record_a)
    angles_b = _extract_angles(record_b)

    houses_a = _extract_house_changes(record_a)
    houses_b = _extract_house_changes(record_b)

    strongest_differences: list[dict[str, Any]] = []

    for angle in sorted(angles_a - angles_b):
        strongest_differences.append(
            {
                "type": "angular_difference",
                "location_id": dest_a.get("location_id"),
                "description": f"{angle} is uniquely emphasized here.",
            }
        )
    for angle in sorted(angles_b - angles_a):
        strongest_differences.append(
            {
                "type": "angular_difference",
                "location_id": dest_b.get("location_id"),
                "description": f"{angle} is uniquely emphasized here.",
            }
        )

    for change in sorted(houses_a - houses_b):
        strongest_differences.append(
            {
                "type": "house_shift",
                "location_id": dest_a.get("location_id"),
                "description": f"{change} is uniquely foregrounded here.",
            }
        )
    for change in sorted(houses_b - houses_a):
        strongest_differences.append(
            {
                "type": "house_shift",
                "location_id": dest_b.get("location_id"),
                "description": f"{change} is uniquely foregrounded here.",
            }
        )

    strongest_differences = sorted(
        strongest_differences,
        key=lambda item: (0 if item["type"] == "angular_difference" else 1, item["description"]),
    )[:MAX_STRONGEST_DIFFERENCES]

    goals_a = {g["goal_key"]: g for g in record_a.get("goal_profile", {}).get("goals", [])}
    goals_b = {g["goal_key"]: g for g in record_b.get("goal_profile", {}).get("goals", [])}

    tradeoffs: list[dict[str, Any]] = []
    for goal_key in sorted(set(goals_a) | set(goals_b)):
        ga = goals_a.get(goal_key, {})
        gb = goals_b.get(goal_key, {})
        opp_a = ga.get("opportunity", 0.0)
        opp_b = gb.get("opportunity", 0.0)

        if abs(opp_a - opp_b) >= 0.3:
            winner, loser = (dest_a, dest_b) if opp_a > opp_b else (dest_b, dest_a)
            tradeoffs.append(
                {
                    "goal_key": goal_key,
                    "goal_label": _format_label(goal_key),
                    "stronger_location_id": winner.get("location_id"),
                    "weaker_location_id": loser.get("location_id"),
                    "delta": round(abs(opp_a - opp_b), 4),
                    "description": f"{winner.get('display_name')} offers significantly stronger support for {_format_label(goal_key)}.",
                }
            )

    tradeoffs = sorted(tradeoffs, key=lambda item: (-item["delta"], item["goal_key"]))[:MAX_TRADEOFFS]

    return {
        "comparison_version": COMPARISON_VERSION,
        "location_a_id": dest_a.get("location_id"),
        "location_b_id": dest_b.get("location_id"),
        "shared_themes": shared_theme_keys,
        "divergent_themes": divergent_theme_keys,
        "strongest_differences": strongest_differences,
        "tradeoffs": tradeoffs,
        "comparison_summary": _build_comparison_summary(
            name_a=name_a,
            name_b=name_b,
            dest_a=dest_a,
            dest_b=dest_b,
            shared_theme_keys=shared_theme_keys,
            strongest_differences=strongest_differences,
            tradeoffs=tradeoffs,
        ),
    }
