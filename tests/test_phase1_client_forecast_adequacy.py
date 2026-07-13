import os
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import generate


class TestWeeklyHoroscopeChronology(unittest.TestCase):
    def test_weekly_report_window_starts_on_report_day_and_covers_seven_days(self):
        report_start = datetime(2026, 7, 15, 14, 30, tzinfo=timezone.utc)

        start, end = generate._report_window("weekly_horoscope", report_start)

        self.assertEqual(start, datetime(2026, 7, 15, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2026, 7, 22, tzinfo=timezone.utc))

    def test_selected_weekly_moments_render_chronologically(self):
        monday = datetime(2025, 12, 29, tzinfo=timezone.utc)
        thursday = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        tuesday = datetime(2025, 12, 30, 9, tzinfo=timezone.utc)
        monday_peak = datetime(2025, 12, 29, 15, tzinfo=timezone.utc)

        fake_moments = [
            _moment(thursday, "Jupiter", score=0.91),
            _moment(monday_peak, "Moon", score=0.62),
            _moment(tuesday, "Venus", score=0.74),
        ]

        transit_engine_stub = types.ModuleType("engine.transit_engine")
        transit_engine_stub.compute_daily_timeline = lambda *args, **kwargs: fake_moments

        with patch.dict(sys.modules, {"engine.transit_engine": transit_engine_stub}):
            ctx = generate._build_weekly_horoscope_context(
                variables={"palette": "vibrant"},
                index_results={},
                payload={"simple_mode": True},
                report_start=monday,
                report_end=monday + timedelta(days=7),
            )

        self.assertEqual(
            [moment["transit_planet"] for moment in ctx["weekly_timeline"]],
            ["Moon", "Venus", "Jupiter"],
        )
        self.assertEqual(
            [moment["peak_datetime"] for moment in ctx["weekly_timeline"]],
            [
                monday_peak.isoformat(),
                tuesday.isoformat(),
                thursday.isoformat(),
            ],
        )
        self.assertEqual(ctx["weekly_timeline_mode"], "daily_balanced_chronological_selected_exact_contacts")
        self.assertEqual(ctx["weekly_day_contact_cap"], 2)
        self.assertTrue(all(day["selected_count"] <= 2 for day in ctx["weekly_days"]))
        self.assertTrue(all("movement_label" in day for day in ctx["weekly_days"]))
        self.assertTrue(all("guidance" in day for day in ctx["weekly_days"]))
        self.assertIn("weekly_complexity_capacity", ctx)
        self.assertIn("weekly_simplified_output_contract", ctx)
        self.assertIn("weekly_theme_headline", ctx)
        self.assertIn("weekly_theme_overview", ctx)
        self.assertIn("weekly_work_with", ctx)
        self.assertGreaterEqual(len(ctx["weekly_watch_for"]), 3)
        self.assertIn("Jupiter", ctx["weekly_theme_headline"])
        self.assertIn("Subscriber narrative synthesized", ctx["weekly_narrative_basis"])
        self.assertEqual(ctx["weekly_timeline"][0]["signal_band"], "useful timing cue")
        self.assertIn("Moon", ctx["weekly_timeline"][0]["localized_focus"])
        self.assertIn("home, family", ctx["weekly_timeline"][0]["localized_focus"])
        self.assertTrue(ctx["weekly_timeline"][0]["reader_guidance"])
        self.assertIn("meaning_primary", ctx["weekly_timeline"][0])
        self.assertIn("technical_label", ctx["weekly_timeline"][0])
        self.assertIn("technical_meta", ctx["weekly_timeline"][0])
        self.assertIn("guidance_line", ctx["weekly_timeline"][0])
        self.assertIn("selector_trace", ctx["weekly_timeline"][0])
        self.assertIn("weekly_prose_ledger", ctx)
        self.assertGreater(ctx["weekly_prose_ledger"]["total_selections"], 0)
        self.assertGreater(len(ctx["weekly_prose_ledger"]["contact_selector_traces"]), 0)

    def test_weekly_context_merges_solar_house_layer(self):
        monday = datetime(2025, 12, 29, tzinfo=timezone.utc)
        fake_moments = [_moment(datetime(2025, 12, 29, 10, tzinfo=timezone.utc), "Saturn", score=0.95)]
        weekly_solar_context = {
            "weekly_solar_layer_available": True,
            "weekly_solar_days": [{"solar_activation_house": 5}],
            "weekly_solar_sign": "Aries",
            "weekly_solar_feature_planet": "Sun",
            "weekly_solar_theme_house_name": "creativity",
            "weekly_solar_theme_block": "Solar week text.",
            "weekly_solar_bridge_block": "Weekly bridge text.",
        }

        transit_engine_stub = types.ModuleType("engine.transit_engine")
        transit_engine_stub.compute_daily_timeline = lambda *args, **kwargs: fake_moments

        with patch.dict(sys.modules, {"engine.transit_engine": transit_engine_stub}):
            with patch(
                "products.sun_sign_horoscope.runtime.solar_context.build_weekly_solar_context",
                return_value=weekly_solar_context,
            ) as solar_builder:
                ctx = generate._build_weekly_horoscope_context(
                    variables={"palette": "vibrant"},
                    index_results={},
                    payload={"simple_mode": False},
                    report_start=monday,
                    report_end=monday + timedelta(days=7),
                )

        solar_builder.assert_called_once()
        self.assertEqual(solar_builder.call_args.args[1], monday)
        self.assertEqual(solar_builder.call_args.args[2], monday + timedelta(days=7))
        self.assertTrue(ctx["weekly_solar_layer_available"])
        self.assertEqual(ctx["weekly_solar_sign"], "Aries")
        self.assertEqual(ctx["weekly_solar_bridge_block"], "Weekly bridge text.")

    def test_weekly_selection_caps_each_day_and_prefers_nonduplicate_contacts(self):
        monday = datetime(2025, 12, 29, tzinfo=timezone.utc)
        monday_first = datetime(2025, 12, 29, 10, tzinfo=timezone.utc)
        monday_duplicate = datetime(2025, 12, 29, 11, tzinfo=timezone.utc)
        monday_alternate = datetime(2025, 12, 29, 12, tzinfo=timezone.utc)
        monday_extra = datetime(2025, 12, 29, 13, tzinfo=timezone.utc)
        tuesday = datetime(2025, 12, 30, 9, tzinfo=timezone.utc)

        fake_moments = [
            _moment(monday_first, "Saturn", score=0.95, natal_target="Moon"),
            _moment(monday_duplicate, "Saturn", score=0.94, natal_target="Moon"),
            _moment(monday_alternate, "Mars", score=0.90, natal_target="Venus"),
            _moment(monday_extra, "Venus", score=0.88, natal_target="Mars"),
            _moment(tuesday, "Jupiter", score=0.70, natal_target="Sun"),
        ]

        transit_engine_stub = types.ModuleType("engine.transit_engine")
        transit_engine_stub.compute_daily_timeline = lambda *args, **kwargs: fake_moments

        with patch.dict(sys.modules, {"engine.transit_engine": transit_engine_stub}):
            ctx = generate._build_weekly_horoscope_context(
                variables={"palette": "vibrant"},
                index_results={},
                payload={"simple_mode": False},
                report_start=monday,
                report_end=monday + timedelta(days=7),
            )

        self.assertEqual(ctx["weekly_timeline_count"], 3)
        self.assertEqual(
            [moment["transit_planet"] for moment in ctx["weekly_timeline"]],
            ["Saturn", "Mars", "Jupiter"],
        )
        self.assertTrue(all(day["selected_count"] <= 2 for day in ctx["weekly_days"]))
        self.assertEqual(ctx["weekly_days"][0]["selected_count"], 2)
        self.assertEqual(ctx["weekly_days"][1]["selected_count"], 1)
        self.assertEqual(ctx["weekly_raw_candidate_count"], 5)

    def test_weekly_contact_guidance_variants_do_not_reuse_when_available(self):
        monday = datetime(2025, 12, 29, tzinfo=timezone.utc)
        fake_moments = [
            _moment(datetime(2025, 12, 29, 10, tzinfo=timezone.utc), "Mars", score=0.90, natal_target="Moon"),
            _moment(datetime(2025, 12, 29, 12, tzinfo=timezone.utc), "Mars", score=0.80, natal_target="Venus"),
            _moment(datetime(2025, 12, 30, 10, tzinfo=timezone.utc), "Mars", score=0.70, natal_target="Sun"),
        ]

        transit_engine_stub = types.ModuleType("engine.transit_engine")
        transit_engine_stub.compute_daily_timeline = lambda *args, **kwargs: fake_moments

        with patch.dict(sys.modules, {"engine.transit_engine": transit_engine_stub}):
            ctx = generate._build_weekly_horoscope_context(
                variables={"palette": "vibrant"},
                index_results={},
                payload={"simple_mode": False},
                report_start=monday,
                report_end=monday + timedelta(days=7),
            )

        guidance_paths = [
            path
            for path in ctx["weekly_prose_ledger"]["selected_block_paths"]
            if path.startswith("moment_guidance/flowing/action/")
        ]
        self.assertGreaterEqual(len(guidance_paths), 3)
        self.assertEqual(len(guidance_paths), len(set(guidance_paths)))

    def test_empty_weekly_moments_still_render_subscriber_guidance(self):
        monday = datetime(2025, 12, 29, tzinfo=timezone.utc)

        transit_engine_stub = types.ModuleType("engine.transit_engine")
        transit_engine_stub.compute_daily_timeline = lambda *args, **kwargs: []

        with patch.dict(sys.modules, {"engine.transit_engine": transit_engine_stub}):
            ctx = generate._build_weekly_horoscope_context(
                variables={"palette": "vibrant"},
                index_results={},
                payload={"simple_mode": False},
                report_start=monday,
                report_end=monday + timedelta(days=7),
            )

        self.assertEqual(ctx["weekly_timeline"], [])
        self.assertEqual(ctx["weekly_theme_headline"], "A Quieter Week for Pattern Recognition")
        self.assertIn("fewer peaks", ctx["weekly_theme_overview"])
        self.assertGreaterEqual(len(ctx["weekly_watch_for"]), 3)

    def test_weekly_contact_selector_preserves_exact_aspect_and_target_group_trace(self):
        moment = _moment(
            datetime(2025, 12, 29, 10, tzinfo=timezone.utc),
            "Sun",
            score=0.72,
            aspect="Sextile",
            aspect_character="flowing",
            natal_target="ASC",
            natal_house=1,
        )
        moment.update(generate._weekly_moment_localization(moment))

        fields = generate._weekly_contact_level_fields(moment)
        trace = fields["selector_trace"]

        self.assertEqual(fields["exact_aspect"], "Sextile")
        self.assertEqual(fields["natal_target_group"], "presence")
        self.assertEqual(trace["inputs"]["exact_aspect"], "Sextile")
        self.assertEqual(trace["inputs"]["natal_target_group"], "presence")
        self.assertEqual(
            trace["contact_meanings"]["requested_key_path"],
            ["Sun", "Sextile", "presence"],
        )
        self.assertEqual(
            trace["contact_meanings"]["resolved_key_path"],
            ["Sun", "Sextile", "presence"],
        )
        self.assertTrue(trace["contact_meanings"]["placeholder_fallback_used"])
        self.assertEqual(trace["contact_meanings"]["legacy_source"], "moment_focus")
        self.assertNotEqual(fields["meaning_primary"], "TODO")
        self.assertIn("in the 1st house", fields["technical_label"])

    def test_weekly_technical_label_does_not_duplicate_existing_house_phrase(self):
        moment = _moment(
            datetime(2025, 12, 29, 10, tzinfo=timezone.utc),
            "Moon",
            score=0.68,
            aspect="Sesquiquadrate",
            aspect_character="challenging",
            natal_target="Mars",
            natal_house=10,
        )
        moment["natal_target_display"] = "your Mars in the 10th house"

        self.assertEqual(
            generate._weekly_technical_label(moment),
            "Moon sesquiquadrate your Mars in the 10th house",
        )

    def test_weekly_technical_meta_uses_noncontradictory_signal_language(self):
        challenging = _moment(
            datetime(2025, 12, 29, 10, tzinfo=timezone.utc),
            "Moon",
            score=0.68,
            aspect="Square",
            aspect_character="challenging",
            natal_target="Mars",
            natal_house=10,
        )
        flowing = _moment(
            datetime(2025, 12, 29, 10, tzinfo=timezone.utc),
            "Venus",
            score=0.70,
            aspect="Trine",
            aspect_character="flowing",
            natal_target="Jupiter",
            natal_house=5,
        )

        self.assertEqual(
            generate._weekly_technical_meta(challenging),
            "House 10 · usable friction · high-priority cue",
        )
        self.assertEqual(
            generate._weekly_technical_meta(flowing),
            "House 5 · supportive opening · high-priority cue",
        )

    def test_weekly_contact_selector_does_not_collapse_exact_aspects_to_character(self):
        cases = [
            ("Sextile", "flowing"),
            ("Trine", "flowing"),
            ("Square", "challenging"),
            ("Opposition", "challenging"),
            ("Semisquare", "challenging"),
            ("Sesquiquadrate", "challenging"),
            ("Quincunx", "challenging"),
        ]

        for aspect, character in cases:
            with self.subTest(aspect=aspect):
                moment = _moment(
                    datetime(2025, 12, 29, 10, tzinfo=timezone.utc),
                    "Mars",
                    score=0.80,
                    aspect=aspect,
                    aspect_character=character,
                    natal_target="Saturn",
                    natal_house=6,
                )
                moment.update(generate._weekly_moment_localization(moment))

                fields = generate._weekly_contact_level_fields(moment)
                trace = fields["selector_trace"]

                self.assertEqual(fields["exact_aspect"], aspect)
                self.assertEqual(trace["inputs"]["aspect_character"], character)
                self.assertEqual(trace["contact_meanings"]["requested_key_path"][1], aspect)
                self.assertNotEqual(trace["contact_meanings"]["requested_key_path"][1], character)
                self.assertEqual(trace["contact_guidance"]["requested_key_path"][0], aspect)
                self.assertNotEqual(fields["meaning_primary"], "TODO")
                self.assertNotEqual(fields["guidance_line"], "TODO")

    def test_weekly_prediction_subject_phrases_stay_tightly_targeted(self):
        import json

        for filename in ("house_domains.json", "planet_motifs.json"):
            blocks_path = os.path.join(
                PROJECT_ROOT,
                "products",
                "weekly_horoscope",
                "blocks",
                filename,
            )

            with open(blocks_path, encoding="utf-8") as handle:
                phrase_map = json.load(handle)

            for key, phrase in phrase_map.items():
                if key.startswith("_"):
                    continue
                with self.subTest(file=filename, key=key):
                    self.assertLessEqual(_reader_facing_subject_count(phrase), 3)


