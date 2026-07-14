"""
First-pass scoring and bucket assignment for Place Resonance Search.

This is deliberately transparent and deterministic. It creates a stable contract
for Search output before the final astrology weighting model is refined.
"""
from __future__ import annotations

import copy
import math
from collections import Counter
from typing import Any


SCORING_VERSION = "place_resonance_search_scoring_v0.3.0"

THEME_KEYS = (
    "visibility_calling",
    "belonging_bonds",
    "hearth_restoration",
    "study_signal",
    "creative_culture",
    "long_term_build",
    "change_aliveness",
    "shadow_pressure",
)

SCORE_KEYS = (
    "overall_resonance",
    *THEME_KEYS,
    "complexity_index",
    "consensus_score",
    "grounding_score",
    "baseline_divergence",
)

BUCKET_KEYS = {
    "highest_resonance",
    "goal_specific_allies",
    "transformational_demanding",
    "quiet_grounding_alternatives",
    "pattern_outliers",
}

BUCKET_LABELS = {
    "highest_resonance": "Highest Resonance",
    "goal_specific_allies": "Goal-Specific Allies",
    "transformational_demanding": "Transformational / Demanding Places",
    "quiet_grounding_alternatives": "Quiet or Grounding Alternatives",
    "pattern_outliers": "Pattern Outliers",
}

RECOMMENDATION_LABELS = {
    "strongly_consider": "Strongly Consider",
    "goal_specific_ally": "Goal-Specific Ally",
    "powerful_but_demanding": "Powerful but Demanding",
    "gentle_alternative": "Gentle Alternative",
    "useful_contrast": "Useful Contrast",
    "stable_baseline": "Stable Baseline",
    "low_signal_not_priority": "Low Signal / Not Priority",
}

THEME_PROSE_FAMILIES = {
    "visibility_calling": "visibility",
    "belonging_bonds": "belonging",
    "hearth_restoration": "restoration",
    "study_signal": "study",
    "creative_culture": "creative",
    "long_term_build": "structure",
    "change_aliveness": "reinvention",
    "shadow_pressure": "complexity",
}

BODY_THEME_WEIGHTS = {
    "Sun": {"visibility_calling": 9, "creative_culture": 4, "change_aliveness": 3},
    "Moon": {"hearth_restoration": 9, "belonging_bonds": 4, "grounding": 3},
    "Mercury": {"study_signal": 9, "change_aliveness": 3, "visibility_calling": 2},
    "Venus": {"belonging_bonds": 8, "creative_culture": 8, "hearth_restoration": 3},
    "Mars": {"change_aliveness": 8, "visibility_calling": 3, "shadow_pressure": 5},
    "Jupiter": {"study_signal": 7, "visibility_calling": 5, "belonging_bonds": 4, "change_aliveness": 4},
    "Saturn": {"long_term_build": 9, "shadow_pressure": 6, "grounding": 4},
    "Uranus": {"change_aliveness": 9, "study_signal": 3, "shadow_pressure": 3},
    "Neptune": {"creative_culture": 7, "hearth_restoration": 4, "shadow_pressure": 3},
    "Pluto": {"shadow_pressure": 9, "change_aliveness": 5, "long_term_build": 3},
}

MAJOR_BODIES = frozenset(BODY_THEME_WEIGHTS)
SUPPORTING_POINTS = frozenset({"North_Node", "South_Node", "Lilith_BML"})

# Search normally receives only Location Services standard-body evidence. The
# custom weight is defensive: if a malformed caller passes EO asteroid evidence
# into this layer, it cannot masquerade as standard locational consensus.
BODY_CLASS_WEIGHT = {
    "major": 1.0,
    "supporting_point": 0.45,
    "custom": 0.18,
}

ANGLE_THEME_WEIGHTS = {
    "Ascendant": {"change_aliveness": 7, "visibility_calling": 4},
    "Midheaven": {"visibility_calling": 9, "long_term_build": 4},
    "Descendant": {"belonging_bonds": 9},
    "Imum_Coeli": {"hearth_restoration": 9, "grounding": 4},
}

