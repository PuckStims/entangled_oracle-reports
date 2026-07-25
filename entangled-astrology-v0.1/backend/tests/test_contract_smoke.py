from __future__ import annotations

from fastapi.testclient import TestClient

from entangled_mobile_backend.main import app


client = TestClient(app)


PROFILE = {
    "id": "smoke",
    "displayName": "Adapter Smoke",
    "localDate": "1990-06-15",
    "localTime": "08:30",
    "timeZoneId": "America/Chicago",
    "locationName": "Peoria, IL",
    "birthTimeConfidence": "EXACT_RECALLED",
}


def test_health_identity_capabilities() -> None:
    assert client.get("/v1/health").json()["status"] == "ok"
    identity = client.get("/v1/engine/identity").json()
    assert identity["engine"] == "Entangled Oracle"
    capabilities = client.get("/v1/capabilities").json()
    assert "natal_chart" in capabilities["supportedTechniques"]
    assert "current_field" in capabilities["supportedTechniques"]
    assert "timeline" in capabilities["supportedTechniques"]
    assert "horoscope" in capabilities["supportedReports"]


def test_profile_validation_normalizes_location_from_engine() -> None:
    response = client.post("/v1/profiles/validate", json={"profile": PROFILE})
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["normalizedProfile"]["timeZoneId"] == "America/Chicago"
    assert payload["normalizedProfile"]["coordinates"]["latitude"]


def test_natal_chart_uses_engine_payload_shape() -> None:
    response = client.post("/v1/charts/natal", json={"profile": PROFILE})
    assert response.status_code == 200
    payload = response.json()
    assert payload["zodiac"] == "Tropical"
    assert payload["houseSystem"] == "Whole Sign"
    assert any(item["body"] == "Sun" for item in payload["placements"])
    assert payload["provenance"]["calculationModules"]


def test_current_field_patterns_reference_returned_events() -> None:
    response = client.post("/v1/fields/current", json={"profile": PROFILE, "moment": "2026-07-18T12:00:00Z"})
    assert response.status_code == 200
    payload = response.json()
    event_ids = {event["id"] for event in payload["events"]}
    assert event_ids
    assert payload["provenance"]["calculationModules"]
    for pattern in payload["patterns"]:
        assert pattern["eventIds"]
        assert set(pattern["eventIds"]).issubset(event_ids)


def test_timeline_returns_calculated_events_with_provenance() -> None:
    response = client.post(
        "/v1/timelines/calculate",
        json={"profile": PROFILE, "start": "2026-07-18", "end": "2026-07-20"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["timeZone"] == "America/Chicago"
    assert payload["provenance"]["calculationModules"]
    assert len({event["id"] for event in payload["events"]}) == len(payload["events"])
