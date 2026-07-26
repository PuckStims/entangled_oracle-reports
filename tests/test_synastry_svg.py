import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.synastry import build_pair_payload
from products.synastry.assembler import assemble_synastry_context
from products.synastry.renderer import render_synastry_html
from tests.test_synastry import natal_payload
from visuals.synastry_svg import (
    SynastrySVGData,
    normalize_synastry_for_svg,
    render_composite_field_sigIl,
    render_directional_landing_map,
    render_relationship_field_map,
    render_section_glyph,
)


FORBIDDEN = (
    "compatibility score",
    "compatibility percentage",
    "soulmate",
    "meant to be",
    "timing window",
    "{'",
    '":',
)


def _svg_pair_payload():
    return build_pair_payload(
        natal_payload({"Sun": 10.0, "Moon": 90.0, "Mercury": 64.0, "Venus": 15.0, "Mars": 128.0}, ascendant=0.0),
        natal_payload({"Sun": 130.0, "Moon": 94.0, "Mercury": 244.0, "Venus": 194.0, "Mars": 20.0}, ascendant=90.0),
        relationship_meta={"person_a_label": "Rowan & Co", "person_b_label": "Mira <North>"},
    )


def _assert_valid_svg(svg: str):
    assert svg.startswith("<svg")
    ET.fromstring(svg)
    lowered = svg.lower()
    for term in FORBIDDEN:
        assert term not in lowered


def test_relationship_field_map_is_valid_escaped_svg():
    context = assemble_synastry_context(_svg_pair_payload())
    svg = render_relationship_field_map(context)

    _assert_valid_svg(svg)
    assert "Rowan &amp; Co" in svg
    assert "Mira &lt;North&gt;" in svg
    assert "Relationship Field Map" in svg


def test_svg_renderers_handle_empty_data_without_crashing():
    empty = SynastrySVGData(person_a_name="A <one>", person_b_name="B & two")

    _assert_valid_svg(render_relationship_field_map(empty))
    _assert_valid_svg(render_directional_landing_map(empty))
    _assert_valid_svg(render_composite_field_sigIl(empty))
    _assert_valid_svg(render_section_glyph("communication_daily_exchange", empty))


def test_normalize_synastry_for_svg_uses_structured_pair_payload():
    data = normalize_synastry_for_svg(assemble_synastry_context(_svg_pair_payload()))

    assert data.aspects
    assert data.house_overlays
    assert data.composite.sun_sign
    assert data.category_scores
    assert "communication_exchange" in data.category_scores


def test_synastry_html_does_not_show_visual_layer_by_default():
    html = render_synastry_html(assemble_synastry_context(_svg_pair_payload()))
    lowered = html.lower()

    assert "relationship field map" not in lowered
    assert "directional landing map" not in lowered
    assert "composite field sigil" not in lowered
    assert "synastry visual legend" not in lowered


def test_synastry_html_can_opt_into_visual_layer_and_boundaries():
    pair = _svg_pair_payload()
    pair["relationship_meta"]["enable_synastry_visuals"] = True
    html = render_synastry_html(assemble_synastry_context(pair))
    lowered = html.lower()

    assert "relationship field map" in lowered
    assert "directional landing map" in lowered
    assert "composite field sigil" in lowered
    assert "synastry visual legend" in lowered
    assert "relative, not a verdict" in lowered
    for term in FORBIDDEN[:5]:
        assert term not in lowered
