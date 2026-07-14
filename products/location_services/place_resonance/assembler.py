"""
Compatibility wrapper for the normalized Place Resonance folder layout.

The canonical implementation remains in
`products.location_services.place_resonance_assembler` for now so existing
tests, tooling, and call paths continue to work unchanged.
"""
from products.location_services.place_resonance_assembler import (
    CONTEXT_VERSION,
    PRODUCT_NAME,
    REPORT_TYPE,
    assemble_place_resonance_context,
    build_place_resonance_context,
    select_synthesis_category,
)

__all__ = [
    "CONTEXT_VERSION",
    "PRODUCT_NAME",
    "REPORT_TYPE",
    "assemble_place_resonance_context",
    "build_place_resonance_context",
    "select_synthesis_category",
]
