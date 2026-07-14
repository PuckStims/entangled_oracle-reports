"""
Tests for the normalized Place Resonance Search package layout.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from products.location_services.place_resonance_search import assembler as search_assembler
from products.location_services.place_resonance_search import renderer as search_renderer
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload


def test_place_resonance_search_context_retitles_the_wrapped_product():
    context = search_assembler.build_place_resonance_search_context(
        _build_natal_payload(),
        SYDNEY,
        purpose_lens="career",
        relationship_to_place="possible_move",
    )

    assert context["context_version"] == "place_resonance_search_context_v0.1.0"
    assert context["report_type"] == "location_services.place_resonance_search"
    assert context["product_name"] == "Place Resonance Search"
    assert context["source_product"] == "location_services.place_resonance"


def test_place_resonance_search_renderer_uses_search_title():
    html = search_renderer.build_place_resonance_search_html(
        _build_natal_payload(),
        SYDNEY,
        purpose_lens="career",
        relationship_to_place="possible_move",
    )

    assert "Place Resonance Search" in html
