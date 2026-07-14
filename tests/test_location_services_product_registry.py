"""
Smoke tests for the Location Services product registry.

These tests intentionally verify the draft product shells without claiming
they are wired into the production evidence pipeline yet.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from products.location_services import get_location_product, list_location_products
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload


EXPECTED_PRODUCT_SHELLS = {
    "location_services.place_resonance",
    "location_services.place_resonance_search",
    "location_services.between_places",
    "location_services.world_lines",
    "location_services.local_compass",
    "location_services.living_map",
}


def test_location_product_registry_lists_new_product_shells():
    assert set(list_location_products()) >= EXPECTED_PRODUCT_SHELLS


@pytest.mark.parametrize("report_type", sorted(EXPECTED_PRODUCT_SHELLS))
def test_registered_location_product_shells_build_context_and_render_html(report_type):
    product = get_location_product(report_type)
    natal_payload = _build_natal_payload()
    chicago = {"display_name": "Chicago, IL"}
    lisbon = {"display_name": "Lisbon, Portugal"}

    if report_type in {"location_services.place_resonance", "location_services.place_resonance_search"}:
        context = product.build_context(
            natal_payload,
            SYDNEY,
            purpose_lens="career",
            relationship_to_place="possible_move",
        )
    elif report_type == "location_services.between_places":
        context = product.build_context(natal_payload, chicago, lisbon)
    else:
        context = product.build_context(natal_payload, chicago)

    html = product.render_html(context)

    assert context["report_type"] == report_type
    assert context["product_name"] in html
    assert context["sections"]
    assert "<!DOCTYPE html>" in html


def test_unknown_location_product_raises_clear_error():
    with pytest.raises(ValueError, match="Unknown location product"):
        get_location_product("location_services.not_real")
