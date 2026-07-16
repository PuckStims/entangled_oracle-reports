"""
World Lines Companion report-context assembly.

This module turns a LocationEvidenceRecord into a structured draft context
for the World Lines Companion product.
"""
from __future__ import annotations

CONTEXT_VERSION = "world_lines_context_v0.2.0"
REPORT_TYPE = "location_services.world_lines"
PRODUCT_NAME = "World Lines Companion"

from engine.location_services import resolve_destination_context
from engine.world_lines import build_line_evidence, WorldLinesEvidenceRecord


ANGLE_DESCRIPTIONS = {
    "Ascendant": "how a place meets your body, visibility, and immediate self-presentation",
    "Descendant": "how a place draws partnership, clients, mirrors, and other people into focus",
    "Midheaven": "how a place speaks to public life, vocation, reputation, and outward direction",
    "Imum_Coeli": "how a place touches privacy, home, roots, memory, and inner steadiness",
}

BODY_THEMES = {
    "Sun": "direction, authorship, confidence, and the question of being visibly yourself",
    "Moon": "emotional rhythm, belonging, memory, and the conditions that help life feel habitable",
    "Mercury": "language, movement, study, negotiation, and the everyday nervous system",
    "Venus": "relationship, taste, reciprocity, pleasure, and the way value becomes visible",
    "Mars": "drive, conflict, assertion, stamina, and the need for clean outlets",
    "Jupiter": "growth, opportunity, teaching, generosity, and the sense of a larger horizon",
    "Saturn": "structure, responsibility, limits, craft, and the pressure to make something durable",
    "Uranus": "freedom, disruption, experimentation, and the need to break stale patterns",
    "Neptune": "imagination, permeability, longing, retreat, and the risk of losing definition",
    "Pluto": "depth, consequence, exposure, power, grief, and real transformation",
}

ANGLE_ACTIONS = {
    "Ascendant": "meets you through body, first response, visibility, and the way you enter the environment",
    "Descendant": "arrives through other people: partners, clients, open mirrors, and direct encounters",
    "Midheaven": "moves through public life, reputation, vocation, responsibility, and contribution",
    "Imum_Coeli": "works through home, privacy, roots, memory, and the ground under the public self",
}

BAND_LANGUAGE = {
    "tight": "This is close enough to treat as one of the location's lead line signals.",
    "moderate": "This is not the loudest possible contact, but it is close enough to matter when the same theme repeats elsewhere.",
    "wide": "This is a real but softer contact; it should color the reading rather than carry the whole interpretation.",
    "background": "This is background context. It may help explain the field, but it should not be treated as a primary reason to choose the place.",
}

BOUNDARY_LANGUAGE = (
    "The line is evidence of spatial emphasis, not a promise that an event has to occur.",
    "Use it as map context rather than a guaranteed outcome.",
    "Keep the claim bounded: the line describes where planetary material gets louder, not what life must deliver.",
)


def _line_body(line: dict, index: int = 0) -> str:
    body = line["body"]
    angle = line["angle"]
    theme = BODY_THEMES.get(body, "a specific planetary topic")
    angle_action = ANGLE_ACTIONS.get(angle, "shows up through a specific angular channel")
    band_text = BAND_LANGUAGE.get(line.get("strength_band"), BAND_LANGUAGE["background"])
    boundary_text = BOUNDARY_LANGUAGE[index % len(BOUNDARY_LANGUAGE)]
    distance_km = line["distance_km"]

    if index % 3 == 0:
        opening = f"The nearest {body} {angle} line sits about {distance_km} km from this destination."
        meaning = (
            f"In this place, {body} themes - {theme} - are most likely to be noticed where the "
            f"{angle} {angle_action}."
        )
    elif index % 3 == 1:
        opening = f"At about {distance_km} km from the destination, the closest {body} {angle} line is a supporting map signal."
        meaning = (
            f"It points {body}'s material - {theme} - toward the {angle}, where it {angle_action}."
        )
    else:
        opening = f"{body} on the {angle} is part of the nearby line field, with its nearest point about {distance_km} km away."
        meaning = (
            f"The practical reading is to watch for {theme} through the angular channel of the {angle}, which "
            f"{angle_action}."
        )

    return f"{opening} {meaning} {band_text} {boundary_text}"


