import json
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config import OUTPUT_DIR
from engine.natal_engine import generate_payload
from engine.synastry import build_pair_payload
from products.synastry.assembler import assemble_synastry_context
from products.synastry.renderer import render_synastry_html
from tests.phase2_fixtures import build_phase8_fixture


SYNASTRY_FIXTURES = [
    {
        "slug": "exact_exact",
        "label": "Exact / Exact",
        "person_a": {
            "fallback_fixture": "exact_day_angular_ruler",
            "name": "Synastry Fixture A Exact",
            "date": "1992-03-21",
            "time": "08:11",
            "location": "Peoria, IL",
        },
        "person_b": {
            "fallback_fixture": "exact_modern_relational",
            "name": "Synastry Fixture B Exact",
            "date": "1995-02-15",
            "time": "18:42",
            "location": "Seattle, WA",
        },
    },
    {
        "slug": "exact_unknown",
        "label": "Exact / Unknown",
        "person_a": {
            "fallback_fixture": "exact_day_angular_ruler",
            "name": "Synastry Fixture A Exact",
            "date": "1992-03-21",
            "time": "08:11",
            "location": "Peoria, IL",
        },
        "person_b": {
            "fallback_fixture": "simple_dob_only",
            "name": "Synastry Fixture B Unknown",
            "date": "1988-11-04",
            "time": None,
            "location": "Austin, TX",
            "simple_mode": True,
        },
    },
    {
        "slug": "unknown_exact",
        "label": "Unknown / Exact",
        "person_a": {
            "fallback_fixture": "simple_dob_only",
            "name": "Synastry Fixture A Unknown",
            "date": "1990-06-15",
            "time": None,
            "location": "Chicago, IL",
            "simple_mode": True,
        },
        "person_b": {
            "fallback_fixture": "exact_modern_relational",
            "name": "Synastry Fixture B Exact",
            "date": "1995-02-15",
            "time": "18:42",
            "location": "Seattle, WA",
        },
    },
]


def _build_birth_data(spec: dict) -> dict:
    birth_data = {
        key: value
        for key, value in spec.items()
        if key != "fallback_fixture"
    }
    if birth_data.get("simple_mode"):
        birth_data["time"] = None
    return birth_data


def _build_natal_payload(spec: dict) -> tuple[dict, str]:
    try:
        return generate_payload(_build_birth_data(spec)), "generate_payload"
    except Exception as exc:
        fallback_name = spec.get("fallback_fixture")
        if not fallback_name:
            raise
        payload = build_phase8_fixture(fallback_name)["payload"]
        payload.setdefault("user_profile", {})
        payload["user_profile"]["synastry_fixture_fallback_reason"] = str(exc)
        return payload, f"phase2_fixture_fallback:{fallback_name}"


def _summarize_pair(pair_payload: dict) -> dict:
    computations = pair_payload["computations"]
    sidecar = pair_payload["sidecar"]
    live_directional = [
        record for record in computations["directional_aspects"]
        if not record.get("withheld")
    ]
    live_overlays = [
        record for record in computations["house_overlays"]
        if not record.get("withheld")
    ]
    return {
        "schema_version": pair_payload["schema_version"],
        "formula_versions": pair_payload["provenance"]["formula_versions"],
        "person_a_birth_time_state": pair_payload["person_a"]["birth_time_state"],
        "person_b_birth_time_state": pair_payload["person_b"]["birth_time_state"],
        "directional_aspect_count": len(live_directional),
        "withheld_directional_aspect_count": len(computations["directional_aspects"]) - len(live_directional),
        "mutual_aspect_count": len(computations["mutual_aspects"]),
        "house_overlay_count": len(live_overlays),
        "withheld_house_overlay_count": len(computations["house_overlays"]) - len(live_overlays),
        "composite_body_count": len(computations["composite"]["bodies"]),
        "composite_aspect_count": len(computations["composite"]["aspects"]),
        "repeated_natal_theme_count": len(computations["repeated_natal_themes"]),
        "relationship_topic_signature_count": len(computations["relationship_topic_signatures"]),
        "relationship_convergence_count": len(computations["relationship_convergence"]),
        "withheld_summary": sidecar["withheld_summary"],
        "client_report_available": sidecar["claim_safety"]["client_report_available"],
        "relationship_verdicts_supported": sidecar["claim_safety"]["relationship_verdicts_supported"],
    }


def build_synastry_fixture_pack(output_dir: str | None = None) -> dict:
    pack_root = output_dir or os.path.join(OUTPUT_DIR, "synastry_fixture_pack")
    payload_dir = os.path.join(pack_root, "payloads")
    context_dir = os.path.join(pack_root, "contexts")
    preview_dir = os.path.join(pack_root, "previews")
    os.makedirs(payload_dir, exist_ok=True)
    os.makedirs(context_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pack_root": pack_root,
        "payload_dir": payload_dir,
        "purpose": "Dev-only synastry evidence inspection pack. Not a client report.",
        "contract_doc": os.path.join(PROJECT_ROOT, "docs", "SYNASTRY_ENGINE_CONTRACT.md"),
        "fixtures": [],
    }

    for fixture in SYNASTRY_FIXTURES:
        person_a_payload, person_a_source = _build_natal_payload(fixture["person_a"])
        person_b_payload, person_b_source = _build_natal_payload(fixture["person_b"])
        pair_payload = build_pair_payload(
            person_a_payload,
            person_b_payload,
            relationship_meta={
                "relationship_type": "fixture",
                "consent_state": "fixture_data",
                "person_a_label": fixture["person_a"]["name"],
                "person_b_label": fixture["person_b"]["name"],
            },
        )
        synastry_context = assemble_synastry_context(pair_payload)
        preview_html = render_synastry_html(synastry_context)
        output_path = os.path.join(payload_dir, f"{fixture['slug']}.json")
        summary_path = os.path.join(payload_dir, f"{fixture['slug']}.summary.json")
        context_path = os.path.join(context_dir, f"{fixture['slug']}.context.json")
        preview_path = os.path.join(preview_dir, f"{fixture['slug']}.html")
        summary = _summarize_pair(pair_payload)

        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(pair_payload, handle, indent=2)
        with open(summary_path, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        with open(context_path, "w", encoding="utf-8") as handle:
            json.dump(synastry_context, handle, indent=2)
        with open(preview_path, "w", encoding="utf-8") as handle:
            handle.write(preview_html)

        manifest["fixtures"].append(
            {
                "slug": fixture["slug"],
                "label": fixture["label"],
                "payload_path": output_path,
                "summary_path": summary_path,
                "context_path": context_path,
                "preview_html_path": preview_path,
                "person_a_natal_payload_source": person_a_source,
                "person_b_natal_payload_source": person_b_source,
                "summary": summary,
            }
        )

    manifest_path = os.path.join(pack_root, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    manifest["manifest_path"] = manifest_path
    return manifest


if __name__ == "__main__":
    result = build_synastry_fixture_pack()
    print(f"[Synastry] Fixture pack generated: {result['pack_root']}")
    print(f"[Synastry] Manifest: {result['manifest_path']}")
    for fixture in result["fixtures"]:
        print(f"[Synastry] {fixture['slug']}: {fixture['summary_path']}")
