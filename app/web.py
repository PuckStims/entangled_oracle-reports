"""Flask routes for the private beta Report Studio."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _prime_stdlib_socketserver_selector() -> None:
    """Let Werkzeug load stdlib selectors before EO's selectors package is needed."""
    project_root = str(Path(__file__).resolve().parents[1])
    original_path = list(sys.path)
    original_selectors = sys.modules.pop("selectors", None)
    try:
        sys.path = [path for path in sys.path if path not in {"", project_root}]
        stdlib_selectors = importlib.import_module("selectors")
        sys.modules["selectors"] = stdlib_selectors
        importlib.import_module("socketserver")
    finally:
        sys.path = original_path
        if original_selectors is not None:
            sys.modules["selectors"] = original_selectors
        else:
            sys.modules.pop("selectors", None)


_prime_stdlib_socketserver_selector()

from flask import Flask, Response, redirect, render_template, request, send_file, url_for


def _install_local_selector_package() -> None:
    """Restore EO's selector package after Flask/Werkzeug stdlib priming."""
    project_root = Path(__file__).resolve().parents[1]
    selectors_module = sys.modules.get("selectors")
    if selectors_module is not None and not hasattr(selectors_module, "__path__"):
        sys.modules.pop("selectors", None)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    importlib.import_module("selectors")


_install_local_selector_package()

