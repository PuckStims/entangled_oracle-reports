"""
engine/location_services.py — Entangled Oracle Location Services

Minimal, non-reporting relocated-chart helper. This is the shared
computational seam Place Resonance and the rest of the Location Services
product family build on (see products/location_services/ASYNC_WORKSTREAMS.md).

A place does not rewrite the natal chart. Relocation preserves the birth
UTC instant / Julian Day exactly and recalculates only what genuinely
depends on where on Earth the chart is read from: the angles (Ascendant,
Midheaven, Descendant, Imum Coeli, Vertex) and the Whole Sign houses those
angles generate. Planetary longitudes do not change with location, so
existing natal bodies are reassigned into their new houses rather than
recomputed from the ephemeris.

Natal planetary condition (dignity, sect, essential/accidental strength) is
never recomputed against a relocated payload. Sect in particular is
determined from the Ascendant/Descendant horizon axis (see
formulas/standard/sect.py), which genuinely rotates with location at a
fixed UTC instant — running condition formulas against a relocated payload
could silently disagree with the natal chart's actual sect. Relocation is
only allowed to touch angularity (house placement, angle contacts), never
condition. See products/location_services/CAPABILITY_INVENTORY.md for the
full audit this module was built against.
"""
from __future__ import annotations

import copy
import hashlib
import re
from datetime import datetime
from typing import Any

import swisseph as swe

from engine.natal_engine import (
    ChartCalculationError,
    build_angle_data,
    generate_whole_sign_houses,
    whole_sign_house,
)
from engine.offline_place_resolver import (
    LocationResolutionError,
    resolve_place,
)
from formulas.standard.angularity import HOUSE_TYPES, evaluate_angularity
from formulas.standard.planetary_condition import evaluate_all_planetary_conditions

FORMULA_VERSION = "location_services_v0.1.0"
EVIDENCE_RECORD_FORMULA_VERSION = "location_evidence_record_v0.1.0"

# Orb ceilings for relocated angle-contact strength bands, in degrees.
# The outer ceiling (8.0) matches evaluate_angularity's own default
# angle_orb -- any contact evaluate_angularity flags as conjunct is
# guaranteed to fall inside one of these bands, none are ever "unbanded."
CONTACT_STRENGTH_BANDS = (
    ("tight", 2.0),
    ("moderate", 5.0),
    ("wide", 8.0),
)

# Angles are location-sensitive; a natal aspect involving one of these is
# stale under relocation and is excluded rather than copied through.
_ANGLE_LINKED_BODY_NAMES = frozenset(
    {"Ascendant", "Descendant", "Midheaven", "Imum_Coeli", "Vertex"}
)

# Explicitly not implemented yet. Surfaced on every comparison so callers
# and content authors never have to guess what this seam can't do.
UNSUPPORTED_METHODS = (
    "astrocartography",
    "local_space",
    "parans",
    "relocated_returns",
)

