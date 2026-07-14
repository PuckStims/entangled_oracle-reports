"""
Plugin registration for the Place Resonance Search product.
"""
from __future__ import annotations

from products.location_services.place_resonance_search.assembler import (
    REPORT_TYPE,
    build_place_resonance_search_context,
)
from products.location_services.place_resonance_search.renderer import (
    render_place_resonance_search_html,
)
from products.location_services.registry import LocationProduct, register_location_product


@register_location_product(REPORT_TYPE)
class PlaceResonanceSearchProduct(LocationProduct):
    """
    Place Resonance Search: the discovery/search-oriented location product.
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
        return build_place_resonance_search_context(
            natal_payload,
            destination,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )

    def render_html(self, context: dict) -> str:
        return render_place_resonance_search_html(context)
