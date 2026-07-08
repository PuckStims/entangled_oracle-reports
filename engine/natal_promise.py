"""
engine/natal_promise.py - Phase 7 natal promise anchors and matching.

The module builds chart-scoped NatalPromiseAnchor records and applies them to
ForecastEvent/PredictiveSignal-shaped dictionaries. It is intentionally
sidecar-safe: no prose, no candidate emission, and no new clock families.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "phase0.1.1"
POLICY_VERSION = "phase7_natal_promise_v1"

DOMAIN_KEYS = {
    "identity",
    "resources",
    "communication",
    "home",
    "creativity",
    "work",
    "partnership",
    "transformation",
    "meaning",
    "vocation",
    "community",
    "spirit",
}

HOUSE_DOMAINS = {
    1: "identity",
    2: "resources",
    3: "communication",
    4: "home",
    5: "creativity",
    6: "work",
    7: "partnership",
    8: "transformation",
    9: "meaning",
    10: "vocation",
    11: "community",
    12: "spirit",
}

HOUSE_TOPIC_KEYS = {
    1: ["identity", "essence", "becoming"],
    2: ["material", "resources", "essential_code"],
    3: ["voice", "message", "translation"],
    4: ["memory", "ancestral_thread", "hidden_lineage"],
    5: ["creativity", "delight", "inner_child"],
    6: ["practice", "labor", "sustained_effort"],
    7: ["attraction", "harmony", "destined_encounter"],
    8: ["transformation", "obligation", "submerged_knowledge"],
    9: ["wisdom", "big_picture", "cosmology"],
    10: ["radiance", "vocation", "right_order"],
    11: ["community", "gathering", "pattern_weaving"],
    12: ["spirit", "silent_prayer", "psychopomp"],
}

BODY_TOPIC_KEYS = {
    "Sun": ["radiance", "essence", "animating_spark"],
    "Moon": ["memory", "remembrance", "submerged_knowledge"],
    "Mercury": ["voice", "message", "translation"],
    "Venus": ["attraction", "harmony", "desire"],
    "Mars": ["catalyst", "strategy", "rupture"],
    "Jupiter": ["wisdom", "big_picture", "opportunity"],
    "Saturn": ["obligation", "right_order", "sustained_effort"],
    "Uranus": ["rupture", "reorganization", "disclosure"],
    "Neptune": ["enchantment", "silent_prayer", "submerged_knowledge"],
    "Pluto": ["transformation", "threshold", "primal_reorganization"],
    "Chiron": ["restoration", "practice", "threshold"],
    "North_Node": ["fate", "thread", "threshold"],
    "South_Node": ["karmic_thread", "memory", "exile_return"],
    "Lilith_BML": ["refusal", "unbound_self", "truth_under_doubt"],
}

ANGLE_TOPIC_KEYS = {
    "Ascendant": ["identity", "becoming", "threshold"],
    "ASC": ["identity", "becoming", "threshold"],
    "Midheaven": ["vocation", "radiance", "right_order"],
    "MC": ["vocation", "radiance", "right_order"],
    "Descendant": ["partnership", "attraction", "destined_encounter"],
    "DSC": ["partnership", "attraction", "destined_encounter"],
    "Imum_Coeli": ["home", "memory", "ancestral_thread"],
    "Imum Coeli": ["home", "memory", "ancestral_thread"],
    "IC": ["home", "memory", "ancestral_thread"],
    "Vertex": ["fate", "destined_encounter", "threshold_event"],
}

SIGNS = [
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
]

TRADITIONAL_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

MODERN_CO_RULERS = {
    "Scorpio": "Pluto",
    "Aquarius": "Uranus",
    "Pisces": "Neptune",
}

ALLOWED_ASPECTS = {"Conjunction", "Sextile", "Square", "Trine", "Opposition"}


def natal_snapshot_id_for_payload(payload: dict, extra: dict | None = None) -> str:
    """Returns a deterministic natal snapshot ID for predictive-engine use."""
    user_profile = payload.get("user_profile") if isinstance(payload.get("user_profile"), dict) else {}
    basis = {
        "birth": {
            "local_datetime": user_profile.get("local_datetime") or payload.get("local_datetime") or payload.get("birth_date"),
            "julian_day": user_profile.get("julian_day") or payload.get("julian_day"),
            "birth_time_state": user_profile.get("birth_time_state") or payload.get("birth_time_state"),
        },
        "methodology": user_profile.get("methodology") if isinstance(user_profile.get("methodology"), dict) else {},
        "standard_planets": payload.get("standard_planets") or {},
        "angles": payload.get("angles") or {},
        "extra": extra or {},
    }
    return _hash_id("natal", basis, length=16)


def build_natal_promise_anchors(
    payload: dict,
    index_results: dict | None = None,
    *,
    natal_snapshot_id: str | None = None,
    created_at: datetime | None = None,
) -> list[dict]:
    """Build NatalPromiseAnchor records for the chart."""
    snapshot_id = natal_snapshot_id or natal_snapshot_id_for_payload(payload)
    emitted_at = created_at or datetime.now(timezone.utc)
    index_results = index_results if isinstance(index_results, dict) else {}
    policy = _load_asteroid_policy()
    houses = _house_signs(payload)
    placements = _placements(payload)
    anchors: list[dict] = []

    for house, sign in sorted(houses.items()):
        rulers = _rulers_for_sign(sign)
        topics = _topic_list(HOUSE_TOPIC_KEYS.get(house, []))
        anchors.append(_anchor(
            snapshot_id,
            "house_axis",
            topics,
            [HOUSE_DOMAINS[house]],
            houses=[house],
            rulers=rulers,
            dispositors=_dispositors_for_bodies(payload, rulers),
            evidence_trace={"source": "whole_sign_house", "house": house, "sign": sign},
            strength_components={"body_prominence": 0.0, "aspect_tightness": 0.0, "configuration_bonus": 0.0, "index_link_bonus": 0.0, "angularity": 0.0, "sect_bonus": 0.0},
            confidence=0.82,
            birth_time_dependency="soft",
            created_at=emitted_at,
        ))

    for body, data in placements["standard_planets"].items():
        house = _int_or_none(data.get("house"))
        topics = _topic_list(BODY_TOPIC_KEYS.get(body, ["situational"]))
        domain_keys = [HOUSE_DOMAINS[house]] if house in HOUSE_DOMAINS else []
        anchors.append(_anchor(
            snapshot_id,
            "topic_focus",
            topics,
            domain_keys,
            natal_bodies=[body],
            houses=[house] if house else [],
            rulers=_rulers_for_sign(str(data.get("sign") or "")),
            dispositors=_dispositors_for_bodies(payload, [body]),
            aspects=_aspects_for_body(payload, body),
            evidence_trace={"source": "natal_body", "body": body, "placement": _public_placement(data)},
            strength_components=_body_strength_components(payload, body, data),
            confidence=0.88,
            birth_time_dependency="soft" if house else "none",
            created_at=emitted_at,
        ))

    for angle, data in placements["angles"].items():
        house = _int_or_none(data.get("house"))
        domain_keys = [HOUSE_DOMAINS[house]] if house in HOUSE_DOMAINS else []
        anchors.append(_anchor(
            snapshot_id,
            "angle_axis",
            _topic_list(ANGLE_TOPIC_KEYS.get(angle, ["threshold"])),
            domain_keys,
            houses=[house] if house else [],
            rulers=_rulers_for_sign(str(data.get("sign") or "")),
            evidence_trace={"source": "natal_angle", "angle": angle, "placement": _public_placement(data)},
            strength_components={"body_prominence": 0.0, "aspect_tightness": 0.0, "configuration_bonus": 0.0, "index_link_bonus": 0.0, "angularity": 0.35, "sect_bonus": 0.0},
            confidence=0.80 if _birth_time_state(payload) != "unknown" else 0.42,
            birth_time_dependency="hard",
            created_at=emitted_at,
        ))

    for asteroid, data in placements["custom_asteroids"].items():
        record = policy.record_for(asteroid) if policy else None
        topics = _topic_list(record.get("topic_keys", []) if record else ["situational"])
        domain_keys = _domain_list(record.get("domain_keys", []) if record else [])
        house = _int_or_none(data.get("house"))
        if house in HOUSE_DOMAINS and HOUSE_DOMAINS[house] not in domain_keys:
            domain_keys.append(HOUSE_DOMAINS[house])
        index_links = _index_links_for_asteroid(asteroid, record, index_results)
        anchors.append(_anchor(
            snapshot_id,
            "index_signature" if index_links else "topic_focus",
            topics,
            domain_keys,
            natal_asteroids=[asteroid],
            houses=[house] if house else [],
            rulers=_rulers_for_sign(str(data.get("sign") or "")),
            dispositors=_dispositors_for_bodies(payload, [asteroid]),
            aspects=_aspects_for_body(payload, asteroid),
            proprietary_index_links=index_links,
            evidence_trace={"source": "custom_asteroid", "asteroid": asteroid, "registry_tier": record.get("tier") if record else "", "placement": _public_placement(data)},
            strength_components=_asteroid_strength_components(payload, asteroid, data, index_links),
            confidence=0.78 if record else 0.58,
            birth_time_dependency="soft" if house else "none",
            created_at=emitted_at,
        ))

    anchors.extend(_configuration_anchors(payload, snapshot_id, emitted_at))
    anchors.extend(_index_result_anchors(payload, index_results, snapshot_id, emitted_at))
    return _dedupe_anchors(anchors)


def apply_anchor_matching(records: list[dict], anchors: list[dict], payload: dict | None = None) -> list[dict]:
    """Mutates records in place, filling natal_anchor_ids and inherited topics/domains."""
    for record in records:
        if not isinstance(record, dict):
            continue
        matched = match_anchor_ids(record, anchors, payload or {})
        record["natal_anchor_ids"] = matched
        topic_keys = set(_string_list(record.get("topic_keys")))
        domain_keys = set(_string_list(record.get("domain_keys")))
        for anchor in anchors:
            if anchor.get("anchor_id") in matched:
                topic_keys.update(_string_list(anchor.get("topic_keys")))
                domain_keys.update(_string_list(anchor.get("domain_keys")))
        record["topic_keys"] = sorted(topic_keys)
        record["domain_keys"] = sorted(domain_keys)
    return records


def match_anchor_ids(record: dict, anchors: list[dict], payload: dict | None = None) -> list[str]:
    """Return anchor IDs activated by a ForecastEvent/PredictiveSignal record."""
    source = _canonical_body(record.get("source_body"))
    target = _canonical_body(record.get("target_body"))
    activation_route = str(record.get("activation_route") or "")
    method_family = str(record.get("method_family") or "")
    record_topics = set(_string_list(record.get("topic_keys")))
    record_domains = set(_string_list(record.get("domain_keys")))
    asteroid_participants = {_canonical_body(item) for item in _string_list(record.get("asteroid_participants"))}
    body_candidates = {item for item in (source, target) if item}
    body_candidates.update(item for item in asteroid_participants if item)
    target_house = _target_house(payload or {}, target)

    scored: list[tuple[float, str]] = []
    for anchor in anchors:
        score = 0.0
        anchor_bodies = {_canonical_body(item) for item in _string_list(anchor.get("natal_bodies"))}
        anchor_asteroids = {_canonical_body(item) for item in _string_list(anchor.get("natal_asteroids"))}
        anchor_lots = {_canonical_body(item) for item in _string_list(anchor.get("natal_lots"))}
        anchor_targets = anchor_bodies | anchor_asteroids | anchor_lots
        if target and target in anchor_targets:
            score += 4.0
        if source and source in anchor_targets:
            score += 2.0
        if anchor_asteroids & body_candidates:
            score += 3.0
        if target_house and target_house in [_int_or_none(h) for h in anchor.get("houses", [])]:
            score += 1.2
        topic_overlap = set(_string_list(anchor.get("topic_keys"))) & record_topics
        domain_overlap = set(_string_list(anchor.get("domain_keys"))) & record_domains
        score += min(1.5, len(topic_overlap) * 0.5)
        score += min(1.0, len(domain_overlap) * 0.5)
        if method_family in {"PROFECTION", "TIME_LORD", "ZODIACAL_RELEASING"} and anchor.get("anchor_kind") in {"house_axis", "ruler_chain"}:
            score += 0.5
        if activation_route.endswith("_to_angle") and anchor.get("anchor_kind") == "angle_axis":
            score += 1.0
        if score > 0:
            scored.append((score, str(anchor.get("anchor_id"))))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [anchor_id for score, anchor_id in scored[:6] if score >= 1.0 and anchor_id]


def _anchor(
    natal_snapshot_id: str,
    anchor_kind: str,
    topic_keys: list[str],
    domain_keys: list[str],
    *,
    natal_bodies: list[str] | None = None,
    natal_asteroids: list[str] | None = None,
    natal_lots: list[str] | None = None,
    houses: list[int] | None = None,
    rulers: list[str] | None = None,
    dispositors: list[str] | None = None,
    aspects: list[dict] | None = None,
    configurations: list[str] | None = None,
    proprietary_index_links: list[dict] | None = None,
    strength_components: dict[str, float] | None = None,
    confidence: float = 0.75,
    birth_time_dependency: str = "none",
    evidence_trace: dict | None = None,
    created_at: datetime | None = None,
) -> dict:
    topics = _topic_list(topic_keys) or ["situational"]
    domains = _domain_list(domain_keys)
    bodies = _unique_strings(natal_bodies or [])
    asteroids = _unique_strings(natal_asteroids or [])
    lots = _unique_strings(natal_lots or [])
    anchor_houses = sorted({int(h) for h in houses or [] if isinstance(h, int) and 1 <= h <= 12})
    components = _complete_strength_components(strength_components or {})
    strength = _bounded(sum(components.values()))
    record = {
        "schema_version": SCHEMA_VERSION,
        "anchor_id": "",
        "natal_snapshot_id": natal_snapshot_id,
        "anchor_kind": anchor_kind,
        "topic_keys": topics,
        "domain_keys": domains,
        "natal_bodies": bodies,
        "natal_asteroids": asteroids,
        "natal_lots": lots,
        "houses": anchor_houses,
        "rulers": _unique_strings(rulers or []),
        "dispositors": _unique_strings(dispositors or []),
        "aspects": aspects or [],
        "configurations": _unique_strings(configurations or []),
        "proprietary_index_links": proprietary_index_links or [],
        "strength": round(strength, 4),
        "strength_components": components,
        "confidence": _bounded(confidence),
        "birth_time_dependency": birth_time_dependency if birth_time_dependency in {"none", "soft", "hard"} else "none",
        "evidence_trace": evidence_trace or {},
        "created_at": _iso_datetime(created_at or datetime.now(timezone.utc)),
        "policy_version": POLICY_VERSION,
    }
    record["anchor_id"] = _anchor_id(record)
    return record


def _configuration_anchors(payload: dict, snapshot_id: str, created_at: datetime) -> list[dict]:
    try:
        from formulas.standard.named_configurations import evaluate_named_configurations
        result = evaluate_named_configurations(payload)
    except Exception:
        return []
    anchors = []
    for config in result.get("configurations", []) if isinstance(result, dict) else []:
        if not isinstance(config, dict):
            continue
        bodies = _string_list(config.get("bodies"))
        houses = sorted({_target_house(payload, body) for body in bodies if _target_house(payload, body)})
        anchors.append(_anchor(
            snapshot_id,
            "named_pattern",
            _configuration_topics(str(config.get("type") or "")),
            [HOUSE_DOMAINS[h] for h in houses if h in HOUSE_DOMAINS],
            natal_bodies=[body for body in bodies if body in _standard(payload)],
            natal_asteroids=[body for body in bodies if body in _custom(payload)],
            houses=houses,
            configurations=[str(config.get("type") or "")],
            evidence_trace={"source": "named_configurations", "configuration": config},
            strength_components={"body_prominence": 0.12, "aspect_tightness": 0.10, "configuration_bonus": 0.30, "index_link_bonus": 0.0, "angularity": 0.0, "sect_bonus": 0.0},
            confidence=0.82,
            birth_time_dependency="soft" if houses else "none",
            created_at=created_at,
        ))
    return anchors


def _index_result_anchors(payload: dict, index_results: dict, snapshot_id: str, created_at: datetime) -> list[dict]:
    anchors = []
    drivers_by_index: dict[str, list[dict]] = {}
    policy = _load_asteroid_policy()
    if policy:
        for name in policy.asteroid_names:
            record = policy.record_for(name) or {}
            for index_name in _string_list(record.get("proprietary_index_links")):
                if name in _custom(payload):
                    drivers_by_index.setdefault(index_name, []).append({
                        "driver_body": name,
                        "topic_keys": record.get("topic_keys", []),
                        "domain_keys": record.get("domain_keys", []),
                    })
    for index_name, result in sorted(index_results.items()):
        if not isinstance(result, dict) or index_name not in drivers_by_index:
            continue
        drivers = drivers_by_index[index_name]
        bodies = [driver["driver_body"] for driver in drivers]
        topics: list[str] = []
        domains: list[str] = []
        for driver in drivers:
            topics.extend(_string_list(driver.get("topic_keys")))
            domains.extend(_string_list(driver.get("domain_keys")))
        links = [{
            "index": str(index_name),
            "dimension": str(index_name),
            "driver_body": body,
            "weight": _bounded(result.get("score", 0.5)),
        } for body in bodies]
        anchors.append(_anchor(
            snapshot_id,
            "index_signature",
            _topic_list(topics) or ["pattern_weaving"],
            _domain_list(domains),
            natal_asteroids=bodies,
            proprietary_index_links=links,
            evidence_trace={"source": "proprietary_index_results", "index": index_name, "result": result},
            strength_components={"body_prominence": 0.0, "aspect_tightness": 0.0, "configuration_bonus": 0.0, "index_link_bonus": min(0.35, 0.12 * len(links)), "angularity": 0.0, "sect_bonus": 0.0},
            confidence=0.74,
            birth_time_dependency="none",
            created_at=created_at,
        ))
    return anchors


def _house_signs(payload: dict) -> dict[int, str]:
    houses = payload.get("houses") if isinstance(payload.get("houses"), dict) else {}
    result: dict[int, str] = {}
    for key, value in houses.items():
        if not isinstance(value, dict):
            continue
        house = _house_number(key, value)
        sign = str(value.get("sign") or "")
        if house and sign:
            result[house] = sign
    if result:
        return result
    asc = _angles(payload).get("Ascendant") or _angles(payload).get("ASC") or {}
    asc_sign = str(asc.get("sign") or "")
    if asc_sign in SIGNS:
        start = SIGNS.index(asc_sign)
        return {house: SIGNS[(start + house - 1) % 12] for house in range(1, 13)}
    return {}


def _placements(payload: dict) -> dict[str, dict[str, dict]]:
    return {
        "standard_planets": _standard(payload),
        "angles": _angles(payload),
        "custom_asteroids": {
            name: data for name, data in _custom(payload).items()
            if isinstance(data, dict)
        },
    }


def _standard(payload: dict) -> dict[str, dict]:
    value = payload.get("standard_planets")
    return value if isinstance(value, dict) else {}


def _angles(payload: dict) -> dict[str, dict]:
    value = payload.get("angles")
    return value if isinstance(value, dict) else {}


def _custom(payload: dict) -> dict[str, Any]:
    value = payload.get("custom_asteroids")
    return value if isinstance(value, dict) else {}


def _rulers_for_sign(sign: str) -> list[str]:
    rulers = []
    if sign in TRADITIONAL_RULERS:
        rulers.append(TRADITIONAL_RULERS[sign])
    if sign in MODERN_CO_RULERS:
        rulers.append(MODERN_CO_RULERS[sign])
    return rulers


def _dispositors_for_bodies(payload: dict, bodies: list[str]) -> list[str]:
    result: list[str] = []
    placements = {**_standard(payload), **{k: v for k, v in _custom(payload).items() if isinstance(v, dict)}}
    for body in bodies:
        data = placements.get(body)
        if isinstance(data, dict):
            result.extend(_rulers_for_sign(str(data.get("sign") or "")))
    return result


def _aspects_for_body(payload: dict, body: str) -> list[dict]:
    aspects = []
    for raw in payload.get("aspects", []) if isinstance(payload.get("aspects"), list) else []:
        if not isinstance(raw, dict):
            continue
        body_a = str(raw.get("body_1") or raw.get("body_a") or "")
        body_b = str(raw.get("body_2") or raw.get("body_b") or "")
        aspect = str(raw.get("aspect") or "")
        if body not in {body_a, body_b} or aspect not in ALLOWED_ASPECTS:
            continue
        aspects.append({
            "body_a": body_a,
            "body_b": body_b,
            "aspect": aspect,
            "orb": round(_float(raw.get("orb"), 0.0), 4),
        })
    return aspects


def _index_links_for_asteroid(asteroid: str, record: dict | None, index_results: dict) -> list[dict]:
    links = []
    for index_name in _string_list((record or {}).get("proprietary_index_links")):
        result = index_results.get(index_name) if isinstance(index_results, dict) else None
        weight = _float(result.get("score"), 0.5) if isinstance(result, dict) else 0.5
        links.append({
            "index": index_name,
            "dimension": index_name,
            "driver_body": asteroid,
            "weight": _bounded(weight),
        })
    return links


def _body_strength_components(payload: dict, body: str, data: dict) -> dict[str, float]:
    angular = 0.18 if _is_angular_house(_int_or_none(data.get("house"))) else 0.0
    aspect_bonus = min(0.22, 0.04 * len(_aspects_for_body(payload, body)))
    return {
        "body_prominence": 0.22,
        "aspect_tightness": aspect_bonus,
        "configuration_bonus": 0.0,
        "index_link_bonus": 0.0,
        "angularity": angular,
        "sect_bonus": 0.0,
    }


def _asteroid_strength_components(payload: dict, asteroid: str, data: dict, index_links: list[dict]) -> dict[str, float]:
    angular = 0.15 if _is_angular_house(_int_or_none(data.get("house"))) else 0.0
    aspect_bonus = min(0.18, 0.04 * len(_aspects_for_body(payload, asteroid)))
    index_bonus = min(0.30, 0.10 * len(index_links))
    return {
        "body_prominence": 0.16,
        "aspect_tightness": aspect_bonus,
        "configuration_bonus": 0.0,
        "index_link_bonus": index_bonus,
        "angularity": angular,
        "sect_bonus": 0.0,
    }


def _complete_strength_components(value: dict[str, float]) -> dict[str, float]:
    keys = ["body_prominence", "aspect_tightness", "configuration_bonus", "index_link_bonus", "angularity", "sect_bonus"]
    return {key: round(_bounded(value.get(key, 0.0)), 4) for key in keys}


def _configuration_topics(config_type: str) -> list[str]:
    return {
        "stellium": ["radiance", "pattern_weaving", "essence"],
        "grand_trine": ["harmony", "grace", "pattern_weaving"],
        "kite": ["opportunity", "radiance", "pattern_weaving"],
        "t_square": ["pressure_system", "catalyst", "threshold"],
        "grand_cross": ["pressure_system", "right_order", "structural_construction"],
        "yod": ["fate", "threshold", "right_order"],
        "mystic_rectangle": ["pattern_weaving", "harmony", "right_order"],
    }.get(config_type, ["pattern_weaving"])


def _target_house(payload: dict, body: str) -> int | None:
    if not body:
        return None
    if body.isdigit():
        house = int(body)
        return house if 1 <= house <= 12 else None
    for collection in (_standard(payload), _angles(payload), _custom(payload)):
        data = collection.get(body)
        if isinstance(data, dict):
            return _int_or_none(data.get("house"))
    alias = {"ASC": "Ascendant", "MC": "Midheaven", "DSC": "Descendant", "IC": "Imum_Coeli"}.get(body)
    if alias:
        data = _angles(payload).get(alias)
        if isinstance(data, dict):
            return _int_or_none(data.get("house"))
    return None


def _public_placement(data: dict) -> dict:
    return {
        "sign": data.get("sign"),
        "house": data.get("house"),
        "degree": data.get("degree"),
        "longitude": data.get("longitude"),
    }


def _birth_time_state(payload: dict) -> str:
    user_profile = payload.get("user_profile") if isinstance(payload.get("user_profile"), dict) else {}
    raw = str(user_profile.get("birth_time_state") or user_profile.get("birth_time_confidence") or payload.get("birth_time_state") or "").lower()
    if "unknown" in raw:
        return "unknown"
    if "approx" in raw:
        return "approximate"
    return "exact"


def _load_asteroid_policy() -> Any:
    try:
        from engine.asteroid_policy import load_asteroid_policy
        return load_asteroid_policy()
    except Exception:
        return None


def _house_number(key: Any, value: dict) -> int | None:
    raw = value.get("house") or value.get("number")
    if raw is None:
        raw = str(key).replace("House_", "").replace("house_", "")
    return _int_or_none(raw)


def _is_angular_house(house: int | None) -> bool:
    return house in {1, 4, 7, 10}


def _topic_list(values: list[Any]) -> list[str]:
    # Reserved Phase 0 topic namespace. Invalid accidental words are dropped.
    allowed = {
        "voice", "attraction", "desire", "harmony", "clarity", "oracle", "radiance", "prophecy",
        "truth_under_doubt", "warning", "insight_validation", "disclosure", "unconcealment",
        "karmic_thread", "cause_effect", "obligation", "destined_encounter", "catalyst", "threshold_person",
        "memory", "remembrance", "ancestral_thread", "submerged_knowledge", "lost_pattern", "hidden_lineage",
        "wisdom", "gnosis", "deep_knowing", "pattern_weaving", "hubris", "structural_construction",
        "rupture", "generative_void", "primal_reorganization", "message", "translation", "boundary_crossing",
        "natural_law", "right_order", "oath", "lyric", "melody", "delight", "celestial_mapping",
        "cosmology", "big_picture", "sacred_song", "silent_prayer", "transformation", "enchantment",
        "potion", "restoration", "magical_sovereignty", "gathering", "practice", "rehearsal",
        "meditation", "intimate_lyric", "eros", "tender_expression", "dance", "rhythm", "movement",
        "strategy", "craft", "tactical_wisdom", "crossroads", "threshold", "keys", "night_wisdom",
        "sacrifice", "ruthless_devotion", "cost_of_love", "labor", "sustained_effort", "industry",
        "soul", "essence", "animating_spark", "fate", "thread", "allotment", "refusal",
        "exile_return", "unbound_self", "psychopomp", "weighing", "transition", "fierce_protection",
        "destruction_of_illusion", "war_against_falsehood", "innocence", "inner_child", "becoming",
        "grace", "luminous_aid", "guardianship", "inheritance", "essential_code", "lineage",
        "chapter_opening", "chapter_climax", "chapter_close", "chapter_reversal", "trigger_exactness",
        "trigger_station", "trigger_ingress", "trigger_lunation", "trigger_eclipse", "trigger_return_moment",
        "long_clock_activation", "long_clock_transition", "time_lord_handoff", "pressure_system",
        "reorganization", "revelation", "disruption", "collision", "opportunity", "aftermath",
        "background_field", "timing_shift", "threshold_event", "situational", "interpersonal",
        "practical", "environmental", "institutional", "material", "atmospheric",
    }
    return sorted({str(item) for item in values if str(item) in allowed})


def _domain_list(values: list[Any]) -> list[str]:
    return sorted({str(item) for item in values if str(item) in DOMAIN_KEYS})


def _dedupe_anchors(anchors: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped = []
    for anchor in sorted(anchors, key=lambda item: item.get("anchor_id", "")):
        anchor_id = str(anchor.get("anchor_id") or "")
        if not anchor_id or anchor_id in seen:
            continue
        seen.add(anchor_id)
        deduped.append(anchor)
    return deduped


def _anchor_id(record: dict) -> str:
    basis = {
        "natal_snapshot_id": record.get("natal_snapshot_id"),
        "topic_keys": sorted(record.get("topic_keys") or []),
        "natal_bodies": sorted(record.get("natal_bodies") or []),
        "natal_asteroids": sorted(record.get("natal_asteroids") or []),
        "natal_lots": sorted(record.get("natal_lots") or []),
        "houses": sorted(record.get("houses") or []),
        "configurations": sorted(record.get("configurations") or []),
        "proprietary_index_links": record.get("proprietary_index_links") or [],
    }
    return _hash_id("npa", basis)


def _hash_id(prefix: str, value: Any, *, length: int = 8) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:length]}"


def _canonical_body(value: Any) -> str:
    label = str(value or "").strip()
    return {
        "Imum Coeli": "Imum_Coeli",
        "Solar": "Sun",
        "Lunar": "Moon",
    }.get(label, label)


def _unique_strings(values: list[Any]) -> list[str]:
    return sorted({str(item) for item in values if str(item)})


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded(value: Any) -> float:
    return max(0.0, min(1.0, _float(value, 0.0)))


def _iso_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
