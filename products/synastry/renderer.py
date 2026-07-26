"""
HTML rendering for the synastry round-1 preview context.
"""
from __future__ import annotations

import copy
import html
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR, PALETTES, TEMPLATES_DIR
from products.synastry.assembler import build_synastry_context
from visuals.synastry_svg import (
    normalize_synastry_for_svg,
    render_composite_field_sigIl,
    render_directional_landing_map,
    render_relationship_field_map,
    render_section_glyph,
    render_visual_legend,
)


RENDER_VERSION = "synastry_render_v0.1.0"
_SHARED_REPORT_CSS_PATH = os.path.join(TEMPLATES_DIR, "shared", "report_visual_system.css")


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _load_shared_report_css() -> str:
    try:
        with open(_SHARED_REPORT_CSS_PATH, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def _build_render_defaults(context: dict | None = None) -> dict:
    current = context or {}
    generation_date = current.get("generation_date", "")
    footer = "Entangled Oracle - Ksisti-Puck LLC"
    if generation_date:
        footer = f"{footer} - Generated {generation_date}"
    return {
        "shared_report_css": _load_shared_report_css(),
        "report_brand_line": "Entangled Oracle - Ksisti-Puck LLC",
        "report_footer_text": footer,
    }


def _resolve_palette_name(synastry_context: dict) -> str:
    relationship_meta = synastry_context.get("relationship_meta") or {}
    palette_name = relationship_meta.get("palette")
    if isinstance(palette_name, str) and palette_name in PALETTES:
        return palette_name
    return "vibrant"


def _prepare_context(synastry_context: dict) -> dict:
    palette_name = _resolve_palette_name(synastry_context)
    render_context = {
        "render_version": RENDER_VERSION,
        "report_title": synastry_context.get("product_name", "Synastry Round 1 Preview"),
        "report_subtitle": "Preview sample",
        "generation_date": datetime.now().strftime("%B %d, %Y"),
        "person_a_name": synastry_context.get("person_a_name"),
        "person_b_name": synastry_context.get("person_b_name"),
        "person_a_birth_time_state": synastry_context.get("person_a_birth_time_state"),
        "person_b_birth_time_state": synastry_context.get("person_b_birth_time_state"),
        "palette_name": palette_name,
        "palette": _deepcopy(PALETTES.get(palette_name, PALETTES["vibrant"])),
        "relationship_meta": _deepcopy(synastry_context.get("relationship_meta") or {}),
        "claim_safety": _deepcopy(synastry_context.get("claim_safety") or {}),
        "withheld_summary": _deepcopy(synastry_context.get("withheld_summary") or {}),
        "sections": _deepcopy(synastry_context.get("sections") or []),
        "section_order": list(synastry_context.get("section_order") or []),
        "visuals": _build_visuals(synastry_context) if _visuals_enabled(synastry_context) else {},
    }
    render_context.update(_build_render_defaults(render_context))
    return render_context


def _visuals_enabled(synastry_context: dict) -> bool:
    relationship_meta = synastry_context.get("relationship_meta") or {}
    return bool(relationship_meta.get("enable_synastry_visuals"))


def _build_visuals(synastry_context: dict) -> dict:
    try:
        svg_data = normalize_synastry_for_svg(synastry_context)
        section_order = list(synastry_context.get("section_order") or [])
        return {
            "relationship_field_map": render_relationship_field_map(svg_data),
            "directional_landing_map": render_directional_landing_map(svg_data),
            "composite_field_sigil": render_composite_field_sigIl(svg_data),
            "visual_legend": render_visual_legend(),
            "section_glyphs": {
                section_key: render_section_glyph(section_key, svg_data)
                for section_key in section_order
            },
        }
    except (TypeError, ValueError, AttributeError, KeyError):
        return {
            "relationship_field_map": "",
            "directional_landing_map": "",
            "composite_field_sigil": "",
            "visual_legend": "",
            "section_glyphs": {},
        }


def _esc(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return html.escape(str(value), quote=True)


def _birth_time_state_label(value: Any) -> str:
    labels = {
        "exact_birth_time": "Exact birth time",
        "approximate_birth_time": "Approximate birth time",
        "unknown_birth_time": "Birth time unknown",
    }
    return labels.get(str(value or ""), str(value or "").replace("_", " ").title())


def _withheld_summary_label(summary: dict) -> str:
    total = int((summary or {}).get("total") or 0)
    if total == 0:
        return "No records withheld"
    return f"{total} record{'s' if total != 1 else ''} withheld"


def _render_prose(text: str) -> str:
    return html.escape(str(text or ""), quote=False).replace("\n", "<br>")


def _render_pills(metadata: dict) -> str:
    parts: list[str] = []
    for key in ("aspect", "polarity", "confidence_state", "score", "salience", "orb"):
        if metadata.get(key) is not None:
            parts.append(
                f"<span class=\"pill\">{_esc(key.replace('_', ' '))}: {_esc(metadata.get(key))}</span>"
            )
    return "".join(parts)


def _section_visual(section_id: str, visuals: dict) -> str:
    return str((visuals.get("section_glyphs") or {}).get(section_id) or "")


def render_synastry_html(synastry_context: dict) -> str:
    ctx = _prepare_context(synastry_context)
    palette = ctx.get("palette") or PALETTES["vibrant"]
    claim_safety = ctx.get("claim_safety") or {}
    withheld_summary = ctx.get("withheld_summary") or {}
    palette_css = f"""
        :root {{
          --bg: {palette['bg']};
          --surface: {palette['surface']};
          --surface-2: {palette['surface_2']};
          --border: {palette['border']};
          --text: {palette['text']};
          --muted: {palette['muted']};
          --subtle: {palette['subtle']};
          --color-identity: {palette['identity']};
          --color-growth: {palette['growth']};
          --color-relationships: {palette['relationships']};
          --color-creativity: {palette['creativity']};
          --color-vocation: {palette['vocation']};
          --color-home: {palette['home']};
          --color-spiritual: {palette['spiritual']};
          --accent: {palette['accent']};
          --purple: {palette['purple']};
          --gold: {palette['gold']};
          --rose: {palette['rose']};
          --ember: {palette['ember']};
          --blue: {palette['blue']};
        }}
    """
    parts = [
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        f"<title>{_esc(ctx.get('report_title'))}</title>",
        "<style>",
        ctx.get("shared_report_css", ""),
        palette_css,
        """
        * { box-sizing: border-box; }
        body.report-shell {
          background: var(--bg);
          color: var(--text);
          margin: 0;
          padding: 48px 24px 72px;
        }
        .container { max-width: 980px; margin: 0 auto; }
        .report-title,
        .meta,
        .section-label,
        .eyebrow,
        .report-record-label,
        .card-kicker,
        .pill {
          font-family: Arial, sans-serif;
        }
        .report-header {
          margin-bottom: 40px;
          padding-bottom: 20px;
          border-bottom: 1px solid var(--border);
        }
        .report-header h1,
        .section-header h2,
        .section-header h3,
        .card-title {
          margin: 0;
        }
        .pairing-name {
          font-size: 1.9rem;
          line-height: 1.2;
          margin-top: 8px;
          color: var(--accent);
        }
        body.report-shell[data-palette="muted"] .pairing-name {
          color: #1a1410;
        }
        .report-title {
          font-size: 0.78rem;
          color: var(--muted);
          margin-top: 8px;
        }
        .meta {
          color: var(--subtle);
          font-size: 0.76rem;
          margin-top: 4px;
        }
        .eyebrow,
        .section-label {
          color: var(--muted);
          font-size: 0.68rem;
          text-transform: uppercase;
          letter-spacing: 1.2px;
        }
        .report-record-grid,
        .section-card-grid {
          display: grid;
          gap: 14px;
        }
        .report-record-grid {
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          margin: 0 0 28px;
        }
        .section-card-grid {
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        }
        .report-record-card,
        .section-card,
        .section-note,
        .trust-note {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 8px;
          box-shadow: 0 14px 36px rgba(0, 0, 0, 0.14);
        }
        .report-record-card {
          padding: 14px 16px;
        }
        .section-card,
        .section-note,
        .trust-note {
          padding: 16px 18px;
        }
        .report-record-label {
          color: var(--muted);
          font-size: 0.56rem;
          letter-spacing: 2px;
          text-transform: uppercase;
          margin-bottom: 6px;
        }
        .report-record-value {
          color: var(--text);
          font-size: 0.9rem;
          line-height: 1.5;
        }
        .report-record-detail {
          color: var(--subtle);
          font-size: 0.72rem;
          line-height: 1.5;
          margin-top: 6px;
        }
        .section {
          margin-top: 34px;
        }
        .section-header {
          margin-bottom: 14px;
        }
        .card-kicker {
          color: var(--muted);
          font-size: 0.62rem;
          letter-spacing: 1.4px;
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        .card-title {
          font-size: 1rem;
          line-height: 1.35;
          margin-bottom: 10px;
        }
        .prose {
          color: var(--text);
          line-height: 1.72;
        }
        .pill-row {
          margin-bottom: 10px;
        }
        .pill {
          display: inline-block;
          padding: 2px 8px;
          border: 1px solid var(--border);
          border-radius: 999px;
          color: var(--muted);
          font-size: 0.7rem;
          margin: 0 6px 6px 0;
        }
        .trace {
          color: var(--subtle);
          font-size: 0.76rem;
          margin-top: 10px;
        }
        .synastry-visual-panel {
          margin: 22px 0 30px;
          padding: 14px;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 8px;
          overflow: hidden;
        }
        .synastry-visual-panel svg {
          display: block;
          width: 100%;
          height: auto;
        }
        .section-header.has-glyph {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 168px;
          gap: 18px;
          align-items: center;
        }
        .section-glyph {
          justify-self: end;
          width: 168px;
        }
        .section-glyph svg {
          display: block;
          width: 168px;
          height: auto;
        }
        ul.clean {
          margin: 10px 0 0;
          padding-left: 18px;
        }
        .section-note {
          margin-top: 14px;
        }
        .trust-note {
          margin-top: 28px;
        }
        .trust-note h3 {
          color: var(--text);
          font-size: 0.72rem;
          letter-spacing: 2px;
          text-transform: uppercase;
          margin: 0 0 10px;
          font-weight: normal;
        }
        .trust-note p {
          margin: 0 0 8px;
        }
        .trust-note p:last-child {
          margin-bottom: 0;
        }
        @media (max-width: 640px) {
          body.report-shell {
            padding: 28px 16px 44px;
          }
          .pairing-name {
            font-size: 1.55rem;
          }
          .section-header.has-glyph {
            grid-template-columns: 1fr;
          }
          .section-glyph {
            justify-self: start;
          }
        }
        @media print {
          .report-record-card,
          .section-card,
          .section-note,
          .trust-note {
            box-shadow: none;
          }
        }
        """,
        f"</style></head><body class=\"report-shell report-magazine report-synastry\" data-palette=\"{_esc(ctx.get('palette_name'))}\"><div class=\"container\">",
        "<header class=\"report-header\">",
        f"<div class=\"section-label\">{_esc(ctx.get('report_subtitle'))}</div>",
        f"<h1 class=\"pairing-name\">{_esc(ctx.get('person_a_name'))} and {_esc(ctx.get('person_b_name'))}</h1>",
        f"<div class=\"report-title\">{_esc(ctx.get('report_title'))}</div>",
        f"<div class=\"meta\">{_esc(ctx.get('report_brand_line'))}</div>",
        f"<div class=\"meta\">Generated { _esc(ctx.get('generation_date')) }</div>",
        "</header>",
        "<section class=\"report-record-grid\">",
        f"<article class=\"report-record-card\"><div class=\"report-record-label\">Birth Time Confidence</div><div class=\"report-record-value\">{_esc(ctx.get('person_a_name'))}: {_esc(_birth_time_state_label(ctx.get('person_a_birth_time_state')))}<br>{_esc(ctx.get('person_b_name'))}: {_esc(_birth_time_state_label(ctx.get('person_b_birth_time_state')))}</div></article>",
        f"<article class=\"report-record-card\"><div class=\"report-record-label\">Sample Status</div><div class=\"report-record-value\">Report status: Preview sample<br>Relationship verdicts supported: {_esc(claim_safety.get('relationship_verdicts_supported'))}</div></article>",
        f"<article class=\"report-record-card\"><div class=\"report-record-label\">Evidence Limits</div><div class=\"report-record-value\">{_esc(_withheld_summary_label(withheld_summary))}</div></article>",
        "</section>",
    ]
    visuals = ctx.get("visuals") or {}
    if visuals.get("relationship_field_map"):
        parts.append(f"<section class=\"synastry-visual-panel\" aria-label=\"Relationship field map\">{visuals['relationship_field_map']}</section>")

    for section in ctx.get("sections", []) or []:
        parts.append(f"<section class=\"section\" id=\"{_esc(section.get('id'))}\">")
        glyph = _section_visual(str(section.get("id") or ""), visuals)
        if glyph:
            parts.append(
                "<div class=\"section-header has-glyph\">"
                f"<div><div class=\"section-label\">Section</div><h2>{_esc(section.get('title'))}</h2></div>"
                f"<div class=\"section-glyph\">{glyph}</div>"
                "</div>"
            )
        else:
            parts.append(f"<div class=\"section-header\"><div class=\"section-label\">Section</div><h2>{_esc(section.get('title'))}</h2></div>")

        if section.get("id") == "directional_landing" and visuals.get("directional_landing_map"):
            parts.append(f"<div class=\"synastry-visual-panel\" aria-label=\"Directional landing map\">{visuals['directional_landing_map']}</div>")

        if section.get("id") == "composite_relationship_field" and visuals.get("composite_field_sigil"):
            parts.append(f"<div class=\"synastry-visual-panel\" aria-label=\"Composite field sigil\">{visuals['composite_field_sigil']}</div>")

        if section.get("blocks"):
            parts.append("<div class=\"section-card-grid\">")
            for block in section.get("blocks", []) or []:
                parts.append("<article class=\"section-card\">")
                parts.append("<div class=\"card-kicker\">Overview</div>")
                parts.append(f"<h3 class=\"card-title\">{_esc(block.get('title') or block.get('id'))}</h3>")
                parts.append(f"<div class=\"prose\">{_render_prose(block.get('body') or '')}</div>")
                parts.append("</article>")
            parts.append("</div>")

        if section.get("items"):
            parts.append("<div class=\"section-card-grid\">")
            for item in section.get("items", []) or []:
                parts.append("<article class=\"section-card\">")
                parts.append("<div class=\"card-kicker\">Evidence Item</div>")
                parts.append(f"<h3 class=\"card-title\">{_esc(item.get('title'))}</h3>")
                metadata = item.get("metadata") or {}
                if metadata:
                    pills = _render_pills(metadata)
                    if pills:
                        parts.append(f"<div class=\"pill-row\">{pills}</div>")
                parts.append(f"<div class=\"prose\">{_render_prose(item.get('body') or '')}</div>")
                families = metadata.get("independent_evidence_families") or []
                if families:
                    parts.append("<div class=\"trace\"><strong>Evidence families:</strong> " + ", ".join(html.escape(str(f), quote=False) for f in families) + "</div>")
                parts.append("</article>")
            parts.append("</div>")

        if section.get("body_items") or section.get("aspect_items") or section.get("ambiguity_items") or section.get("boundary_items"):
            if section.get("method_note"):
                parts.append(f"<div class=\"section-note\"><div class=\"eyebrow\">Method</div><div class=\"prose\">{_render_prose((section.get('method_note') or {}).get('body') or '')}</div></div>")
            for label, key in (
                ("Midpoint Bodies", "body_items"),
                ("Composite Aspects", "aspect_items"),
                ("Midpoint Ambiguities", "ambiguity_items"),
                ("Non-Live Layers", "boundary_items"),
            ):
                items = section.get(key) or []
                if not items:
                    continue
                parts.append(f"<div class=\"section-header\" style=\"margin-top:18px\"><div class=\"section-label\">Composite</div><h3>{_esc(label)}</h3></div>")
                parts.append("<div class=\"section-card-grid\">")
                for item in items:
                    parts.append("<article class=\"section-card\">")
                    parts.append("<div class=\"card-kicker\">Composite Evidence</div>")
                    parts.append(f"<h3 class=\"card-title\">{_esc(item.get('title') or item.get('id'))}</h3>")
                    parts.append(f"<div class=\"prose\">{_render_prose(item.get('body') or '')}</div>")
                    parts.append("</article>")
                parts.append("</div>")

        if section.get("withheld_summary"):
            summary = section.get("withheld_summary") or {}
            by_reason = summary.get("by_reason") or {}
            if by_reason:
                parts.append("<div class=\"section-note\"><div class=\"eyebrow\">Withheld Reasons</div><ul class=\"clean\">")
                for reason, count in by_reason.items():
                    parts.append(f"<li>{_esc(reason)}: {_esc(count)}</li>")
                parts.append("</ul></div>")

        if section.get("id") == "technical_appendix" and visuals.get("visual_legend"):
            parts.append(f"<div class=\"synastry-visual-panel\" aria-label=\"Synastry visual legend\">{visuals['visual_legend']}</div>")

        parts.append("</section>")

    parts.append(f"<footer class=\"meta trust-note\">{_esc(ctx.get('report_footer_text'))}</footer>")
    parts.append("</div></body></html>")
    return "".join(parts)


def build_synastry_html(
    person_a_natal_payload: dict,
    person_b_natal_payload: dict,
    *,
    relationship_meta: dict[str, Any] | None = None,
) -> str:
    context = build_synastry_context(
        person_a_natal_payload,
        person_b_natal_payload,
        relationship_meta=relationship_meta,
    )
    return render_synastry_html(context)


def write_synastry_html(html_content: str, output_filename: str | None = None) -> str:
    output_dir = Path(OUTPUT_DIR) / "synastry"
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_filename is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"synastry_preview_{stamp}_{uuid.uuid4().hex[:8]}.html"
    output_path = output_dir / output_filename
    output_path.write_text(html_content, encoding="utf-8")
    return str(output_path)
