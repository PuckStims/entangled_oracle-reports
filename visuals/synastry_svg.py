"""Deterministic SVG visuals for synastry report surfaces.

The renderer consumes structured synastry evidence and emits inline SVG only.
It intentionally avoids compatibility scores, verdict language, timing claims,
and unsupported relationship-outcome language.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from math import cos, pi, sin
from pathlib import Path
from typing import Any


FORBIDDEN_CONSUMER_TERMS = (
    "compatibility percentage",
    "compatibility score",
    "soulmate",
    "meant to be",
    "destined",
    "guaranteed",
    "success rate",
    "failure rate",
    "timing window",
)

HOUSE_TOPIC_LABELS = {
    1: "body and presence",
    2: "resources and steadiness",
    3: "daily communication",
    4: "private ground",
    5: "play and romance",
    6: "routine and care",
    7: "partnership-recognition field",
    8: "intimacy and shared stakes",
    9: "meaning and worldview",
    10: "public direction",
    11: "networks and future plans",
    12: "hidden/porous/private material",
}

CATEGORY_LABELS = {
    "emotional_climate": "Emotional climate",
    "communication_exchange": "Communication",
    "attraction_encounter": "Attraction",
    "depth_shared_stakes": "Depth",
    "private_ground": "Private ground",
    "play_romance": "Play",
    "care_responsibility": "Care",
    "growth_meaning": "Meaning",
    "friction_growth": "Growth edges",
    "composite_field": "Composite",
}

SECTION_CATEGORY_HINTS = {
    "relationship_at_a_glance": "composite_field",
    "core_relationship_signature": "attraction_encounter",
    "emotional_rhythm_attachment": "emotional_climate",
    "communication_daily_exchange": "communication_exchange",
    "growth_meaning_worldview": "growth_meaning",
    "care_routine_responsibility": "care_responsibility",
    "depth_intimacy_shared_stakes": "depth_shared_stakes",
    "attraction_visibility_encounter": "attraction_encounter",
    "home_body_private_terrain": "private_ground",
    "play_romance_idealization": "play_romance",
    "directional_landing": "private_ground",
    "shared_natal_baseline": "emotional_climate",
    "composite_relationship_field": "composite_field",
    "friction_growth_edges": "friction_growth",
    "integrated_relationship_portrait": "composite_field",
}


@dataclass(frozen=True)
class SynastryAspect:
    source_person: str
    source_body: str
    target_person: str
    target_body: str
    aspect: str
    orb: float | None = None
    score: float | None = None
    salience: float | None = None
    category: str = "composite_field"
    tone: str = "mixed"
    section_routes: list[str] = field(default_factory=list)
    label: str = ""


@dataclass(frozen=True)
class HouseOverlay:
    source_person: str
    source_body: str
    house_owner: str
    house_number: int
    house_topic_label: str
    salience: float | None = None
    section_routes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompositeSummary:
    sun_sign: str | None = None
    moon_sign: str | None = None
    mercury_sign: str | None = None
    venus_sign: str | None = None
    mars_sign: str | None = None
    saturn_sign: str | None = None
    dominant_register: str | None = None
    emotional_register: str | None = None
    key_composite_aspects: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class SynastrySVGData:
    person_a_name: str = "Person A"
    person_b_name: str = "Person B"
    birth_time_confidence: dict[str, str] = field(default_factory=dict)
    report_status: str = "Preview sample"
    aspects: list[SynastryAspect] = field(default_factory=list)
    house_overlays: list[HouseOverlay] = field(default_factory=list)
    composite: CompositeSummary | dict[str, Any] = field(default_factory=CompositeSummary)
    shared_natal_baseline: dict[str, Any] = field(default_factory=dict)
    category_scores: dict[str, float] = field(default_factory=dict)
    dominant_themes: list[str] = field(default_factory=list)
    evidence_limits: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SVGPalette:
    background: str
    panel: str
    text: str
    muted: str
    line: str
    ease: str
    activation: str
    tension: str
    mixed: str
    chip: str
    border: str


PALETTES = {
    "print_light": SVGPalette(
        background="#fbf7ef",
        panel="#fffdf8",
        text="#102238",
        muted="#6f675d",
        line="#25364f",
        ease="#5f8a7d",
        activation="#b88346",
        tension="#9c5a58",
        mixed="#6c6f87",
        chip="#f3eadc",
        border="#d9cbbb",
    ),
    "web_dark": SVGPalette(
        background="#111722",
        panel="#17202c",
        text="#f4efe5",
        muted="#b7aa99",
        line="#d8c49b",
        ease="#8fc6b0",
        activation="#d9a15e",
        tension="#d07472",
        mixed="#a7a1c9",
        chip="#243044",
        border="#384456",
    ),
    "monochrome_safe": SVGPalette(
        background="#ffffff",
        panel="#f8f8f8",
        text="#111111",
        muted="#555555",
        line="#111111",
        ease="#333333",
        activation="#111111",
        tension="#111111",
        mixed="#444444",
        chip="#eeeeee",
        border="#bbbbbb",
    ),
}


def normalize_synastry_for_svg(raw_synastry: Any) -> SynastrySVGData:
    """Adapts pair payloads or assembled synastry contexts into SVG input."""
    if isinstance(raw_synastry, SynastrySVGData):
        return raw_synastry
    if not isinstance(raw_synastry, dict):
        return SynastrySVGData(evidence_limits=["No structured synastry data was available for the visual layer."])

    pair_payload = raw_synastry.get("source_pair_payload") if "source_pair_payload" in raw_synastry else raw_synastry
    if not isinstance(pair_payload, dict):
        pair_payload = {}

    context_names = {
        "A": raw_synastry.get("person_a_name"),
        "B": raw_synastry.get("person_b_name"),
    }
    names = {
        "A": _person_name(pair_payload, "A", context_names.get("A")),
        "B": _person_name(pair_payload, "B", context_names.get("B")),
    }
    computations = pair_payload.get("computations") or {}
    mutuals = [item for item in computations.get("mutual_aspects", []) or [] if isinstance(item, dict)]
    directional = [item for item in computations.get("directional_aspects", []) or [] if isinstance(item, dict)]
    overlays = [item for item in computations.get("house_overlays", []) or [] if isinstance(item, dict) and not item.get("withheld")]
    composite = _normalize_composite(computations.get("composite") or {})
    aspects = _normalize_aspects(mutuals, directional, names)
    house_overlays = _normalize_house_overlays(overlays)
    category_scores = _category_scores(
        aspects,
        house_overlays,
        computations.get("relationship_convergence") or [],
        composite,
    )
    dominant_themes = _dominant_themes(category_scores, computations.get("relationship_convergence") or [])
    sidecar = pair_payload.get("sidecar") or {}
    withheld = sidecar.get("withheld_summary") or {}
    evidence_limits = []
    if int(withheld.get("total") or 0) > 0:
        evidence_limits.append(f"{int(withheld.get('total') or 0)} angle- or house-dependent record(s) withheld by confidence policy.")
    evidence_limits.extend(str(item) for item in (pair_payload.get("confidence") or {}).get("assumptions") or [] if isinstance(item, str))
    return SynastrySVGData(
        person_a_name=names["A"],
        person_b_name=names["B"],
        birth_time_confidence={
            "A": str((pair_payload.get("person_a") or {}).get("birth_time_state") or raw_synastry.get("person_a_birth_time_state") or ""),
            "B": str((pair_payload.get("person_b") or {}).get("birth_time_state") or raw_synastry.get("person_b_birth_time_state") or ""),
        },
        report_status=str(raw_synastry.get("report_status") or raw_synastry.get("report_subtitle") or "Preview sample"),
        aspects=aspects,
        house_overlays=house_overlays,
        composite=composite,
        shared_natal_baseline={"themes": computations.get("repeated_natal_themes") or []},
        category_scores=category_scores,
        dominant_themes=dominant_themes,
        evidence_limits=evidence_limits,
        claim_boundaries=[
            "Visuals show emphasis, directionality, resonance, activation, and growth edges.",
            "Static synastry visuals do not show outcomes or timing.",
            "House overlays are directional and belong to the chart that owns the houses.",
            "The midpoint composite is separate from cross-chart contacts.",
        ],
    )


def render_relationship_field_map(data: Any) -> str:
    data = normalize_synastry_for_svg(data)
    palette = PALETTES["print_light"]
    width, height = 920, 640
    left_center = (230, 250)
    right_center = (690, 250)
    aspects = _top_aspects(data.aspects, 10)
    body_positions = _body_positions(aspects, left_center, right_center)
    overlay_chips = _top_overlays(data.house_overlays, 6)
    theme_chips = data.dominant_themes[:4] or ["Evidence-based pattern map"]

    parts = _svg_start(width, height, "Relationship Field Map", _field_desc(data), palette)
    parts.append(_defs())
    parts.append(f"<rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" rx=\"18\" fill=\"{palette.background}\"/>")
    parts.append(f"<rect x=\"26\" y=\"24\" width=\"868\" height=\"592\" rx=\"16\" fill=\"{palette.panel}\" stroke=\"{palette.border}\"/>")
    parts.append(_field_shell(left_center, data.person_a_name, palette, "A"))
    parts.append(_field_shell(right_center, data.person_b_name, palette, "B"))

    for aspect in aspects:
        left = body_positions.get((aspect.source_person, aspect.source_body))
        right = body_positions.get((aspect.target_person, aspect.target_body))
        if not left or not right:
            continue
        color = _tone_color(aspect.tone, palette)
        width_px = _stroke_width(aspect.salience, aspect.score)
        dash = " stroke-dasharray=\"10 8\"" if aspect.tone == "tension" else ""
        double = aspect.tone == "activation" and _is_repeated_theme(aspect, aspects)
        curve = _bridge_path(left, right)
        parts.append(_metallic_thread_path(curve, color, width_px, palette, dash=dash))
        if double:
            parts.append(_metallic_thread_path(curve, color, "0.85", palette, transform="translate(0 5)", opacity="0.52"))

    for (person, body), (x, y) in body_positions.items():
        salience = max([_numeric(a.salience, _numeric(a.score, 0.35)) for a in aspects if (a.source_person, a.source_body) == (person, body) or (a.target_person, a.target_body) == (person, body)] or [0.35])
        parts.append(_node(x, y, body, salience, palette))

    parts.append(_chip_row(theme_chips, 250, 70, 420, palette))
    parts.append(_overlay_chip_panel(overlay_chips, data, palette))
    parts.append(_category_bars(data.category_scores, 92, 506, 736, palette))
    parts.append(_legend(586, 316, palette))
    parts.append("</svg>")
    return _sanitize_svg_output("".join(parts))


def save_relationship_field_map(data: Any, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_relationship_field_map(data), encoding="utf-8")
    return path


def render_section_glyph(section_key: str, data: Any) -> str:
    data = normalize_synastry_for_svg(data)
    palette = PALETTES["print_light"]
    score = _clamp(data.category_scores.get(SECTION_CATEGORY_HINTS.get(section_key, "composite_field"), 0.35), 0.08, 1.0)
    tone = _dominant_section_tone(section_key, data)
    color = _tone_color(tone, palette)
    title = str(section_key or "section").replace("_", " ").title()
    parts = _svg_start(168, 96, f"{title} Motif", f"Small visual motif for {title}.", palette, css_class="synastry-section-glyph")
    parts.append(f"<rect x=\"1\" y=\"1\" width=\"166\" height=\"94\" rx=\"10\" fill=\"{palette.panel}\" stroke=\"{palette.border}\"/>")
    cx, cy = 84, 48
    if section_key == "core_relationship_signature":
        parts.append(_knot(cx, cy, color, palette, score))
    elif section_key == "emotional_rhythm_attachment":
        parts.append(_ripples(cx, cy, color, palette, score))
    elif section_key == "communication_daily_exchange":
        parts.append(_signal(cx, cy, color, palette, score))
    elif section_key == "growth_meaning_worldview":
        parts.append(_compass(cx, cy, color, palette, score))
    elif section_key == "care_routine_responsibility":
        parts.append(_rings(cx, cy, color, palette, score))
    elif section_key == "depth_intimacy_shared_stakes":
        parts.append(_vault(cx, cy, color, palette, score))
    elif section_key == "attraction_visibility_encounter":
        parts.append(_magnetism(cx, cy, color, palette, score))
    elif section_key == "home_body_private_terrain":
        parts.append(_ground(cx, cy, color, palette, score))
    elif section_key == "play_romance_idealization":
        parts.append(_spark(cx, cy, color, palette, score))
    elif section_key == "directional_landing":
        parts.append(_mirrored(cx, cy, color, palette, score))
    elif section_key == "shared_natal_baseline":
        parts.append(_echo(cx, cy, color, palette, score))
    elif section_key == "composite_relationship_field":
        parts.append(_composite_mark(cx, cy, color, palette, score, data))
    elif section_key == "friction_growth_edges":
        parts.append(_tension(cx, cy, color, palette, score))
    elif section_key == "integrated_relationship_portrait":
        parts.append(_integrated(cx, cy, color, palette, score))
    else:
        parts.append(_knot(cx, cy, color, palette, score))
    parts.append(f"<text x=\"84\" y=\"86\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"8\" fill=\"{palette.muted}\">{_text(title[:28])}</text>")
    parts.append("</svg>")
    return _sanitize_svg_output("".join(parts))


def render_directional_landing_map(data: Any) -> str:
    data = normalize_synastry_for_svg(data)
    palette = PALETTES["print_light"]
    parts = _svg_start(760, 300, "Directional Landing Map", _directional_desc(data), palette)
    parts.append(f"<rect x=\"0\" y=\"0\" width=\"760\" height=\"300\" rx=\"16\" fill=\"{palette.background}\"/>")
    parts.append(_landing_side(24, 34, 344, 224, "A_to_B", data.person_a_name, data.person_b_name, data, palette))
    parts.append(_landing_side(392, 34, 344, 224, "B_to_A", data.person_b_name, data.person_a_name, data, palette))
    parts.append(f"<text x=\"380\" y=\"282\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"10\" fill=\"{palette.muted}\">House overlays are directional; they describe where one person's body symbolism lands in the other person's house field.</text>")
    parts.append("</svg>")
    return _sanitize_svg_output("".join(parts))


def render_composite_field_sigIl(data: Any) -> str:
    return render_composite_field_sigil(data)


def render_composite_field_sigil(data: Any) -> str:
    data = normalize_synastry_for_svg(data)
    palette = PALETTES["print_light"]
    parts = _svg_start(360, 220, "Composite Field Sigil", _composite_desc(data), palette)
    parts.append(f"<rect x=\"0\" y=\"0\" width=\"360\" height=\"220\" rx=\"16\" fill=\"{palette.background}\"/>")
    parts.append(_composite_mark(180, 98, palette.activation, palette, 0.8, data, large=True))
    composite = data.composite if isinstance(data.composite, CompositeSummary) else CompositeSummary()
    labels = [
        ("Sun", composite.sun_sign),
        ("Moon", composite.moon_sign),
        ("Mercury", composite.mercury_sign),
        ("Venus", composite.venus_sign),
        ("Mars", composite.mars_sign),
        ("Saturn", composite.saturn_sign),
    ]
    x = 48
    for body, sign in labels:
        if not sign:
            continue
        parts.append(f"<text x=\"{x}\" y=\"190\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"9\" fill=\"{palette.text}\">{_text(body)}</text>")
        parts.append(f"<text x=\"{x}\" y=\"204\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"8\" fill=\"{palette.muted}\">{_text(sign)}</text>")
        x += 52
    parts.append("</svg>")
    return _sanitize_svg_output("".join(parts))


def render_aspect_badge(label: str, tone: str) -> str:
    palette = PALETTES["print_light"]
    color = _tone_color(_normalize_tone(tone), palette)
    safe = _text(label)
    width = max(92, min(220, 44 + len(safe) * 7))
    parts = _svg_start(width, 30, "Aspect Badge", f"Inline aspect badge labeled {safe}.", palette)
    parts.append(f"<rect x=\"1\" y=\"1\" width=\"{width - 2}\" height=\"28\" rx=\"14\" fill=\"{palette.chip}\" stroke=\"{color}\"/>")
    parts.append(f"<circle cx=\"17\" cy=\"15\" r=\"4\" fill=\"{color}\"/>")
    parts.append(f"<text x=\"30\" y=\"19\" font-family=\"Arial, sans-serif\" font-size=\"11\" fill=\"{palette.text}\">{safe}</text>")
    parts.append("</svg>")
    return _sanitize_svg_output("".join(parts))


def render_visual_legend() -> str:
    palette = PALETTES["print_light"]
    parts = _svg_start(760, 170, "Synastry Visual Legend", "Legend for deterministic synastry visuals and method boundaries.", palette)
    parts.append(f"<rect x=\"0\" y=\"0\" width=\"760\" height=\"170\" rx=\"14\" fill=\"{palette.background}\"/>")
    parts.append(_legend(34, 24, palette, full=True))
    notes = [
        "Directional aspects show contact routing, not blame or one-way causality.",
        "Mutual aspects summarize traceable contacts; line weight shows relative emphasis only.",
        "House overlays are directional and belong to the chart that owns the houses.",
        "The midpoint composite is separate from cross-chart contacts.",
        "Static synastry does not support timing claims or relationship outcomes.",
    ]
    y = 42
    for note in notes:
        parts.append(f"<text x=\"292\" y=\"{y}\" font-family=\"Arial, sans-serif\" font-size=\"11\" fill=\"{palette.text}\">{_text(note)}</text>")
        y += 22
    parts.append("</svg>")
    return _sanitize_svg_output("".join(parts))


def _normalize_aspects(mutuals: list[dict], directional: list[dict], names: dict[str, str]) -> list[SynastryAspect]:
    aspects: list[SynastryAspect] = []
    for mutual in mutuals:
        entries = [entry for entry in mutual.get("mutual_key", []) or [] if isinstance(entry, dict)]
        if len(entries) < 2 or not mutual.get("aspect"):
            continue
        source, target = entries[0], entries[1]
        category = _category_for_bodies({str(source.get("body") or ""), str(target.get("body") or "")}, mutual.get("aspect"))
        tone = _tone_for_aspect(mutual.get("aspect"), {str(source.get("body") or ""), str(target.get("body") or "")})
        label = f"{names.get(source.get('person'), source.get('person'))} {source.get('body')} {mutual.get('aspect')} {names.get(target.get('person'), target.get('person'))} {target.get('body')}"
        aspects.append(
            SynastryAspect(
                source_person=str(source.get("person") or ""),
                source_body=str(source.get("body") or ""),
                target_person=str(target.get("person") or ""),
                target_body=str(target.get("body") or ""),
                aspect=str(mutual.get("aspect") or ""),
                orb=_optional_float(mutual.get("orb")),
                score=_optional_float(mutual.get("orb_fraction")),
                salience=_optional_float(mutual.get("salience")),
                category=category,
                tone=tone,
                section_routes=_sections_for_category(category),
                label=label,
            )
        )
    if aspects:
        return aspects

    for record in directional:
        if record.get("withheld") or not record.get("aspect"):
            continue
        bodies = {str(record.get("source_body") or ""), str(record.get("target_body") or "")}
        category = _category_for_bodies(bodies, record.get("aspect"))
        aspects.append(
            SynastryAspect(
                source_person=str(record.get("source_person") or ""),
                source_body=str(record.get("source_body") or ""),
                target_person=str(record.get("target_person") or ""),
                target_body=str(record.get("target_body") or ""),
                aspect=str(record.get("aspect") or ""),
                orb=_optional_float(record.get("orb")),
                score=_optional_float(record.get("orb_fraction")),
                salience=_optional_float(record.get("orb_fraction")),
                category=category,
                tone=_tone_for_aspect(record.get("aspect"), bodies),
                section_routes=_sections_for_category(category),
                label=f"{record.get('source_body')} {record.get('aspect')} {record.get('target_body')}",
            )
        )
    return aspects


def _normalize_house_overlays(overlays: list[dict]) -> list[HouseOverlay]:
    records = []
    for overlay in overlays:
        house = overlay.get("target_house")
        if not isinstance(house, int):
            continue
        source_body = str(overlay.get("source_body") or "")
        category = _category_for_overlay(source_body, house)
        records.append(
            HouseOverlay(
                source_person=str(overlay.get("source_person") or ""),
                source_body=source_body,
                house_owner=str(overlay.get("target_person") or ""),
                house_number=house,
                house_topic_label=HOUSE_TOPIC_LABELS.get(house, f"House {house}"),
                salience=_overlay_salience(source_body, house),
                section_routes=_sections_for_category(category),
            )
        )
    records.sort(key=lambda item: (-_numeric(item.salience, 0.0), item.house_owner, item.house_number, item.source_body))
    return records


def _normalize_composite(composite: dict) -> CompositeSummary:
    body_map = {
        str(item.get("body")): item
        for item in composite.get("bodies", []) or []
        if isinstance(item, dict) and not item.get("ambiguous")
    }

    def sign(body: str) -> str | None:
        return (body_map.get(body) or {}).get("zodiac_position", {}).get("sign")

    return CompositeSummary(
        sun_sign=sign("Sun"),
        moon_sign=sign("Moon"),
        mercury_sign=sign("Mercury"),
        venus_sign=sign("Venus"),
        mars_sign=sign("Mars"),
        saturn_sign=sign("Saturn"),
        dominant_register=sign("Sun") or sign("Mercury"),
        emotional_register=sign("Moon"),
        key_composite_aspects=[item for item in composite.get("aspects", []) or [] if isinstance(item, dict)][:6],
    )


def _category_scores(aspects: list[SynastryAspect], overlays: list[HouseOverlay], convergence: list[dict], composite: CompositeSummary) -> dict[str, float]:
    scores = {key: 0.0 for key in CATEGORY_LABELS}
    topic_to_category = {
        "attachment_emotional_rhythm": "emotional_climate",
        "communication": "communication_exchange",
        "affection_value_attraction": "attraction_encounter",
        "desire_friction_action": "friction_growth",
        "commitment_constraint_time": "care_responsibility",
        "visibility_public_path": "attraction_encounter",
        "growth_meaning": "growth_meaning",
        "intensity_merging_shared_resources": "depth_shared_stakes",
    }
    used_convergence = False
    for item in convergence:
        if not isinstance(item, dict):
            continue
        category = topic_to_category.get(str(item.get("signature_key") or ""))
        if category:
            scores[category] = max(scores[category], _clamp(_numeric(item.get("score"), 0.0), 0.0, 1.0))
            used_convergence = True
    for aspect in aspects:
        scores[aspect.category] += _numeric(aspect.salience, _numeric(aspect.score, 0.25)) * 0.22
        if aspect.tone == "tension":
            scores["friction_growth"] += 0.18
    for overlay in overlays:
        category = _category_for_overlay(overlay.source_body, overlay.house_number)
        scores[category] += _numeric(overlay.salience, 0.25) * 0.16
    if composite.sun_sign or composite.moon_sign:
        scores["composite_field"] = max(scores["composite_field"], 0.62)
    if not used_convergence and not aspects and not overlays:
        scores["composite_field"] = 0.18
    return {key: round(_clamp(value, 0.0, 1.0), 4) for key, value in scores.items()}


def _dominant_themes(scores: dict[str, float], convergence: list[dict]) -> list[str]:
    topic_labels = {
        "attachment_emotional_rhythm": "emotional rhythm",
        "communication": "communication",
        "affection_value_attraction": "attraction",
        "desire_friction_action": "activation",
        "commitment_constraint_time": "care and responsibility",
        "visibility_public_path": "visibility",
        "growth_meaning": "growth and meaning",
        "intensity_merging_shared_resources": "depth and shared stakes",
    }
    themes = [
        topic_labels.get(str(item.get("signature_key") or ""))
        for item in sorted([c for c in convergence if isinstance(c, dict)], key=lambda c: -_numeric(c.get("score"), 0.0))
    ]
    clean = [theme for theme in themes if theme]
    if clean:
        return clean[:4]
    return [CATEGORY_LABELS[key] for key, _ in sorted(scores.items(), key=lambda item: -item[1])[:4] if _ > 0.05]


def _person_name(pair_payload: dict, label: str, context_name: Any = None) -> str:
    if isinstance(context_name, str) and context_name.strip():
        return context_name.strip()
    relationship_meta = pair_payload.get("relationship_meta") or {}
    meta_key = "person_a_label" if label == "A" else "person_b_label"
    if isinstance(relationship_meta.get(meta_key), str) and relationship_meta[meta_key].strip():
        return relationship_meta[meta_key].strip()
    person_key = "person_a" if label == "A" else "person_b"
    profile = (((pair_payload.get(person_key) or {}).get("natal_payload") or {}).get("user_profile") or {})
    if isinstance(profile.get("name"), str) and profile["name"].strip():
        name = profile["name"].strip()
        if not name.lower().startswith("fixture"):
            return name
    return "Person A" if label == "A" else "Person B"


def _top_aspects(aspects: list[SynastryAspect], limit: int) -> list[SynastryAspect]:
    return sorted(aspects, key=lambda item: (-_numeric(item.salience, _numeric(item.score, 0.0)), _numeric(item.orb, 99.0), item.label))[:limit]


def _top_overlays(overlays: list[HouseOverlay], limit: int) -> list[HouseOverlay]:
    return sorted(overlays, key=lambda item: (-_numeric(item.salience, 0.0), item.house_owner, item.house_number, item.source_body))[:limit]


def _body_positions(aspects: list[SynastryAspect], left_center: tuple[int, int], right_center: tuple[int, int]) -> dict[tuple[str, str], tuple[float, float]]:
    people = {"A": [], "B": []}
    for aspect in aspects:
        for person, body in ((aspect.source_person, aspect.source_body), (aspect.target_person, aspect.target_body)):
            if person in people and body not in people[person]:
                people[person].append(body)
    positions = {}
    for person, bodies in people.items():
        center = left_center if person == "A" else right_center
        radius = 116
        count = max(1, len(bodies))
        for index, body in enumerate(bodies):
            angle = (-0.78 * pi) + (1.56 * pi * index / max(1, count - 1)) if count > 1 else -pi / 2
            if person == "B":
                angle = pi - angle
            positions[(person, body)] = (center[0] + radius * cos(angle), center[1] + radius * sin(angle))
    return positions


def _field_shell(center: tuple[int, int], name: str, palette: SVGPalette, label: str) -> str:
    cx, cy = center
    return (
        f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"128\" fill=\"none\" stroke=\"{palette.border}\" stroke-width=\"1.2\"/>"
        f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"90\" fill=\"none\" stroke=\"{palette.border}\" stroke-width=\"0.8\" stroke-dasharray=\"4 7\"/>"
        f"<text x=\"{cx}\" y=\"{cy - 8}\" text-anchor=\"middle\" font-family=\"Georgia, serif\" font-size=\"20\" fill=\"{palette.text}\">{_text(name)}</text>"
        f"<text x=\"{cx}\" y=\"{cy + 16}\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"10\" fill=\"{palette.muted}\">Person {label} field</text>"
    )


def _node(x: float, y: float, body: str, salience: float, palette: SVGPalette) -> str:
    radius = 8 + _clamp(salience, 0.0, 1.4) * 3.2
    label = _body_label(body)
    return (
        f"<circle cx=\"{x:.1f}\" cy=\"{y:.1f}\" r=\"{radius:.1f}\" fill=\"{palette.panel}\" stroke=\"{palette.line}\" stroke-width=\"1.5\"/>"
        f"<text x=\"{x:.1f}\" y=\"{y + radius + 13:.1f}\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"9\" fill=\"{palette.text}\">{_text(label)}</text>"
    )


def _bridge_path(left: tuple[float, float], right: tuple[float, float]) -> str:
    lx, ly = left
    rx, ry = right
    mid_y = (ly + ry) / 2
    return f"M {lx:.1f} {ly:.1f} C {(lx + 120):.1f} {mid_y - 62:.1f}, {(rx - 120):.1f} {mid_y + 62:.1f}, {rx:.1f} {ry:.1f}"


def _metallic_thread_path(
    path: str,
    color: str,
    width_px: str,
    palette: SVGPalette,
    *,
    dash: str = "",
    transform: str = "",
    opacity: str = "0.82",
) -> str:
    transform_attr = f" transform=\"{transform}\"" if transform else ""
    core_width = float(width_px)
    shadow_width = core_width + 0.75
    highlight_width = max(0.35, core_width * 0.32)
    return (
        f"<path d=\"{path}\" fill=\"none\" stroke=\"{palette.line}\" stroke-width=\"{shadow_width:.2f}\" "
        f"stroke-linecap=\"round\" opacity=\"0.16\"{dash}{transform_attr}/>"
        f"<path d=\"{path}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{core_width:.2f}\" "
        f"stroke-linecap=\"round\" opacity=\"{opacity}\"{dash}{transform_attr}/>"
        f"<path d=\"{path}\" fill=\"none\" stroke=\"#fff7df\" stroke-width=\"{highlight_width:.2f}\" "
        f"stroke-linecap=\"round\" opacity=\"0.62\" stroke-dasharray=\"1 10\" stroke-dashoffset=\"2\"{transform_attr}/>"
    )


def _chip_row(labels: list[str], x: int, y: int, max_width: int, palette: SVGPalette) -> str:
    parts = []
    cursor = x
    for label in labels:
        text = _text(label)
        width = min(max_width, max(82, 38 + len(text) * 7))
        parts.append(f"<rect x=\"{cursor}\" y=\"{y}\" width=\"{width}\" height=\"26\" rx=\"13\" fill=\"{palette.chip}\" stroke=\"{palette.border}\"/>")
        parts.append(f"<text x=\"{cursor + width / 2:.1f}\" y=\"{y + 17}\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"10\" fill=\"{palette.text}\">{text[:42]}</text>")
        cursor += width + 8
        if cursor > x + max_width:
            break
    return "".join(parts)


def _overlay_chip_panel(overlays: list[HouseOverlay], data: SynastrySVGData, palette: SVGPalette) -> str:
    parts = [f"<g aria-label=\"House overlay landing zones\"><text x=\"92\" y=\"348\" font-family=\"Arial, sans-serif\" font-size=\"11\" fill=\"{palette.muted}\">Directional house landings</text>"]
    x, y = 92, 362
    for overlay in overlays:
        source = data.person_a_name if overlay.source_person == "A" else data.person_b_name
        owner = data.person_a_name if overlay.house_owner == "A" else data.person_b_name
        label = f"{source}'s {_body_label(overlay.source_body)} -> {owner}'s {overlay.house_topic_label}"
        safe = _text(label)
        width = min(300, max(156, 32 + len(safe) * 5.5))
        if x + width > 828:
            x = 92
            y += 28
        parts.append(f"<rect x=\"{x}\" y=\"{y}\" width=\"{width:.1f}\" height=\"22\" rx=\"11\" fill=\"{palette.panel}\" stroke=\"{palette.border}\"/>")
        parts.append(f"<text x=\"{x + 12}\" y=\"{y + 15}\" font-family=\"Arial, sans-serif\" font-size=\"9\" fill=\"{palette.text}\">{safe[:58]}</text>")
        x += width + 10
    parts.append("</g>")
    return "".join(parts)


def _category_bars(scores: dict[str, float], x: int, y: int, width: int, palette: SVGPalette) -> str:
    items = sorted(scores.items(), key=lambda item: -item[1])[:6]
    if not items:
        return ""
    parts = [f"<g aria-label=\"Category emphasis\"><text x=\"{x}\" y=\"{y - 10}\" font-family=\"Arial, sans-serif\" font-size=\"11\" fill=\"{palette.muted}\">Category emphasis (relative, not a verdict)</text>"]
    bar_w = width / len(items)
    for index, (key, score) in enumerate(items):
        h = 12 + score * 44
        bx = x + index * bar_w + 6
        by = y + 60 - h
        parts.append(f"<rect x=\"{bx:.1f}\" y=\"{by:.1f}\" width=\"{bar_w - 12:.1f}\" height=\"{h:.1f}\" rx=\"5\" fill=\"{palette.chip}\" stroke=\"{palette.border}\"/>")
        parts.append(f"<rect x=\"{bx:.1f}\" y=\"{by + h - max(4, h * .55):.1f}\" width=\"{bar_w - 12:.1f}\" height=\"{max(4, h * .55):.1f}\" rx=\"5\" fill=\"{palette.ease}\" opacity=\"0.55\"/>")
        parts.append(f"<text x=\"{bx + (bar_w - 12) / 2:.1f}\" y=\"{y + 76}\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"8\" fill=\"{palette.text}\">{_text(CATEGORY_LABELS.get(key, key))[:16]}</text>")
    parts.append("</g>")
    return "".join(parts)


def _legend(x: int, y: int, palette: SVGPalette, *, full: bool = False) -> str:
    rows = [
        ("solid curve", palette.ease, "", "ease / flow"),
        ("dashed curve", palette.tension, " stroke-dasharray=\"8 6\"", "friction / growth edge"),
        ("double curve", palette.activation, "", "activation / repeated emphasis"),
    ]
    parts = [f"<g aria-label=\"Visual key\"><text x=\"{x}\" y=\"{y}\" font-family=\"Arial, sans-serif\" font-size=\"11\" fill=\"{palette.muted}\">Visual key</text>"]
    yy = y + 18
    for _, color, dash, label in rows:
        parts.append(_metallic_thread_path(f"M {x} {yy} C {x + 24} {yy - 10}, {x + 54} {yy + 10}, {x + 78} {yy}", color, "1.7", palette, dash=dash))
        if "double" in label:
            parts.append(_metallic_thread_path(f"M {x} {yy + 6} C {x + 24} {yy - 4}, {x + 54} {yy + 16}, {x + 78} {yy + 6}", color, "0.8", palette, opacity="0.55"))
        parts.append(f"<text x=\"{x + 92}\" y=\"{yy + 4}\" font-family=\"Arial, sans-serif\" font-size=\"10\" fill=\"{palette.text}\">{_text(label)}</text>")
        yy += 24
    if full:
        parts.append(f"<text x=\"{x}\" y=\"{yy + 14}\" font-family=\"Arial, sans-serif\" font-size=\"10\" fill=\"{palette.muted}\">Line weight and node size show relative evidence emphasis only.</text>")
    parts.append("</g>")
    return "".join(parts)


def _landing_side(x: int, y: int, w: int, h: int, route: str, source: str, target: str, data: SynastrySVGData, palette: SVGPalette) -> str:
    source_label, target_label = ("A", "B") if route == "A_to_B" else ("B", "A")
    overlays = [item for item in data.house_overlays if item.source_person == source_label and item.house_owner == target_label][:5]
    parts = [f"<g><rect x=\"{x}\" y=\"{y}\" width=\"{w}\" height=\"{h}\" rx=\"14\" fill=\"{palette.panel}\" stroke=\"{palette.border}\"/>"]
    parts.append(f"<text x=\"{x + 20}\" y=\"{y + 28}\" font-family=\"Georgia, serif\" font-size=\"16\" fill=\"{palette.text}\">{_text(source)} lands for {_text(target)}</text>")
    cx, cy = x + w / 2, y + 116
    parts.append(f"<circle cx=\"{cx:.1f}\" cy=\"{cy:.1f}\" r=\"66\" fill=\"none\" stroke=\"{palette.border}\"/>")
    if not overlays:
        parts.append(f"<text x=\"{cx:.1f}\" y=\"{cy:.1f}\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"11\" fill=\"{palette.muted}\">No live house overlays</text>")
    for index, overlay in enumerate(overlays):
        angle = -pi / 2 + index * (2 * pi / max(5, len(overlays)))
        px = cx + 74 * cos(angle)
        py = cy + 54 * sin(angle)
        parts.append(f"<line x1=\"{cx:.1f}\" y1=\"{cy:.1f}\" x2=\"{px:.1f}\" y2=\"{py:.1f}\" stroke=\"{palette.activation}\" stroke-width=\"{1.5 + _numeric(overlay.salience, .3) * 2:.1f}\" opacity=\"0.7\"/>")
        parts.append(f"<circle cx=\"{px:.1f}\" cy=\"{py:.1f}\" r=\"16\" fill=\"{palette.chip}\" stroke=\"{palette.line}\"/>")
        parts.append(f"<text x=\"{px:.1f}\" y=\"{py + 4:.1f}\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"9\" fill=\"{palette.text}\">{_text(str(overlay.house_number))}</text>")
    y2 = y + 190
    for overlay in overlays[:3]:
        label = f"{_body_label(overlay.source_body)} -> {overlay.house_topic_label}"
        parts.append(f"<text x=\"{x + 22}\" y=\"{y2}\" font-family=\"Arial, sans-serif\" font-size=\"10\" fill=\"{palette.text}\">{_text(label)}</text>")
        y2 += 18
    parts.append("</g>")
    return "".join(parts)


def _svg_start(width: int, height: int, title: str, desc: str, palette: SVGPalette, *, css_class: str = "synastry-svg") -> list[str]:
    return [
        f"<svg class=\"{css_class}\" xmlns=\"http://www.w3.org/2000/svg\" role=\"img\" viewBox=\"0 0 {width} {height}\" width=\"100%\" height=\"auto\">",
        f"<title>{_text(title)}</title>",
        f"<desc>{_text(desc)}</desc>",
    ]


def _defs() -> str:
    return (
        "<defs>"
        "<filter id=\"softShadow\" x=\"-20%\" y=\"-20%\" width=\"140%\" height=\"140%\">"
        "<feDropShadow dx=\"0\" dy=\"8\" stdDeviation=\"10\" flood-color=\"#102238\" flood-opacity=\"0.10\"/>"
        "</filter>"
        "</defs>"
    )


def _knot(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    width = 1.5 + score * 2.4
    return (
        f"<path d=\"M {cx-52} {cy} C {cx-22} {cy-44}, {cx+22} {cy+44}, {cx+52} {cy} C {cx+22} {cy-44}, {cx-22} {cy+44}, {cx-52} {cy}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{width:.1f}\"/>"
        f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"7\" fill=\"{palette.panel}\" stroke=\"{palette.line}\"/>"
    )


def _ripples(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return "".join(f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"{18 + i * 13}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1 + score * 1.2:.1f}\" opacity=\"{0.8 - i * .16:.2f}\"/>" for i in range(4))


def _signal(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<path d=\"M {cx-58} {cy+22} L {cx-28} {cy-10} L {cx} {cy+12} L {cx+28} {cy-20} L {cx+58} {cy+8}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1.6 + score * 2:.1f}\" stroke-linejoin=\"round\"/>"
        f"<circle cx=\"{cx-28}\" cy=\"{cy-10}\" r=\"5\" fill=\"{palette.panel}\" stroke=\"{color}\"/><circle cx=\"{cx+28}\" cy=\"{cy-20}\" r=\"5\" fill=\"{palette.panel}\" stroke=\"{color}\"/>"
    )


def _compass(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"34\" fill=\"none\" stroke=\"{palette.border}\"/>"
        f"<path d=\"M {cx} {cy-42} L {cx+14} {cy+8} L {cx} {cy+2} L {cx-14} {cy+8} Z\" fill=\"{color}\" opacity=\"0.78\"/>"
        f"<line x1=\"{cx-48}\" y1=\"{cy}\" x2=\"{cx+48}\" y2=\"{cy}\" stroke=\"{palette.border}\"/>"
    )


def _rings(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<ellipse cx=\"{cx}\" cy=\"{cy}\" rx=\"54\" ry=\"25\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1.4 + score * 2:.1f}\"/>"
        f"<ellipse cx=\"{cx}\" cy=\"{cy}\" rx=\"34\" ry=\"48\" fill=\"none\" stroke=\"{palette.line}\" stroke-width=\"1\" opacity=\"0.5\"/>"
        f"<rect x=\"{cx-18}\" y=\"{cy-18}\" width=\"36\" height=\"36\" rx=\"4\" fill=\"none\" stroke=\"{palette.border}\"/>"
    )


def _vault(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<path d=\"M {cx-42} {cy+26} L {cx-42} {cy-6} C {cx-42} {cy-44}, {cx+42} {cy-44}, {cx+42} {cy-6} L {cx+42} {cy+26} Z\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1.8 + score * 2:.1f}\"/>"
        f"<circle cx=\"{cx}\" cy=\"{cy+2}\" r=\"10\" fill=\"none\" stroke=\"{palette.line}\"/>"
    )


def _magnetism(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<path d=\"M {cx-48} {cy-18} C {cx-58} {cy+38}, {cx-8} {cy+38}, {cx-8} {cy-2}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{2 + score * 2:.1f}\"/>"
        f"<path d=\"M {cx+48} {cy-18} C {cx+58} {cy+38}, {cx+8} {cy+38}, {cx+8} {cy-2}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{2 + score * 2:.1f}\"/>"
        f"<line x1=\"{cx-18}\" y1=\"{cy-24}\" x2=\"{cx+18}\" y2=\"{cy-24}\" stroke=\"{palette.border}\"/>"
    )


def _ground(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<path d=\"M {cx-56} {cy+28} C {cx-22} {cy+4}, {cx+22} {cy+4}, {cx+56} {cy+28}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1.6 + score * 2:.1f}\"/>"
        f"<path d=\"M {cx} {cy+28} L {cx} {cy-34} M {cx} {cy-6} L {cx-24} {cy-24} M {cx} {cy+2} L {cx+24} {cy-18}\" stroke=\"{palette.line}\" fill=\"none\"/>"
    )


def _spark(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    points = []
    for i in range(10):
        r = 46 if i % 2 == 0 else 18
        angle = -pi / 2 + i * pi / 5
        points.append(f"{cx + r * cos(angle):.1f},{cy + r * sin(angle):.1f}")
    return f"<polygon points=\"{' '.join(points)}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1.3 + score * 1.8:.1f}\"/>"


def _mirrored(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<circle cx=\"{cx-32}\" cy=\"{cy}\" r=\"25\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1.5 + score * 1.7:.1f}\"/>"
        f"<circle cx=\"{cx+32}\" cy=\"{cy}\" r=\"25\" fill=\"none\" stroke=\"{color}\" stroke-width=\"{1.5 + score * 1.7:.1f}\"/>"
        f"<path d=\"M {cx-8} {cy} C {cx-1} {cy-18}, {cx+1} {cy+18}, {cx+8} {cy}\" fill=\"none\" stroke=\"{palette.line}\"/>"
    )


def _echo(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return "".join(f"<path d=\"M {cx-52+i*18} {cy+28} C {cx-36+i*18} {cy-28}, {cx-8+i*18} {cy-28}, {cx+8+i*18} {cy+28}\" fill=\"none\" stroke=\"{color if i % 2 == 0 else palette.line}\" stroke-width=\"{1.1 + score:.1f}\" opacity=\"0.75\"/>" for i in range(5))


def _composite_mark(cx: int, cy: int, color: str, palette: SVGPalette, score: float, data: SynastrySVGData, *, large: bool = False) -> str:
    r = 52 if large else 34
    composite = data.composite if isinstance(data.composite, CompositeSummary) else CompositeSummary()
    spokes = len([v for v in (composite.sun_sign, composite.moon_sign, composite.mercury_sign, composite.venus_sign, composite.mars_sign, composite.saturn_sign) if v]) or 4
    parts = [f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"{r}\" fill=\"none\" stroke=\"{palette.border}\"/>"]
    for i in range(spokes):
        angle = -pi / 2 + i * (2 * pi / spokes)
        parts.append(f"<line x1=\"{cx}\" y1=\"{cy}\" x2=\"{cx + r * cos(angle):.1f}\" y2=\"{cy + r * sin(angle):.1f}\" stroke=\"{color}\" stroke-width=\"{1.2 + score:.1f}\" opacity=\"0.72\"/>")
    parts.append(f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"{r * .42:.1f}\" fill=\"{palette.chip}\" stroke=\"{palette.line}\"/>")
    return "".join(parts)


def _tension(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        f"<path d=\"M {cx-52} {cy-28} L {cx+52} {cy+28} M {cx-52} {cy+28} L {cx+52} {cy-28}\" stroke=\"{color}\" stroke-width=\"{1.4 + score * 2:.1f}\" stroke-linecap=\"round\"/>"
        f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"24\" fill=\"none\" stroke=\"{palette.border}\" stroke-dasharray=\"5 6\"/>"
    )


def _integrated(cx: int, cy: int, color: str, palette: SVGPalette, score: float) -> str:
    return (
        _ripples(cx, cy, color, palette, score)
        + f"<path d=\"M {cx-48} {cy} C {cx-12} {cy-38}, {cx+12} {cy+38}, {cx+48} {cy}\" fill=\"none\" stroke=\"{palette.line}\" stroke-width=\"1.5\"/>"
    )


def _field_desc(data: SynastrySVGData) -> str:
    return f"Relationship field map for {data.person_a_name} and {data.person_b_name}, showing selected cross-chart contacts, directional house landings, and relative category emphasis."


def _directional_desc(data: SynastrySVGData) -> str:
    return f"Directional landing map showing how {data.person_a_name} lands in {data.person_b_name}'s house field and how {data.person_b_name} lands in {data.person_a_name}'s house field."


def _composite_desc(data: SynastrySVGData) -> str:
    composite = data.composite if isinstance(data.composite, CompositeSummary) else CompositeSummary()
    return f"Compact midpoint composite field symbol. Dominant register: {composite.dominant_register or 'not available'}; emotional register: {composite.emotional_register or 'not available'}."


def _tone_for_aspect(aspect: Any, bodies: set[str]) -> str:
    value = str(aspect or "").lower()
    if value in {"trine", "sextile"}:
        return "ease"
    if value in {"square", "opposition", "quincunx"}:
        return "tension"
    if value == "conjunction" or bodies & {"Mars", "Ascendant", "Descendant", "Midheaven", "Imum_Coeli", "North_Node", "South_Node"}:
        return "activation"
    return "mixed"


def _normalize_tone(tone: str) -> str:
    value = str(tone or "").strip().lower()
    if value in {"ease", "flow", "harmony", "supportive"}:
        return "ease"
    if value in {"tension", "friction", "growth", "tensional"}:
        return "tension"
    if value in {"activation", "active", "mixed"}:
        return "activation" if value != "mixed" else "mixed"
    return "mixed"


def _tone_color(tone: str, palette: SVGPalette) -> str:
    return {
        "ease": palette.ease,
        "activation": palette.activation,
        "tension": palette.tension,
        "mixed": palette.mixed,
    }.get(_normalize_tone(tone), palette.mixed)


def _stroke_width(salience: float | None, score: float | None) -> str:
    value = _clamp(_numeric(salience, _numeric(score, 0.35)), 0.0, 1.4)
    return f"{0.75 + value * 0.92:.2f}"


def _is_repeated_theme(aspect: SynastryAspect, aspects: list[SynastryAspect]) -> bool:
    bodies = {aspect.source_body, aspect.target_body}
    return sum(1 for item in aspects if bodies & {item.source_body, item.target_body}) >= 3


def _category_for_bodies(bodies: set[str], aspect: Any = None) -> str:
    if bodies & {"Moon"}:
        return "emotional_climate"
    if bodies & {"Mercury"}:
        return "communication_exchange"
    if bodies & {"Venus", "Mars", "Ascendant", "Descendant"}:
        return "attraction_encounter"
    if bodies & {"Pluto"}:
        return "depth_shared_stakes"
    if bodies & {"Saturn"}:
        return "care_responsibility"
    if bodies & {"Jupiter"}:
        return "growth_meaning"
    if str(aspect or "") in {"Square", "Opposition", "Quincunx"}:
        return "friction_growth"
    return "composite_field"


def _category_for_overlay(source_body: str, house: int) -> str:
    if source_body == "Moon" or house == 4:
        return "emotional_climate" if source_body == "Moon" else "private_ground"
    if source_body == "Mercury" or house == 3:
        return "communication_exchange"
    if source_body in {"Venus", "Mars", "Sun"} or house in {1, 5, 7, 10}:
        return "attraction_encounter" if house != 5 else "play_romance"
    if house == 8 or source_body == "Pluto":
        return "depth_shared_stakes"
    if source_body == "Saturn" or house == 6:
        return "care_responsibility"
    if source_body == "Jupiter" or house == 9:
        return "growth_meaning"
    if house == 12:
        return "private_ground"
    return "composite_field"


def _sections_for_category(category: str) -> list[str]:
    mapping = {
        "emotional_climate": ["emotional_rhythm_attachment"],
        "communication_exchange": ["communication_daily_exchange"],
        "attraction_encounter": ["attraction_visibility_encounter"],
        "depth_shared_stakes": ["depth_intimacy_shared_stakes"],
        "private_ground": ["home_body_private_terrain"],
        "play_romance": ["play_romance_idealization"],
        "care_responsibility": ["care_routine_responsibility"],
        "growth_meaning": ["growth_meaning_worldview"],
        "friction_growth": ["friction_growth_edges"],
        "composite_field": ["composite_relationship_field"],
    }
    return mapping.get(category, [])


def _overlay_salience(source_body: str, house: int) -> float:
    body_weight = {
        "Sun": 0.95,
        "Moon": 0.95,
        "Mercury": 0.82,
        "Venus": 0.86,
        "Mars": 0.86,
        "Jupiter": 0.76,
        "Saturn": 0.76,
        "Pluto": 0.68,
        "Neptune": 0.64,
        "Uranus": 0.64,
    }.get(source_body, 0.55)
    house_weight = {1: 0.94, 4: 0.92, 5: 0.78, 7: 0.95, 8: 0.9, 10: 0.82, 3: 0.78, 9: 0.74, 6: 0.68}.get(house, 0.54)
    return round(_clamp((body_weight + house_weight) / 2, 0.0, 1.0), 4)


def _dominant_section_tone(section_key: str, data: SynastrySVGData) -> str:
    if section_key == "friction_growth_edges":
        return "tension"
    category = SECTION_CATEGORY_HINTS.get(section_key)
    tones = [aspect.tone for aspect in data.aspects if aspect.category == category]
    if "tension" in tones:
        return "tension"
    if "activation" in tones:
        return "activation"
    if "ease" in tones:
        return "ease"
    return "mixed"


def _body_label(body: str) -> str:
    return str(body or "").replace("_", " ")


def _text(value: Any) -> str:
    return escape(str(value or ""), quote=True)


def _optional_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _numeric(value: Any, fallback: float) -> float:
    return float(value) if isinstance(value, (int, float)) else fallback


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _sanitize_svg_output(svg: str) -> str:
    lower = svg.lower()
    for term in FORBIDDEN_CONSUMER_TERMS:
        if term in lower:
            raise ValueError(f"Synastry SVG contains forbidden consumer-facing term: {term}")
    return svg
