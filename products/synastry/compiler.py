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


def _body_name(body: str | None) -> str:
    return str(body or "").replace("_", " ")


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
            "A": self.relationship_meta.get("person_a_label") or "Person A",
            "B": self.relationship_meta.get("person_b_label") or "Person B",
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
        families = self._evidence_family_labels(signature)
        topic_leaf = select_topic_signature_leaf(topic_key)
        polarity_leaf = select_topic_polarity_leaf(convergence.get("polarity") or signature.get("polarity"))
        confidence_leaf = select_topic_confidence_leaf(signature.get("confidence_state") or convergence.get("confidence_state"))
        topic_intro = self._topic_intro(topic_key, signature)
        bridge = ""
        if families:
            bridge = f"The evidence repeats through {_serial_join(families[:4])}, so the theme does not stay abstract for long."
        modifier = self._topic_modifier(topic_key)
        body = _sentence_join([topic_intro, bridge, topic_leaf.get("body"), polarity_leaf.get("body"), modifier, confidence_leaf.get("body")])
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
        sorted_topics = self._sorted_topics()
        top_labels = [self._top_topic_label(item[0]) for item in sorted_topics[:3]]
        main_sentence = "The relationship at a glance is organized most clearly around " + _serial_join(top_labels) + "."
        attraction = self._attraction_summary()
        depth = self._depth_summary()
        composite = self._composite_brief()
        body = _sentence_join([main_sentence, attraction, depth, composite])
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
        top_topic = self._sorted_topics()[0][0] if self._sorted_topics() else None
        top_mutuals = self._top_mutuals(3)
        top_overlays = self._top_overlays(3)
        sentences = []
        if top_topic:
            sentences.append(f"The core signature here is {self._top_topic_label(top_topic)}, not as a vague atmosphere but as a repeated pattern that keeps being confirmed by live evidence.")
        if top_mutuals:
            phrases = [_self_or_other_phrase(mutual, self.names) for mutual in top_mutuals]
            sentences.append(f"The highest-salience cross-chart contacts include {_serial_join(phrases)}, which gives the relationship its most immediate points of recognition and activation.")
        if top_overlays:
            overlay_phrase = _serial_join([self._overlay_phrase(item) for item in top_overlays])
            sentences.append(f"The lived terrain is not symmetrical either: {overlay_phrase}.")
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
        cluster = self._attraction_cluster_records()
        if not cluster:
            return None
        sentences = [self._attraction_summary()]
        if self._find_overlay("Venus", 7):
            overlay = self._find_overlay("Venus", 7)
            sentences.append(
                f"{self.names[overlay['source_person']]}'s Venus lands in {self.names[overlay['target_person']]}'s seventh house, so {self.names[overlay['source_person']]} registers strongly in {self.names[overlay['target_person']]}'s partnership field."
            )
        if self._find_mutual({"Venus", "Ascendant"}, aspect="Opposition"):
            mutual = self._find_mutual({"Venus", "Ascendant"}, aspect="Opposition")
            source, target = _mutual_people_by_body(mutual, "Venus", "Ascendant")
            if source and target:
                sentences.append(
                    f"{self.names[source]}'s Venus opposes {self.names[target]}'s Ascendant, which makes relational visibility hard to miss on first encounter."
                )
        catalytic = self._catalytic_heat_summary()
        if catalytic:
            sentences.append(catalytic)
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
        records = [
            item for item in self.overlays
            if item.get("target_house") == 5 or item.get("source_body") in {"Venus", "Neptune"}
        ]
        if not records:
            return None
        pieces = [
            "Play, romance, and idealization are present as a secondary but real layer in the connection."
        ]
        neptune_fifth = self._find_overlay("Neptune", 5)
        if neptune_fifth:
            pieces.append(
                f"{self.names[neptune_fifth['source_person']]}'s Neptune in {self.names[neptune_fifth['target_person']]}'s fifth house can make pleasure, creativity, and desire feel more porous, atmospheric, or idealized than they first appear."
            )
        venus_seventh = self._find_overlay("Venus", 7)
        if venus_seventh:
            pieces.append(
                f"Venus overlay material keeps the sweeter side of attraction visible, which helps this section read as more than pure heat."
            )
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
            fields = self._directional_fields(source_person, target_person)
            if not fields:
                continue
            blocks.append(
                {
                    "id": f"directional_landing:{source_person}:{target_person}",
                    "title": f"How {self.names[source_person]} Lands for {self.names[target_person]}",
                    "body": "Strongest activations: " + "\n".join(f"- {field}" for field in fields),
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
            confidence_leaf = select_repeated_theme_confidence_leaf(theme.get("confidence_state"))
            phrase = theme_leaf.get("body")
            theme_phrases.append(_sentence_join([phrase, confidence_leaf.get("body")]))
        body = _sentence_join(
            [
                "The shared natal baseline matters because this relationship is not being built from completely unfamiliar symbolic material.",
                "At minimum, both people are arriving with some similar natal architecture already in place.",
                *theme_phrases[:2],
                theme_phrases[2] if len(theme_phrases) > 2 else "",
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
            "Taken together, this relationship does not read as casual, purely conceptual, or easy to keep at arm's length.",
            self._attraction_summary(),
            self._depth_summary(),
            "The strongest through-line is that emotional rhythm, communication, attraction, and consequence keep crossing into each other rather than staying compartmentalized.",
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

    def _top_mutuals(self, limit: int) -> list[dict]:
        ordered = sorted(
            self.mutuals,
            key=lambda item: (
                -float(item.get("salience", 0.0) or 0.0),
                float(item.get("orb", 99.0) or 99.0),
            ),
        )
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


def _self_or_other_phrase(mutual: dict, names: dict[str, str]) -> str:
    entries = [entry for entry in mutual.get("mutual_key", []) or [] if isinstance(entry, dict)]
    if len(entries) < 2:
        return "a major mutual contact"
    left = f"{names.get(entries[0].get('person'), entries[0].get('person'))}'s {_body_name(entries[0].get('body'))}"
    right = f"{names.get(entries[1].get('person'), entries[1].get('person'))}'s {_body_name(entries[1].get('body'))}"
    aspect = str(mutual.get("aspect") or "").lower()
    return f"{left} {aspect}s {right}" if aspect == "opposition" else f"{left} {aspect} {right}"


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
