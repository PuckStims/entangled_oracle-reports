"""
HTML rendering for Place Resonance Search.

The legacy single-destination wrapper still delegates to the Place Profile
renderer. The multi-location Search renderer below consumes the new candidate
search context directly.
"""
from __future__ import annotations

import html
import uuid
from datetime import datetime
from typing import Any

import products.location_services.place_resonance_renderer as _root_renderer

from products.location_services.place_resonance_search.assembler import (
    assemble_place_resonance_search_results_context,
    build_place_resonance_search_context,
)


RENDER_VERSION = "place_resonance_search_render_v0.2.0"
OUTPUT_DIR = _root_renderer.OUTPUT_DIR


def _escape(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=False)


def _is_draft_leaf(leaf: dict | None) -> bool:
    return isinstance(leaf, dict) and str(leaf.get("body") or "").strip() == "TODO"


def _render_leaf(leaf: dict | None, fallback_prompt: str, context_vars: dict | None = None) -> str:
    if not isinstance(leaf, dict):
        return ""
    if _is_draft_leaf(leaf):
        prompt = _escape(leaf.get("_note") or fallback_prompt)
        evidence = ", ".join(str(item) for item in leaf.get("requires_evidence", []) or [])
        return (
            '<div class="search-draft">'
            '<div class="draft-label">Draft Slot</div>'
            f'<p>{prompt}</p>'
            f'<small>Requires: {_escape(evidence)}</small>'
            '</div>'
        )
    body = str(leaf.get("body") or "")
    if context_vars:
        for k, v in context_vars.items():
            if v is not None:
                body = body.replace(f"{{{k}}}", str(v))
    body = _escape(body).replace("\n", "<br>")
    return f'<div class="search-prose">{body}</div>'


def _format_theme(theme: str) -> str:
    return str(theme or "").replace("_", " ").title()


def _score_bar(label: str, value: int) -> str:
    width = max(0, min(100, int(value or 0)))
    return (
        '<div class="score-row">'
        f'<span>{_escape(label)}</span>'
        '<div class="score-track">'
        f'<div class="score-fill" style="width:{width}%"></div>'
        '</div>'
        f'<strong>{width}</strong>'
        '</div>'
    )


def _format_population_tier(value: str | None) -> str:
    return str(value or "").replace("_", " ")


def _location_texture_sentence(location: dict) -> str:
    candidate = location.get("candidate") or {}
    traits = location.get("prose_variation_traits") or {}
    population = _format_population_tier(candidate.get("population_tier"))
    region = str(candidate.get("region") or "").strip()
    texture_tags = _candidate_texture_tags(candidate, limit=3)
    primary_family = str(traits.get("primary_family") or "signal").replace("_", " ")

    context_bits = []
    if population:
        context_bits.append(f"a {population} candidate")
    if region:
        context_bits.append(f"within {region}")
    if texture_tags:
        context_bits.append(f"tagged for {', '.join(texture_tags)}")
    if not context_bits:
        return ""

    setting = " ".join(context_bits)
    texture_lookup = {tag.lower() for tag in texture_tags}
    if population in {"major metro", "large metro"}:
        expression = "with the signal likely to express through scale, density, and public circulation"
    elif population == "small town":
        expression = "with the signal likely to feel more concentrated, local, and harder to diffuse"
    elif any(tag in {"ocean coast", "gulf coast", "great lakes", "island", "coastal"} for tag in texture_lookup):
        expression = "with the signal filtered through a more edge-facing or maritime setting"
    elif any("river" in tag for tag in texture_lookup):
        expression = "with the signal shaped by movement, passage, and local continuity"
    else:
        expression = "with the catalog context giving this pattern a more specific place texture"

    return f"Place texture: {setting}, emphasizing the {primary_family} expression {expression}."


def _candidate_texture_tags(candidate: dict[str, Any], limit: int = 4) -> list[str]:
    tags: list[str] = []
    for field in ("place_archetypes", "collections", "climate_sensory_tags", "interpretive_use_cases", "notes"):
        for value in candidate.get(field) or []:
            text = str(value).replace("_", " ").strip()
            if text and text not in tags:
                tags.append(text)
            if len(tags) >= limit:
                return tags
    return tags


