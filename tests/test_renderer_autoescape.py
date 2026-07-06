import os
import re
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import generate
from tests.phase2_fixtures import build_phase8_fixture


def _palette_stub() -> dict:
    return {
        "bg": "#070709",
        "surface": "#13131A",
        "surface_2": "#1A1A24",
        "border": "#2B2B38",
        "text": "#F5F1E8",
        "muted": "#B8B2A7",
        "subtle": "#807A70",
        "identity": "#7BC6FF",
        "growth": "#9BFFB1",
        "relationships": "#FF9BC2",
        "creativity": "#FFC36B",
        "vocation": "#C6A0FF",
        "home": "#FFD39B",
        "spiritual": "#9FE0D0",
        "accent": "#F3D27A",
        "purple": "#8B6DFF",
        "gold": "#D4AF37",
        "rose": "#E78FB3",
        "ember": "#FF8A5B",
        "blue": "#6FA8FF",
    }


class RendererAutoescapeTests(unittest.TestCase):
    def test_fallback_querent_name_is_escaped(self):
        html = generate._render_fallback(
            "personal_forecast",
            {
                "querent_name": '<script>alert("x")</script>',
                "generation_date": "July 2, 2026",
                "generation_location": "Chicago, IL",
            },
        )

        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", html)
        self.assertNotIn('<script>alert("x")</script>', html)

    def test_fallback_visible_metadata_is_escaped(self):
        html = generate._render_fallback(
            "personal_forecast",
            {
                "querent_name": "Fallback Test",
                "generation_date": "July 2, 2026",
                "generation_location": '<img src=x onerror="alert(1)">',
            },
        )

        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;", html)
        self.assertNotIn('<img src=x onerror="alert(1)">', html)

    def test_fallback_does_not_emit_raw_user_html(self):
        html = generate._render_fallback(
            "personal_forecast",
            {
                "querent_name": '<script>alert("x")</script>',
                "generation_date": "July 2, 2026",
                "generation_location": '<img src=x onerror="alert(1)">',
                "long_user_note": "User supplied note: <div onclick=\"steal()\">click me</div>",
            },
        )

        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertNotIn('<div onclick="', html)
        self.assertIn("onclick=&quot;steal()&quot;", html)

    @unittest.skipUnless(generate.JINJA2_AVAILABLE, "Jinja2 not installed.")
    def test_querent_name_is_escaped_in_active_template(self):
        html = generate.render_template(
            "personal_forecast",
            {
                "palette": _palette_stub(),
                "palette_name": "vibrant",
                "querent_name": '<script>alert("x")</script>',
                "birth_location": "Chicago, IL",
                "generation_date": "July 2, 2026",
                "report_start_display": "July 2, 2026",
                "report_end_display": "October 2, 2026",
                "birth_date_display": "",
                "birth_time_display": "",
                "birth_time_status": "unknown",
            },
        )

        self.assertIn("&lt;script&gt;alert(", html)
        self.assertIn("&lt;/script&gt;", html)
        self.assertNotIn('<script>alert("x")</script>', html)

    @unittest.skipUnless(generate.JINJA2_AVAILABLE, "Jinja2 not installed.")
    def test_birth_location_is_escaped_in_active_template(self):
        html = generate.render_template(
            "personal_forecast",
            {
                "palette": _palette_stub(),
                "palette_name": "vibrant",
                "querent_name": "Escaping Test",
                "birth_location": '<img src=x onerror="alert(1)">',
                "generation_date": "July 2, 2026",
                "report_start_display": "July 2, 2026",
                "report_end_display": "October 2, 2026",
                "birth_date_display": "",
                "birth_time_display": "",
                "birth_time_status": "unknown",
            },
        )

        self.assertIn("&lt;img", html)
        self.assertIn("onerror=&#34;alert(1)&#34;", html)
        self.assertNotIn('<img src=x onerror="alert(1)">', html)

    @unittest.skipUnless(generate.JINJA2_AVAILABLE, "Jinja2 not installed.")
    def test_shared_report_css_still_renders_as_raw_css(self):
        html = generate.render_template(
            "personal_forecast",
            {
                "palette": _palette_stub(),
                "palette_name": "vibrant",
                "querent_name": "CSS Test",
                "birth_location": "Chicago, IL",
                "generation_date": "July 2, 2026",
                "report_start_display": "July 2, 2026",
                "report_end_display": "October 2, 2026",
                "birth_date_display": "",
                "birth_time_display": "",
                "birth_time_status": "unknown",
                "shared_report_css": ":root { --autoescape-test: 1; }",
            },
        )

        self.assertRegex(
            html,
            r"<style[^>]*>.*:root\s*\{\s*--autoescape-test:\s*1;\s*\}.*</style>",
        )
        self.assertNotIn("&lt;style", html)
        self.assertNotIn("--autoescape-test:&lt;", html)

    def test_normal_report_generation_still_succeeds(self):
        fixture = build_phase8_fixture("simple_dob_only")
        birth_data = dict(fixture["birth_data"])
        birth_data.setdefault("palette", "vibrant")
        birth_data.setdefault("report_date", "2026-01-01")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generate, "get_payload", return_value=fixture["payload"]):
                output_path = generate.generate_report(
                    report_type="horoscope",
                    birth_data=birth_data,
                    output_filename="renderer_autoescape_smoke.html",
                    content_pack="plainspeak",
                    output_dir=tmpdir,
                )

            self.assertTrue(os.path.exists(output_path))
            self.assertTrue(os.path.exists(output_path.replace(".html", ".manifest.json")))

    def test_report_stdout_redacts_full_paths_by_default(self):
        fixture = build_phase8_fixture("simple_dob_only")
        birth_data = dict(fixture["birth_data"])
        birth_data.setdefault("palette", "vibrant")
        birth_data.setdefault("report_date", "2026-01-01")

        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with patch.object(generate, "get_payload", return_value=fixture["payload"]):
                with patch.dict(os.environ, {}, clear=False):
                    with redirect_stdout(stdout):
                        output_path = generate.generate_report(
                            report_type="horoscope",
                            birth_data=birth_data,
                            output_filename="renderer_stdout_redaction.html",
                            content_pack="plainspeak",
                            output_dir=tmpdir,
                        )

            rendered = stdout.getvalue()
            self.assertIn("[Done] Report saved: renderer_stdout_redaction.html", rendered)
            self.assertIn("[Done] Manifest saved: renderer_stdout_redaction.manifest.json", rendered)
            self.assertNotIn(output_path, rendered)
            self.assertNotIn(tmpdir, rendered)
            self.assertNotIn("[Formulas] Computing indexes...", rendered)
            self.assertNotIn("[Variables] Resolving...", rendered)
            self.assertNotIn("[Blocks] Selecting...", rendered)
            self.assertNotIn("[Render] Building HTML...", rendered)

    def test_report_stdout_emits_full_paths_when_opted_in(self):
        fixture = build_phase8_fixture("simple_dob_only")
        birth_data = dict(fixture["birth_data"])
        birth_data.setdefault("palette", "vibrant")
        birth_data.setdefault("report_date", "2026-01-01")

        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with patch.object(generate, "get_payload", return_value=fixture["payload"]):
                with patch.dict(os.environ, {"EO_STDOUT_REPORT_PATHS": "1"}, clear=False):
                    with redirect_stdout(stdout):
                        output_path = generate.generate_report(
                            report_type="horoscope",
                            birth_data=birth_data,
                            output_filename="renderer_stdout_paths.html",
                            content_pack="plainspeak",
                            output_dir=tmpdir,
                        )

            rendered = stdout.getvalue()
            self.assertIn("[Done] Report path:", rendered)
            self.assertIn("[Done] Manifest path:", rendered)
            self.assertIn(output_path, rendered)
            self.assertIn(tmpdir, rendered)

    def test_report_stdout_emits_progress_when_verbose_opted_in(self):
        fixture = build_phase8_fixture("simple_dob_only")
        birth_data = dict(fixture["birth_data"])
        birth_data.setdefault("palette", "vibrant")
        birth_data.setdefault("report_date", "2026-01-01")

        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with patch.object(generate, "get_payload", return_value=fixture["payload"]):
                with patch.dict(os.environ, {"EO_VERBOSE_STDOUT": "1"}, clear=False):
                    with redirect_stdout(stdout):
                        generate.generate_report(
                            report_type="horoscope",
                            birth_data=birth_data,
                            output_filename="renderer_stdout_verbose.html",
                            content_pack="plainspeak",
                            output_dir=tmpdir,
                        )

            rendered = stdout.getvalue()
            self.assertIn("[Formulas] Computing indexes...", rendered)
            self.assertIn("[Variables] Resolving...", rendered)
            self.assertIn("[Blocks] Selecting...", rendered)
            self.assertIn("[Render] Building HTML...", rendered)

    def test_default_output_filenames_are_unique_and_manifests_match(self):
        fixture = build_phase8_fixture("simple_dob_only")
        birth_data = dict(fixture["birth_data"])
        birth_data.setdefault("palette", "vibrant")
        birth_data["report_date"] = "2026-01-01"

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generate, "get_payload", return_value=fixture["payload"]):
                first_output = generate.generate_report(
                    report_type="horoscope",
                    birth_data=dict(birth_data),
                    content_pack="plainspeak",
                    output_dir=tmpdir,
                )
                second_output = generate.generate_report(
                    report_type="horoscope",
                    birth_data=dict(birth_data),
                    content_pack="plainspeak",
                    output_dir=tmpdir,
                )

            self.assertNotEqual(first_output, second_output)
            self.assertTrue(os.path.exists(first_output))
            self.assertTrue(os.path.exists(second_output))

            first_manifest = first_output.replace(".html", ".manifest.json")
            second_manifest = second_output.replace(".html", ".manifest.json")
            self.assertTrue(os.path.exists(first_manifest))
            self.assertTrue(os.path.exists(second_manifest))

            with open(first_manifest, "r", encoding="utf-8") as handle:
                first_manifest_payload = json.load(handle)
            with open(second_manifest, "r", encoding="utf-8") as handle:
                second_manifest_payload = json.load(handle)

            self.assertEqual(first_manifest_payload["report_path"], first_output)
            self.assertEqual(second_manifest_payload["report_path"], second_output)


if __name__ == "__main__":
    unittest.main()
