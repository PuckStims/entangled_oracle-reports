"""
formulas/proprietary_indexes.py — Entangled Oracle Formula Engine

Implements:
- KVQ: Kassandra Validation Quotient
- MKI: Mythkeeper Index
- RWI: Reality Weaver Index
- DFIS: Dark Feminine Integration Score
- Catalyst Index
- AHL: Ancestral Lineage Thread
- NGE: Narrative Genre Engine (v0.2)

Compatibility note:
MCQ, SIREN, and MAGNETIC are retained temporarily so the existing
Asteroid Portrait renderer continues to run while its block/template
layer is migrated to NGE.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AHL_TIERS, ORB_CONFIG, SCORE_TIERS
from formulas.governance_registry import (
    METHOD_STATUS_EO_PROPRIETARY,
    REPORT_PROFILE_CORE_STANDARD_PLUS_EO,
    REPORT_PROFILE_FULL_ENTANGLED_ORACLE,
)
from selectors.utils import (
    aspect_strength,
    aspect_strength_angle,
    body_exists,
    get_body_modality,
    get_body_sign,
    get_score_tier,
    house_match,
    is_retrograde,
    sign_element_match,
)


# ── EAS Expression Matrices ────────────────────────────────────
#
# These names are the user-facing identity layer. Formula machinery
# determines archetype / genre + driver modality; this matrix resolves
# the final expression label.

EXPRESSION_MATRIX = {
    "The World Weaver": {
        "cardinal": "The First Thread",
        "fixed": "The Living Loom",
        "mutable": "The Network Gardener",
    },
    "The Trickster Architect": {
        "cardinal": "The Structured Void",
        "fixed": "The Pregnant Dark",
        "mutable": "The Unwritten",
    },
    "The Disruptor": {
        "cardinal": "The Messenger From Tomorrow",
        "fixed": "The Eternal Passerby",
        "mutable": "The Translator Between Worlds",
    },
    "The Storyteller": {
        "cardinal": "The Truth Declarer",
        "fixed": "The Lorekeeper",
        "mutable": "The Memory Singer",
    },
    "The Archivist": {
        "cardinal": "The Memory Diver",
        "fixed": "The Vaultkeeper",
        "mutable": "The Ancestor's Voice",
    },
    "The Resurrector": {
        "cardinal": "The Reclaimer",
        "fixed": "The Ruin Walker",
        "mutable": "The Forgotten Cartographer",
    },
    "The Scholar": {
        "cardinal": "The Descending Light",
        "fixed": "The Keeper of Names",
        "mutable": "The Grace Between Worlds",
    },
    "The Translator": {
        "cardinal": "The Signal Unearther",
        "fixed": "The Lineage Keeper",
        "mutable": "The Archaeologist of Meaning",
    },
    "The Sovereign Queen": {
        "cardinal": "The Boundary Architect",
        "fixed": "The Untameable",
        "mutable": "The Self-Exiled Sovereign",
    },
    "The Alchemist": {
        "cardinal": "The Severing Mother",
        "fixed": "The Crucible",
        "mutable": "The Unbound",
    },
    "The Enchantress": {
        "cardinal": "The Hedge Witch",
        "fixed": "The Hearth Witch",
        "mutable": "The Wild Apothecary",
    },
    "The Warrior": {
        "cardinal": "The Righteous Flame",
        "fixed": "The Unsilenced",
        "mutable": "The Strategic Fire",
    },
    "The Crone/Oracle": {
        "cardinal": "The Threshold Keeper",
        "fixed": "The Dark Lantern",
        "mutable": "The Threshold Keybearer",
    },
    "The Awakener": {
        "cardinal": "The Lightning Strike",
        "fixed": "The Permanent Disruption",
        "mutable": "The Rolling Thunder",
    },
    "The Mirror": {
        "cardinal": "The Wound Opener",
        "fixed": "The Wounded Healer",
        "mutable": "The Scar Teacher",
    },
    "The Catalyst": {
        "cardinal": "The Fated Encounter",
        "fixed": "The Karmic Anchor",
        "mutable": "The Refrain",
    },
    "The Herald": {
        "cardinal": "The First Arrival",
        "fixed": "The Keeper of the Message",
        "mutable": "The Quicksilver Word",
    },
    "Vindicated Oracle": {
        "cardinal": "The Returning Voice",
        "fixed": "The Still Standing",
        "mutable": "The Persistent Signal",
    },
    "Empathic Observer": {
        "cardinal": "The Room Reader",
        "fixed": "The Still Witness",
        "mutable": "The Undercurrent Tracker",
    },
    "Grounded Realist": {
        "cardinal": "The Pattern Namer",
        "fixed": "The Reality Anchor",
        "mutable": "The Plain Witness",
    },
    "The Epic": {
        "cardinal": "The Founding Quest",
        "fixed": "The Eternal Champion",
        "mutable": "The Wandering Hero",
    },
    "The Mythology": {
        "cardinal": "The Origin Keeper",
        "fixed": "The Living Symbol",
        "mutable": "The Carried Tale",
    },
    "The Mystery": {
        "cardinal": "The Revelation",
        "fixed": "The Hidden Flame",
        "mutable": "The Veilwalker",
    },
    "The Masquerade": {
        "cardinal": "The Performer",
        "fixed": "The Masterpiece",
        "mutable": "The Chameleon",
    },
    "The Odyssey": {
        "cardinal": "The Departure",
        "fixed": "The Long Voyage",
        "mutable": "The Returning Wanderer",
    },
    "The Kingdom": {
        "cardinal": "The Founder",
        "fixed": "The Regent",
        "mutable": "The Successor",
    },
    "The Heist": {
        "cardinal": "The Architect",
        "fixed": "The Vault",
        "mutable": "The Wildcard",
    },
    "The Fairy Tale": {
        "cardinal": "The Wish",
        "fixed": "The Enchantment",
        "mutable": "The Happily Ever After",
    },
    "The Calling": {
        "cardinal": "The Invitation",
        "fixed": "The Temptation",
        "mutable": "The Choice",
    },
    "The Vow": {
        "cardinal": "The Promise",
        "fixed": "The Devoted Heart",
        "mutable": "The Pilgrim",
    },
    "The Romance": {
        "cardinal": "The Pursuer",
        "fixed": "The Beloved",
        "mutable": "The Lover in Every Season",
    },
    "The Festival": {
        "cardinal": "The Gathering",
        "fixed": "The Feast",
        "mutable": "The Dance",
    },
}

NGE_GENRES = {
    "Apollo": {
        "Heroic": ("The Epic", "What must be achieved?"),
        "Legacy": ("The Mythology", "What must be remembered?"),
        "Prophetic": ("The Mystery", "What must be revealed?"),
        "Artistic": ("The Masquerade", "What must be expressed?"),
    },
    "Themis": {
        "Momentum": ("The Odyssey", "What must be journeyed?"),
        "Pattern": ("The Kingdom", "What must be built?"),
    },
    "Terpsichore": {
        "Improvisation": ("The Heist", "What must be seized?"),
        "Grace": ("The Fairy Tale", "What must be believed?"),
    },
    "Sirene": {
        "Magnetic Test": ("The Calling", "What calls to you?"),
        "Devotion": ("The Vow", "What do you devote yourself to?"),
    },
    "Aphrodite": {
        "Sovereignty": ("The Romance", "Who do you choose?"),
        "Embodiment": ("The Festival", "What deserves celebration?"),
    },
}


# ── Shared Helpers ─────────────────────────────────────────────

def _argmax(weight_map: dict) -> tuple[str, float]:
    """
    Returns the first highest-scoring key and its score.

    Python dictionaries preserve insertion order, which gives ties a stable,
    intentional first-listed resolution.
    """
    if not weight_map:
        return "", 0.0

    key = max(weight_map, key=weight_map.get)
    return key, float(weight_map[key])


def _scale_to_ten(raw_score: float, theoretical_max: float) -> float:
    """
    Converts an index's weighted raw score to the shared 0–10 EAS scale.

    The individual matrices have different theoretical maxima. This keeps
    activation states comparable without discarding the raw audit value.
    """
    if theoretical_max <= 0:
        return 0.0

    return min(10.0, (raw_score / theoretical_max) * 10.0)


def _activation_state(score_ten: float) -> str:
    """Maps a 0–10 display score to the EAS activation language."""
    if score_ten <= 0:
        return "Suppressed"
    if score_ten < 3.0:
        return "Awakening"
    if score_ten < 6.0:
        return "Embodied"
    return "Sovereign"


def _visibility(score_ten: float) -> tuple[bool, bool]:
    """
    Returns:
        suppressed: omit entirely
        display_full: render complete section

    0.1–1.9 is retained as an optional subtle-signal state.
    """
    return score_ten == 0.0, score_ten >= 2.0


def _expression_for(archetype_or_genre: str, modality: str) -> str:
    """Resolves a named EAS expression, with a safe fallback."""
    normalized_modality = (modality or "").lower()
    return EXPRESSION_MATRIX.get(
        archetype_or_genre,
        {},
    ).get(normalized_modality, "")


def _modality_match(payload: dict, body: str, modality: str) -> int:
    """Returns 1 when a body's sign has the requested modality."""
    return 1 if get_body_modality(payload, body) == modality.lower() else 0


