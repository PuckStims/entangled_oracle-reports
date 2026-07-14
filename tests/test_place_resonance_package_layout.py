"""
Tests for the normalized Place Resonance product-folder layout.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from products.location_services import place_resonance_assembler as root_assembler
from products.location_services import place_resonance_renderer as root_renderer
from products.location_services.place_resonance import assembler as package_assembler
from products.location_services.place_resonance import renderer as package_renderer


def test_place_resonance_package_assembler_reexports_root_symbols():
    assert package_assembler.CONTEXT_VERSION == root_assembler.CONTEXT_VERSION
    assert package_assembler.REPORT_TYPE == root_assembler.REPORT_TYPE
    assert package_assembler.PRODUCT_NAME == root_assembler.PRODUCT_NAME
    assert package_assembler.assemble_place_resonance_context is root_assembler.assemble_place_resonance_context
    assert package_assembler.build_place_resonance_context is root_assembler.build_place_resonance_context
    assert package_assembler.select_synthesis_category is root_assembler.select_synthesis_category


def test_place_resonance_package_renderer_exposes_the_root_render_contract():
    assert package_renderer.RENDER_VERSION == root_renderer.RENDER_VERSION
    assert package_renderer.OUTPUT_DIR == root_renderer.OUTPUT_DIR
    assert callable(package_renderer.build_place_resonance_html)
    assert callable(package_renderer.render_place_resonance_html)
    assert callable(package_renderer.write_place_resonance_html)
