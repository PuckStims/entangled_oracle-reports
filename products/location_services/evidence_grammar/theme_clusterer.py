"""
Theme Clusterer for the Location Services locational grammar.

This module converts resolved evidence groups into reader-facing interpretive 
clusters, banding them by strength and confidence, without inventing final prose.
"""
from __future__ import annotations

import copy
from typing import Any

from .taxonomy import STRENGTH_THRESHOLDS, CONFIDENCE_THRESHOLDS

THEME_CLUSTER_VERSION = "location_services_theme_clusterer_v0.1.0"

def _copy(value: Any) -> Any:
    return copy.deepcopy(value)

def _band_strength(strength: float) -> str:
    if strength >= STRENGTH_THRESHOLDS["defining"]:
        return "defining"
    if strength >= STRENGTH_THRESHOLDS["strong"]:
        return "strong"
    if strength >= STRENGTH_THRESHOLDS["supportive"]:
        return "supportive"
    if strength >= STRENGTH_THRESHOLDS["background"]:
        return "background"
    return "unstable"

def _band_confidence(confidence: float) -> str:
    if confidence >= CONFIDENCE_THRESHOLDS["high"]:
        return "high"
    if confidence >= CONFIDENCE_THRESHOLDS["medium"]:
        return "medium"
    if confidence >= CONFIDENCE_THRESHOLDS["low"]:
        return "low"
    return "sensitive"

def cluster_themes(resolved_groups: list[dict], normalized_items: list[dict]) -> dict:
    """
    Convert resolved evidence groups into theme clusters.
    """
    # Create a quick lookup for items to extract opportunity/pressure tags
    item_map = {item["evidence_id"]: item for item in normalized_items}

    clusters = []

    for idx, group in enumerate(resolved_groups):
        rel_type = group.get("relationship_type", "single_signal")
        
        # Determine cluster type
        if rel_type in ("independent_repetition", "same_root_confirmation", "single_signal"):
            cluster_type = "convergent_theme"
        elif rel_type == "contradictory_axis":
            cluster_type = "contradictory_axis"
        elif rel_type == "compensatory_structure":
            cluster_type = "compensatory_structure"
        elif rel_type == "technical_context":
            cluster_type = "technical_context"
        elif rel_type == "appendix_only":
            cluster_type = "technical_context"
        elif rel_type == "low_signal":
            if group.get("claim_boundary") == "technical_context":
                cluster_type = "technical_context"
            else:
                cluster_type = "low_signal"
        else:
            cluster_type = "mixed_location"

        # Gather tags from member evidence items
        opp_tags = set()
        press_tags = set()
        for eid in group.get("member_evidence_ids", []):
            item = item_map.get(eid)
            if item:
                opp_tags.update(item.get("supports", []))
                press_tags.update(item.get("costs", []))

        strength_band = _band_strength(group.get("combined_strength", 0))
        confidence_band = _band_confidence(group.get("combined_confidence", 0))
        
        omit = False
        if cluster_type in ("low_signal", "technical_context") or strength_band == "unstable":
            omit = True

        theme_keys = sorted(dict.fromkeys(group.get("theme_keys", [])))
        headline_key = f"{cluster_type}_{'_'.join(theme_keys[:2] or ['unknown'])}"
        duration_hint = "not_applicable" if cluster_type == "technical_context" else "baseline_static"

        clusters.append({
            "cluster_id": f"cluster_{idx}_{cluster_type}",
            "cluster_type": cluster_type,
            "headline_key": headline_key,
            "theme_keys": theme_keys,
            "supporting_group_ids": [group["group_id"]],
            "tension_group_ids": [],  # Could be expanded if contradiction axes merge groups
            "source_evidence_ids": _copy(group.get("member_evidence_ids", [])),
            "strength_band": strength_band,
            "confidence_band": confidence_band,
            "opportunity_tags": sorted(list(opp_tags)),
            "pressure_tags": sorted(list(press_tags)),
            "duration_hint": duration_hint,
            "omit_from_primary_report": omit,
        })

    return {
        "theme_cluster_version": THEME_CLUSTER_VERSION,
        "clusters": clusters,
    }
