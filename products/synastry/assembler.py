"""
Round-1 synastry context assembly.

This module turns the synastry pair payload into a structured draft context
that exercises the authored prose libraries without claiming a finished client
product surface.
"""
from __future__ import annotations

import copy
from typing import Any

from engine.synastry import ANGLE_POINTS, BODY_WEIGHTS, TOPIC_SPECS, build_pair_payload
from products.synastry.compiler import SynastryNarrativeCompiler
from selectors.synastry_selector import (
    classify_body_pair_family,
    select_body_pair_family_leaf,
    select_composite_ambiguity_leaf,
    select_composite_aspect_leaf,
    select_composite_body_midpoint_leaf,
    select_composite_unsupported_layer_leaf,
    select_directional_aspect_leaf,
    select_exact_body_pair_leaf,
    select_house_overlay_confidence_leaf,
    select_house_overlay_intersection_leaf,
    select_house_overlay_source_body_leaf,
    select_house_overlay_target_house_leaf,
    select_repeated_theme_confidence_leaf,
    select_repeated_theme_type_leaf,
    select_technical_appendix_leaf,
    select_topic_confidence_leaf,
    select_topic_convergence_leaf,
    select_topic_polarity_leaf,
    select_topic_signature_leaf,
)


CONTEXT_VERSION = "synastry_context_v0.2.0"
REPORT_TYPE = "synastry.narrative_preview"
PRODUCT_NAME = "Synastry Narrative Preview"
ANGLE_SET = set(ANGLE_POINTS)
MUTUAL_HIGHLIGHT_LIMIT = 6
TOPIC_HIGHLIGHT_LIMIT = 4
HOUSE_OVERLAY_LIMIT = 8
REPEATED_THEME_LIMIT = 5
COMPOSITE_BODY_LIMIT = 8
COMPOSITE_ASPECT_LIMIT = 6
REPEATED_ASPECT_FAMILY_LIMIT = 2


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _fallback_person_name(fallback_label: str) -> str:
    return "Person A" if fallback_label == "A" else "Person B"


def _is_internal_fixture_name(value: str) -> bool:
    return str(value or "").strip().lower().startswith("synastry fixture")


def _clean_display_name(value: Any, fallback_label: str) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or _is_internal_fixture_name(stripped):
        return None
    return stripped


def _display_name(person_record: dict, fallback_label: str, relationship_meta: dict | None = None) -> str:
    relationship_meta = relationship_meta or {}
    meta_key = "person_a_label" if fallback_label == "A" else "person_b_label"
    meta_name = _clean_display_name(relationship_meta.get(meta_key), fallback_label)
    if meta_name:
        return meta_name
    profile = (person_record.get("natal_payload") or {}).get("user_profile", {})
    for key in ("name", "report_name", "display_name"):
        value = _clean_display_name(profile.get(key), fallback_label)
        if value:
            return value
    return _fallback_person_name(fallback_label)


def _person_names(pair_payload: dict) -> dict[str, str]:
    relationship_meta = pair_payload.get("relationship_meta") or {}
    return {
        "A": _display_name(pair_payload.get("person_a") or {}, "A", relationship_meta),
        "B": _display_name(pair_payload.get("person_b") or {}, "B", relationship_meta),
    }


def _body_phrase(entry: dict, names: dict[str, str]) -> str:
    person = entry.get("person")
    body = entry.get("body")
    return f"{names.get(person, person)}'s {body}"


def _mutual_contains_non_angle_body(mutual: dict) -> bool:
    return any(
        isinstance(entry, dict) and entry.get("body") not in ANGLE_SET
        for entry in mutual.get("mutual_key", []) or []
    )


def _mutual_sort_key(mutual: dict) -> tuple[Any, ...]:
    bodies = [entry.get("body") for entry in mutual.get("mutual_key", []) or []]
    body_weight = max(BODY_WEIGHTS.get(body, 0.0) for body in bodies if isinstance(body, str)) if bodies else 0.0
    return (
        not _mutual_contains_non_angle_body(mutual),
        -float(mutual.get("salience", 0.0)),
        -body_weight,
        float(mutual.get("orb", 99.0) or 99.0),
    )


def _is_pure_angle_mutual(mutual: dict) -> bool:
    entries = mutual.get("mutual_key", []) or []
    bodies = [entry.get("body") for entry in entries if isinstance(entry, dict)]
    return bool(bodies) and all(body in ANGLE_SET for body in bodies)


def _mutual_bodies(mutual: dict) -> list[str]:
    return [
        entry.get("body")
        for entry in mutual.get("mutual_key", []) or []
        if isinstance(entry, dict) and isinstance(entry.get("body"), str)
    ]


def _mutual_family(mutual: dict) -> str:
    return classify_body_pair_family(_mutual_bodies(mutual))


