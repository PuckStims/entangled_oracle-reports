from copy import deepcopy

from engine.living_map import build_living_map_evidence
from products.location_services.living_map.assembler import build_living_map_context
from engine.natal_engine import generate_payload


def get_dummy_payload():
    return generate_payload({
        "name": "Test",
        "date": "1990-01-01",
        "time": "12:00",
        "location": "New York",
        "simple_mode": False
    })


def test_living_map_evidence_schema_uses_real_relocated_angle_transits():
    natal_payload = get_dummy_payload()
    destination = {"display_name": "Chicago", "latitude": 41.8781, "longitude": -87.6298}
    start_date = "2024-01-01"
    end_date = "2025-01-01"
    natal_before = deepcopy(natal_payload)

    evidence = build_living_map_evidence(natal_payload, destination, start_date, end_date)

    assert natal_payload == natal_before
    assert evidence["formula_version"] == "living_map_v0.2.0"
    assert evidence["destination"]["display_name"] == "Chicago"
    assert evidence["date_range"] == {"start_date": start_date, "end_date": end_date}
    assert "static_baseline" in evidence
    assert evidence["timing_windows"]
    assert evidence["appendix_trace"]["methodology"].startswith("Daily noon UTC scan")

    window = evidence["timing_windows"][0]
    assert window["active_planet"] in evidence["appendix_trace"]["transit_bodies"]
    assert window["event_type"] == "transit_to_relocated_angle"
    assert window["target"] in {"Ascendant", "Midheaven", "Descendant", "Imum_Coeli"}
    assert window["target_evidence_id"].startswith("relocated_angle:")
    assert window["start_date"] <= window["exact_date"] <= window["end_date"]
    assert window["strength"] in {"high", "medium", "low"}
    assert "temporar" in window["temporary_weather_note"]


def test_living_map_assembler_renders_computed_windows():
    natal_payload = get_dummy_payload()
    destination = {"location": "Tokyo, Japan"}

    context = build_living_map_context(
        natal_payload,
        destination,
        purpose_lens="career",
        start_date="2026-08-01",
        end_date="2026-10-01",
    )

    assert context["destination_name"] == "Tokyo, Japan"
    assert context["destination_context"]["latitude"] == 35.6895
    assert context["destination_context"]["longitude"] == 139.6917
    assert context["purpose_lens_label"] == "Career"
    assert context["date_range"] == {"start_date": "2026-08-01", "end_date": "2026-10-01"}

    sections = {s["id"]: s for s in context["sections"]}
    assert "current_place_weather" in sections
    assert "windows_of_emphasis" in sections
    assert "timing_frame" in sections

    weather_count = len(sections["current_place_weather"]["blocks"])
    emphasis_count = len(sections["windows_of_emphasis"]["blocks"])
    assert weather_count + emphasis_count > 0

    timing_frame = sections["timing_frame"]
    assert timing_frame["blocks"][0]["title"] == "Purpose frame"
    assert "The active lens for this reading is Career, over the window from 2026-08-01 through 2026-10-01." in timing_frame["blocks"][0]["leaf"]["body"]
    assert "window ranking is not yet purpose-weighted" in timing_frame["blocks"][0]["leaf"]["note"]

    first_block = (
        sections["current_place_weather"]["blocks"]
        or sections["windows_of_emphasis"]["blocks"]
    )[0]
    assert " on " in first_block["title"]
    assert "temporar" in first_block["leaf"]["note"] or first_block["leaf"]["note"] in {"high", "medium", "low"}
    assert "daily noon UTC" in sections["technical_appendix"]["blocks"][0]["leaf"]["body"]
    assert not any(section.get("is_future_method") for section in context["sections"])
