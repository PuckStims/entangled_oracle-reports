"""
Evidence Resolver for the Location Services locational grammar.

This module consumes normalized evidence items and groups them into 
relationship-aware evidence groups (independent repetition, same-root
confirmation, contradiction, compensation, single signal, low signal).
"""
from __future__ import annotations

import copy
from typing import Any

from .taxonomy import CONTRADICTION_PAIRS, COMPENSATORY_THEMES

RESOLVER_VERSION = "location_services_evidence_resolver_v0.1.0"
APPENDIX_RELATIONSHIP_TYPE = "appendix_only"
TECHNICAL_RELATIONSHIP_TYPE = "technical_context"
SAME_ROOT_FAMILIES = frozenset({"angularity", "relocated_house_expression"})

def _copy(value: Any) -> Any:
    return copy.deepcopy(value)

def _generate_group_id(relationship_type: str, primary_theme: str) -> str:
    return f"resolved_group:{relationship_type}:{primary_theme}"

def _source_evidence_id(item: dict) -> str:
    source_factors = item.get("source_factors") or {}
    value = source_factors.get("source_evidence_id") or item.get("evidence_id")
    return str(value)

def _same_root_key(item: dict) -> tuple[str, str] | None:
    """
    Same-root confirmation is intentionally narrow. It is allowed only for
    current relocated chart geometry where an angle contact and house-expression
    item describe the same body-place relationship. Natal condition, warnings,
    goal data, and future methods must not be collapsed into this relationship.
    """
    family = item.get("family")
    if family not in SAME_ROOT_FAMILIES:
        return None
    subject = item.get("subject")
    if not subject:
        return None
    return ("relocated_body_geometry", str(subject))

def _relationship_group_id(relationship_type: str, themes: list[str], member_ids: list[str]) -> str:
    theme_part = "_".join(sorted(themes)) if themes else "unknown"
    member_part = "_".join(sorted(member_ids))
    return f"resolved_group:{relationship_type}:{theme_part}:{member_part}"

def _combined_themes(*groups: dict) -> list[str]:
    themes = []
    for group in groups:
        themes.extend(group.get("theme_keys", []))
    return sorted(dict.fromkeys(themes))

def _combined_member_ids(*groups: dict) -> list[str]:
    member_ids = []
    for group in groups:
        member_ids.extend(group.get("member_evidence_ids", []))
    return sorted(dict.fromkeys(member_ids))

