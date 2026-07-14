"""
Plugin registration for the Place Resonance product.
"""
from __future__ import annotations

from products.location_services.place_resonance.assembler import (
    REPORT_TYPE,
    build_place_resonance_context,
)
from products.location_services.place_resonance.renderer import (
    render_place_resonance_html,
)
from products.location_services.registry import LocationProduct, register_location_product


@register_location_product(REPORT_TYPE)
class PlaceResonanceProduct(LocationProduct):
    """
    Place Resonance: the reference single-location Location Services product.
    """

    report_type = REPORT_TYPE

    def build_context(
        self,
        natal_payload: dict,
        destination: dict,
        *,
        purpose_lens: str | None = None,
        relationship_to_place: str | None = None,
    ) -> dict:
        """
        Build the Place Resonance report context from natal and destination inputs.
        """
        return build_place_resonance_context(
            natal_payload,
            destination,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )

    def render_html(self, context: dict) -> str:
        """
        Render a prepared Place Resonance context into HTML.
        """
        return render_place_resonance_html(context)
