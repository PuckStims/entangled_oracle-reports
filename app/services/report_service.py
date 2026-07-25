"""Report Studio boundary around the existing Entangled Oracle generator."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import traceback

from generate import InputValidationError, generate_report

from .report_registry import get_report_definition
from .session_store import create_session_dir, manifest_path, write_json


@dataclass(frozen=True)
class ReportRequest:
    report_type: str
    name: str
    birth_date: str
    birth_time: str | None
    location: str
    destination: str | None = None
    anchor_location: str | None = None
    report_date: str | None = None
    report_end_date: str | None = None
    purpose_lens: str | None = None
    relationship_to_place: str | None = None
    route_waypoints: str | None = None
    route_corridor_km: str | None = None
    route_id: str | None = None
    palette: str = "vibrant"
    content_pack: str = "plainspeak"
    consent_acknowledged: bool = False


@dataclass(frozen=True)
class ReportResult:
    session_id: str
    report_type: str
    html_path: Path
    manifest_path: Path | None
    created_at: datetime


class WebInputError(ValueError):
    """Friendly input error for the browser flow."""


def _require(value: str | None, message: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise WebInputError(message)
    return cleaned


def _validate_yyyy_mm_dd(value: str, label: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise WebInputError(f"Please enter {label} as YYYY-MM-DD.") from None
    return value


def _validate_time(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    time_format = "%H:%M:%S" if cleaned.count(":") == 2 else "%H:%M"
    try:
        datetime.strptime(cleaned, time_format)
    except ValueError:
        raise WebInputError("Please enter birth time as HH:MM, or choose a report that supports unknown time.") from None
    return cleaned


def _normalize_optional_text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _parse_route_waypoints(value: str | None) -> list[dict[str, float]] | None:
    if not value:
        return None
    waypoints: list[dict[str, float]] = []
    for chunk in value.split(";"):
        text = chunk.strip()
        if not text:
            continue
        parts = [part.strip() for part in text.split(",")]
        if len(parts) != 2:
            raise WebInputError("Route waypoints must use 'lat,lon;lat,lon;...' format.")
        try:
            latitude = float(parts[0])
            longitude = float(parts[1])
        except ValueError:
            raise WebInputError("Route waypoints must contain numeric latitude/longitude pairs.") from None
        waypoints.append({"latitude": latitude, "longitude": longitude})
    if len(waypoints) < 2:
        raise WebInputError("Route waypoints require at least two coordinate pairs.")
    return waypoints


def _validate_route_corridor_km(value: str | None) -> str | None:
    cleaned = _normalize_optional_text(value)
    if cleaned is None:
        return None
    try:
        numeric = float(cleaned)
    except ValueError:
        raise WebInputError("Route corridor width must be a number in kilometers.") from None
    if numeric <= 0:
        raise WebInputError("Route corridor width must be greater than zero.")
    return cleaned


def validate_report_request(request: ReportRequest) -> ReportRequest:
    definition = get_report_definition(request.report_type)
    if definition is None:
        raise WebInputError("That report type is not part of the beta studio.")
    if not definition.available:
        raise WebInputError(f"{definition.label} is not exposed in the beta studio yet.")

    name = _require(request.name, "Please enter a display name for the report.")
    birth_date = _validate_yyyy_mm_dd(_require(request.birth_date, "Please enter a birth date."), "birth date")
    birth_time = _validate_time(request.birth_time)
    location = _require(request.location, "Please enter a birth location.")
    destination = _normalize_optional_text(request.destination)
    anchor_location = _normalize_optional_text(request.anchor_location)
    report_date = _normalize_optional_text(request.report_date)
    report_end_date = _normalize_optional_text(request.report_end_date)
    purpose_lens = _normalize_optional_text(request.purpose_lens)
    relationship_to_place = _normalize_optional_text(request.relationship_to_place)
    route_waypoints = _normalize_optional_text(request.route_waypoints)
    route_corridor_km = _validate_route_corridor_km(request.route_corridor_km)
    route_id = _normalize_optional_text(request.route_id)
    if report_date:
        report_date = _validate_yyyy_mm_dd(report_date, "the report start date")
    if report_end_date:
        report_end_date = _validate_yyyy_mm_dd(report_end_date, "the report end date")
    if report_date and report_end_date and report_end_date < report_date:
        raise WebInputError("Report end date must be the same day or later than the report start date.")
    palette = request.palette if request.palette in {"vibrant", "muted"} else "vibrant"
    content_pack = request.content_pack if request.content_pack in definition.content_packs else definition.default_content_pack

    if not birth_time and not definition.allow_unknown_time:
        raise WebInputError(f"{definition.label} requires an exact birth time for this beta studio flow.")
    if definition.needs_destination:
        destination = _require(destination, f"Please enter a {definition.destination_label.lower()} for {definition.label}.")
    if definition.needs_anchor:
        anchor_location = _require(anchor_location, f"Please enter an {definition.anchor_label.lower()} for {definition.label}.")
    if route_waypoints:
        _parse_route_waypoints(route_waypoints)
    if not request.consent_acknowledged:
        raise WebInputError("Please acknowledge the local/private beta handling note before generating.")

    return ReportRequest(
        report_type=request.report_type,
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        location=location,
        destination=destination,
        anchor_location=anchor_location,
        report_date=report_date,
        report_end_date=report_end_date,
        purpose_lens=purpose_lens,
        relationship_to_place=relationship_to_place,
        route_waypoints=route_waypoints,
        route_corridor_km=route_corridor_km,
        route_id=route_id,
        palette=palette,
        content_pack=content_pack,
        consent_acknowledged=True,
    )


def create_report(request: ReportRequest) -> ReportResult:
    validated = validate_report_request(request)
    session_id, session_dir = create_session_dir()
    write_json(
        session_dir / "request.json",
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "request": asdict(validated),
            "privacy_note": "Local beta session metadata; not suitable for public hosting.",
        },
    )

    birth_data = {
        "name": validated.name,
        "date": validated.birth_date,
        "time": validated.birth_time,
        "location": validated.location,
        "current_location": validated.location,
        "simple_mode": validated.birth_time is None,
        "palette": validated.palette,
        "report_date": validated.report_date,
        "report_end_date": validated.report_end_date,
        "destination": validated.destination,
        "anchor_location": validated.anchor_location,
        "purpose_lens": validated.purpose_lens,
        "relationship_to_place": validated.relationship_to_place,
    }
    route_waypoints = _parse_route_waypoints(validated.route_waypoints)
    if route_waypoints:
        birth_data["route"] = {
            "route_id": validated.route_id or "studio-route",
            "corridor_width_km": float(validated.route_corridor_km or "150"),
            "waypoints": route_waypoints,
        }

    try:
        html_path = Path(
            generate_report(
                validated.report_type,
                birth_data,
                output_filename="report.html",
                content_pack=validated.content_pack,
                output_dir=str(session_dir),
            )
        )
    except InputValidationError as exc:
        raise WebInputError(str(exc)) from exc
    except Exception as exc:
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        friendly = _friendly_generation_error(exc)
        raise WebInputError(friendly) from exc

    return ReportResult(
        session_id=session_id,
        report_type=validated.report_type,
        html_path=html_path,
        manifest_path=manifest_path(session_id),
        created_at=datetime.now(timezone.utc),
    )


def _friendly_generation_error(exc: Exception) -> str:
    name = exc.__class__.__name__
    message = str(exc).strip()
    if name in {"LocationResolutionError", "ChartCalculationError"} and message:
        return message
    if message and ("location" in message.lower() or "birth" in message.lower()):
        return message
    return "The report could not be generated. Please check the birth details and try again."