HOUSE_THEME_WEIGHTS = {
    1: {"change_aliveness": 6, "visibility_calling": 3},
    2: {"long_term_build": 5, "grounding": 4},
    3: {"study_signal": 6, "belonging_bonds": 2},
    4: {"hearth_restoration": 7, "grounding": 4},
    5: {"creative_culture": 7, "belonging_bonds": 2},
    6: {"long_term_build": 6, "grounding": 3},
    7: {"belonging_bonds": 7},
    8: {"shadow_pressure": 7, "change_aliveness": 2},
    9: {"study_signal": 7, "change_aliveness": 3},
    10: {"visibility_calling": 7, "long_term_build": 4},
    11: {"belonging_bonds": 5, "study_signal": 3, "change_aliveness": 2},
    12: {"hearth_restoration": 4, "shadow_pressure": 6},
}

STRENGTH_MULTIPLIER = {
    "tight": 1.25,
    "moderate": 1.0,
    "wide": 0.7,
}

NORMALIZATION_PROFILE = {
    "method": "candidate_pool_percentile_minmax",
    "lower_percentile": 10,
    "upper_percentile": 100,
    "zero_floor": 0,
    "flat_nonzero_score": 50,
    "custom_body_weight": BODY_CLASS_WEIGHT["custom"],
    "supporting_point_weight": BODY_CLASS_WEIGHT["supporting_point"],
}

PROXIMITY_CLUSTER_MILES = 500.0
MAX_SIMILAR_TILES_PER_PROXIMITY_CLUSTER = 2


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _add_weights(target: Counter, weights: dict[str, float], multiplier: float = 1.0) -> None:
    for key, value in weights.items():
        target[key] += value * multiplier


