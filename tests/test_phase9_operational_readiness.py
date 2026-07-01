import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(__file__))

import generate
from product_versions import build_version_registry
from scripts.build_phase9_baseline import build_phase9_baseline
from tests.phase2_fixtures import build_phase8_fixture


class Phase9OperationalReadinessTests(unittest.TestCase):
    def test_birth_metadata_marks_approximate_time_as_non_exact(self):
        fixture = build_phase8_fixture("approximate_night_cadent_ruler")
        birth_meta = generate._build_birth_metadata(fixture["payload"])
        self.assertEqual(birth_meta["birth_time_status"], "approximate")
        self.assertEqual(
            birth_meta["birth_time_confidence"],
            "Birth time unknown or approximate",
        )
        self.assertFalse(generate._has_exact_birth_time(fixture["payload"]))

    def test_version_registry_exposes_required_production_layers(self):
        registry = build_version_registry("year_ahead", "entangled_oracle")
        for key in (
            "formula_modules",
            "standard_engine_package",
            "established_niche_registry",
            "eo_proprietary_formula_package",
            "content_libraries",
            "block_files",
            "templates",
            "visual_system_css",
            "report_generation_code",
            "output_package",
            "content_pack",
        ):
            self.assertIn(key, registry)

    def test_generate_report_writes_manifest_sidecar(self):
        fixture = build_phase8_fixture("simple_dob_only")
        birth_data = dict(fixture["birth_data"])
        birth_data.setdefault("palette", "vibrant")
        birth_data.setdefault("report_date", "2026-01-01")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generate, "get_payload", return_value=fixture["payload"]):
                output_path = generate.generate_report(
                    report_type="horoscope",
                    birth_data=birth_data,
                    output_filename="phase9_manifest_smoke.html",
                    content_pack="plainspeak",
                    output_dir=tmpdir,
                )

            manifest_path = output_path.replace(".html", ".manifest.json")
            self.assertTrue(os.path.exists(manifest_path))
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)

            self.assertEqual(manifest["methodology"]["zodiac"], "Tropical")
            self.assertEqual(manifest["methodology"]["houses"], "Whole Sign")
            self.assertEqual(manifest["birth_data_confidence"]["state"], "unknown_birth_time")
            self.assertIn("active_standard_modules", manifest)
            self.assertIn("template_version", manifest)
            self.assertIn("formula_version", manifest)
            self.assertNotIn("Sidereal", json.dumps(manifest))
            self.assertNotIn("Placidus", json.dumps(manifest))
            self.assertNotIn("ayanamsa", json.dumps(manifest))
            self.assertNotIn("synthesis profile", json.dumps(manifest).lower())

    def test_baseline_builder_writes_required_snapshot_files(self):
        fake_review_pack = {
            "pack_root": "C:/entangled_oracle/output/phase8_review_pack",
            "html_dir": "C:/entangled_oracle/output/phase8_review_pack/html",
            "checklist_path": "C:/entangled_oracle/output/phase8_review_pack/review_checklist.md",
            "manifest_path": "C:/entangled_oracle/output/phase8_review_pack/review_pack_manifest.json",
        }
        fake_test_results = {
            "command": "python -m unittest discover -s tests -p test_*.py",
            "returncode": 0,
            "stdout": "OK",
            "stderr": "",
            "passed": True,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.build_phase9_baseline._run_unittest_suite", return_value=fake_test_results), \
                 patch("scripts.build_phase9_baseline.generate_review_pack", return_value=fake_review_pack):
                baseline = build_phase9_baseline(output_dir=tmpdir)

            self.assertTrue(os.path.exists(os.path.join(tmpdir, "baseline_manifest.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "phase_statuses.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "formula_and_module_inventory.json")))
            self.assertEqual(baseline["baseline_root"], tmpdir)


if __name__ == "__main__":
    unittest.main()
