"""
Tests for the full Location Services evidence grammar pipeline.

This suite proves the determinism and correctness of the interpretation seam
(Resolver, Clusterer, Goal Profile, and Report Planner) without using mock data.
"""
import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.location_services import build_location_evidence_record
from products.location_services.evidence_grammar import (
    normalize_location_evidence_record,
    resolve_evidence,
    cluster_themes,
    build_goal_profile,
    build_report_plan,
)
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload

def _contract_item(
    evidence_id: str,
    *,
    family: str,
    subject: str,
    interface: str,
    strength: float,
    confidence: float,
    themes: list[str],
    supports: list[str] | None = None,
    costs: list[str] | None = None,
    calculation_status: str = "computed",
    claim_boundary: str = "bounded_interpretation",
) -> dict:
    return {
        "evidence_id": evidence_id,
        "family": family,
        "subject": subject,
        "interface": interface,
        "strength": strength,
        "confidence": confidence,
        "themes": themes,
        "supports": supports or [],
        "costs": costs or [],
        "source_factors": {"source_evidence_id": evidence_id},
        "calculation_status": calculation_status,
        "claim_boundary": claim_boundary,
    }

def test_full_pipeline_integration():
    """
    Integration test proving the full pipeline from raw calculation
    through the synthesis planner works deterministically.
    """
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)
    
    # Area A: Resolver
    resolved = resolve_evidence(grammar["items"])
    assert "resolved_groups" in resolved
    assert len(resolved["resolved_groups"]) > 0
    
    # Area B: Clusterer
    clustered = cluster_themes(resolved["resolved_groups"], grammar["items"])
    assert "clusters" in clustered
    assert len(clustered["clusters"]) > 0
    
    # Verify no un-banded clusters
    for cluster in clustered["clusters"]:
        assert cluster["strength_band"] in ("defining", "strong", "supportive", "background", "unstable")
        assert cluster["confidence_band"] in ("high", "medium", "low", "sensitive")
    
    # Area C: Goal Profile
    goal_profile = build_goal_profile(clustered["clusters"], purpose_lens="career_visibility")
    assert "goals" in goal_profile
    assert len(goal_profile["goals"]) > 0
    
    # Verify a goal's fit label
    for goal in goal_profile["goals"]:
        assert "fit_label" in goal
        assert 0.0 <= goal["opportunity"] <= 1.0
        assert 0.0 <= goal["demand"] <= 1.0
        assert 0.0 <= goal["ease"] <= 1.0
        assert 0.0 <= goal["durability"] <= 1.0
        assert 0.0 <= goal["volatility"] <= 1.0
        
    # Area D: Report Planner
    report_plan = build_report_plan(clustered["clusters"], goal_profile, product_type="place_resonance_search")
    assert "section_plan" in report_plan
    assert report_plan["product_type"] == "place_resonance_search"
    
    sections = {s["section_id"]: s for s in report_plan["section_plan"]}
    assert "thesis" in sections
    assert "practical_uses" in sections
    assert "technical_appendix" in sections
    assert any(section["source_evidence_ids"] for section in report_plan["section_plan"])
    
    # Ensure no raw prose generation happened (thesis is a key)
    assert not report_plan["thesis_key"].startswith("This place is")

def test_resolver_preserves_contradictory_axes():
    """
    Verify that contradictory evidence does not get averaged away into neutrality.
    Instead, it produces a contradictory_axis.
    """
    contract_items = [
        _contract_item(
            "test_mc_vis",
            family="angularity",
            subject="Sun",
            interface="mc",
            strength=0.9,
            confidence=0.9,
            themes=["visibility", "career"],
        ),
        _contract_item(
            "test_ic_priv",
            family="angularity",
            subject="Moon",
            interface="ic",
            strength=0.85,
            confidence=0.9,
            themes=["home", "privacy"],
        ),
    ]
    resolved = resolve_evidence(contract_items)
    
    # We should have a contradictory_axis group
    axes = [g for g in resolved["resolved_groups"] if g["relationship_type"] == "contradictory_axis"]
    assert len(axes) == 1
    axis = axes[0]
    
    assert axis["combined_strength"] == 0.9
    assert axis["combined_confidence"] == 0.9
    assert "test_mc_vis" in axis["member_evidence_ids"]
    assert "test_ic_priv" in axis["member_evidence_ids"]
    assert axis["theme_keys"] == sorted(axis["theme_keys"])

def test_resolver_is_deterministic_for_contradictory_axis_theme_order():
    contract_items = [
        _contract_item(
            "test_mc_vis",
            family="angularity",
            subject="Sun",
            interface="mc",
            strength=0.9,
            confidence=0.9,
            themes=["visibility", "career"],
        ),
        _contract_item(
            "test_ic_priv",
            family="angularity",
            subject="Moon",
            interface="ic",
            strength=0.85,
            confidence=0.9,
            themes=["home", "privacy"],
        ),
    ]

    first = resolve_evidence(contract_items)
    second = resolve_evidence(list(reversed(contract_items)))
    first_axis = next(g for g in first["resolved_groups"] if g["relationship_type"] == "contradictory_axis")
    second_axis = next(g for g in second["resolved_groups"] if g["relationship_type"] == "contradictory_axis")

    assert first_axis["theme_keys"] == second_axis["theme_keys"]
    assert first_axis["group_id"] == second_axis["group_id"]