from .services.ai_companion import copy_to_ai_prompt, prompt_groups
from .services.report_registry import available_reports, deferred_reports, get_report_definition
from .services.report_service import ReportRequest, WebInputError, create_report, validate_report_request
from .services.session_store import (
    SessionNotFoundError,
    cleanup_expired_sessions,
    delete_session,
    manifest_path,
    read_json,
    report_html_path,
)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "local-report-studio-prototype"
    cleanup_expired_sessions()

    @app.get("/")
    def welcome() -> str:
        return render_template("welcome.html")

    @app.get("/reports")
    def reports() -> str:
        return render_template(
            "report_picker.html",
            reports=available_reports(),
            deferred_reports=deferred_reports(),
        )

    @app.get("/create/<report_type>")
    def create_form(report_type: str) -> str:
        definition = get_report_definition(report_type)
        if definition is None or not definition.available:
            return render_template(
                "error.html",
                title="Report unavailable",
                message="That report is not exposed in the private beta studio yet.",
            ), 404
        return render_template(
            "birth_form.html",
            report=definition,
            values=_blank_values(report_type),
            errors=[],
        )

    @app.post("/create/<report_type>/edit")
    def edit_form(report_type: str) -> str:
        definition = get_report_definition(report_type)
        if definition is None or not definition.available:
            return render_template(
                "error.html",
                title="Report unavailable",
                message="That report is not exposed in the private beta studio yet.",
            ), 404
        return render_template(
            "birth_form.html",
            report=definition,
            values=_request_from_form(report_type),
            errors=[],
        )

    @app.post("/review/<report_type>")
    def review(report_type: str) -> str:
        values = _request_from_form(report_type)
        definition = get_report_definition(report_type)
        if definition is None:
            return render_template("error.html", title="Report unavailable", message="Unknown report type."), 404
        try:
            validated = validate_report_request(values)
        except WebInputError as exc:
            return render_template("birth_form.html", report=definition, values=values, errors=[str(exc)]), 400
        return render_template("review.html", report=definition, values=validated)

    @app.post("/generate")
    def generate() -> Response | str:
        values = _request_from_form(request.form.get("report_type", ""))
        try:
            result = create_report(values)
        except WebInputError as exc:
            definition = get_report_definition(values.report_type)
            if definition:
                return render_template("birth_form.html", report=definition, values=values, errors=[str(exc)]), 400
            return render_template("error.html", title="Generation failed", message=str(exc)), 400
        return redirect(url_for("report_viewer", session_id=result.session_id))

    @app.get("/report/<session_id>")
    def report_viewer(session_id: str) -> str:
        try:
            html_path = report_html_path(session_id)
            meta_path = manifest_path(session_id)
        except SessionNotFoundError:
            return render_template(
                "error.html",
                title="Report not found",
                message="That local report session is gone or was deleted.",
            ), 404

        manifest = read_json(meta_path) if meta_path else None
        report_type = manifest.get("report_type", "report") if manifest else "report"
        definition = get_report_definition(report_type)
        method_details = _method_details(manifest)
        return render_template(
            "report_viewer.html",
            session_id=session_id,
            report=definition,
            html_path=html_path,
            method_details=method_details,
            prompt_groups=prompt_groups(),
            copy_prompt=copy_to_ai_prompt(),
        )

    @app.get("/report/<session_id>/raw")
    def report_raw(session_id: str):
        try:
            path = report_html_path(session_id)
        except SessionNotFoundError:
            return render_template(
                "error.html",
                title="Report not found",
                message="That local report session is gone or was deleted.",
            ), 404
        return send_file(path)

    @app.post("/report/<session_id>/delete")
    def report_delete(session_id: str) -> str:
        try:
            delete_session(session_id)
        except SessionNotFoundError:
            pass
        except PermissionError:
            return render_template(
                "error.html",
                title="Report is still open",
                message="Close any full-screen report tab for this session, then try deleting again.",
            ), 423
        return render_template("deleted.html")

    @app.get("/companion")
    def companion() -> str:
        return render_template(
            "ai_companion.html",
            prompt_groups=prompt_groups(),
            copy_prompt=copy_to_ai_prompt(),
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _blank_values(report_type: str) -> ReportRequest:
    definition = get_report_definition(report_type)
    return ReportRequest(
        report_type=report_type,
        name="",
        birth_date="",
        birth_time="",
        location="",
        destination="",
        anchor_location="",
        report_date="",
        report_end_date="",
        purpose_lens="",
        relationship_to_place="",
        route_waypoints="",
        route_corridor_km="150",
        route_id="",
        palette="vibrant",
        content_pack=definition.default_content_pack if definition else "plainspeak",
        consent_acknowledged=False,
    )


def _request_from_form(report_type: str) -> ReportRequest:
    return ReportRequest(
        report_type=report_type,
        name=request.form.get("name", ""),
        birth_date=request.form.get("birth_date", ""),
        birth_time=request.form.get("birth_time", "") or None,
        location=request.form.get("location", ""),
        destination=request.form.get("destination", "") or None,
        anchor_location=request.form.get("anchor_location", "") or None,
        report_date=request.form.get("report_date", "") or None,
        report_end_date=request.form.get("report_end_date", "") or None,
        purpose_lens=request.form.get("purpose_lens", "") or None,
        relationship_to_place=request.form.get("relationship_to_place", "") or None,
        route_waypoints=request.form.get("route_waypoints", "") or None,
        route_corridor_km=request.form.get("route_corridor_km", "") or None,
        route_id=request.form.get("route_id", "") or None,
        palette=request.form.get("palette", "vibrant"),
        content_pack=request.form.get("content_pack", "plainspeak"),
        consent_acknowledged=request.form.get("consent_acknowledged") == "yes",
    )


def _method_details(manifest: dict | None) -> list[tuple[str, str]]:
    if not manifest:
        return []
    methodology = manifest.get("methodology") or {}
    birth_confidence = manifest.get("birth_data_confidence") or {}
    details = [
        ("Report type", str(manifest.get("report_type", ""))),
        ("Report version", str(manifest.get("report_version", ""))),
        ("Zodiac", str(methodology.get("zodiac", ""))),
        ("Houses", str(methodology.get("houses", ""))),
        ("Birth-time confidence", str(birth_confidence.get("state", ""))),
        ("Content pack", str(manifest.get("content_pack", ""))),
    ]
    return [(label, value) for label, value in details if value]
