"""
Local Compass report-context assembly.

This module turns a LocationEvidenceRecord into a structured draft context
for the Local Compass directional interpretation product.
"""
from __future__ import annotations

CONTEXT_VERSION = "local_compass_context_v0.2.0"
REPORT_TYPE = "location_services.local_compass"
PRODUCT_NAME = "Local Compass"

def assemble_local_compass_context(evidence_record: dict) -> dict:
    """
    Build a structured Local Compass draft context from an evidence record.
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
                "id": "directional_signature",
                "title": "Directional Signature",
                "kicker": "Core Compass Alignment",
                "is_future_method": True,
                "future_title": "Local Space Signature (Coming Soon)",
                "future_description": "Our upcoming engine will convert planetary positions into 360-degree horizon azimuths relative to your current location.",
                "blocks": []
            },
            {
                "id": "planetary_directions",
                "title": "Planetary Directions",
                "kicker": "Lines of Force",
                "is_future_method": True,
                "future_title": "Azimuth Mapping (Coming Soon)",
                "future_description": "Maps which planets pull in which geographic directions—e.g. Venus lines for aesthetic quarters, Mars for high-energy zones.",
                "blocks": []
            },
            {
                "id": "destination_relationship",
                "title": "Destination Relationship",
                "kicker": "Geographic Connection",
                "is_future_method": True,
                "future_title": "City-to-City Vectors (Coming Soon)",
                "future_description": "Calculates exactly which planetary line connects your current location to the target destination.",
                "blocks": []
            },
            {
                "id": "use_modes",
                "title": "Use Modes",
                "kicker": "Practical Application",
                "blocks": [
                    {
                        "id": "feng_shui",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Suggest how to arrange a room or travel routes based on these directional lines.",
                            "note": "Awaiting azimuth data."
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
                        "id": "compass_trace",
                        "leaf": {
                            "is_draft": True,
                            "draft_prompt": "Display raw azimuths and zenith data.",
                            "note": "Awaiting local space layer."
                        }
                    }
                ]
            }
        ]
    }

def build_local_compass_context(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None
) -> dict:
    """
    Evidence-record wrapper seam for Local Compass.
    """
    record = {"destination_context": destination} if destination else {"destination_context": {"display_name": "Location"}}
    return assemble_local_compass_context(record)
