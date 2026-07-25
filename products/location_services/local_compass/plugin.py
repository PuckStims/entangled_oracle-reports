"""
Plugin registration for the Local Compass product.
"""
from __future__ import annotations

from products.location_services.registry import LocationProduct, register_location_product
from products.location_services.local_compass.assembler import build_local_compass_context, REPORT_TYPE
from products.location_services.local_compass.renderer import render_local_compass_html

@register_location_product(REPORT_TYPE)
class LocalCompassProduct(LocationProduct):
    """
    Local Compass: Local Space directional interpretation.
    """
    report_type = REPORT_TYPE

    def build_context(
        self,
        natal_payload: dict,
        anchor: dict,
        *,
        destination: dict | None = None,
        route: dict | None = None,
        purpose_lens: str | None = None,
    ) -> dict:
        """
        Builds the context for Local Compass.
        """
        return build_local_compass_context(
            natal_payload=natal_payload,
            anchor=anchor,
            destination=destination,
            route=route,
            purpose_lens=purpose_lens,
        )

    def render_html(self, context: dict) -> str:
        """
        Renders the context into HTML.
        """
        return render_local_compass_html(context)
