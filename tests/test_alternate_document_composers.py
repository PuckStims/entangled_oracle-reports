from __future__ import annotations

from products.shared.composers import compose_report
from products.shared.document_parity import validate_document_parity
from products.shared.document_model import Section
from products.shared.docx_renderer import DocxRenderer


def _markers(document):
    return {node.marker for node in document.nodes if isinstance(node, Section) and node.marker}


def test_synastry_composer_preserves_completed_section_structure(tmp_path):
    from engine.synastry import build_pair_payload
    from products.synastry.assembler import assemble_synastry_context
    from tests.test_synastry import natal_payload

    pair = build_pair_payload(
        natal_payload({"Venus": 10.0, "Moon": 90.0}, ascendant=0.0),
        natal_payload({"Mars": 14.0, "Moon": 94.0}, ascendant=90.0),
        relationship_meta={"relationship_type": "test_fixture", "consent_state": "test"},
    )
    context = assemble_synastry_context(pair)
    document = compose_report("synastry", context)

    assert _markers(document) >= set(context["section_order"])
    assert not validate_document_parity(document, context)
    output = tmp_path / "synastry.docx"
    DocxRenderer(theme_id=document.theme_id).render_to_path(document, output)
    assert output.exists()


def test_location_composer_handles_standard_section_contexts():
    from products.location_services import get_location_product
    from tests.test_location_services_relocated_payload import SYDNEY, _build_natal_payload

    natal_payload = _build_natal_payload()
    for report_type in (
        "location_services.place_resonance",
        "location_services.world_lines",
        "location_services.local_compass",
        "location_services.living_map",
    ):
        context = get_location_product(report_type).build_context(natal_payload, SYDNEY, purpose_lens="career")
        document = compose_report(report_type, context)

        assert _markers(document) >= {section["id"] for section in context["sections"]}
        assert not validate_document_parity(document, context)


def test_location_composer_handles_comparison_and_search_contexts():
    from products.location_services import get_location_product
    from tests.test_location_services_relocated_payload import SYDNEY, _build_natal_payload

    natal_payload = _build_natal_payload()
    comparison_context = get_location_product("location_services.between_places").build_context(
        natal_payload,
        SYDNEY,
        {"display_name": "Chicago, Illinois, United States", "latitude": 41.8781, "longitude": -87.6298, "timezone": "America/Chicago"},
    )
    comparison_document = compose_report("location_services.between_places", comparison_context)
    assert _markers(comparison_document) >= {section["id"] for section in comparison_context["sections"]}
    assert not validate_document_parity(comparison_document, comparison_context)

    search_context = get_location_product("location_services.place_resonance_search").build_search_context(
        natal_payload, purpose_lens="career", selection_limit=2
    )
    search_document = compose_report("location_services.place_resonance_search", search_context)
    assert any(marker.startswith("bucket-") for marker in _markers(search_document))
    assert not validate_document_parity(search_document, search_context)
