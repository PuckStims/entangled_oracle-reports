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

PURPOSE_LENS_LABELS = {
    "career": "Career",
    "belonging": "Belonging",
    "rest": "Rest",
    "partnership": "Partnership",
    "creative_visibility": "Creative visibility",
    "study": "Study",
    "retreat": "Retreat",
    "structure": "Structure",
    "experimentation": "Experimentation",
}


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


def _strength_band_rank(value: str) -> int:
    return {"defining": 0, "strong": 1, "moderate": 2, "supporting": 3, "background": 4}.get(value, 9)


def _compact_profile(record: dict) -> dict:
    destination = record.get("destination_context", {})
    clusters = record.get("theme_clusters", {}).get("clusters", [])
    goals = record.get("goal_profile", {}).get("goals", [])

    theme_labels: list[str] = []
    for cluster in sorted(clusters, key=lambda item: (_strength_band_rank(item.get("strength_band")), item.get("cluster_id", ""))):
        for theme in cluster.get("theme_keys", []):
            label = str(theme).replace("_", " ").title()
            if label not in theme_labels:
                theme_labels.append(label)
            if len(theme_labels) >= 4:
                break
        if len(theme_labels) >= 4:
            break

    goal_highlights = []
    for goal in sorted(goals, key=lambda item: (-item.get("opportunity", 0.0), item.get("goal_key", "")))[:3]:
        goal_highlights.append(
            {
                "goal_label": str(goal.get("goal_key", "")).replace("_", " ").title(),
                "fit_label": str(goal.get("fit_label", "")).replace("_", " "),
                "opportunity": goal.get("opportunity", 0.0),
            }
        )

    return {
        "name": destination.get("display_name", "Location"),
        "theme_labels": theme_labels,
        "goal_highlights": goal_highlights,
        "primary_evidence_count": len(record.get("evidence_record", {}).get("evidence_ranking", {}).get("primary_evidence", [])),
    }


def _comparison_notes(
    *,
    name_a: str,
    name_b: str,
    purpose_lens: str | None,
    comparison: dict,
) -> list[str]:
    notes = [
        "Use the shared themes as chart material that is likely to travel with you, not as proof that the two places feel interchangeable."
    ]
    if purpose_lens:
        label = PURPOSE_LENS_LABELS.get(purpose_lens, purpose_lens.replace("_", " ").title())
        notes.append(
            f"The active lens for this comparison is {label}. Read the tradeoffs as question-specific evidence, not as a universal winner/loser verdict."
        )
    if comparison.get("strongest_differences"):
        notes.append(
            "A short list of unique angular or house-emphasis differences usually matters more than a long cloud of mild divergent tags."
        )
    if comparison.get("tradeoffs"):
        notes.append(
            f"If {name_a} and {name_b} both stay plausible after the structural read, let the highest-delta tradeoffs break the tie before treating the chart as undecided."
        )
    else:
        notes.append(
            "If the tradeoff map stays thin, practical realities such as cost, language, care network, and timeline may deserve more weight than astrology in the final decision."
        )
    return notes


def assemble_between_places_context(
    record_a: dict,
    record_b: dict,
    comparison: dict,
    *,
    purpose_lens: str | None = None,
) -> dict:
    """
    Build a structured Between Places context from two full evidence records and their comparison.
    """
    dest_a = record_a.get("destination_context", {})
    dest_b = record_b.get("destination_context", {})
    name_a = dest_a.get("display_name", "Location A")
    name_b = dest_b.get("display_name", "Location B")
    sections = [
        {"id": "comparison_summary", "title": "Comparison Summary"},
        {"id": "place_profiles", "title": "Place Profiles"},
        {"id": "shared_themes", "title": "Shared Themes"},
        {"id": "divergent_themes", "title": "Divergent Themes"},
        {"id": "strongest_differences", "title": "Strongest Differences"},
        {"id": "tradeoffs", "title": "Tradeoffs"},
        {"id": "decision_notes", "title": "Decision Notes"},
    ]

    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "location_a": dest_a,
        "location_b": dest_b,
        "name_a": name_a,
        "name_b": name_b,
        "purpose_lens": purpose_lens,
        "purpose_lens_label": PURPOSE_LENS_LABELS.get(
            purpose_lens or "",
            purpose_lens.replace("_", " ").title() if purpose_lens else "",
        ),
        "comparison_record": comparison,
        "compact_profile_a": _compact_profile(record_a),
        "compact_profile_b": _compact_profile(record_b),
        "decision_notes": _comparison_notes(
            name_a=name_a,
            name_b=name_b,
            purpose_lens=purpose_lens,
            comparison=comparison,
        ),
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
    return assemble_between_places_context(record_a, record_b, comparison, purpose_lens=purpose_lens)
