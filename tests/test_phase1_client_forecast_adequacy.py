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
                report_end=monday + timedelta(days=5),
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
        self.assertEqual(ctx["weekly_timeline_mode"], "chronological_selected_exact_contacts")


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


def _moment(peak_datetime, transit_planet, score):
    return {
        "peak_datetime": peak_datetime,
        "transit_planet": transit_planet,
        "aspect": "Trine",
        "aspect_character": "flowing",
        "natal_target": "Moon",
        "natal_target_display": "natal Moon",
        "natal_house": 4,
        "score": score,
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
