import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import generate
import oracle_to_pdf


class Phase7RenderingSystemTests(unittest.TestCase):
    def test_render_defaults_expose_single_browser_print_workflow(self):
        defaults = generate._build_render_defaults({"generation_date": "June 30, 2026"})

        self.assertEqual(defaults["pdf_workflow"]["route"], "browser_print")
        self.assertEqual(defaults["pdf_workflow"]["approved_browser"], "Chrome")
        self.assertTrue(defaults["pdf_workflow"]["background_graphics_required"])
        self.assertIn("Generated June 30, 2026", defaults["report_footer_text"])
        self.assertIn(":root", defaults["shared_report_css"])

    def test_fallback_renderer_includes_shared_css_brand_and_footer(self):
        html = generate.render_template(
            "year_ahead",
            {
                "querent_name": "Phase 7 Test",
                "generation_date": "June 30, 2026",
                "generation_location": "Chicago, IL",
                "year_overview_block": "Orientation prose that is long enough to hit fallback rendering.",
            },
        )

        self.assertIn("report-shell", html)
        self.assertIn("Entangled Oracle", html)
        self.assertIn("Generated June 30, 2026", html)
        self.assertIn("--measure-readable", html)

    def test_active_templates_consume_shared_render_contract(self):
        templates = [
            PROJECT_ROOT / "products" / "year_ahead" / "templates" / "active" / "year_ahead.html",
            PROJECT_ROOT / "products" / "personal_forecast" / "templates" / "personal_forecast.html",
            PROJECT_ROOT / "products" / "soul_ecosystem" / "templates" / "soul_ecosystem.html",
        ]
        for path in templates:
            text = path.read_text(encoding="utf-8")
            self.assertIn("shared_report_css", text, path.name)
            self.assertIn("report_footer_text", text, path.name)

    def test_oracle_to_pdf_declares_same_approved_route(self):
        self.assertEqual(oracle_to_pdf.APPROVED_PDF_WORKFLOW["route"], "browser_print")
        self.assertEqual(oracle_to_pdf.APPROVED_PDF_WORKFLOW["workflow_doc"], "products/shared/REPORT_PDF_WORKFLOW.md")


if __name__ == "__main__":
    unittest.main()