def _mutual_editorial_score(mutual: dict) -> float:
    salience = float(mutual.get("salience", 0.0) or 0.0)
    dependency = str(mutual.get("dependency") or "")
    family = _mutual_family(mutual)
    score = salience
    if dependency == "body_to_body":
        score += 0.35
    elif dependency == "angle_dependent":
        score -= 0.12
    if _is_pure_angle_mutual(mutual):
        score -= 1.1
    if family == "node_or_chiron_contact":
        score -= 0.45
    bodies = _mutual_bodies(mutual)
    if {"Sun", "Moon"} & set(bodies):
        score += 0.15
    if {"Venus", "Mars", "Mercury"} & set(bodies):
        score += 0.1
    return score


def _normalize_confidence_state(state: str | None) -> str:
    return str(state or "fallback")


def _sentence_join(parts: list[str]) -> str:
    clean = [str(part).strip() for part in parts if isinstance(part, str) and part.strip()]
    return " ".join(clean)


def _indefinite_article(phrase: str | None) -> str:
    text = str(phrase or "").strip().lower()
    if not text:
        return "a"
    return "an" if text[0] in {"a", "e", "i", "o", "u"} else "a"


def _ordinal(number: int | None) -> str:
    if not isinstance(number, int):
        return ""
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _aspect_item(mutual: dict, names: dict[str, str]) -> dict:
    entries = mutual.get("mutual_key", []) or []
    bodies = [entry.get("body") for entry in entries if isinstance(entry, dict)]
    aspect = mutual.get("aspect")
    dependency = mutual.get("dependency")
    polarity = select_polarity_for_aspect(aspect)
    family = classify_body_pair_family(bodies)

    aspect_leaf = select_directional_aspect_leaf(aspect, dependency, polarity)
    exact_pair_leaf = select_exact_body_pair_leaf(bodies) if dependency == "body_to_body" else None
    family_leaf = select_body_pair_family_leaf(family) if exact_pair_leaf is None else None
    title = " - ".join(_body_phrase(entry, names) for entry in entries) + f" ({aspect})"
    mutual_key_id = "|".join(
        f"{entry.get('person')}:{entry.get('body')}"
        for entry in entries
        if isinstance(entry, dict)
    )
    body = _sentence_join(
        [
            (
                f"{_body_phrase(entries[0], names)} and {_body_phrase(entries[1], names)} "
                f"form {_indefinite_article(aspect)} {aspect.lower()} in the live synastry evidence."
            )
            if len(entries) >= 2 and aspect
            else ""
            ,
            aspect_leaf.get("body"),
            exact_pair_leaf.get("body") if exact_pair_leaf else "",
            family_leaf.get("body") if family_leaf else "",
        ]
    )
    return {
        "id": f"mutual:{mutual_key_id}:{aspect}",
        "title": title,
        "body": body,
        "source": _deepcopy(mutual),
        "selected_leaves": {
            "aspect": aspect_leaf,
            "exact_body_pair": exact_pair_leaf,
            "body_pair_family": family_leaf,
        },
        "metadata": {
            "aspect": aspect,
            "dependency": dependency,
            "polarity": polarity,
            "confidence_state": mutual.get("confidence_state"),
            "salience": mutual.get("salience"),
            "orb": mutual.get("orb"),
        },
    }


def _overlay_item(overlay: dict, names: dict[str, str]) -> dict:
    source_name = names.get(overlay.get("source_person"), overlay.get("source_person"))
    target_name = names.get(overlay.get("target_person"), overlay.get("target_person"))
    intersection_leaf = select_house_overlay_intersection_leaf(overlay.get("source_body"), overlay.get("target_house"))
    source_body_leaf = select_house_overlay_source_body_leaf(overlay.get("source_body"))
    house_leaf = select_house_overlay_target_house_leaf(overlay.get("target_house"))
    confidence_leaf = select_house_overlay_confidence_leaf(
        overlay.get("confidence_state"),
        withheld=bool(overlay.get("withheld")),
    )
    house_label = _ordinal(overlay.get("target_house"))
    title = f"{source_name}'s {overlay.get('source_body')} in {target_name}'s House {overlay.get('target_house')}"
    body = _sentence_join(
        [
            f"{source_name}'s {overlay.get('source_body')} falls in {target_name}'s {house_label} house"
            + (f" in {overlay.get('target_house_sign')}." if overlay.get("target_house_sign") else "."),
            intersection_leaf.get("body") if intersection_leaf else "",
            source_body_leaf.get("body") if intersection_leaf is None else "",
            house_leaf.get("body") if intersection_leaf is None else "",
            confidence_leaf.get("body"),
        ]
    )
    return {
        "id": f"overlay:{overlay.get('source_person')}:{overlay.get('source_body')}:{overlay.get('target_person')}:{overlay.get('target_house')}",
        "title": title,
        "body": body,
        "source": _deepcopy(overlay),
        "selected_leaves": {
            "body_house_intersection": intersection_leaf,
            "source_body": source_body_leaf,
            "target_house": house_leaf,
            "confidence": confidence_leaf,
        },
        "metadata": {
            "confidence_state": overlay.get("confidence_state"),
            "target_house_sign": overlay.get("target_house_sign"),
        },
    }