LOCATION_EVIDENCE_BODY_GROUPS = ("standard_planets",)
CORE_CONDITION_BODIES = frozenset(
    {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
)


# ── Internal helpers ────────────────────────────────────────────

def _get_julian_day(natal_payload: dict) -> float | None:
    profile = natal_payload.get("user_profile") or {}
    julian_day = profile.get("julian_day") if isinstance(profile, dict) else None
    if isinstance(julian_day, (int, float)):
        return float(julian_day)
    return None


def _destination_coordinates(destination: dict) -> tuple[float, float] | None:
    try:
        latitude = float(destination["latitude"])
        longitude = float(destination["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    return latitude, longitude


def _resolve_destination(destination: dict) -> dict:
    """
    Normalizes a destination into a dict carrying numeric latitude/longitude.

    Accepts either pre-resolved coordinates or a bare place-name string
    under "location" (or "display_name"), reusing the same offline
    resolver natal charts use. Does not mutate the caller's dict. Never
    falls back to an online lookup — see CAPABILITY_INVENTORY.md §4 for why.
    """
    destination = dict(destination)

    if _destination_coordinates(destination) is not None:
        destination.setdefault("coordinate_source", "user_provided")
        return destination

    location_name = destination.get("location") or destination.get("display_name")
    if not location_name:
        raise ValueError(
            "destination requires numeric latitude/longitude, or a "
            "'location' place name to resolve offline."
        )

    try:
        resolved = resolve_place(str(location_name))
    except LocationResolutionError as exc:
        raise ValueError(
            f"Could not resolve destination \"{location_name}\": {exc}"
        ) from exc

    destination.setdefault("display_name", resolved["display_name"])
    destination.setdefault("timezone", resolved["timezone"])
    destination["latitude"] = resolved["latitude"]
    destination["longitude"] = resolved["longitude"]
    destination["coordinate_source"] = resolved.get("source", "offline_geonamescache")
    return destination


def _relocated_angle_longitudes(julian_day: float, latitude: float, longitude: float) -> dict[str, float]:
    """
    Recomputes Ascendant/Midheaven/Vertex for a destination at the same
    Julian Day used for the natal chart. Mirrors engine.natal_engine's
    Placidus -> Porphyry fallback (natal_engine.py:435-446): only ascmc
    (the angles) is ever used, never house cusps, so Porphyry is a safe
    fallback inside the polar circles where Placidus is degenerate.
    """
    try:
        _cusps, ascmc = swe.houses(julian_day, latitude, longitude, b"P")
    except swe.Error:
        try:
            _cusps, ascmc = swe.houses(julian_day, latitude, longitude, b"O")
        except swe.Error as exc:
            raise ChartCalculationError(
                f"Could not calculate relocated chart angles for latitude "
                f"{latitude}°. Extreme polar latitudes can fall outside "
                f"what the house-angle calculation supports. "
                f"Original error: {exc}"
            ) from exc

    ascendant = ascmc[0]
    midheaven = ascmc[1]
    vertex = ascmc[3]

    return {
        "Ascendant": ascendant,
        "Midheaven": midheaven,
        "Vertex": vertex,
        "Descendant": (ascendant + 180) % 360,
        "Imum_Coeli": (midheaven + 180) % 360,
    }


def _reassign_bodies(natal_bodies: dict, relocated_ascendant: float) -> dict[str, Any]:
    """
    Copies each body's longitude/speed/sign as-is and recalculates only its
    Whole Sign house under the relocated Ascendant. Deep-copies every
    record so the returned structure shares no mutable state with the
    natal payload.
    """
    reassigned: dict[str, Any] = {}
    for name, data in (natal_bodies or {}).items():
        if not isinstance(data, dict) or not isinstance(data.get("longitude"), (int, float)):
            reassigned[name] = copy.deepcopy(data)
            continue
        body_copy = copy.deepcopy(data)
        body_copy["house"] = whole_sign_house(data["longitude"], relocated_ascendant)
        reassigned[name] = body_copy
    return reassigned


def _filter_angle_linked_aspects(aspects: list, warnings: list[str]) -> list:
    kept = []
    excluded_count = 0
    for aspect in aspects or []:
        if not isinstance(aspect, dict):
            continue
        if aspect.get("body_1") in _ANGLE_LINKED_BODY_NAMES or aspect.get("body_2") in _ANGLE_LINKED_BODY_NAMES:
            excluded_count += 1
            continue
        kept.append(copy.deepcopy(aspect))

    if excluded_count:
        warnings.append(
            f"{excluded_count} natal aspect(s) involving an angle (Ascendant/Descendant/"
            "Midheaven/Imum_Coeli/Vertex) were excluded from the relocated payload's aspect "
            "list because those angles move under relocation. See relocated_angle_contacts "
            "from compare_natal_to_relocated() for the relocated equivalents."
        )

    return kept


# ── Public API ──────────────────────────────────────────────────

def build_relocated_payload(natal_payload: dict, destination: dict) -> dict:
    """
    Builds a relocated chart baseline from an existing natal payload and a
    destination place: same sky, same UTC instant, new angles and houses.

    Requirements enforced here:
    - natal_payload is never mutated.
    - The birth UTC instant / Julian Day is carried through unchanged.
    - Angles are recalculated for the destination coordinates.
    - Whole Sign houses are regenerated from the relocated Ascendant.
    - Existing natal body longitudes are reassigned into relocated houses,
      not recomputed from the ephemeris.
    - Natal condition (dignity/sect/overall condition score) is not
      recomputed here; only house placement changes.
    """
    if not isinstance(natal_payload, dict) or not natal_payload:
        raise ValueError("A natal payload is required to build a relocated chart.")

    julian_day = _get_julian_day(natal_payload)
    if julian_day is None:
        raise ValueError(
            "natal_payload.user_profile.julian_day is required to preserve the "
            "birth UTC instant during relocation."
        )

    if not isinstance(destination, dict) or not destination:
        raise ValueError("A destination with latitude/longitude (or a resolvable location name) is required.")

    destination = _resolve_destination(destination)
    latitude, longitude = _destination_coordinates(destination)

    warnings: list[str] = []

    if not destination.get("timezone"):
        warnings.append(
            "destination.timezone was not provided. This does not affect relocated angle/house "
            "math, which runs entirely on the preserved UTC instant, but any future "
            "local-clock display for this destination will be unavailable."
        )

    angle_longitudes = _relocated_angle_longitudes(julian_day, latitude, longitude)
    relocated_ascendant = angle_longitudes["Ascendant"]

    relocated_angles = {
        "Ascendant": build_angle_data(angle_longitudes["Ascendant"]),
        "Midheaven": build_angle_data(angle_longitudes["Midheaven"]),
        "Descendant": build_angle_data(angle_longitudes["Descendant"]),
        "Imum_Coeli": build_angle_data(angle_longitudes["Imum_Coeli"]),
        "Vertex": {
            **build_angle_data(angle_longitudes["Vertex"]),
            "house": whole_sign_house(angle_longitudes["Vertex"], relocated_ascendant),
        },
    }

    natal_profile = natal_payload.get("user_profile")
    natal_profile = copy.deepcopy(natal_profile) if isinstance(natal_profile, dict) else {}

    relocated_aspects = _filter_angle_linked_aspects(natal_payload.get("aspects", []), warnings)

    return {
        "location_services": {
            "formula_version": FORMULA_VERSION,
            "relation_to_natal": "relocated_expression_only",
        },
        "destination": {
            "display_name": destination.get("display_name") or destination.get("location") or "",
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "timezone": destination.get("timezone"),
            "coordinate_source": destination.get("coordinate_source", "user_provided"),
        },
        "birth_utc_preserved": {
            "julian_day": julian_day,
            "utc_datetime": natal_profile.get("utc_datetime"),
        },
        "user_profile": natal_profile,
        "angles": relocated_angles,
        "houses": generate_whole_sign_houses(relocated_ascendant),
        "standard_planets": _reassign_bodies(natal_payload.get("standard_planets", {}), relocated_ascendant),
        "custom_asteroids": {},
        "aspects": relocated_aspects,
        "warnings": warnings,
    }


def compare_natal_to_relocated(natal_payload: dict, relocated_payload: dict) -> dict:
    """
    Structural (non-prose) comparison of a natal payload to its relocated
    counterpart: angle shifts, per-body house changes, and relocated angle
    contacts. Never recomputes natal condition — dignity, sect, and overall
    condition score stay sourced from natal_payload alone; only angularity
    (house placement, angle-conjunction) is read from the relocated chart.
    """
    warnings: list[str] = list(relocated_payload.get("warnings", []))

    natal_julian_day = _get_julian_day(natal_payload)
    relocated_julian_day = (relocated_payload.get("birth_utc_preserved") or {}).get("julian_day")

    birth_instant_preserved = (
        natal_julian_day is not None
        and isinstance(relocated_julian_day, (int, float))
        and abs(natal_julian_day - float(relocated_julian_day)) < 1e-9
    )
    if not birth_instant_preserved:
        warnings.append(
            "Relocated payload's Julian Day does not match the natal Julian Day; "
            "birth UTC instant preservation could not be confirmed."
        )

    natal_angles = natal_payload.get("angles") or {}
    relocated_angles = relocated_payload.get("angles") or {}

    angle_comparison: dict[str, dict[str, Any]] = {}
    for angle_name in ("Ascendant", "Midheaven", "Descendant", "Imum_Coeli", "Vertex"):
        natal_angle = natal_angles.get(angle_name) or {}
        relocated_angle = relocated_angles.get(angle_name) or {}
        natal_sign = natal_angle.get("sign")
        relocated_sign = relocated_angle.get("sign")
        angle_comparison[angle_name] = {
            "natal_sign": natal_sign,
            "natal_longitude": natal_angle.get("longitude"),
            "natal_house": natal_angle.get("house"),
            "relocated_sign": relocated_sign,
            "relocated_longitude": relocated_angle.get("longitude"),
            "relocated_house": relocated_angle.get("house"),
            "sign_changed": bool(natal_sign and relocated_sign and natal_sign != relocated_sign),
        }

    house_changes: dict[str, dict[str, Any]] = {}
    angle_contacts: dict[str, dict[str, Any]] = {}

    for group_name in LOCATION_EVIDENCE_BODY_GROUPS:
        natal_group = natal_payload.get(group_name) or {}
        relocated_group = relocated_payload.get(group_name) or {}

        for body_name, natal_body in natal_group.items():
            if not isinstance(natal_body, dict):
                continue

            relocated_body = relocated_group.get(body_name)
            if not isinstance(relocated_body, dict):
                warnings.append(
                    f"{body_name} is missing from the relocated payload; house comparison skipped."
                )
                continue

            natal_house = natal_body.get("house")
            relocated_house = relocated_body.get("house")
            house_changes[body_name] = {
                "natal_house": natal_house,
                "relocated_house": relocated_house,
                "changed": natal_house != relocated_house,
            }

            relocated_angularity = evaluate_angularity(relocated_payload, body_name)
            if relocated_angularity.get("is_conjunct_angle"):
                angle_contacts[body_name] = {
                    "angle": relocated_angularity.get("conjunct_angle_name"),
                    "orb": relocated_angularity.get("orb"),
                    "house_type": relocated_angularity.get("house_type"),
                }

    changed_house_count = sum(1 for entry in house_changes.values() if entry["changed"])

    return {
        "formula_version": FORMULA_VERSION,
        "birth_instant_preserved": birth_instant_preserved,
        "destination": relocated_payload.get("destination", {}),
        "angle_comparison": angle_comparison,
        "house_changes": house_changes,
        "changed_house_count": changed_house_count,
        "relocated_angle_contacts": angle_contacts,
        "natal_condition_note": (
            "Natal planetary condition (dignity, sect, essential/accidental strength, overall "
            "condition score) is not recomputed here and must not be. Read it from "
            "formulas.standard.planetary_condition.evaluate_all_planetary_conditions(natal_payload). "
            "Relocation only changes angularity/house placement, captured above."
        ),
        "unsupported_methods": list(UNSUPPORTED_METHODS),
        "warnings": warnings,
    }


# ── LocationEvidenceRecord (Round 2: Contract Formation) ───────────────────
#
# Evidence-shaped, not prose-shaped. No client-facing language lives here —
# see products/location_services/LOCATION_EVIDENCE_RECORD_CONTRACT.md for
# the field-by-field contract this was built against, including which
# BLOCK_SCHEMA.md fields this v0.1 cannot yet support and why.

def _house_type(house_number: Any) -> str:
    return HOUSE_TYPES.get(house_number, "unknown")


def _contact_strength(orb: Any) -> str:
    if not isinstance(orb, (int, float)):
        return "unknown"
    for label, max_orb in CONTACT_STRENGTH_BANDS:
        if orb <= max_orb:
            return label
    return CONTACT_STRENGTH_BANDS[-1][0]


def _movement_type(natal_house: Any, relocated_house: Any) -> str:
    if not isinstance(natal_house, int) or not isinstance(relocated_house, int):
        return "unknown"
    if natal_house == relocated_house:
        return "same_house"

    natal_type = _house_type(natal_house)
    relocated_type = _house_type(relocated_house)
    if relocated_type == "angular" and natal_type != "angular":
        return "newly_angular"
    if natal_type == "angular" and relocated_type != "angular":
        return "leaves_angular"
    return "house_changed"


def _evidence_birth_context(natal_payload: dict, warnings: list[str]) -> dict:
    profile = natal_payload.get("user_profile") or {}
    is_simple = bool(profile.get("simple_mode") or natal_payload.get("simple_mode"))
    local_datetime_raw = profile.get("local_datetime")

    birth_date = None
    birth_time = None
    if isinstance(local_datetime_raw, str):
        try:
            parsed = datetime.fromisoformat(local_datetime_raw)
        except ValueError:
            warnings.append(
                "birth_context: natal_payload.user_profile.local_datetime could not be parsed."
            )
        else:
            birth_date = parsed.date().isoformat()
            if not is_simple:
                birth_time = parsed.time().isoformat()

    if is_simple and local_datetime_raw:
        warnings.append(
            "birth_context.birth_time is withheld: natal_payload was generated in simple_mode. "
            "A placeholder noon time is used internally for chart math only and is not a real "
            "reported birth time."
        )

    return {
        "birth_date": birth_date,
        "birth_time": birth_time,
        "birth_location": natal_payload.get("birth_location") or profile.get("resolved_location"),
        "birth_timezone": profile.get("timezone"),
        "birth_time_confidence": profile.get("birth_time_state") or profile.get("birth_time_confidence"),
        "utc_instant": profile.get("utc_datetime"),
        "julian_day": profile.get("julian_day"),
        "calculation_profile": profile.get("methodology") or {
            "id": profile.get("methodology_id"),
            "label": profile.get("methodology_label"),
        },
    }


def _evidence_destination_context(relocated_payload: dict) -> dict:
    destination = relocated_payload.get("destination") or {}
    return {
        "display_name": destination.get("display_name"),
        "latitude": destination.get("latitude"),
        "longitude": destination.get("longitude"),
        "timezone": destination.get("timezone"),
        "coordinate_precision": destination.get("coordinate_source", "unknown"),
    }


def _evidence_relocated_chart(relocated_payload: dict) -> dict:
    methodology = (relocated_payload.get("user_profile") or {}).get("methodology") or {}
    return {
        "house_system": methodology.get("house_system", "Whole Sign"),
        "zodiac": methodology.get("zodiac", "Tropical"),
        "angles": relocated_payload.get("angles", {}),
        "house_cusps": relocated_payload.get("houses", {}),
    }


def _evidence_planet_house_changes(comparison: dict) -> list[dict]:
    items = []
    for body_name, entry in comparison.get("house_changes", {}).items():
        natal_house = entry.get("natal_house")
        relocated_house = entry.get("relocated_house")
        items.append({
            "id": f"house_change:{body_name}",
            "body": body_name,
            "natal_house": natal_house,
            "relocated_house": relocated_house,
            "house_changed": bool(entry.get("changed")),
            "natal_house_type": _house_type(natal_house),
            "relocated_house_type": _house_type(relocated_house),
            "movement_type": _movement_type(natal_house, relocated_house),
        })
    return items


def _evidence_relocated_angle_contacts(comparison: dict) -> list[dict]:
    items = []
    for body_name, contact in comparison.get("relocated_angle_contacts", {}).items():
        orb = contact.get("orb")
        items.append({
            "id": f"angle_contact:{body_name}:{contact.get('angle')}",
            "body": body_name,
            "angle": contact.get("angle"),
            "orb": orb,
            "contact_strength": _contact_strength(orb),
            "relocated_house_type": contact.get("house_type"),
        })
    return items


def _evidence_emphasized_bodies(house_change_items: list[dict], angle_contact_items: list[dict]) -> set[str]:
    emphasized = {item["body"] for item in angle_contact_items}
    emphasized |= {item["body"] for item in house_change_items if item["house_changed"]}
    return emphasized


def _evidence_natal_modifiers(
    natal_payload: dict,
    emphasized_bodies: set[str],
    warnings: list[str],
) -> dict[str, dict]:
    """
    Natal-only condition data for relocation-emphasized bodies, computed by
    calling evaluate_all_planetary_conditions() directly on natal_payload --
    never on the relocated payload. This is safe precisely because it is the
    narrow standard-formula function, not formulas.report_surface's layered
    report bundle: it reads natal_payload's own angles/houses/planets and
    returns each body's dignity, sect, and overall condition score exactly
    as the natal chart alone determines them. Relocation cannot see or
    change any of these values -- it only supplies which bodies are
    "emphasized" enough (via a relocated house change or angle contact) to
    be worth including here.

    Covers Sun through Pluto only, matching
    formulas.standard.planetary_condition.STANDARD_BODIES. Nodes, Lilith,
    and asteroids get no entry even if emphasized -- see warnings.
    """
    if not emphasized_bodies:
        return {}

    try:
        condition_records = evaluate_all_planetary_conditions(natal_payload)
    except Exception as exc:  # noqa: BLE001 - surfaced as a warning, not a crash
        warnings.append(f"Could not compute natal condition modifiers: {exc}")
        return {}

    modifiers: dict[str, dict] = {}
    for body_name in sorted(emphasized_bodies):
        record = condition_records.get(body_name)
        if record is None:
            warnings.append(
                f"{body_name} is relocation-emphasized but has no natal condition record "
                "(evaluate_all_planetary_conditions covers Sun through Pluto only)."
            )
            continue

        record_dict = record.to_dict() if hasattr(record, "to_dict") else dict(record)
        modifiers[body_name] = {
            "body": body_name,
            "source_standard_formula": "formulas.standard.planetary_condition.evaluate_all_planetary_conditions",
            "condition_classification": record_dict.get("condition_classification"),
            "overall_condition_score": record_dict.get("overall_condition_score"),
            "essential_dignity": record_dict.get("essential_dignity"),
            "accidental_dignity": record_dict.get("accidental_dignity"),
            "sect_condition": record_dict.get("sect_condition"),
            "motion_condition": record_dict.get("motion_condition"),
            "natal_house_type": record_dict.get("angularity"),
            "was_natal_angular": record_dict.get("angularity") == "angular",
            "routing_tags": record_dict.get("routing_tags", []),
            "confidence": record_dict.get("confidence"),
            "missing_inputs": record_dict.get("missing_inputs", []),
            "note": (
                "Computed from natal_payload only. Relocation does not change this planet's "
                "dignity, sect, or overall condition score -- only its relocated house/angle "
                "expression, tracked separately in planet_house_changes / relocated_angle_contacts."
            ),
        }
    return modifiers


def _evidence_ranking(
    natal_payload: dict,
    comparison: dict,
    house_change_items: list[dict],
    angle_contact_items: list[dict],
    natal_modifiers: dict[str, dict],
) -> dict:
    """
    Deterministic ranking implementing exactly the "Evidence Priority" rules
    already authored in products/location_services/EVIDENCE_TO_MEANING_MATRIX.md
    (Primary Evidence / Context Evidence / Restricted Evidence) -- no new
    interpretive judgment is introduced here. contradictory_evidence is left
    empty: conflict detection (e.g. "visibility vs privacy" from that same
    doc's "Evidence Conflict Handling" section) is not implemented in v0.1.
    """
    primary_ids: list[str] = []
    supporting_ids: list[str] = []

    bodies_with_angle_contact: set[str] = set()
    for item in angle_contact_items:
        bodies_with_angle_contact.add(item["body"])
        if item["body"] in CORE_CONDITION_BODIES:
            primary_ids.append(item["id"])
        else:
            supporting_ids.append(item["id"])

    for item in house_change_items:
        if not item["house_changed"]:
            continue
        if item["body"] not in CORE_CONDITION_BODIES:
            supporting_ids.append(item["id"])
        elif item["movement_type"] == "newly_angular":
            primary_ids.append(item["id"])
        elif item["body"] in bodies_with_angle_contact:
            # Repeats a body already flagged via angle contact.
            primary_ids.append(item["id"])
        else:
            supporting_ids.append(item["id"])

    for angle_name, entry in comparison.get("angle_comparison", {}).items():
        if angle_name == "Vertex":
            continue
        if entry.get("sign_changed"):
            primary_ids.append(f"orientation_shift:{angle_name}")

    supporting_ids.extend(f"natal_modifier:{body_name}" for body_name in natal_modifiers)

    confidence_notes: list[str] = []
    birth_time_confidence = (natal_payload.get("user_profile") or {}).get("birth_time_state")
    if birth_time_confidence and birth_time_confidence != "exact_birth_time":
        confidence_notes.append(
            f"Birth time confidence is '{birth_time_confidence}'; angle-contact and "
            "house-placement evidence should be treated with reduced certainty."
        )

    return {
        "primary_evidence": primary_ids,
        "supporting_evidence": supporting_ids,
        "contradictory_evidence": [],
        "speculative_or_excluded_evidence": list(UNSUPPORTED_METHODS),
        "confidence_notes": confidence_notes,
    }


# Known per-body-repeated warning templates, matched against the exact
# f-strings this module generates elsewhere. Grouping by template (rather
# than only by literal string equality) is what actually collapses the
# "30+ repeated asteroid modifier warnings" case documented in
# LOCATION_EVIDENCE_RECORD_SAMPLES.md -- those warnings differ only by the
# interpolated body name, so they are never literally identical strings.
_WARNING_TEMPLATES = (
    (
        "no_natal_condition_record",
        re.compile(
            r"^(?P<body>.+) is relocation-emphasized but has no natal condition record "
            r"\(evaluate_all_planetary_conditions covers Sun through Pluto only\)\.$"
        ),
    ),
    (
        "missing_from_relocated_payload",
        re.compile(
            r"^(?P<body>.+) is missing from the relocated payload; house comparison skipped\.$"
        ),
    ),
)


# Human-readable base phrasing for each templated warning above, used only
# when a template's count > 1 (see _summarize_warnings). Kept as a
# separate mapping so the regex and the summary phrasing can each read
# clearly on their own.
_WARNING_TEMPLATE_MESSAGES = {
    "no_natal_condition_record": (
        "relocation-emphasized bodies have no natal condition record "
        "(evaluate_all_planetary_conditions covers Sun through Pluto only)."
    ),
    "missing_from_relocated_payload": (
        "bodies are missing from the relocated payload; house comparison skipped."
    ),
}


def _stable_message_key(message: str) -> str:
    return f"other_{hashlib.sha256(message.encode('utf-8')).hexdigest()[:8]}"


def _summarize_warnings(warnings: list[str]) -> list[dict]:
    """
    Groups the raw warnings list into stable, countable entries -- without
    altering the raw list itself (that stays exactly as generated,
    unaggregated, for anyone who wants the literal record). Two known
    per-body templates (see _WARNING_TEMPLATES) are recognized and
    collapsed with a count and the list of affected bodies; any other
    warning is grouped only with other messages that are byte-identical to
    it, keyed by a short stable hash so repeated identical one-off
    warnings still collapse too.
    """
    grouped: dict[str, dict] = {}
    order: list[str] = []

    for message in warnings:
        key = None
        body = None
        for template_key, pattern in _WARNING_TEMPLATES:
            match = pattern.match(message)
            if match:
                key = template_key
                body = match.group("body")
                break

        if key is None:
            key = _stable_message_key(message)

        entry = grouped.get(key)
        if entry is None:
            entry = {
                "id": f"warning_summary:{key}",
                "key": key,
                "message": message,
                "count": 0,
                "examples": [],
            }
            grouped[key] = entry
            order.append(key)

        entry["count"] += 1
        if body is not None and body not in entry["examples"]:
            entry["examples"].append(body)

    summary: list[dict] = []
    for key in order:
        entry = grouped[key]
        if entry["count"] > 1 and key in _WARNING_TEMPLATE_MESSAGES:
            entry["message"] = f"{entry['count']} {_WARNING_TEMPLATE_MESSAGES[key]}"
        summary.append(entry)

    return summary


def build_location_evidence_record(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> dict:
    """
    Builds a structured LocationEvidenceRecord for a natal chart relocated
    to a destination. Reuses build_relocated_payload() and
    compare_natal_to_relocated() rather than recomputing anything.

    Evidence-shaped, not prose-shaped: no interpretive language, no report
    rendering, no CLI generation. purpose_lens and relationship_to_place are
    recorded as provided and are not validated against any enumerated list
    (that taxonomy belongs to the content lane's block schema, not this
    engine layer) -- see LOCATION_EVIDENCE_RECORD_CONTRACT.md.

    Never runs a condition-bearing formula (evaluate_dignity,
    evaluate_chart_sect*, evaluate_all_planetary_conditions) against the
    relocated payload -- only against natal_payload, via
    _evidence_natal_modifiers().
    """
    if purpose_lens is not None and not isinstance(purpose_lens, str):
        raise ValueError("purpose_lens must be a string or None.")
    if relationship_to_place is not None and not isinstance(relationship_to_place, str):
        raise ValueError("relationship_to_place must be a string or None.")

    relocated_payload = build_relocated_payload(natal_payload, destination)
    comparison = compare_natal_to_relocated(natal_payload, relocated_payload)

    warnings: list[str] = list(comparison.get("warnings", []))

    house_change_items = _evidence_planet_house_changes(comparison)
    angle_contact_items = _evidence_relocated_angle_contacts(comparison)
    emphasized_bodies = _evidence_emphasized_bodies(house_change_items, angle_contact_items)
    natal_modifiers = _evidence_natal_modifiers(natal_payload, emphasized_bodies, warnings)
    evidence_ranking = _evidence_ranking(
        natal_payload, comparison, house_change_items, angle_contact_items, natal_modifiers
    )

    birth_context = _evidence_birth_context(natal_payload, warnings)
    destination_context = _evidence_destination_context(relocated_payload)

    # Computed last, after every warning-producing step above has had a
    # chance to append to `warnings` -- this summary must reflect the
    # complete raw list, not a partial one.
    warning_summary = _summarize_warnings(warnings)

    appendix_trace = {
        "formula_version": EVIDENCE_RECORD_FORMULA_VERSION,
        "relocated_payload_formula_version": FORMULA_VERSION,
        "calculation_sources": [
            "engine.natal_engine.generate_payload",
            "engine.location_services.build_relocated_payload",
            "engine.location_services.compare_natal_to_relocated",
            "formulas.standard.angularity.evaluate_angularity (relocated payload)",
            "formulas.standard.planetary_condition.evaluate_all_planetary_conditions (natal_payload only)",
        ],
        "tolerances": {
            "angle_contact_max_orb_degrees": CONTACT_STRENGTH_BANDS[-1][1],
            "contact_strength_bands_degrees": dict(CONTACT_STRENGTH_BANDS),
        },
        "unsupported_methods": list(UNSUPPORTED_METHODS),
        "warnings": warnings,
        "warning_summary": warning_summary,
        "birth_time_confidence": birth_context.get("birth_time_confidence"),
        "coordinate_precision": destination_context.get("coordinate_precision"),
        "methodology": (relocated_payload.get("user_profile") or {}).get("methodology", {}),
    }

    return {
        "formula_version": EVIDENCE_RECORD_FORMULA_VERSION,
        "birth_context": birth_context,
        "destination_context": destination_context,
        "relocated_chart": _evidence_relocated_chart(relocated_payload),
        "planet_house_changes": house_change_items,
        "relocated_angle_contacts": angle_contact_items,
        "natal_modifiers": natal_modifiers,
        "evidence_ranking": evidence_ranking,
        "purpose_lens": purpose_lens,
        "relationship_to_place": relationship_to_place,
        "appendix_trace": appendix_trace,
        "unsupported_methods": list(UNSUPPORTED_METHODS),
        "warnings": warnings,
        "warning_summary": warning_summary,
    }
