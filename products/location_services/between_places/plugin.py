"""
Plugin registration for the Between Places product.
"""
from __future__ import annotations

from products.location_services.registry import LocationProduct, register_location_product
from products.location_services.between_places.assembler import build_between_places_context, REPORT_TYPE
from products.location_services.between_places.renderer import render_between_places_html

@register_location_product(REPORT_TYPE)
class BetweenPlacesProduct(LocationProduct):
    """
    Between Places: A multi-destination comparison product.
    """
    report_type = REPORT_TYPE

    def build_context(
        self,
        natal_payload: dict,
        destination_a: dict,
        destination_b: dict,
        *,
        purpose_lens: str | None = None
    ) -> dict:
        """
        Builds the context for the Between Places comparison.
        """
        return build_between_places_context(
            natal_payload=natal_payload,
            destination_a=destination_a,
            destination_b=destination_b,
            purpose_lens=purpose_lens
        )

    def render_html(self, context: dict) -> str:
        """
        Renders the context into HTML.
        """
        return render_between_places_html(context)
