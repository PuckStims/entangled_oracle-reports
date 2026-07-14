"""
Tests for Place Resonance HTML rendering.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.location_services import build_location_evidence_record
from products.location_services.place_resonance.assembler import assemble_place_resonance_context
from products.location_services.place_resonance.renderer import (
    build_place_resonance_html,
    render_place_resonance_html,
    write_place_resonance_html,
)
from test_location_services_relocated_payload import SYDNEY, _build_natal_payload


def test_render_place_resonance_html_renders_authored_synthesis_and_shell():
    record = build_location_evidence_record(
        _build_natal_payload(),
        SYDNEY,
        purpose_lens="career",
        relationship_to_place="possible_move",
    )
    context = assemble_place_resonance_context(record)

    html = render_place_resonance_html(context)

    assert "Place Resonance" in html
    assert "Locational evidence draft" in html
    assert "Several parts of the relocated chart point toward the same chart function here." in html
    assert "Sydney, Australia" in html
    assert "Draft Slot" not in html
    assert "contenteditable=\"true\"" not in html


def test_build_place_resonance_html_hides_raw_todo_and_renders_authored_fallback_copy():
    html = build_place_resonance_html(_build_natal_payload(), SYDNEY)
    assert ">TODO<" not in html
    assert "Draft Slot" not in html
    assert "Source note" not in html
    assert "Several parts of the relocated chart point toward the same chart function here." in html


def test_render_place_resonance_html_uses_warning_summary_not_raw_warning_lines():
    record = build_location_evidence_record(_build_natal_payload(), SYDNEY)
    context = assemble_place_resonance_context(record)

    html = render_place_resonance_html(context)

    assert "Raw warnings:" in html
    assert "Warning groups:" in html
    assert "warning_summary:" in html
    assert "natal aspect(s) involving an angle" not in html


def test_build_place_resonance_html_wrapper_renders_directly_from_inputs():
    html = build_place_resonance_html(
        _build_natal_payload(),
        SYDNEY,
        purpose_lens="study",
        relationship_to_place="trial_visit",
    )

    assert "Purpose: study" in html
    assert "Relationship: trial_visit" in html
    assert "Relocated Angle Contacts" in html
    assert "Chart Visuals" in html
    assert "Astrocartography Visual" in html
    assert "Astrocartography Visual Contract" in html
    assert "<svg" in html


def test_build_place_resonance_html_renders_astrocartography_contract_slot():
    html = build_place_resonance_html(_build_natal_payload(), SYDNEY)
    assert "Chart Visuals" in html
    assert "Astrocartography Visual" in html
    assert "Astrocartography Visual Contract" in html
    assert "Planetary ASC/DSC/MC/IC" in html
    assert "Natal reference wheel rendered in the monochrome line profile" in html
    assert "cw-narr-layer" in html


def test_write_place_resonance_html_writes_to_location_services_output(monkeypatch, tmp_path):
    from products.location_services.place_resonance import renderer

    monkeypatch.setattr(renderer, "OUTPUT_DIR", str(tmp_path))
    path = write_place_resonance_html("<html><body>draft</body></html>", "sample.html")

    written = Path(path)
    assert written.exists()
    assert written.name == "sample.html"
    assert written.parent == tmp_path / "location_services"
    assert written.read_text(encoding="utf-8") == "<html><body>draft</body></html>"
