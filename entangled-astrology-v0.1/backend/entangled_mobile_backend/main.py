from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response

from . import engine_bridge as bridge


app = FastAPI(
    title="Entangled Oracle Engine API",
    version=bridge.SCHEMA_VERSION,
    description="Thin mobile bridge over the existing Entangled Oracle engine.",
)


def api_error(status_code: int, code: str, message: str, details: dict[str, str] | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details or {}},
    )


def unsupported(feature: str) -> HTTPException:
    return api_error(
        501,
        "UNSUPPORTED_CAPABILITY",
        f"{feature} is not exposed until the adapter can prove parity with existing engine outputs.",
        {"feature": feature},
    )


@app.get("/v1/health")
def health() -> dict[str, Any]:
    try:
        version = bridge.engine_version()
    except Exception as exc:
        return {"status": "error", "checkedAt": bridge.utc_now(), "message": str(exc)}
    return {"status": "ok", "checkedAt": bridge.utc_now(), "message": f"Engine root {bridge.ENGINE_ROOT} version {version}"}


@app.get("/v1/engine/identity")
def identity() -> dict[str, Any]:
    return {
        "engine": bridge.ENGINE_NAME,
        "engineVersion": bridge.engine_version(),
        "schemaVersion": bridge.SCHEMA_VERSION,
        "ephemeris": str(bridge.ENGINE_ROOT / "ephemeris"),
        "buildId": None,
    }


@app.get("/v1/capabilities")
def capabilities() -> dict[str, Any]:
    reports = bridge.available_report_keys()
    return {
        "supportedTechniques": ["natal_chart", "current_field", "timeline", "report_generation"],
        "supportedReports": reports,
        "supportedHouseSystems": ["Whole Sign"],
        "supportsRelationships": False,
        "supportsPlaceResonance": False,
        "supportsBetweenPlaces": False,
    }


@app.post("/v1/profiles/validate")
def validate_profile(request: dict[str, Any]) -> dict[str, Any]:
    profile = request.get("profile") or {}
    issues = []
    try:
        payload = bridge.get_payload_for_profile(profile)
    except bridge.BridgeError as exc:
        issues.append({"field": exc.field or "profile", "severity": "error", "message": str(exc)})
    except Exception as exc:
        issues.append({"field": "profile", "severity": "error", "message": str(exc)})

    if issues:
        return {"valid": False, "normalizedProfile": None, "issues": issues}
    return {"valid": True, "normalizedProfile": bridge.normalized_profile(profile, payload), "issues": []}


@app.post("/v1/charts/natal")
def natal_chart(request: dict[str, Any]) -> dict[str, Any]:
    try:
        return bridge.build_natal_chart(request)
    except bridge.BridgeError as exc:
        raise api_error(422, "INVALID_REQUEST", str(exc), {"field": exc.field or "request"}) from exc
    except Exception as exc:
        raise api_error(500, "ENGINE_ERROR", str(exc)) from exc


@app.post("/v1/fields/current")
def current_field(request: dict[str, Any]) -> dict[str, Any]:
    try:
        return bridge.build_current_field(request)
    except bridge.BridgeError as exc:
        raise api_error(422, "INVALID_REQUEST", str(exc), {"field": exc.field or "request"}) from exc
    except Exception as exc:
        raise api_error(500, "ENGINE_ERROR", str(exc)) from exc


@app.post("/v1/timelines/calculate")
def timeline(request: dict[str, Any]) -> dict[str, Any]:
    try:
        return bridge.build_timeline(request)
    except bridge.BridgeError as exc:
        raise api_error(422, "INVALID_REQUEST", str(exc), {"field": exc.field or "request"}) from exc
    except Exception as exc:
        raise api_error(500, "ENGINE_ERROR", str(exc)) from exc


@app.post("/v1/places/resonance")
def place_resonance(_: dict[str, Any]) -> Response:
    raise unsupported("place_resonance_structured_endpoint")


@app.post("/v1/places/compare")
def between_places(_: dict[str, Any]) -> Response:
    raise unsupported("between_places")


@app.post("/v1/relationships/calculate")
def relationship(_: dict[str, Any]) -> Response:
    raise unsupported("relationships")


@app.post("/v1/reports/generate", status_code=202)
def generate_report(request: dict[str, Any]) -> JSONResponse:
    try:
        return JSONResponse(status_code=202, content=bridge.create_report_job(request))
    except bridge.BridgeError as exc:
        raise api_error(422, "INVALID_REQUEST", str(exc), {"field": exc.field or "request"}) from exc
    except Exception as exc:
        raise api_error(500, "ENGINE_ERROR", str(exc)) from exc


@app.get("/v1/jobs/{job_id}")
def report_job(job_id: str) -> dict[str, Any]:
    try:
        bridge.read_report(job_id)
    except Exception as exc:
        raise api_error(404, "NOT_FOUND", str(exc)) from exc
    return {
        "jobId": job_id,
        "status": "complete",
        "submittedAt": bridge.utc_now(),
        "reportId": job_id,
        "error": None,
    }


@app.get("/v1/reports/{report_id}")
def report(report_id: str) -> dict[str, Any]:
    try:
        return bridge.read_report(report_id)
    except Exception as exc:
        raise api_error(404, "NOT_FOUND", str(exc)) from exc
