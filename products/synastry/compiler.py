"""
Narrative compiler for synastry report mode.

This layer transforms raw evidence records into reader-native sections without
discarding the underlying audit trail preserved elsewhere in the context.
"""
from __future__ import annotations

import copy
from typing import Any

from engine.synastry import ANGLE_POINTS, ASPECT_POLARITY, BODY_WEIGHTS
from selectors.synastry_selector import (
    select_repeated_theme_confidence_leaf,
    select_repeated_theme_type_leaf,
    select_topic_confidence_leaf,
    select_topic_polarity_leaf,
    select_topic_signature_leaf,
)


ANGLE_SET = set(ANGLE_POINTS)
HOUSE_LABELS = {
    1: "body and presence",
    2: "resources and steadiness",
    3: "daily communication",
    4: "private ground",
    5: "play and romance",
    6: "routine and care",
    7: "partnership field",
    8: "intimacy and shared stakes",
    9: "meaning and worldview",
    10: "public direction",
    11: "networks and future plans",
    12: "privacy and hidden weather",
}
TOPIC_TITLE_MAP = {
    "attachment_emotional_rhythm": ("emotional_rhythm_attachment", "Emotional Rhythm and Attachment"),
    "communication": ("communication_daily_exchange", "Communication and Daily Exchange"),
    "growth_meaning": ("growth_meaning_worldview", "Growth, Meaning, and Worldview"),
    "commitment_constraint_time": ("care_routine_responsibility", "Care, Routine, and Responsibility"),
    "intensity_merging_shared_resources": ("depth_intimacy_shared_stakes", "Depth, Intimacy, and Shared Stakes"),
}
TOPIC_ORDER = [
    "attachment_emotional_rhythm",
    "communication",
    "growth_meaning",
    "commitment_constraint_time",
    "intensity_merging_shared_resources",
]
TOPIC_RECORD_PREFERENCES = {
    "attachment_emotional_rhythm": ["moon_overlay", "fourth_house_overlay", "moon_contacts", "imum_coeli_angle_contact", "ic_angle_contact"],
    "communication": ["mercury_overlay", "third_house_overlay", "mercury_contacts"],
    "growth_meaning": ["jupiter_overlay", "ninth_house_overlay", "jupiter_contacts"],
    "commitment_constraint_time": ["saturn_overlay", "saturn_contacts"],
    "intensity_merging_shared_resources": ["eighth_house_overlay", "pluto_overlay", "pluto_contacts"],
    "affection_value_attraction": ["venus_contacts", "venus_overlay", "mars_contacts", "mars_overlay"],
}
FAMILY_LABELS = {
    "moon_contacts": "Moon contacts",
    "moon_overlay": "Moon overlays",
    "fourth_house_overlay": "fourth-house material",
    "ic_angle_contact": "IC contact",
    "imum_coeli_angle_contact": "IC contact",
    "mercury_contacts": "Mercury contacts",
    "mercury_overlay": "Mercury overlays",
    "third_house_overlay": "third-house material",
    "venus_contacts": "Venus contacts",
    "venus_overlay": "Venus overlays",
    "mars_contacts": "Mars contacts",
    "mars_overlay": "Mars overlays",
    "jupiter_contacts": "Jupiter contacts",
    "jupiter_overlay": "Jupiter overlays",
    "ninth_house_overlay": "ninth-house material",
    "saturn_contacts": "Saturn contacts",
    "saturn_overlay": "Saturn overlays",
    "pluto_contacts": "Pluto contacts",
    "pluto_overlay": "Pluto overlays",
    "eighth_house_overlay": "eighth-house material",
}
SIGN_TONE = {
    "Aries": "direct, initiating, and hard to keep passive",
    "Taurus": "slow-building, embodied, and steady once engaged",
    "Gemini": "curious, mobile, and mentally changeable",
    "Cancer": "protective, responsive, and rooted in feeling",
    "Leo": "visible, expressive, and dramatic about what matters",
    "Virgo": "practical, discerning, and detail-aware",
    "Libra": "relational, balancing, and concerned with fairness",
    "Scorpio": "intense, private, and difficult to keep superficial",
    "Sagittarius": "expansive, exploratory, and horizon-seeking",
    "Capricorn": "structured, consequential, and serious about follow-through",
    "Aquarius": "future-facing, unconventional, and in need of space",
    "Pisces": "porous, symbolic, intuitive, and sometimes hard to define cleanly",
}
POINT_LABELS = {
    "Ascendant": "Ascendant",
    "Descendant": "Descendant",
    "Midheaven": "Midheaven",
    "Imum_Coeli": "Imum Coeli",
    "North_Node": "North Node",
    "South_Node": "South Node",
}


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _sentence_join(parts: list[str]) -> str:
    clean = [str(part).strip() for part in parts if isinstance(part, str) and part.strip()]
    return " ".join(clean)


def _serial_join(parts: list[str]) -> str:
    clean = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def _title_case_signal(value: str) -> str:
    return str(value or "").replace("_", " ").title()


def _body_name(body: Any) -> str:
    if isinstance(body, dict):
        body = body.get("body")
    key = str(body or "")
    return POINT_LABELS.get(key, key.replace("_", " "))


def _fallback_person_name(person: str | None) -> str:
    return "Person A" if person == "A" else "Person B" if person == "B" else str(person or "Person")


def _is_internal_fixture_name(value: str) -> bool:
    return str(value or "").strip().lower().startswith("synastry fixture")


def _clean_person_name(value: Any, person: str) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and not _is_internal_fixture_name(stripped):
            return stripped
    return _fallback_person_name(person)


