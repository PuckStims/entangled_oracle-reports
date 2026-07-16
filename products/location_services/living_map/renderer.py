"""
HTML rendering for the Living Map draft report.
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
from products.location_services.living_map.assembler import build_living_map_context

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

TEMPLATE_NAME = "location_services/templates/living_map.html"
RENDER_VERSION = "living_map_render_v0.2.0"

def _build_render_context(place_context: dict) -> dict:
    return {
        "render_version": RENDER_VERSION,
        "report_title": place_context.get("product_name", "Living Map"),
        "report_subtitle": "Dynamic locational timing draft",
        "generation_date": datetime.now().strftime("%B %d, %Y"),
        "destination_name": place_context.get("destination_name", "Unknown Location"),
        "sections": place_context.get("sections", []),
    }

def render_living_map_html(place_context: dict) -> str:
    """
    Render a Living Map context into HTML.
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
            pass

    return _render_fallback(render_context)

def _render_fallback(render_context: dict) -> str:
    return f"<html><body><h1>{render_context['report_title']}</h1><p>Jinja2 template failed or missing.</p></body></html>"

def build_living_map_html(natal_payload: dict, destination: dict) -> str:
    context = build_living_map_context(natal_payload, destination)
    return render_living_map_html(context)

def write_living_map_html(html_str: str, filename: str | None = None) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"living_map_{timestamp}.html"
    
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_str)
    
    return path
