import json
import unittest
from pathlib import Path

import generate
from config import CONTENT_PACKS


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _all_string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _all_string_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_string_values(child)


class TestTier5ReportScaffolding(unittest.TestCase):
    def test_new_tier5_block_files_are_literal_todo_scaffolds(self):
        paths = [
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/annual_profection_blocks.json",
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/zodiacal_releasing_blocks.json",
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/return_blocks.json",
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/forecast_synthesis_blocks.json",
        ]

        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8"))
            strings = list(_all_string_values(data))
            self.assertTrue(strings, path)
            self.assertTrue(all(value == "TODO" for value in strings), path)

    def test_year_ahead_tier5_surface_selects_todo_blocks_from_live_pack_paths(self):
        synthesis = {
            "annual_terrain_map": {
                "label": "convergent",
                "method_families": ["TRANSIT", "TIME_LORD"],
                "dominant_topics": ["house:1"],
            },
            "monthly_terrain": [
                {
                    "month_name": "January 2027",
                    "zone": "opening",
                    "relative_intensity": 0.8,
                    "method_families": ["TRANSIT"],
                    "dominant_topics": ["house:1"],
                }
            ],
            "evidence_chapters": [
                {
                    "chapter_type": "monthly_terrain",
                    "label": "opening",
                    "time_scope": "January 2027",
                    "topic_keys": ["house:1"],
                }
            ],
            "contradictions": [],
        }
        timeline = {
            "time_lord_periods": [
                {
                    "system": "annual_profection",
                    "start_at": "2027-01-01T00:00:00+00:00",
                    "end_at": "2028-01-01T00:00:00+00:00",
                    "period_house": 1,
                    "period_lord": "Mars",
                    "period_sign": "Aries",
                    "confidence": 0.8415,
                }
            ],
            "zodiacal_releasing_periods": [
                {"period_id": "zr1", "level": "L1"}
            ],
            "zodiacal_releasing_events": [
                {
                    "period_id": "zr1",
                    "method_variant": "zr_peak",
                    "peak_datetime": "2027-02-01T00:00:00+00:00",
                    "period_lord": "Venus",
                    "period_sign": "Libra",
                    "natal_target": "Fortune",
                }
            ],
            "return_events": [
                {
                    "method_variant": "solar_return",
                    "peak_datetime": "2027-03-01T00:00:00+00:00",
                    "return_body": "Sun",
                    "temporal_precision": "instant",
                    "confidence": 0.833,
                }
            ],
        }

        surface = generate._build_tier5_year_ahead_surfaces(
            timeline,
            synthesis,
            CONTENT_PACKS["plainspeak"],
        )

        self.assertEqual(surface["annual_profections"][0]["body"], "TODO")
        self.assertEqual(surface["zodiacal_releasing"][0]["body"], "TODO")
        self.assertEqual(surface["exact_returns"][0]["body"], "TODO")
        self.assertEqual(surface["forecast_terrain"]["annual"]["body"], "TODO")
        self.assertEqual(surface["forecast_terrain"]["months"][0]["body"], "TODO")
        self.assertEqual(surface["forecast_terrain"]["chapters"][0]["body"], "TODO")

    def test_predictive_chapters_remap_tier4_synthesis_to_existing_prose(self):
        synthesis = {
            "annual_terrain_map": {
                "label": "supportive",
                "method_families": ["TRANSIT"],
                "dominant_topics": ["house:1"],
            },
            "evidence_chapters": [
                {
                    "chapter_type": "monthly_terrain",
                    "label": "opening",
                    "time_scope": "January 2027",
                    "topic_keys": ["house:1"],
                    "supporting_event_ids": ["event-1"],
                    "complicating_event_ids": [],
                    "provenance": [],
                }
            ],
        }

        surface = generate._build_predictive_report_surface(
            {},
            "year_ahead",
            synthesis,
            CONTENT_PACKS["plainspeak"],
        )

        self.assertTrue(surface["enabled"])
        self.assertEqual(surface["chapters"][0]["chapter_kind"], "long_transit_cycle")
        self.assertEqual(surface["chapters"][0]["domain_key"], "identity")
        self.assertIn("The system flags", surface["chapters"][0]["body"])
        self.assertNotEqual(surface["chapters"][0]["body"], "TODO")

    def test_personal_forecast_candidates_remap_method_families_to_existing_prose(self):
        synthesis = {
            "annual_terrain_map": {
                "label": "supportive",
                "method_families": ["RETURN_MOON"],
                "dominant_topics": ["house:4"],
            },
            "evidence_chapters": [],
        }

        surface = generate._build_predictive_report_surface(
            {},
            "personal_forecast",
            synthesis,
            CONTENT_PACKS["plainspeak"],
        )

        self.assertTrue(surface["enabled"])
        self.assertEqual(surface["candidates"][0]["domain_key"], "home")
        self.assertEqual(surface["candidates"][0]["family_key"], "return_family_moon")
        self.assertIn("emotional reset", surface["candidates"][0]["body"])
        self.assertNotEqual(surface["candidates"][0]["body"], "TODO")


if __name__ == "__main__":
    unittest.main()
