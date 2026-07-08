import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from formulas.standard.forecast_activation import (
    build_forecast_activation_profile,
    enrich_forecast_event,
    link_related_forecast_events,
)
from phase2_fixtures import build_payload


class ForecastEnginePhase4Tests(unittest.TestCase):
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
        self.profile = build_forecast_activation_profile(self.payload)

    def _base_transit(self, target: str, orb: float = 0.4, duration_days: float = 36.0) -> dict:
        peak_dt = datetime(2026, 7, 14, tzinfo=timezone.utc)
        return {
            "event_type": "transit",
            "transit_planet": "Saturn",
            "aspect": "Conjunction",
            "natal_target": target,
            "natal_house": 1 if target == "Sun" else 6,
            "maximum_orb": 3.0,
            "orb": orb,
            "raw_score": 0.74,
            "concentration_score": 0.74,
            "combined_intensity_score": 0.74,
            "entry_datetime": peak_dt,
            "peak_datetime": peak_dt,
            "leave_datetime": peak_dt,
            "duration_days": duration_days,
            "contact_count": 1,
        }

    def test_central_natal_target_scores_above_background_target(self):
        chart_ruler_target = self._base_transit("Sun")
        background_target = self._base_transit("Saturn")

        ruler_event = enrich_forecast_event(chart_ruler_target, self.profile)
        background_event = enrich_forecast_event(background_target, self.profile)

        self.assertGreater(ruler_event["natal_relevance"], background_event["natal_relevance"])
        self.assertGreater(ruler_event["reader_facing_activity_score"], background_event["reader_facing_activity_score"])

    def test_high_emphasis_ingress_outranks_low_emphasis_ingress(self):
        peak_dt = datetime(2026, 8, 1, tzinfo=timezone.utc)
        strong_house = enrich_forecast_event(
            {
                "event_type": "ingress",
                "transit_planet": "Jupiter",
                "house_number": 1,
                "whole_sign_house": 1,
                "raw_score": 0.45,
                "combined_intensity_score": 0.45,
                "entry_datetime": peak_dt,
                "peak_datetime": peak_dt,
                "leave_datetime": None,
                "duration_days": 0.0,
            },
            self.profile,
        )
        weak_house = enrich_forecast_event(
            {
                "event_type": "ingress",
                "transit_planet": "Jupiter",
                "house_number": 12,
                "whole_sign_house": 12,
                "raw_score": 0.45,
                "combined_intensity_score": 0.45,
                "entry_datetime": peak_dt,
                "peak_datetime": peak_dt,
                "leave_datetime": None,
                "duration_days": 0.0,
            },
            self.profile,
        )

        self.assertGreater(strong_house["natal_relevance"], weak_house["natal_relevance"])
        self.assertLessEqual(strong_house["reader_facing_activity_score"], 0.62)

    def test_station_linked_to_active_cycle_is_marked_and_softened(self):
        peak_dt = datetime(2026, 9, 10, tzinfo=timezone.utc)
        transit = enrich_forecast_event(
            {
                "event_type": "transit",
                "transit_planet": "Venus",
                "aspect": "Conjunction",
                "natal_target": "Moon",
                "natal_house": 1,
                "maximum_orb": 4.0,
                "orb": 0.2,
                "raw_score": 0.64,
                "concentration_score": 0.64,
                "combined_intensity_score": 0.64,
                "entry_datetime": datetime(2026, 9, 1, tzinfo=timezone.utc),
                "peak_datetime": peak_dt,
                "leave_datetime": datetime(2026, 9, 18, tzinfo=timezone.utc),
                "duration_days": 17.0,
                "contact_count": 3,
                "cycle_id": "venus_cycle_1",
            },
            self.profile,
        )
        station = enrich_forecast_event(
            {
                "event_type": "station",
                "transit_planet": "Venus",
                "station_type": "Retrograde",
                "natal_target": "Moon",
                "natal_house": 1,
                "distance_to_natal_target": 0.5,
                "raw_score": 0.61,
                "combined_intensity_score": 0.61,
                "entry_datetime": peak_dt,
                "peak_datetime": peak_dt,
                "leave_datetime": None,
                "duration_days": 0.0,
            },
            self.profile,
        )

        linked = link_related_forecast_events(
            [transit],
            [],
            [station],
            [],
            self.profile,
        )
        transits, ingresses, stations, eclipses = linked["transit_events"], linked["ingress_events"], linked["station_events"], linked["eclipse_events"]
        linked_station = stations[0]
        self.assertTrue(linked_station["near_active_transit_cycle"])
        self.assertEqual(linked_station["pass_sequence"], "station_linked")
        self.assertIn("venus_cycle_1", linked_station["related_cycle_ids"])
        self.assertLess(linked_station["reader_facing_activity_score"], station["reader_facing_activity_score"])
        self.assertEqual(len(transits), 1)
        self.assertEqual(len(ingresses), 0)
        self.assertEqual(len(eclipses), 0)

    def test_eclipse_without_central_contact_stays_lower_than_luminary_contact(self):
        peak_dt = datetime(2026, 10, 4, tzinfo=timezone.utc)
        broad = enrich_forecast_event(
            {
                "event_type": "eclipse",
                "eclipse_type": "Solar",
                "transit_planet": "Solar",
                "natal_target": "",
                "natal_house": 11,
                "whole_sign_house": 11,
                "distance_to_natal_target": None,
                "raw_score": 0.34,
                "combined_intensity_score": 0.34,
                "entry_datetime": peak_dt,
                "peak_datetime": peak_dt,
                "leave_datetime": None,
                "duration_days": 0.0,
            },
            self.profile,
        )
        personal = enrich_forecast_event(
            {
                "event_type": "eclipse",
                "eclipse_type": "Solar",
                "transit_planet": "Solar",
                "natal_target": "Sun",
                "natal_house": 1,
                "whole_sign_house": 1,
                "distance_to_natal_target": 0.4,
                "raw_score": 0.72,
                "combined_intensity_score": 0.72,
                "entry_datetime": peak_dt,
                "peak_datetime": peak_dt,
                "leave_datetime": None,
                "duration_days": 0.0,
            },
            self.profile,
        )

        self.assertLess(broad["natal_relevance"], personal["natal_relevance"])
        self.assertLess(broad["reader_facing_activity_score"], personal["reader_facing_activity_score"])

    def test_long_duration_alone_does_not_force_visibility(self):
        long_running = enrich_forecast_event(
            self._base_transit("Saturn", orb=1.8, duration_days=180.0),
            self.profile,
        )
        short_exact = enrich_forecast_event(
            self._base_transit("Sun", orb=0.1, duration_days=8.0),
            self.profile,
        )

        self.assertGreater(long_running["structural_importance"], short_exact["structural_importance"] - 0.05)
        self.assertLess(long_running["reader_facing_activity_score"], short_exact["reader_facing_activity_score"])

    def test_three_pass_transit_sets_pass_sequence(self):
        event = enrich_forecast_event(
            {
                "event_type": "transit",
                "transit_planet": "Saturn",
                "aspect": "Square",
                "natal_target": "Sun",
                "natal_house": 1,
                "maximum_orb": 3.0,
                "orb": 0.15,
                "raw_score": 0.81,
                "concentration_score": 0.81,
                "combined_intensity_score": 0.81,
                "entry_datetime": datetime(2026, 6, 1, tzinfo=timezone.utc),
                "peak_datetime": datetime(2026, 7, 1, tzinfo=timezone.utc),
                "leave_datetime": datetime(2026, 8, 1, tzinfo=timezone.utc),
                "duration_days": 61.0,
                "contact_count": 3,
            },
            self.profile,
        )

        self.assertEqual(event["pass_sequence"], "retrograde_three_pass")


if __name__ == "__main__":
    unittest.main()
