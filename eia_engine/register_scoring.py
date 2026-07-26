"""Rules-first v0.1 scoring for EIA registers."""

from __future__ import annotations

from typing import Any

from eia_engine.schema import BASELINE_WEIGHTS, clamp

MODE_RULES = {
    "ignition": {
        "Direct Spark": {"bodies": ["Sun", "Mars", "Ascendant"], "elements": ["fire"], "modalities": ["cardinal"], "houses": [1]},
        "Responsive Pull": {"bodies": ["Moon", "Venus"], "elements": ["water"], "modalities": ["mutable"], "houses": [4, 7]},
        "Structured Commitment": {"bodies": ["Saturn", "Mars"], "elements": ["earth"], "houses": [6, 10]},
        "Relational Opening": {"bodies": ["Venus", "Moon"], "elements": ["air"], "houses": [7, 11]},
        "Threshold Break": {"bodies": ["Uranus", "Pluto", "Mars"], "elements": ["fire"], "houses": [8, 10], "aspects": [("Mars", "Uranus")]},
        "Quiet Accumulation": {"bodies": ["Saturn", "Moon"], "elements": ["earth", "water"], "modalities": ["fixed"], "houses": [2, 4, 12]},
    },
    "reception": {
        "Open Field": {"bodies": ["Moon", "Neptune"], "elements": ["water"], "modalities": ["mutable"], "houses": [12]},
        "Selective Gate": {"bodies": ["Saturn", "Mercury"], "elements": ["earth"], "houses": [6, 10]},
        "Mirror System": {"bodies": ["Moon", "Venus"], "elements": ["air", "water"], "houses": [7]},
        "Deep Sponge": {"bodies": ["Moon", "Neptune", "Pluto"], "elements": ["water"], "houses": [8, 12]},
        "Pattern Receiver": {"bodies": ["Mercury", "Uranus", "Saturn"], "elements": ["air"], "houses": [3, 11]},
        "Low-Noise Receiver": {"bodies": ["Saturn", "Mercury"], "elements": ["earth"], "houses": [6, 12]},
    },
    "decision": {
        "Immediate Knowing": {"bodies": ["Sun", "Mars", "Mercury"], "elements": ["fire"], "modalities": ["cardinal"], "houses": [1, 3]},
        "Tidal Knowing": {"bodies": ["Moon", "Neptune"], "elements": ["water"], "modalities": ["mutable"], "houses": [4, 12]},
        "Embodied Check": {"bodies": ["Venus", "Mars", "Sun"], "elements": ["earth"], "houses": [2, 6]},
        "Dialogic Knowing": {"bodies": ["Mercury", "Venus"], "elements": ["air"], "houses": [3, 7]},
        "Pattern Recognition": {"bodies": ["Mercury", "Saturn", "Uranus"], "elements": ["air", "earth"], "houses": [3, 11]},
        "Stillness First": {"bodies": ["Saturn", "Neptune", "Moon"], "elements": ["water", "earth"], "houses": [12]},
    },
    "current": {
        "Steady Flame": {"bodies": ["Sun", "Saturn"], "elements": ["fire", "earth"], "modalities": ["fixed"], "houses": [2, 6]},
        "Pulse Current": {"bodies": ["Mars", "Uranus", "Sun"], "elements": ["fire"], "modalities": ["cardinal"], "houses": [1, 5]},
        "Deep Reservoir": {"bodies": ["Pluto", "Moon"], "elements": ["water"], "houses": [8, 12]},
        "Borrowed Charge": {"bodies": ["Moon", "Venus", "Jupiter"], "elements": ["air"], "houses": [7, 11]},
        "Seasonal Field": {"bodies": ["Moon", "Jupiter"], "elements": ["water"], "modalities": ["mutable"], "houses": [4, 9, 12]},
        "Precision Battery": {"bodies": ["Mercury", "Saturn"], "elements": ["earth"], "houses": [3, 6, 10]},
    },
    "boundary": {
        "Membrane": {"bodies": ["Moon", "Neptune"], "elements": ["water"], "houses": [4, 12]},
        "Gate": {"bodies": ["Saturn", "Venus"], "elements": ["earth", "air"], "houses": [7]},
        "Mirror": {"bodies": ["Moon", "Venus"], "elements": ["air"], "houses": [7]},
        "Wall": {"bodies": ["Saturn", "Mars"], "elements": ["earth"], "houses": [1, 10]},
        "Anchor": {"bodies": ["Saturn", "Moon"], "elements": ["earth"], "houses": [2, 4, 10]},
        "Blade": {"bodies": ["Mars", "Pluto"], "elements": ["fire"], "houses": [1, 8]},
        "Vessel": {"bodies": ["Moon", "Pluto", "Saturn"], "elements": ["water", "earth"], "houses": [8, 12]},
    },
    "contact": {
        "Catalyst": {"bodies": ["Mars", "Uranus", "Pluto"], "elements": ["fire"], "houses": [8, 10]},
        "Stabilizer": {"bodies": ["Saturn", "Venus"], "elements": ["earth"], "houses": [2, 10]},
        "Translator": {"bodies": ["Mercury", "Moon"], "elements": ["air"], "houses": [3, 7, 11]},
        "Amplifier": {"bodies": ["Jupiter", "Moon", "Neptune"], "elements": ["water", "fire"], "houses": [5, 11]},
        "Witness": {"bodies": ["Saturn", "Mercury"], "elements": ["air", "earth"], "houses": [9, 12]},
        "Sanctuary": {"bodies": ["Moon", "Venus", "Neptune"], "elements": ["water"], "houses": [4, 12]},
        "Challenger": {"bodies": ["Mars", "Saturn", "Uranus"], "elements": ["fire", "earth"], "houses": [1, 10]},
    },
    "restoration": {
        "Solitude and Sleep": {"bodies": ["Moon", "Neptune"], "elements": ["water"], "houses": [4, 12]},
        "Movement and Heat": {"bodies": ["Mars", "Sun"], "elements": ["fire"], "houses": [1, 5]},
        "Beauty and Pleasure": {"bodies": ["Venus", "Moon"], "elements": ["earth", "water"], "houses": [2, 5]},
        "Naming and Writing": {"bodies": ["Mercury"], "elements": ["air"], "houses": [3, 6]},
        "Ritual and Repetition": {"bodies": ["Saturn"], "elements": ["earth"], "houses": [6, 10]},
        "Trusted Witnessing": {"bodies": ["Moon", "Venus", "Mercury"], "elements": ["air", "water"], "houses": [7]},
        "Material Simplification": {"bodies": ["Saturn", "Mercury"], "elements": ["earth"], "houses": [2, 6]},
        "Clean Agreement": {"bodies": ["Saturn", "Venus", "Mercury"], "elements": ["air", "earth"], "houses": [7, 10]},
    },
}

