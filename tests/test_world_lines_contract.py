from engine.world_lines import build_line_evidence
from products.location_services.world_lines_companion.assembler import build_world_lines_context
from test_location_services_relocated_payload import _build_natal_payload


def test_world_lines_evidence_schema_uses_real_line_computation():
    natal_payload = _build_natal_payload()
    destination = {"display_name": "New York", "latitude": 40.7128, "longitude": -74.0060}

    evidence = build_line_evidence(natal_payload, destination)

    assert evidence["formula_version"] == "world_lines_v0.2.0"
    assert evidence["destination"] == destination
    assert evidence["lines"]
    assert evidence["appendix_trace"]["methodology"].startswith("Swiss Ephemeris")

    distances = [line["distance_km"] for line in evidence["lines"]]
    assert distances == sorted(distances)
    for line in evidence["lines"]:
        assert line["body"] in natal_payload["standard_planets"]
        assert line["angle"] in {"Ascendant", "Descendant", "Midheaven", "Imum_Coeli"}
        assert line["distance_km"] >= 0
        assert line["strength_band"] in {"tight", "moderate", "wide", "background"}
        assert -90 <= line["nearest_point"]["latitude"] <= 90
        assert -180 <= line["nearest_point"]["longitude"] <= 180
        assert line["geometry_method"] in {
            "sidereal_meridian_longitude",
            "sampled_horizon_rise_set_curve_2deg",
        }


def test_world_lines_assembler_renders_computed_lines():
    natal_payload = _build_natal_payload()
    destination = {"location": "Tokyo, Japan"}

    context = build_world_lines_context(natal_payload, destination)

    assert context["destination_name"] == "Tokyo, Japan"
    assert context["destination_context"]["latitude"] == 35.6895
    assert context["destination_context"]["longitude"] == 139.6917

    sections = {s["id"]: s for s in context["sections"]}
    assert "closest_lines" in sections

    closest_lines = sections["closest_lines"]
    assert closest_lines["blocks"]
    assert " on the " in closest_lines["blocks"][0]["title"]
    assert "Distance:" in closest_lines["blocks"][0]["leaf"]["note"]

    natal_context = sections["natal_context"]
    assert natal_context["blocks"]
    assert natal_context["blocks"][0]["title"].startswith("How You Carry ")

    distance = sections["distance_and_uncertainty"]
    assert distance["blocks"]
    assert "nearest point" in distance["blocks"][0]["leaf"]["body"]
    assert "Swiss Ephemeris" in sections["technical_appendix"]["blocks"][0]["leaf"]["body"]
    assert not any(section.get("is_future_method") for section in context["sections"])
