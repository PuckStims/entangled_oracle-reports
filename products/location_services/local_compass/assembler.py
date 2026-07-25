"""
Local Compass report-context assembly.

This module turns a LocationEvidenceRecord into a structured draft context
for the Local Compass directional interpretation product.
"""
from __future__ import annotations

CONTEXT_VERSION = "local_compass_context_v0.3.0"
REPORT_TYPE = "location_services.local_compass"
PRODUCT_NAME = "Local Compass"

from engine.location_services import resolve_destination_context
from engine.local_space import build_local_space_evidence, LocalSpaceEvidenceRecord


MODE_THEMES = {
    "Visibility": "public presence, authorship, confidence, and the choice to be seen directly",
    "Restoration": "emotional pacing, belonging, habit, and the kind of environment that lets the body settle",
    "Study": "learning, writing, errands, conversation, and the way attention moves through daily life",
    "Relationship": "contact, reciprocity, pleasure, taste, and the quality of exchange with other people",
    "Movement": "action, courage, friction, exercise, conflict, and the need for an honest outlet",
    "Expansion": "teaching, travel, opportunity, optimism, and the search for a wider field",
    "Structure": "commitment, limits, discipline, responsibility, and work that has to become durable",
    "Experimentation": "change, invention, disruption, freedom, and a break from stale patterning",
    "Retreat": "imagination, spiritual quiet, permeability, art, and the need for clearer boundaries",
    "Deep Work": "depth, repair, power, grief, consequence, and the material that cannot stay superficial",
}