def _render_bucket_sections(context: dict) -> str:
    selected = context.get("selected_locations") or []
    bucket_leaves = context.get("bucket_leaves") or {}
    parts: list[str] = []
    seen_buckets = []
    for location in selected:
        bucket = location.get("bucket")
        if bucket and bucket not in seen_buckets:
            seen_buckets.append(bucket)

    for bucket in seen_buckets:
        locations = [item for item in selected if item.get("bucket") == bucket]
        label = locations[0].get("bucket_label") if locations else bucket
        
        context_vars = {
            "bucket": label,
            "count": len(locations)
        }
        
        parts.append('<section class="report-band">')
        parts.append(f'<div class="eyebrow">Bucket</div><h2>{_escape(label)}</h2>')
        parts.append(_render_leaf(bucket_leaves.get(bucket), "Write this bucket introduction.", context_vars))
        parts.append('<div class="location-grid">')
        for location in locations:
            parts.append(_render_location_card(context, location))
        parts.append('</div></section>')
    return "".join(parts)


def _render_location_card(context: dict, location: dict) -> str:
    scores = location.get("scores") or {}
    themes = location.get("dominant_themes") or []
    rec_leaf = (context.get("recommendation_leaves") or {}).get(location.get("location_id"))
    tile_leaves = (context.get("tile_detail_leaves") or {}).get(location.get("location_id")) or {}
    evidence_refs = location.get("evidence_refs") or []
    alternates = location.get("cluster_alternates") or []
    score_labels = [
        ("Overall", scores.get("overall_resonance", 0)),
        ("Consensus", scores.get("consensus_score", 0)),
        ("Complexity", scores.get("complexity_index", 0)),
        ("Grounding", scores.get("grounding_score", 0)),
        ("Divergence", scores.get("baseline_divergence", 0)),
    ]
    theme_text = ", ".join(_format_theme(theme) for theme in themes) or "Unclassified"
    evidence_text = ", ".join(str(ref) for ref in evidence_refs[:4]) or "No refs"
    
    context_vars = {
        "city_name": location.get("display_name", ""),
        "bucket": location.get("bucket_label") or location.get("bucket", ""),
        "evidence_refs": evidence_text,
        "primary_score": scores.get("overall_resonance", 0),
        "dominant_theme": _format_theme(themes[0] if themes else "Unknown"),
    }

    parts = [
        '<article class="location-card">',
        f'<div class="rank">#{_escape(location.get("selection_rank"))}</div>',
        f'<h3>{_escape(location.get("display_name"))}</h3>',
        f'<div class="recommendation">{_escape(location.get("recommendation_label"))}</div>',
        f'<p class="themes">{_escape(theme_text)}</p>',
        _render_leaf(rec_leaf, "Write this recommendation label explanation.", context_vars),
        _render_leaf(tile_leaves.get("bucket_role"), "Write this city-specific bucket role.", context_vars),
        _render_leaf(tile_leaves.get("best_use_case"), "Write this city's best use case.", context_vars),
        f'<p class="place-texture">{_escape(_location_texture_sentence(location))}</p>',
        _render_leaf(tile_leaves.get("sibling_difference"), "Write the sibling difference explanation.", context_vars) if location.get("sibling_difference") else "",
        f'<p class="place-texture">{_escape(location.get("sibling_difference"))}</p>' if location.get("sibling_difference") else "",
        '<div class="score-list">',
    ]
    for label, value in score_labels:
        parts.append(_score_bar(label, int(value or 0)))
    parts.extend([
        '</div>',
        _render_cluster_alternates(alternates, tile_leaves.get("cluster_alternates"), context_vars),
        f'<details><summary>Evidence refs</summary><p>{_escape(evidence_text)}</p></details>',
        '</article>',
    ])
    return "".join(parts)


