import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import generate
from product_versions import report_version, template_path
from products.location_services import routing


def test_location_report_type_aliases_round_trip():
    assert routing.is_location_report_type("place_resonance")
    assert routing.is_location_report_type("location_services.place_resonance")
    assert routing.resolve_location_report_type("place_resonance") == "location_services.place_resonance"
    assert routing.public_location_report_type("location_services.world_lines") == "world_lines"


def test_build_location_report_artifacts_routes_search_context(monkeypatch):
    calls: list[tuple[str, tuple, dict]] = []

    class FakeSearchProduct:
        def build_search_context(self, *args, **kwargs):
            calls.append(("build_search_context", args, kwargs))
            return {"report_type": "location_services.place_resonance_search", "selected_locations": []}

        def render_html(self, context):
            calls.append(("render_html", (context,), {}))
            return "<html>search</html>"

    monkeypatch.setattr(routing, "get_location_product", lambda report_type: FakeSearchProduct())

    artifacts = routing.build_location_report_artifacts(
        "place_resonance_search",
        {"payload": True},
        {"purpose_lens": "career", "relationship_to_place": "possible_move", "selection_limit": 7},
    )

    assert artifacts["public_report_type"] == "place_resonance_search"
    assert artifacts["full_report_type"] == "location_services.place_resonance_search"
    assert calls[0][0] == "build_search_context"
    assert calls[0][2]["purpose_lens"] == "career"
    assert calls[0][2]["relationship_to_place"] == "possible_move"
    assert calls[0][2]["selection_limit"] == 7
    assert artifacts["html"] == "<html>search</html>"


def test_generate_report_location_branch_writes_manifest(monkeypatch, tmp_path: Path):
    manifest_calls = []

    monkeypatch.setattr(generate, "get_payload", lambda birth_data: {"payload": True})
    monkeypatch.setattr(
        generate,
        "build_location_report_artifacts",
        lambda report_type, payload, birth_data: {
            "public_report_type": "place_resonance",
            "full_report_type": "location_services.place_resonance",
            "context": {"report_type": "location_services.place_resonance"},
            "html": "<html><body>location</body></html>",
        },
    )

    def fake_manifest(**kwargs):
        manifest_calls.append(kwargs)
        manifest_path = tmp_path / "sample.manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")
        return str(manifest_path)

    monkeypatch.setattr(generate, "_write_report_manifest", fake_manifest)

    output_path = generate.generate_report(
        "place_resonance",
        {
            "name": "Smoke",
            "date": "1990-01-01",
            "time": "12:00",
            "location": "New York",
            "current_location": "New York",
            "destination": "Tokyo, Japan",
        },
        output_filename="sample.html",
        output_dir=str(tmp_path),
    )

    assert Path(output_path).exists()
    assert Path(output_path).name == "sample.html"
    assert manifest_calls
    assert manifest_calls[0]["report_type"] == "place_resonance"
    assert manifest_calls[0]["standard_report_bundle"] == {}


def test_build_location_report_artifacts_routes_local_compass_specific_inputs(monkeypatch):
    calls: list[tuple[str, tuple, dict]] = []

    class FakeCompassProduct:
        def build_context(self, *args, **kwargs):
            calls.append(("build_context", args, kwargs))
            return {"report_type": "location_services.local_compass", "sections": []}

        def render_html(self, context):
            calls.append(("render_html", (context,), {}))
            return "<html>compass</html>"

    route = {
        "route_id": "chi-mke",
        "corridor_width_km": 120.0,
        "waypoints": [
            {"latitude": 41.8781, "longitude": -87.6298},
            {"latitude": 42.3314, "longitude": -87.8601},
        ],
    }
    monkeypatch.setattr(routing, "get_location_product", lambda report_type: FakeCompassProduct())

    artifacts = routing.build_location_report_artifacts(
        "local_compass",
        {"payload": True},
        {
            "anchor_location": "Chicago, IL",
            "destination": "Milwaukee, WI",
            "purpose_lens": "study",
            "route": route,
        },
    )

    assert artifacts["public_report_type"] == "local_compass"
    assert calls[0][0] == "build_context"
    assert calls[0][1][1]["location"] == "Chicago, IL"
    assert calls[0][2]["destination"]["location"] == "Milwaukee, WI"
    assert calls[0][2]["route"] == route
    assert calls[0][2]["purpose_lens"] == "study"
    assert artifacts["html"] == "<html>compass</html>"


def test_location_report_window_uses_explicit_living_map_end_date():
    start, end = routing.location_report_window(
        "living_map",
        {
            "report_date": "2026-07-25",
            "report_end_date": "2026-10-01",
        },
    )

    assert start.isoformat().startswith("2026-07-25")
    assert end.isoformat().startswith("2026-10-01")


def test_location_report_versions_and_templates_are_registered():
    assert report_version("place_resonance") == "Place Resonance v0.1"
    assert report_version("location_services.local_compass") == "Local Compass v0.3"
    assert template_path("world_lines").endswith("products\\location_services\\templates\\world_lines.html")
    assert template_path("location_services.place_resonance_search").endswith(
        "products\\location_services\\place_resonance_search\\renderer.py"
    )
