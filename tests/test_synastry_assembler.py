import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from products.synastry.assembler import (
    CONTEXT_VERSION,
    PRODUCT_NAME,
    REPORT_TYPE,
    assemble_synastry_context,
    build_synastry_context,
)
from products.synastry.renderer import render_synastry_html
from tests.test_synastry import APPROXIMATE_BIRTH_TIME, UNKNOWN_BIRTH_TIME, natal_payload


def _section(context: dict, section_id: str) -> dict:
    matches = [section for section in context["sections"] if section["id"] == section_id]
    assert len(matches) == 1
    return matches[0]


def _item_with_body(items: list[dict]) -> dict:
    match = next(item for item in items if isinstance(item.get("body"), str) and item["body"].strip())
    assert match["body"] != "TODO"
    return match


def _pair_payload_exact_exact() -> dict:
    from engine.synastry import build_pair_payload

    return build_pair_payload(
        natal_payload({"Venus": 10.0, "Mercury": 65.0, "Moon": 90.0, "Pluto": 210.0}, ascendant=0.0),
        natal_payload({"Mars": 14.0, "Saturn": 190.0, "Moon": 94.0, "Jupiter": 94.0}, ascendant=90.0),
        relationship_meta={"relationship_type": "test_fixture", "consent_state": "test"},
    )


def _synthetic_mutual(
    body_a: str,
    body_b: str,
    *,
    aspect: str = "Conjunction",
    salience: float = 1.0,
    orb: float = 0.1,
    dependency: str = "body_to_body",
) -> dict:
    return {
        "mutual_key": [
            {"person": "A", "body": body_a},
            {"person": "B", "body": body_b},
        ],
        "aspect": aspect,
        "dependency": dependency,
        "confidence_state": "exact_birth_time",
        "salience": salience,
        "orb": orb,
    }


def _synthetic_theme(
    theme_key: str,
    theme_type: str,
    person_a_evidence: dict,
    person_b_evidence: dict,
    *,
    salience: float = 0.62,
    confidence_state: str = "exact_birth_time",
) -> dict:
    return {
        "theme_key": theme_key,
        "theme_type": theme_type,
        "person_a_evidence": person_a_evidence,
        "person_b_evidence": person_b_evidence,
        "confidence_state": confidence_state,
        "salience": salience,
    }


def test_assemble_synastry_context_has_stable_top_level_shape():
    pair = _pair_payload_exact_exact()
    context = assemble_synastry_context(pair)

    assert context["context_version"] == CONTEXT_VERSION
    assert context["report_type"] == REPORT_TYPE
    assert context["product_name"] == PRODUCT_NAME
    assert context["pair_schema_version"] == pair["schema_version"]
    assert context["section_order"][0] == "overview"
    assert context["section_order"][-1] == "technical_appendix"
    assert "relationship_at_a_glance" in context["section_order"]
    assert "core_relationship_signature" in context["section_order"]
    assert "directional_landing" in context["section_order"]
    assert "shared_natal_baseline" in context["section_order"]
    assert "composite_relationship_field" in context["section_order"]
    assert "integrated_relationship_portrait" in context["section_order"]
    assert context["source_pair_payload"]["schema_version"] == pair["schema_version"]


def test_assemble_synastry_context_does_not_mutate_pair_payload():
    pair = _pair_payload_exact_exact()
    before = copy.deepcopy(pair)
    context = assemble_synastry_context(pair)

    context["relationship_meta"]["relationship_type"] = "MUTATED"
    _section(context, "relationship_at_a_glance")["blocks"][0]["body"] = "MUTATED"
    assert pair == before


def test_relationship_topics_section_compiles_reader_native_narrative():
    context = assemble_synastry_context(_pair_payload_exact_exact())
    section = _section(context, "emotional_rhythm_attachment")

    assert section["blocks"]
    body = section["blocks"][0]["body"]
    assert "organizing theme" in body.lower()
    assert "Moon contacts" in body
    assert "IC contact" in body
    assert "guaranteed relationship outcome" in body


def test_core_relationship_signature_uses_ranked_contacts_and_directionality():
    context = assemble_synastry_context(_pair_payload_exact_exact())
    section = _section(context, "core_relationship_signature")

    assert section["blocks"]
    body = section["blocks"][0]["body"]
    assert "highest-salience cross-chart contacts" in body
    assert "lived terrain is not symmetrical" in body


