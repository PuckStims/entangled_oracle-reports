from __future__ import annotations

import importlib
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


SCHEMA_VERSION = "1.0.0"
ENGINE_NAME = "Entangled Oracle"
ENGINE_ROOT = Path(os.environ.get("EO_ENGINE_ROOT", Path(__file__).resolve().parents[3])).resolve()
STANDARD_BODY_ORDER = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Chiron",
    "North_Node",
    "South_Node",
    "Lilith_BML",
]
MAX_TIMELINE_DAYS = 120


class BridgeError(ValueError):
    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_datetime(value: str, *, field: str) -> datetime:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise BridgeError(f"{field} is required.", field=field)
    if cleaned.endswith("Z"):
        cleaned = f"{cleaned[:-1]}+00:00"
    try:
        moment = datetime.fromisoformat(cleaned)
    except ValueError:
        raise BridgeError(f"{field} must be an ISO-8601 date-time.", field=field) from None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _parse_date(value: str, *, field: str) -> date:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise BridgeError(f"{field} is required.", field=field)
    try:
        return date.fromisoformat(cleaned)
    except ValueError:
        raise BridgeError(f"{field} must be YYYY-MM-DD.", field=field) from None


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return None


def _event_sort_moment(event: dict[str, Any]) -> datetime:
    for key in ("peak_at", "peak_datetime", "exact_at", "entry_datetime", "start_at"):
        value = event.get(key)
        if isinstance(value, list):
            value = value[0] if value else None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.max.replace(tzinfo=timezone.utc)


def _event_score(event: dict[str, Any]) -> float:
    for key in ("event_strength", "combined_intensity_score", "score", "raw_score"):
        try:
            return float(event.get(key))
        except (TypeError, ValueError):
            continue
    return 0.0


def _event_phase(event: dict[str, Any], reference: datetime | None = None) -> str:
    if str(event.get("event_type") or "") in {"timeline", "lunation", "eclipse", "station"}:
        return "exact"
    peak = event.get("peak_at") or event.get("peak_datetime")
    start = event.get("start_at") or event.get("entry_datetime")
    end = event.get("end_at") or event.get("leave_datetime")
    if not isinstance(peak, datetime):
        return "background"
    if reference is None:
        return "exact"
    if start and isinstance(start, datetime) and reference < start:
        return "background"
    if end and isinstance(end, datetime) and reference > end:
        return "background"
    if abs((reference - peak).total_seconds()) <= 6 * 3600:
        return "exact"
    return "applying" if reference < peak else "separating"


def _event_title(event: dict[str, Any]) -> str:
    explicit = str(event.get("title") or "").strip()
    if explicit:
        return explicit
    event_type = str(event.get("event_type") or "").strip()
    planet = str(event.get("transit_planet") or event.get("source_body") or "").strip()
    aspect = str(event.get("aspect") or "").strip()
    target = str(event.get("natal_target") or event.get("target_body") or event.get("natal_contact") or "").strip()
    station = str(event.get("station_type") or "").strip()
    lunation = str(event.get("lunation_type") or event.get("eclipse_type") or "").strip()
    if event_type in {"station"} and planet:
        return f"{planet} stations {station}".strip()
    if event_type in {"lunation", "eclipse"}:
        return f"{lunation or event_type.title()} in {event.get('lunation_sign') or event.get('eclipse_sign') or 'the sky'}"
    if planet and aspect and target:
        return f"{planet} {aspect} natal {target}"
    if planet and target:
        return f"{planet} activates natal {target}"
    return event_type.replace("_", " ").title() or "Calculated event"


