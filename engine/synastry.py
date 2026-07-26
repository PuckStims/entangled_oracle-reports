"""
Computation-first synastry layer for two natal payloads.

This module intentionally stops at evidence records. It does not generate
client-facing relationship prose or compatibility verdicts.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from config import MAJOR_ASPECTS, ORB_CONFIG, SIGN_ELEMENTS, SIGN_MODALITIES
from formulas.standard.confidence import (
    ANGLE_DEPENDENT_UNAVAILABLE,
    APPROXIMATE_BIRTH_TIME,
    EXACT_BIRTH_TIME,
    PROVISIONAL_NEAR_HORIZON,
    UNKNOWN_BIRTH_TIME,
)


SCHEMA_VERSION = "synastry_pair_v0.1"
FORMULA_VERSION = "synastry_computation_v0.2.0"
COMPOSITE_METHOD = "midpoint_composite"

LIVE_STATUS = "implemented_verified"
NOT_IMPLEMENTED = "not_implemented"
WITHHELD_MISSING_BIRTH_TIME = "withheld_missing_birth_time"
WITHHELD_ANGLE_DEPENDENCY = "withheld_angle_dependency"

SIGNS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)

CORE_BODIES = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)
OPTIONAL_BODIES = ("Chiron", "North_Node", "South_Node")
ANGLE_POINTS = ("Ascendant", "Descendant", "Midheaven", "Imum_Coeli", "Vertex")

BODY_DOMAINS = {
    "Sun": "identity/vitality/visibility",
    "Moon": "emotion/body/rhythm",
    "Mercury": "communication/perception/exchange",
    "Venus": "affection/attraction/value",
    "Mars": "desire/assertion/action",
    "Jupiter": "growth/meaning/opportunity",
    "Saturn": "commitment/constraint/time",
    "Uranus": "change/liberation/disruption",
    "Neptune": "imagination/porosity/idealization",
    "Pluto": "intensity/merging/transformation",
    "Chiron": "sensitivity/repair/teaching",
    "North_Node": "growth_direction/developmental_pull",
    "South_Node": "familiar_pattern/inherited_gravity",
    "Ascendant": "identity/body/interface",
    "Descendant": "partnership/mirror/encounter",
    "Midheaven": "visibility/vocation/public_path",
    "Imum_Coeli": "home/root/private_foundation",
    "Vertex": "encounter/fated-feeling/threshold",
}

BODY_WEIGHTS = {
    "Sun": 1.20,
    "Moon": 1.20,
    "Ascendant": 1.20,
    "Descendant": 1.20,
    "Midheaven": 1.20,
    "Imum_Coeli": 1.20,
    "Vertex": 1.20,
    "Mercury": 1.10,
    "Venus": 1.10,
    "Mars": 1.10,
    "Jupiter": 1.00,
    "Saturn": 1.00,
    "Uranus": 0.85,
    "Neptune": 0.85,
    "Pluto": 0.85,
    "Chiron": 0.85,
    "North_Node": 0.85,
    "South_Node": 0.85,
}

ASPECT_WEIGHTS = {
    "Conjunction": 1.15,
    "Opposition": 1.15,
    "Square": 1.00,
    "Trine": 1.00,
    "Sextile": 0.80,
}

ASPECT_POLARITY = {
    "Conjunction": "mixed",
    "Opposition": "tensional",
    "Square": "tensional",
    "Trine": "supportive",
    "Sextile": "supportive",
}
ADVANCED_MIDPOINT_SPECS = {
    "sun_moon": ("Sun", "Moon"),
    "venus_mars": ("Venus", "Mars"),
}
ADVANCED_BODY_SET = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
ADVANCED_MIDPOINT_ORB = 2.0
ADVANCED_ANTISCIA_ORB = 2.0

TOPIC_SPECS = {
    "attachment_emotional_rhythm": {
        "label": "attachment/emotional rhythm",
        "bodies": {"Moon"},
        "angles": {"Imum_Coeli"},
        "houses": {4},
        "families": {"moon_contacts", "fourth_house_overlay", "ic_angle_contact"},
    },
    "affection_value_attraction": {
        "label": "affection/value/attraction",
        "bodies": {"Venus"},
        "angles": set(),
        "houses": set(),
        "families": {"venus_contacts", "venus_overlay"},
    },
    "desire_friction_action": {
        "label": "desire/friction/action",
        "bodies": {"Mars"},
        "angles": set(),
        "houses": set(),
        "families": {"mars_contacts", "mars_overlay"},
    },
    "communication": {
        "label": "communication",
        "bodies": {"Mercury"},
        "angles": set(),
        "houses": {3},
        "families": {"mercury_contacts", "third_house_overlay"},
    },
    "commitment_constraint_time": {
        "label": "commitment/constraint/time",
        "bodies": {"Saturn"},
        "angles": set(),
        "houses": set(),
        "families": {"saturn_contacts", "saturn_overlay"},
    },
    "visibility_public_path": {
        "label": "visibility/public path",
        "bodies": {"Sun"},
        "angles": {"Midheaven"},
        "houses": {10},
        "families": {"sun_contacts", "mc_angle_contact", "tenth_house_overlay"},
    },
    "growth_meaning": {
        "label": "growth/meaning",
        "bodies": {"Jupiter"},
        "angles": set(),
        "houses": {9},
        "families": {"jupiter_contacts", "ninth_house_overlay"},
    },
    "intensity_merging_shared_resources": {
        "label": "intensity/merging/shared resources",
        "bodies": {"Pluto"},
        "angles": set(),
        "houses": {8},
        "families": {"pluto_contacts", "eighth_house_overlay"},
    },
}


def build_pair_payload(
    person_a_natal_payload: dict[str, Any],
    person_b_natal_payload: dict[str, Any],
    *,
    relationship_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Builds the first synastry pair payload from two natal payloads."""
    person_a = _person_record("A", person_a_natal_payload)
    person_b = _person_record("B", person_b_natal_payload)
    people = {"A": person_a, "B": person_b}

    directional_aspects, aspect_withheld = scan_directional_aspects(people)
    mutual_aspects = normalize_mutual_aspects(directional_aspects)
    house_overlays, overlay_withheld = scan_house_overlays(people)
    composite = compute_midpoint_composite(person_a_natal_payload, person_b_natal_payload)
    composite_to_natal_resonance, composite_resonance_withheld = compute_composite_to_natal_resonance(people, composite)
    advanced_static_evidence = compute_advanced_static_evidence(people)
    repeated_natal_themes = compute_repeated_natal_themes(people)
    relationship_topic_signatures = compute_relationship_topic_signatures(
        mutual_aspects,
        house_overlays,
    )
    relationship_convergence = compute_relationship_convergence(relationship_topic_signatures)

    withheld_records = aspect_withheld + overlay_withheld + composite_resonance_withheld
    meta = {
        "relationship_type": "unspecified",
        "consent_state": "unreviewed",
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }
    if relationship_meta:
        meta.update(relationship_meta)

    return {
        "schema_version": SCHEMA_VERSION,
        "person_a": person_a,
        "person_b": person_b,
        "relationship_meta": meta,
        "computations": {
            "directional_aspects": directional_aspects,
            "mutual_aspects": mutual_aspects,
            "house_overlays": house_overlays,
            "repeated_natal_themes": repeated_natal_themes,
            "composite": composite,
            "composite_to_natal_resonance": composite_to_natal_resonance,
            "advanced_static_evidence": advanced_static_evidence,
            "relationship_topic_signatures": relationship_topic_signatures,
            "relationship_convergence": relationship_convergence,
            "relationship_timing": [],
        },
        "confidence": {
            "angle_house_policy": {
                "angle_contacts": "An angle contact is live only when the chart that owns the angle is angle-eligible.",
                "house_overlays": "A house overlay is live only when the chart that owns the houses is angle-eligible.",
                "eligible_birth_time_states": [
                    EXACT_BIRTH_TIME,
                    APPROXIMATE_BIRTH_TIME,
                    PROVISIONAL_NEAR_HORIZON,
                ],
            },
            "withheld_records": withheld_records,
            "assumptions": [
                "Synastry body-to-body contacts use existing natal longitudes from both payloads.",
                "Synastry aspect orbs use config.ORB_CONFIG['max_orb_synastry'] as the hard cap.",
                "Whole Sign house overlays reuse each natal payload's house-owner Ascendant sign.",
                "Composite-to-natal resonance compares midpoint-composite body positions back to each natal chart without borrowing composite houses.",
                "Advanced static evidence is a separate fine-grain layer built from longitude-only midpoint and antiscia techniques with tighter orbs than the core synastry scan.",
            ],
        },
        "sidecar": _build_sidecar(withheld_records),
        "provenance": {
            "source_payload_ids": [
                _payload_id(person_a_natal_payload, "A"),
                _payload_id(person_b_natal_payload, "B"),
            ],
            "formula_versions": [FORMULA_VERSION],
        },
    }