def _describe_repeated_theme(theme: dict) -> str:
    theme_type = theme.get("theme_type")
    if theme_type == "same_sign_emphasis":
        sign = (theme.get("person_a_evidence") or {}).get("sign")
        return f"Both charts concentrate multiple included bodies in {sign}."
    if theme_type == "same_element_concentration":
        element = (theme.get("person_a_evidence") or {}).get("element")
        return f"Both charts repeat a strong {element} emphasis."
    if theme_type == "same_modality_concentration":
        modality = (theme.get("person_a_evidence") or {}).get("modality")
        return f"Both charts repeat a {modality} pacing pattern."
    if theme_type == "repeated_aspect_family":
        evidence = theme.get("person_a_evidence") or {}
        body_1 = _pretty_body_token(str(evidence.get("body_1") or ""))
        body_2 = _pretty_body_token(str(evidence.get("body_2") or ""))
        aspect = str(evidence.get("aspect") or "").lower()
        if body_1 and body_2 and aspect:
            return (
                f"Both charts already carry a natal {body_1} / {body_2} {aspect} pattern,"
                " so the relationship is meeting structure each person was already carrying alone."
            )
        return "Both charts already repeat a closely related natal aspect pattern before the synastry contact is even added."
    if theme_type == "shared_house_emphasis":
        house = (theme.get("person_a_evidence") or {}).get("house")
        return f"Both charts place emphasis in the {_ordinal(house)} house."
    return f"Both charts repeat the natal pattern keyed as {theme.get('theme_key')}."


def _pretty_body_token(token: str) -> str:
    mapping = {
        "north": "North",
        "south": "South",
        "node": "Node",
        "chiron": "Chiron",
        "pluto": "Pluto",
        "venus": "Venus",
        "mercury": "Mercury",
        "mars": "Mars",
        "moon": "Moon",
        "sun": "Sun",
        "saturn": "Saturn",
        "jupiter": "Jupiter",
        "uranus": "Uranus",
        "neptune": "Neptune",
    }
    return mapping.get(token.lower(), token.replace("_", " ").title())


def _format_repeated_theme_title(theme: dict) -> str:
    theme_type = theme.get("theme_type")
    evidence_a = theme.get("person_a_evidence") or {}
    if theme_type == "same_sign_emphasis":
        return f"Shared {evidence_a.get('sign')} Emphasis"
    if theme_type == "same_element_concentration":
        element = str(evidence_a.get("element") or "").title()
        return f"Shared {element} Emphasis"
    if theme_type == "same_modality_concentration":
        modality = str(evidence_a.get("modality") or "").title()
        return f"Shared {modality} Modality"
    if theme_type == "shared_house_emphasis":
        house = evidence_a.get("house")
        return f"Shared {_ordinal(house).title()} House Emphasis"
    if theme_type == "repeated_aspect_family":
        raw_key = str(theme.get("theme_key") or "")
        tokens = raw_key.removeprefix("shared_").split("_")
        if len(tokens) >= 3:
            aspect = tokens[-1].title()
            left = _pretty_body_token(tokens[0])
            right = " ".join(_pretty_body_token(token) for token in tokens[1:-1])
            if right:
                return f"Shared {left} / {right} {aspect} Pattern"
        return "Shared Natal Aspect Pattern"
    return str(theme.get("theme_key") or "Repeated Natal Theme").replace("_", " ").title()


def _repeated_theme_editorial_score(theme: dict) -> float:
    score = float(theme.get("salience", 0.0) or 0.0)
    theme_type = str(theme.get("theme_type") or "")
    if theme_type != "repeated_aspect_family":
        return score

    evidence = theme.get("person_a_evidence") or {}
    bodies = [str(evidence.get("body_1") or ""), str(evidence.get("body_2") or "")]
    family = classify_body_pair_family(bodies)
    if family == "node_or_chiron_contact":
        score -= 0.18
    elif family == "outer_planet_contact":
        score -= 0.06
    elif family == "luminary_contact":
        score += 0.14
    elif family == "personal_planet_contact":
        score += 0.12
    elif family == "social_planet_contact":
        score += 0.05

    body_set = set(bodies)
    if {"Sun", "Moon"} & body_set:
        score += 0.08
    if {"Mercury", "Venus", "Mars"} & body_set:
        score += 0.05
    return score


