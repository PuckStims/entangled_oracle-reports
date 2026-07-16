"""
HTML rendering for the Place Resonance draft report.

This consumes the structured context produced by place_resonance_assembler and
renders a browser-reviewable HTML draft. Unauthored scaffold leaves are shown
as explicit draft slots instead of raw TODO paragraphs.
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
from engine.astrocartography_svg import build_astrocartography_svg_contract
from products.location_services.place_resonance_assembler import build_place_resonance_context

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


TEMPLATE_NAME = "location_services/templates/place_resonance.html"
RENDER_VERSION = "place_resonance_render_v0.1.0"
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


def _is_draft_body(body: Any) -> bool:
    return isinstance(body, str) and body.strip() == "TODO"


def _draft_prompt(note: str, fallback: str) -> str:
    text = (note or "").strip()
    if text:
        return text
    return fallback


def _prepare_leaf(leaf: dict | None, fallback_prompt: str) -> dict | None:
    if not isinstance(leaf, dict):
        return None

    body = leaf.get("body") or ""
    note = leaf.get("_note") or ""
    is_draft = _is_draft_body(body)
    return {
        "body": "" if is_draft else str(body),
        "note": str(note),
        "claim_level": str(leaf.get("claim_level") or ""),
        "requires_evidence": list(leaf.get("requires_evidence") or []),
        "is_draft": is_draft,
        "draft_prompt": _draft_prompt(note, fallback_prompt),
    }


def _format_source_value(value: Any) -> str:
    if value is None:
        return "Unknown"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _summarize_source(source: dict | None, evidence_type: str) -> str:
    if not isinstance(source, dict):
        return "No structured source summary."
    if evidence_type == "angle_contact":
        return (
            f"{source.get('body')} near {source.get('angle')} "
            f"({source.get('contact_strength')}, orb {source.get('orb')})"
        )
    if evidence_type == "house_change":
        return (
            f"{source.get('body')} from house {source.get('natal_house')} to "
            f"{source.get('relocated_house')} ({source.get('movement_type')})"
        )
    if evidence_type == "orientation_shift":
        return f"{source.get('angle')} sign changes under relocation."
    if evidence_type == "natal_modifier":
        return (
            f"{source.get('body')} natal condition: "
            f"{source.get('condition_classification')} "
            f"({source.get('confidence')})"
        )
    if evidence_type == "unsupported_method":
        return f"{source.get('method')} is intentionally excluded in v0.1."
    return "Evidence item."


def _prepare_synthesis_section(section: dict) -> dict:
    return {
        "id": section["id"],
        "title": section["title"],
        "category": section.get("category"),
        "repeated_bodies": list(section.get("repeated_bodies") or []),
        "source_evidence_ids": list(section.get("source_evidence_ids") or []),
        "leaf": _prepare_leaf(section.get("selected_leaf"), "Write the lead synthesis paragraph here."),
    }


def _prepare_blocks_section(section: dict, draft_prompt: str) -> dict:
    blocks = []
    for block in section.get("blocks", []) or []:
        source = block.get("source") or {}
        blocks.append({
            "id": block.get("id"),
            "source": source,
            "leaf": _prepare_leaf(block.get("selected_leaf"), draft_prompt),
        })
    return {
        "id": section["id"],
        "title": section["title"],
        "blocks": blocks,
    }


def _prepare_evidence_summary_section(section: dict, grammar: dict | None = None) -> dict:
    rows = []
    items = (grammar or {}).get("normalized_evidence", {}).get("items", [])
    for row in section.get("rows", []) or []:
        evidence_type = row.get("evidence_type") or "unknown"
        theme_relationship = ""
        for item in items:
            if item.get("evidence_id") == row.get("id"):
                rel = item.get("relationship", "").replace("_", " ")
                theme = item.get("theme_key", "").replace("_", " ")
                theme_relationship = f"{rel} {theme}"
                break
                
        rows.append({
            "id": row.get("id"),
            "tier": row.get("tier"),
            "evidence_type": evidence_type,
            "theme_relationship": theme_relationship,
            "source_summary": _summarize_source(row.get("source"), evidence_type),
            "leaf": _prepare_leaf(row.get("selected_leaf"), "Write the evidence note here."),
        })
    return {
        "id": section["id"],
        "title": section["title"],
        "rows": rows,
    }


def _prepare_technical_appendix_section(section: dict) -> dict:
    prepared = _prepare_blocks_section(section, "Write the technical appendix note here.")
    prepared["raw_warning_count"] = section.get("raw_warning_count")
    prepared["warning_summary_count"] = section.get("warning_summary_count")
    return prepared


def _prepared_sections(context: dict) -> list[dict]:
    prepared = []
    grammar = context.get("_grammar")
    for section in context.get("sections", []) or []:
        section_id = section.get("id")
        if section_id == "place_signature":
            prepared.append(_prepare_synthesis_section(section))
        elif section_id == "evidence_summary":
            prepared.append(_prepare_evidence_summary_section(section, grammar))
        elif section_id == "technical_appendix":
            prepared.append(_prepare_technical_appendix_section(section))
        else:
            prepared.append(_prepare_blocks_section(section, "Write this draft section here."))
    return prepared


def _draft_counts(sections: list[dict]) -> tuple[int, int]:
    total = 0
    draft = 0
    for section in sections:
        leaf = section.get("leaf")
        if isinstance(leaf, dict):
            total += 1
            draft += 1 if leaf.get("is_draft") else 0
        for block in section.get("blocks", []) or []:
            leaf = block.get("leaf")
            if isinstance(leaf, dict):
                total += 1
                draft += 1 if leaf.get("is_draft") else 0
        for row in section.get("rows", []) or []:
            leaf = row.get("leaf")
            if isinstance(leaf, dict):
                total += 1
                draft += 1 if leaf.get("is_draft") else 0
    return draft, total


def _build_render_context(place_context: dict) -> dict:
    birth = place_context.get("birth_context") or {}
    destination = place_context.get("destination_context") or {}
    prepared_sections = _prepared_sections(place_context)
    draft_count, leaf_count = _draft_counts(prepared_sections)

    render_context = {
        "render_version": RENDER_VERSION,
        "report_title": place_context.get("product_name", "Place Resonance"),
        "report_subtitle": "Locational evidence draft",
        "generation_date": datetime.now().strftime("%B %d, %Y"),
        "birth_location": birth.get("birth_location"),
        "destination_name": destination.get("display_name"),
        "birth_date": birth.get("birth_date"),
        "birth_time": birth.get("birth_time"),
        "birth_time_confidence": birth.get("birth_time_confidence"),
        "purpose_lens": place_context.get("purpose_lens"),
        "relationship_to_place": place_context.get("relationship_to_place"),
        "section_order": list(place_context.get("section_order") or []),
        "sections": prepared_sections,
        "draft_leaf_count": draft_count,
        "leaf_count": leaf_count,
        "chart_wheel_svg": place_context.get("chart_wheel_svg", ""),
        "chart_wheel_data": place_context.get("chart_wheel_data"),
        "chart_wheel_note": place_context.get("chart_wheel_note", ""),
        "astrocartography_visual": _deepcopy(place_context.get("astrocartography_visual") or {}),
        "_grammar": _deepcopy(place_context.get("_grammar") or {}),
    }
    render_context.update(_build_render_defaults(render_context))
    return render_context


def render_place_resonance_html(place_context: dict) -> str:
    """
    Render a Place Resonance context into HTML.
    """
    render_context = _build_render_context(place_context)

    if not JINJA2_AVAILABLE:
        return _render_fallback(render_context)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(TEMPLATE_NAME)
    return template.render(**render_context)


def build_place_resonance_html(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> str:
    context = build_place_resonance_context(
        natal_payload,
        destination,
        purpose_lens=purpose_lens,
        relationship_to_place=relationship_to_place,
    )
    context.update(_build_visual_context(natal_payload, context))
    return render_place_resonance_html(context)


def write_place_resonance_html(html_content: str, output_filename: str | None = None) -> str:
    """
    Write rendered Place Resonance HTML to the output directory.
    """
    output_dir = Path(OUTPUT_DIR) / "location_services"
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_filename is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"place_resonance_{stamp}_{uuid.uuid4().hex[:8]}.html"

    output_path = output_dir / output_filename
    output_path.write_text(html_content, encoding="utf-8")
    return str(output_path)


def _render_leaf_block(leaf: dict | None, element_id: str) -> str:
    if not isinstance(leaf, dict):
        return ""

    if leaf.get("is_draft"):
        prompt = html.escape(leaf.get("draft_prompt") or "", quote=True)
        note = html.escape(leaf.get("note") or "", quote=False)
        return (
            f'<div class="draft-block">'
            f'<div class="draft-label">Draft Slot</div>'
            f'<div class="draft-prompt">{prompt}</div>'
            f'<div id="{html.escape(element_id, quote=True)}" class="draft-editor" '
            f'contenteditable="true" data-placeholder="{prompt}"></div>'
            f'<details class="draft-note"><summary>Source note</summary><p>{note}</p></details>'
            f"</div>"
        )

    body = html.escape(leaf.get("body") or "", quote=False).replace("\n", "<br>")
    return f'<div class="prose-block" id="{html.escape(element_id, quote=True)}">{body}</div>'


def _render_fallback(render_context: dict) -> str:
    """
    Minimal HTML fallback when Jinja2 is unavailable.
    """
    parts = [
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        f"<title>{html.escape(render_context.get('report_title') or 'Place Resonance')}</title>",
        "<style>",
        render_context.get("shared_report_css", ""),
        """
        :root {
          --bg: #f5efe5;
          --surface: #fffaf4;
          --surface-2: #efe4d6;
          --border: #c8b9a6;
          --text: #1f1f1b;
          --muted: #6f665b;
          --subtle: #897d70;
          --color-growth: #5b7f6e;
          --ember: #a66233;
          --purple: #3e5c55;
        }
        body.report-shell { background: linear-gradient(180deg, #f7f1e8 0%, #efe4d6 100%); color: var(--text); margin: 0; padding: 32px; }
        .container { max-width: 980px; margin: 0 auto; }
        .draft-editor:empty::before { content: attr(data-placeholder); color: var(--subtle); }
        .draft-editor { min-height: 120px; border: 1px dashed var(--border); background: #fffdf9; padding: 12px; }
        .draft-block, .block-card, .meta-card, .summary-table { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin: 16px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border-bottom: 1px solid var(--border); text-align: left; padding: 10px 8px; vertical-align: top; }
        .eyebrow { text-transform: uppercase; letter-spacing: 2px; font-size: 0.7rem; color: var(--muted); }
        .hero { display: grid; gap: 12px; margin-bottom: 24px; }
        """,
        "</style></head><body class=\"report-shell\"><div class=\"container\">",
        f"<header class=\"hero\"><div class=\"eyebrow\">{html.escape(render_context.get('report_subtitle') or '')}</div>",
        f"<h1>{html.escape(render_context.get('report_title') or '')}</h1>",
        f"<p>{html.escape(render_context.get('destination_name') or 'Unknown destination')}</p></header>",
    ]

    if render_context.get("chart_wheel_svg") or render_context.get("astrocartography_visual"):
        parts.append("<section class=\"block-card\"><div class=\"eyebrow\">Visual Reference</div>")
        if render_context.get("chart_wheel_svg"):
            parts.append("<div class=\"block-card\">")
            parts.append(render_context["chart_wheel_svg"])
            if render_context.get("chart_wheel_note"):
                parts.append(f"<p>{html.escape(render_context['chart_wheel_note'])}</p>")
            parts.append("</div>")
        astro = render_context.get("astrocartography_visual") or {}
        if astro:
            parts.append("<div class=\"block-card\">")
            parts.append(f"<strong>{html.escape(astro.get('title') or 'Astrocartography slot')}</strong>")
            if astro.get("svg"):
                parts.append(str(astro["svg"]))
            parts.append(f"<p>{html.escape(astro.get('note') or '')}</p>")
            parts.append("</div>")
        parts.append("</section>")

    for section in render_context.get("sections", []):
        parts.append(f"<section><div class=\"eyebrow\">{html.escape(section.get('title') or '')}</div>")
        leaf = section.get("leaf")
        if isinstance(leaf, dict):
            parts.append(_render_leaf_block(leaf, f"{section.get('id')}-leaf"))
        for row in section.get("rows", []) or []:
            parts.append("<div class=\"block-card\">")
            parts.append(f"<strong>{html.escape(row.get('id') or '')}</strong>")
            parts.append(f"<p>{html.escape(row.get('source_summary') or '')}</p>")
            parts.append(_render_leaf_block(row.get("leaf"), f"{row.get('id')}-leaf"))
            parts.append("</div>")
        for block in section.get("blocks", []) or []:
            parts.append("<div class=\"block-card\">")
            parts.append(f"<strong>{html.escape(block.get('id') or '')}</strong>")
            parts.append(_render_leaf_block(block.get("leaf"), f"{block.get('id')}-leaf"))
            parts.append("</div>")
        parts.append("</section>")

    parts.append(f"<footer>{html.escape(render_context.get('report_footer_text') or '')}</footer>")
    parts.append("</div></body></html>")
    return "".join(parts)


def _build_visual_context(natal_payload: dict, place_context: dict) -> dict:
    """
    Optional visual assets for Place Resonance.

    Today this includes the natal SVG wheel and a reserved astrocartography
    slot that stays explicit about the current capability boundary.
    """
    visuals = {
        "chart_wheel_svg": "",
        "chart_wheel_data": None,
        "chart_wheel_note": "",
        "astrocartography_visual": build_astrocartography_svg_contract(natal_payload, place_context),
    }

    birth_context = place_context.get("birth_context") or {}
    if birth_context.get("birth_time_confidence") != "exact_birth_time":
        visuals["chart_wheel_note"] = (
            "Natal wheel skipped: exact birth time is required for a reliable "
            "angle-based wheel rendering in this draft."
        )
        return visuals

    try:
        from engine.chart_wheel import build_chart_wheel_data, render_natal_wheel_svg
    except Exception as exc:  # noqa: BLE001
        visuals["chart_wheel_note"] = f"Natal wheel unavailable: {exc}"
        return visuals

    try:
        chart_wheel_data = build_chart_wheel_data(natal_payload, report_type="personal_forecast")
        if chart_wheel_data:
            visuals["chart_wheel_data"] = chart_wheel_data
            visuals["chart_wheel_svg"] = render_natal_wheel_svg(
                chart_wheel_data,
                compact=False,
                config={
                    "theme": "monochrome_line",
                },
            )
            visuals["chart_wheel_note"] = (
                "Natal reference wheel rendered in the monochrome line profile, keeping the "
                "connecting structure visible while letting the relocation map stay visually distinct."
            )
        else:
            visuals["chart_wheel_note"] = (
                "Natal wheel unavailable: the payload did not contain the angle "
                "data required by the wheel renderer."
            )
    except Exception as exc:  # noqa: BLE001
        visuals["chart_wheel_note"] = f"Natal wheel skipped: {exc}"

    return visuals