def _render_cluster_alternates(
    alternates: list[dict],
    leaf: dict | None,
    context_vars: dict | None = None,
) -> str:
    if not alternates:
        return ""
    items = []
    for alternate in alternates[:4]:
        themes = ", ".join(_format_theme(theme) for theme in alternate.get("dominant_themes", [])[:2])
        distance = alternate.get("distance_from_representative_miles")
        distance_text = f" · {distance} mi" if distance is not None else ""
        items.append(
            "<li>"
            f"<strong>{_escape(alternate.get('display_name'))}</strong>{_escape(distance_text)}"
            f"<span>{_escape(themes)}</span>"
            f"<small>{_escape(alternate.get('sibling_difference'))}</small>"
            "</li>"
        )
    return (
        '<div class="cluster-alternates">'
        '<div class="eyebrow">Nearby Similar Alternates</div>'
        f'{_render_leaf(leaf, "Write the clustered alternate explanation.", context_vars)}'
        f'<ul>{"".join(items)}</ul>'
        '</div>'
    )


def render_place_resonance_search_results_html(search_context: dict) -> str:
    selected = search_context.get("selected_locations") or []
    candidate_pool = search_context.get("candidate_pool") or {}
    selected_leaves = search_context.get("selected_leaves") or {}
    distribution = search_context.get("bucket_distribution") or {}
    generated = datetime.now().strftime("%B %d, %Y")

    context_vars = {
        "candidate_count": candidate_pool.get("evaluated_count"),
        "dominant_theme": _format_theme(search_context.get("dominant_search_theme")),
    }
    
    html_parts = [
        '<!DOCTYPE html><html><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'<title>{_escape(search_context.get("product_name") or "Place Resonance Search")}</title>',
        '<style>',
        _root_renderer._load_shared_report_css(),
        """
        :root {
          --search-bg: #f4efe6;
          --search-ink: #20211d;
          --search-muted: #68665f;
          --search-line: #c8c0b2;
          --search-panel: #fffaf1;
          --search-panel-2: #ebe2d2;
          --search-accent: #2f6f73;
          --search-warm: #9c6437;
        }
        body.search-shell { margin: 0; color: var(--search-ink); background: linear-gradient(180deg, #f7f2e9 0%, #e8ddce 100%); font-family: Georgia, "Times New Roman", serif; }
        .search-wrap { max-width: 1120px; margin: 0 auto; padding: 40px 24px 64px; }
        .hero { padding: 36px 0 24px; border-bottom: 1px solid var(--search-line); }
        .hero h1 { font-size: 3rem; line-height: 1.02; margin: 8px 0 12px; letter-spacing: 0; }
        .hero p { max-width: 760px; color: var(--search-muted); font-size: 1.05rem; }
        .eyebrow, .draft-label { color: var(--search-accent); font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; font-family: Verdana, sans-serif; font-weight: 700; }
        .summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 24px 0; }
        .metric, .search-draft, .location-card, .synthesis-panel { background: var(--search-panel); border: 1px solid var(--search-line); border-radius: 8px; padding: 16px; }
        .metric strong { display: block; font-size: 1.8rem; }
        .report-band { padding: 28px 0; border-bottom: 1px solid var(--search-line); }
        .report-band h2 { font-size: 1.8rem; margin: 4px 0 12px; }
        .location-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 18px; }
        .location-card { position: relative; }
        .location-card h3 { margin: 0 48px 8px 0; font-size: 1.35rem; }
        .rank { position: absolute; top: 14px; right: 14px; color: var(--search-warm); font-family: Verdana, sans-serif; font-weight: 700; }
        .recommendation { display: inline-block; color: var(--search-accent); font-family: Verdana, sans-serif; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
        .themes { color: var(--search-muted); margin: 0 0 12px; }
        .place-texture { color: var(--search-muted); border-left: 3px solid var(--search-line); margin: 12px 0 0; padding-left: 10px; font-size: 0.92rem; }
        .cluster-alternates { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--search-line); }
        .cluster-alternates ul { list-style: none; padding: 0; margin: 8px 0 0; display: grid; gap: 8px; }
        .cluster-alternates li { display: grid; gap: 3px; color: var(--search-muted); font-size: 0.88rem; }
        .cluster-alternates li strong { color: var(--search-ink); }
        .cluster-alternates li span, .cluster-alternates li small { display: block; }
        .search-draft { background: #fbf5ea; border-style: dashed; margin: 12px 0; }
        .search-draft p { margin: 6px 0; }
        .search-draft small { color: var(--search-muted); }
        .score-list { display: grid; gap: 8px; margin-top: 14px; }
        .score-row { display: grid; grid-template-columns: 88px 1fr 36px; align-items: center; gap: 8px; font-family: Verdana, sans-serif; font-size: 0.78rem; }
        .score-track { height: 8px; background: var(--search-panel-2); border-radius: 999px; overflow: hidden; }
        .score-fill { height: 100%; background: linear-gradient(90deg, var(--search-accent), var(--search-warm)); }
        details { margin-top: 12px; color: var(--search-muted); font-size: 0.88rem; }
        footer { color: var(--search-muted); padding-top: 28px; font-size: 0.86rem; }
        @media (max-width: 760px) {
          .search-wrap { padding: 28px 16px 48px; }
          .hero h1 { font-size: 2.2rem; }
          .summary-grid, .location-grid { grid-template-columns: 1fr; }
        }
        """,
        '</style></head><body class="search-shell"><main class="search-wrap">',
        '<header class="hero">',
        '<div class="eyebrow">Location Services</div>',
        f'<h1>{_escape(search_context.get("product_name") or "Place Resonance Search")}</h1>',
        '<p>Curated symbolic search across a candidate location pool. Scores are relative indexes within this evaluated pool, not universal measurements.</p>',
        '</header>',
        '<section class="summary-grid">',
        f'<div class="metric"><span>Evaluated</span><strong>{_escape(candidate_pool.get("evaluated_count"))}</strong></div>',
        f'<div class="metric"><span>Selected</span><strong>{len(selected)}</strong></div>',
        f'<div class="metric"><span>Dominant</span><strong>{_escape(_format_theme(search_context.get("dominant_search_theme")))}</strong></div>',
        f'<div class="metric"><span>Mode</span><strong>{_escape(search_context.get("search_mode"))}</strong></div>',
        '</section>',
        '<section class="report-band">',
        '<div class="eyebrow">Search Summary</div>',
        _render_leaf(selected_leaves.get("search_summary"), "Write the search summary.", context_vars),
        '<div class="synthesis-panel">',
        '<div class="eyebrow">Pattern Synthesis</div>',
        _render_leaf(selected_leaves.get("pattern_synthesis"), "Write the pattern synthesis.", context_vars),
        '</div>',
        '</section>',
        '<section class="report-band"><div class="eyebrow">Bucket Distribution</div><p class="themes">Score bars are calibrated against the evaluated candidate pool for this run.</p><div class="summary-grid">',
    ]

    for bucket, count in distribution.items():
        if count:
            html_parts.append(f'<div class="metric"><span>{_escape(_format_theme(bucket))}</span><strong>{count}</strong></div>')
    html_parts.extend(['</div></section>', _render_bucket_sections(search_context)])
    html_parts.append(f'<footer>Entangled Oracle - Ksisti-Puck LLC - Generated {generated}</footer>')
    html_parts.append('</main></body></html>')
    return "".join(html_parts)


