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

from config import OUTPUT_DIR, TEMPLATES_DIR
from products.synastry.assembler import build_synastry_context


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


def _prepare_context(synastry_context: dict) -> dict:
    render_context = {
        "render_version": RENDER_VERSION,
        "report_title": synastry_context.get("product_name", "Synastry Round 1 Preview"),
        "report_subtitle": "Evidence-linked prose preview",
        "generation_date": datetime.now().strftime("%B %d, %Y"),
        "person_a_name": synastry_context.get("person_a_name"),
        "person_b_name": synastry_context.get("person_b_name"),
        "person_a_birth_time_state": synastry_context.get("person_a_birth_time_state"),
        "person_b_birth_time_state": synastry_context.get("person_b_birth_time_state"),
        "claim_safety": _deepcopy(synastry_context.get("claim_safety") or {}),
        "withheld_summary": _deepcopy(synastry_context.get("withheld_summary") or {}),
        "sections": _deepcopy(synastry_context.get("sections") or []),
        "section_order": list(synastry_context.get("section_order") or []),
    }
    render_context.update(_build_render_defaults(render_context))
    return render_context


def _esc(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return html.escape(str(value), quote=True)


def _render_prose(text: str) -> str:
    return html.escape(str(text or ""), quote=False).replace("\n", "<br>")


def render_synastry_html(synastry_context: dict) -> str:
    ctx = _prepare_context(synastry_context)
    parts = [
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        f"<title>{_esc(ctx.get('report_title'))}</title>",
        "<style>",
        ctx.get("shared_report_css", ""),
        """
        :root {
          --bg: #0d0d12;
          --surface: #151521;
          --surface-2: #1d1d2b;
          --border: #333347;
          --text: #ece7df;
          --muted: #a8a0b3;
          --subtle: #7b7488;
          --accent: #6ad6c3;
          --accent-2: #d57fe7;
          --accent-3: #f1c75d;
        }
        body.report-shell { background: linear-gradient(180deg, #08080d 0%, #12121a 100%); color: var(--text); margin: 0; padding: 32px; }
        .container { max-width: 1120px; margin: 0 auto; }
        .hero { display: grid; gap: 10px; margin-bottom: 28px; }
        .eyebrow { text-transform: uppercase; letter-spacing: 1px; font-size: 0.78rem; color: var(--muted); }
        h1, h2, h3 { margin: 0; }
        .hero-grid, .meta-grid, .item-grid { display: grid; gap: 16px; }
        .hero-grid { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
        .meta-grid { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
        .item-grid { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
        .panel, .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
        .card h3 { font-size: 1rem; margin-bottom: 8px; }
        .prose { line-height: 1.7; color: var(--text); }
        .meta { color: var(--muted); font-size: 0.92rem; }
        .pill { display: inline-block; padding: 3px 8px; border: 1px solid var(--border); border-radius: 999px; color: var(--muted); font-size: 0.8rem; margin-right: 8px; margin-bottom: 6px; }
        .section { margin-top: 28px; }
        .section-header { margin-bottom: 14px; }
        .trace { margin-top: 10px; color: var(--subtle); font-size: 0.82rem; }
        ul.clean { margin: 8px 0 0; padding-left: 18px; }
        """,
        "</style></head><body class=\"report-shell\"><div class=\"container\">",
        "<header class=\"hero\">",
        f"<div class=\"eyebrow\">{_esc(ctx.get('report_subtitle'))}</div>",
        f"<h1>{_esc(ctx.get('person_a_name'))} and {_esc(ctx.get('person_b_name'))}</h1>",
        f"<div class=\"meta\">{_esc(ctx.get('report_title'))}</div>",
        "</header>",
        "<section class=\"hero-grid\">",
        f"<div class=\"panel\"><div class=\"eyebrow\">Birth Time States</div><div class=\"prose\">{_esc(ctx.get('person_a_name'))}: {_esc(ctx.get('person_a_birth_time_state'))}<br>{_esc(ctx.get('person_b_name'))}: {_esc(ctx.get('person_b_birth_time_state'))}</div></div>",
        f"<div class=\"panel\"><div class=\"eyebrow\">Claim Safety</div><div class=\"prose\">Client report available: {_esc((ctx.get('claim_safety') or {}).get('client_report_available'))}<br>Relationship verdicts supported: {_esc((ctx.get('claim_safety') or {}).get('relationship_verdicts_supported'))}</div></div>",
        f"<div class=\"panel\"><div class=\"eyebrow\">Withheld Summary</div><div class=\"prose\">Total withheld records: {_esc((ctx.get('withheld_summary') or {}).get('total'))}</div></div>",
        "</section>",
    ]

    for section in ctx.get("sections", []) or []:
        parts.append(f"<section class=\"section\" id=\"{_esc(section.get('id'))}\">")
        parts.append(f"<div class=\"section-header\"><div class=\"eyebrow\">Section</div><h2>{_esc(section.get('title'))}</h2></div>")

        if section.get("blocks"):
            parts.append("<div class=\"item-grid\">")
            for block in section.get("blocks", []) or []:
                parts.append("<article class=\"card\">")
                parts.append(f"<h3>{_esc(block.get('title') or block.get('id'))}</h3>")
                parts.append(f"<div class=\"prose\">{_render_prose(block.get('body') or '')}</div>")
                parts.append("</article>")
            parts.append("</div>")

        if section.get("items"):
            parts.append("<div class=\"item-grid\">")
            for item in section.get("items", []) or []:
                parts.append("<article class=\"card\">")
                parts.append(f"<h3>{_esc(item.get('title'))}</h3>")
                metadata = item.get("metadata") or {}
                if metadata:
                    parts.append("<div class=\"meta\">")
                    for key in ("aspect", "polarity", "confidence_state", "score", "salience", "orb"):
                        if metadata.get(key) is not None:
                            parts.append(f"<span class=\"pill\">{_esc(key.replace('_', ' '))}: {_esc(metadata.get(key))}</span>")
                    parts.append("</div>")
                parts.append(f"<div class=\"prose\">{_render_prose(item.get('body') or '')}</div>")
                families = metadata.get("independent_evidence_families") or []
                if families:
                    parts.append("<div class=\"trace\"><strong>Evidence families:</strong> " + ", ".join(html.escape(str(f), quote=False) for f in families) + "</div>")
                parts.append("</article>")
            parts.append("</div>")

        if section.get("body_items") or section.get("aspect_items") or section.get("ambiguity_items") or section.get("boundary_items"):
            if section.get("method_note"):
                parts.append(f"<div class=\"panel\"><div class=\"eyebrow\">Method</div><div class=\"prose\">{_render_prose((section.get('method_note') or {}).get('body') or '')}</div></div>")
            for label, key in (
                ("Midpoint Bodies", "body_items"),
                ("Composite Aspects", "aspect_items"),
                ("Midpoint Ambiguities", "ambiguity_items"),
                ("Non-Live Layers", "boundary_items"),
            ):
                items = section.get(key) or []
                if not items:
                    continue
                parts.append(f"<div class=\"section-header\" style=\"margin-top:18px\"><div class=\"eyebrow\">Composite</div><h3>{_esc(label)}</h3></div>")
                parts.append("<div class=\"item-grid\">")
                for item in items:
                    parts.append("<article class=\"card\">")
                    parts.append(f"<h3>{_esc(item.get('title') or item.get('id'))}</h3>")
                    parts.append(f"<div class=\"prose\">{_render_prose(item.get('body') or '')}</div>")
                    parts.append("</article>")
                parts.append("</div>")

        if section.get("withheld_summary"):
            summary = section.get("withheld_summary") or {}
            by_reason = summary.get("by_reason") or {}
            if by_reason:
                parts.append("<div class=\"panel\"><div class=\"eyebrow\">Withheld Reasons</div><ul class=\"clean\">")
                for reason, count in by_reason.items():
                    parts.append(f"<li>{_esc(reason)}: {_esc(count)}</li>")
                parts.append("</ul></div>")

        parts.append("</section>")

    parts.append(f"<footer class=\"meta\" style=\"margin-top:32px\">{_esc(ctx.get('report_footer_text'))}</footer>")
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
