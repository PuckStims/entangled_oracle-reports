import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config import OUTPUT_DIR, PRODUCTS_DIR
import generate
from tests.phase2_fixtures import build_phase8_fixture


REVIEW_PACK_REPORTS = [
    {
        "slug": "year_ahead_exact",
        "report_type": "year_ahead",
        "fixture": "exact_day_angular_ruler",
        "content_pack": "entangled_oracle",
        "label": "Year Ahead",
    },
    {
        "slug": "personal_forecast_exact",
        "report_type": "personal_forecast",
        "fixture": "exact_day_angular_ruler",
        "content_pack": "entangled_oracle",
        "label": "Personal Forecast",
    },
    {
        "slug": "soul_ecosystem_asteroid_rich",
        "report_type": "soul_ecosystem",
        "fixture": "exact_asteroid_rich",
        "content_pack": "plainspeak",
        "label": "Soul Ecosystem",
    },
    {
        "slug": "horoscope_exact",
        "report_type": "horoscope",
        "fixture": "exact_modern_relational",
        "content_pack": "plainspeak",
        "label": "Horoscope",
    },
    {
        "slug": "horoscope_simple",
        "report_type": "horoscope",
        "fixture": "simple_dob_only",
        "content_pack": "plainspeak",
        "label": "Simple DOB-only Horoscope",
    },
    {
        "slug": "asteroid_portrait_rich",
        "report_type": "asteroid_portrait",
        "fixture": "exact_asteroid_rich",
        "content_pack": "plainspeak",
        "label": "Asteroid Portrait",
    },
]

REVIEW_CRITERIA = [
    "factual calculation correctness",
    "methodology accuracy",
    "birth-time safety",
    "section ordering",
    "routing integrity",
    "prose repetition",
    "standard / niche / EO distinction",
    "visual hierarchy",
    "page pacing",
    "annual rhythm accuracy",
    "event-card relevance",
    "PDF behavior",
    "page length",
    "fallback behavior",
    "technical disclosure",
    "EO-layer usefulness",
]


def _swisseph_available() -> bool:
    try:
        import swisseph  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _build_birth_data(spec: dict) -> dict:
    birth_data = dict(spec["birth_data"])
    birth_data.setdefault("location", "Unknown location")
    birth_data.setdefault("palette", "vibrant")
    birth_data.setdefault("report_date", "2026-01-01")
    if birth_data.get("simple_mode"):
        birth_data["time"] = None
    return birth_data


def _render_checklist(manifest: dict) -> str:
    lines = [
        "# Phase 8 Manual Review Pack",
        "",
        f"Generated: {manifest['generated_at_utc']}",
        "",
        "Use the HTML files as the source of truth for manual review. Follow the approved PDF route in `products/shared/REPORT_PDF_WORKFLOW.md` when PDF verification is needed.",
        "",
    ]
    for item in manifest["reports"]:
        lines.extend(
            [
                f"## {item['label']}",
                f"- Report type: `{item['report_type']}`",
                f"- Fixture: `{item['fixture']}`",
                f"- Scenarios: {', '.join(item['scenarios'])}",
                f"- Timeline mode: `{item['timeline_mode']}`",
                f"- HTML: `{item['html_path']}`",
                "- Review criteria:",
            ]
        )
        for criterion in REVIEW_CRITERIA:
            lines.append(f"  - [ ] {criterion}")
        lines.append("")
    return "\n".join(lines)


def _fallback_year_ahead_context(fixture: dict) -> dict:
    name = fixture["birth_data"]["name"]
    return {
        "year_ahead_curated_summaries": {
            "seasonal_highlights": [
                {
                    "title": "Opening Quarter",
                    "summary": f"{name}'s review-pack timeline begins with a concentrated emphasis on chart-ruler and vocational themes so block routing and pacing can be inspected.",
                },
                {
                    "title": "Integration Quarter",
                    "summary": "The middle stretch stays intentionally quieter so monthly pacing, fallback restraint, and non-dramatic forecast language remain visible.",
                },
            ],
            "climate_highlights": [
                {
                    "field_label": "Career / Public Life",
                    "summary_line": "Primary pattern: sustained public-facing pressure with enough support to test annual-rhythm wording without deterministic event claims.",
                },
                {
                    "field_label": "Inner Life / Rest",
                    "summary_line": "Supporting pattern: quieter recovery space remains visible so convergence language does not swallow the whole year.",
                },
            ],
            "orientation": {
                "long_cycle_emphasis": "Dominant long cycle: the review-pack forecast keeps one headline developmental thread and one quieter recovery thread in view at the same time.",
            },
        },
        "forecast_shape_label": "Developing annual story",
        "methodology_disclosure": "Methodology: Tropical zodiac + Whole Sign houses. This fallback review-pack context is only used when the local transit dependency is unavailable.",
        "technical_disclosure": "Timeline source: deterministic review-pack fixture fallback. Use this pass for routing, prose, and layout inspection rather than ephemeris validation.",
    }


