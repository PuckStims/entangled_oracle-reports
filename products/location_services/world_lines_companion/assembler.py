"""
World Lines Companion report-context assembly.

This module turns a LocationEvidenceRecord into a structured draft context
for the World Lines Companion product.
"""
from __future__ import annotations

CONTEXT_VERSION = "world_lines_context_v0.2.0"
REPORT_TYPE = "location_services.world_lines"
PRODUCT_NAME = "World Lines Companion"

def assemble_world_lines_context(evidence_record: dict) -> dict:
    """
    Build a structured World Lines draft context from an evidence record.
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
                "id": "map_summary",
                "title": "Map Summary",
                "kicker": "Astrocartography Overview",
                "is_future_method": True,
                "future_title": "Astrocartography Baseline (Coming Soon)",
                "future_description": "Our upcoming spatial engine will calculate precise planetary line distances and intersections at this exact longitude and latitude.",
                "blocks": []
            },
            {
                "id": "closest_lines",
                "title": "Closest Lines",
                "kicker": "Primary Planetary Influence",
                "is_future_method": True,
                "future_title": "Line Detection (Coming Soon)",
                "future_description": "Identifies the closest planetary lines (within 500km) to this location, highlighting their core themes.",
                "blocks": []
            },
            {
                "id": "angle_meaning",
                "title": "Angle Meaning",
                "kicker": "The Four Angles",
                "is_future_method": True,
                "future_title": "Angular Expression (Coming Soon)",
                "future_description": "Analyzes how lines on the Ascendant, Midheaven, Descendant, and IC differ in their worldly expression.",
                "blocks": []
            },
            {
                "id": "natal_context",
                "title": "Natal Context",
                "kicker": "Your Blueprint",
                "blocks": [
                    {
                        "id": "natal_integration",
                        "title": "How You Carry These Lines",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Explain how the natal condition of the line's planet modifies the map's raw promise.",
                            "note": "Requires the planet identification from the astrocartography layer."
                        }
                    }
                ]
            },
            {
                "id": "distance_and_uncertainty",
                "title": "Distance and Uncertainty",
                "kicker": "Precision Metrics",
                "is_future_method": True,
                "future_title": "Orb Calculation (Coming Soon)",
                "future_description": "Calculates the exact orb and distance attenuation of the planetary lines to determine their relative strength.",
                "blocks": []
            },
            {
                "id": "line_clusters",
                "title": "Line Clusters",
                "kicker": "Complex Intersections",
                "is_future_method": True,
                "future_title": "Parans & Crossings (Coming Soon)",
                "future_description": "Identifies localized line crossings, parans, and complex multi-planetary signatures unique to this latitude.",
                "blocks": []
            },
            {
                "id": "technical_appendix",
                "title": "Technical Appendix",
                "kicker": "Calculation Trace",
                "blocks": [
                    {
                        "id": "astrocartography_trace",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Show calculation boundaries and method references.",
                            "note": "Awaiting geometry layer."
                        }
                    }
                ]
            }
        ]
    }

def build_world_lines_context(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None
) -> dict:
    """
    Evidence-record wrapper seam for World Lines Companion.
    """
    # For now, pass empty record with destination info.
    record = {"destination_context": destination} if destination else {"destination_context": {"display_name": "Location"}}
    return assemble_world_lines_context(record)