POLARITY_BY_MODE = {
    "positive": {"Direct Spark", "Threshold Break", "Immediate Knowing", "Pulse Current", "Blade", "Catalyst", "Movement and Heat", "Challenger"},
    "negative": {"Responsive Pull", "Open Field", "Deep Sponge", "Tidal Knowing", "Deep Reservoir", "Borrowed Charge", "Membrane", "Sanctuary", "Solitude and Sleep"},
}

EAS_KEYWORDS_BY_MODE = {
    "Gate": ["boundary", "agreement", "consent"],
    "Blade": ["sovereign", "precision"],
    "Catalyst": ["catalyst", "activation"],
    "Challenger": ["challenge", "friction"],
    "Translator": ["narrative", "translation", "language"],
    "Witness": ["witness", "validation"],
    "Pattern Receiver": ["kassandra", "pattern", "validation"],
}


def score_register_modes(
    register: str,
    modes: list[str],
    features: dict[str, Any],
    eas_indexes: dict[str, Any] | None = None,
    state_overlay: dict[str, Any] | None = None,
    client_checkin: dict[str, Any] | None = None,
) -> dict[str, float]:
    confidence = features.get("confidence_modifier", 1.0)
    scores = {}
    for mode in modes:
        score = 0.0
        score += BASELINE_WEIGHTS["natal_signature"] * score_natal_signature(register, mode, features)
        score += BASELINE_WEIGHTS["eas_resonance"] * score_eas_resonance(register, mode, eas_indexes)
        score += BASELINE_WEIGHTS["polarity_current"] * score_polarity(register, mode, features)
        score += BASELINE_WEIGHTS["biophysical_metaphor"] * score_system_language(register, mode, features)
        score += BASELINE_WEIGHTS["state_overlay"] * score_state_overlay(register, mode, state_overlay)
        score += BASELINE_WEIGHTS["client_calibration"] * score_client_checkin(register, mode, client_checkin)
        scores[mode] = round(clamp(score * confidence), 4)
    return scores


