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

PURPOSE_LENS_TIMING_FRAMES = {
    "career": "Use the timing layer to notice when public role, work pressure, structure, and outward participation become louder at the place, without collapsing those windows into success promises.",
    "belonging": "Use the timing layer to notice when home, support, or social reciprocity feels easier to test, while keeping the distinction between temporary weather and enduring fit.",
    "rest": "Use the timing layer to notice when the place feels calmer, more exposed, or more demanding on the nervous system, rather than assuming every active window is useful for restoration.",
    "partnership": "Use the timing layer to notice when encounters, direct contact, and reciprocity become louder, not as a guarantee that the place will produce a relationship event.",
    "creative_visibility": "Use the timing layer to notice when authorship, display, confidence, and audience contact are emphasized, while remembering that visibility and recognition are not identical.",
    "study": "Use the timing layer to notice when focus, writing, conversation, and information flow are easier to work with at the place.",
    "retreat": "Use the timing layer to notice when the place supports quiet, reflection, and symbolic depth, and when a louder window may work against retreat even if it is astrologically strong.",
    "structure": "Use the timing layer to notice when discipline, limits, and durable work are easier to organize, not as proof that the window will feel easy.",
    "experimentation": "Use the timing layer to notice when novelty, motion, and productive disruption come forward at the place, while keeping an eye on volatility.",
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


def _purpose_timing_frame_body(purpose_lens: str, start_date: str, end_date: str) -> str:
    label = PURPOSE_LENS_LABELS.get(purpose_lens, purpose_lens.replace("_", " ").title())
    frame = PURPOSE_LENS_TIMING_FRAMES.get(
        purpose_lens,
        "Use the stated purpose to decide which temporary windows deserve attention, without treating the timing layer as a fit score."
    )
    return f"The active lens for this reading is {label}, over the window from {start_date} through {end_date}. {frame}"


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
    purpose_lens: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Evidence-record wrapper seam for Living Map.
    """
    import datetime

    start_date = start_date or datetime.date.today().isoformat()
    end_date = end_date or (datetime.date.fromisoformat(start_date) + datetime.timedelta(days=365)).isoformat()
    resolved_destination = resolve_destination_context(destination or {"display_name": "Location"})
    record = build_living_map_evidence(natal_payload, resolved_destination, start_date, end_date)
    context = assemble_living_map_context(record)
    context["purpose_lens"] = purpose_lens
    context["purpose_lens_label"] = PURPOSE_LENS_LABELS.get(
        purpose_lens or "",
        purpose_lens.replace("_", " ").title() if purpose_lens else "",
    )
    context["date_range"] = {"start_date": start_date, "end_date": end_date}
    framing_blocks = [
        {
            "id": "window_scope",
            "title": "Window scope",
            "leaf": {
                "body": (
                    f"This scan covers {start_date} through {end_date}. Treat the listed windows as temporary pressure on the place baseline, "
                    "not as a replacement for the place's longer-lived signature."
                ),
                "note": "Date range is part of the report contract for Living Map."
            },
        }
    ]
    if purpose_lens:
        framing_blocks.insert(
            0,
            {
                "id": "purpose_timing_frame",
                "title": "Purpose frame",
                "leaf": {
                    "body": _purpose_timing_frame_body(purpose_lens, start_date, end_date),
                    "note": "Purpose lens is a reading frame; window ranking is not yet purpose-weighted."
                },
            },
        )
    context["sections"].insert(
        1,
        {
            "id": "timing_frame",
            "title": "Timing Frame",
            "kicker": "How To Read The Window",
            "blocks": framing_blocks,
        },
    )
    return context
