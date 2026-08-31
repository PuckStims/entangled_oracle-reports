from argparse import Namespace

import pytest

from engine.report_inputs import (
    InputValidationError,
    parse_birth_data,
    parse_route_waypoints,
    validate_iso_date,
)


def _args(**overrides):
    values = {
        "name": " Rowan ",
        "date": "1992-03-21",
        "time": "08:11",
        "location": "Peoria, IL",
        "simple": False,
        "palette": "vibrant",
        "include_debug_json": False,
        "include_practitioner_appendix": False,
        "report_date": "2026-01-01",
        "report_end_date": None,
        "destination": None,
        "anchor_location": None,
        "purpose_lens": None,
        "relationship_to_place": None,
        "route_waypoints": None,
        "route_id": None,
        "route_corridor_km": 150.0,
        "sample_identity_mode": None,
        "sample_display_name": None,
    }
    values.update(overrides)
    return Namespace(**values)


def test_parse_birth_data_keeps_exact_time_when_supplied():
    birth_data = parse_birth_data(_args())

    assert birth_data["name"] == "Rowan"
    assert birth_data["date"] == "1992-03-21"
    assert birth_data["time"] == "08:11"
    assert birth_data["simple_mode"] is False
    assert birth_data["report_date"] == "2026-01-01"


def test_parse_birth_data_defaults_to_simple_mode_without_time():
    birth_data = parse_birth_data(_args(time=None))

    assert birth_data["time"] is None
    assert birth_data["simple_mode"] is True


def test_parse_birth_data_rejects_invalid_time():
    with pytest.raises(InputValidationError, match="valid 24-hour time"):
        parse_birth_data(_args(time="25:99"))


def test_parse_birth_data_rejects_end_date_before_start_date():
    with pytest.raises(InputValidationError, match="same day or later"):
        parse_birth_data(_args(report_date="2026-02-02", report_end_date="2026-02-01"))


def test_parse_route_waypoints_builds_coordinate_records():
    assert parse_route_waypoints("40.1,-89.5;41.8,-87.6") == [
        {"latitude": 40.1, "longitude": -89.5},
        {"latitude": 41.8, "longitude": -87.6},
    ]


def test_parse_route_waypoints_rejects_single_point():
    with pytest.raises(InputValidationError, match="at least two"):
        parse_route_waypoints("40.1,-89.5")


def test_validate_iso_date_rejects_invalid_date():
    with pytest.raises(InputValidationError, match="YYYY-MM-DD"):
        validate_iso_date("2026-02-31", "--report-date")
