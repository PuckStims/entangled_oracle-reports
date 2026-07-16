"""
Goal Compatibility Profile for the Location Services locational grammar.

This module evaluates the relevance of theme clusters for specific user goals 
without altering the underlying technical evidence strength.
"""
from __future__ import annotations

import copy
from typing import Any

from .taxonomy import GOAL_DIMENSIONS, GOAL_THEME_MAPPING

GOAL_PROFILE_VERSION = "location_services_goal_profile_v0.1.0"

def _copy(value: Any) -> Any:
    return copy.deepcopy(value)

def _compute_fit_label(opportunity: float, ease: float, demand: float, volatility: float) -> str:
    if opportunity < 0.2:
        return "low_relevance"
    
    if opportunity >= 0.7:
        if demand >= 0.6:
            return "strong_but_demanding"
        if volatility >= 0.6:
            return "promising_but_volatile"
        if ease >= 0.6:
            return "supportive_and_stable"
        return "strong_relevance"
    
    if ease >= 0.5 and demand < 0.4:
        return "quietly_useful"
    
    return "moderate_relevance"

def build_goal_profile(clusters: list[dict], purpose_lens: str | None = None) -> dict:
    """
    Rank relevance for user purposes based on theme clusters.
    """
    records = []
    
    # Pre-calculate cluster strengths mapped by theme
    theme_to_clusters = {}
    for cluster in clusters:
        if cluster.get("omit_from_primary_report"):
            continue
        for theme in cluster.get("theme_keys", []):
            theme_to_clusters.setdefault(theme, []).append(cluster)

    for goal_key in GOAL_DIMENSIONS:
        relevant_themes = GOAL_THEME_MAPPING.get(goal_key, [])
        
        supporting_clusters = []
        caution_clusters = []
        
        opportunity_sum = 0.0
        demand_sum = 0.0
        ease_sum = 0.0
        volatility_sum = 0.0
        
        for theme in relevant_themes:
            for cluster in theme_to_clusters.get(theme, []):
                # We approximate dimension scores from cluster bands and tags
                strength_val = 0.8 if cluster["strength_band"] in ("defining", "strong") else 0.4
                
                if "compensatory_structure" in cluster["cluster_type"]:
                    ease_sum += strength_val
                if "contradictory_axis" in cluster["cluster_type"]:
                    demand_sum += strength_val
                    volatility_sum += strength_val * 0.5
                    caution_clusters.append(cluster["cluster_id"])
                else:
                    opportunity_sum += strength_val
                    supporting_clusters.append(cluster["cluster_id"])
                    
                # Analyze pressure tags for demand/volatility
                if any(p in ["overreliance", "strain", "public_exposure"] for p in cluster.get("pressure_tags", [])):
                    demand_sum += strength_val * 0.5
                if any(p in ["disruption", "instability", "overidentification"] for p in cluster.get("pressure_tags", [])):
                    volatility_sum += strength_val * 0.5

        # Normalize metrics (0.0 to 1.0)
        # Using a simple cap for safety, though a real implementation might use an asymptote
        opportunity = min(1.0, opportunity_sum)
        demand = min(1.0, demand_sum)
        ease = min(1.0, ease_sum + (opportunity * 0.3)) # Base ease on opportunity unless offset by demand
        volatility = min(1.0, volatility_sum)
        durability = min(1.0, 1.0 - volatility + (ease * 0.5))
        
        # Apply purpose lens weighting (purely relevance boosting, no technical alteration)
        if purpose_lens and purpose_lens == goal_key:
            opportunity = min(1.0, opportunity * 1.2)
        
        fit_label = _compute_fit_label(opportunity, ease, demand, volatility)
        
        records.append({
            "goal_key": goal_key,
            "opportunity": round(opportunity, 4),
            "ease": round(ease, 4),
            "demand": round(demand, 4),
            "durability": round(durability, 4),
            "volatility": round(volatility, 4),
            "supporting_cluster_ids": sorted(list(set(supporting_clusters))),
            "caution_cluster_ids": sorted(list(set(caution_clusters))),
            "fit_label": fit_label,
            "fit_explanation_key": f"explanation_{fit_label}",
        })

    return {
        "goal_profile_version": GOAL_PROFILE_VERSION,
        "goals": records,
    }
