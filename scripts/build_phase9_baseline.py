import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from formulas.governance_registry import authoritative_catalog
from product_versions import (
    FINAL_BASELINE_PACKAGE_VERSION,
    PRODUCTION_BASELINE_VERSION,
    build_version_registry,
)
from scripts.generate_review_pack import generate_review_pack
from tests.phase2_fixtures import get_phase8_fixture_library


BASELINE_DIR_NAME = "final_pre_revision_baseline"
SHARED_DOCS = [
    "products/shared/LOCAL_GENERATION_PROCEDURE.md",
    "products/shared/VERSIONING_POLICY.md",
    "products/shared/CLIENT_METHOD_AND_LIMITS.md",
    "products/shared/PRE_DELIVERY_QC_CHECKLIST.md",
    "products/shared/B2B_DEMO_AND_EARLY_RECIPIENT_PACKAGE.md",
    "products/shared/CONTROLLED_FEEDBACK_INTAKE_TEMPLATE.md",
    "products/shared/REPORT_PDF_WORKFLOW.md",
]


def _write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _run_unittest_suite() -> dict:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0,
    }


def _architecture_map_text() -> str:
    return """# Architecture Map

## Runtime Flow

1. `generate.py` receives local birth-data input and report parameters.
2. `engine.natal_engine.generate_payload()` builds the normalized natal payload.
3. `formulas/` computes standard, established-niche, and EO-proprietary structures.
4. `formulas/report_surface.py` produces the layered routing bundle and trace summary.
5. `selectors/variable_resolver.py` flattens the structured results into template-ready variables.
6. Report-specific context builders in `generate.py` assemble narrative/report structures.
7. `render_template()` renders the active HTML template or the documented fallback renderer.
8. `generate_report()` writes the HTML file and adjacent manifest sidecar.
9. Manual HTML review and browser-print PDF workflow complete delivery prep.

## Active Production Layers

- Standard astrology foundation: Tropical zodiac + Whole Sign houses
- Established-niche layer: registry-governed specialist bodies
- EO layer: additive proprietary indexes and bridges

## Active Operator Scripts

- `scripts/run_phase8_qa.ps1`
- `scripts/generate_review_pack.py`
- `scripts/build_phase9_baseline.py`
"""


def _methodology_spec_text() -> str:
    return """# Tropical + Whole Sign Methodology Specification

- Zodiac: Tropical
- Houses: Whole Sign
- Standard chart foundation remains primary.
- Established-niche material remains distinct from the standard chart foundation.
- EO material is additive and may extend standard findings but does not replace them.
- Birth time unknown or approximate: angle- and house-sensitive material must be softened, withheld, or clearly qualified.
- Forecast timing remains symbolic and non-deterministic.

Inactive production concepts are excluded from the active operational baseline:

- Sidereal
- Placidus
- ayanamsa
- synthesis profile
"""


def _known_limitations_text(test_results: dict) -> str:
    limitations = [
        "- PDF generation still depends on the approved manual browser-print workflow; it is not completed by this script.",
        "- Human manual review notes and PDF sign-off still require an operator to complete the review checklist.",
    ]
    if "Warning: jinja2 not installed" in (test_results.get("stdout") or ""):
        limitations.append("- `jinja2` is not installed in the current local environment, so fallback HTML rendering remains active in this snapshot.")
    if "pyswisseph" in (test_results.get("stdout") or "") or "pyswisseph" in (test_results.get("stderr") or ""):
        limitations.append("- `pyswisseph` is not available in the current local environment, so live transit-dependent browser-review outputs may require the fixture-backed fallback route for some scripts.")
    return "# Known Limitations\n\n" + "\n".join(limitations) + "\n"


def _deferred_feature_text() -> str:
    return """# Deferred Feature List

- Manual PDF visual QA sign-off remains an operator task rather than an automated script step.
- Controlled recipient feedback must still be reviewed before becoming a product requirement.
- Legacy EO bridge modules remain present for compatibility and should be retired only through a controlled revision.
"""


def _pdf_qa_text(review_pack_manifest: dict) -> str:
    return f"""# PDF QA Results

Active PDF route:

- `products/shared/REPORT_PDF_WORKFLOW.md`

Current script status:

- HTML review pack generated: `{review_pack_manifest['pack_root']}`
- PDF generation is intentionally not automated here.
- PDF visual QA remains a manual browser-print review step.
"""


def _manual_review_notes_text(review_pack_manifest: dict) -> str:
    return f"""# Manual Review Notes

Generated review pack:

- HTML directory: `{review_pack_manifest['html_dir']}`
- Checklist: `{review_pack_manifest['checklist_path']}`

Current status:

- Review pack generated
- Checklist generated
- Human section-by-section sign-off pending
"""


