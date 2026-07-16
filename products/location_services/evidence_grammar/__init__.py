"""
Normalized evidence grammar for Location Services.

This package adapts the current LocationEvidenceRecord into a reusable
evidence layer. It does not render prose and does not compute future methods.
"""
from products.location_services.evidence_grammar.adapter import (
    GRAMMAR_VERSION,
    normalize_location_evidence_record,
)
from products.location_services.evidence_grammar.resolver import resolve_evidence, RESOLVER_VERSION
from products.location_services.evidence_grammar.theme_clusterer import cluster_themes, THEME_CLUSTER_VERSION
from products.location_services.evidence_grammar.goal_profile import build_goal_profile, GOAL_PROFILE_VERSION
from products.location_services.evidence_grammar.report_planner import build_report_plan, REPORT_PLAN_VERSION

__all__ = [
    "GRAMMAR_VERSION",
    "normalize_location_evidence_record",
    "RESOLVER_VERSION",
    "resolve_evidence",
    "THEME_CLUSTER_VERSION",
    "cluster_themes",
    "GOAL_PROFILE_VERSION",
    "build_goal_profile",
    "REPORT_PLAN_VERSION",
    "build_report_plan",
]
