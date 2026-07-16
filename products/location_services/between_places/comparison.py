"""
Between Places comparison engine.

This module implements the core comparison logic for two or more destinations,
identifying shared themes, divergent themes, strongest differences, and purpose tradeoffs.
"""
from __future__ import annotations

import copy
from typing import Any

COMPARISON_VERSION = "between_places_comparison_v0.1.0"


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
            angles.add(f"{contact.get('body')} on {contact.get('angle')}")
    return angles


def _extract_house_changes(record: dict) -> set[str]:
    changes = set()
    for change in record.get("evidence_record", {}).get("planet_house_changes", []):
        if change.get("movement_type") in ("newly_angular", "left_angle"):
            changes.add(f"{change.get('body')} {change.get('movement_type').replace('_', ' ')}")
    return changes


def build_comparison_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compare multiple destination records (currently exactly 2) based on their grammar outputs.
    
    Each record must have:
    - destination_context
    - evidence_record
    - normalized_evidence
    - resolved_evidence
    - theme_clusters
    - goal_profile
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

    shared_theme_keys = sorted(list(themes_a & themes_b))
    divergent_theme_keys = sorted(list(themes_a ^ themes_b))

    angles_a = _extract_angles(record_a)
    angles_b = _extract_angles(record_b)
    
    houses_a = _extract_house_changes(record_a)
    houses_b = _extract_house_changes(record_b)

    strongest_differences = []
    
    # Angular differences
    for angle in angles_a - angles_b:
        strongest_differences.append({
            "type": "angular_difference",
            "location_id": dest_a.get("location_id"),
            "description": f"{angle} is uniquely emphasized here.",
        })
    for angle in angles_b - angles_a:
        strongest_differences.append({
            "type": "angular_difference",
            "location_id": dest_b.get("location_id"),
            "description": f"{angle} is uniquely emphasized here.",
        })
        
    # House changes
    for change in houses_a - houses_b:
        strongest_differences.append({
            "type": "house_shift",
            "location_id": dest_a.get("location_id"),
            "description": f"{change.capitalize()} here.",
        })
    for change in houses_b - houses_a:
        strongest_differences.append({
            "type": "house_shift",
            "location_id": dest_b.get("location_id"),
            "description": f"{change.capitalize()} here.",
        })

    # Tradeoffs from goal profiles
    goals_a = {g["goal_key"]: g for g in record_a.get("goal_profile", {}).get("goals", [])}
    goals_b = {g["goal_key"]: g for g in record_b.get("goal_profile", {}).get("goals", [])}
    
    tradeoffs = []
    for goal_key in set(goals_a.keys()) | set(goals_b.keys()):
        ga = goals_a.get(goal_key, {})
        gb = goals_b.get(goal_key, {})
        opp_a = ga.get("opportunity", 0.0)
        opp_b = gb.get("opportunity", 0.0)
        
        if abs(opp_a - opp_b) >= 0.3:
            winner, loser = (dest_a, dest_b) if opp_a > opp_b else (dest_b, dest_a)
            tradeoffs.append({
                "goal_key": goal_key,
                "stronger_location_id": winner.get("location_id"),
                "weaker_location_id": loser.get("location_id"),
                "delta": abs(opp_a - opp_b),
                "description": f"{winner.get('display_name')} offers significantly stronger support for {goal_key.replace('_', ' ')}."
            })

    return {
        "comparison_version": COMPARISON_VERSION,
        "location_a_id": dest_a.get("location_id"),
        "location_b_id": dest_b.get("location_id"),
        "shared_themes": shared_theme_keys,
        "divergent_themes": divergent_theme_keys,
        "strongest_differences": strongest_differences,
        "tradeoffs": tradeoffs,
    }