DIRECTION_USES = {
    "North": "orientation, planning, and a cooler long-view posture",
    "North-Northeast": "planning that is beginning to move from idea into experiment",
    "Northeast": "study, opening, and a willingness to follow a new horizon",
    "East-Northeast": "fresh contact, early action, and the first test of a new direction",
    "East": "beginnings, visibility, initiation, and meeting the day directly",
    "East-Southeast": "momentum, conversation, and active adjustment",
    "Southeast": "creative heat, pursuit, and outward movement",
    "South-Southeast": "sustained effort, embodiment, and a warmer practical push",
    "South": "full expression, visibility, and active participation",
    "South-Southwest": "integration after effort, recovery, and sorting what has been activated",
    "Southwest": "relationship, memory, repair, and return to what needs tending",
    "West-Southwest": "release, negotiation, and making room for what is no longer central",
    "West": "encounter, reflection, exchange, and the mirror of other people",
    "West-Northwest": "discernment, closure, and the need to choose what remains useful",
    "Northwest": "structure, simplification, and mature perspective",
    "North-Northwest": "quiet preparation, containment, and a more deliberate next step",
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

PURPOSE_LENS_FRAMES = {
    "career": "Read the strongest directions as places to test visibility, contribution, structure, and working posture rather than as guarantees about success, clients, or status.",
    "belonging": "Read the strongest directions for whether they support familiarity, emotional settling, and repeatable social contact rather than for a promise that the place will automatically feel like home.",
    "rest": "Read the strongest directions for pacing, recovery, privacy, and body regulation, and notice when a loud or exposed direction may be useful but too activating for actual rest.",
    "partnership": "Read the strongest directions for encounter, reciprocity, and the style of exchange they support, not as proof that a relationship outcome will happen there.",
    "creative_visibility": "Read the strongest directions for authorship, style, attention, and public expression, while keeping the boundary that visibility is not the same thing as recognition.",
    "study": "Read the strongest directions for attention, writing, errands, learning, and signal clarity rather than expecting every useful direction to feel dramatic.",
    "retreat": "Read the strongest directions for quiet, permeability, symbolic depth, and boundary management, especially where an otherwise strong direction may still be too exposed for retreat.",
    "structure": "Read the strongest directions for discipline, responsibility, repetition, and durability, not as a claim that the place removes difficulty.",
    "experimentation": "Read the strongest directions for change, invention, novelty, and healthy disruption, while keeping one eye on what becomes unstable as well as what becomes alive.",
}


def _direction_body(direction: dict) -> str:
    mode = direction["practical_mode"]
    mode_theme = MODE_THEMES.get(mode, "a specific planetary topic")
    direction_use = DIRECTION_USES.get(direction["direction_label"], "a particular spatial emphasis")
    return (
        f"Rank {direction['rank']} brings {direction['body']} forward as a {mode.lower()} direction, "
        f"pointing {direction['direction_label']} from the anchor. That direction is useful for "
        f"{direction_use}, while the planetary mode emphasizes {mode_theme}. The score "
        f"({direction['weighted_score']}) describes relative strength inside this compass, not a "
        "command to face that direction for every decision."
    )


def _relationship_body(direction: dict) -> str:
    cross_track = direction.get("cross_track_distance_km")
    bearing = direction.get("bearing_to_destination")
    if cross_track is None or bearing is None:
        return (
            f"No destination bearing was available for {direction['body']}; the report can "
            "still use the raw local-space direction, but cannot compare it to a route or place."
        )
    alignment = (
        "very close to"
        if cross_track <= 100
        else "near"
        if cross_track <= 500
        else "well away from"
    )
    return (
        f"The destination bearing is {bearing} degrees, and the {direction['body']} direction runs "
        f"{alignment} that bearing at about {cross_track} km of cross-track distance. This says whether "
        "the place itself participates in the planetary direction, not whether the destination will "
        "deliver the planet's desired outcome."
    )


def _route_body(direction: dict) -> str:
    route_geometry = direction.get("route_geometry") or {}
    strength = route_geometry.get("strength")
    route_read = {
        "high": "The route repeatedly stays inside this planetary corridor.",
        "medium": "The route intersects the corridor enough to matter, but not enough to define the whole path.",
        "low": "The route only brushes the corridor; treat it as context, not the route's main signature.",
    }.get(strength, "The route relationship is present but should be read cautiously.")
    return (
        f"The route comes within about {route_geometry.get('minimum_offset_km')} km of the "
        f"{direction['body']} directional ray, with roughly {route_geometry.get('overlap_length_km')} km "
        f"inside the defined corridor. {route_read} This is geometric alignment, not travel advice "
        "or a promise about what will happen on the path."
    )


def _signature_body(name: str, directions: list[dict]) -> str:
    if not directions:
        return "No planetary local-space directions were available for this anchor."
    lead = directions[0]
    mode_theme = MODE_THEMES.get(lead["practical_mode"], "a specific planetary topic")
    direction_use = DIRECTION_USES.get(lead["direction_label"], "a particular spatial emphasis")
    return (
        f"{name}'s strongest compass signal is {lead['body']} toward {lead['direction_label']}. "
        f"That points the reading toward {mode_theme}, carried through {direction_use}. "
        "The compass is not choosing a destination for the reader; it is showing which planetary "
        "topic has the clearest directional handle from this anchor."
    )


def _purpose_frame_body(purpose_lens: str) -> str:
    label = PURPOSE_LENS_LABELS.get(purpose_lens, purpose_lens.replace("_", " ").title())
    frame = PURPOSE_LENS_FRAMES.get(
        purpose_lens,
        "Use the stated purpose to decide which directional themes deserve closer attention, without turning the compass into a promise engine."
    )
    return f"The active lens for this reading is {label}. {frame}"


def _scope_body(anchor_name: str, destination_name: str | None, route_context: dict) -> str:
    if destination_name and destination_name != anchor_name:
        return (
            f"The anchor for this compass is {anchor_name}, and the destination comparison is {destination_name}. "
            "Read the ranked directions first as rays extending from the anchor, then use the destination relationship "
            "section to see whether the compared place actually sits near one of those rays."
        )
    if route_context:
        return (
            f"The compass is anchored at {anchor_name}. No separate destination comparison was supplied, so the report is "
            "reading directional strength from the anchor itself and, where route geometry exists, whether the supplied path "
            "stays close to those rays."
        )
    return (
        f"The compass is anchored at {anchor_name} with no separate destination comparison. "
        "Read the directions as a spatial orientation layer for movement, ritual, workspace, pacing, or attention from that anchor."
    )


def assemble_local_compass_context(evidence_record: LocalSpaceEvidenceRecord) -> dict:
    """
    Build a structured Local Compass draft context from an evidence record.
    """
    dest = evidence_record.get("destination_context", {})
    anchor = evidence_record.get("anchor_context", {})
    name = dest.get("display_name") or anchor.get("display_name", "Anchor")
    directions = evidence_record.get("directions", [])
    route_context = evidence_record.get("route_context", {})
    has_route_geometry = any(direction.get("route_geometry") for direction in directions)
    sections = [
            {
                "id": "directional_signature",
                "title": "Directional Signature",
                "kicker": "Core Compass Alignment",
                "blocks": [
                    {
                        "id": "directional_signature_computed",
                        "leaf": {
                            "body": _signature_body(name, directions)
                        }
                    }
                ]
            },
            {
                "id": "planetary_directions",
                "title": "Planetary Directions",
                "kicker": "Lines of Force",
                "blocks": [
                    {
                        "id": f"direction_{direction['id']}",
                        "title": f"{direction['body']} towards {direction['direction_label']}",
                        "leaf": {
                            "body": _direction_body(direction),
                            "note": f"Mode: {direction['practical_mode']}; score {direction['weighted_score']}"
                        },
                        "evidence": direction
                    }
                    for direction in directions
                ]
            },
            {
                "id": "destination_relationship",
                "title": "Destination Relationship",
                "kicker": "Geographic Connection",
                "blocks": [
                    {
                        "id": f"relationship_{direction['id']}",
                        "title": f"Distance to {direction['body']}",
                        "leaf": {
                            "body": _relationship_body(direction),
                            "note": f"Distance metric for {direction['body']}"
                        }
                    }
                    for direction in directions
                ]
            },
            {
                "id": "use_modes",
                "title": "Use Modes",
                "kicker": "Practical Application",
                "blocks": [
                    {
                        "id": "feng_shui",
                        "leaf": {
                            "body": (
                                "Use these directions as a practical layer after the main locational question is clear. "
                                "A strong direction can support where to place attention, movement, ritual, study, "
                                "conversation, or recovery inside an environment. It should not replace ordinary "
                                "judgment about safety, logistics, accessibility, or the real purpose of the trip."
                            ),
                            "note": "Route-corridor geometry is geometric alignment evidence, not travel advice."
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
                            "body": "Computed with Swiss Ephemeris equatorial positions projected to local horizon azimuths at the anchor place.",
                            "note": "Computed local-space azimuth, direction-strength weighting, and optional route-corridor geometry are available."
                        },
                        "trace": evidence_record.get("appendix_trace")
                    }
                ]
            },
        ]

    if has_route_geometry:
        sections.insert(3, {
            "id": "route_relationship",
            "title": "Route Relationship",
            "kicker": "Path Corridor Alignment",
            "present": True,
            "blocks": [
                {
                    "id": f"route_{direction['id']}",
                    "title": f"Route alignment for {direction['body']}",
                    "leaf": {
                        "body": _route_body(direction),
                        "note": (
                            f"Route {direction['route_geometry']['route_id']}; "
                            f"strength {direction['route_geometry']['strength']}"
                        ),
                    },
                    "evidence": direction["route_geometry"],
                }
                for direction in directions
                if direction.get("route_geometry")
            ],
            "route_context": route_context,
        })

    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "destination_name": name,
        "destination_context": dest,
        "sections": sections,
    }