def _fallback_personal_forecast_context(fixture: dict) -> dict:
    name = fixture["birth_data"]["name"]
    return {
        "opening_message": f"{name}'s personal forecast review pack centers the natal target before describing timing, so we can inspect whether forecast prose stays proportionate to the natal architecture.",
        "forecast_focus": "A public-direction theme is paired with one quieter support thread to make repetition, prioritization, and forecast closing language easy to audit.",
        "integration_note": "This fallback review-pack context is deterministic and only appears when the local transit dependency is unavailable.",
    }


def generate_review_pack(output_dir: str | None = None) -> dict:
    pack_root = output_dir or os.path.join(OUTPUT_DIR, "phase8_review_pack")
    html_dir = os.path.join(pack_root, "html")
    os.makedirs(html_dir, exist_ok=True)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pack_root": pack_root,
        "html_dir": html_dir,
        "pdf_workflow_doc": os.path.join(PRODUCTS_DIR, "shared", "REPORT_PDF_WORKFLOW.md"),
        "render_mode": "template_html" if generate.JINJA2_AVAILABLE else "fallback_html",
        "live_transit_engine_available": _swisseph_available(),
        "reports": [],
    }

    for report_spec in REVIEW_PACK_REPORTS:
        fixture = build_phase8_fixture(report_spec["fixture"])
        output_filename = f"{report_spec['slug']}.html"
        birth_data = _build_birth_data(fixture)

        patchers = [patch.object(generate, "get_payload", return_value=fixture["payload"])]
        timeline_mode = "live_engine"
        if not manifest["live_transit_engine_available"] and report_spec["report_type"] == "year_ahead":
            patchers.append(
                patch.object(generate, "_build_year_ahead_context", return_value=_fallback_year_ahead_context(fixture))
            )
            timeline_mode = "fixture_stubbed"
        if not manifest["live_transit_engine_available"] and report_spec["report_type"] == "personal_forecast":
            patchers.append(
                patch.object(generate, "_build_personal_forecast_context", return_value=_fallback_personal_forecast_context(fixture))
            )
            timeline_mode = "fixture_stubbed"

        with patchers[0]:
            for patcher in patchers[1:]:
                patcher.__enter__()
            try:
                html_path = generate.generate_report(
                    report_type=report_spec["report_type"],
                    birth_data=birth_data,
                    output_filename=output_filename,
                    content_pack=report_spec["content_pack"],
                    output_dir=html_dir,
                )
            finally:
                for patcher in reversed(patchers[1:]):
                    patcher.__exit__(None, None, None)

        manifest["reports"].append(
            {
                "slug": report_spec["slug"],
                "label": report_spec["label"],
                "report_type": report_spec["report_type"],
                "fixture": report_spec["fixture"],
                "scenarios": fixture["scenarios"],
                "html_path": html_path,
                "birth_time_state": fixture["payload"].get("user_profile", {}).get("birth_time_state", "exact"),
                "simple_mode": bool(fixture["payload"].get("simple_mode")),
                "content_pack": report_spec["content_pack"],
                "timeline_mode": timeline_mode,
            }
        )

    manifest_path = os.path.join(pack_root, "review_pack_manifest.json")
    checklist_path = os.path.join(pack_root, "review_checklist.md")

    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    with open(checklist_path, "w", encoding="utf-8") as handle:
        handle.write(_render_checklist(manifest))

    manifest["manifest_path"] = manifest_path
    manifest["checklist_path"] = checklist_path
    return manifest


if __name__ == "__main__":
    result = generate_review_pack()
    print(f"[Phase8] Review pack generated: {result['pack_root']}")
    print(f"[Phase8] Manifest: {result['manifest_path']}")
    print(f"[Phase8] Checklist: {result['checklist_path']}")
