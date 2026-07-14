"""
Between Places report-context assembly.

This module turns two LocationEvidenceRecords into a structured draft context
for the Between Places comparison product.
"""
from __future__ import annotations

CONTEXT_VERSION = "between_places_context_v0.2.0"
REPORT_TYPE = "location_services.between_places"
PRODUCT_NAME = "Between Places"

def assemble_between_places_context(evidence_record_a: dict, evidence_record_b: dict) -> dict:
    """
    Build a structured Between Places draft context from two evidence records.
    """
    dest_a = evidence_record_a.get("destination_context", {})
    dest_b = evidence_record_b.get("destination_context", {})
    name_a = dest_a.get("display_name", "Location A")
    name_b = dest_b.get("display_name", "Location B")

    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "location_a": dest_a,
        "location_b": dest_b,
        "name_a": name_a,
        "name_b": name_b,
        "sections": [
            {
                "id": "comparison_summary",
                "title": "Comparison Summary",
                "kicker": "At a Glance",
                "blocks": [
                    {
                        "id": "executive_summary",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": f"Write the high-level synthesis of how {name_a} and {name_b} contrast.",
                            "note": "NOT_COMPUTABLE: We need the differential logic output here."
                        }
                    }
                ]
            },
            {
                "id": "place_profiles",
                "title": "Place Profiles",
                "kicker": "Baseline Signatures",
                "blocks": [
                    {
                        "id": "profile_a",
                        "title": f"Profile: {name_a}",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": f"Summarize the static signature of {name_a}.",
                            "note": "Derived from location_a evidence."
                        }
                    },
                    {
                        "id": "profile_b",
                        "title": f"Profile: {name_b}",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": f"Summarize the static signature of {name_b}.",
                            "note": "Derived from location_b evidence."
                        }
                    }
                ]
            },
            {
                "id": "best_fit_by_purpose",
                "title": "Best Fit By Purpose",
                "kicker": "Actionable Lenses",
                "is_future_method": True,
                "future_title": "Purpose Matching (Coming Soon)",
                "future_description": "Our upcoming routing logic will automatically classify which location better serves specific life domains (Career, Rest, Creativity).",
                "blocks": []
            },
            {
                "id": "strongest_difference",
                "title": "Strongest Difference",
                "kicker": "Key Contrast",
                "blocks": [
                    {
                        "id": "key_contrast",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "What is the single biggest astrological shift between these two places?",
                            "note": "NOT_COMPUTABLE: Requires delta analysis."
                        }
                    }
                ]
            },
            {
                "id": "shared_themes",
                "title": "Shared Themes",
                "kicker": "Common Ground",
                "blocks": [
                    {
                        "id": "common_ground",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "What planetary or thematic emphasis exists in both places?",
                            "note": "NOT_COMPUTABLE: Requires intersection analysis."
                        }
                    }
                ]
            },
            {
                "id": "tradeoff_map",
                "title": "Tradeoff Map",
                "kicker": "What You Gain vs Lose",
                "blocks": [
                    {
                        "id": "tradeoffs",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Detail the specific sacrifices and gains when choosing one over the other.",
                            "note": "NOT_COMPUTABLE: Requires tradeoff weighting."
                        }
                    }
                ]
            },
            {
                "id": "decision_notes",
                "title": "Decision Notes",
                "kicker": "Final Thoughts",
                "blocks": [
                    {
                        "id": "conclusion",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Final synthesizing thoughts on this decision.",
                            "note": "Draft manually for now."
                        }
                    }
                ]
            },
            {
                "id": "technical_appendix",
                "title": "Technical Appendix",
                "kicker": "Calculation Trace",
                "blocks": [
                    {
                        "id": "appendix_trace",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Render the underlying evidence tables.",
                            "note": "Appendices from both records go here."
                        }
                    }
                ]
            }
        ]
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
    # For now, pass empty records to generate the scaffold context.
    record_a = {"destination_context": destination_a} if destination_a else {"destination_context": {"display_name": "Location A"}}
    record_b = {"destination_context": destination_b} if destination_b else {"destination_context": {"display_name": "Location B"}}
    return assemble_between_places_context(record_a, record_b)
