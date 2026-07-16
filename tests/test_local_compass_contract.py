from engine.local_space import build_local_space_evidence, _rank_directions
from products.location_services.local_compass.assembler import build_local_compass_context
from test_location_services_relocated_payload import _build_natal_payload


def test_local_space_evidence_schema_uses_real_azimuths():
    natal_payload = _build_natal_payload()
    anchor = {"display_name": "New York", "latitude": 40.7128, "longitude": -74.0060}
    destination = {"display_name": "Boston", "latitude": 42.3601, "longitude": -71.0589}
    route = {
        "route_id": "nyc-boston",
        "corridor_width_km": 180.0,
        "waypoints": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 41.3083, "longitude": -72.9279},
            {"latitude": 42.3601, "longitude": -71.0589},
        ],
    }

    evidence = build_local_space_evidence(natal_payload, anchor, destination, route)

    assert evidence["formula_version"] == "local_space_v0.3.0"
    assert evidence["anchor_context"] == anchor
    assert evidence["destination_context"] == destination
    assert evidence["route_context"] == route
    assert evidence["directions"]
    assert evidence["appendix_trace"]["azimuth_convention"].startswith("0 degrees")
    assert evidence["unsupported_methods"] == []
    assert "weighting_policy" in evidence["appendix_trace"]
    assert "route_geometry_policy" in evidence["appendix_trace"]

    previous_score = None
    seen_ranks = []
    for direction in evidence["directions"]:
        assert direction["body"] in natal_payload["standard_planets"]
        assert 0 <= direction["azimuth"] < 360
        assert -90 <= direction["altitude"] <= 90
        assert direction["direction_label"]
        assert direction["cross_track_distance_km"] is not None
        assert direction["cross_track_distance_km"] >= 0
        assert direction["practical_mode"]
        assert 0.0 <= direction["weighted_score"] <= 1.0
        assert set(direction["raw_inputs"]) == {
            "altitude_relevance",
            "angular_relevance",
            "natal_condition",
            "destination_alignment",
        }
        assert set(direction["weight_components"]) == set(direction["raw_inputs"])
        seen_ranks.append(direction["rank"])
        assert direction["route_geometry"] is not None
        assert direction["route_geometry"]["route_id"] == "nyc-boston"
        assert direction["route_geometry"]["minimum_offset_km"] >= 0
        assert direction["route_geometry"]["overlap_length_km"] >= 0
        assert direction["route_geometry"]["strength"] in {"high", "medium", "low"}
        if previous_score is not None:
            assert direction["weighted_score"] <= previous_score
        previous_score = direction["weighted_score"]

    assert seen_ranks == list(range(1, len(evidence["directions"]) + 1))


def test_local_space_anchor_only_has_no_fake_route_geometry():
    natal_payload = _build_natal_payload()
    anchor = {"display_name": "New York", "latitude": 40.7128, "longitude": -74.0060}

    evidence = build_local_space_evidence(natal_payload, anchor)

    assert evidence["route_context"] == {}
    assert evidence["unsupported_methods"] == []
    assert all(direction["route_geometry"] is None for direction in evidence["directions"])


def test_local_space_ranking_tie_break_is_body_name_stable():
    directions = [
        {
            "id": "direction:Venus",
            "body": "Venus",
            "azimuth": 50.0,
            "altitude": 10.0,
            "direction_label": "Northeast",
            "cross_track_distance_km": 10.0,
            "bearing_to_destination": 20.0,
            "natal_condition": {},
            "practical_mode": "Relationship",
            "raw_inputs": {},
            "weight_components": {},
            "weighted_score": 0.75,
            "rank": 0,
        },
        {
            "id": "direction:Mercury",
            "body": "Mercury",
            "azimuth": 10.0,
            "altitude": 5.0,
            "direction_label": "North",
            "cross_track_distance_km": 10.0,
            "bearing_to_destination": 20.0,
            "natal_condition": {},
            "practical_mode": "Study",
            "raw_inputs": {},
            "weight_components": {},
            "weighted_score": 0.75,
            "rank": 0,
        },
    ]

    ranked = _rank_directions(directions)

    assert [item["body"] for item in ranked] == ["Mercury", "Venus"]
    assert [item["rank"] for item in ranked] == [1, 2]


def test_local_compass_assembler_renders_computed_directions():
    natal_payload = _build_natal_payload()
    anchor = {
        "location": "Tokyo, Japan",
        "route": {
            "route_id": "tokyo-loop",
            "corridor_width_km": 120.0,
            "waypoints": [
                {"latitude": 35.6895, "longitude": 139.6917},
                {"latitude": 35.6762, "longitude": 139.6503},
                {"latitude": 35.6586, "longitude": 139.7454},
            ],
        },
    }

    context = build_local_compass_context(natal_payload, anchor)

    assert context["destination_name"] == "Tokyo, Japan"
    assert context["destination_context"]["latitude"] == 35.6895
    assert context["destination_context"]["longitude"] == 139.6917

    sections = {s["id"]: s for s in context["sections"]}
    assert "planetary_directions" in sections

    directions = sections["planetary_directions"]
    assert directions["blocks"]
    assert " towards " in directions["blocks"][0]["title"]
    assert "score" in directions["blocks"][0]["leaf"]["note"]
    assert "Rank 1" in directions["blocks"][0]["leaf"]["body"]

    relationship = sections["destination_relationship"]
    assert relationship["blocks"]
    assert relationship["blocks"][0]["title"].startswith("Distance to ")
    assert "destination bearing" in relationship["blocks"][0]["leaf"]["body"]

    route = sections["route_relationship"]
    assert route["present"] is True
    assert route["blocks"]
    assert "Route alignment" in route["blocks"][0]["title"]
    assert "route" in route["blocks"][0]["leaf"]["body"].lower()

    assert "direction-strength weighting" in sections["technical_appendix"]["blocks"][0]["leaf"]["note"]
    assert not any(section.get("is_future_method") for section in context["sections"])
