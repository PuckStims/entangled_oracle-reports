"""
Between Places report-context assembly.

This module turns two LocationEvidenceRecords into a structured draft context
for the Between Places comparison product, passing them through the grammar
pipeline and generating a comparison record.
"""
from __future__ import annotations

from engine.location_services import build_location_evidence_record
from products.location_services.evidence_grammar import (
    normalize_location_evidence_record,
    resolve_evidence,
    cluster_themes,
    build_goal_profile,
)
from products.location_services.between_places.comparison import build_comparison_record


CONTEXT_VERSION = "between_places_context_v0.3.0"
REPORT_TYPE = "location_services.between_places"
PRODUCT_NAME = "Between Places"


def _build_full_record(natal_payload: dict, destination: dict, purpose_lens: str | None = None) -> dict:
    evidence = build_location_evidence_record(natal_payload, destination, purpose_lens=purpose_lens)
    normalized = normalize_location_evidence_record(evidence)
    resolved = resolve_evidence(normalized.get("items", []))
    clusters = cluster_themes(resolved.get("resolved_groups", []), normalized.get("items", []))
    goal_profile = build_goal_profile(clusters.get("clusters", []), purpose_lens=purpose_lens)
    
    return {
        "destination_context": evidence.get("destination_context", {}),
        "evidence_record": evidence,
        "normalized_evidence": normalized,
        "resolved_evidence": resolved,
        "theme_clusters": clusters,
        "goal_profile": goal_profile,
    }


def assemble_between_places_context(record_a: dict, record_b: dict, comparison: dict) -> dict:
    """
    Build a structured Between Places context from two full evidence records and their comparison.
    """
    dest_a = record_a.get("destination_context", {})
    dest_b = record_b.get("destination_context", {})
    name_a = dest_a.get("display_name", "Location A")
    name_b = dest_b.get("display_name", "Location B")
    sections = [
        {"id": "shared_themes", "title": "Shared Themes"},
        {"id": "divergent_themes", "title": "Divergent Themes"},
        {"id": "strongest_differences", "title": "Strongest Differences"},
        {"id": "tradeoffs", "title": "Tradeoffs"},
    ]

    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "location_a": dest_a,
        "location_b": dest_b,
        "name_a": name_a,
        "name_b": name_b,
        "comparison_record": comparison,
        "record_a": record_a,
        "record_b": record_b,
        "sections": sections,
    }


def build_between_places_context(
    natal_payload: dict,
    destination_a: dict,
    destination_b: dict,
    *,
    purpose_lens: str | None = None
) -> dict:
    """
    Batch record-generation wrapper seam for comparison.
    """
    record_a = _build_full_record(natal_payload, destination_a, purpose_lens=purpose_lens)
    record_b = _build_full_record(natal_payload, destination_b, purpose_lens=purpose_lens)
    comparison = build_comparison_record([record_a, record_b])
    return assemble_between_places_context(record_a, record_b, comparison)
