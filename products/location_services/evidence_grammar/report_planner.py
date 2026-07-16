"""
Report Planner for the Location Services locational grammar.

This module synthesizes theme clusters and goal profiles into an ordered 
narrative plan, without generating final prose.
"""
from __future__ import annotations

import copy
from typing import Any

REPORT_PLAN_VERSION = "location_services_report_plan_v0.1.0"

def _copy(value: Any) -> Any:
    return copy.deepcopy(value)

def _cluster_lookup(clusters: list[dict]) -> dict[str, dict]:
    return {cluster["cluster_id"]: cluster for cluster in clusters if isinstance(cluster, dict) and cluster.get("cluster_id")}

def _source_evidence_ids(cluster_ids: list[str], cluster_map: dict[str, dict]) -> list[str]:
    evidence_ids = []
    for cluster_id in cluster_ids:
        cluster = cluster_map.get(cluster_id) or {}
        evidence_ids.extend(cluster.get("source_evidence_ids", []))
    return sorted(dict.fromkeys(evidence_ids))

def _confidence_classification(clusters: list[dict]) -> str:
    foreground = [
        cluster for cluster in clusters
        if not cluster.get("omit_from_primary_report")
        and cluster.get("strength_band") in {"defining", "strong"}
    ]
    if not foreground:
        return "low_signal"

    bands = {cluster.get("confidence_band") for cluster in foreground}
    if "sensitive" in bands:
        return "sensitive"
    if "low" in bands:
        return "low"
    if "medium" in bands:
        return "medium"
    return "high"

def build_report_plan(
    clusters: list[dict], 
    goal_profile: dict, 
    product_type: str = "place_profile"
) -> dict:
    """
    Synthesize clusters and goal profiles into a section-by-section plan.
    """
    dominant_cluster_id = None
    primary_tradeoff_cluster_id = None
    supporting_cluster_ids = []
    appendix_inputs = []
    cluster_map = _cluster_lookup(clusters)

    # Sort clusters by priority (Defining/Strong first, then others)
    # We assume clusters are already somewhat ordered by the resolver's sorting,
    # but let's do a simple extraction based on bands.
    
    for cluster in clusters:
        cid = cluster["cluster_id"]
        if cluster.get("omit_from_primary_report"):
            appendix_inputs.append(cid)
            continue
            
        if cluster["cluster_type"] == "contradictory_axis" and not primary_tradeoff_cluster_id:
            primary_tradeoff_cluster_id = cid
            if not dominant_cluster_id:
                dominant_cluster_id = cid
            else:
                supporting_cluster_ids.append(cid)
            continue
            
        if not dominant_cluster_id and cluster["strength_band"] in ("defining", "strong"):
            dominant_cluster_id = cid
            continue
            
        supporting_cluster_ids.append(cid)

    # If no dominant found, fallback to the strongest available
    if not dominant_cluster_id and supporting_cluster_ids:
        dominant_cluster_id = supporting_cluster_ids.pop(0)

    # Goal guidance
    best_use_goal_keys = []
    mismatched_use_goal_keys = []
    
    for goal in goal_profile.get("goals", []):
        if goal["fit_label"] in ("strong_relevance", "supportive_and_stable"):
            best_use_goal_keys.append(goal["goal_key"])
        elif goal["opportunity"] < 0.2 and goal["demand"] > 0.6:
            mismatched_use_goal_keys.append(goal["goal_key"])

    # Build the section plan
    section_plan = []
    
    # Thesis section
    thesis_cluster_ids = [dominant_cluster_id] if dominant_cluster_id else []
    section_plan.append({
        "section_id": "thesis",
        "purpose": "State the one-sentence place thesis",
        "source_cluster_ids": thesis_cluster_ids,
        "source_evidence_ids": _source_evidence_ids(thesis_cluster_ids, cluster_map),
        "required_disclosures": [],
        "prose_status": "pending",
        "claim_boundary": "thesis_claim",
    })
    
    if dominant_cluster_id:
        section_plan.append({
            "section_id": "dominant_pattern",
            "purpose": "Expand on the primary geographic signature",
            "source_cluster_ids": [dominant_cluster_id],
            "source_evidence_ids": _source_evidence_ids([dominant_cluster_id], cluster_map),
            "required_disclosures": [],
            "prose_status": "pending",
            "claim_boundary": "bounded_interpretation",
        })
        
    if primary_tradeoff_cluster_id and primary_tradeoff_cluster_id != dominant_cluster_id:
        section_plan.append({
            "section_id": "primary_tradeoff",
            "purpose": "Address the contradictory axis directly",
            "source_cluster_ids": [primary_tradeoff_cluster_id],
            "source_evidence_ids": _source_evidence_ids([primary_tradeoff_cluster_id], cluster_map),
            "required_disclosures": [],
            "prose_status": "pending",
            "claim_boundary": "bounded_interpretation",
        })
        
    if supporting_cluster_ids:
        section_plan.append({
            "section_id": "supporting_patterns",
            "purpose": "Detail remaining supportive or complicating themes",
            "source_cluster_ids": _copy(supporting_cluster_ids),
            "source_evidence_ids": _source_evidence_ids(supporting_cluster_ids, cluster_map),
            "required_disclosures": [],
            "prose_status": "pending",
            "claim_boundary": "bounded_interpretation",
        })
        
    section_plan.append({
        "section_id": "practical_uses",
        "purpose": "Advise on best uses and areas of demand based on user goals",
        "source_cluster_ids": _copy(supporting_cluster_ids[:5]),
        "source_evidence_ids": _source_evidence_ids(supporting_cluster_ids[:5], cluster_map),
        "required_disclosures": ["goal_compatibility_is_not_guarantee"],
        "prose_status": "pending",
        "claim_boundary": "bounded_advice",
    })
    
    section_plan.append({
        "section_id": "technical_appendix",
        "purpose": "Disclose unsupported methods and low-signal data",
        "source_cluster_ids": _copy(appendix_inputs),
        "source_evidence_ids": _source_evidence_ids(appendix_inputs, cluster_map),
        "required_disclosures": ["unsupported_method_disclosure", "confidence_warning_if_any"],
        "prose_status": "pending",
        "claim_boundary": "technical_context",
    })

    confidence_classification = _confidence_classification(clusters)

    thesis_key = "thesis_template_default"
    if dominant_cluster_id:
        thesis_key = "thesis_template_driven_by_dominant"
    
    return {
        "report_plan_version": REPORT_PLAN_VERSION,
        "product_type": product_type,
        "thesis_key": thesis_key,
        "dominant_pattern_cluster_id": dominant_cluster_id,
        "primary_tradeoff_cluster_id": primary_tradeoff_cluster_id,
        "supporting_cluster_ids": supporting_cluster_ids,
        "best_use_goal_keys": best_use_goal_keys,
        "mismatched_use_goal_keys": mismatched_use_goal_keys,
        "duration_profile": "baseline_static",
        "confidence_classification": confidence_classification,
        "section_plan": section_plan,
        "appendix_inputs": appendix_inputs,
    }