def _event_life_areas(event: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("topic_keys", "domain_keys", "shared_life_domains"):
        raw = event.get(key)
        if isinstance(raw, str) and raw:
            values.append(raw)
        elif isinstance(raw, (list, tuple, set)):
            values.extend(str(item) for item in raw if item not in (None, ""))
    house = event.get("natal_house") or event.get("whole_sign_house") or event.get("house_number")
    if house:
        values.append(f"house_{house}")
    return sorted(set(values))


def _event_id(event: dict[str, Any], fallback_index: int) -> str:
    existing = str(event.get("event_id") or "").strip()
    if existing:
        return existing
    adapter = importlib.import_module("engine.forecast_event_adapter")
    normalized = adapter.normalize_to_forecast_event(event)
    return str(normalized.get("event_id") or f"event_{fallback_index}")


def _calculated_event(event: dict[str, Any], index: int, *, reference: datetime | None = None) -> dict[str, Any]:
    event_id = _event_id(event, index)
    exact_values = event.get("exact_at") if isinstance(event.get("exact_at"), list) else []
    exact_at = _iso(exact_values[0]) if exact_values else _iso(event.get("peak_at") or event.get("peak_datetime"))
    return {
        "id": event_id,
        "technique": str(event.get("method_variant") or event.get("event_type") or "forecast_event"),
        "movingBody": str(event.get("transit_planet") or event.get("source_body") or "") or None,
        "natalTarget": str(event.get("natal_target") or event.get("target_body") or event.get("natal_contact") or "sky"),
        "aspect": str(event.get("aspect") or "") or None,
        "orbDegrees": float(event.get("orb")) if event.get("orb") is not None else None,
        "phase": _event_phase(event, reference),
        "startsAt": _iso(event.get("start_at") or event.get("entry_datetime")),
        "exactAt": exact_at,
        "endsAt": _iso(event.get("end_at") or event.get("leave_datetime")),
        "lifeAreas": _event_life_areas(event),
        "birthTimeSensitive": bool(event.get("natal_house") or event.get("whole_sign_house") or event.get("target_kind") == "angle"),
        "title": _event_title(event),
        "interpretation": None,
    }


def _include_angles(payload: dict[str, Any]) -> bool:
    profile = payload.get("user_profile") or {}
    return str(profile.get("birth_time_state") or profile.get("birth_time_confidence") or "") == "exact_birth_time"


def _profile_zone(payload: dict[str, Any], profile: dict[str, Any]) -> ZoneInfo:
    user_profile = payload.get("user_profile") or {}
    name = user_profile.get("timezone") or profile.get("timeZoneId") or "UTC"
    try:
        return ZoneInfo(str(name))
    except Exception:
        return ZoneInfo("UTC")


def install_engine_imports() -> None:
    if not ENGINE_ROOT.exists():
        raise BridgeError(f"EO_ENGINE_ROOT does not exist: {ENGINE_ROOT}")

    selectors_module = sys.modules.get("selectors")
    if selectors_module is not None and not hasattr(selectors_module, "__path__"):
        sys.modules.pop("selectors", None)

    engine_root_text = str(ENGINE_ROOT)
    if engine_root_text not in sys.path:
        sys.path.insert(0, engine_root_text)

    importlib.import_module("selectors")


def pin_ephemeris_path() -> None:
    install_engine_imports()
    try:
        import swisseph as swe
    except ImportError:
        return
    swe.set_ephe_path(str(ENGINE_ROOT / "ephemeris"))


def engine_version() -> str:
    install_engine_imports()
    versions = importlib.import_module("product_versions")
    return getattr(versions, "PRODUCTION_BASELINE_VERSION", "unknown")


def available_report_keys() -> list[str]:
    install_engine_imports()
    registry = importlib.import_module("app.services.report_registry")
    return [report.key for report in registry.available_reports()]


def provenance(
    modules: list[str],
    *,
    content_pack_ids: list[str] | None = None,
    fallback_tier: str | None = None,
    warnings: list[str] | None = None,
    normalization_applied: bool = True,
) -> dict[str, Any]:
    return {
        "engineVersion": engine_version(),
        "schemaVersion": SCHEMA_VERSION,
        "calculationModules": modules,
        "normalizationApplied": normalization_applied,
        "contentPackIds": content_pack_ids or [],
        "fallbackTierUsed": fallback_tier,
        "warnings": warnings or [],
    }


def profile_to_birth_data(profile: dict[str, Any], parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    parameters = parameters or {}
    display_name = str(profile.get("displayName") or "").strip()
    local_date = str(profile.get("localDate") or "").strip()
    local_time = profile.get("localTime")
    location_name = str(profile.get("locationName") or "").strip()
    confidence = str(profile.get("birthTimeConfidence") or "").strip()

    if not display_name:
        raise BridgeError("displayName is required.", field="profile.displayName")
    if not local_date:
        raise BridgeError("localDate is required.", field="profile.localDate")
    try:
        datetime.strptime(local_date, "%Y-%m-%d")
    except ValueError:
        raise BridgeError("localDate must be YYYY-MM-DD.", field="profile.localDate") from None

    cleaned_time = str(local_time).strip() if local_time is not None else None
    if cleaned_time:
        time_format = "%H:%M:%S" if cleaned_time.count(":") == 2 else "%H:%M"
        try:
            datetime.strptime(cleaned_time, time_format)
        except ValueError:
            raise BridgeError("localTime must be HH:MM or HH:MM:SS.", field="profile.localTime") from None

    if not location_name:
        raise BridgeError("locationName is required.", field="profile.locationName")

    simple_mode = not cleaned_time or confidence == "UNKNOWN"
    return {
        "name": display_name,
        "date": local_date,
        "time": None if simple_mode else cleaned_time,
        "location": location_name,
        "current_location": parameters.get("currentLocation") or location_name,
        "simple_mode": simple_mode,
        "palette": parameters.get("palette", "vibrant"),
        "report_date": parameters.get("reportDate"),
        "destination": parameters.get("destination"),
    }


def get_payload_for_profile(profile: dict[str, Any], parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    install_engine_imports()
    pin_ephemeris_path()
    generate = importlib.import_module("generate")
    pin_ephemeris_path()
    return generate.get_payload(profile_to_birth_data(profile, parameters))


def normalized_profile(profile: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    user_profile = payload.get("user_profile") or {}
    coords = user_profile.get("resolved_coordinates") or {}
    result = dict(profile)
    result["locationName"] = user_profile.get("resolved_location") or payload.get("birth_location") or profile.get("locationName")
    result["timeZoneId"] = user_profile.get("timezone") or profile.get("timeZoneId")
    if coords.get("latitude") is not None and coords.get("longitude") is not None:
        result["coordinates"] = {
            "latitude": float(coords["latitude"]),
            "longitude": float(coords["longitude"]),
        }
    return result


def build_natal_chart(request: dict[str, Any]) -> dict[str, Any]:
    profile = request.get("profile") or {}
    house_system = request.get("houseSystem")
    if house_system and house_system.lower().replace("-", " ") not in {"whole sign", "whole"}:
        raise BridgeError("Only Whole Sign houses are exposed by the current engine adapter.", field="houseSystem")

    payload = get_payload_for_profile(profile)
    user_profile = payload.get("user_profile") or {}
    placements = []
    planets = payload.get("standard_planets") or {}
    for body in STANDARD_BODY_ORDER:
        placement = planets.get(body)
        if not isinstance(placement, dict):
            continue
        placements.append(
            {
                "body": body.replace("_", " "),
                "sign": placement.get("sign") or "",
                "degree": float(placement.get("degree_decimal") or 0.0),
                "house": placement.get("house"),
                "retrograde": bool(placement.get("retrograde", False)),
            }
        )

    for angle_name, angle in (payload.get("angles") or {}).items():
        if not isinstance(angle, dict):
            continue
        placements.append(
            {
                "body": angle_name.replace("_", " "),
                "sign": angle.get("sign") or "",
                "degree": float(angle.get("degree_decimal") or 0.0),
                "house": angle.get("house"),
                "retrograde": False,
            }
        )

    aspects = []
    for aspect in payload.get("aspects") or []:
        if not isinstance(aspect, dict):
            continue
        aspects.append(
            {
                "pointA": str(aspect.get("body_1") or "").replace("_", " "),
                "aspect": str(aspect.get("aspect") or ""),
                "pointB": str(aspect.get("body_2") or "").replace("_", " "),
                "orbDegrees": float(aspect.get("orb") or 0.0),
            }
        )

    return {
        "calculatedAt": utc_now(),
        "timeZone": user_profile.get("timezone") or profile.get("timeZoneId") or "UTC",
        "zodiac": user_profile.get("zodiac") or "Tropical",
        "houseSystem": user_profile.get("house_system") or "Whole Sign",
        "placements": placements,
        "aspects": aspects,
        "provenance": provenance(
            ["generate.get_payload", "engine.natal_engine.generate_payload"],
            warnings=[] if placements else ["No natal placements were returned by the engine."],
        ),
    }


def build_current_field(request: dict[str, Any]) -> dict[str, Any]:
    profile = request.get("profile") or {}
    moment = _parse_datetime(str(request.get("moment") or ""), field="moment")
    window = str(request.get("window") or "today")
    payload = get_payload_for_profile(profile)
    zone = _profile_zone(payload, profile)
    local_moment = moment.astimezone(zone)
    if window == "week":
        local_start = datetime.combine(local_moment.date() - timedelta(days=local_moment.weekday()), time.min, zone)
        local_end = local_start + timedelta(days=7)
    elif window == "month":
        local_start = datetime.combine(local_moment.date().replace(day=1), time.min, zone)
        local_end = (local_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        local_start = datetime.combine(local_moment.date(), time.min, zone)
        local_end = local_start + timedelta(days=1)
    window_start = local_start.astimezone(timezone.utc)
    window_end = local_end.astimezone(timezone.utc)

    pin_ephemeris_path()
    transit_engine = importlib.import_module("engine.transit_engine")
    include_angles = _include_angles(payload)
    active = transit_engine.compute_current_transits(payload, moment)
    daily = transit_engine.compute_daily_timeline(
        payload,
        window_start,
        window_end,
        count=5,
        include_angles=include_angles,
        include_slow_planet_peaks=True,
    )
    raw_events = active[:5] + daily[:5]
    raw_events.sort(key=lambda event: (-_event_score(event), _event_sort_moment(event)))
    events = [_calculated_event(event, index, reference=moment) for index, event in enumerate(raw_events)]

    patterns = []
    if events:
        dominant = events[0]
        patterns.append(
            {
                "id": f"pattern_{dominant['id']}",
                "title": dominant["title"] or "Dominant active transit",
                "summary": "Highest-scoring active event from the Entangled Oracle current transit and daily timeline scanners.",
                "role": "dominant",
                "stage": dominant["phase"],
                "eventIds": [dominant["id"]],
                "orientation": [],
            }
        )
    if len(events) > 1:
        support_ids = [event["id"] for event in events[1:4]]
        patterns.append(
            {
                "id": "pattern_supporting_current_events",
                "title": "Supporting active events",
                "summary": "Additional calculated events present in the requested current-field window.",
                "role": "supporting",
                "stage": window,
                "eventIds": support_ids,
                "orientation": [],
            }
        )

    return {
        "fieldId": f"current_{moment.date().isoformat()}_{window}",
        "calculatedAt": utc_now(),
        "timeZone": str(zone.key),
        "windowStart": window_start.isoformat(),
        "windowEnd": window_end.isoformat(),
        "patterns": patterns,
        "events": events,
        "provenance": provenance(
            [
                "generate.get_payload",
                "engine.transit_engine.compute_current_transits",
                "engine.transit_engine.compute_daily_timeline",
                "engine.forecast_event_adapter.normalize_to_forecast_event",
            ],
            warnings=[] if patterns else ["No active current-field events were returned for this profile and window."],
        ),
    }


def build_timeline(request: dict[str, Any]) -> dict[str, Any]:
    profile = request.get("profile") or {}
    start = _parse_date(str(request.get("start") or ""), field="start")
    end = _parse_date(str(request.get("end") or ""), field="end")
    if end < start:
        raise BridgeError("end must be on or after start.", field="end")
    day_count = (end - start).days + 1
    if day_count > MAX_TIMELINE_DAYS:
        raise BridgeError(f"Timeline range is limited to {MAX_TIMELINE_DAYS} days.", field="end")

    payload = get_payload_for_profile(profile)
    zone = _profile_zone(payload, profile)
    start_dt = datetime.combine(start, time.min, zone).astimezone(timezone.utc)
    end_dt = (datetime.combine(end, time.min, zone) + timedelta(days=1)).astimezone(timezone.utc)

    pin_ephemeris_path()
    transit_engine = importlib.import_module("engine.transit_engine")
    timeline = transit_engine.compute_year_ahead_events(
        payload,
        start_dt,
        end_dt,
        step_hours=12,
        include_moon_progressions=day_count <= 120,
        include_year_texture=False,
    )
    raw_events = list(timeline.get("all_events") or [])
    raw_events.sort(key=lambda event: (_event_sort_moment(event), -_event_score(event)))
    events = [_calculated_event(event, index) for index, event in enumerate(raw_events)]

    return {
        "calculatedAt": utc_now(),
        "timeZone": str(zone.key),
        "events": events,
        "provenance": provenance(
            [
                "generate.get_payload",
                "engine.transit_engine.compute_year_ahead_events",
                "engine.forecast_event_adapter.normalize_to_forecast_event",
            ],
            warnings=[] if events else ["No forecast events were returned for the requested timeline range."],
        ),
    }


def create_report_job(request: dict[str, Any]) -> dict[str, Any]:
    install_engine_imports()
    pin_ephemeris_path()
    report_service = importlib.import_module("app.services.report_service")

    profile = request.get("profile") or {}
    report_type = str(request.get("reportType") or "").strip()
    parameters = request.get("parameters") or {}
    if report_type not in available_report_keys():
        raise BridgeError(f"Unsupported reportType: {report_type}", field="reportType")

    service_request = report_service.ReportRequest(
        report_type=report_type,
        name=str(profile.get("displayName") or "").strip(),
        birth_date=str(profile.get("localDate") or "").strip(),
        birth_time=None if profile.get("birthTimeConfidence") == "UNKNOWN" else profile.get("localTime"),
        location=str(profile.get("locationName") or "").strip(),
        destination=parameters.get("destination"),
        report_date=parameters.get("reportDate"),
        palette=parameters.get("palette", "vibrant"),
        content_pack=parameters.get("contentPack", "plainspeak"),
        consent_acknowledged=True,
    )
    pin_ephemeris_path()
    result = report_service.create_report(service_request)
    submitted_at = result.created_at.astimezone(timezone.utc).isoformat()
    return {
        "jobId": result.session_id,
        "status": "complete",
        "submittedAt": submitted_at,
        "reportId": result.session_id,
        "error": None,
    }


def read_report(report_id: str) -> dict[str, Any]:
    install_engine_imports()
    session_store = importlib.import_module("app.services.session_store")
    html_path = session_store.report_html_path(report_id)
    manifest_file = session_store.manifest_path(report_id)
    manifest = session_store.read_json(manifest_file) if manifest_file else {}
    report_type = manifest.get("report_type", "report")
    generated_at = manifest.get("generation_date") or utc_now()
    content_pack = manifest.get("content_pack")
    if isinstance(content_pack, dict):
        content_pack_ids = [str(content_pack.get("name") or "")]
    else:
        content_pack_ids = []
    warnings = manifest.get("warnings_or_missing_inputs") or []

    return {
        "reportId": report_id,
        "reportType": report_type,
        "title": str(report_type).replace("_", " ").title(),
        "generatedAt": generated_at,
        "mimeType": "text/html",
        "downloadUrl": f"/v1/reports/{report_id}",
        "content": Path(html_path).read_text(encoding="utf-8"),
        "provenance": provenance(
            ["app.services.report_service.create_report", "generate.generate_report"],
            content_pack_ids=[item for item in content_pack_ids if item],
            fallback_tier=None,
            warnings=[str(item) for item in warnings],
        ),
    }