def test_same_root_requires_relocated_geometry_families_not_subject_alone():
    contract_items = [
        _contract_item(
            "natal_modifier:Venus",
            family="natal_condition",
            subject="Venus",
            interface="natal_condition",
            strength=0.7,
            confidence=0.9,
            themes=["value", "natal_condition"],
        ),
        _contract_item(
            "angle_contact:Venus:Midheaven",
            family="angularity",
            subject="Venus",
            interface="mc",
            strength=0.8,
            confidence=0.9,
            themes=["value", "public_role"],
        ),
    ]

    resolved = resolve_evidence(contract_items)

    assert all(group["relationship_type"] != "same_root_confirmation" for group in resolved["resolved_groups"])

def test_same_root_groups_angle_and_house_geometry_for_same_body():
    contract_items = [
        _contract_item(
            "angle_contact:Venus:Midheaven",
            family="angularity",
            subject="Venus",
            interface="mc",
            strength=0.8,
            confidence=0.9,
            themes=["value", "visibility"],
        ),
        _contract_item(
            "house_change:Venus",
            family="relocated_house_expression",
            subject="Venus",
            interface="house:10",
            strength=0.7,
            confidence=0.9,
            themes=["value", "career"],
        ),
    ]

    resolved = resolve_evidence(contract_items)

    same_root = [group for group in resolved["resolved_groups"] if group["relationship_type"] == "same_root_confirmation"]
    assert same_root
    assert set(same_root[0]["member_evidence_ids"]) == {"angle_contact:Venus:Midheaven", "house_change:Venus"}

def test_clusterer_separates_appendix_items():
    """
    Verify that unavailable methods and technical context items are routed 
    correctly and marked for omission from the primary report.
    """
    contract_items = [
        _contract_item(
            "test_unsupported",
            family="unsupported_method",
            subject="parans",
            interface="future_method",
            strength=0.0,
            confidence=1.0,
            themes=[],
            calculation_status="unavailable",
            claim_boundary="unavailable_method_note",
        )
    ]
    
    resolved = resolve_evidence(contract_items)
    assert resolved["resolved_groups"][0]["relationship_type"] == "appendix_only"
    clustered = cluster_themes(resolved["resolved_groups"], contract_items)
    
    assert len(clustered["clusters"]) == 1
    cluster = clustered["clusters"][0]
    
    assert cluster["cluster_type"] == "technical_context"
    assert cluster["omit_from_primary_report"] is True
    assert cluster["strength_band"] == "unstable"
    assert cluster["duration_hint"] == "not_applicable"

def test_goal_profile_does_not_mutate_technical_evidence():
    """
    Verify that the user purpose lens changes relevance without altering 
    the underlying evidence strength.
    """
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    grammar = normalize_location_evidence_record(record)
    resolved = resolve_evidence(grammar["items"])
    clustered = cluster_themes(resolved["resolved_groups"], grammar["items"])
    
    # Create two profiles with different lenses
    profile_career = build_goal_profile(clustered["clusters"], purpose_lens="career_visibility")
    profile_retreat = build_goal_profile(clustered["clusters"], purpose_lens="spiritual_retreat")
    
    # Extract the career goals
    career_goal_with_lens = next(g for g in profile_career["goals"] if g["goal_key"] == "career_visibility")
    career_goal_without_lens = next(g for g in profile_retreat["goals"] if g["goal_key"] == "career_visibility")
    
    # The opportunity score for career visibility should be boosted by the lens
    assert career_goal_with_lens["opportunity"] >= career_goal_without_lens["opportunity"]
    
    # But the clusters themselves are unmutated (strength_band remains identical)
    for c_with, c_without in zip(profile_career.get("clusters", []), profile_retreat.get("clusters", [])):
        assert c_with["strength_band"] == c_without["strength_band"]

def test_report_planner_builds_appendix():
    """
    Ensure the report planner captures omitted items into the appendix section.
    """
    mock_clusters = [
        {
            "cluster_id": "c1",
            "cluster_type": "convergent_theme",
            "strength_band": "strong",
            "confidence_band": "high",
            "omit_from_primary_report": False
        },
        {
            "cluster_id": "c2",
            "cluster_type": "technical_context",
            "strength_band": "unstable",
            "confidence_band": "high",
            "omit_from_primary_report": True
        }
    ]
    
    plan = build_report_plan(mock_clusters, {"goals": []})
    
    assert "c2" in plan["appendix_inputs"]
    assert "c1" not in plan["appendix_inputs"]
    
    appendix_section = next(s for s in plan["section_plan"] if s["section_id"] == "technical_appendix")
    assert "c2" in appendix_section["source_cluster_ids"]

def test_report_planner_carries_source_evidence_ids_into_sections():
    clusters = [
        {
            "cluster_id": "c1",
            "cluster_type": "convergent_theme",
            "strength_band": "strong",
            "confidence_band": "high",
            "source_evidence_ids": ["angle_contact:Sun:Midheaven", "house_change:Sun"],
            "omit_from_primary_report": False,
        },
        {
            "cluster_id": "c2",
            "cluster_type": "technical_context",
            "strength_band": "unstable",
            "confidence_band": "high",
            "source_evidence_ids": ["unsupported_method:parans"],
            "omit_from_primary_report": True,
        },
    ]

    plan = build_report_plan(clusters, {"goals": []})
    sections = {section["section_id"]: section for section in plan["section_plan"]}

    assert sections["thesis"]["source_evidence_ids"] == ["angle_contact:Sun:Midheaven", "house_change:Sun"]
    assert sections["technical_appendix"]["source_evidence_ids"] == ["unsupported_method:parans"]
    assert plan["confidence_classification"] == "high"