class TestLightweightSurfaceContracts(unittest.TestCase):
    def test_daily_horoscope_context_declares_complexity_contract(self):
        variables = {
            "simple_mode": True,
            "moon_phase_descriptor": "New Moon",
            "sky_moon_sign_element": "fire",
            "activation_planet": "Moon",
            "activation_house_number": 1,
            "day_ruler_name": "Sun",
            "dominant_eas_dimension": "",
            "dimension_names": {},
            "activation_source": "moon_house_fallback",
            "activation_basis_line": "Moon fallback localized through the current house.",
            "palette": "vibrant",
        }

        ctx = generate._build_horoscope_context(
            variables,
            index_results={},
            payload={"simple_mode": True},
        )

        self.assertEqual(ctx["horoscope_output_mode"], "simple_collective_daily_guidance")
        self.assertIn("horoscope_complexity_capacity", ctx)
        self.assertIn("horoscope_simplified_output_contract", ctx)
        self.assertGreaterEqual(len(ctx["horoscope_complexity_capacity"]), 3)
        self.assertEqual(ctx["activation_source"], "moon_house_fallback")
        self.assertIn("Moon fallback", ctx["activation_basis_line"])


class TestPersonalForecastTimelinePositions(unittest.TestCase):
    def test_timeline_position_uses_actual_report_window_date(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = start + timedelta(days=90)

        self.assertEqual(
            generate._personal_forecast_timeline_position_pct(
                {"peak_datetime": start},
                start,
                end,
            ),
            0,
        )
        self.assertEqual(
            generate._personal_forecast_timeline_position_pct(
                {"peak_datetime": start + timedelta(days=45)},
                start,
                end,
            ),
            50,
        )
        self.assertEqual(
            generate._personal_forecast_timeline_position_pct(
                {"peak_datetime": end},
                start,
                end,
            ),
            100,
        )

    def test_timeline_position_clamps_out_of_range_events(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = start + timedelta(days=90)

        self.assertEqual(
            generate._personal_forecast_timeline_position_pct(
                {"peak_datetime": start - timedelta(days=3)},
                start,
                end,
            ),
            0,
        )
        self.assertEqual(
            generate._personal_forecast_timeline_position_pct(
                {"peak_datetime": end + timedelta(days=3)},
                start,
                end,
            ),
            100,
        )


def _moment(
    peak_datetime,
    transit_planet,
    score,
    aspect="Trine",
    aspect_character="flowing",
    natal_target="Moon",
    natal_house=4,
):
    return {
        "peak_datetime": peak_datetime,
        "transit_planet": transit_planet,
        "aspect": aspect,
        "aspect_character": aspect_character,
        "natal_target": natal_target,
        "natal_target_display": f"natal {natal_target}",
        "natal_house": natal_house,
        "score": score,
    }


def _reader_facing_subject_count(phrase: str) -> int:
    return len([part for part in phrase.replace(", and ", ", ").split(",") if part.strip()])


if __name__ == "__main__":
    unittest.main(verbosity=2)
