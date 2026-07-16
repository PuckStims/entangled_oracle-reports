"""
Plugin registration for the Place Resonance Search product.
"""
from __future__ import annotations

from products.location_services.place_resonance_search.assembler import (
    REPORT_TYPE,
    assemble_place_resonance_search_results_context,
    build_place_resonance_search_context,
)
from products.location_services.place_resonance_search.renderer import (
    render_place_resonance_search_html,
    render_place_resonance_search_results_html,
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
        """
        Legacy/compatibility path for single-location wrapping.
        """
        return build_place_resonance_search_context(
            natal_payload,
            destination,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )

    def build_search_context(
        self,
        natal_payload: dict,
        candidates: list[dict] | None = None,
        *,
        purpose_lens: str | None = None,
        relationship_to_place: str | None = None,
        selection_limit: int = 20,
    ) -> dict:
        """
        Canonical multi-location search path.
        """
        return assemble_place_resonance_search_results_context(
            natal_payload,
            candidates=candidates,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
            selection_limit=selection_limit,
        )

    def render_html(self, context: dict) -> str:
        # Route rendering appropriately depending on context structure
        if "selected_locations" in context:
            return render_place_resonance_search_results_html(context)
        return render_place_resonance_search_html(context)
