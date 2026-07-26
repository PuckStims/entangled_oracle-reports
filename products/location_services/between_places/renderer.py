"""
HTML rendering for the Between Places draft report.
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

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


TEMPLATE_NAME = "location_services/templates/between_places.html"
RENDER_VERSION = "between_places_render_v0.3.0"


def _format_theme(theme: str) -> str:
    return theme.replace("_", " ").title()


def _format_fit_label(label: str) -> str:
    return label.replace("_", " ").title()

def _build_render_context(place_context: dict) -> dict:
    comparison = place_context.get("comparison_record", {})
    return {
        "render_version": RENDER_VERSION,
        "report_title": place_context.get("product_name", "Between Places"),
        "report_subtitle": "Locational comparison",
        "generation_date": datetime.now().strftime("%B %d, %Y"),
        "name_a": place_context.get("name_a", "Location A"),
        "name_b": place_context.get("name_b", "Location B"),
        "purpose_lens_label": place_context.get("purpose_lens_label", ""),
        "location_a_id": place_context.get("location_a", {}).get("location_id"),
        "location_b_id": place_context.get("location_b", {}).get("location_id"),
        "comparison_summary": comparison.get("comparison_summary", ""),
        "shared_themes": [_format_theme(t) for t in comparison.get("shared_themes", [])],
        "divergent_themes": [_format_theme(t) for t in comparison.get("divergent_themes", [])],
        "strongest_differences": comparison.get("strongest_differences", []),
        "tradeoffs": comparison.get("tradeoffs", []),
        "compact_profile_a": {
            **place_context.get("compact_profile_a", {}),
            "goal_highlights": [
                {
                    **goal,
                    "fit_label": _format_fit_label(goal.get("fit_label", "")),
                }
                for goal in place_context.get("compact_profile_a", {}).get("goal_highlights", [])
            ],
        },
        "compact_profile_b": {
            **place_context.get("compact_profile_b", {}),
            "goal_highlights": [
                {
                    **goal,
                    "fit_label": _format_fit_label(goal.get("fit_label", "")),
                }
                for goal in place_context.get("compact_profile_b", {}).get("goal_highlights", [])
            ],
        },
        "decision_notes": place_context.get("decision_notes", []),
        "record_a": place_context.get("record_a", {}),
        "record_b": place_context.get("record_b", {}),
    }


def render_between_places_html(place_context: dict) -> str:
    """
    Render a Between Places context into HTML.
    """
    render_context = _build_render_context(place_context)

    if JINJA2_AVAILABLE:
        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )
        try:
            template = env.get_template(TEMPLATE_NAME)
            return template.render(**render_context)
        except TemplateNotFound:
            pass # fallback to manual render if template not found

    return _render_fallback(render_context)


def _render_fallback(render_context: dict) -> str:
    """
    Minimal HTML fallback.
    """
    return f"<html><body><h1>{render_context['report_title']}</h1><p>Jinja2 template failed or missing.</p></body></html>"

def write_between_places_html(html_content: str, output_filename: str | None = None) -> str:
    if output_filename is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"between_places_{stamp}_{uuid.uuid4().hex[:8]}.html"
    
    out_path = Path(OUTPUT_DIR) / output_filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")
    return str(out_path)