def build_local_compass_context(
    natal_payload: dict,
    anchor: dict,
    *,
    destination: dict | None = None,
    route: dict | None = None,
    purpose_lens: str | None = None,
) -> dict:
    """
    Evidence-record wrapper seam for Local Compass.
    """
    route = route or (anchor or {}).get("route")
    resolved_anchor = resolve_destination_context(anchor or {"display_name": "Anchor"})
    resolved_destination = resolve_destination_context(destination) if destination else None
    record = build_local_space_evidence(
        natal_payload,
        resolved_anchor,
        resolved_destination,
        route=route,
    )
    context = assemble_local_compass_context(record)
    if not destination:
        context["destination_context"] = dict(resolved_anchor)
        context["destination_name"] = resolved_anchor.get("display_name", "Anchor")
    context["anchor_context"] = resolved_anchor
    context["anchor_name"] = resolved_anchor.get("display_name", "Anchor")
    context["purpose_lens"] = purpose_lens
    context["purpose_lens_label"] = PURPOSE_LENS_LABELS.get(
        purpose_lens or "",
        purpose_lens.replace("_", " ").title() if purpose_lens else "",
    )
    context["route_context"] = dict(route or {})
    framing_blocks = []
    if purpose_lens:
        framing_blocks.append(
            {
                "id": "purpose_frame",
                "title": "Purpose frame",
                "leaf": {
                    "body": _purpose_frame_body(purpose_lens),
                    "note": "A reading frame, not a fit taxonomy."
                },
            }
        )
    framing_blocks.append(
        {
            "id": "scope_frame",
            "title": "Compass scope",
            "leaf": {
                "body": _scope_body(
                    context["anchor_name"],
                    context.get("destination_name"),
                    context["route_context"],
                ),
                "note": "Anchor, destination, and route are separate inputs in this product."
            },
        }
    )
    context["sections"].insert(
        1,
        {
            "id": "reading_frame",
            "title": "Reading Frame",
            "kicker": "How To Use This Surface",
            "blocks": framing_blocks,
        },
    )
    return context