def _phase_statuses() -> dict:
    return {
        "phase_1": {"status": "COMPLETE", "note": "Foundational local architecture is present in the active repository snapshot."},
        "phase_2": {"status": "COMPLETE", "note": "Standard natal architecture tests and routing are present."},
        "phase_3": {"status": "COMPLETE", "note": "Established-niche governance and registry behavior are covered in the active test suite."},
        "phase_4": {"status": "COMPLETE", "note": "Forecast engine logic and timing tests are present."},
        "phase_5": {"status": "COMPLETE", "note": "Standard report wiring and report-surface trace bundle are present."},
        "phase_6": {"status": "COMPLETE", "note": "Client-facing standard and forecast content scaffolding is present."},
        "phase_7": {"status": "COMPLETE", "note": "Shared rendering system and approved PDF workflow documentation are present."},
        "phase_8": {"status": "APPROVED DEFERRED", "note": "Technical suite and manual review pack are ready; final human PDF/manual sign-off remains outside script automation."},
        "phase_9": {"status": "COMPLETE", "note": "Operational docs, sidecar manifests, QC checklist, and B2B readiness materials are present."},
        "phase_10": {"status": "APPROVED DEFERRED", "note": "Final baseline package is generated; ordinary revision cycles should begin after human review artifacts are signed off."},
    }


def build_phase9_baseline(output_dir: str | None = None) -> dict:
    baseline_root = output_dir or os.path.join(PROJECT_ROOT, "output", BASELINE_DIR_NAME)
    if os.path.isdir(baseline_root):
        shutil.rmtree(baseline_root)
    os.makedirs(baseline_root, exist_ok=True)

    test_results = _run_unittest_suite()
    review_pack_manifest = generate_review_pack()
    catalog = authoritative_catalog()
    fixtures = get_phase8_fixture_library()
    version_snapshot = {
        report_type: build_version_registry(report_type, "entangled_oracle" if report_type in {"year_ahead", "personal_forecast"} else "plainspeak")
        for report_type in ("horoscope", "year_ahead", "personal_forecast", "soul_ecosystem")
    }

    _write_text(os.path.join(baseline_root, "architecture_map.md"), _architecture_map_text())
    _write_text(os.path.join(baseline_root, "tropical_whole_methodology_specification.md"), _methodology_spec_text())
    _write_json(os.path.join(baseline_root, "formula_and_module_inventory.json"), version_snapshot)
    _write_json(
        os.path.join(baseline_root, "established_niche_registry.json"),
        {
            "methods": {
                key: value
                for key, value in catalog["methods"].items()
                if value["method_status"] == "established_niche"
            },
            "asteroid_eligibility": catalog["asteroid_eligibility"],
        },
    )
    _write_json(
        os.path.join(baseline_root, "eo_proprietary_inventory.json"),
        {
            "methods": {
                key: value
                for key, value in catalog["methods"].items()
                if value["method_status"] == "eo_proprietary"
            }
        },
    )
    _write_json(os.path.join(baseline_root, "fixture_inventory.json"), fixtures)
    _write_json(os.path.join(baseline_root, "test_results.json"), test_results)
    _write_json(
        os.path.join(baseline_root, "report_output_baseline_set.json"),
        review_pack_manifest,
    )
    _write_text(os.path.join(baseline_root, "pdf_qa_results.md"), _pdf_qa_text(review_pack_manifest))
    _write_text(os.path.join(baseline_root, "manual_review_notes.md"), _manual_review_notes_text(review_pack_manifest))
    _write_text(os.path.join(baseline_root, "known_limitations.md"), _known_limitations_text(test_results))
    _write_text(os.path.join(baseline_root, "deferred_feature_list.md"), _deferred_feature_text())
    _write_json(os.path.join(baseline_root, "phase_statuses.json"), _phase_statuses())

    docs_dir = os.path.join(baseline_root, "shared_docs")
    os.makedirs(docs_dir, exist_ok=True)
    for relative_path in SHARED_DOCS:
        source = os.path.join(PROJECT_ROOT, relative_path)
        target = os.path.join(docs_dir, os.path.basename(relative_path))
        shutil.copyfile(source, target)

    baseline_manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_package_version": FINAL_BASELINE_PACKAGE_VERSION,
        "production_baseline_version": PRODUCTION_BASELINE_VERSION,
        "baseline_root": baseline_root,
        "shared_docs_dir": docs_dir,
        "review_pack_manifest": review_pack_manifest.get("manifest_path", ""),
        "test_results_file": os.path.join(baseline_root, "test_results.json"),
        "phase_statuses_file": os.path.join(baseline_root, "phase_statuses.json"),
    }
    _write_json(os.path.join(baseline_root, "baseline_manifest.json"), baseline_manifest)
    return baseline_manifest


if __name__ == "__main__":
    result = build_phase9_baseline()
    print(f"[Phase9] Baseline package: {result['baseline_root']}")
