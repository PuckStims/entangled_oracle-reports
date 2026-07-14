"""
Tests for the astrocartography SVG contract scaffold.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.astrocartography_svg import (
    CONTRACT_VERSION,
    VIEWBOX,
    build_astrocartography_svg_contract,
)
from engine.location_services import build_location_evidence_record
from products.location_services.place_resonance.assembler import assemble_place_resonance_context
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload


def test_build_astrocartography_svg_contract_has_stable_shape_and_svg():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)

    contract = build_astrocartography_svg_contract(_build_natal_payload(), context)

    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["projection"] == "equirectangular"
    assert contract["viewbox"] == VIEWBOX
    assert contract["status"] == "contract_ready_future_method"
    assert contract["capability_boundary"]["line_geometry"] == "not_computed"
    assert isinstance(contract["layers"], list) and contract["layers"]
    assert contract["anchors"]["birth"]
    assert contract["anchors"]["destination"]
    assert "<svg" in contract["svg"]
    assert "Astrocartography Visual Contract" in contract["svg"]


def test_build_astrocartography_svg_contract_warns_when_birth_time_not_exact():
    natal_payload = _build_natal_payload()
    natal_payload["user_profile"]["birth_time_state"] = "unknown_birth_time"
    natal_payload["user_profile"]["birth_time_confidence"] = "unknown_birth_time"

    record = build_location_evidence_record(natal_payload, SYDNEY)
    context = assemble_place_resonance_context(record)

    contract = build_astrocartography_svg_contract(natal_payload, context)

    assert any("Exact birth time" in warning for warning in contract["warnings"])
    planetary_layer = next(layer for layer in contract["layers"] if layer["id"] == "planetary_lines")
    assert "exact birth time" in planetary_layer["detail"]


def test_build_astrocartography_svg_contract_uses_destination_display_name_in_svg():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)

    contract = build_astrocartography_svg_contract(_build_natal_payload(), context)

    assert "Sydney, Australia" in contract["svg"]