def _sign_match(payload: dict, body: str, sign: str) -> int:
    """Returns 1 when a body occupies the requested zodiac sign."""
    return 1 if get_body_sign(payload, body) == sign else 0


def _either_house(payload: dict, body: str, first: int, second: int) -> int:
    """Returns 1 when a body occupies either of two designated houses."""
    return max(
        house_match(payload, body, first),
        house_match(payload, body, second),
    )


def _result(
    *,
    raw_score: float,
    theoretical_max: float,
    archetype: str,
    driver_body: str,
    payload: dict,
    components: dict,
    expression_basis: str | None = None,
    extra: dict | None = None,
    method_name: str = "",
    body_or_point: str | None = None,
    limitations: list[str] | None = None,
    visibility_state: str = "eo_overlay_only",
) -> dict:
    """
    Builds the standardized formula result shape used across EAS indexes.

    score             normalized 0.0–1.0, safe for ranking/sorting
    activation_score  user-facing 0.0–10.0 calibration scale
    raw_score         audit/debug value in the native formula scale
    """
    activation_score = _scale_to_ten(raw_score, theoretical_max)
    score = activation_score / 10.0
    modality = get_body_modality(payload, driver_body)
    expression_key = expression_basis or archetype
    suppressed, display_full = _visibility(activation_score)

    result = {
        "method_status": METHOD_STATUS_EO_PROPRIETARY,
        "method_name": method_name or archetype,
        "body_or_point": body_or_point or driver_body,
        "formula_version": "v0.2",
        "report_eligibility": [
            REPORT_PROFILE_CORE_STANDARD_PLUS_EO,
            REPORT_PROFILE_FULL_ENTANGLED_ORACLE,
        ],
        "visibility_state": visibility_state,
        "birth_time_dependency": "varies_by_formula",
        "confidence_state": "exact_birth_time"
        if not bool(payload.get("user_profile", {}).get("simple_mode") or payload.get("simple_mode"))
        else "angle_dependent_unavailable",
        "supporting_inputs": list(components.keys()),
        "limitations": list(limitations or []),
        "score": round(score, 4),
        "activation_score": round(activation_score, 4),
        "raw_score": round(raw_score, 4),
        "theoretical_max": round(theoretical_max, 4),
        "tier": get_score_tier(score),
        "archetype": archetype,
        "driver_body": driver_body,
        "driver_modality": modality,
        "expression": _expression_for(expression_key, modality),
        "activation": _activation_state(activation_score),
        "suppressed": suppressed,
        "subtle_signal": 0.0 < activation_score < 2.0,
        "display_full": display_full,
        "components": {
            name: round(value, 4) if isinstance(value, float) else value
            for name, value in components.items()
        },
    }

    if extra:
        result.update(extra)

    return result


