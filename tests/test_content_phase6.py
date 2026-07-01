import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from config import CONTENT_PACKS, HOUSE_DOMAINS
from formulas.report_surface import build_layered_report_bundle
from generate import _build_event_why_this_matters, _build_standard_natal_foundation
from phase2_fixtures import build_payload


class ContentPhase6Tests(unittest.TestCase):
    def setUp(self):
        self.payload = build_payload(
            asc_sign="Leo",
            placements={
                "Sun": 5.0,
                "Moon": 12.0,
                "Mercury": 8.0,
                "Venus": 42.0,
                "Mars": 98.0,
                "Jupiter": 122.0,
                "Saturn": 275.0,
                "Uranus": 281.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            },
        )
        self.bundle = build_layered_report_bundle(self.payload, "year_ahead", index_results={})
        self.standard = self.bundle["standard_result_bundle"]
        self.pack = CONTENT_PACKS["entangled_oracle"]

    def test_standard_natal_foundation_uses_traceable_standard_categories(self):
        foundation = _build_standard_natal_foundation(
            self.standard,
            self.payload,
            self.pack,
            HOUSE_DOMAINS,
        )

        self.assertTrue(foundation["intro"])
        self.assertGreaterEqual(len(foundation["sections"]), 5)
        titles = {section["title"] for section in foundation["sections"]}
        self.assertIn("Chart orientation", titles)
        self.assertIn("Central planets and condition", titles)
        self.assertIn("Convergence theme", titles)
        self.assertIn("Tropical zodiac", foundation["methodology_note"])

    def test_forecast_event_context_anchors_transits_and_ingresses_to_natal_priority(self):
        transit_text = _build_event_why_this_matters(
            {
                "event_type": "transit",
                "natal_target": "Sun",
                "natal_target_display": "your Sun",
                "natal_house": 9,
            },
            self.standard,
            self.pack,
            HOUSE_DOMAINS,
        )
        self.assertIn("main organizing points", transit_text)

        ingress_text = _build_event_why_this_matters(
            {
                "event_type": "ingress",
                "house_number": 9,
            },
            self.standard,
            self.pack,
            HOUSE_DOMAINS,
        )
        self.assertIn("stronger domains", ingress_text)

    def test_shared_phase6_library_avoids_deterministic_or_pathologizing_language(self):
        path = PROJECT_ROOT / "products" / "year_ahead" / "blocks" / "shared" / "Standard_Natal_Foundation_Blocks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        text = json.dumps(
            {
                "foundation": data["foundation"],
                "forecast_context": data["forecast_context"],
            }
        ).lower()
        for banned in ("guaranteed", "destiny", "trauma", "pathology", "diagnosis", "fated"):
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
