"""
Place Resonance Search renderer wrapper.

This package currently reuses the Place Resonance HTML path while
preserving a distinct report identity and output filename prefix.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import products.location_services.place_resonance_renderer as _root_renderer

from products.location_services.place_resonance_search.assembler import (
    build_place_resonance_search_context,
)


RENDER_VERSION = "place_resonance_search_render_v0.1.0"
OUTPUT_DIR = _root_renderer.OUTPUT_DIR


def render_place_resonance_search_html(place_context: dict) -> str:
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
