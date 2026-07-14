"""
Normalized Place Resonance Search package facade.

This package currently reuses the existing Place Resonance evidence and
render path while establishing a distinct product identity for the
search/discovery concept.
"""
from products.location_services.place_resonance_search.assembler import (
    CONTEXT_VERSION,
    PRODUCT_NAME,
    REPORT_TYPE,
    assemble_place_resonance_search_context,
    assemble_place_resonance_search_results_context,
    build_search_evidence_records,
    build_scored_search_locations,
    build_place_resonance_search_context,
    select_synthesis_category,
)
from products.location_services.place_resonance_search.renderer import (
    RENDER_VERSION,
    build_place_resonance_search_results_html,
    build_place_resonance_search_html,
    render_place_resonance_search_results_html,
    render_place_resonance_search_html,
    write_place_resonance_search_html,
)

__all__ = [
    "CONTEXT_VERSION",
    "PRODUCT_NAME",
    "REPORT_TYPE",
    "RENDER_VERSION",
    "assemble_place_resonance_search_context",
    "assemble_place_resonance_search_results_context",
    "build_search_evidence_records",
    "build_scored_search_locations",
    "build_place_resonance_search_context",
    "select_synthesis_category",
    "build_place_resonance_search_results_html",
    "build_place_resonance_search_html",
    "render_place_resonance_search_results_html",
    "render_place_resonance_search_html",
    "write_place_resonance_search_html",
]