def generate_pair_payload(
    person_a_natal_payload: dict[str, Any],
    person_b_natal_payload: dict[str, Any],
    *,
    relationship_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Alias matching the natal engine's payload-generation language."""
    return build_pair_payload(
        person_a_natal_payload,
        person_b_natal_payload,
        relationship_meta=relationship_meta,
    )


def scan_directional_aspects(
    people: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scans A-to-B and B-to-A directional synastry aspects."""
    records: list[dict[str, Any]] = []
    withheld: list[dict[str, Any]] = []
    body_names = _pair_body_names(people)
    for source_label, target_label in (("A", "B"), ("B", "A")):
        source = people[source_label]
        target = people[target_label]
        for source_point in _eligible_points(source, body_names):
            for target_point in _eligible_points(target, body_names):
                if source_point["name"] == target_point["name"] and source_label == target_label:
                    continue
                unavailable = _angle_unavailable_reason(source_point, target_point)
                if unavailable:
                    withheld_record = _withheld_angle_aspect_record(
                        source_label,
                        source_point,
                        target_label,
                        target_point,
                        unavailable,
                    )
                    records.append(withheld_record)
                    withheld.append(withheld_record)
                    continue

                match = _best_aspect_match(source_point["longitude"], target_point["longitude"])
                if not match:
                    continue
                dependency = _directional_dependency(source_point, target_point)
                confidence_state = _aspect_confidence_state(source, target, dependency)
                records.append(
                    {
                        "record_type": "directional_aspect",
                        "source_person": source_label,
                        "source_body": source_point["name"],
                        "target_person": target_label,
                        "target_body": target_point["name"],
                        "aspect": match["aspect"],
                        "exact_angle": match["exact_angle"],
                        "measured_distance": match["measured_distance"],
                        "orb": match["orb"],
                        "max_orb": match["max_orb"],
                        "orb_fraction": match["orb_fraction"],
                        "source_domain": BODY_DOMAINS.get(source_point["name"], "unspecified"),
                        "target_domain": BODY_DOMAINS.get(target_point["name"], "unspecified"),
                        "directional_dependency": dependency,
                        "confidence_state": confidence_state,
                        "withheld": False,
                    }
                )
    records.sort(key=_directional_sort_key)
    return records, withheld


def normalize_mutual_aspects(
    directional_aspects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Builds unordered mutual records while retaining directional evidence."""
    grouped: dict[tuple[tuple[str, str], tuple[str, str]], list[dict[str, Any]]] = defaultdict(list)
    for record in directional_aspects:
        if record.get("withheld"):
            continue
        source = (record["source_person"], record["source_body"])
        target = (record["target_person"], record["target_body"])
        key = tuple(sorted((source, target)))
        grouped[key].append(record)

    mutual_records = []
    for key, records in grouped.items():
        strongest = max(records, key=lambda item: item.get("orb_fraction", 0.0))
        dependency = (
            "angle_dependent"
            if any(item.get("directional_dependency") != "body_to_body" for item in records)
            else "body_to_body"
        )
        confidence_state = _mutual_confidence_state(records)
        salience = _salience(strongest, confidence_state)
        mutual_records.append(
            {
                "record_type": "mutual_aspect",
                "mutual_key": [
                    {"person": person, "body": body}
                    for person, body in key
                ],
                "aspect": strongest["aspect"],
                "exact_angle": strongest["exact_angle"],
                "measured_distance": strongest["measured_distance"],
                "orb": strongest["orb"],
                "orb_fraction": strongest["orb_fraction"],
                "dependency": dependency,
                "confidence_state": confidence_state,
                "salience": salience,
                "directional_records": records,
            }
        )

    mutual_records.sort(
        key=lambda item: (
            -item["salience"],
            item["orb"],
            item["mutual_key"][0]["person"],
            item["mutual_key"][0]["body"],
            item["mutual_key"][1]["person"],
            item["mutual_key"][1]["body"],
        )
    )
    return mutual_records


def scan_house_overlays(
    people: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scans directional Whole Sign house overlays with birth-time gating."""
    records: list[dict[str, Any]] = []
    withheld: list[dict[str, Any]] = []
    body_names = _pair_body_names(people)
    for source_label, target_label in (("A", "B"), ("B", "A")):
        source = people[source_label]
        target = people[target_label]
        source_bodies = _body_points(source, body_names)
        if not target["angle_eligible"]:
            for source_body in source_bodies:
                record = {
                    "record_type": "house_overlay",
                    "source_person": source_label,
                    "source_body": source_body["name"],
                    "target_person": target_label,
                    "target_house": None,
                    "target_house_sign": None,
                    "source_longitude": source_body["longitude"],
                    "confidence_state": ANGLE_DEPENDENT_UNAVAILABLE,
                    "withheld": True,
                    "withheld_reason": WITHHELD_MISSING_BIRTH_TIME,
                    "missing_inputs": [f"{target_label}.birth_time"],
                }
                records.append(record)
                withheld.append(record)
            continue

        ascendant = _angle_longitude(target["natal_payload"], "Ascendant")
        if ascendant is None:
            for source_body in source_bodies:
                record = {
                    "record_type": "house_overlay",
                    "source_person": source_label,
                    "source_body": source_body["name"],
                    "target_person": target_label,
                    "target_house": None,
                    "target_house_sign": None,
                    "source_longitude": source_body["longitude"],
                    "confidence_state": ANGLE_DEPENDENT_UNAVAILABLE,
                    "withheld": True,
                    "withheld_reason": "withheld_missing_payload_field",
                    "missing_inputs": [f"{target_label}.angles.Ascendant"],
                }
                records.append(record)
                withheld.append(record)
            continue

        for source_body in source_bodies:
            house_number = _whole_sign_house(source_body["longitude"], ascendant)
            house = target["natal_payload"].get("houses", {}).get(f"House_{house_number}", {})
            records.append(
                {
                    "record_type": "house_overlay",
                    "source_person": source_label,
                    "source_body": source_body["name"],
                    "target_person": target_label,
                    "target_house": house_number,
                    "target_house_sign": house.get("sign") or _sign_for_house(ascendant, house_number),
                    "source_longitude": source_body["longitude"],
                    "confidence_state": target["birth_time_state"],
                    "withheld": False,
                }
            )
    records.sort(
        key=lambda item: (
            item["source_person"],
            item["target_person"],
            item["source_body"],
            item.get("target_house") or 99,
        )
    )
    return records, withheld


def compute_midpoint_composite(
    person_a_natal_payload: dict[str, Any],
    person_b_natal_payload: dict[str, Any],
    *,
    ambiguity_epsilon: float = 1e-6,
) -> dict[str, Any]:
    """Computes midpoint-composite body positions for matching bodies."""
    bodies = []
    for body_name in CORE_BODIES + OPTIONAL_BODIES:
        lon_a = _body_longitude(person_a_natal_payload, body_name)
        lon_b = _body_longitude(person_b_natal_payload, body_name)
        if lon_a is None or lon_b is None:
            continue
        delta = ((lon_b - lon_a + 540.0) % 360.0) - 180.0
        is_ambiguous = abs(abs(delta) - 180.0) <= ambiguity_epsilon
        if is_ambiguous:
            midpoint = None
            zodiac = None
            possible_midpoints = sorted(
                {
                    round((lon_a + 90.0) % 360.0, 4),
                    round((lon_a - 90.0) % 360.0, 4),
                }
            )
        else:
            midpoint = round((lon_a + (delta / 2.0)) % 360.0, 4)
            zodiac = _zodiac_position(midpoint)
            possible_midpoints = []
        bodies.append(
            {
                "body": body_name,
                "person_a_longitude": round(lon_a % 360.0, 4),
                "person_b_longitude": round(lon_b % 360.0, 4),
                "delta": round(delta, 4),
                "longitude": midpoint,
                "zodiac_position": zodiac,
                "ambiguous": is_ambiguous,
                "possible_midpoints": possible_midpoints,
            }
        )
    aspects = _scan_composite_aspects(bodies)

    return {
        "record_type": "composite",
        "composite_method": COMPOSITE_METHOD,
        "bodies": bodies,
        "aspects": aspects,
        "houses": None,
        "status": {
            "body_midpoints": LIVE_STATUS,
            "composite_aspects": LIVE_STATUS,
            "composite_houses": NOT_IMPLEMENTED,
            "davison": NOT_IMPLEMENTED,
        },
    }


def compute_repeated_natal_themes(
    people: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compares natal payload structures without adding interpretation."""
    body_names = _pair_body_names(people)
    person_a = people["A"]
    person_b = people["B"]
    payload_a = person_a["natal_payload"]
    payload_b = person_b["natal_payload"]
    records: list[dict[str, Any]] = []

    for sign in SIGNS:
        evidence_a = _bodies_with_sign(payload_a, body_names, sign)
        evidence_b = _bodies_with_sign(payload_b, body_names, sign)
        if len(evidence_a) >= 2 and len(evidence_b) >= 2:
            records.append(
                _repeated_theme_record(
                    theme_key=f"shared_{sign.lower()}_emphasis",
                    theme_type="same_sign_emphasis",
                    person_a_evidence={"sign": sign, "bodies": evidence_a},
                    person_b_evidence={"sign": sign, "bodies": evidence_b},
                    confidence_state=_least_precise_state(
                        person_a["birth_time_state"],
                        person_b["birth_time_state"],
                    ),
                    salience=_bounded_theme_salience(len(evidence_a), len(evidence_b), 5),
                )
            )

    for element, signs in SIGN_ELEMENTS.items():
        evidence_a = _bodies_in_signs(payload_a, body_names, set(signs))
        evidence_b = _bodies_in_signs(payload_b, body_names, set(signs))
        if len(evidence_a) >= 4 and len(evidence_b) >= 4:
            records.append(
                _repeated_theme_record(
                    theme_key=f"shared_{element}_element_concentration",
                    theme_type="same_element_concentration",
                    person_a_evidence={"element": element, "bodies": evidence_a},
                    person_b_evidence={"element": element, "bodies": evidence_b},
                    confidence_state=_least_precise_state(
                        person_a["birth_time_state"],
                        person_b["birth_time_state"],
                    ),
                    salience=_bounded_theme_salience(len(evidence_a), len(evidence_b), 7),
                )
            )

    for modality, signs in SIGN_MODALITIES.items():
        evidence_a = _bodies_in_signs(payload_a, body_names, set(signs))
        evidence_b = _bodies_in_signs(payload_b, body_names, set(signs))
        if len(evidence_a) >= 4 and len(evidence_b) >= 4:
            records.append(
                _repeated_theme_record(
                    theme_key=f"shared_{modality}_modality_concentration",
                    theme_type="same_modality_concentration",
                    person_a_evidence={"modality": modality, "bodies": evidence_a},
                    person_b_evidence={"modality": modality, "bodies": evidence_b},
                    confidence_state=_least_precise_state(
                        person_a["birth_time_state"],
                        person_b["birth_time_state"],
                    ),
                    salience=_bounded_theme_salience(len(evidence_a), len(evidence_b), 7),
                )
            )

    for family_key in sorted(_aspect_family_set(payload_a, body_names) & _aspect_family_set(payload_b, body_names)):
        body_a, body_b, aspect = family_key.split("|")
        records.append(
            _repeated_theme_record(
                theme_key=f"shared_{body_a.lower()}_{body_b.lower()}_{aspect.lower()}",
                theme_type="repeated_aspect_family",
                person_a_evidence={"body_1": body_a, "body_2": body_b, "aspect": aspect},
                person_b_evidence={"body_1": body_a, "body_2": body_b, "aspect": aspect},
                confidence_state=_least_precise_state(
                    person_a["birth_time_state"],
                    person_b["birth_time_state"],
                ),
                salience=0.62,
            )
        )

    if person_a["angle_eligible"] and person_b["angle_eligible"]:
        for house_number in range(1, 13):
            evidence_a = _bodies_in_house(payload_a, body_names, house_number)
            evidence_b = _bodies_in_house(payload_b, body_names, house_number)
            if len(evidence_a) >= 2 and len(evidence_b) >= 2:
                records.append(
                    _repeated_theme_record(
                        theme_key=f"shared_house_{house_number}_emphasis",
                        theme_type="shared_house_emphasis",
                        person_a_evidence={"house": house_number, "bodies": evidence_a},
                        person_b_evidence={"house": house_number, "bodies": evidence_b},
                        confidence_state=_least_precise_state(
                            person_a["birth_time_state"],
                            person_b["birth_time_state"],
                        ),
                        salience=_bounded_theme_salience(len(evidence_a), len(evidence_b), 5),
                    )
                )

    records.sort(key=lambda item: (-item["salience"], item["theme_key"]))
    return records


def compute_composite_to_natal_resonance(
    people: dict[str, dict[str, Any]],
    composite: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Compares midpoint-composite bodies back to each natal chart."""
    live_bodies = [
        item
        for item in composite.get("bodies", []) or []
        if isinstance(item, dict) and not item.get("ambiguous") and isinstance(item.get("longitude"), (int, float))
    ]
    body_contacts: list[dict[str, Any]] = []
    house_overlays: list[dict[str, Any]] = []
    withheld: list[dict[str, Any]] = []

    for label, person in people.items():
        payload = person["natal_payload"]
        birth_time_state = person["birth_time_state"]
        target_body_names = _available_body_names(payload)
        target_body_points = [
            {
                "name": body_name,
                "kind": "body",
                "longitude": _body_longitude(payload, body_name),
                "owner": label,
                "owner_angle_eligible": person["angle_eligible"],
            }
            for body_name in target_body_names
            if _body_longitude(payload, body_name) is not None
        ]
        target_angle_points = _angle_points(person)

        for composite_body in live_bodies:
            composite_name = str(composite_body.get("body") or "")
            composite_longitude = float(composite_body.get("longitude") or 0.0)
            source_point = {
                "name": composite_name,
                "kind": "composite_body",
                "longitude": composite_longitude,
                "owner": "Composite",
                "owner_angle_eligible": True,
            }

            for target_point in target_body_points + target_angle_points:
                unavailable = _angle_unavailable_reason(source_point, target_point)
                if unavailable:
                    record = {
                        "record_type": "composite_to_natal_aspect",
                        "target_person": label,
                        "composite_body": composite_name,
                        "target_body": target_point["name"],
                        "aspect": None,
                        "exact_angle": None,
                        "measured_distance": None,
                        "orb": None,
                        "max_orb": ORB_CONFIG["max_orb_synastry"],
                        "orb_fraction": 0.0,
                        "target_domain": BODY_DOMAINS.get(target_point["name"], "unspecified"),
                        "directional_dependency": "angle_dependent",
                        "confidence_state": unavailable["confidence_state"],
                        "withheld": True,
                        "withheld_reason": unavailable["withheld_reason"],
                        "missing_inputs": unavailable["missing_inputs"],
                    }
                    body_contacts.append(record)
                    withheld.append(record)
                    continue
                match = _best_aspect_match(composite_longitude, float(target_point["longitude"]))
                if not match:
                    continue
                dependency = "angle_dependent" if target_point["kind"] == "angle" else "body_to_body"
                confidence_state = (
                    birth_time_state
                    if dependency == "angle_dependent"
                    else _least_precise_state(people["A"]["birth_time_state"], people["B"]["birth_time_state"])
                )
                record = {
                    "record_type": "composite_to_natal_aspect",
                    "target_person": label,
                    "composite_body": composite_name,
                    "target_body": target_point["name"],
                    "aspect": match["aspect"],
                    "exact_angle": match["exact_angle"],
                    "measured_distance": match["measured_distance"],
                    "orb": match["orb"],
                    "max_orb": match["max_orb"],
                    "orb_fraction": match["orb_fraction"],
                    "target_domain": BODY_DOMAINS.get(target_point["name"], "unspecified"),
                    "directional_dependency": dependency,
                    "confidence_state": confidence_state,
                    "withheld": False,
                    "withheld_reason": None,
                    "missing_inputs": [],
                }
                record["salience"] = round(
                    BODY_WEIGHTS.get(composite_name, 0.75)
                    * BODY_WEIGHTS.get(target_point["name"], 0.75)
                    * ASPECT_WEIGHTS.get(record["aspect"], 0.75)
                    * record.get("orb_fraction", 0.0)
                    * _confidence_score(confidence_state),
                    4,
                )
                body_contacts.append(record)

            if not person["angle_eligible"]:
                record = {
                    "record_type": "composite_to_natal_overlay",
                    "target_person": label,
                    "composite_body": composite_name,
                    "target_house": None,
                    "target_house_sign": None,
                    "confidence_state": UNKNOWN_BIRTH_TIME,
                    "withheld": True,
                    "withheld_reason": WITHHELD_MISSING_BIRTH_TIME,
                    "missing_inputs": [f"{label}.birth_time"],
                    "salience": 0.0,
                }
                house_overlays.append(record)
                withheld.append(record)
                continue

            ascendant = _angle_longitude(payload, "Ascendant")
            if ascendant is None:
                record = {
                    "record_type": "composite_to_natal_overlay",
                    "target_person": label,
                    "composite_body": composite_name,
                    "target_house": None,
                    "target_house_sign": None,
                    "confidence_state": birth_time_state,
                    "withheld": True,
                    "withheld_reason": "withheld_missing_payload_field",
                    "missing_inputs": [f"{label}.angles.Ascendant"],
                    "salience": 0.0,
                }
                house_overlays.append(record)
                withheld.append(record)
                continue

            house_number = _whole_sign_house(composite_longitude, ascendant)
            house = payload.get("houses", {}).get(f"House_{house_number}", {})
            record = {
                "record_type": "composite_to_natal_overlay",
                "target_person": label,
                "composite_body": composite_name,
                "target_house": house_number,
                "target_house_sign": house.get("sign") or _sign_for_house(ascendant, house_number),
                "confidence_state": birth_time_state,
                "withheld": False,
                "withheld_reason": None,
                "missing_inputs": [],
                "salience": round(BODY_WEIGHTS.get(composite_name, 0.75) * _confidence_score(birth_time_state), 4),
            }
            house_overlays.append(record)

    body_contacts.sort(
        key=lambda item: (
            str(item.get("target_person") or ""),
            item.get("withheld", False),
            -float(item.get("salience", 0.0) or 0.0),
            float(item.get("orb", 99.0) or 99.0),
            str(item.get("composite_body") or ""),
            str(item.get("target_body") or ""),
        )
    )
    house_overlays.sort(
        key=lambda item: (
            str(item.get("target_person") or ""),
            item.get("withheld", False),
            -BODY_WEIGHTS.get(str(item.get("composite_body") or ""), 0.0),
            item.get("target_house") or 99,
        )
    )

    return (
        {
            "record_type": "composite_to_natal_resonance",
            "composite_method": COMPOSITE_METHOD,
            "body_contacts": body_contacts,
            "house_overlays": house_overlays,
            "by_person": {
                label: {
                    "body_contacts": [item for item in body_contacts if item.get("target_person") == label],
                    "house_overlays": [item for item in house_overlays if item.get("target_person") == label],
                }
                for label in people
            },
            "status": {
                "body_contacts": LIVE_STATUS,
                "house_overlays": LIVE_STATUS,
            },
        },
        withheld,
    )


def compute_advanced_static_evidence(
    people: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Builds a separate fine-grain evidence layer from midpoint and antiscia techniques."""
    midpoint_contacts: list[dict[str, Any]] = []
    antiscia_contacts: list[dict[str, Any]] = []

    for target_label, target_person in people.items():
        source_label = "B" if target_label == "A" else "A"
        source_payload = people[source_label]["natal_payload"]
        target_payload = target_person["natal_payload"]
        confidence_state = _least_precise_state(
            people[source_label]["birth_time_state"],
            target_person["birth_time_state"],
        )

        midpoint_definitions = _midpoint_definitions(target_payload)
        for midpoint_key, midpoint_data in midpoint_definitions.items():
            midpoint_longitude = midpoint_data.get("longitude")
            if not isinstance(midpoint_longitude, (int, float)):
                continue
            for source_body in ADVANCED_BODY_SET:
                source_longitude = _body_longitude(source_payload, source_body)
                if source_longitude is None:
                    continue
                match = _best_aspect_match_with_orb(float(source_longitude), float(midpoint_longitude), ADVANCED_MIDPOINT_ORB)
                if not match or str(match.get("aspect") or "") not in {"Conjunction", "Opposition"}:
                    continue
                record = {
                    "record_type": "advanced_midpoint_contact",
                    "source_person": source_label,
                    "source_body": source_body,
                    "target_person": target_label,
                    "midpoint_key": midpoint_key,
                    "midpoint_bodies": list(midpoint_data.get("bodies") or []),
                    "midpoint_longitude": round(float(midpoint_longitude) % 360.0, 4),
                    "aspect": match["aspect"],
                    "exact_angle": match["exact_angle"],
                    "measured_distance": match["measured_distance"],
                    "orb": match["orb"],
                    "max_orb": match["max_orb"],
                    "orb_fraction": match["orb_fraction"],
                    "confidence_state": confidence_state,
                    "salience": round(
                        BODY_WEIGHTS.get(source_body, 0.75)
                        * sum(BODY_WEIGHTS.get(body, 0.75) for body in midpoint_data.get("bodies") or []) / max(len(midpoint_data.get("bodies") or []), 1)
                        * ASPECT_WEIGHTS.get(match["aspect"], 0.75)
                        * match["orb_fraction"]
                        * _confidence_score(confidence_state),
                        4,
                    ),
                }
                midpoint_contacts.append(record)

    for source_label, source_person in people.items():
        target_label = "B" if source_label == "A" else "A"
        source_payload = source_person["natal_payload"]
        target_payload = people[target_label]["natal_payload"]
        confidence_state = _least_precise_state(
            source_person["birth_time_state"],
            people[target_label]["birth_time_state"],
        )
        for source_body in ADVANCED_BODY_SET:
            source_longitude = _body_longitude(source_payload, source_body)
            if source_longitude is None:
                continue
            mirrored = _antiscia_longitude(source_longitude)
            contra = (mirrored + 180.0) % 360.0
            for target_body in ADVANCED_BODY_SET:
                target_longitude = _body_longitude(target_payload, target_body)
                if target_longitude is None:
                    continue
                for relation, reference_longitude in (("antiscia", mirrored), ("contra_antiscia", contra)):
                    orb = _angular_distance(float(reference_longitude), float(target_longitude))
                    if orb > ADVANCED_ANTISCIA_ORB:
                        continue
                    orb_fraction = round(_clamp(1.0 - (orb / ADVANCED_ANTISCIA_ORB), 0.0, 1.0), 4)
                    record = {
                        "record_type": "advanced_antiscia_contact",
                        "source_person": source_label,
                        "source_body": source_body,
                        "target_person": target_label,
                        "target_body": target_body,
                        "relation": relation,
                        "reference_longitude": round(reference_longitude % 360.0, 4),
                        "orb": round(orb, 4),
                        "max_orb": round(ADVANCED_ANTISCIA_ORB, 4),
                        "orb_fraction": orb_fraction,
                        "confidence_state": confidence_state,
                        "salience": round(
                            BODY_WEIGHTS.get(source_body, 0.75)
                            * BODY_WEIGHTS.get(target_body, 0.75)
                            * (0.92 if relation == "antiscia" else 0.82)
                            * orb_fraction
                            * _confidence_score(confidence_state),
                            4,
                        ),
                    }
                    antiscia_contacts.append(record)

    midpoint_contacts.sort(
        key=lambda item: (
            str(item.get("target_person") or ""),
            -float(item.get("salience", 0.0) or 0.0),
            float(item.get("orb", 99.0) or 99.0),
            str(item.get("midpoint_key") or ""),
            str(item.get("source_body") or ""),
        )
    )
    antiscia_contacts.sort(
        key=lambda item: (
            str(item.get("source_person") or ""),
            -float(item.get("salience", 0.0) or 0.0),
            float(item.get("orb", 99.0) or 99.0),
            str(item.get("relation") or ""),
            str(item.get("source_body") or ""),
            str(item.get("target_body") or ""),
        )
    )

    return {
        "record_type": "advanced_static_evidence",
        "techniques": {
            "midpoint_contacts": {
                "active": True,
                "midpoints": sorted(ADVANCED_MIDPOINT_SPECS),
                "orb": ADVANCED_MIDPOINT_ORB,
                "aspects": ["Conjunction", "Opposition"],
            },
            "antiscia_contacts": {
                "active": True,
                "orb": ADVANCED_ANTISCIA_ORB,
                "relations": ["antiscia", "contra_antiscia"],
            },
            "declination_contacts": {
                "active": False,
                "reason": "declination_not_in_payload",
            },
        },
        "midpoint_contacts": midpoint_contacts,
        "antiscia_contacts": antiscia_contacts,
        "status": {
            "midpoint_contacts": LIVE_STATUS,
            "antiscia_contacts": LIVE_STATUS,
            "declination_contacts": NOT_IMPLEMENTED,
        },
    }


def compute_relationship_topic_signatures(
    mutual_aspects: list[dict[str, Any]],
    house_overlays: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregates synastry evidence into relationship topic signatures."""
    signatures = []
    live_overlays = [record for record in house_overlays if not record.get("withheld")]
    for signature_key, spec in TOPIC_SPECS.items():
        contributing_records: list[dict[str, Any]] = []
        family_scores: defaultdict[str, float] = defaultdict(float)
        polarity_counts = {"supportive": 0, "tensional": 0, "mixed": 0}
        confidence_states = []
        localization_types = set()

        for mutual in mutual_aspects:
            bodies = {entry["body"] for entry in mutual.get("mutual_key", [])}
            if not (bodies & spec["bodies"] or bodies & spec["angles"]):
                continue
            family = _topic_family_for_aspect(mutual, spec)
            polarity = ASPECT_POLARITY.get(mutual.get("aspect"), "mixed")
            polarity_counts[polarity] += 1
            confidence_states.append(mutual.get("confidence_state", UNKNOWN_BIRTH_TIME))
            localization_types.add(_localization_type(mutual.get("dependency")))
            family_scores[family] += mutual.get("salience", 0.0)
            contributing_records.append(_topic_aspect_reference(mutual, family, polarity))

        for overlay in live_overlays:
            source_body = overlay.get("source_body")
            target_house = overlay.get("target_house")
            if source_body not in spec["bodies"] and target_house not in spec["houses"]:
                continue
            family = _topic_family_for_overlay(overlay, spec)
            confidence_states.append(overlay.get("confidence_state", UNKNOWN_BIRTH_TIME))
            localization_types.add("house_localized")
            family_scores[family] += BODY_WEIGHTS.get(source_body, 0.75) * 0.35
            polarity_counts["mixed"] += 1
            contributing_records.append(_topic_overlay_reference(overlay, family))

        if not contributing_records:
            continue

        evidence_score = _topic_score(family_scores)
        signatures.append(
            {
                "record_type": "relationship_topic_signature",
                "signature_key": signature_key,
                "topic_label": spec["label"],
                "contributing_records": contributing_records,
                "supportive_tensional_mixed_distribution": polarity_counts,
                "confidence_by_evidence_family": {
                    family: _family_confidence(family, contributing_records)
                    for family in sorted(family_scores)
                },
                "evidence_family_scores": {
                    family: round(score, 4)
                    for family, score in sorted(family_scores.items())
                },
                "evidence_count": len(contributing_records),
                "independent_evidence_families": sorted(family_scores),
                "localization": _signature_localization(localization_types),
                "confidence_state": _least_precise_state(*confidence_states),
                "score": evidence_score,
                "polarity": _dominant_polarity(polarity_counts),
            }
        )

    signatures.sort(key=lambda item: (-item["score"], item["signature_key"]))
    return signatures


def compute_relationship_convergence(
    topic_signatures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ranks topic signatures without producing compatibility verdicts."""
    convergence = []
    for signature in topic_signatures:
        family_count = len(signature.get("independent_evidence_families", []))
        count_modifier = min(1.0, signature.get("evidence_count", 0) / 6.0)
        family_modifier = min(1.0, family_count / 3.0)
        confidence_modifier = _confidence_score(signature.get("confidence_state", UNKNOWN_BIRTH_TIME))
        score = (
            signature.get("score", 0.0) * 0.62
            + count_modifier * 0.18
            + family_modifier * 0.12
            + confidence_modifier * 0.08
        )
        convergence.append(
            {
                "record_type": "relationship_convergence",
                "signature_key": signature["signature_key"],
                "score": round(_clamp(score, 0.0, 1.0), 4),
                "polarity": signature["polarity"],
                "evidence_count": signature["evidence_count"],
                "independent_evidence_families": signature["independent_evidence_families"],
                "confidence_state": signature["confidence_state"],
                "trace": signature["contributing_records"],
            }
        )
    convergence.sort(key=lambda item: (-item["score"], item["signature_key"]))
    return convergence


def _scan_composite_aspects(bodies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    usable_bodies = [
        body
        for body in bodies
        if not body.get("ambiguous") and isinstance(body.get("longitude"), (int, float))
    ]
    aspects = []
    for index, body_a in enumerate(usable_bodies):
        for body_b in usable_bodies[index + 1:]:
            match = _best_aspect_match(body_a["longitude"], body_b["longitude"])
            if not match:
                continue
            aspects.append(
                {
                    "record_type": "composite_aspect",
                    "body_1": body_a["body"],
                    "body_2": body_b["body"],
                    "aspect": match["aspect"],
                    "exact_angle": match["exact_angle"],
                    "measured_distance": match["measured_distance"],
                    "orb": match["orb"],
                    "max_orb": match["max_orb"],
                    "orb_fraction": match["orb_fraction"],
                    "composite_method": COMPOSITE_METHOD,
                    "confidence_state": EXACT_BIRTH_TIME,
                }
            )
    aspects.sort(key=lambda item: (-item["orb_fraction"], item["orb"], item["body_1"], item["body_2"]))
    return aspects


def _bodies_with_sign(
    payload: dict[str, Any],
    body_names: tuple[str, ...],
    sign: str,
) -> list[dict[str, Any]]:
    return [
        {"body": body_name, "sign": sign, "longitude": _body_longitude(payload, body_name)}
        for body_name in body_names
        if _body_sign(payload, body_name) == sign
    ]


def _bodies_in_signs(
    payload: dict[str, Any],
    body_names: tuple[str, ...],
    signs: set[str],
) -> list[dict[str, Any]]:
    bodies = []
    for body_name in body_names:
        sign = _body_sign(payload, body_name)
        if sign in signs:
            bodies.append(
                {
                    "body": body_name,
                    "sign": sign,
                    "longitude": _body_longitude(payload, body_name),
                }
            )
    return bodies


def _bodies_in_house(
    payload: dict[str, Any],
    body_names: tuple[str, ...],
    house_number: int,
) -> list[dict[str, Any]]:
    bodies = []
    for body_name in body_names:
        body = payload.get("standard_planets", {}).get(body_name)
        if not isinstance(body, dict) or body.get("house") != house_number:
            continue
        bodies.append(
            {
                "body": body_name,
                "house": house_number,
                "longitude": _body_longitude(payload, body_name),
            }
        )
    return bodies


def _repeated_theme_record(
    *,
    theme_key: str,
    theme_type: str,
    person_a_evidence: dict[str, Any],
    person_b_evidence: dict[str, Any],
    confidence_state: str,
    salience: float,
) -> dict[str, Any]:
    return {
        "record_type": "repeated_theme",
        "theme_key": theme_key,
        "theme_type": theme_type,
        "person_a_evidence": person_a_evidence,
        "person_b_evidence": person_b_evidence,
        "confidence_state": confidence_state,
        "salience": round(_clamp(salience, 0.0, 1.0), 4),
    }


def _bounded_theme_salience(count_a: int, count_b: int, denominator: int) -> float:
    shared_strength = min(count_a, count_b) / max(1, denominator)
    balance = min(count_a, count_b) / max(count_a, count_b)
    return _clamp((shared_strength * 0.75) + (balance * 0.25), 0.0, 1.0)


def _aspect_family_set(payload: dict[str, Any], body_names: tuple[str, ...]) -> set[str]:
    allowed = set(body_names)
    families = set()
    for aspect in payload.get("aspects", []):
        body_a = aspect.get("body_1")
        body_b = aspect.get("body_2")
        aspect_name = aspect.get("aspect")
        if body_a not in allowed or body_b not in allowed or not isinstance(aspect_name, str):
            continue
        first, second = sorted((body_a, body_b))
        families.add(f"{first}|{second}|{aspect_name}")
    return families


def _topic_family_for_aspect(mutual: dict[str, Any], spec: dict[str, Any]) -> str:
    bodies = {entry["body"] for entry in mutual.get("mutual_key", [])}
    for body_name in sorted(bodies & spec["bodies"]):
        return f"{body_name.lower()}_contacts"
    for angle_name in sorted(bodies & spec["angles"]):
        return f"{angle_name.lower()}_angle_contact"
    return "general_contacts"


def _topic_family_for_overlay(overlay: dict[str, Any], spec: dict[str, Any]) -> str:
    source_body = overlay.get("source_body")
    if source_body in spec["bodies"]:
        return f"{str(source_body).lower()}_overlay"
    house = overlay.get("target_house")
    return {
        3: "third_house_overlay",
        4: "fourth_house_overlay",
        8: "eighth_house_overlay",
        9: "ninth_house_overlay",
        10: "tenth_house_overlay",
    }.get(house, f"house_{house}_overlay")


def _topic_aspect_reference(
    mutual: dict[str, Any],
    family: str,
    polarity: str,
) -> dict[str, Any]:
    return {
        "record_type": "mutual_aspect_reference",
        "evidence_family": family,
        "polarity": polarity,
        "mutual_key": mutual.get("mutual_key", []),
        "aspect": mutual.get("aspect"),
        "orb": mutual.get("orb"),
        "salience": mutual.get("salience", 0.0),
        "dependency": mutual.get("dependency"),
        "confidence_state": mutual.get("confidence_state"),
    }


def _topic_overlay_reference(
    overlay: dict[str, Any],
    family: str,
) -> dict[str, Any]:
    return {
        "record_type": "house_overlay_reference",
        "evidence_family": family,
        "polarity": "mixed",
        "source_person": overlay.get("source_person"),
        "source_body": overlay.get("source_body"),
        "target_person": overlay.get("target_person"),
        "target_house": overlay.get("target_house"),
        "target_house_sign": overlay.get("target_house_sign"),
        "confidence_state": overlay.get("confidence_state"),
    }


def _topic_score(family_scores: dict[str, float]) -> float:
    if not family_scores:
        return 0.0
    strongest = max(family_scores.values())
    breadth = min(1.0, len(family_scores) / 3.0)
    total = min(1.0, sum(family_scores.values()) / 3.0)
    return round(_clamp(strongest * 0.55 + breadth * 0.25 + total * 0.20, 0.0, 1.0), 4)


def _family_confidence(
    family: str,
    records: list[dict[str, Any]],
) -> str:
    states = [
        record.get("confidence_state", UNKNOWN_BIRTH_TIME)
        for record in records
        if record.get("evidence_family") == family
    ]
    return _least_precise_state(*states)


def _localization_type(dependency: str | None) -> str:
    if dependency and dependency != "body_to_body":
        return "angle_localized"
    return "body_only"


def _signature_localization(localization_types: set[str]) -> str:
    if "house_localized" in localization_types:
        return "house_localized"
    if "angle_localized" in localization_types:
        return "angle_localized"
    return "body_only"


def _dominant_polarity(polarity_counts: dict[str, int]) -> str:
    total = sum(polarity_counts.values())
    if total == 0:
        return "mixed"
    if polarity_counts["supportive"] > polarity_counts["tensional"] and polarity_counts["supportive"] >= polarity_counts["mixed"]:
        return "supportive"
    if polarity_counts["tensional"] > polarity_counts["supportive"] and polarity_counts["tensional"] >= polarity_counts["mixed"]:
        return "tensional"
    return "mixed"


def _confidence_score(state: str) -> float:
    return {
        EXACT_BIRTH_TIME: 1.0,
        APPROXIMATE_BIRTH_TIME: 0.85,
        PROVISIONAL_NEAR_HORIZON: 0.75,
        UNKNOWN_BIRTH_TIME: 0.55,
        ANGLE_DEPENDENT_UNAVAILABLE: 0.0,
    }.get(state, 0.0)


def _person_record(label: str, natal_payload: dict[str, Any]) -> dict[str, Any]:
    state = _birth_time_state(natal_payload)
    return {
        "label": label,
        "natal_payload": natal_payload,
        "birth_time_state": state,
        "angle_eligible": _is_angle_eligible(state),
    }


def _birth_time_state(payload: dict[str, Any]) -> str:
    profile = payload.get("user_profile", {})
    raw_state = (
        profile.get("birth_time_state")
        or profile.get("birth_time_confidence")
        or payload.get("birth_time_state")
    )
    if raw_state in {
        EXACT_BIRTH_TIME,
        APPROXIMATE_BIRTH_TIME,
        UNKNOWN_BIRTH_TIME,
        PROVISIONAL_NEAR_HORIZON,
    }:
        return raw_state
    if raw_state == "exact":
        return EXACT_BIRTH_TIME
    if raw_state in {"approximate", "approximate_birth_time"}:
        return APPROXIMATE_BIRTH_TIME
    if raw_state in {"unknown", "unknown_birth_time"}:
        return UNKNOWN_BIRTH_TIME
    if bool(profile.get("simple_mode") or payload.get("simple_mode")):
        return UNKNOWN_BIRTH_TIME
    return EXACT_BIRTH_TIME


def _is_angle_eligible(state: str) -> bool:
    return state in {EXACT_BIRTH_TIME, APPROXIMATE_BIRTH_TIME, PROVISIONAL_NEAR_HORIZON}


def _payload_id(payload: dict[str, Any], fallback: str) -> str:
    profile = payload.get("user_profile", {})
    for key in ("payload_id", "chart_id", "name", "report_name"):
        value = profile.get(key) or payload.get(key)
        if value:
            return str(value)
    local_datetime = profile.get("local_datetime")
    location = profile.get("resolved_location") or payload.get("birth_location")
    if local_datetime or location:
        return f"{fallback}:{local_datetime or 'unknown_time'}:{location or 'unknown_location'}"
    return fallback


def _pair_body_names(people: dict[str, dict[str, Any]]) -> tuple[str, ...]:
    names = [
        body_name
        for body_name in CORE_BODIES
        if any(_body_longitude(person["natal_payload"], body_name) is not None for person in people.values())
    ]
    for body_name in OPTIONAL_BODIES:
        if all(_body_longitude(person["natal_payload"], body_name) is not None for person in people.values()):
            names.append(body_name)
    return tuple(names)


def _eligible_points(person: dict[str, Any], body_names: tuple[str, ...]) -> list[dict[str, Any]]:
    return _body_points(person, body_names) + _angle_points(person)


def _body_points(person: dict[str, Any], body_names: tuple[str, ...]) -> list[dict[str, Any]]:
    payload = person["natal_payload"]
    points = []
    for body_name in body_names:
        longitude = _body_longitude(payload, body_name)
        if longitude is None:
            continue
        points.append(
            {
                "name": body_name,
                "kind": "body",
                "longitude": longitude,
                "owner": person["label"],
                "owner_angle_eligible": person["angle_eligible"],
            }
        )
    return points


def _angle_points(person: dict[str, Any]) -> list[dict[str, Any]]:
    payload = person["natal_payload"]
    points = []
    for angle_name in ANGLE_POINTS:
        longitude = _angle_longitude(payload, angle_name)
        if longitude is None and not person["angle_eligible"]:
            longitude = 0.0
        if longitude is None:
            continue
        points.append(
            {
                "name": angle_name,
                "kind": "angle",
                "longitude": longitude,
                "owner": person["label"],
                "owner_angle_eligible": person["angle_eligible"],
            }
        )
    return points


def _body_longitude(payload: dict[str, Any], body_name: str) -> float | None:
    body = payload.get("standard_planets", {}).get(body_name)
    if isinstance(body, dict) and isinstance(body.get("longitude"), (int, float)):
        return float(body["longitude"]) % 360.0
    return None


def _body_sign(payload: dict[str, Any], body_name: str) -> str | None:
    body = payload.get("standard_planets", {}).get(body_name)
    if isinstance(body, dict) and isinstance(body.get("sign"), str):
        return body["sign"]
    longitude = _body_longitude(payload, body_name)
    if longitude is None:
        return None
    return SIGNS[int((longitude % 360.0) // 30.0)]


def _available_body_names(payload: dict[str, Any]) -> tuple[str, ...]:
    names = [body_name for body_name in CORE_BODIES if _body_longitude(payload, body_name) is not None]
    for body_name in OPTIONAL_BODIES:
        if _body_longitude(payload, body_name) is not None:
            names.append(body_name)
    return tuple(names)


def _midpoint_longitude(
    longitude_a: float,
    longitude_b: float,
    *,
    ambiguity_epsilon: float = 1e-6,
) -> float | None:
    delta = ((longitude_b - longitude_a + 540.0) % 360.0) - 180.0
    if abs(abs(delta) - 180.0) <= ambiguity_epsilon:
        return None
    return round((longitude_a + (delta / 2.0)) % 360.0, 4)


def _midpoint_definitions(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for key, bodies in ADVANCED_MIDPOINT_SPECS.items():
        first, second = bodies
        lon_a = _body_longitude(payload, first)
        lon_b = _body_longitude(payload, second)
        if lon_a is None or lon_b is None:
            continue
        midpoint = _midpoint_longitude(lon_a, lon_b)
        if midpoint is None:
            continue
        records[key] = {
            "bodies": bodies,
            "longitude": midpoint,
        }
    return records


def _antiscia_longitude(longitude: float) -> float:
    return round((180.0 - float(longitude)) % 360.0, 4)


def _angle_longitude(payload: dict[str, Any], angle_name: str) -> float | None:
    angle = payload.get("angles", {}).get(angle_name)
    if isinstance(angle, dict) and isinstance(angle.get("longitude"), (int, float)):
        return float(angle["longitude"]) % 360.0
    return None


def _angle_unavailable_reason(
    source_point: dict[str, Any],
    target_point: dict[str, Any],
) -> dict[str, Any] | None:
    missing_inputs = []
    for point in (source_point, target_point):
        if point["kind"] == "angle" and not point["owner_angle_eligible"]:
            missing_inputs.append(f"{point['owner']}.birth_time")
    if not missing_inputs:
        return None
    return {
        "confidence_state": ANGLE_DEPENDENT_UNAVAILABLE,
        "withheld_reason": WITHHELD_ANGLE_DEPENDENCY,
        "missing_inputs": sorted(set(missing_inputs)),
    }


def _withheld_angle_aspect_record(
    source_label: str,
    source_point: dict[str, Any],
    target_label: str,
    target_point: dict[str, Any],
    unavailable: dict[str, Any],
) -> dict[str, Any]:
    return {
        "record_type": "directional_aspect",
        "source_person": source_label,
        "source_body": source_point["name"],
        "target_person": target_label,
        "target_body": target_point["name"],
        "aspect": None,
        "exact_angle": None,
        "measured_distance": None,
        "orb": None,
        "max_orb": ORB_CONFIG["max_orb_synastry"],
        "orb_fraction": 0.0,
        "source_domain": BODY_DOMAINS.get(source_point["name"], "unspecified"),
        "target_domain": BODY_DOMAINS.get(target_point["name"], "unspecified"),
        "directional_dependency": "angle_dependent",
        "confidence_state": unavailable["confidence_state"],
        "withheld": True,
        "withheld_reason": unavailable["withheld_reason"],
        "missing_inputs": unavailable["missing_inputs"],
    }


def _best_aspect_match(longitude_a: float, longitude_b: float) -> dict[str, Any] | None:
    distance = _angular_distance(longitude_a, longitude_b)
    max_orb = float(ORB_CONFIG["max_orb_synastry"])
    best = None
    for aspect_name, exact_angle in MAJOR_ASPECTS:
        orb = abs(distance - float(exact_angle))
        if orb > max_orb:
            continue
        orb_fraction = _clamp(1.0 - (orb / max_orb), 0.0, 1.0)
        candidate = {
            "aspect": aspect_name,
            "exact_angle": float(exact_angle),
            "measured_distance": round(distance, 4),
            "orb": round(orb, 4),
            "max_orb": round(max_orb, 4),
            "orb_fraction": round(orb_fraction, 4),
        }
        if best is None or (candidate["orb"], -candidate["orb_fraction"]) < (best["orb"], -best["orb_fraction"]):
            best = candidate
    return best


def _best_aspect_match_with_orb(longitude_a: float, longitude_b: float, max_orb: float) -> dict[str, Any] | None:
    distance = _angular_distance(longitude_a, longitude_b)
    best = None
    for aspect_name, exact_angle in MAJOR_ASPECTS:
        orb = abs(distance - float(exact_angle))
        if orb > max_orb:
            continue
        orb_fraction = _clamp(1.0 - (orb / max_orb), 0.0, 1.0)
        candidate = {
            "aspect": aspect_name,
            "exact_angle": float(exact_angle),
            "measured_distance": round(distance, 4),
            "orb": round(orb, 4),
            "max_orb": round(max_orb, 4),
            "orb_fraction": round(orb_fraction, 4),
        }
        if best is None or (candidate["orb"], -candidate["orb_fraction"]) < (best["orb"], -best["orb_fraction"]):
            best = candidate
    return best


def _directional_dependency(
    source_point: dict[str, Any],
    target_point: dict[str, Any],
) -> str:
    if source_point["kind"] == "angle" and target_point["kind"] == "angle":
        return "angle_to_angle"
    if source_point["kind"] == "angle" or target_point["kind"] == "angle":
        return "angle_dependent"
    return "body_to_body"


def _aspect_confidence_state(
    source: dict[str, Any],
    target: dict[str, Any],
    dependency: str,
) -> str:
    if dependency != "body_to_body":
        if source["birth_time_state"] == UNKNOWN_BIRTH_TIME or target["birth_time_state"] == UNKNOWN_BIRTH_TIME:
            return ANGLE_DEPENDENT_UNAVAILABLE
        return _least_precise_state(source["birth_time_state"], target["birth_time_state"])
    return _least_precise_state(source["birth_time_state"], target["birth_time_state"])


def _least_precise_state(*states: str) -> str:
    if not states:
        return UNKNOWN_BIRTH_TIME
    priority = {
        UNKNOWN_BIRTH_TIME: 0,
        PROVISIONAL_NEAR_HORIZON: 1,
        APPROXIMATE_BIRTH_TIME: 2,
        EXACT_BIRTH_TIME: 3,
    }
    return min(states, key=lambda state: priority.get(state, 0))


def _mutual_confidence_state(records: list[dict[str, Any]]) -> str:
    return _least_precise_state(*(record.get("confidence_state", UNKNOWN_BIRTH_TIME) for record in records))


def _salience(record: dict[str, Any], confidence_state: str) -> float:
    confidence_modifier = {
        EXACT_BIRTH_TIME: 1.0,
        APPROXIMATE_BIRTH_TIME: 0.9,
        PROVISIONAL_NEAR_HORIZON: 0.85,
        UNKNOWN_BIRTH_TIME: 0.8,
    }.get(confidence_state, 0.0)
    score = (
        BODY_WEIGHTS.get(record["source_body"], 0.75)
        * BODY_WEIGHTS.get(record["target_body"], 0.75)
        * ASPECT_WEIGHTS.get(record["aspect"], 0.75)
        * record.get("orb_fraction", 0.0)
        * confidence_modifier
    )
    return round(score, 4)


def _directional_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("withheld", False),
        record.get("source_person"),
        record.get("target_person"),
        record.get("source_body"),
        record.get("target_body"),
        record.get("orb") if record.get("orb") is not None else 999.0,
    )


def _angular_distance(longitude_a: float, longitude_b: float) -> float:
    difference = abs((longitude_a - longitude_b) % 360.0)
    return min(difference, 360.0 - difference)


def _whole_sign_house(longitude: float, ascendant_longitude: float) -> int:
    body_sign_index = int((longitude % 360.0) // 30.0)
    ascendant_sign_index = int((ascendant_longitude % 360.0) // 30.0)
    return ((body_sign_index - ascendant_sign_index) % 12) + 1


def _sign_for_house(ascendant_longitude: float, house_number: int) -> str:
    ascendant_sign_index = int((ascendant_longitude % 360.0) // 30.0)
    return SIGNS[(ascendant_sign_index + house_number - 1) % 12]


def _zodiac_position(longitude: float) -> dict[str, Any]:
    longitude = longitude % 360.0
    sign_index = int(longitude // 30.0)
    degree_decimal = longitude % 30.0
    return {
        "sign": SIGNS[sign_index],
        "degree": int(degree_decimal),
        "minute": int((degree_decimal % 1.0) * 60.0),
        "degree_decimal": round(degree_decimal, 4),
    }


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _build_sidecar(withheld_records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "formula_version": FORMULA_VERSION,
        "computation_status": {
            "pair_payload": LIVE_STATUS,
            "directional_aspects": LIVE_STATUS,
            "mutual_aspects": LIVE_STATUS,
            "house_overlays": LIVE_STATUS,
            "composite_midpoint_bodies": LIVE_STATUS,
            "composite_aspects": LIVE_STATUS,
            "composite_to_natal_resonance": LIVE_STATUS,
            "advanced_static_evidence": LIVE_STATUS,
            "composite_houses": NOT_IMPLEMENTED,
            "davison": NOT_IMPLEMENTED,
            "repeated_natal_themes": LIVE_STATUS,
            "relationship_topic_signatures": LIVE_STATUS,
            "relationship_convergence": LIVE_STATUS,
            "relationship_timing": NOT_IMPLEMENTED,
        },
        "withheld_summary": {
            "total": len(withheld_records),
            "by_reason": dict(_count_by_reason(withheld_records)),
        },
        "claim_safety": {
            "client_report_available": False,
            "relationship_verdicts_supported": False,
            "notes": [
                "This payload is an evidence layer, not a relationship verdict.",
                "Report surfaces must read sidecar statuses before claiming a synastry layer is live.",
            ],
        },
    }


def _count_by_reason(records: list[dict[str, Any]]) -> defaultdict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    for record in records:
        counts[record.get("withheld_reason", "unspecified")] += 1
    return counts
