"""
formulas/standard_indexes.py — Standard Astrological Computations
Derives computed values from the v2 payload that are needed
across all report types. No proprietary content here.
"""
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SIGN_ELEMENTS, SIGN_MODALITIES, HOUSE_DOMAINS, HOUSE_THEMES,
    DAY_RULERS, PLANET_WEIGHTS, MAJOR_ASPECTS, ASPECT_CHARACTERS,
    INTENSITY_LEVELS, DURATION_MODIFIERS, ORB_CONFIG
)
from selectors.utils import (
    get_body_sign, get_body_house, get_sign_element,
    get_aspect_from_payload, aspect_strength
)


def get_elemental_balance(payload: dict) -> dict:
    """Count planets per element across all bodies in the payload."""
    counts = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    for element, signs in SIGN_ELEMENTS.items():
        for group in [payload.get("standard_planets", {}),
                      payload.get("custom_asteroids", {})]:
            for _, data in group.items():
                if isinstance(data, str):
                    continue
                if data.get("sign") in signs:
                    counts[element] += 1
    return counts


def get_dominant_element(payload: dict) -> str:
    """Returns element with highest planet count. Sun sign breaks ties."""
    balance = get_elemental_balance(payload)
    max_count = max(balance.values())
    dominant = [e for e, c in balance.items() if c == max_count]
    if len(dominant) == 1:
        return dominant[0]
    sun_sign = payload.get("standard_planets", {}).get("Sun", {}).get("sign", "")
    for element, signs in SIGN_ELEMENTS.items():
        if sun_sign in signs and element in dominant:
            return element
    return dominant[0]


def get_modal_balance(payload: dict) -> dict:
    """Count planets per modality."""
    counts = {"cardinal": 0, "fixed": 0, "mutable": 0}
    for modality, signs in SIGN_MODALITIES.items():
        for group in [payload.get("standard_planets", {}),
                      payload.get("custom_asteroids", {})]:
            for _, data in group.items():
                if isinstance(data, str):
                    continue
                if data.get("sign") in signs:
                    counts[modality] += 1
    return counts


def get_sun_moon_relationship(payload: dict) -> str:
    """Returns 'flowing', 'challenging', or 'unaspected'."""
    asp = get_aspect_from_payload(payload, "Sun", "Moon")
    if not asp:
        return "unaspected"
    return ASPECT_CHARACTERS.get(asp["aspect"], "unaspected")


def get_day_ruler(date: datetime = None) -> str:
    """Chaldean planetary ruler for the given day."""
    if date is None:
        date = datetime.now(timezone.utc)
    return DAY_RULERS[date.weekday()]


def get_house_domain(house_number: int) -> str:
    return HOUSE_DOMAINS.get(house_number, "")


def get_house_theme(house_number: int) -> str:
    return HOUSE_THEMES.get(house_number, "")


def get_dominant_aspect_pattern(payload: dict, top_n: int = 2) -> list:
    """
    Returns the top N most significant natal aspects ranked by
    max(planet_weight) × aspect_strength.
    Used by Soul Journey's dominant aspect section.
    """
    scored = []
    for asp in payload.get("aspects", []):
        a, b = asp["body_1"], asp["body_2"]
        weight = max(PLANET_WEIGHTS.get(a, 0.5), PLANET_WEIGHTS.get(b, 0.5))
        strength = aspect_strength(payload, a, b,
                                   [x[0] for x in MAJOR_ASPECTS], ORB_CONFIG)
        scored.append({
            "body_a": a, "body_b": b,
            "aspect": asp["aspect"],
            "aspect_character": ASPECT_CHARACTERS.get(asp["aspect"], "flowing"),
            "orb": asp["orb"],
            "significance": weight * strength
        })
    scored.sort(key=lambda x: x["significance"], reverse=True)
    major = [a for a in scored if a["aspect"] != "Sextile"]
    return (major if major else scored)[:top_n]


def get_intensity_label(score: float) -> str:
    for threshold, label, _ in INTENSITY_LEVELS:
        if score >= threshold:
            return label
    return "Passing"


def get_intensity_bar(score: float) -> str:
    for threshold, _, bar in INTENSITY_LEVELS:
        if score >= threshold:
            return bar
    return "█"


def apply_duration_modifier(base_score: float, duration_days: int) -> float:
    for threshold, modifier in DURATION_MODIFIERS:
        if duration_days > threshold:
            return min(1.0, base_score * modifier)
    return min(1.0, base_score * 0.75)


def get_month_activated_domains(transits_this_month: list, top_n: int = 3) -> list:
    """
    Maps transits to human life domains and returns the top N
    most activated domains with intensity bars.
    Used by Monthly Chapter 'Most Activated Areas'.
    """
    domain_scores = {}
    for t in transits_this_month:
        house = t.get("natal_house")
        if not house:
            continue
        domain = HOUSE_DOMAINS.get(house, "")
        if not domain:
            continue
        score = t.get("combined_intensity_score", 0)
        domain_scores[domain] = domain_scores.get(domain, 0) + score

    domain_scores = {d: s for d, s in domain_scores.items() if s >= 0.20}
    if not domain_scores:
        return []

    max_score = max(domain_scores.values())
    sorted_domains = sorted(domain_scores.items(),
                            key=lambda x: x[1], reverse=True)[:top_n]
    return [{"domain": d, "score": s,
             "bar": "█" * round((s / max_score) * 12)}
            for d, s in sorted_domains]


def get_annual_arc(all_transits: list) -> dict:
    """
    Monthly intensity across 12 months for the Annual Arc visual.
    Returns {1: {intensity, bar, label}, ..., 12: {...}}.
    """
    monthly_peaks = {}
    for t in all_transits:
        m = t.get("peak_month")
        if m is None:
            continue
        score = t.get("combined_intensity_score", 0)
        if score > monthly_peaks.get(m, 0):
            monthly_peaks[m] = score

    max_score = max(monthly_peaks.values()) if monthly_peaks else 1.0
    arc = {}
    for m in range(1, 13):
        score = monthly_peaks.get(m, 0)
        bar_len = round((score / max_score) * 12) if max_score > 0 else 0
        arc[m] = {
            "intensity": score,
            "bar": "█" * bar_len,
            "label": get_intensity_label(score)
        }
    return arc
