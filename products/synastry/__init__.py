"""
Synastry round-1 preview facade.
"""
from products.synastry.assembler import (
    CONTEXT_VERSION,
    PRODUCT_NAME,
    REPORT_TYPE,
    assemble_synastry_context,
    build_synastry_context,
)
from products.synastry.compiler import SynastryNarrativeCompiler
from products.synastry.renderer import (
    RENDER_VERSION,
    build_synastry_html,
    render_synastry_html,
    write_synastry_html,
)

__all__ = [
    "CONTEXT_VERSION",
    "PRODUCT_NAME",
    "REPORT_TYPE",
    "RENDER_VERSION",
    "assemble_synastry_context",
    "build_synastry_context",
    "SynastryNarrativeCompiler",
    "render_synastry_html",
    "build_synastry_html",
    "write_synastry_html",
]