def render_place_resonance_search_html(place_context: dict) -> str:
    if isinstance(place_context, dict) and "selected_locations" in place_context:
        return render_place_resonance_search_results_html(place_context)
    return _root_renderer.render_place_resonance_html(place_context)


def build_place_resonance_search_html(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> str:
    context = build_place_resonance_search_context(
        natal_payload,
        destination,
        purpose_lens=purpose_lens,
        relationship_to_place=relationship_to_place,
    )
    return render_place_resonance_search_html(context)


def build_place_resonance_search_results_html(
    natal_payload: dict,
    candidates: list[dict] | None = None,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
    selection_limit: int = 20,
) -> str:
    context = assemble_place_resonance_search_results_context(
        natal_payload,
        candidates,
        purpose_lens=purpose_lens,
        relationship_to_place=relationship_to_place,
        selection_limit=selection_limit,
    )
    return render_place_resonance_search_results_html(context)


def write_place_resonance_search_html(html_content: str, output_filename: str | None = None) -> str:
    previous_output_dir = _root_renderer.OUTPUT_DIR
    _root_renderer.OUTPUT_DIR = OUTPUT_DIR
    try:
        if output_filename is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"place_resonance_search_{stamp}_{uuid.uuid4().hex[:8]}.html"
        return _root_renderer.write_place_resonance_html(html_content, output_filename)
    finally:
        _root_renderer.OUTPUT_DIR = previous_output_dir