def test_friction_and_growth_edges_keep_heat_specific_and_non_fatalistic():
    pair = _pair_payload_exact_exact()
    pair["computations"]["mutual_aspects"] = [
        _synthetic_mutual("Mars", "Sun", salience=1.35),
        _synthetic_mutual("Ascendant", "Mars", aspect="Square", salience=1.3, dependency="angle_dependent"),
        _synthetic_mutual("Mercury", "Moon", aspect="Square", salience=1.25),
        _synthetic_mutual("Sun", "Moon", aspect="Trine", salience=1.1),
        _synthetic_mutual("Venus", "Mars", aspect="Sextile", salience=1.05),
        _synthetic_mutual("Mercury", "Jupiter", aspect="Trine", salience=1.0),
        _synthetic_mutual("Moon", "Saturn", aspect="Sextile", salience=0.95),
    ]

    context = assemble_synastry_context(pair)
    section = _section(context, "friction_growth_edges")
    body = section["blocks"][0]["body"]
    assert "growth edges" in body.lower()
    assert "Mars is active on both sides of the field" in body
    assert "need pacing" in body


def test_house_overlay_section_tracks_withheld_count_and_authored_prose():
    from engine.synastry import build_pair_payload

    pair = build_pair_payload(
        natal_payload({"Venus": 10.0}, ascendant=0.0, state=UNKNOWN_BIRTH_TIME),
        natal_payload({"Mars": 14.0, "Moon": 90.0}, ascendant=90.0),
    )
    context = assemble_synastry_context(pair)
    appendix = _section(context, "technical_appendix")
    assert context["withheld_summary"]["total"] > 0
    assert appendix["withheld_summary"]["total"] > 0


def test_shared_natal_baseline_section_handles_empty_and_non_empty_states():
    empty_context = assemble_synastry_context(_pair_payload_exact_exact())
    assert isinstance(_section(empty_context, "shared_natal_baseline")["blocks"], list)
    assert "No single repeated natal baseline dominates this pairing." in _section(empty_context, "shared_natal_baseline")["blocks"][0]["body"]

    from engine.synastry import build_pair_payload

    repeated_aspect = {"body_1": "Venus", "body_2": "Saturn", "aspect": "Square", "orb": 0.0, "angle": 90.0}
    person_a = natal_payload({"Sun": 1.0, "Moon": 2.0, "Venus": 45.0, "Saturn": 135.0})
    person_b = natal_payload({"Sun": 3.0, "Moon": 4.0, "Venus": 75.0, "Saturn": 165.0})
    person_a["aspects"] = [repeated_aspect]
    person_b["aspects"] = [repeated_aspect]
    repeated_context = assemble_synastry_context(build_pair_payload(person_a, person_b))

    section = _section(repeated_context, "shared_natal_baseline")
    assert section["blocks"]
    body = section["blocks"][0]["body"]
    assert "natal baseline" in body.lower()
    assert "repeated structures" in body


def test_shared_natal_baseline_section_avoids_raw_theme_keys():
    pair = _pair_payload_exact_exact()
    pair["computations"]["repeated_natal_themes"] = [
        _synthetic_theme(
            "shared_capricorn_emphasis",
            "same_sign_emphasis",
            {"sign": "Capricorn", "bodies": ["Sun", "Mercury"]},
            {"sign": "Capricorn", "bodies": ["Moon", "Venus"]},
            salience=0.9,
        ),
        _synthetic_theme(
            "shared_earth_element_concentration",
            "same_element_concentration",
            {"element": "earth", "bodies": ["Sun", "Mercury", "Venus", "Mars"]},
            {"element": "earth", "bodies": ["Moon", "Saturn", "Jupiter", "Pluto"]},
            salience=0.88,
        ),
        _synthetic_theme(
            "shared_mars_pluto_square",
            "repeated_aspect_family",
            {"body_1": "Mars", "body_2": "Pluto", "aspect": "Square"},
            {"body_1": "Mars", "body_2": "Pluto", "aspect": "Square"},
        ),
    ]

    context = assemble_synastry_context(pair)
    section = _section(context, "shared_natal_baseline")
    body = section["blocks"][0]["body"]
    assert "shared_mars_pluto_square" not in body
    assert "similar natal architecture" in body