# ── KVQ — Kassandra Validation Quotient ────────────────────────

def compute_kvq(payload: dict, orb_config: dict | None = None) -> dict:
    """
    KVQ v0.2.

    Mercury, Uranus, and Saturn use hard aspects only. Easy Kassandra–
    Mercury contact is retained as a non-scoring "clear translator" nuance.
    """
    if orb_config is None:
        orb_config = ORB_CONFIG

    hard_aspects = ["Conjunction", "Square", "Opposition"]

    kass_angle = max(
        aspect_strength_angle(payload, "Kassandra", "Ascendant",
                              ["Conjunction"], orb_config),
        aspect_strength_angle(payload, "Kassandra", "Midheaven",
                              ["Conjunction"], orb_config),
        aspect_strength_angle(payload, "Kassandra", "Imum_Coeli",
                              ["Conjunction"], orb_config),
    )

    kass_merc_hard = aspect_strength(
        payload, "Kassandra", "Mercury", hard_aspects, orb_config
    )
    kass_merc_easy = aspect_strength(
        payload, "Kassandra", "Mercury",
        ["Sextile", "Trine"], orb_config
    )
    kass_uran_hard = aspect_strength(
        payload, "Kassandra", "Uranus", hard_aspects, orb_config
    )
    kass_saturn_hard = aspect_strength(
        payload, "Kassandra", "Saturn", hard_aspects, orb_config
    )
    kass_12th = house_match(payload, "Kassandra", 12)

    raw_score = (
        kass_angle * 3.0
        + kass_merc_hard * 2.0
        + kass_uran_hard * 2.5
        + kass_12th * 1.8
        + kass_saturn_hard * 1.5
    )

    activation_score = _scale_to_ten(raw_score, 10.8)

    if activation_score >= 7.0:
        archetype = "Vindicated Oracle"
    elif activation_score >= 4.0:
        archetype = "Empathic Observer"
    else:
        archetype = "Grounded Realist"

    return _result(
        raw_score=raw_score,
        theoretical_max=10.8,
        archetype=archetype,
        driver_body="Kassandra",
        payload=payload,
        components={
            "kass_angle": kass_angle,
            "kass_merc_hard": kass_merc_hard,
            "kass_merc_easy": kass_merc_easy,
            "kass_uran_hard": kass_uran_hard,
            "kass_saturn_hard": kass_saturn_hard,
            "kass_12th": kass_12th,
        },
        extra={
            "clear_translator": kass_merc_easy > 0.0,
        },
        method_name="Kassandra Validation Quotient",
    )


