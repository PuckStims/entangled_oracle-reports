import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.report_service import ReportRequest, WebInputError, validate_report_request
from generate import InputValidationError, parse_birth_data


def test_validate_report_request_accepts_local_compass_anchor_and_route():
    request = ReportRequest(
        report_type="local_compass",
        name="Aster",
        birth_date="1990-01-01",
        birth_time="12:00",
        location="Chicago, IL",
        anchor_location="Chicago, IL",
        destination="Milwaukee, WI",
        purpose_lens="study",
        route_waypoints="41.8781,-87.6298;42.3314,-87.8601",
        route_corridor_km="120",
        route_id="chi-mke",
        consent_acknowledged=True,
    )

    validated = validate_report_request(request)

    assert validated.anchor_location == "Chicago, IL"
    assert validated.destination == "Milwaukee, WI"
    assert validated.purpose_lens == "study"
    assert validated.route_waypoints == "41.8781,-87.6298;42.3314,-87.8601"
    assert validated.route_corridor_km == "120"
    assert validated.route_id == "chi-mke"


def test_validate_report_request_rejects_end_date_before_start():
    request = ReportRequest(
        report_type="living_map",
        name="Aster",
        birth_date="1990-01-01",
        birth_time="12:00",
        location="Chicago, IL",
        destination="Tokyo, Japan",
        report_date="2026-07-25",
        report_end_date="2026-07-24",
        consent_acknowledged=True,
    )

    with pytest.raises(WebInputError, match="Report end date must be the same day or later"):
        validate_report_request(request)


def test_validate_report_request_accepts_between_places_destinations():
    request = ReportRequest(
        report_type="between_places",
        name="Aster",
        birth_date="1990-01-01",
        birth_time="12:00",
        location="Chicago, IL",
        destination_a="Lisbon, Portugal",
        destination_b="Kyoto, Japan",
        purpose_lens="belonging",
        consent_acknowledged=True,
    )

    validated = validate_report_request(request)

    assert validated.destination == "Lisbon, Portugal"
    assert validated.destination_a == "Lisbon, Portugal"
    assert validated.destination_b == "Kyoto, Japan"
    assert validated.purpose_lens == "belonging"


def test_parse_birth_data_accepts_location_service_cli_fields():
    args = SimpleNamespace(
        name="Aster",
        date="1990-01-01",
        time="12:00",
        location="Chicago, IL",
        simple=False,
        palette="vibrant",
        report_date="2026-07-25",
        report_end_date="2026-10-01",
        destination="Tokyo, Japan",
        anchor_location="Chicago, IL",
        purpose_lens="career",
        relationship_to_place="possible_move",
        route_waypoints="41.8781,-87.6298;42.3314,-87.8601",
        route_corridor_km=120.0,
        route_id="chi-mke",
    )

    birth_data = parse_birth_data(args)

    assert birth_data["report_date"] == "2026-07-25"
    assert birth_data["report_end_date"] == "2026-10-01"
    assert birth_data["destination"] == "Tokyo, Japan"
    assert birth_data["anchor_location"] == "Chicago, IL"
    assert birth_data["purpose_lens"] == "career"
    assert birth_data["relationship_to_place"] == "possible_move"
    assert birth_data["route"]["route_id"] == "chi-mke"


def test_parse_birth_data_rejects_end_date_before_start():
    args = SimpleNamespace(
        name="Aster",
        date="1990-01-01",
        time="12:00",
        location="Chicago, IL",
        simple=False,
        palette="vibrant",
        report_date="2026-07-25",
        report_end_date="2026-07-24",
        destination=None,
        anchor_location=None,
        purpose_lens=None,
        relationship_to_place=None,
        route_waypoints=None,
        route_corridor_km=150.0,
        route_id=None,
    )

    with pytest.raises(InputValidationError, match="same day or later"):
        parse_birth_data(args)
