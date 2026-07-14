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
RENDER_VERSION = "between_places_render_v0.2.0"


def _build_render_context(place_context: dict) -> dict:
    return {
        "render_version": RENDER_VERSION,
        "report_title": place_context.get("product_name", "Between Places"),
        "report_subtitle": "Locational comparison draft",
        "generation_date": datetime.now().strftime("%B %d, %Y"),
        "name_a": place_context.get("name_a", "Location A"),
        "name_b": place_context.get("name_b", "Location B"),
        "sections": place_context.get("sections", []),
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
