"""
Compatibility wrapper for the normalized Place Resonance folder layout.

The canonical implementation remains in
`products.location_services.place_resonance_renderer` for now so existing
tests, tooling, and generation scripts continue to work unchanged.
"""
from __future__ import annotations

import products.location_services.place_resonance_renderer as _root_renderer


RENDER_VERSION = _root_renderer.RENDER_VERSION
OUTPUT_DIR = _root_renderer.OUTPUT_DIR


def render_place_resonance_html(place_context: dict) -> str:
    return _root_renderer.render_place_resonance_html(place_context)


def build_place_resonance_html(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> str:
    return _root_renderer.build_place_resonance_html(
        natal_payload,
        destination,
        purpose_lens=purpose_lens,
        relationship_to_place=relationship_to_place,
    )


def write_place_resonance_html(html_content: str, output_filename: str | None = None) -> str:
    # Keep the package-local OUTPUT_DIR monkeypatchable for tests/tooling while
    # the root module remains the canonical implementation.
    previous_output_dir = _root_renderer.OUTPUT_DIR
    _root_renderer.OUTPUT_DIR = OUTPUT_DIR
    try:
        return _root_renderer.write_place_resonance_html(html_content, output_filename)
    finally:
        _root_renderer.OUTPUT_DIR = previous_output_dir

__all__ = [
    "RENDER_VERSION",
    "OUTPUT_DIR",
    "build_place_resonance_html",
    "render_place_resonance_html",
    "write_place_resonance_html",
]
