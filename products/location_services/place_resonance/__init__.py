"""
Normalized Place Resonance package facade.

The canonical implementation still lives in the root-level
`place_resonance_assembler.py` and `place_resonance_renderer.py` modules.
This package provides a product-folder home without breaking the current
call path during migration.
"""
from products.location_services.place_resonance.assembler import (
    CONTEXT_VERSION,
    PRODUCT_NAME,
    REPORT_TYPE,
    assemble_place_resonance_context,
    build_place_resonance_context,
    select_synthesis_category,
)
from products.location_services.place_resonance.renderer import (
    RENDER_VERSION,
    build_place_resonance_html,
    render_place_resonance_html,
    write_place_resonance_html,
)

__all__ = [
    "CONTEXT_VERSION",
    "PRODUCT_NAME",
    "REPORT_TYPE",
    "RENDER_VERSION",
    "assemble_place_resonance_context",
    "build_place_resonance_context",
    "select_synthesis_category",
    "build_place_resonance_html",
    "render_place_resonance_html",
    "write_place_resonance_html",
]