def _serial_join(parts: list[str]) -> str:
    clean = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def _repeated_theme_structural_phrase(theme: dict) -> str:
    theme_type = str(theme.get("theme_type") or "")
    evidence = theme.get("person_a_evidence") or {}
    if theme_type == "same_sign_emphasis":
        sign = evidence.get("sign")
        return f"shared {sign} emphasis"
    if theme_type == "same_element_concentration":
        element = str(evidence.get("element") or "").title()
        return f"shared {element} concentration"
    if theme_type == "same_modality_concentration":
        modality = str(evidence.get("modality") or "").lower()
        return f"shared {modality} pacing"
    if theme_type == "shared_house_emphasis":
        house = _ordinal(evidence.get("house"))
        return f"shared {house} house emphasis"
    return ""


def _repeated_theme_aspect_phrase(theme: dict) -> str:
    evidence = theme.get("person_a_evidence") or {}
    body_1 = _pretty_body_token(str(evidence.get("body_1") or ""))
    body_2 = _pretty_body_token(str(evidence.get("body_2") or ""))
    aspect = str(evidence.get("aspect") or "").lower()
    if body_1 and body_2 and aspect:
        return f"a shared {body_1} / {body_2} {aspect} pattern"
    return "a shared natal aspect pattern"


def _repeated_theme_summary_blocks(themes: list[dict]) -> list[dict]:
    blocks = []
    structural_phrases = [
        _repeated_theme_structural_phrase(theme)
        for theme in themes
        if str(theme.get("theme_type") or "") != "repeated_aspect_family"
    ]
    structural_phrases = [phrase for phrase in structural_phrases if phrase]
    if structural_phrases:
        blocks.append(
            {
                "id": "repeated_themes:baseline",
                "title": "Shared Baseline",
                "body": (
                    "Several repeated natal signatures set the baseline atmosphere before the charts even touch directly: "
                    f"{_serial_join(structural_phrases[:3])}. "
                    "That suggests the synastry is being received through some similar habits of emphasis, not through wholly unfamiliar material."
                ),
            }
        )

    aspect_phrases = [
        _repeated_theme_aspect_phrase(theme)
        for theme in themes
        if str(theme.get("theme_type") or "") == "repeated_aspect_family"
    ]
    aspect_phrases = [phrase for phrase in aspect_phrases if phrase]
    if aspect_phrases:
        blocks.append(
            {
                "id": "repeated_themes:aspect_echoes",
                "title": "Recurring Pattern Echoes",
                "body": (
                    "The repeated aspect layer is notable too: both charts already carry "
                    f"{_serial_join(aspect_phrases[:2])}. "
                    "That does not make the relationship predetermined, but it can make certain exchanges feel immediately familiar because each person arrives with related built-in wiring."
                ),
            }
        )

    return blocks


def _repeated_theme_item(theme: dict) -> dict:
    type_leaf = select_repeated_theme_type_leaf(theme.get("theme_type"))
    confidence_leaf = select_repeated_theme_confidence_leaf(theme.get("confidence_state"))
    body = _sentence_join(
        [
            _describe_repeated_theme(theme),
            type_leaf.get("body"),
            confidence_leaf.get("body"),
        ]
    )
    return {
        "id": f"repeated:{theme.get('theme_key')}",
        "title": _format_repeated_theme_title(theme),
        "body": body,
        "source": _deepcopy(theme),
        "selected_leaves": {
            "theme_type": type_leaf,
            "confidence": confidence_leaf,
        },
        "metadata": {
            "theme_type": theme.get("theme_type"),
            "confidence_state": theme.get("confidence_state"),
            "salience": theme.get("salience"),
        },
    }


def _live_topic_records(signature: dict) -> list[dict]:
    live_records = []
    for record in signature.get("contributing_records", []) or []:
        if not isinstance(record, dict):
            continue
        confidence_state = record.get("confidence_state")
        if confidence_state == "angle_dependent_unavailable":
            continue
        if record.get("record_type") == "mutual_aspect_reference" and float(record.get("salience", 0.0) or 0.0) <= 0.0:
            continue
        live_records.append(record)
    return live_records


def _topic_localization_key(signature: dict, convergence: dict | None, live_records: list[dict]) -> str:
    signature_localization = signature.get("localization")
    if isinstance(signature_localization, str) and signature_localization:
        return signature_localization
    convergence_localization = (convergence or {}).get("localization")
    if isinstance(convergence_localization, str) and convergence_localization:
        return convergence_localization
    if any(record.get("record_type") == "house_overlay_reference" for record in live_records):
        return "house_localized"
    if any(record.get("dependency") != "body_to_body" for record in live_records):
        return "angle_localized"
    return "body_only"


def _topic_family_signal(signature: dict, live_records: list[dict]) -> list[str]:
    scores = signature.get("evidence_family_scores") or {}
    families = {record.get("evidence_family") for record in live_records if isinstance(record.get("evidence_family"), str)}
    ordered = sorted(
        families,
        key=lambda family: (-float(scores.get(family, 0.0) or 0.0), family),
    )
    return ordered[:2]


