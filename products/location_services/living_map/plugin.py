"""
Plugin registration for the Living Map product.
"""
from __future__ import annotations

from products.location_services.registry import LocationProduct, register_location_product
from products.location_services.living_map.assembler import build_living_map_context, REPORT_TYPE
from products.location_services.living_map.renderer import render_living_map_html

@register_location_product(REPORT_TYPE)
class LivingMapProduct(LocationProduct):
    """
    Living Map: Dynamic location timing overlay.
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
        Builds the context for Living Map.
        """
        return build_living_map_context(
            natal_payload=natal_payload,
            destination=destination,
            purpose_lens=purpose_lens
        )

    def render_html(self, context: dict) -> str:
        """
        Renders the context into HTML.
        """
        return render_living_map_html(context)