def resolve_evidence(normalized_items: list[dict]) -> dict:
    """
    Resolve normalized evidence items into relationship-aware groups.
    """
    # 1. Index items and separate unavailable methods
    computed_items = []
    appendix_items = []
    for item in normalized_items:
        if item.get("calculation_status") == "unavailable":
            appendix_items.append(item)
        elif item.get("claim_boundary") == "technical_context":
            appendix_items.append(item)
        else:
            computed_items.append(item)

    groups = []
    used_item_ids = set()

    # We will build an index by theme to detect repetition
    theme_to_items = {}
    for item in computed_items:
        for theme in item.get("themes", []):
            theme_to_items.setdefault(theme, []).append(item)

    # 3 & 4. Detect same-root confirmation and independent repetition.
    sorted_themes = sorted(theme_to_items.keys())
    
    for theme in sorted_themes:
        items_for_theme = theme_to_items[theme]
        available_items = [i for i in items_for_theme if i["evidence_id"] not in used_item_ids]
        if not available_items:
            continue

        root_to_items = {}
        for item in available_items:
            root_key = _same_root_key(item)
            if root_key is not None:
                root_to_items.setdefault(root_key, []).append(item)

        for root_key, sub_items in sorted(root_to_items.items()):
            families = {item.get("family") for item in sub_items}
            if len(sub_items) > 1 and len(families) > 1:
                # Same root confirmation
                member_ids = sorted(i["evidence_id"] for i in sub_items)
                max_strength = max((i.get("strength", 0) for i in sub_items), default=0)
                max_confidence = max((i.get("confidence", 0) for i in sub_items), default=0)
                
                groups.append({
                    "group_id": _relationship_group_id("same_root_confirmation", [theme, root_key[1]], member_ids),
                    "relationship_type": "same_root_confirmation",
                    "theme_keys": [theme],
                    "member_evidence_ids": member_ids,
                    "representative_evidence_id": member_ids[0],
                    "combined_strength": max_strength,
                    "combined_confidence": max_confidence,
                    "breadth_score": 1.0,
                    "precision_score": 1.5,
                    "claim_boundary": "bounded_interpretation",
                    "resolution_note": "Same-root confirmation detected.",
                })
                used_item_ids.update(member_ids)

    # Re-evaluate independent repetition for themes that still have items across different subjects
    for theme in sorted_themes:
        available_items = [i for i in theme_to_items[theme] if i["evidence_id"] not in used_item_ids]
        if len(available_items) > 1:
            member_ids = sorted(i["evidence_id"] for i in available_items)
            max_strength = max((i.get("strength", 0) for i in available_items), default=0)
            max_confidence = max((i.get("confidence", 0) for i in available_items), default=0)
            groups.append({
                "group_id": _relationship_group_id("independent_repetition", [theme], member_ids),
                "relationship_type": "independent_repetition",
                "theme_keys": [theme],
                "member_evidence_ids": member_ids,
                "representative_evidence_id": member_ids[0],
                "combined_strength": max_strength,
                "combined_confidence": max_confidence,
                "breadth_score": 1.5,
                "precision_score": 1.0,
                "claim_boundary": "bounded_interpretation",
                "resolution_note": "Independent repetition detected.",
            })
            used_item_ids.update(member_ids)

    # Group remaining as single signal or low signal
    for item in computed_items:
        if item["evidence_id"] not in used_item_ids:
            strength = item.get("strength", 0)
            rel_type = "single_signal" if strength >= 0.4 else "low_signal"
            themes = sorted(dict.fromkeys(item.get("themes", [])))
            theme = themes[0] if themes else "unknown"
            groups.append({
                "group_id": _relationship_group_id(rel_type, themes, [item["evidence_id"]]),
                "relationship_type": rel_type,
                "theme_keys": themes,
                "member_evidence_ids": [item["evidence_id"]],
                "representative_evidence_id": item["evidence_id"],
                "combined_strength": strength,
                "combined_confidence": item.get("confidence", 0),
                "breadth_score": 1.0,
                "precision_score": 1.0,
                "claim_boundary": item.get("claim_boundary", "bounded_interpretation"),
                "resolution_note": "Single item.",
            })
            used_item_ids.add(item["evidence_id"])

    # 5. Detect contradiction
    # Cross-reference existing groups based on CONTRADICTION_PAIRS
    new_groups = []
    groups_to_remove = set()
    for pair_a, pair_b in CONTRADICTION_PAIRS:
        # Find groups supporting A and B
        groups_a = [g for g in groups if g["group_id"] not in groups_to_remove and set(g["theme_keys"]).intersection(pair_a)]
        groups_b = [g for g in groups if g["group_id"] not in groups_to_remove and set(g["theme_keys"]).intersection(pair_b)]
        
        if groups_a and groups_b:
            # We found a contradiction. Merge them into a contradiction axis.
            # Take the strongest from A and strongest from B
            best_a = max(groups_a, key=lambda g: g["combined_strength"])
            best_b = max(groups_b, key=lambda g: g["combined_strength"])
            
            combined_themes = _combined_themes(best_a, best_b)
            member_ids = _combined_member_ids(best_a, best_b)
            new_groups.append({
                "group_id": _relationship_group_id("contradictory_axis", combined_themes, member_ids),
                "relationship_type": "contradictory_axis",
                "theme_keys": combined_themes,
                "member_evidence_ids": member_ids,
                "representative_evidence_id": best_a["representative_evidence_id"],
                "combined_strength": max(best_a["combined_strength"], best_b["combined_strength"]),
                "combined_confidence": min(best_a["combined_confidence"], best_b["combined_confidence"]),
                "breadth_score": 2.0,
                "precision_score": 1.0,
                "claim_boundary": "bounded_interpretation",
                "resolution_note": "Contradictory axis detected.",
            })
            groups_to_remove.add(best_a["group_id"])
            groups_to_remove.add(best_b["group_id"])

    # 6. Detect compensation
    for group in groups:
        if group["group_id"] in groups_to_remove:
            continue
        if any(t in COMPENSATORY_THEMES for t in group["theme_keys"]):
            group["relationship_type"] = "compensatory_structure"
            group["resolution_note"] = "Compensatory structure detected."

    # Finalize groups
    final_groups = [g for g in groups if g["group_id"] not in groups_to_remove] + new_groups
    
    # Add appendix items as explicit appendix/technical groups.
    for item in appendix_items:
        relationship_type = (
            TECHNICAL_RELATIONSHIP_TYPE
            if item.get("claim_boundary") == "technical_context"
            else APPENDIX_RELATIONSHIP_TYPE
        )
        themes = sorted(dict.fromkeys(item.get("themes", [])))
        final_groups.append({
            "group_id": _relationship_group_id(relationship_type, themes or [str(item.get("subject", "unknown"))], [item["evidence_id"]]),
            "relationship_type": relationship_type,
            "theme_keys": themes,
            "member_evidence_ids": [item["evidence_id"]],
            "representative_evidence_id": item["evidence_id"],
            "combined_strength": item.get("strength", 0),
            "combined_confidence": item.get("confidence", 0),
            "breadth_score": 0.0,
            "precision_score": 0.0,
            "claim_boundary": item.get("claim_boundary", "technical_context"),
            "resolution_note": "Appendix item.",
            "calculation_status": item.get("calculation_status"),
        })

    # Sort groups deterministically by strength, then confidence, then breadth, then ID
    final_groups.sort(key=lambda g: (-g["combined_strength"], -g["combined_confidence"], -g["breadth_score"], g["group_id"]))

    return {
        "resolved_evidence_version": RESOLVER_VERSION,
        "resolved_groups": final_groups,
    }
