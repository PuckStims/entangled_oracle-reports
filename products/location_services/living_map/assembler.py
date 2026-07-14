"""
Living Map report-context assembly.

This module turns a LocationEvidenceRecord into a structured draft context
for the Living Map dynamic location timing product.
"""
from __future__ import annotations

CONTEXT_VERSION = "living_map_context_v0.2.0"
REPORT_TYPE = "location_services.living_map"
PRODUCT_NAME = "Living Map"

def assemble_living_map_context(evidence_record: dict) -> dict:
    """
    Build a structured Living Map draft context from an evidence record.
    """
    dest = evidence_record.get("destination_context", {})
    name = dest.get("display_name", "Destination")
    
    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "destination_name": name,
        "destination_context": dest,
        "sections": [
            {
                "id": "static_place_baseline",
                "title": "Static Place Baseline",
                "kicker": "The Underlying Promise",
                "blocks": [
                    {
                        "id": "baseline_summary",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "What does this location offer unconditionally, regardless of timing?",
                            "note": "Pulls from the core Place Resonance structural shift."
                        }
                    }
                ]
            },
            {
                "id": "current_place_weather",
                "title": "Current Place Weather",
                "kicker": "Present Activation",
                "is_future_method": True,
                "future_title": "Active Timing Layers (Coming Soon)",
                "future_description": "Our upcoming temporal engine will calculate exactly which relocated angles and planets are being activated by current transits and profections.",
                "blocks": []
            },
            {
                "id": "windows_of_emphasis",
                "title": "Windows Of Emphasis",
                "kicker": "When The Location Gets Loud",
                "is_future_method": True,
                "future_title": "Timing Windows (Coming Soon)",
                "future_description": "Calculates future periods where the unique promise of this location is heavily emphasized or challenged.",
                "blocks": []
            },
            {
                "id": "baseline_vs_temporary",
                "title": "What Is Baseline vs Temporary",
                "kicker": "Managing Expectations",
                "blocks": [
                    {
                        "id": "expectation_management",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Remind the user not to confuse a temporary transit with a permanent locational feature.",
                            "note": "Draft manually for now."
                        }
                    }
                ]
            },
            {
                "id": "purpose_timing",
                "title": "Purpose Timing",
                "kicker": "Aligning Action",
                "is_future_method": True,
                "future_title": "Strategic Lenses (Coming Soon)",
                "future_description": "Identifies the best timing for specific purposes (Career, Rest, Partnership) at this specific location.",
                "blocks": []
            },
            {
                "id": "technical_appendix",
                "title": "Technical Appendix",
                "kicker": "Calculation Trace",
                "blocks": [
                    {
                        "id": "timing_trace",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "List the transits/profections hitting relocated angles.",
                            "note": "Awaiting temporal engine."
                        }
                    }
                ]
            }
        ]
    }

def build_living_map_context(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None
) -> dict:
    """
    Evidence-record wrapper seam for Living Map.
    """
    record = {"destination_context": destination} if destination else {"destination_context": {"display_name": "Location"}}
    return assemble_living_map_context(record)