def _topic_lead_sentence(signature: dict, live_records: list[dict]) -> str:
    families = _topic_family_signal(signature, live_records)
    if not families:
        return f"This topic clusters {signature.get('evidence_count')} contributing record(s) in the current synastry evidence."
    if len(families) == 1:
        return f"Most of the live signal here is being carried by {families[0].replace('_', ' ')} evidence."
    return f"Most of the live signal here is being carried by {families[0].replace('_', ' ')} and {families[1].replace('_', ' ')} evidence."


def _topic_item(signature: dict, convergence: dict | None) -> dict:
    signature_key = signature.get("signature_key")
    live_records = _live_topic_records(signature)
    topic_leaf = select_topic_signature_leaf(signature_key)
    polarity_leaf = select_topic_polarity_leaf(signature.get("polarity"))
    localization_key = _topic_localization_key(signature, convergence, live_records)
    convergence_leaf = select_topic_convergence_leaf(localization_key)
    confidence_leaf = select_topic_confidence_leaf(signature.get("confidence_state"))
    label = str(signature.get("topic_label") or TOPIC_SPECS.get(signature_key, {}).get("label") or signature_key).replace("_", " ")
    displayed_families = sorted(
        {
            record.get("evidence_family")
            for record in (live_records or signature.get("contributing_records") or [])
            if isinstance(record, dict) and isinstance(record.get("evidence_family"), str)
        }
    )
    displayed_count = len(live_records) if live_records else int(signature.get("evidence_count") or 0)
    body = _sentence_join(
        [
            _topic_lead_sentence(signature, live_records),
            f"This topic currently resolves through {displayed_count} live contributing record(s) across {len(displayed_families)} evidence families." if displayed_families else "",
            topic_leaf.get("body"),
            polarity_leaf.get("body"),
            convergence_leaf.get("body"),
            confidence_leaf.get("body"),
        ]
    )
    return {
        "id": f"topic:{signature_key}",
        "title": label.title(),
        "body": body,
        "source": {
            "signature": _deepcopy(signature),
            "convergence": _deepcopy(convergence) if isinstance(convergence, dict) else None,
        },
        "selected_leaves": {
            "topic": topic_leaf,
            "polarity": polarity_leaf,
            "convergence": convergence_leaf,
            "confidence": confidence_leaf,
        },
        "metadata": {
            "signature_key": signature_key,
            "score": (convergence or {}).get("score", signature.get("score")),
            "polarity": signature.get("polarity"),
            "confidence_state": signature.get("confidence_state"),
            "independent_evidence_families": displayed_families,
            "localization": localization_key,
        },
    }


def _composite_body_item(record: dict) -> dict:
    leaf = select_composite_body_midpoint_leaf(record.get("body"))
    position = record.get("zodiac_position") or {}
    body = _sentence_join(
        [
            (
                f"The composite {record.get('body')} midpoint lands in {position.get('sign')} "
                f"at {position.get('degree')} degrees."
                if position.get("sign") is not None
                else ""
            ),
            leaf.get("body"),
        ]
    )
    return {
        "id": f"composite_body:{record.get('body')}",
        "title": f"Composite {record.get('body')}",
        "body": body,
        "source": _deepcopy(record),
        "selected_leaves": {"body_midpoint": leaf},
        "metadata": {
            "ambiguous": record.get("ambiguous"),
            "longitude": record.get("longitude"),
        },
    }


def _composite_aspect_item(record: dict) -> dict:
    leaf = select_composite_aspect_leaf(record.get("aspect"))
    body = _sentence_join(
        [
            (
                f"The composite {record.get('body_1')} and composite {record.get('body_2')} "
                f"form {_indefinite_article(record.get('aspect'))} {str(record.get('aspect') or '').lower()}."
            ),
            leaf.get("body"),
        ]
    )
    return {
        "id": f"composite_aspect:{record.get('body_1')}:{record.get('body_2')}:{record.get('aspect')}",
        "title": f"Composite {record.get('body_1')} / {record.get('body_2')} ({record.get('aspect')})",
        "body": body,
        "source": _deepcopy(record),
        "selected_leaves": {"composite_aspect": leaf},
        "metadata": {
            "orb": record.get("orb"),
            "confidence_state": record.get("confidence_state"),
        },
    }


def _composite_ambiguity_item(record: dict) -> dict:
    leaf = select_composite_ambiguity_leaf("opposite_midpoint")
    body = _sentence_join(
        [
            f"The composite {record.get('body')} midpoint is ambiguous because the natal longitudes are exact opposites.",
            leaf.get("body"),
        ]
    )
    return {
        "id": f"composite_ambiguity:{record.get('body')}",
        "title": f"Composite {record.get('body')} Ambiguity",
        "body": body,
        "source": _deepcopy(record),
        "selected_leaves": {"ambiguity": leaf},
        "metadata": {
            "possible_midpoints": list(record.get("possible_midpoints") or []),
        },
    }


