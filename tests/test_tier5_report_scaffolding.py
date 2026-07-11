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
    def test_tier5_block_files_have_no_remaining_todo_placeholders(self):
        """These four files started as literal "TODO" scaffolds (see git
        history) and have since been filled in with real interpretive
        copy. This replaces the old assertion that every string equaled
        "TODO" -- that was correct while the content was genuinely
        unwritten, but would now silently pass again if a placeholder
        were ever reintroduced by mistake, which is the opposite of what
        this test should guard against."""
        paths = [
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/annual_profection_blocks.json",
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/zodiacal_releasing_blocks.json",
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/return_blocks.json",
            PROJECT_ROOT / "products/year_ahead/blocks/plainspeak/forecast_synthesis_blocks.json",
        ]

        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8"))
            strings = [
                value for key, value in data.items()
                if key not in ("_note", "_version")
            ]
            leaf_strings = list(_all_string_values(strings))
            self.assertTrue(leaf_strings, path)
            self.assertTrue(
                all(value != "TODO" for value in leaf_strings),
                f"{path} still has an unfilled TODO placeholder",
            )
            self.assertTrue(
                all(len(value) > 40 for value in leaf_strings),
                f"{path} has a suspiciously short block (placeholder-like, not real prose)",
            )

    def test_year_ahead_tier5_surface_selects_real_content_from_live_pack_paths(self):
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

        for body in (
            surface["annual_profections"][0]["body"],
            surface["zodiacal_releasing"][0]["body"],
            surface["exact_returns"][0]["body"],
            surface["forecast_terrain"]["annual"]["body"],
            surface["forecast_terrain"]["months"][0]["body"],
            surface["forecast_terrain"]["chapters"][0]["body"],
        ):
            self.assertNotEqual(body, "TODO")
            self.assertGreater(len(body), 40)

    def test_tier5_recurring_methods_are_grouped_as_timing_notes(self):
        synthesis = {
            "annual_terrain_map": {
                "label": "convergent",
                "method_families": ["RETURN_MOON", "TIME_LORD"],
                "dominant_topics": ["house:4"],
            },
            "monthly_terrain": [],
            "evidence_chapters": [],
            "contradictions": [],
        }
        timeline = {
            "time_lord_periods": [],
            "zodiacal_releasing_periods": [
                {"period_id": "zr1", "level": "L2"},
            ],
            "zodiacal_releasing_events": [
                {
                    "period_id": "zr1",
                    "method_variant": "zr_peak",
                    "peak_datetime": "2027-02-01T00:00:00+00:00",
                    "period_lord": "Venus",
                    "period_sign": "Libra",
                    "natal_target": "Fortune",
                },
                {
                    "period_id": "zr1",
                    "method_variant": "zr_peak",
                    "peak_datetime": "2027-03-01T00:00:00+00:00",
                    "period_lord": "Venus",
                    "period_sign": "Libra",
                    "natal_target": "Fortune",
                },
            ],
            "return_events": [
                {
                    "method_variant": "lunar_return",
                    "peak_datetime": "2027-01-05T00:00:00+00:00",
                    "return_body": "Moon",
                    "temporal_precision": "instant",
                    "confidence": 0.81,
                },
                {
                    "method_variant": "lunar_return",
                    "peak_datetime": "2027-02-02T00:00:00+00:00",
                    "return_body": "Moon",
                    "temporal_precision": "instant",
                    "confidence": 0.82,
                },
                {
                    "method_variant": "solar_return",
                    "peak_datetime": "2027-09-24T00:00:00+00:00",
                    "return_body": "Sun",
                    "temporal_precision": "instant",
                    "confidence": 0.9,
                },
            ],
        }

        surface = generate._build_tier5_year_ahead_surfaces(
            timeline,
            synthesis,
            CONTENT_PACKS["plainspeak"],
        )

        self.assertEqual(len(surface["exact_returns"]), 2)
        lunar = next(card for card in surface["exact_returns"] if card["method_variant"] == "lunar_return")
        self.assertEqual(lunar["title"], "Lunar Return")
        self.assertEqual(lunar["source_label"], "Return timing note")
        self.assertEqual(lunar["date_labels"], ["January 05, 2027", "February 02, 2027"])
        self.assertNotIn("return_events", lunar.values())

        self.assertEqual(len(surface["zodiacal_releasing"]), 1)
        zr = surface["zodiacal_releasing"][0]
        self.assertEqual(zr["source_label"], "Chapter timing note")
        self.assertEqual(zr["date_labels"], ["February 01, 2027", "March 01, 2027"])
        self.assertNotIn("zodiacal_releasing_events", zr.values())

    def test_year_ahead_template_has_no_client_visible_scaffold_or_raw_sources(self):
        template = (PROJECT_ROOT / "products/year_ahead/templates/active/year_ahead.html").read_text(encoding="utf-8")
        prohibited = [
            "Time-Lord &amp; Return Scaffolds",
            "Forecast Terrain Scaffold",
            "Placeholder TODO",
            "{{ card.source }}",
            "{{ tier5_predictive_surfaces.forecast_terrain.annual.source }}",
            "{{ card.source }} - {{ card.tier4_label }}",
        ]

        for text in prohibited:
            self.assertNotIn(text, template)

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