def test_shared_natal_baseline_section_prefers_nonverdictive_pattern_echo_language():
    pair = _pair_payload_exact_exact()
    pair["computations"]["repeated_natal_themes"] = [
        _synthetic_theme(
            "shared_fixed_modality_concentration",
            "same_modality_concentration",
            {"modality": "fixed", "bodies": ["Moon", "Venus", "Mars", "Pluto"]},
            {"modality": "fixed", "bodies": ["Sun", "Mercury", "Saturn", "Jupiter"]},
            salience=0.94,
        ),
        _synthetic_theme(
            "shared_capricorn_emphasis",
            "same_sign_emphasis",
            {"sign": "Capricorn", "bodies": ["Sun", "Mercury"]},
            {"sign": "Capricorn", "bodies": ["Moon", "Venus"]},
            salience=0.9,
        ),
        _synthetic_theme(
            "shared_mars_pluto_square",
            "repeated_aspect_family",
            {"body_1": "Mars", "body_2": "Pluto", "aspect": "Square"},
            {"body_1": "Mars", "body_2": "Pluto", "aspect": "Square"},
        ),
        _synthetic_theme(
            "shared_moon_venus_trine",
            "repeated_aspect_family",
            {"body_1": "Moon", "body_2": "Venus", "aspect": "Trine"},
            {"body_1": "Moon", "body_2": "Venus", "aspect": "Trine"},
        ),
        _synthetic_theme(
            "shared_mercury_north_node_square",
            "repeated_aspect_family",
            {"body_1": "Mercury", "body_2": "North_Node", "aspect": "Square"},
            {"body_1": "Mercury", "body_2": "North_Node", "aspect": "Square"},
        ),
    ]

    context = assemble_synastry_context(pair)
    section = _section(context, "shared_natal_baseline")
    body = section["blocks"][0]["body"]
    assert "immediately recognizable from the inside" in body
    assert "do not decide the relationship" in body


def test_composite_relationship_field_section_synthesizes_bodies_and_aspects():
    context = assemble_synastry_context(_pair_payload_exact_exact())
    section = _section(context, "composite_relationship_field")

    assert section["blocks"]
    body = section["blocks"][0]["body"]
    assert "Composite Moon" in body
    assert "emotional climate" in body


def test_technical_appendix_includes_withheld_and_unsupported_routes():
    from engine.synastry import build_pair_payload

    pair = build_pair_payload(
        natal_payload({"Venus": 10.0}, ascendant=0.0, state=APPROXIMATE_BIRTH_TIME),
        natal_payload({"Mars": 14.0}, ascendant=90.0, state=UNKNOWN_BIRTH_TIME),
    )
    context = assemble_synastry_context(pair)
    appendix = _section(context, "technical_appendix")

    assert appendix["blocks"]
    assert any(block["id"].startswith("unsupported_layer:") for block in appendix["blocks"])
    assert appendix["withheld_summary"]["total"] > 0


def test_build_synastry_context_wrapper_builds_pair_then_assembles():
    context = build_synastry_context(
        natal_payload({"Venus": 10.0}, ascendant=0.0),
        natal_payload({"Mars": 14.0}, ascendant=90.0),
        relationship_meta={
            "relationship_type": "wrapper_test",
            "person_a_label": "Rowan",
            "person_b_label": "Mira",
        },
    )
    assert context["product_name"] == PRODUCT_NAME
    assert context["relationship_meta"]["relationship_type"] == "wrapper_test"
    assert context["person_a_name"] == "Rowan"
    assert context["person_b_name"] == "Mira"


def test_render_synastry_html_emits_section_titles_and_no_todo():
    html = render_synastry_html(assemble_synastry_context(_pair_payload_exact_exact()))
    assert "Synastry Narrative Preview" in html
    assert "Relationship at a Glance" in html
    assert "Integrated Relationship Portrait" in html
    assert "Technical Appendix" in html
    assert "TODO" not in html
    assert "Client report available: No" in html
    assert "Relationship verdicts supported: No" in html


def test_assemble_synastry_context_rejects_missing_required_fields():
    with pytest.raises(ValueError, match="missing required field"):
        assemble_synastry_context({"schema_version": "partial"})
