"""CLI input parsing helpers for report generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class InputValidationError(ValueError):
    """Raised when CLI-supplied birth data is malformed."""


def normalize_optional_text(value: str | None) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def validate_iso_date(value: str | None, flag_name: str) -> str | None:
    cleaned = normalize_optional_text(value)
    if cleaned is None:
        return None
    try:
        datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError:
        raise InputValidationError(
            f"{flag_name} '{cleaned}' is not a valid date in YYYY-MM-DD format."
        ) from None
    return cleaned


def parse_route_waypoints(value: str | None) -> list[dict] | None:
    if not value:
        return None
    waypoints: list[dict] = []
    for chunk in value.split(";"):
        text = chunk.strip()
        if not text:
            continue
        parts = [part.strip() for part in text.split(",")]
        if len(parts) != 2:
            raise InputValidationError(
                "--route-waypoints must use 'lat,lon;lat,lon;...' format."
            )
        try:
            latitude = float(parts[0])
            longitude = float(parts[1])
        except ValueError:
            raise InputValidationError(
                "--route-waypoints must contain numeric latitude/longitude pairs."
            ) from None
        waypoints.append({"latitude": latitude, "longitude": longitude})
    if len(waypoints) < 2:
        raise InputValidationError(
            "--route-waypoints requires at least two waypoint pairs."
        )
    return waypoints


def parse_birth_data(args: Any) -> dict:
    """Parse CLI arguments into a birth-data dict."""
    name = args.name
    if not name or not name.strip():
        raise InputValidationError("--name cannot be empty or whitespace-only.")
    name = name.strip()

    sample_identity_mode = getattr(args, "sample_identity_mode", None)
    sample_display_name = (
        getattr(args, "sample_display_name", None) or "Sample Client"
    ).strip() or "Sample Client"
    report_display_name = sample_display_name if sample_identity_mode == "anonymized" else name

    date_string = args.date
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise InputValidationError(
            f"--date '{date_string}' is not a valid date in YYYY-MM-DD format."
        ) from None

    birth_data = {
        "name": report_display_name,
        "date": date_string,
        "location": args.location or "",
        "simple_mode": getattr(args, "simple", False),
        "sample_identity_mode": sample_identity_mode,
        "sample_display_name": sample_display_name,
    }
    if not birth_data["location"].strip():
        raise InputValidationError("--location is required and cannot be empty.")
    if hasattr(args, "time") and args.time and not birth_data["simple_mode"]:
        time_string = args.time
        time_format = "%H:%M:%S" if time_string.count(":") == 2 else "%H:%M"
        try:
            datetime.strptime(time_string, time_format)
        except ValueError:
            raise InputValidationError(
                f"--time '{time_string}' is not a valid 24-hour time in HH:MM or HH:MM:SS format."
            ) from None
        birth_data["time"] = time_string
    else:
        birth_data["time"] = None
        birth_data["simple_mode"] = True
    birth_data["palette"] = getattr(args, "palette", "vibrant")
    birth_data["include_debug_json"] = bool(getattr(args, "include_debug_json", False))
    birth_data["include_practitioner_appendix"] = bool(
        getattr(args, "include_practitioner_appendix", False)
    )
    birth_data["report_date"] = validate_iso_date(
        getattr(args, "report_date", None),
        "--report-date",
    )
    birth_data["report_end_date"] = validate_iso_date(
        getattr(args, "report_end_date", None),
        "--report-end-date",
    )
    report_start = datetime.strptime(
        birth_data["report_date"] or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "%Y-%m-%d",
    )
    if birth_data["report_end_date"]:
        report_end = datetime.strptime(birth_data["report_end_date"], "%Y-%m-%d")
        if report_end < report_start:
            raise InputValidationError(
                "--report-end-date must be the same day or later than --report-date."
            )
    birth_data["destination"] = normalize_optional_text(getattr(args, "destination", None))
    birth_data["anchor_location"] = normalize_optional_text(
        getattr(args, "anchor_location", None)
    )
    birth_data["purpose_lens"] = normalize_optional_text(getattr(args, "purpose_lens", None))
    birth_data["relationship_to_place"] = normalize_optional_text(
        getattr(args, "relationship_to_place", None)
    )
    route_waypoints = parse_route_waypoints(getattr(args, "route_waypoints", None))
    if route_waypoints:
        birth_data["route"] = {
            "route_id": getattr(args, "route_id", None) or "cli-route",
            "corridor_width_km": float(
                getattr(args, "route_corridor_km", 150.0) or 150.0
            ),
            "waypoints": route_waypoints,
        }
    return birth_data


def parse_synastry_party_data(args: Any, suffix: str) -> dict:
    name = getattr(args, f"name{suffix}", None)
    if not name or not str(name).strip():
        raise InputValidationError(f"--name{suffix} cannot be empty or whitespace-only.")

    date_string = getattr(args, f"date{suffix}", None)
    if not date_string:
        raise InputValidationError(f"--date{suffix} is required for synastry.")
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise InputValidationError(
            f"--date{suffix} '{date_string}' is not a valid date in YYYY-MM-DD format."
        ) from None

    location = getattr(args, f"location{suffix}", None)
    if not location or not str(location).strip():
        raise InputValidationError(f"--location{suffix} is required for synastry.")

    simple_mode = bool(getattr(args, f"simple{suffix}", False))
    birth_data = {
        "name": name,
        "date": date_string,
        "location": location,
        "simple_mode": simple_mode,
        "palette": getattr(args, "palette", "vibrant"),
    }

    time_string = getattr(args, f"time{suffix}", None)
    if time_string:
        time_format = "%H:%M:%S" if str(time_string).count(":") == 2 else "%H:%M"
        try:
            datetime.strptime(time_string, time_format)
        except ValueError:
            raise InputValidationError(
                f"--time{suffix} '{time_string}' is not a valid 24-hour time in HH:MM or HH:MM:SS format."
            ) from None
        birth_data["time"] = time_string
        birth_data["simple_mode"] = False
    else:
        birth_data["time"] = None
        birth_data["simple_mode"] = True

    return birth_data