def _overlay_mechanism_sentence(source_name: str, source_body: str, target_name: str, target_house_label: str) -> str:
    mechanisms = {
        "Sun": "brings visibility, identity, and direction into",
        "Moon": "brings emotional tone and responsiveness into",
        "Mercury": "brings language, interpretation, and exchange into",
        "Venus": "brings affection, preference, and relational ease into",
        "Mars": "brings activation, directness, and heat into",
        "Jupiter": "brings encouragement, scale, and possibility into",
        "Saturn": "brings pacing, responsibility, and follow-through into",
        "Uranus": "brings disruption, awakening, and changed expectations into",
        "Neptune": "softens and idealizes",
        "Pluto": "intensifies",
        "North Node": "pulls attention toward",
        "South Node": "stirs familiar patterning inside",
        "Chiron": "sensitizes",
    }
    mechanism = mechanisms.get(source_body, "places its symbolism inside")
    if source_body in {"Neptune", "Pluto", "North Node", "South Node", "Chiron"}:
        return f"{source_name}'s {source_body} {mechanism} {target_name}'s {target_house_label}."
    return f"{source_name}'s {source_body} {mechanism} {target_name}'s {target_house_label}."


def _aspect_verb(aspect: str) -> str:
    mapping = {
        "conjunction": "conjoins",
        "opposition": "opposes",
        "square": "squares",
        "trine": "trines",
        "sextile": "sextiles",
    }
    return mapping.get(str(aspect or "").lower(), str(aspect or "").lower())


def _aspect_adjective(aspect: str) -> str:
    mapping = {
        "conjunction": "conjunct",
        "opposition": "opposite",
        "square": "square",
        "trine": "trine",
        "sextile": "sextile",
    }
    return mapping.get(str(aspect or "").lower(), str(aspect or "").lower())


def _mutual_topic_mechanism(left: str, aspect: str, right: str, bodies: set[str]) -> str:
    verb = _aspect_verb(aspect)
    if "Venus" in bodies and "Ascendant" in bodies:
        return f"{left} {verb} {right}, making attraction and visible presentation hard to keep separate."
    if "Venus" in bodies and "Descendant" in bodies:
        return f"{left} {verb} {right}, bringing affection directly into the partnership-recognition field."
    if "Venus" in bodies and {"North_Node", "South_Node"} & bodies:
        return f"{left} {verb} {right}, tying attraction to developmental pull without turning it into fate."
    if "Moon" in bodies and "Venus" in bodies:
        return f"{left} {verb} {right}, giving emotional response and affection a shared route."
    if "Sun" in bodies and "Mars" in bodies:
        return f"{left} {verb} {right}, adding heat, pursuit, and activation to the contact."
    return f"{left} {verb} {right}, anchoring the theme in a named cross-chart contact."


def directional_overlay_interpretation(
    source_name: str,
    source_body: str,
    target_name: str,
    target_house_label: str,
    *,
    implication: str | None = None,
) -> str:
    sentence = _overlay_mechanism_sentence(source_name, source_body, target_name, target_house_label)
    if implication:
        sentence += f" {implication.strip()}"
    return sentence


def mutual_contact_interpretation(
    left_name: str,
    left_body: str,
    aspect: str,
    right_name: str,
    right_body: str,
    *,
    implication: str | None = None,
) -> str:
    body = (
        f"{left_name}'s {left_body} {_aspect_verb(aspect)} {right_name}'s {right_body}"
    )
    sentence = f"{body}, creating a contact the relationship is unlikely to experience as neutral."
    if implication:
        sentence += f" {implication.strip()}"
    return sentence