# ── MKI — Mythkeeper Index ─────────────────────────────────────

def compute_mki(payload: dict, orb_config: dict | None = None) -> dict:
    """MKI v0.2 — Knowledge Legacy."""
    if orb_config is None:
        orb_config = ORB_CONFIG

    w_mnemosyne = (
        aspect_strength(
            payload, "Mnemosyne", "Moon",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + _either_house(payload, "Mnemosyne", 4, 12) * 1.5
        + aspect_strength(
            payload, "Mnemosyne", "Saturn",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
    )

    w_atlantis = (
        aspect_strength(
            payload, "Atlantis", "Pluto",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 2.5
        + _either_house(payload, "Atlantis", 8, 12) * 1.5
        + aspect_strength(
            payload, "Atlantis", "Neptune",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
    )

    w_sophia = (
        aspect_strength(
            payload, "Sophia", "Jupiter",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + _either_house(payload, "Sophia", 9, 12) * 1.5
        + aspect_strength(
            payload, "Sophia", "Mercury",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
    )

    w_hermes = (
        aspect_strength(
            payload, "Hermes", "Mercury",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + _either_house(payload, "Hermes", 3, 12) * 1.5
        + aspect_strength(
            payload, "Hermes", "Neptune",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
    )

    weights = {
        "The Archivist": w_mnemosyne,
        "The Resurrector": w_atlantis,
        "The Scholar": w_sophia,
        "The Translator": w_hermes,
    }
    archetype, _ = _argmax(weights)

    drivers = {
        "The Archivist": "Mnemosyne",
        "The Resurrector": "Atlantis",
        "The Scholar": "Sophia",
        "The Translator": "Hermes",
    }

    return _result(
        raw_score=sum(weights.values()),
        theoretical_max=20.5,
        archetype=archetype,
        driver_body=drivers[archetype],
        payload=payload,
        components={
            "mnemosyne": w_mnemosyne,
            "atlantis": w_atlantis,
            "sophia": w_sophia,
            "hermes": w_hermes,
        },
        method_name="Mythkeeper Index",
    )


# ── RWI — Reality Weaver Index ─────────────────────────────────

def compute_rwi(payload: dict, orb_config: dict | None = None) -> dict:
    """RWI v0.2 — Reality Field."""
    if orb_config is None:
        orb_config = ORB_CONFIG

    w_arachne = (
        aspect_strength(
            payload, "Arachne", "North_Node",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + house_match(payload, "Arachne", 11) * 1.5
        + aspect_strength(
            payload, "Arachne", "Saturn",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
    )

    w_chaos = (
        aspect_strength(
            payload, "Chaos", "Uranus",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 2.5
        + aspect_strength(
            payload, "Chaos", "Themis",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.5
        + _modality_match(payload, "Chaos", "mutable") * 1.0
    )

    w_hermes = (
        aspect_strength(
            payload, "Hermes", "Uranus",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 2.0
        + _either_house(payload, "Hermes", 3, 9) * 1.5
        + aspect_strength(
            payload, "Hermes", "Mercury",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 1.5
    )

    w_apollo = (
        aspect_strength(
            payload, "Apollo", "Sun",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + aspect_strength(
            payload, "Apollo", "Jupiter",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
        + sign_element_match(payload, "Apollo", "fire") * 1.0
    )

    weights = {
        "The World Weaver": w_arachne,
        "The Trickster Architect": w_chaos,
        "The Disruptor": w_hermes,
        "The Storyteller": w_apollo,
    }
    archetype, _ = _argmax(weights)

    drivers = {
        "The World Weaver": "Arachne",
        "The Trickster Architect": "Chaos",
        "The Disruptor": "Hermes",
        "The Storyteller": "Apollo",
    }

    return _result(
        raw_score=sum(weights.values()),
        theoretical_max=20.5,
        archetype=archetype,
        driver_body=drivers[archetype],
        payload=payload,
        components={
            "arachne": w_arachne,
            "chaos": w_chaos,
            "hermes": w_hermes,
            "apollo": w_apollo,
        },
        method_name="Reality Weaver Index",
    )


# ── DFIS — Dark Feminine Integration Score ─────────────────────

def compute_dfis(payload: dict, orb_config: dict | None = None) -> dict:
    """
    DFIS v0.2 — Power Current.

    Black Moon Lilith is intentionally distinct from asteroid Lilith.
    The Warrior component is Medea, not a second Kaali component.
    """
    if orb_config is None:
        orb_config = ORB_CONFIG

    lilith_body = "Lilith_BML"

    w_lilith = (
        sign_element_match(payload, lilith_body, "earth") * 1.5
        + house_match(payload, lilith_body, 1)
        + aspect_strength(
            payload, lilith_body, "Saturn",
            ["Conjunction", "Square", "Trine"], orb_config
        )
    )

    w_kaali = (
        sign_element_match(payload, "Kaali", "water")
        + aspect_strength(
            payload, "Kaali", "Pluto",
            ["Conjunction", "Square", "Opposition"], orb_config
        )
    )

    w_circe = (
        _either_house(payload, "Circe", 2, 7)
        + aspect_strength(
            payload, "Circe", "Venus",
            ["Conjunction", "Sextile", "Trine"], orb_config
        )
    )

    w_medea = (
        sign_element_match(payload, "Medea", "fire")
        + aspect_strength(
            payload, "Medea", "Mars",
            ["Conjunction", "Square", "Opposition"], orb_config
        )
    )

    w_hekate = (
        house_match(payload, "Hekate", 12)
        + aspect_strength(
            payload, "Hekate", "Moon",
            ["Conjunction", "Sextile", "Trine"], orb_config
        )
    )

    weights = {
        "The Sovereign Queen": w_lilith,
        "The Alchemist": w_kaali,
        "The Enchantress": w_circe,
        "The Warrior": w_medea,
        "The Crone/Oracle": w_hekate,
    }
    archetype, _ = _argmax(weights)

    drivers = {
        "The Sovereign Queen": lilith_body,
        "The Alchemist": "Kaali",
        "The Enchantress": "Circe",
        "The Warrior": "Medea",
        "The Crone/Oracle": "Hekate",
    }

    return _result(
        raw_score=sum(weights.values()),
        theoretical_max=11.5,
        archetype=archetype,
        driver_body=drivers[archetype],
        payload=payload,
        components={
            "lilith": w_lilith,
            "kaali": w_kaali,
            "circe": w_circe,
            "medea": w_medea,
            "hekate": w_hekate,
        },
        extra={
            "lilith_source": lilith_body,
        },
        method_name="Dark Feminine Integration Score",
        limitations=["black_moon_lilith_and_asteroid_lilith_are_not_interchangeable"],
    )


# ── Catalyst Index ─────────────────────────────────────────────

def compute_catalyst(payload: dict, orb_config: dict | None = None) -> dict:
    """Catalyst Index v0.2 — Impact Radius."""
    if orb_config is None:
        orb_config = ORB_CONFIG

    w_uranus = (
        aspect_strength_angle(
            payload, "Uranus", "Descendant",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 3.0
    )

    w_chiron = house_match(payload, "Chiron", 7) * 2.5

    destinn_vertex = aspect_strength_angle(
        payload, "Destinn", "Vertex", ["Conjunction"], orb_config
    )
    karma_vertex = aspect_strength_angle(
        payload, "Karma", "Vertex", ["Conjunction"], orb_config
    )
    w_karma_destinn = (destinn_vertex + karma_vertex) * 2.0

    w_hermes = (
        aspect_strength(
            payload, "Hermes", "Uranus",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
    )

    weights = {
        "The Awakener": w_uranus,
        "The Mirror": w_chiron,
        "The Catalyst": w_karma_destinn,
        "The Herald": w_hermes,
    }
    archetype, _ = _argmax(weights)

    if destinn_vertex > karma_vertex:
        catalyst_driver = "Destinn"
    else:
        catalyst_driver = "Karma"

    drivers = {
        "The Awakener": "Uranus",
        "The Mirror": "Chiron",
        "The Catalyst": catalyst_driver,
        "The Herald": "Hermes",
    }

    return _result(
        raw_score=sum(weights.values()),
        theoretical_max=11.0,
        archetype=archetype,
        driver_body=drivers[archetype],
        payload=payload,
        components={
            "uranus": w_uranus,
            "chiron": w_chiron,
            "karma_destinn": w_karma_destinn,
            "destinn_vertex": destinn_vertex,
            "karma_vertex": karma_vertex,
            "hermes": w_hermes,
        },
        method_name="Catalyst Index",
    )


# ── AHL — Ancestral Lineage Thread ─────────────────────────────

def compute_ahl(payload: dict, orb_config: dict | None = None) -> dict:
    """
    AHL v0.2 — optional ancestral-lineage signal.

    AHL intentionally keeps its raw 0–5.5 score in `score` for backward
    compatibility with the existing portrait blocks and AHL thresholds.
    """
    if orb_config is None:
        orb_config = ORB_CONFIG

    dna_retro = (1 if is_retrograde(payload, "DNA") else 0) * 2.0

    child_chiron = (
        aspect_strength(
            payload, "Child", "Chiron",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 1.8
    )

    anubis_4th = house_match(payload, "Anubis", 4) * 1.7

    raw_score = dna_retro + child_chiron + anubis_4th

    if raw_score >= AHL_TIERS["DEEP"]:
        tier = "DEEP"
    elif raw_score >= AHL_TIERS["PRESENT"]:
        tier = "PRESENT"
    else:
        tier = "BELOW_THRESHOLD"

    return {
        "method_status": METHOD_STATUS_EO_PROPRIETARY,
        "method_name": "Ancestral Lineage Thread",
        "body_or_point": "AHL",
        "formula_version": "v0.2",
        "report_eligibility": [
            REPORT_PROFILE_CORE_STANDARD_PLUS_EO,
            REPORT_PROFILE_FULL_ENTANGLED_ORACLE,
        ],
        "visibility_state": "eo_overlay_only",
        "birth_time_dependency": "varies_by_formula",
        "confidence_state": "exact_birth_time"
        if not bool(payload.get("user_profile", {}).get("simple_mode") or payload.get("simple_mode"))
        else "angle_dependent_unavailable",
        "supporting_inputs": ["dna_retro", "child_chiron", "anubis_4th"],
        "limitations": [],
        "score": round(raw_score, 4),
        "normalized_score": round(min(1.0, raw_score / 5.5), 4),
        "activation_score": round(_scale_to_ten(raw_score, 5.5), 4),
        "raw_score": round(raw_score, 4),
        "theoretical_max": 5.5,
        "tier": tier,
        "fires": raw_score >= AHL_TIERS["PRESENT"],
        "suppressed": raw_score == 0.0,
        "subtle_signal": 0.0 < raw_score < AHL_TIERS["PRESENT"],
        "display_full": raw_score >= AHL_TIERS["PRESENT"],
        "components": {
            "dna_retro": round(dna_retro, 4),
            "child_chiron": round(child_chiron, 4),
            "anubis_4th": round(anubis_4th, 4),
        },
    }


# ── NGE — Narrative Genre Engine ───────────────────────────────

def compute_nge(payload: dict, orb_config: dict | None = None) -> dict:
    """
    Narrative Genre Engine v0.2.

    Pass 1:
        Each body receives the maximum of its internal facet scores.
    Pass 2:
        The dominant body's highest facet resolves its genre.
    """
    if orb_config is None:
        orb_config = ORB_CONFIG

    # Apollo facets
    apollo_heroic = (
        aspect_strength(
            payload, "Apollo", "Sun",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + aspect_strength(
            payload, "Apollo", "Mars",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
        + sign_element_match(payload, "Apollo", "fire") * 1.0
    )
    apollo_legacy = (
        aspect_strength(
            payload, "Apollo", "Saturn",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + house_match(payload, "Apollo", 10) * 1.5
        + _modality_match(payload, "Apollo", "fixed") * 1.0
    )
    apollo_prophetic = (
        aspect_strength(
            payload, "Apollo", "Neptune",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + house_match(payload, "Apollo", 12) * 1.5
        + sign_element_match(payload, "Apollo", "water") * 1.0
    )
    apollo_artistic = (
        aspect_strength(
            payload, "Apollo", "Venus",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + house_match(payload, "Apollo", 5) * 1.5
        + _sign_match(payload, "Apollo", "Libra") * 1.0
    )

    # Themis facets
    themis_momentum = (
        aspect_strength(
            payload, "Themis", "Jupiter",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + aspect_strength(
            payload, "Themis", "Destinn",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + _modality_match(payload, "Themis", "cardinal") * 1.0
        + _either_house(payload, "Themis", 1, 9) * 1.5
    )
    themis_pattern = (
        aspect_strength(
            payload, "Themis", "Saturn",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + aspect_strength(
            payload, "Themis", "Sun",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
        + sign_element_match(payload, "Themis", "earth") * 1.0
        + _either_house(payload, "Themis", 2, 10) * 1.5
    )

    # Terpsichore facets
    terps_improvisation = (
        aspect_strength(
            payload, "Terpsichore", "Uranus",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 2.0
        + aspect_strength(
            payload, "Terpsichore", "Mercury",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
        + _modality_match(payload, "Terpsichore", "mutable") * 1.0
        + _either_house(payload, "Terpsichore", 3, 5) * 1.5
    )
    terps_grace = (
        aspect_strength(
            payload, "Terpsichore", "Venus",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + aspect_strength(
            payload, "Terpsichore", "Jupiter",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 1.5
        + max(
            sign_element_match(payload, "Terpsichore", "air"),
            sign_element_match(payload, "Terpsichore", "water"),
        ) * 1.0
        + _either_house(payload, "Terpsichore", 5, 11) * 1.5
    )

    # Sirene facets
    sirene_magnetic = (
        aspect_strength(
            payload, "Sirene", "Pluto",
            ["Conjunction", "Square", "Opposition"], orb_config
        ) * 2.5
        + aspect_strength_angle(
            payload, "Sirene", "Ascendant",
            ["Conjunction"], orb_config
        ) * 2.0
        + _modality_match(payload, "Sirene", "fixed") * 1.0
    )
    sirene_devotion = (
        aspect_strength(
            payload, "Sirene", "Neptune",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + _either_house(payload, "Sirene", 7, 12) * 1.5
        + sign_element_match(payload, "Sirene", "water") * 1.0
    )

    # Aphrodite facets
    aphrodite_sovereignty = (
        aspect_strength(
            payload, "Aphrodite", "Venus",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + house_match(payload, "Aphrodite", 1) * 1.5
        + _modality_match(payload, "Aphrodite", "cardinal") * 1.0
    )
    aphrodite_embodiment = (
        aspect_strength(
            payload, "Aphrodite", "Moon",
            ["Conjunction", "Sextile", "Trine"], orb_config
        ) * 2.0
        + house_match(payload, "Aphrodite", 5) * 1.5
        + max(
            sign_element_match(payload, "Aphrodite", "earth"),
            sign_element_match(payload, "Aphrodite", "water"),
        ) * 1.0
    )

    facet_maps = {
        "Apollo": {
            "Heroic": apollo_heroic,
            "Legacy": apollo_legacy,
            "Prophetic": apollo_prophetic,
            "Artistic": apollo_artistic,
        },
        "Themis": {
            "Momentum": themis_momentum,
            "Pattern": themis_pattern,
        },
        "Terpsichore": {
            "Improvisation": terps_improvisation,
            "Grace": terps_grace,
        },
        "Sirene": {
            "Magnetic Test": sirene_magnetic,
            "Devotion": sirene_devotion,
        },
        "Aphrodite": {
            "Sovereignty": aphrodite_sovereignty,
            "Embodiment": aphrodite_embodiment,
        },
    }

    body_weights = {
        body: max(facets.values()) if facets else 0.0
        for body, facets in facet_maps.items()
    }
    dominant_body, _ = _argmax(body_weights)
    dominant_facet, _ = _argmax(facet_maps[dominant_body])

    genre, narrative_question = NGE_GENRES[dominant_body][dominant_facet]
    raw_score = sum(body_weights.values())

    return _result(
        raw_score=raw_score,
        theoretical_max=27.0,
        archetype=genre,
        driver_body=dominant_body,
        payload=payload,
        components={
            "apollo": body_weights["Apollo"],
            "themis": body_weights["Themis"],
            "terpsichore": body_weights["Terpsichore"],
            "sirene": body_weights["Sirene"],
            "aphrodite": body_weights["Aphrodite"],
        },
        expression_basis=genre,
        extra={
            "genre": genre,
            "dominant_body": dominant_body,
            "dominant_facet": dominant_facet,
            "narrative_question": narrative_question,
            "facets": {
                body: {
                    facet: round(value, 4)
                    for facet, value in facets.items()
                }
                for body, facets in facet_maps.items()
            },
        },
        method_name="Narrative Genre Engine",
    )


# ── Aggregate / Ordering Helpers ───────────────────────────────

def compute_all_indexes(
    payload: dict,
    orb_config: dict | None = None,
) -> dict:
    """
    Computes all formula results.

    NGE is included as the current v0.2 system.
    MAGNETIC remains temporarily for the existing portrait renderer.
    """
    if orb_config is None:
        orb_config = ORB_CONFIG

    return {
        "KVQ": compute_kvq(payload, orb_config),
        "MKI": compute_mki(payload, orb_config),
        "RWI": compute_rwi(payload, orb_config),
        "DFIS": compute_dfis(payload, orb_config),
        "CATALYST": compute_catalyst(payload, orb_config),
        "NGE": compute_nge(payload, orb_config),
        "AHL": compute_ahl(payload, orb_config),
    }


def get_eas_dimension_order(index_results: dict) -> list:
    """
    v0.2 EAS ordering for the future NGE-based portrait renderer.

    AHL is not one of the six primary EAS indexes; it is appended only
    when it qualifies for a full ancillary section.
    """
    primary_dimensions = {
        "KVQ": index_results.get("KVQ", {}).get("score", 0.0),
        "MKI": index_results.get("MKI", {}).get("score", 0.0),
        "RWI": index_results.get("RWI", {}).get("score", 0.0),
        "DFIS": index_results.get("DFIS", {}).get("score", 0.0),
        "NGE": index_results.get("NGE", {}).get("score", 0.0),
        "CATALYST": index_results.get("CATALYST", {}).get("score", 0.0),
    }

    ordered = sorted(
        primary_dimensions.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    result = [key for key, _ in ordered]

    if index_results.get("AHL", {}).get("fires"):
        result.append("AHL")

    return result