def _candidate_coordinates(item: dict[str, Any]) -> tuple[float, float] | None:
    candidate = item.get("candidate") or {}
    try:
        latitude = float(candidate["latitude"])
        longitude = float(candidate["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    return latitude, longitude


def _distance_miles(item_a: dict[str, Any], item_b: dict[str, Any]) -> float | None:
    coords_a = _candidate_coordinates(item_a)
    coords_b = _candidate_coordinates(item_b)
    if coords_a is None or coords_b is None:
        return None

    lat1, lon1 = (math.radians(value) for value in coords_a)
    lat2, lon2 = (math.radians(value) for value in coords_b)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    hav = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 3958.7613 * 2 * math.asin(min(1.0, math.sqrt(hav)))


def _lead_evidence_signature(item: dict[str, Any]) -> str:
    for evidence_id in item.get("evidence_refs", []) or []:
        if not isinstance(evidence_id, str):
            continue
        parts = evidence_id.split(":")
        if len(parts) >= 3 and parts[0] == "angle_contact":
            return f"angle_contact:{parts[1]}:{parts[2]}"
        if len(parts) >= 2 and parts[0] in {"house_change", "natal_modifier"}:
            return f"{parts[0]}:{parts[1]}"
        if len(parts) >= 2 and parts[0] == "orientation_shift":
            return f"orientation_shift:{parts[1]}"
    return "no_lead_evidence"


def _place_texture_signature(item: dict[str, Any]) -> str:
    candidate = item.get("candidate") or {}
    notes = tuple(str(note).strip().lower() for note in (candidate.get("notes") or [])[:2])
    return "|".join([
        str(candidate.get("population_tier") or ""),
        str(candidate.get("region") or ""),
        ",".join(notes),
    ])


def _similarity_signature(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        item.get("bucket"),
        tuple((item.get("dominant_themes") or [])[:2]),
        _lead_evidence_signature(item),
    )


def _is_similar_nearby(item: dict[str, Any], selected: dict[str, Any]) -> bool:
    distance = _distance_miles(item, selected)
    if distance is None or distance > PROXIMITY_CLUSTER_MILES:
        return False
    return _similarity_signature(item) == _similarity_signature(selected)


def _alternate_summary(item: dict[str, Any], representative: dict[str, Any], distance: float | None) -> dict[str, Any]:
    return {
        "location_id": item.get("location_id"),
        "display_name": item.get("display_name"),
        "bucket": item.get("bucket"),
        "recommendation_label": item.get("recommendation_label"),
        "dominant_themes": list(item.get("dominant_themes") or []),
        "scores": copy.deepcopy(item.get("scores") or {}),
        "candidate": copy.deepcopy(item.get("candidate") or {}),
        "distance_from_representative_miles": round(distance, 1) if distance is not None else None,
        "sibling_difference": _sibling_difference(item, representative, distance),
    }


def _sibling_difference(item: dict[str, Any], representative: dict[str, Any], distance: float | None) -> str:
    candidate = item.get("candidate") or {}
    rep_candidate = representative.get("candidate") or {}
    distance_text = f"about {round(distance)} miles from {representative.get('display_name')}" if distance is not None else "near the selected representative"
    population = str(candidate.get("population_tier") or "").replace("_", " ")
    rep_population = str(rep_candidate.get("population_tier") or "").replace("_", " ")
    notes = ", ".join(str(note) for note in (candidate.get("notes") or [])[:2])
    if population and rep_population and population != rep_population:
        return (
            f"{item.get('display_name')} carries a similar evidence signature {distance_text}, "
            f"but expresses it through a {population} setting rather than {rep_population}."
        )
    if notes:
        return (
            f"{item.get('display_name')} carries a similar evidence signature {distance_text}, "
            f"with catalog texture marked by {notes}."
        )
    return f"{item.get('display_name')} carries a similar evidence signature {distance_text}."


def _initialize_tile_metadata(item: dict[str, Any]) -> None:
    item.setdefault("regional_role", "standalone")
    item.setdefault("proximity_cluster_radius_miles", PROXIMITY_CLUSTER_MILES)
    item.setdefault("similarity_signature", {
        "bucket": item.get("bucket"),
        "dominant_themes": list((item.get("dominant_themes") or [])[:2]),
        "lead_evidence": _lead_evidence_signature(item),
        "place_texture": _place_texture_signature(item),
    })
    item.setdefault("cluster_alternates", [])
    item.setdefault("sibling_difference", "")


def _evidence_refs(record: dict[str, Any]) -> list[str]:
    ranking = record.get("evidence_ranking") or {}
    refs: list[str] = []
    for tier in ("primary_evidence", "supporting_evidence"):
        for evidence_id in ranking.get(tier, []) or []:
            if isinstance(evidence_id, str):
                refs.append(evidence_id)
    return refs[:8]


def _all_evidence_refs(record: dict[str, Any]) -> list[str]:
    ranking = record.get("evidence_ranking") or {}
    refs: list[str] = []
    for tier in ("primary_evidence", "supporting_evidence", "contradictory_evidence"):
        for evidence_id in ranking.get(tier, []) or []:
            if isinstance(evidence_id, str):
                refs.append(evidence_id)
    return refs


def _evidence_class(evidence_id: str) -> str:
    return evidence_id.split(":", 1)[0] if ":" in evidence_id else evidence_id


def _body_class(body: Any) -> str:
    if body in MAJOR_BODIES:
        return "major"
    if body in SUPPORTING_POINTS:
        return "supporting_point"
    return "custom"


def _body_weight(body: Any) -> float:
    return BODY_CLASS_WEIGHT[_body_class(body)]


def _weighted_count(items: list[dict[str, Any]]) -> float:
    return sum(_body_weight(item.get("body")) for item in items if isinstance(item, dict))


def _weighted_distinct_bodies(items: list[dict[str, Any]]) -> float:
    by_body: dict[str, float] = {}
    for item in items:
        body = item.get("body") if isinstance(item, dict) else None
        if isinstance(body, str):
            by_body[body] = max(by_body.get(body, 0.0), _body_weight(body))
    return sum(by_body.values())


def _theme_points(record: dict[str, Any]) -> Counter:
    points: Counter = Counter()

    for contact in record.get("relocated_angle_contacts", []) or []:
        if not isinstance(contact, dict):
            continue
        body = contact.get("body")
        angle = contact.get("angle")
        multiplier = STRENGTH_MULTIPLIER.get(contact.get("contact_strength"), 0.8) * _body_weight(body)
        _add_weights(points, BODY_THEME_WEIGHTS.get(body, {}), multiplier)
        _add_weights(points, ANGLE_THEME_WEIGHTS.get(angle, {}), multiplier)

    for change in record.get("planet_house_changes", []) or []:
        if not isinstance(change, dict) or not change.get("house_changed"):
            continue
        body = change.get("body")
        house = change.get("relocated_house")
        base_multiplier = 1.15 if change.get("movement_type") == "newly_angular" else 0.75
        multiplier = base_multiplier * _body_weight(body)
        _add_weights(points, BODY_THEME_WEIGHTS.get(body, {}), multiplier)
        if isinstance(house, int):
            _add_weights(points, HOUSE_THEME_WEIGHTS.get(house, {}), multiplier)

    return points


def dominant_themes(scores: dict[str, int], limit: int = 3) -> list[str]:
    ranked = sorted(THEME_KEYS, key=lambda key: scores.get(key, 0), reverse=True)
    return [key for key in ranked[:limit] if scores.get(key, 0) > 0]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * (percentile / 100)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _normalize_values(values: list[float]) -> list[int]:
    if not values:
        return []
    if max(values) <= 0:
        return [0 for _ in values]

    lower = _percentile(values, NORMALIZATION_PROFILE["lower_percentile"])
    upper = _percentile(values, NORMALIZATION_PROFILE["upper_percentile"])
    if math.isclose(lower, upper):
        return [
            NORMALIZATION_PROFILE["flat_nonzero_score"] if value > 0 else 0
            for value in values
        ]

    normalized: list[int] = []
    for value in values:
        scaled = ((float(value) - lower) / (upper - lower)) * 100
        normalized.append(_clamp_score(scaled))
    return normalized


def raw_score_location_record(record: dict[str, Any]) -> dict[str, float]:
    points = _theme_points(record)
    theme_scores = {key: float(points.get(key, 0)) for key in THEME_KEYS}

    angle_contacts = [item for item in record.get("relocated_angle_contacts", []) or [] if isinstance(item, dict)]
    changed_houses = [
        item for item in record.get("planet_house_changes", []) or []
        if isinstance(item, dict) and item.get("house_changed")
    ]
    all_refs = _all_evidence_refs(record)
    repeated_bodies = [
        {"body": body}
        for body in (
            {item.get("body") for item in angle_contacts}
            & {item.get("body") for item in changed_houses}
        )
        if isinstance(body, str)
    ]
    evidence_classes = {_evidence_class(evidence_id) for evidence_id in all_refs}
    primary_refs = (record.get("evidence_ranking") or {}).get("primary_evidence", []) or []
    supporting_refs = (record.get("evidence_ranking") or {}).get("supporting_evidence", []) or []
    tight_contacts = [
        item for item in angle_contacts
        if item.get("contact_strength") == "tight"
    ]
    moderate_contacts = [
        item for item in angle_contacts
        if item.get("contact_strength") == "moderate"
    ]
    newly_angular = [
        item for item in changed_houses
        if item.get("movement_type") == "newly_angular"
    ]
    angular_house_moves = [
        item for item in changed_houses
        if item.get("relocated_house") in {1, 4, 7, 10}
    ]
    pressure_house_moves = [
        item for item in changed_houses
        if item.get("relocated_house") in {8, 12}
    ]
    contact_precision = sum(
        (max(0.0, 8.0 - float(item.get("orb") or 8.0)) / 8.0) * _body_weight(item.get("body"))
        for item in angle_contacts
    )
    weighted_primary_refs = sum(
        _body_weight(evidence_id.split(":", 2)[1])
        if isinstance(evidence_id, str) and evidence_id.startswith(("angle_contact:", "house_change:", "natal_modifier:"))
        else 1.0
        for evidence_id in primary_refs
    )
    weighted_supporting_refs = sum(
        _body_weight(evidence_id.split(":", 2)[1])
        if isinstance(evidence_id, str) and evidence_id.startswith(("angle_contact:", "house_change:", "natal_modifier:"))
        else 1.0
        for evidence_id in supporting_refs
    )

    complexity = (
        theme_scores["shadow_pressure"] * 0.75
        + len([item for item in angle_contacts if item.get("body") in {"Mars", "Saturn", "Pluto"}]) * 8
        + _weighted_count([item for item in changed_houses if item.get("relocated_house") in {8, 12}]) * 6
    )
    consensus = (
        min(weighted_primary_refs, 8) * 3
        + min(weighted_supporting_refs, 12) * 1.25
        + len(evidence_classes) * 10
        + min(_weighted_distinct_bodies([*angle_contacts, *changed_houses]), 10) * 2
        + _weighted_count(repeated_bodies) * 8
        + min(contact_precision, 12) * 1.5
    )
    baseline_divergence = (
        _weighted_count(tight_contacts) * 7
        + _weighted_count(moderate_contacts) * 4
        + _weighted_count(newly_angular) * 9
        + _weighted_count(angular_house_moves) * 4
        + _weighted_count(pressure_house_moves) * 3
        + _weighted_count(repeated_bodies) * 6
    )
    return {
        **theme_scores,
        "complexity_index": float(complexity),
        "consensus_score": float(consensus),
        "grounding_score": float(points.get("grounding", 0) * 4 + theme_scores["hearth_restoration"] * 0.35 + theme_scores["long_term_build"] * 0.2),
        "baseline_divergence": float(baseline_divergence),
    }


def normalize_raw_scores(raw_scores: list[dict[str, float]]) -> list[dict[str, int]]:
    if not raw_scores:
        return []

    normalized_by_key: dict[str, list[int]] = {}
    component_keys = [*THEME_KEYS, "complexity_index", "consensus_score", "grounding_score", "baseline_divergence"]
    for key in component_keys:
        normalized_by_key[key] = _normalize_values([item.get(key, 0.0) for item in raw_scores])

    preliminary: list[dict[str, int]] = []
    overall_raw: list[float] = []
    for index, raw in enumerate(raw_scores):
        scores = {key: normalized_by_key[key][index] for key in component_keys}
        overall = (
            max(scores[key] for key in THEME_KEYS) * 0.38
            + sum(sorted((scores[key] for key in THEME_KEYS), reverse=True)[:3]) * 0.13
            + scores["consensus_score"] * 0.18
            + scores["baseline_divergence"] * 0.11
            + scores["grounding_score"] * 0.07
        )
        preliminary.append(scores)
        overall_raw.append(overall)

    overall_scores = _normalize_values(overall_raw)
    return [
        {
            "overall_resonance": overall_scores[index],
            **scores,
        }
        for index, scores in enumerate(preliminary)
    ]


def score_location_record(record: dict[str, Any]) -> dict[str, int]:
    """
    Score one record without a comparison pool.

    Search uses normalize_raw_scores() across the whole candidate pool. This
    single-record helper remains for narrow tests and callers; a nonzero raw
    signal normalizes to midrange rather than pretending one location can define
    its own top of scale.
    """
    return normalize_raw_scores([raw_score_location_record(record)])[0]


def assign_bucket(scores: dict[str, int], themes: list[str], rank: int = 0) -> str:
    if scores["complexity_index"] >= 70 and scores["overall_resonance"] >= 45:
        return "transformational_demanding"
    if scores["grounding_score"] >= 55 and scores["complexity_index"] <= 55:
        return "quiet_grounding_alternatives"
    if scores["baseline_divergence"] >= 70 and rank > 2:
        return "pattern_outliers"
    if scores["overall_resonance"] >= 65 and scores["consensus_score"] >= 55:
        return "highest_resonance"
    if themes:
        return "goal_specific_allies"
    return "pattern_outliers"


def recommendation_key_for_bucket(bucket: str, scores: dict[str, int]) -> str:
    if bucket == "highest_resonance":
        return "strongly_consider"
    if bucket == "transformational_demanding":
        return "powerful_but_demanding"
    if bucket == "quiet_grounding_alternatives":
        return "gentle_alternative" if scores["overall_resonance"] >= 35 else "stable_baseline"
    if bucket == "pattern_outliers":
        return "useful_contrast"
    if bucket == "goal_specific_allies":
        return "goal_specific_ally"
    return "low_signal_not_priority"


def prose_variation_traits(scores: dict[str, int], themes: list[str]) -> dict[str, str]:
    primary_theme = themes[0] if themes else "fallback"
    secondary_theme = themes[1] if len(themes) > 1 else "fallback"
    primary_family = THEME_PROSE_FAMILIES.get(primary_theme, "mixed")
    secondary_family = THEME_PROSE_FAMILIES.get(secondary_theme, "mixed")

    if scores.get("complexity_index", 0) >= 75:
        cost_style = "high_pressure"
    elif scores.get("baseline_divergence", 0) >= 75:
        cost_style = "disruptive"
    elif scores.get("grounding_score", 0) >= 70:
        cost_style = "low_drama"
    else:
        cost_style = "moderate"

    if scores.get("grounding_score", 0) >= 75:
        support_style = "grounding"
    elif scores.get("baseline_divergence", 0) >= 75:
        support_style = "contrast"
    elif primary_family in {"visibility", "structure", "study"}:
        support_style = "public_or_practical"
    elif primary_family in {"belonging", "restoration", "creative"}:
        support_style = "relational_or_restorative"
    else:
        support_style = "change_or_complexity"

    return {
        "primary_theme": primary_theme,
        "secondary_theme": secondary_theme,
        "primary_family": primary_family,
        "secondary_family": secondary_family,
        "support_style": support_style,
        "cost_style": cost_style,
    }


def recommendation_prose_key(
    recommendation_key: str,
    scores: dict[str, int],
    themes: list[str],
    candidate: dict[str, Any] | None = None,
) -> str:
    traits = prose_variation_traits(scores, themes)
    primary = traits["primary_family"]
    secondary = traits["secondary_family"]
    population_tier = str((candidate or {}).get("population_tier") or "")

    if recommendation_key == "strongly_consider":
        if primary == "belonging" and secondary == "restoration":
            return "strongly_consider_belonging_restoration"
        if primary == "belonging" and secondary in {"creative", "reinvention"}:
            return "strongly_consider_belonging_aliveness"
        if primary == "visibility":
            return "strongly_consider_visibility"
        if primary == "reinvention":
            return "strongly_consider_reinvention"
        return "strongly_consider_coherent"

    if recommendation_key == "gentle_alternative":
        if primary == "restoration" or traits["support_style"] == "grounding":
            return "gentle_alternative_restorative"
        if primary == "visibility":
            return "gentle_alternative_visibility"
        if primary == "belonging":
            return "gentle_alternative_belonging"
        return "gentle_alternative_steady"

    if recommendation_key == "powerful_but_demanding":
        if primary == "complexity":
            return "powerful_but_demanding_pressure"
        if primary == "reinvention":
            return "powerful_but_demanding_reinvention"
        if primary == "restoration":
            return "powerful_but_demanding_private"
        if primary == "visibility":
            return "powerful_but_demanding_visibility"
        if primary == "structure":
            return "powerful_but_demanding_structure"
        if primary == "belonging":
            return "powerful_but_demanding_belonging"
        return "powerful_but_demanding_consequential"

    if recommendation_key == "goal_specific_ally":
        return f"goal_specific_ally_{primary}" if primary != "mixed" else "goal_specific_ally"

    if recommendation_key == "useful_contrast":
        if primary == "visibility" and secondary == "study":
            if population_tier in {"major_metro", "large_metro"}:
                return "useful_contrast_visibility_signal_metro"
            if population_tier == "small_town":
                return "useful_contrast_visibility_signal_small_place"
            return "useful_contrast_visibility_signal"
        if primary == "visibility":
            return "useful_contrast_visibility"
        return "useful_contrast_divergent" if traits["cost_style"] == "disruptive" else "useful_contrast"

    return recommendation_key


def build_scored_location(record: dict[str, Any], candidate: dict[str, Any], *, rank: int = 0) -> dict[str, Any]:
    scores = score_location_record(record)
    themes = dominant_themes(scores)
    bucket = assign_bucket(scores, themes, rank=rank)
    recommendation_key = recommendation_key_for_bucket(bucket, scores)
    prose_key = recommendation_prose_key(recommendation_key, scores, themes, candidate)
    return {
        "location_id": candidate["location_id"],
        "display_name": candidate["display_name"],
        "candidate": copy.deepcopy(candidate),
        "bucket": bucket,
        "bucket_label": BUCKET_LABELS[bucket],
        "recommendation_key": recommendation_key,
        "recommendation_prose_key": prose_key,
        "recommendation_label": RECOMMENDATION_LABELS[recommendation_key],
        "prose_variation_traits": prose_variation_traits(scores, themes),
        "dominant_themes": themes,
        "scores": scores,
        "evidence_refs": _evidence_refs(record),
        "evidence_record": copy.deepcopy(record),
    }


def build_scored_locations(records_with_candidates: list[tuple[dict[str, Any], dict[str, Any]]]) -> list[dict[str, Any]]:
    raw_scores = [raw_score_location_record(record) for record, _candidate in records_with_candidates]
    normalized_scores = normalize_raw_scores(raw_scores)
    scored: list[dict[str, Any]] = []
    for index, ((record, candidate), scores) in enumerate(zip(records_with_candidates, normalized_scores)):
        themes = dominant_themes(scores)
        bucket = assign_bucket(scores, themes, rank=index)
        recommendation_key = recommendation_key_for_bucket(bucket, scores)
        prose_key = recommendation_prose_key(recommendation_key, scores, themes, candidate)
        scored.append({
            "location_id": candidate["location_id"],
            "display_name": candidate["display_name"],
            "candidate": copy.deepcopy(candidate),
            "bucket": bucket,
            "bucket_label": BUCKET_LABELS[bucket],
            "recommendation_key": recommendation_key,
            "recommendation_prose_key": prose_key,
            "recommendation_label": RECOMMENDATION_LABELS[recommendation_key],
            "prose_variation_traits": prose_variation_traits(scores, themes),
            "dominant_themes": themes,
            "scores": scores,
            "raw_scores": copy.deepcopy(raw_scores[index]),
            "normalization_profile": copy.deepcopy(NORMALIZATION_PROFILE),
            "evidence_refs": _evidence_refs(record),
            "evidence_record": copy.deepcopy(record),
        })
    return scored


def select_curated_locations(scored_locations: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    ranked = sorted(
        (copy.deepcopy(item) for item in scored_locations),
        key=lambda item: (
            item["scores"]["overall_resonance"],
            item["scores"]["consensus_score"],
            item["scores"]["baseline_divergence"],
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    state_counts: Counter = Counter()
    bucket_counts: Counter = Counter()
    for item in ranked:
        _initialize_tile_metadata(item)
        nearby_similar = [
            selected_item
            for selected_item in selected
            if _is_similar_nearby(item, selected_item)
        ]
        if len(nearby_similar) >= MAX_SIMILAR_TILES_PER_PROXIMITY_CLUSTER:
            representative = min(
                nearby_similar,
                key=lambda selected_item: _distance_miles(item, selected_item) or float("inf"),
            )
            distance = _distance_miles(item, representative)
            representative["cluster_alternates"].append(
                _alternate_summary(item, representative, distance)
            )
            continue

        state = (item.get("candidate") or {}).get("state")
        if state and state_counts[state] >= 3:
            continue
        if bucket_counts[item["bucket"]] >= max(3, limit // 3):
            continue
        if nearby_similar:
            item["regional_role"] = "cluster_peer"
            representative = min(
                nearby_similar,
                key=lambda selected_item: _distance_miles(item, selected_item) or float("inf"),
            )
            item["sibling_difference"] = _sibling_difference(item, representative, _distance_miles(item, representative))
        item["selection_rank"] = len(selected) + 1
        selected.append(item)
        if state:
            state_counts[state] += 1
        bucket_counts[item["bucket"]] += 1
        if len(selected) >= limit:
            break

    if len(selected) < min(limit, len(ranked)):
        selected_ids = {item["location_id"] for item in selected}
        for item in ranked:
            if item["location_id"] in selected_ids:
                continue
            _initialize_tile_metadata(item)
            nearby_similar = [
                selected_item
                for selected_item in selected
                if _is_similar_nearby(item, selected_item)
            ]
            if len(nearby_similar) >= MAX_SIMILAR_TILES_PER_PROXIMITY_CLUSTER:
                representative = min(
                    nearby_similar,
                    key=lambda selected_item: _distance_miles(item, selected_item) or float("inf"),
                )
                distance = _distance_miles(item, representative)
                representative["cluster_alternates"].append(
                    _alternate_summary(item, representative, distance)
                )
                continue
            if nearby_similar:
                item["regional_role"] = "cluster_peer"
                representative = min(
                    nearby_similar,
                    key=lambda selected_item: _distance_miles(item, selected_item) or float("inf"),
                )
                item["sibling_difference"] = _sibling_difference(item, representative, _distance_miles(item, representative))
            item["selection_rank"] = len(selected) + 1
            selected.append(item)
            if len(selected) >= limit:
                break

    for item in selected:
        if item.get("cluster_alternates"):
            item["regional_role"] = "cluster_lead"

    return selected


def bucket_distribution(selected_locations: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter = Counter(item.get("bucket") for item in selected_locations)
    return {bucket: counts.get(bucket, 0) for bucket in BUCKET_KEYS}
