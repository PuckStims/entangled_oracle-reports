"""
Living Map report-context assembly.

This module turns a LocationEvidenceRecord into a structured draft context
for the Living Map dynamic location timing product.
"""
from __future__ import annotations

CONTEXT_VERSION = "living_map_context_v0.2.0"
REPORT_TYPE = "location_services.living_map"
PRODUCT_NAME = "Living Map"

from engine.location_services import resolve_destination_context
from engine.living_map import build_living_map_evidence, LivingMapEvidenceRecord


PLANET_WEATHER = {
    "Sun": "visibility, confidence, authorship, and the need to act from a clearer center",
    "Mercury": "conversation, planning, writing, movement, and fast adjustments",
    "Venus": "relationship, reciprocity, beauty, pleasure, and value decisions",
    "Mars": "action, friction, assertion, momentum, and the need for a clean outlet",
    "Jupiter": "growth, teaching, opportunity, generosity, and the temptation to overextend",
    "Saturn": "structure, limits, responsibility, patience, and durable work",
    "Uranus": "disruption, experimentation, freedom, and sudden changes of pattern",
    "Neptune": "imagination, sensitivity, longing, retreat, and the need for clearer edges",
    "Pluto": "depth, exposure, consequence, grief, repair, and transformation",
}

ANGLE_WEATHER = {
    "Ascendant": "body, first response, self-presentation, and how the place meets you",
    "Midheaven": "public role, work, reputation, visibility, and outward direction",
    "Descendant": "partnership, clients, direct encounters, projection, and other people",
    "Imum_Coeli": "home, privacy, roots, memory, family, and the inner base of life",
}

STRENGTH_LANGUAGE = {
    "high": "This is one of the louder windows in the scan and can be treated as a focused activation.",
    "medium": "This is a meaningful window, but it should be read alongside the static place baseline.",
    "low": "This is a lighter window; it may color the period without defining the whole experience of the place.",
}


def _window_body(window: dict) -> str:
    planet = window["active_planet"]
    target = window["target"]
    planet_theme = PLANET_WEATHER.get(planet, "a specific planetary topic")
    target_theme = ANGLE_WEATHER.get(target, "a relocated angle")
    strength = STRENGTH_LANGUAGE.get(window.get("strength"), STRENGTH_LANGUAGE["low"])
    return (
        f"From {window['start_date']} through {window['end_date']}, {planet} activates the relocated "
        f"{target}, with the closest pass on {window['exact_date']} at {window['minimum_orb']} degrees. "
        f"The temporary weather is {planet_theme} moving through {target_theme}. {strength} "
        "It does not change the permanent signature of the place; it marks a period when one part "
        "of that place becomes easier to notice, test, or manage."
    )


def _baseline_body(name: str) -> str:
    return (
        f"{name}'s living-map reading starts with the static relocated chart: the same birth moment, "
        "reframed through this destination's angles and Whole Sign houses. The timing windows below "
        "do not replace that baseline. They show when transits temporarily press on one relocated "
        "angle, making a specific part of the place louder for a limited period."
    )


def assemble_living_map_context(evidence_record: LivingMapEvidenceRecord) -> dict:
    """
    Build a structured Living Map draft context from an evidence record.
    """
    dest = evidence_record.get("destination", {})
    name = dest.get("display_name", "Destination")
    timing_windows = evidence_record.get("timing_windows", [])
    
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
                            "body": _baseline_body(name),
                            "note": "Pulls from the core relocated-place baseline."
                        }
                    }
                ]
            },
            {
                "id": "current_place_weather",
                "title": "Current Place Weather",
                "kicker": "Present Activation",
                "blocks": [
                    {
                        "id": f"weather_{window['id']}",
                        "title": f"Current: {window['active_planet']} on {window['target']}",
                        "leaf": {
                            "body": _window_body(window),
                            "note": window['temporary_weather_note']
                        },
                        "evidence": window
                    }
                    for window in timing_windows if window['exact_date'] == window['start_date'] # Simplified logic for current weather vs future window
                ]
            },
            {
                "id": "windows_of_emphasis",
                "title": "Windows Of Emphasis",
                "kicker": "When The Location Gets Loud",
                "blocks": [
                    {
                        "id": f"emphasis_{window['id']}",
                        "title": f"Upcoming: {window['active_planet']} on {window['target']}",
                        "leaf": {
                            "body": _window_body(window),
                            "note": f"Strength: {window['strength']}"
                        }
                    }
                    for window in timing_windows if window['exact_date'] != window['start_date'] # Simplified logic for current weather vs future window
                ]
            },
            {
                "id": "baseline_vs_temporary",
                "title": "What Is Baseline vs Temporary",
                "kicker": "Managing Expectations",
                "blocks": [
                    {
                        "id": "expectation_management",
                        "leaf": {
                            "body": (
                                "Baseline and weather answer different questions. Baseline asks what the place "
                                "tends to foreground whenever the chart is relocated there. Weather asks when "
                                "one of those relocated angles is temporarily activated. A strong window can be "
                                "useful for scheduling attention, recovery, conversation, visibility, or action, "
                                "but it should not be mistaken for destiny or for the whole character of the city."
                            )
                        }
                    }
                ]
            },
            {
                "id": "purpose_timing",
                "title": "Purpose Timing",
                "kicker": "Aligning Action",
                "blocks": [
                    {
                        "id": "purpose_timing_boundary",
                        "leaf": {
                            "body": (
                                "This v1 timing layer identifies transits to relocated angles. "
                                "It does not yet rank windows by purpose lens such as career, rest, "
                                "partnership, or travel strategy."
                            )
                        },
                        "unsupported_methods": evidence_record.get("unsupported_methods", [])
                    }
                ]
            },
            {
                "id": "technical_appendix",
                "title": "Technical Appendix",
                "kicker": "Calculation Trace",
                "blocks": [
                    {
                        "id": "timing_trace",
                        "leaf": {
                            "body": "Computed by scanning daily noon UTC transiting planets against relocated chart angles for the requested date range.",
                            "note": "Relocated returns and dynamic astrocartography remain excluded."
                        },
                        "trace": evidence_record.get("appendix_trace")
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
    import datetime
    start_date = datetime.date.today().isoformat()
    end_date = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    resolved_destination = resolve_destination_context(destination or {"display_name": "Location"})
    record = build_living_map_evidence(natal_payload, resolved_destination, start_date, end_date)
    return assemble_living_map_context(record)
