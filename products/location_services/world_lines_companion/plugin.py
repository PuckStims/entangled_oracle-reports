"""
Plugin registration for the World Lines Companion product.
"""
from __future__ import annotations

from products.location_services.registry import LocationProduct, register_location_product
from products.location_services.world_lines_companion.assembler import build_world_lines_context, REPORT_TYPE
from products.location_services.world_lines_companion.renderer import render_world_lines_html

@register_location_product(REPORT_TYPE)
class WorldLinesProduct(LocationProduct):
    """
    World Lines Companion: Astrocartography map interpretation.
    """
    report_type = REPORT_TYPE

    def build_context(
        self,
        natal_payload: dict,
        destination: dict,
        *,
        purpose_lens: str | None = None
    ) -> dict:
        """
        Builds the context for World Lines Companion.
        """
        return build_world_lines_context(
            natal_payload=natal_payload,
            destination=destination,
            purpose_lens=purpose_lens
        )

    def render_html(self, context: dict) -> str:
        """
        Renders the context into HTML.
        """
        return render_world_lines_html(context)