class SynastryNarrativeCompiler:
    def __init__(self, pair_payload: dict):
        self.pair_payload = pair_payload
        self.computations = pair_payload.get("computations", {}) or {}
        self.relationship_meta = pair_payload.get("relationship_meta", {}) or {}
        self.names = self._person_names()
        self.topics = self._topic_map()
        self.convergence = self._convergence_map()
        self.mutuals = [item for item in self.computations.get("mutual_aspects", []) or [] if isinstance(item, dict)]
        self.overlays = [
            item
            for item in self.computations.get("house_overlays", []) or []
            if isinstance(item, dict) and not item.get("withheld")
        ]
        self.repeated_themes = [item for item in self.computations.get("repeated_natal_themes", []) or [] if isinstance(item, dict)]
        self.composite = self.computations.get("composite", {}) or {}

    def compile_sections(self) -> list[dict]:
        sections: list[dict] = [
            self._relationship_at_a_glance_section(),
            self._core_relationship_signature_section(),
        ]

        for topic_key in TOPIC_ORDER:
            section = self._topic_section(topic_key)
            if section:
                sections.append(section)

        for builder in (
            self._attraction_section,
            self._home_body_private_section,
            self._play_romance_section,
            self._directional_landing_section,
            self._shared_natal_baseline_section,
            self._composite_relationship_field_section,
            self._friction_growth_edges_section,
            self._integrated_relationship_portrait_section,
        ):
            section = builder()
            if section:
                sections.append(section)

        return sections

    def _person_names(self) -> dict[str, str]:
        return {
            "A": _clean_person_name(self.relationship_meta.get("person_a_label"), "A"),
            "B": _clean_person_name(self.relationship_meta.get("person_b_label"), "B"),
        }

    def _topic_map(self) -> dict[str, dict]:
        return {
            item.get("signature_key"): item
            for item in self.computations.get("relationship_topic_signatures", []) or []
            if isinstance(item, dict) and item.get("signature_key")
        }

    def _convergence_map(self) -> dict[str, dict]:
        return {
            item.get("signature_key"): item
            for item in self.computations.get("relationship_convergence", []) or []
            if isinstance(item, dict) and item.get("signature_key")
        }

    def _sorted_topics(self) -> list[tuple[str, dict, dict | None]]:
        records = []
        for key, signature in self.topics.items():
            convergence = self.convergence.get(key)
            score = float((convergence or {}).get("score", 0.0) or 0.0)
            evidence_count = int(signature.get("evidence_count", 0) or 0)
            records.append((key, signature, convergence, score, evidence_count))
        records.sort(key=lambda item: (-item[3], -item[4], str(item[0])))
        return [(key, signature, convergence) for key, signature, convergence, _, _ in records]

    def _evidence_family_labels(self, signature: dict) -> list[str]:
        labels = []
        for family in signature.get("independent_evidence_families", []) or []:
            labels.append(FAMILY_LABELS.get(str(family), _title_case_signal(str(family))))
        return labels

    def _top_topic_label(self, topic_key: str | None) -> str:
        mapping = {
            "attachment_emotional_rhythm": "emotional rhythm",
            "communication": "communication",
            "growth_meaning": "growth and meaning",
            "commitment_constraint_time": "care and responsibility",
            "intensity_merging_shared_resources": "depth and shared stakes",
            "affection_value_attraction": "attraction",
            "desire_friction_action": "heat and activation",
            "visibility_public_path": "visibility and public direction",
        }
        return mapping.get(str(topic_key or ""), _title_case_signal(str(topic_key or "relationship theme")).lower())

    def _topic_section(self, topic_key: str) -> dict | None:
        signature = self.topics.get(topic_key)
        if not signature:
            return None
        convergence = self.convergence.get(topic_key) or {}
        section_id, title = TOPIC_TITLE_MAP[topic_key]
        topic_intro = self._topic_intro(topic_key, signature)
        evidence = self._topic_evidence_sentences(topic_key, signature)
        modifier = self._topic_modifier(topic_key)
        close = self._topic_close(topic_key)
        body = _sentence_join([topic_intro, *evidence, modifier, close])
        families = self._evidence_family_labels(signature)
        return {
            "id": section_id,
            "title": title,
            "blocks": [
                {
                    "id": f"{section_id}:summary",
                    "title": title,
                    "body": body,
                }
            ],
            "metadata": {
                "topic_key": topic_key,
                "score": float(convergence.get("score", 0.0) or 0.0),
                "polarity": convergence.get("polarity") or signature.get("polarity"),
                "evidence_families": families,
            },
        }

    def _topic_intro(self, topic_key: str, signature: dict) -> str:
        if topic_key == "attachment_emotional_rhythm":
            return "Emotional rhythm is the clearest organizing theme in this relationship."
        if topic_key == "communication":
            return "Communication is not peripheral here; it is one of the main ways the relationship becomes real."
        if topic_key == "growth_meaning":
            return "Growth and meaning are active enough here that the relationship keeps widening the frame around itself."
        if topic_key == "commitment_constraint_time":
            return "Care, routine, and responsibility matter because this bond does not stay purely atmospheric."
        if topic_key == "intensity_merging_shared_resources":
            return "Depth and shared stakes are part of the structure, not just occasional mood."
        label = self._top_topic_label(topic_key).capitalize()
        return f"{label} is one of the stronger recurring themes in this relationship."

    def _topic_modifier(self, topic_key: str) -> str:
        if topic_key == "communication":
            if self._find_mutual({"Moon", "Mercury"}, aspect="Square"):
                return "Communication is central and usable, but emotional meaning and verbal interpretation do not always arrive on the same rhythm."
        if topic_key == "attachment_emotional_rhythm":
            if self._find_overlay("Moon", 3):
                return "Because Moon overlay material also enters the communication field, feeling and conversation keep crossing each other's boundary."
        if topic_key == "growth_meaning":
            if self._find_overlay("Jupiter", 1):
                return f"{self.names['A']}'s Jupiter in {self.names['B']}'s first house reinforces the sense that encouragement and possibility are being carried directly into the relationship's lived encounter."
        if topic_key == "intensity_merging_shared_resources":
            if self._find_overlay("Sun", 8):
                return f"{self.names['A']}'s Sun in {self.names['B']}'s eighth house is part of why this theme reads as consequential rather than merely intriguing."
        return ""

    def _relationship_at_a_glance_section(self) -> dict:
        body = _sentence_join(
            [
                self._core_signature_thesis(preview=True),
                self._glance_evidence_sentence(),
                self._composite_brief(),
            ]
        )
        return {
            "id": "relationship_at_a_glance",
            "title": "Relationship at a Glance",
            "blocks": [
                {
                    "id": "relationship_at_a_glance:summary",
                    "title": "At a Glance",
                    "body": body,
                }
            ],
        }

    def _core_relationship_signature_section(self) -> dict:
        top_mutuals = self._top_mutuals(3, include_angle_only=False)
        top_overlays = self._top_overlays(3)
        sentences = []
        sentences.append(self._core_signature_thesis())
        if top_mutuals:
            phrases = [_self_or_other_phrase(mutual, self.names) for mutual in top_mutuals]
            sentences.append(f"The highest-salience cross-chart contacts include {_serial_join(phrases)}, which gives the relationship its most immediate points of recognition and activation.")
        if top_overlays:
            overlay_phrase = _serial_join([self._overlay_phrase(item) for item in top_overlays])
            sentences.append(f"Directionally, that recognition keeps landing through {overlay_phrase}.")
        return {
            "id": "core_relationship_signature",
            "title": "Core Relationship Signature",
            "blocks": [
                {
                    "id": "core_relationship_signature:summary",
                    "title": "Core Signature",
                    "body": _sentence_join(sentences),
                }
            ],
        }

    def _attraction_section(self) -> dict | None:
        signature = self.topics.get("affection_value_attraction") or {}
        evidence = self._topic_evidence_sentences("affection_value_attraction", signature, limit=3) if signature else []
        if not evidence:
            return None
        sentences = [
            "Attraction is present here as something visible and consequential rather than purely atmospheric.",
            *evidence,
            self._attraction_close(),
        ]
        return {
            "id": "attraction_visibility_encounter",
            "title": "Attraction, Visibility, and Encounter",
            "blocks": [
                {
                    "id": "attraction_visibility_encounter:summary",
                    "title": "Attraction and Encounter",
                    "body": _sentence_join(sentences),
                }
            ],
        }

    def _home_body_private_section(self) -> dict | None:
        relevant = [
            item for item in self.overlays
            if item.get("target_house") in {1, 4}
            or item.get("source_body") in {"Moon", "Mars", "Sun"}
        ]
        if not relevant:
            return None
        pieces = []
        mars_fourth = self._find_overlay("Mars", 4)
        if mars_fourth:
            pieces.append(
                f"{self.names[mars_fourth['source_person']]}'s Mars enters {self.names[mars_fourth['target_person']]}'s fourth house, so drive and directness land in private ground rather than staying only on the visible surface."
            )
        asc_mars = self._find_mutual({"Ascendant", "Mars"}, aspect="Square")
        if asc_mars:
            source, target = _mutual_people_by_body(asc_mars, "Mars", "Ascendant")
            if source and target:
                pieces.append(
                    f"{self.names[source]}'s Mars also squares {self.names[target]}'s Ascendant, which means the same catalytic energy touches both outer interface and inner shelter."
                )
        moon_third = self._find_overlay("Moon", 3)
        if moon_third:
            pieces.append(
                f"{self.names[moon_third['source_person']]}'s Moon in {self.names[moon_third['target_person']]}'s third house adds emotional tone to everyday exchange, so the private field is not sealed off from conversation."
            )
        if not pieces:
            return None
        return {
            "id": "home_body_private_terrain",
            "title": "Home, Body, and Private Terrain",
            "blocks": [
                {
                    "id": "home_body_private_terrain:summary",
                    "title": "Private Terrain",
                    "body": _sentence_join(pieces),
                }
            ],
        }

    def _play_romance_section(self) -> dict | None:
        evidence = self._play_evidence_sentences(limit=3)
        if not evidence:
            return None
        pieces = [
            "Play, romance, and idealization appear when the bond becomes expressive rather than only practical."
        ]
        pieces.extend(evidence)
        pieces.append(self._play_close())
        return {
            "id": "play_romance_idealization",
            "title": "Play, Romance, and Idealization",
            "blocks": [
                {
                    "id": "play_romance_idealization:summary",
                    "title": "Play and Idealization",
                    "body": _sentence_join(pieces),
                }
            ],
        }

    def _directional_landing_section(self) -> dict | None:
        if not self.overlays:
            return None
        blocks = []
        for source_person, target_person in (("A", "B"), ("B", "A")):
            body = self._directional_landing_body(source_person, target_person)
            if not body:
                continue
            blocks.append(
                {
                    "id": f"directional_landing:{source_person}:{target_person}",
                    "title": f"How {self.names[source_person]} Lands for {self.names[target_person]}",
                    "body": body,
                }
            )
        if not blocks:
            return None
        return {
            "id": "directional_landing",
            "title": "Directional Landing",
            "blocks": blocks,
        }

    def _shared_natal_baseline_section(self) -> dict | None:
        if not self.repeated_themes:
            return {
                "id": "shared_natal_baseline",
                "title": "Shared Natal Baseline",
                "blocks": [
                    {
                        "id": "shared_natal_baseline:summary",
                        "title": "Shared Baseline",
                        "body": "No single repeated natal baseline dominates this pairing. That usually means the relationship is being shaped more by live cross-chart contact than by duplicated natal wiring, even though both people still arrive with their own established patterning.",
                    }
                ],
            }
        top_themes = sorted(
            self.repeated_themes,
            key=lambda item: (-float(item.get("salience", 0.0) or 0.0), str(item.get("theme_key") or "")),
        )[:5]
        structural_themes = [theme for theme in top_themes if str(theme.get("theme_type") or "") != "repeated_aspect_family"]
        aspect_themes = [theme for theme in top_themes if str(theme.get("theme_type") or "") == "repeated_aspect_family"]
        chosen_themes = structural_themes[:2]
        if aspect_themes:
            chosen_themes.append(aspect_themes[0])
        theme_phrases = []
        for theme in chosen_themes:
            theme_type = str(theme.get("theme_type") or "")
            theme_leaf = select_repeated_theme_type_leaf(theme_type)
            phrase = theme_leaf.get("body")
            theme_phrases.append(_sentence_join([phrase, self._repeated_theme_specifics(theme)]))
        body = _sentence_join(
            [
                "The shared natal baseline matters because this relationship is not being built from completely unfamiliar symbolic material.",
                "At minimum, both people are arriving with some similar natal architecture already in place.",
                *theme_phrases[:2],
                theme_phrases[2] if len(theme_phrases) > 2 else "",
                self._repeated_theme_bridge(chosen_themes),
                "These repeated structures do not decide the relationship, but they do help explain why some dynamics feel immediately recognizable from the inside.",
            ]
        )
        return {
            "id": "shared_natal_baseline",
            "title": "Shared Natal Baseline",
            "blocks": [
                {
                    "id": "shared_natal_baseline:summary",
                    "title": "Shared Baseline",
                    "body": body,
                }
            ],
        }

    def _composite_relationship_field_section(self) -> dict | None:
        bodies = [item for item in self.composite.get("bodies", []) or [] if isinstance(item, dict) and not item.get("ambiguous")]
        aspects = [item for item in self.composite.get("aspects", []) or [] if isinstance(item, dict)]
        if not bodies:
            return None
        body_map = {item.get("body"): item for item in bodies}
        pieces = []
        sun = body_map.get("Sun")
        mercury = body_map.get("Mercury")
        moon = body_map.get("Moon")
        venus = body_map.get("Venus")
        saturn = body_map.get("Saturn")
        mars = body_map.get("Mars")
        if sun or mercury:
            signs = [item.get("zodiac_position", {}).get("sign") for item in (sun, mercury) if item]
            tone = SIGN_TONE.get(signs[0], "symbolic and relational") if signs else "symbolic and relational"
            pieces.append(
                f"The composite field is {tone}. "
                + (
                    f"Composite Sun in {sun.get('zodiac_position', {}).get('sign')} and Mercury in {mercury.get('zodiac_position', {}).get('sign')} make the relationship think and organize itself in that register."
                    if sun and mercury
                    else f"Composite {_body_name((sun or mercury).get('body'))} in {(sun or mercury).get('zodiac_position', {}).get('sign')} gives the relationship a center of gravity in that register."
                )
            )
        if moon:
            pieces.append(
                f"Composite Moon in {moon.get('zodiac_position', {}).get('sign')} shapes the emotional climate toward {SIGN_TONE.get(moon.get('zodiac_position', {}).get('sign'), 'relational balance')}."
            )
        if venus and saturn:
            pieces.append(
                f"Composite Venus in {venus.get('zodiac_position', {}).get('sign')} and Saturn in {saturn.get('zodiac_position', {}).get('sign')} add a need for both affection and workable structure."
            )
        if mars:
            pieces.append(
                f"Composite Mars in {mars.get('zodiac_position', {}).get('sign')} gives the bond {SIGN_TONE.get(mars.get('zodiac_position', {}).get('sign'), 'real momentum')} when something has to move."
            )
        aspect_bits = []
        for bodies_set, aspect, phrase in (
            ({"Moon", "Venus"}, "Trine", "Moon trine Venus gives the relationship an internal comfort pathway."),
            ({"Jupiter", "Saturn"}, "Trine", "Jupiter trine Saturn helps hope and structure cooperate."),
            ({"Mercury", "North_Node"}, "Square", "Mercury square North Node makes communication part of the relationship's growth demand."),
        ):
            if self._find_composite_aspect(bodies_set, aspect):
                aspect_bits.append(phrase)
        pieces.extend(aspect_bits)
        return {
            "id": "composite_relationship_field",
            "title": "Composite Relationship Field",
            "blocks": [
                {
                    "id": "composite_relationship_field:summary",
                    "title": "Composite Field",
                    "body": _sentence_join(pieces),
                }
            ],
        }

    def _friction_growth_edges_section(self) -> dict | None:
        tensions = [
            mutual for mutual in self.mutuals
            if str(mutual.get("aspect") or "") in {"Square", "Opposition"}
        ]
        mixed_topics = [
            key for key, convergence in self.convergence.items()
            if str(convergence.get("polarity") or "") == "mixed"
        ]
        if not tensions and not mixed_topics:
            return None
        pieces = ["The relationship has real growth edges, but they are specific rather than abstractly ominous."]
        catalytic = self._catalytic_heat_summary()
        if catalytic:
            pieces.append(catalytic)
        if "communication" in mixed_topics or self._find_mutual({"Moon", "Mercury"}, aspect="Square"):
            pieces.append("Communication is one of the growth edges precisely because it matters so much; the relationship has signal, but it still needs translation.")
        if "growth_meaning" in mixed_topics:
            pieces.append("Hope expands possibility here, but it works best when inspiration is paired with structure rather than trusted to self-regulate.")
        return {
            "id": "friction_growth_edges",
            "title": "Friction and Growth Edges",
            "blocks": [
                {
                    "id": "friction_growth_edges:summary",
                    "title": "Growth Edges",
                    "body": _sentence_join(pieces),
                }
            ],
        }

    def _integrated_relationship_portrait_section(self) -> dict:
        pieces = [
            "Taken together, the chart reads less like a one-note compatibility story and more like a relationship with several active axes of recognition.",
            self._portrait_synthesis(),
            "The strongest through-line is that private grounding, communication, attraction, visibility, and deeper stakes keep crossing into each other rather than staying compartmentalized.",
            "The healthiest use of the chart is not to treat intensity as proof, but to notice where recognition is real, where pacing is required, and where each person is landing in the other's lived terrain.",
        ]
        return {
            "id": "integrated_relationship_portrait",
            "title": "Integrated Relationship Portrait",
            "blocks": [
                {
                    "id": "integrated_relationship_portrait:summary",
                    "title": "Integrated Portrait",
                    "body": _sentence_join(pieces),
                }
            ],
        }

    def _top_mutuals(self, limit: int, *, include_angle_only: bool = True) -> list[dict]:
        ordered = sorted(
            self.mutuals,
            key=lambda item: (
                self._pure_angle_penalty(item, include_angle_only=include_angle_only),
                self._dependency_penalty(item),
                -float(item.get("salience", 0.0) or 0.0),
                float(item.get("orb", 99.0) or 99.0),
            ),
        )
        if not include_angle_only:
            filtered = [item for item in ordered if not self._is_pure_angle_mutual(item)]
            if filtered:
                ordered = filtered + [item for item in ordered if self._is_pure_angle_mutual(item)]
        return ordered[:limit]

    def _top_overlays(self, limit: int) -> list[dict]:
        ordered = sorted(
            self.overlays,
            key=lambda item: (
                -BODY_WEIGHTS.get(str(item.get("source_body") or ""), 0.0),
                item.get("target_house") or 99,
            ),
        )
        return ordered[:limit]

    def _find_mutual(self, bodies: set[str], aspect: str | None = None) -> dict | None:
        for mutual in sorted(self.mutuals, key=lambda item: -float(item.get("salience", 0.0) or 0.0)):
            mutual_bodies = {
                entry.get("body")
                for entry in mutual.get("mutual_key", []) or []
                if isinstance(entry, dict)
            }
            if bodies <= mutual_bodies and (aspect is None or str(mutual.get("aspect") or "") == aspect):
                return mutual
        return None

    def _find_overlay(self, source_body: str, target_house: int) -> dict | None:
        for overlay in self._top_overlays(len(self.overlays)):
            if str(overlay.get("source_body") or "") == source_body and int(overlay.get("target_house") or 0) == target_house:
                return overlay
        return None

    def _find_composite_aspect(self, bodies: set[str], aspect: str) -> dict | None:
        for item in self.composite.get("aspects", []) or []:
            if not isinstance(item, dict):
                continue
            body_set = {item.get("body_1"), item.get("body_2")}
            if bodies <= body_set and str(item.get("aspect") or "") == aspect:
                return item
        return None

    def _directional_fields(self, source_person: str, target_person: str) -> list[str]:
        overlays = [
            item for item in self.overlays
            if item.get("source_person") == source_person and item.get("target_person") == target_person
        ]
        overlays.sort(key=lambda item: (-BODY_WEIGHTS.get(str(item.get("source_body") or ""), 0.0), item.get("target_house") or 99))
        fields = []
        for overlay in overlays:
            label = HOUSE_LABELS.get(int(overlay.get("target_house") or 0))
            if label and label not in fields:
                fields.append(label)
            if len(fields) >= 6:
                break
        return fields

    def _overlay_phrase(self, overlay: dict) -> str:
        return (
            f"{self.names[overlay.get('source_person')]}'s {_body_name(overlay.get('source_body'))} "
            f"in {self.names[overlay.get('target_person')]}'s {HOUSE_LABELS.get(int(overlay.get('target_house') or 0), 'lived field')}"
        )

    def _attraction_cluster_records(self) -> list[dict]:
        records = []
        for mutual in self.mutuals:
            bodies = {
                entry.get("body")
                for entry in mutual.get("mutual_key", []) or []
                if isinstance(entry, dict)
            }
            if bodies & {"Venus", "Mars", "Sun", "Ascendant", "Descendant"}:
                records.append(mutual)
        for overlay in self.overlays:
            if overlay.get("source_body") in {"Venus", "Mars", "Sun"} or int(overlay.get("target_house") or 0) in {1, 5, 7}:
                records.append(overlay)
        return records

    def _attraction_summary(self) -> str:
        if not self._attraction_cluster_records():
            return "Attraction is present, but it is not the most dominant organizing layer in the current evidence."
        sentences = [
            "The attraction signatures are vivid rather than subtle."
        ]
        if self._find_overlay("Venus", 7):
            sentences.append("Venus overlay material lands directly in partnership space, which makes relational recognition easy to feel.")
        if self._find_mutual({"Mars", "Sun"}, aspect="Conjunction"):
            sentences.append("Mars-Sun contact adds heat, urgency, and embodied activation instead of leaving the field purely soft.")
        return _sentence_join(sentences)

    def _catalytic_heat_summary(self) -> str:
        if not (
            self._find_mutual({"Mars", "Sun"}, aspect="Conjunction")
            or self._find_mutual({"Ascendant", "Mars"}, aspect="Square")
            or self._find_overlay("Mars", 4)
        ):
            return ""
        return "Mars is active on both sides of the field, creating charge, momentum, and pressure that need pacing if directness is going to stay usable."

    def _depth_summary(self) -> str:
        signals = []
        if self._find_overlay("Sun", 8):
            signals.append("Sun overlay material enters the eighth-house field")
        if self._find_mutual({"Sun", "Pluto"}, aspect="Trine"):
            signals.append("Sun-Pluto contact adds depth without making intensity the only story")
        if any(
            item.get("signature_key") == "intensity_merging_shared_resources"
            for item in self.convergence.values()
        ):
            signals.append("the topic ranking keeps returning to shared stakes and merging pressure")
        if not signals:
            return "Depth exists in the chart, but it is not the sole story the relationship is asking to tell."
        return "This relationship is not structured as purely casual. " + _serial_join(signals[:3]).capitalize() + "."

    def _composite_brief(self) -> str:
        body_map = {
            item.get("body"): item
            for item in self.composite.get("bodies", []) or []
            if isinstance(item, dict) and not item.get("ambiguous")
        }
        sun = body_map.get("Sun")
        moon = body_map.get("Moon")
        if not (sun and moon):
            return ""
        return (
            f"The composite field itself leans {SIGN_TONE.get(sun.get('zodiac_position', {}).get('sign'), 'symbolic')} at the center, "
            f"with a {moon.get('zodiac_position', {}).get('sign')} Moon shaping how the relationship tries to feel balanced or emotionally legible."
        )

    def _topic_evidence_sentences(self, topic_key: str, signature: dict, limit: int = 2) -> list[str]:
        return [self._topic_record_sentence(record) for record in self._topic_evidence_records(topic_key, signature, limit=limit)]

    def _topic_evidence_records(self, topic_key: str, signature: dict, limit: int = 2) -> list[dict]:
        preferences = TOPIC_RECORD_PREFERENCES.get(topic_key, [])
        records = [record for record in signature.get("contributing_records", []) or [] if isinstance(record, dict)]
        ordered = sorted(records, key=lambda record: self._topic_record_sort_key(record, preferences))
        return ordered[:limit]

    def _topic_record_sort_key(self, record: dict, preferences: list[str]) -> tuple[Any, ...]:
        family = str(record.get("evidence_family") or "")
        family_index = preferences.index(family) if family in preferences else len(preferences) + 1
        salience = -float(record.get("salience", 0.0) or 0.0)
        pure_angle = 0
        if record.get("record_type") == "mutual_aspect_reference":
            entries = [entry for entry in record.get("mutual_key", []) or [] if isinstance(entry, dict)]
            pure_angle = 1 if entries and all(entry.get("body") in ANGLE_SET for entry in entries) else 0
        return (family_index, pure_angle, salience)

    def _topic_record_sentence(self, record: dict) -> str:
        if record.get("record_type") == "mutual_aspect_reference":
            entries = [entry for entry in record.get("mutual_key", []) or [] if isinstance(entry, dict)]
            if len(entries) >= 2:
                left = f"{self.names.get(entries[0].get('person'))}'s {_body_name(entries[0].get('body'))}"
                right = f"{self.names.get(entries[1].get('person'))}'s {_body_name(entries[1].get('body'))}"
                bodies = {str(entry.get("body") or "") for entry in entries}
                return _mutual_topic_mechanism(left, str(record.get("aspect") or ""), right, bodies)
        if record.get("record_type") == "house_overlay_reference":
            house_label = HOUSE_LABELS.get(int(record.get("target_house") or 0), "lived field")
            return directional_overlay_interpretation(
                self.names.get(record.get("source_person")),
                _body_name(record.get("source_body")),
                self.names.get(record.get("target_person")),
                house_label,
            )
        return ""

    def _topic_close(self, topic_key: str) -> str:
        mapping = {
            "attachment_emotional_rhythm": "This is why the emotional field reads lived-in quickly rather than staying polite or distant.",
            "communication": "The result is a relationship where exchange itself becomes part of the bond's substance.",
            "growth_meaning": "So the relationship keeps widening its frame, even when it has to negotiate how much possibility can actually be carried.",
            "commitment_constraint_time": "That is why this theme tends to show up in calendars, follow-through, and what the connection can actually hold.",
            "intensity_merging_shared_resources": "That is what makes the depth here feel consequential instead of decorative.",
        }
        return mapping.get(topic_key, "")

    def _core_signature_thesis(self, preview: bool = False) -> str:
        axes = self._core_signature_axes()
        if axes:
            if preview:
                return "At first read, the relationship announces itself through " + _serial_join(axes[:4]) + "."
            return "The core signature here is a recognition pattern running through " + _serial_join(axes[:6]) + " rather than one isolated topic."
        top_topic = self._sorted_topics()[0][0] if self._sorted_topics() else None
        if top_topic:
            return f"The core signature here is {self._top_topic_label(top_topic)}, not as a vague atmosphere but as a repeated pattern that keeps being confirmed by live evidence."
        return "The core signature here is being carried by repeated live evidence rather than a single stock label."

    def _core_signature_axes(self) -> list[str]:
        axes: list[str] = []
        def add(value: str) -> None:
            if value and value not in axes:
                axes.append(value)
        if self._find_overlay("Moon", 4) or self._find_mutual({"Imum_Coeli", "Moon"}) or self._find_mutual({"Moon", "Moon"}):
            add("private grounding")
        if self.topics.get("communication") or self._find_mutual({"Mercury", "Mercury"}) or self._find_overlay("Mercury", 3):
            add("communication")
        if self.topics.get("affection_value_attraction") or self._find_mutual({"Venus", "Mars"}) or self._find_mutual({"Moon", "Venus"}):
            add("affection")
        if any(int(item.get("target_house") or 0) == 7 for item in self.overlays):
            add("partnership")
        if any(int(item.get("target_house") or 0) == 10 for item in self.overlays):
            add("public direction")
        if any(int(item.get("target_house") or 0) == 8 for item in self.overlays) or self.topics.get("intensity_merging_shared_resources"):
            add("intimacy and shared stakes")
        if not axes:
            axes = [self._top_topic_label(item[0]) for item in self._sorted_topics()[:3]]
        return axes

    def _glance_evidence_sentence(self) -> str:
        mutuals = self._top_mutuals(2, include_angle_only=False)
        overlays = self._top_overlays(2)
        parts = []
        if mutuals:
            parts.append("Immediate evidence includes " + _serial_join([_self_or_other_phrase(item, self.names) for item in mutuals]) + ".")
        if overlays:
            parts.append("The overlay pattern keeps that recognition landing through " + _serial_join([self._overlay_phrase(item) for item in overlays]) + ".")
        return _sentence_join(parts)

    def _attraction_close(self) -> str:
        if self._find_mutual({"Venus", "Saturn"}):
            return "So attraction here can feel both immediate and weight-bearing, as if desire and consequence arrive in the same breath."
        if self._find_mutual({"Venus", "Mars"}):
            return "That keeps the chemistry from staying hypothetical; it wants to register in the body."
        return "If this layer is not dominant, it still marks where the connection becomes unmistakably personal."

    def _play_evidence_sentences(self, limit: int = 3) -> list[str]:
        sentences: list[str] = []
        neptune_fifth = self._find_overlay("Neptune", 5)
        if neptune_fifth:
            sentences.append(
                directional_overlay_interpretation(
                    self.names[neptune_fifth["source_person"]],
                    "Neptune",
                    self.names[neptune_fifth["target_person"]],
                    "play and romance",
                    implication="That can make pleasure, fantasy, and desire feel more porous or idealized than they first appear.",
                )
            )
        moon_venus = self._find_mutual({"Moon", "Venus"}, aspect="Conjunction") or self._find_mutual({"Moon", "Venus"})
        if moon_venus and len(sentences) < limit:
            sentences.append(self._mutual_sentence(moon_venus, implication="That adds sweetness and responsiveness to the more expressive side of the bond."))
        venus_mars = self._find_mutual({"Venus", "Mars"}, aspect="Conjunction") or self._find_mutual({"Venus", "Mars"})
        if venus_mars and len(sentences) < limit:
            sentences.append(self._mutual_sentence(venus_mars, implication="That keeps flirtation, chemistry, and pursuit in active circulation."))
        fifth_overlay = next(
            (
                item for item in self.overlays
                if int(item.get("target_house") or 0) == 5 and item is not neptune_fifth
            ),
            None,
        )
        if fifth_overlay and len(sentences) < limit:
            sentences.append(
                directional_overlay_interpretation(
                    self.names[fifth_overlay["source_person"]],
                    _body_name(fifth_overlay.get("source_body")),
                    self.names[fifth_overlay["target_person"]],
                    "play and romance",
                )
            )
        return sentences[:limit]

    def _play_close(self) -> str:
        return "If this section stays secondary, it still shows where the connection becomes playful, idealized, or briefly less defended."

    def _portrait_synthesis(self) -> str:
        axes = self._core_signature_axes()
        if axes:
            return "The chart keeps tying together " + _serial_join(axes[:6]) + ", which is why the relationship resists being reduced to one simple story about chemistry, ease, or pressure."
        return "The chart keeps linking multiple layers of contact at once, which is why the relationship resists a thin reading."

    def _repeated_theme_specifics(self, theme: dict) -> str:
        theme_type = str(theme.get("theme_type") or "")
        person_a = theme.get("person_a_evidence") or {}
        person_b = theme.get("person_b_evidence") or {}
        if theme_type == "same_sign_emphasis":
            sign = person_a.get("sign") or person_b.get("sign")
            a_bodies = [_body_name(body) for body in (person_a.get("bodies") or [])[:2]]
            b_bodies = [_body_name(body) for body in (person_b.get("bodies") or [])[:2]]
            details = []
            if sign:
                details.append(f"Here the shared register is {sign}.")
            if a_bodies and b_bodies:
                details.append(f"{self.names['A']} carries it through {_serial_join(a_bodies)}, while {self.names['B']} carries it through {_serial_join(b_bodies)}.")
            return _sentence_join(details)
        if theme_type == "same_element_concentration":
            element = str(person_a.get("element") or person_b.get("element") or "")
            if element:
                return f"That gives both charts a similar {element} vocabulary for instinct, emphasis, and response."
        if theme_type == "same_modality_concentration":
            modality = str(person_a.get("modality") or person_b.get("modality") or "")
            if modality:
                return f"In practice that means both people tend to meet change through a similarly {modality} pacing style."
        if theme_type == "repeated_aspect_family":
            body_1 = _body_name(person_a.get("body_1") or person_b.get("body_1"))
            body_2 = _body_name(person_a.get("body_2") or person_b.get("body_2"))
            aspect = str(person_a.get("aspect") or person_b.get("aspect") or "")
            if body_1 and body_2 and aspect:
                return f"Both natal charts already know the {body_1}-{body_2} {aspect.lower()} pattern from the inside."
        return ""

    def _repeated_theme_bridge(self, themes: list[dict]) -> str:
        structural = [theme for theme in themes if str(theme.get("theme_type") or "") != "repeated_aspect_family"]
        aspectual = [theme for theme in themes if str(theme.get("theme_type") or "") == "repeated_aspect_family"]
        if structural and aspectual:
            return "Taken together, that means the recognition is happening at two levels at once: similar overall wiring and at least one echoed internal aspect problem or gift."
        if structural:
            return "The recognition here comes less from one exact repeated problem and more from a shared style of emphasis, pacing, or symbolic taste."
        if aspectual:
            return "What repeats most clearly is not broad temperament but a familiar internal aspect pattern, which can make certain reactions feel strangely pre-known."
        return ""

    def _pure_angle_penalty(self, mutual: dict, *, include_angle_only: bool) -> int:
        return 0 if include_angle_only else int(self._is_pure_angle_mutual(mutual))

    def _dependency_penalty(self, mutual: dict) -> int:
        return 0 if str(mutual.get("dependency") or "") == "body_to_body" else 1

    def _is_pure_angle_mutual(self, mutual: dict) -> bool:
        entries = [entry for entry in mutual.get("mutual_key", []) or [] if isinstance(entry, dict)]
        bodies = [entry.get("body") for entry in entries]
        return bool(bodies) and all(body in ANGLE_SET for body in bodies)

    def _directional_landing_body(self, source_person: str, target_person: str) -> str:
        overlays = [
            item for item in self.overlays
            if item.get("source_person") == source_person and item.get("target_person") == target_person
        ]
        if not overlays:
            return ""
        overlays.sort(key=lambda item: (-BODY_WEIGHTS.get(str(item.get("source_body") or ""), 0.0), item.get("target_house") or 99))
        fields = self._directional_fields(source_person, target_person)
        field_sentence = (
            f"{self.names[source_person]} lands for {self.names[target_person]} through {_serial_join(fields[:3])}, with the strongest emphasis arriving in lived rather than abstract ways."
            if fields
            else ""
        )
        bullet_lines = ["- " + self._directional_overlay_bullet(overlay) for overlay in overlays[:3]]
        return _sentence_join([field_sentence, "\n".join(bullet_lines)])

    def _directional_overlay_bullet(self, overlay: dict) -> str:
        house_label = HOUSE_LABELS.get(int(overlay.get("target_house") or 0), "lived field")
        implication = self._directional_implication(overlay)
        return directional_overlay_interpretation(
            self.names[overlay.get("source_person")],
            _body_name(overlay.get("source_body")),
            self.names[overlay.get("target_person")],
            house_label,
            implication=implication,
        )

    def _directional_implication(self, overlay: dict) -> str:
        source_body = str(overlay.get("source_body") or "")
        house = int(overlay.get("target_house") or 0)
        if source_body == "Moon" and house == 3:
            return "That gives everyday exchange an emotional undertone rather than keeping feeling separate from conversation."
        if source_body == "Sun" and house == 8:
            return "The contact often feels consequential quickly, because visibility is entering a field of trust, exposure, and deeper stakes."
        if source_body == "Venus" and house == 7:
            return "That tends to make recognition, liking, and relational receptivity easier to register on contact."
        if source_body == "Mars" and house == 4:
            return "Directness and activation reach private ground, not only the outer surface of the relationship."
        if house == 10:
            return "It tends to shape how the relationship is felt in public direction, ambition, or visible trajectory."
        if house == 11:
            return "It often affects the friendship layer, shared networks, and the future-facing side of the bond."
        if house == 5:
            return "That keeps play, chemistry, and expressive spontaneity in motion."
        return ""

    def _mutual_sentence(self, mutual: dict, *, implication: str | None = None) -> str:
        entries = [entry for entry in mutual.get("mutual_key", []) or [] if isinstance(entry, dict)]
        if len(entries) < 2:
            return ""
        aspect = str(mutual.get("aspect") or "")
        return mutual_contact_interpretation(
            self.names.get(entries[0].get("person")),
            _body_name(entries[0].get("body")),
            aspect,
            self.names.get(entries[1].get("person")),
            _body_name(entries[1].get("body")),
            implication=implication,
        )


def _self_or_other_phrase(mutual: dict, names: dict[str, str]) -> str:
    entries = [entry for entry in mutual.get("mutual_key", []) or [] if isinstance(entry, dict)]
    if len(entries) < 2:
        return "a major mutual contact"
    left = f"{names.get(entries[0].get('person'), entries[0].get('person'))}'s {_body_name(entries[0].get('body'))}"
    right = f"{names.get(entries[1].get('person'), entries[1].get('person'))}'s {_body_name(entries[1].get('body'))}"
    return f"{left} {_aspect_adjective(str(mutual.get('aspect') or ''))} {right}"


def _mutual_people_by_body(mutual: dict, first_body: str, second_body: str) -> tuple[str | None, str | None]:
    first_person = None
    second_person = None
    for entry in mutual.get("mutual_key", []) or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("body") == first_body:
            first_person = entry.get("person")
        if entry.get("body") == second_body:
            second_person = entry.get("person")
    return first_person, second_person