def select_polarity_for_aspect(aspect: str | None) -> str:
    return {
        "Conjunction": "mixed",
        "Opposition": "tensional",
        "Square": "tensional",
        "Trine": "supportive",
        "Sextile": "supportive",
    }.get(str(aspect or ""), "mixed")


def _select_mutual_highlights(mutuals: list[dict], limit: int) -> list[dict]:
    ordered = sorted(
        [mutual for mutual in mutuals if isinstance(mutual, dict)],
        key=lambda mutual: (
            -_mutual_editorial_score(mutual),
            _mutual_sort_key(mutual),
        ),
    )
    selected: list[dict] = []
    body_counts: dict[str, int] = {}
    pure_angle_count = 0
    specialist_count = 0

    for mutual in ordered:
        entries = [entry for entry in mutual.get("mutual_key", []) or [] if isinstance(entry, dict)]
        non_angle_bodies = [entry.get("body") for entry in entries if entry.get("body") not in ANGLE_SET]
        is_pure_angle = _is_pure_angle_mutual(mutual)
        family = _mutual_family(mutual)
        if is_pure_angle and pure_angle_count >= 1:
            continue
        if family == "node_or_chiron_contact" and specialist_count >= 1:
            continue
        if non_angle_bodies and any(body_counts.get(body, 0) >= 2 for body in non_angle_bodies):
            continue
        selected.append(mutual)
        if is_pure_angle:
            pure_angle_count += 1
        if family == "node_or_chiron_contact":
            specialist_count += 1
        for body in non_angle_bodies:
            body_counts[body] = body_counts.get(body, 0) + 1
        if len(selected) >= limit:
            return selected

    for mutual in ordered:
        if mutual in selected:
            continue
        family = _mutual_family(mutual)
        if family == "node_or_chiron_contact" and specialist_count >= 1:
            continue
        selected.append(mutual)
        if family == "node_or_chiron_contact":
            specialist_count += 1
        if len(selected) >= limit:
            break
    return selected


def _select_house_overlay_highlights(overlays: list[dict], limit: int) -> list[dict]:
    ordered = sorted(overlays, key=_house_overlay_sort_key)
    selected: list[dict] = []
    used_bodies: set[str] = set()
    used_houses: set[int] = set()

    for overlay in ordered:
        body = str(overlay.get("source_body") or "")
        house = overlay.get("target_house")
        if body in used_bodies or house in used_houses:
            continue
        selected.append(overlay)
        used_bodies.add(body)
        if isinstance(house, int):
            used_houses.add(house)
        if len(selected) >= limit:
            return selected

    for overlay in ordered:
        if overlay in selected:
            continue
        selected.append(overlay)
        if len(selected) >= limit:
            break
    return selected


def _select_repeated_theme_highlights(themes: list[dict], limit: int) -> list[dict]:
    ordered = sorted(
        [theme for theme in themes if isinstance(theme, dict)],
        key=lambda item: (-_repeated_theme_editorial_score(item), str(item.get("theme_key") or "")),
    )
    selected: list[dict] = []
    aspect_family_count = 0
    seen_theme_types: set[str] = set()

    for theme in ordered:
        theme_type = str(theme.get("theme_type") or "")
        if theme_type == "repeated_aspect_family" and aspect_family_count >= REPEATED_ASPECT_FAMILY_LIMIT:
            continue
        if theme_type not in seen_theme_types or theme_type == "repeated_aspect_family":
            selected.append(theme)
            seen_theme_types.add(theme_type)
            if theme_type == "repeated_aspect_family":
                aspect_family_count += 1
            if len(selected) >= limit:
                return selected

    for theme in ordered:
        if theme in selected:
            continue
        if str(theme.get("theme_type") or "") == "repeated_aspect_family" and aspect_family_count >= REPEATED_ASPECT_FAMILY_LIMIT:
            continue
        selected.append(theme)
        if str(theme.get("theme_type") or "") == "repeated_aspect_family":
            aspect_family_count += 1
        if len(selected) >= limit:
            break
    return selected


def _composite_body_sort_key(record: dict) -> tuple[Any, ...]:
    return (
        -BODY_WEIGHTS.get(str(record.get("body")), 0.0),
        str(record.get("body") or ""),
    )


def _composite_aspect_sort_key(record: dict) -> tuple[Any, ...]:
    combined_weight = BODY_WEIGHTS.get(str(record.get("body_1")), 0.0) + BODY_WEIGHTS.get(str(record.get("body_2")), 0.0)
    return (
        -combined_weight,
        float(record.get("orb", 99.0) or 99.0),
        str(record.get("body_1") or ""),
        str(record.get("body_2") or ""),
    )