def _natal_context_body(line: dict) -> str:
    condition = line.get("natal_condition") or {}
    sign = condition.get("natal_sign") or "its natal sign"
    house = condition.get("natal_house")
    house_text = f" and house {house}" if house else ""
    theme = BODY_THEMES.get(line["body"], "this planetary function")
    return (
        f"{line['body']} still comes from the natal chart through {sign}{house_text}. "
        f"The location can foreground {theme}, but it does not improve, erase, or rewrite "
        "the natal pattern. Read the line as emphasis, then let natal condition describe "
        "how easy or demanding that material is to live."
    )


def _distance_body(line: dict) -> str:
    band_text = BAND_LANGUAGE.get(line.get("strength_band"), BAND_LANGUAGE["background"])
    return (
        f"The nearest point is {line['distance_km']} km from the destination, with "
        f"{line['birth_time_sensitivity']} birth-time sensitivity for this angle. {band_text} "
        "If birth time confidence is lower, keep the interpretation quieter; the same line "
        "can remain useful context without becoming a decisive relocation claim."
    )


def _map_summary_body(name: str, lines: list[dict]) -> str:
    if not lines:
        return "No angular line proximity signals were available for this destination."
    lead = lines[0]
    lead_theme = BODY_THEMES.get(lead["body"], "a planetary topic")
    return (
        f"{name} is organized first around {lead['body']} on the {lead['angle']}: "
        f"{lead_theme}. The report includes {len(lines)} nearby ASC, DSC, MC, and IC "
        "line signals, but the nearest line sets the first interpretive question rather "
        "than declaring this place good or bad."
    )


def assemble_world_lines_context(evidence_record: WorldLinesEvidenceRecord) -> dict:
    """
    Build a structured World Lines draft context from an evidence record.
    """
    dest = evidence_record.get("destination", {})
    name = dest.get("display_name", "Destination")
    lines = evidence_record.get("lines", [])
    
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
                "blocks": [
                    {
                        "id": "map_summary_computed",
                        "leaf": {
                            "body": _map_summary_body(name, lines)
                        }
                    }
                ]
            },
            {
                "id": "closest_lines",
                "title": "Closest Lines",
                "kicker": "Primary Planetary Influence",
                "blocks": [
                    {
                        "id": f"line_{line['id']}",
                        "title": f"{line['body']} on the {line['angle']}",
                        "leaf": {
                            "body": _line_body(line, index),
                            "note": f"Distance: {line['distance_km']} km ({line['strength_band']})"
                        },
                        "evidence": line
                    }
                    for index, line in enumerate(lines)
                ]
            },
            {
                "id": "angle_meaning",
                "title": "Angle Meaning",
                "kicker": "The Four Angles",
                "blocks": [
                    {
                        "id": f"angle_meaning_{angle}",
                        "title": angle.replace("_", " "),
                        "leaf": {
                            "body": (
                                f"{angle.replace('_', ' ')} lines describe "
                                f"{ANGLE_DESCRIPTIONS.get(angle, 'a specific form of angular emphasis')}."
                            )
                        }
                    }
                    for angle in sorted({line["angle"] for line in lines})
                ]
            },
            {
                "id": "natal_context",
                "title": "Natal Context",
                "kicker": "Your Blueprint",
                "blocks": [
                    {
                        "id": f"natal_integration_{line['id']}",
                        "title": f"How You Carry {line['body']}",
                        "leaf": {
                            "body": _natal_context_body(line)
                        }
                    }
                    for line in lines
                ]
            },
            {
                "id": "distance_and_uncertainty",
                "title": "Distance and Uncertainty",
                "kicker": "Precision Metrics",
                "blocks": [
                    {
                        "id": f"distance_metrics_{line['id']}",
                        "leaf": {
                            "body": _distance_body(line)
                        }
                    }
                    for line in lines
                ]
            },
            {
                "id": "line_clusters",
                "title": "Calculation Boundaries",
                "kicker": "Unsupported Advanced Methods",
                "blocks": [
                    {
                        "id": "unsupported_world_lines_methods",
                        "leaf": {
                            "body": (
                                "This report includes planetary ASC, DSC, MC, and IC line proximity. "
                                "It does not yet include parans, remote activation, or line-crossing interpretation."
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
                        "id": "astrocartography_trace",
                        "leaf": {
                            "body": "Computed with Swiss Ephemeris equatorial positions, meridian longitudes, and sampled horizon curves.",
                            "note": "Parans, crossings, and remote activation remain excluded."
                        },
                        "trace": evidence_record.get("appendix_trace")
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
    resolved_destination = resolve_destination_context(destination or {"display_name": "Location"})
    record = build_line_evidence(natal_payload, resolved_destination)
    return assemble_world_lines_context(record)