def score_natal_signature(register: str, mode: str, features: dict[str, Any]) -> float:
    rules = MODE_RULES[register][mode]
    score = 0.10
    score += 0.30 * _body_score(rules.get("bodies", []), features)
    score += 0.24 * _balance_score(rules.get("elements", []), features.get("element_balance", {}))
    score += 0.14 * _balance_score(rules.get("modalities", []), features.get("modality_balance", {}))
    score += 0.16 * _house_score(rules.get("houses", []), features)
    score += 0.06 * _aspect_score(rules.get("aspects", []), features)
    return clamp(score)


def score_eas_resonance(register: str, mode: str, eas_indexes: dict[str, Any] | None) -> float:
    if not eas_indexes:
        return 0.25
    haystack = " ".join(str(value).lower() for value in _flatten(eas_indexes))
    keywords = EAS_KEYWORDS_BY_MODE.get(mode, [mode.lower()])
    matches = sum(1 for keyword in keywords if keyword.lower() in haystack)
    return clamp(0.20 + matches * 0.30)


def score_polarity(register: str, mode: str, features: dict[str, Any]) -> float:
    polarity = _dominant_polarity(features)
    if mode in POLARITY_BY_MODE.get(polarity, set()):
        return 0.75
    if polarity == "neutral" and mode not in POLARITY_BY_MODE["positive"] | POLARITY_BY_MODE["negative"]:
        return 0.72
    return 0.30


def score_system_language(register: str, mode: str, features: dict[str, Any]) -> float:
    if register in {"reception", "decision", "restoration"}:
        return 0.62
    if "threshold" in mode.lower() or "pulse" in mode.lower() or "field" in mode.lower():
        return 0.70
    return 0.48


def score_state_overlay(register: str, mode: str, state_overlay: dict[str, Any] | None) -> float:
    if not state_overlay:
        return 0.0
    score = 0.45 if state_overlay.get("active_register") == register else 0.0
    if mode in state_overlay.get("mode_hints", []):
        score += 0.45
    return clamp(score)


def score_client_checkin(register: str, mode: str, client_checkin: dict[str, Any] | None) -> float:
    if not client_checkin:
        return 0.0
    text = " ".join(str(value).lower() for value in _flatten(client_checkin))
    if "overloaded" in text and mode in {"Open Field", "Low-Noise Receiver", "Solitude and Sleep"}:
        return 0.80
    if "volatile" in text and mode in {"Pulse Current", "Threshold Break"}:
        return 0.75
    if "clear" in text and mode in {"Immediate Knowing", "Embodied Check"}:
        return 0.65
    return 0.20


def _body_score(bodies: list[str], features: dict[str, Any]) -> float:
    if not bodies:
        return 0.0
    available = set(features.get("body_signs", {}))
    matches = sum(1 for body in bodies if body in available)
    body_houses = features.get("body_houses", {})
    angle_bonus = 0.15 if any(body_houses.get(body) in {1, 4, 7, 10} for body in bodies) else 0.0
    return clamp(matches / len(bodies) + angle_bonus)


def _balance_score(keys: list[str], balance: dict[str, float]) -> float:
    if not keys:
        return 0.0
    return clamp(sum(balance.get(key, 0.0) for key in keys) * 2.2)


def _house_score(houses: list[int], features: dict[str, Any]) -> float:
    if not houses:
        return 0.0
    emphasized = features.get("emphasized_houses", set())
    return clamp(sum(1 for house in houses if house in emphasized) / len(houses))


def _aspect_score(aspect_pairs: list[tuple[str, str]], features: dict[str, Any]) -> float:
    if not aspect_pairs:
        return 0.0
    aspects = features.get("aspects", set())
    matches = 0
    for first, second in aspect_pairs:
        ordered = tuple(sorted([first, second]))
        if any(item[0] == ordered[0] and item[1] == ordered[1] for item in aspects):
            matches += 1
    return clamp(matches / len(aspect_pairs))


def _dominant_polarity(features: dict[str, Any]) -> str:
    elements = features.get("element_balance", {})
    positive = elements.get("fire", 0.0) + elements.get("air", 0.0)
    negative = elements.get("water", 0.0)
    neutral = elements.get("earth", 0.0)
    if positive >= negative and positive >= neutral:
        return "positive"
    if negative >= neutral:
        return "negative"
    return "neutral"


def _flatten(value: Any) -> list[Any]:
    if isinstance(value, dict):
        items = []
        for nested in value.values():
            items.extend(_flatten(nested))
        return items
    if isinstance(value, (list, tuple, set)):
        items = []
        for nested in value:
            items.extend(_flatten(nested))
        return items
    return [value]