def _unique_confidence_states(pair_payload: dict) -> list[str]:
    states = {
        str((pair_payload.get("person_a") or {}).get("birth_time_state") or ""),
        str((pair_payload.get("person_b") or {}).get("birth_time_state") or ""),
    }
    return sorted(state for state in states if state)


def _overview_section(pair_payload: dict) -> dict:
    blocks = [
        {
            "id": "pair_payload",
            "title": "Evidence Basis",
            "body": select_technical_appendix_leaf("calculation_note", "pair_payload").get("body"),
            "selected_leaf": select_technical_appendix_leaf("calculation_note", "pair_payload"),
        },
        {
            "id": "relationship_verdicts_supported_false",
            "title": "Claim Boundary",
            "body": select_technical_appendix_leaf("claim_safety", "relationship_verdicts_supported_false").get("body"),
            "selected_leaf": select_technical_appendix_leaf("claim_safety", "relationship_verdicts_supported_false"),
        },
    ]
    for state in _unique_confidence_states(pair_payload):
        leaf = select_technical_appendix_leaf("confidence_note", state)
        blocks.append(
            {
                "id": f"confidence:{state}",
                "title": state.replace("_", " ").title(),
                "body": leaf.get("body"),
                "selected_leaf": leaf,
            }
        )
    return {
        "id": "overview",
        "title": "Overview",
        "blocks": blocks,
    }


def _topic_section(pair_payload: dict) -> dict:
    signatures = {
        record.get("signature_key"): record
        for record in pair_payload.get("computations", {}).get("relationship_topic_signatures", []) or []
        if isinstance(record, dict)
    }
    convergence_items = list(pair_payload.get("computations", {}).get("relationship_convergence", []) or [])
    items = []
    convergence_items.sort(key=lambda item: (-float(item.get("score", 0.0) or 0.0), str(item.get("signature_key") or "")))
    for convergence in convergence_items[:TOPIC_HIGHLIGHT_LIMIT]:
        signature = signatures.get(convergence.get("signature_key"))
        if not signature:
            continue
        items.append(_topic_item(signature, convergence))
    if not items:
        for signature in list(signatures.values())[:TOPIC_HIGHLIGHT_LIMIT]:
            items.append(_topic_item(signature, None))
    return {
        "id": "relationship_topics",
        "title": "Relationship Topics",
        "items": items,
    }


def _mutual_aspect_section(pair_payload: dict) -> dict:
    names = _person_names(pair_payload)
    mutuals = pair_payload.get("computations", {}).get("mutual_aspects", []) or []
    items = [_aspect_item(mutual, names) for mutual in _select_mutual_highlights(mutuals, MUTUAL_HIGHLIGHT_LIMIT)]
    return {
        "id": "mutual_aspects",
        "title": "Mutual Aspects",
        "items": items,
    }


def _house_overlay_sort_key(overlay: dict) -> tuple[Any, ...]:
    return (
        -BODY_WEIGHTS.get(str(overlay.get("source_body")), 0.0),
        overlay.get("target_house") or 99,
        str(overlay.get("source_person") or ""),
        str(overlay.get("target_person") or ""),
    )


def _house_overlay_section(pair_payload: dict) -> dict:
    names = _person_names(pair_payload)
    overlays = [
        overlay
        for overlay in pair_payload.get("computations", {}).get("house_overlays", []) or []
        if isinstance(overlay, dict) and not overlay.get("withheld")
    ]
    items = [_overlay_item(overlay, names) for overlay in _select_house_overlay_highlights(overlays, HOUSE_OVERLAY_LIMIT)]
    return {
        "id": "house_overlays",
        "title": "House Overlays",
        "items": items,
        "withheld_count": len(
            [
                overlay for overlay in pair_payload.get("computations", {}).get("house_overlays", []) or []
                if isinstance(overlay, dict) and overlay.get("withheld")
            ]
        ),
    }


def _repeated_theme_section(pair_payload: dict) -> dict:
    themes = pair_payload.get("computations", {}).get("repeated_natal_themes", []) or []
    selected_themes = _select_repeated_theme_highlights(themes, REPEATED_THEME_LIMIT)
    items = [_repeated_theme_item(theme) for theme in selected_themes]
    return {
        "id": "repeated_themes",
        "title": "Repeated Natal Themes",
        "blocks": _repeated_theme_summary_blocks(selected_themes),
        "items": items,
    }


def _composite_section(pair_payload: dict) -> dict:
    composite = pair_payload.get("computations", {}).get("composite", {}) or {}
    bodies = [item for item in composite.get("bodies", []) or [] if isinstance(item, dict)]
    aspects = [item for item in composite.get("aspects", []) or [] if isinstance(item, dict)]
    body_items = [
        _composite_body_item(item)
        for item in sorted(
            [item for item in bodies if not item.get("ambiguous")],
            key=_composite_body_sort_key,
        )[:COMPOSITE_BODY_LIMIT]
    ]
    ambiguity_items = [
        _composite_ambiguity_item(item)
        for item in bodies
        if item.get("ambiguous")
    ]
    aspect_items = [
        _composite_aspect_item(item)
        for item in sorted(aspects, key=_composite_aspect_sort_key)[:COMPOSITE_ASPECT_LIMIT]
    ]
    boundary_items = []
    for layer in ("composite_houses", "davison"):
        leaf = select_composite_unsupported_layer_leaf(layer)
        boundary_items.append(
            {
                "id": f"composite_boundary:{layer}",
                "title": layer.replace("_", " ").title(),
                "body": leaf.get("body"),
                "selected_leaf": leaf,
            }
        )
    return {
        "id": "composite",
        "title": "Composite Layer",
        "body_items": body_items,
        "aspect_items": aspect_items,
        "ambiguity_items": ambiguity_items,
        "boundary_items": boundary_items,
        "method_note": select_technical_appendix_leaf("calculation_note", "midpoint_composite"),
    }


def _technical_appendix_section(pair_payload: dict) -> dict:
    blocks = []
    for key in ("directional_aspects", "mutual_aspects", "house_overlays", "midpoint_composite", "composite_to_natal_resonance", "advanced_static_evidence"):
        leaf = select_technical_appendix_leaf("calculation_note", key)
        blocks.append(
            {
                "id": f"calculation_note:{key}",
                "title": key.replace("_", " ").title(),
                "body": leaf.get("body"),
                "selected_leaf": leaf,
            }
        )

    withheld_summary = ((pair_payload.get("sidecar") or {}).get("withheld_summary") or {}).get("by_reason") or {}
    for reason_key in sorted(withheld_summary):
        leaf = select_technical_appendix_leaf("withheld_reason", reason_key)
        blocks.append(
            {
                "id": f"withheld_reason:{reason_key}",
                "title": reason_key.replace("_", " ").title(),
                "body": leaf.get("body"),
                "selected_leaf": leaf,
                "count": withheld_summary.get(reason_key),
            }
        )

    for layer_key in ("composite_houses", "davison", "relationship_timing"):
        leaf = select_technical_appendix_leaf("unsupported_layer", layer_key)
        blocks.append(
            {
                "id": f"unsupported_layer:{layer_key}",
                "title": layer_key.replace("_", " ").title(),
                "body": leaf.get("body"),
                "selected_leaf": leaf,
            }
        )

    return {
        "id": "technical_appendix",
        "title": "Technical Appendix",
        "blocks": blocks,
        "withheld_summary": _deepcopy((pair_payload.get("sidecar") or {}).get("withheld_summary") or {}),
    }


def assemble_synastry_context(pair_payload: dict) -> dict:
    if not isinstance(pair_payload, dict):
        raise ValueError("pair_payload must be a dict.")

    required = {
        "schema_version",
        "person_a",
        "person_b",
        "relationship_meta",
        "computations",
        "confidence",
        "sidecar",
        "provenance",
    }
    missing = sorted(required - set(pair_payload))
    if missing:
        raise ValueError(f"pair_payload is missing required field(s): {', '.join(missing)}")

    compiler = SynastryNarrativeCompiler(pair_payload)
    sections = [
        _overview_section(pair_payload),
        *compiler.compile_sections(),
        _technical_appendix_section(pair_payload),
    ]
    names = _person_names(pair_payload)
    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "pair_schema_version": pair_payload.get("schema_version"),
        "formula_versions": list((pair_payload.get("provenance") or {}).get("formula_versions") or []),
        "person_a_name": names["A"],
        "person_b_name": names["B"],
        "person_a_birth_time_state": (pair_payload.get("person_a") or {}).get("birth_time_state"),
        "person_b_birth_time_state": (pair_payload.get("person_b") or {}).get("birth_time_state"),
        "relationship_meta": _deepcopy(pair_payload.get("relationship_meta") or {}),
        "claim_safety": _deepcopy((pair_payload.get("sidecar") or {}).get("claim_safety") or {}),
        "withheld_summary": _deepcopy((pair_payload.get("sidecar") or {}).get("withheld_summary") or {}),
        "sections": sections,
        "section_order": [section["id"] for section in sections],
        "source_pair_payload": _deepcopy(pair_payload),
    }


def build_synastry_context(
    person_a_natal_payload: dict,
    person_b_natal_payload: dict,
    *,
    relationship_meta: dict[str, Any] | None = None,
) -> dict:
    pair_payload = build_pair_payload(
        person_a_natal_payload,
        person_b_natal_payload,
        relationship_meta=relationship_meta,
    )
    return assemble_synastry_context(pair_payload)
