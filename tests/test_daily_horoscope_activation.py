"""
tests/test_daily_horoscope_activation.py

Regression coverage for Daily Horoscope's "today's activation" selection
(selectors/variable_resolver.py) and its supporting engine functions
(engine/transit_engine.py's compute_daily_activation_transits and the
Whole Sign house fix).

Two real bugs were found and fixed while building this feature, and both
get a permanent test here so they cannot silently regress:

1. The pre-existing activation-house math used a degree-offset-from-
   Ascendant formula (Equal House), not the Whole Sign math used
   everywhere else in the engine. It gave the wrong house whenever the
   Ascendant wasn't near 0 degrees of its sign.
2. The first attempt at "today's activation" reused Year Ahead's wide
   transit orbs (3-4 degrees), which are correct for week/month-scale
   forecasting but wrong for a same-day decision: a 120-day empirical
   sweep against a real chart showed Neptune winning 62% of days
   outright, and the Moon fallback never fired once, because Neptune's
   near-standstill daily motion keeps it "in range" of a 3-degree orb
   for weeks or months at a time.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from collections import Counter
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.transit_engine import (
    _whole_sign_house,
    DAILY_ACTIVATION_PLANETS,
    DAILY_ACTIVATION_ORB,
    compute_daily_activation_transits,
)
from selectors.variable_resolver import resolve_all


def _payload_stub(ascendant_longitude=25.0):
    """
    A minimal but complete natal payload for resolve_all(). Ascendant is
    deliberately NOT at 0 degrees of its sign (25 degrees Aries) — the
    Equal-House-vs-Whole-Sign bug only shows up off that boundary, so a
    stub with Ascendant at exactly 0 degrees would hide it.
    """
    return {
        "simple_mode": True,
        "user_profile": {"house_system": "Whole Sign"},
        "standard_planets": {
            "Sun": {"sign": "Aries", "house": 1, "degree_decimal": 10.0, "longitude": 10.0},
            "Moon": {"sign": "Leo", "house": 5, "degree_decimal": 20.0, "longitude": 140.0},
            "Mercury": {"sign": "Aries", "house": 1, "degree_decimal": 11.0, "longitude": 11.0},
            "Venus": {"sign": "Taurus", "house": 2, "degree_decimal": 5.0, "longitude": 35.0},
            "Mars": {"sign": "Gemini", "house": 3, "degree_decimal": 15.0, "longitude": 75.0},
            "Jupiter": {"sign": "Cancer", "house": 4, "degree_decimal": 4.0, "longitude": 94.0},
            "Saturn": {"sign": "Aquarius", "house": 11, "degree_decimal": 18.0, "longitude": 318.0},
            "Uranus": {"sign": "Capricorn", "house": 10, "degree_decimal": 7.0, "longitude": 277.0},
            "Neptune": {"sign": "Capricorn", "house": 10, "degree_decimal": 8.0, "longitude": 278.0},
            "Pluto": {"sign": "Scorpio", "house": 8, "degree_decimal": 12.0, "longitude": 222.0},
            "Chiron": {"sign": "Virgo", "house": 6, "degree_decimal": 9.0, "longitude": 159.0},
            "North_Node": {"sign": "Sagittarius", "house": 9, "degree_decimal": 13.0, "longitude": 253.0},
            "South_Node": {"sign": "Gemini", "house": 3, "degree_decimal": 13.0, "longitude": 73.0},
            "Lilith_BML": {"sign": "Capricorn", "house": 1, "degree_decimal": 2.0, "longitude": 272.0},
        },
        "angles": {
            "Ascendant": {"sign": "Aries", "degree_decimal": ascendant_longitude, "longitude": ascendant_longitude},
            "Midheaven": {"sign": "Capricorn", "degree_decimal": 0.0, "longitude": 270.0},
            "Descendant": {"sign": "Libra", "degree_decimal": 0.0, "longitude": 180.0},
            "Imum_Coeli": {"sign": "Cancer", "degree_decimal": 0.0, "longitude": 90.0},
            "Vertex": {"sign": "Scorpio", "degree_decimal": 0.0, "longitude": 210.0},
        },
        "aspects": [],
    }


class TestWholeSignHouseFix(unittest.TestCase):
    """Locks in the Equal-House-vs-Whole-Sign bug fix."""

    def test_same_sign_as_ascendant_is_house_one_even_off_zero_degrees(self):
        # Ascendant at 25 degrees Aries, body at 5 degrees Aries: same
        # sign as the Ascendant, so Whole Sign says house 1 regardless
        # of the exact degree gap.
        self.assertEqual(_whole_sign_house(5.0, 25.0), 1)

    def test_old_equal_house_formula_gave_a_different_wrong_answer(self):
        # Documents the actual bug that shipped: the old degree-offset
        # formula said house 12 for this exact case.
        old_formula_result = int((5.0 - 25.0) % 360 // 30) + 1
        self.assertEqual(old_formula_result, 12)
        self.assertNotEqual(old_formula_result, _whole_sign_house(5.0, 25.0))

    def test_next_sign_is_house_two(self):
        self.assertEqual(_whole_sign_house(40.0, 25.0), 2)

    def test_formulas_agree_when_ascendant_is_at_zero_degrees(self):
        # At exactly 0 degrees of its sign, Equal House and Whole Sign
        # coincide — this is why a stub with Ascendant at 0 would have
        # hidden the bug.
        old_formula_result = int((40.0 - 0.0) % 360 // 30) + 1
        self.assertEqual(old_formula_result, _whole_sign_house(40.0, 0.0))


class TestDailyActivationTransitScan(unittest.TestCase):

    def test_moon_never_appears_in_daily_activation_planets(self):
        # The Moon keeps its own always-available house-based fallback;
        # it should never come from this same-day aspect scan.
        self.assertNotIn("Moon", DAILY_ACTIVATION_PLANETS.values())

    def test_slower_planets_get_tighter_orbs_than_faster_ones(self):
        # The calibration lesson from the empirical sweep: without this,
        # a slow planet lingers near "exact" for weeks and structurally
        # dominates every day's selection.
        self.assertLess(DAILY_ACTIVATION_ORB["Pluto"], DAILY_ACTIVATION_ORB["Sun"])
        self.assertLess(DAILY_ACTIVATION_ORB["Neptune"], DAILY_ACTIVATION_ORB["Jupiter"])
        self.assertLess(DAILY_ACTIVATION_ORB["Saturn"], DAILY_ACTIVATION_ORB["Mars"])

    def test_returns_results_sorted_by_score_descending(self):
        payload = _payload_stub()
        moment = datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc)
        results = compute_daily_activation_transits(payload, moment)
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_every_result_stays_within_its_planets_configured_orb(self):
        payload = _payload_stub()
        moment = datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc)
        results = compute_daily_activation_transits(payload, moment)
        self.assertTrue(results, "expected at least one in-orb contact for this stub chart on this date")
        for event in results:
            self.assertLessEqual(event["orb"], DAILY_ACTIVATION_ORB[event["transit_planet"]])


class TestActivationDistributionBalance(unittest.TestCase):
    """
    Regression guard for the Neptune-dominance bug: reusing Year Ahead's
    wide orbs let one planet structurally win most days. Samples a month
    against a fixed chart and asserts no planet can dominate that way.
    """

    def test_no_single_planet_dominates_a_sampled_month(self):
        payload = _payload_stub()
        winners = Counter()
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for i in range(30):
            moment = start + timedelta(days=i)
            results = compute_daily_activation_transits(payload, moment)
            if results:
                results.sort(key=lambda e: e["score"], reverse=True)
                winners[results[0]["transit_planet"]] += 1

        self.assertTrue(winners, "expected at least some days to produce a winning transit")
        _, top_count = winners.most_common(1)[0]
        self.assertLessEqual(
            top_count / 30,
            0.5,
            f"a single planet should not structurally dominate 30 sampled days: {dict(winners)}",
        )


class TestActivationPriorityChain(unittest.TestCase):
    """
    Tests the priority wiring in resolve_all() with controlled fake
    engine results, independent of real ephemeris timing — station beats
    transit beats Moon fallback.
    """

    def test_station_outranks_a_transit_on_the_same_day(self):
        fake_station = [{"transit_planet": "Mercury", "score": 0.2}]
        fake_transit = [{"transit_planet": "Pluto", "score": 0.99}]  # would win if stations were empty

        with patch("engine.transit_engine.scan_stations", return_value=fake_station):
            with patch("engine.transit_engine.compute_daily_activation_transits", return_value=fake_transit):
                variables = resolve_all(_payload_stub(), {}, querent_name="Priority Test")

        self.assertEqual(variables["activation_planet"], "Mercury")
        self.assertEqual(variables["activation_house_number"], 0)
        self.assertEqual(variables["natal_house_name"], "")
        self.assertIn("house and angle localization are withheld", variables["activation_basis_line"])

    def test_transit_wins_when_no_station_fires(self):
        with patch("engine.transit_engine.scan_stations", return_value=[]):
            with patch(
                "engine.transit_engine.compute_daily_activation_transits",
                return_value=[{"transit_planet": "Venus", "score": 0.5}],
            ):
                variables = resolve_all(_payload_stub(), {}, querent_name="Priority Test")

        self.assertEqual(variables["activation_planet"], "Venus")

    def test_falls_back_to_moon_when_nothing_fires(self):
        with patch("engine.transit_engine.scan_stations", return_value=[]):
            with patch("engine.transit_engine.compute_daily_activation_transits", return_value=[]):
                variables = resolve_all(_payload_stub(), {}, querent_name="Priority Test")

        self.assertEqual(variables["activation_planet"], "Moon")

    def test_multiple_transit_candidates_pick_the_highest_score(self):
        with patch("engine.transit_engine.scan_stations", return_value=[]):
            with patch(
                "engine.transit_engine.compute_daily_activation_transits",
                return_value=[
                    {"transit_planet": "Jupiter", "score": 0.3},
                    {"transit_planet": "Saturn", "score": 0.7},
                    {"transit_planet": "Sun", "score": 0.5},
                ],
            ):
                variables = resolve_all(_payload_stub(), {}, querent_name="Priority Test")

        self.assertEqual(variables["activation_planet"], "Saturn")

    def test_report_start_date_controls_daily_display_and_activation_scan(self):
        report_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with patch("engine.transit_engine.scan_stations", return_value=[]) as scan_stations:
            with patch("engine.transit_engine.compute_daily_activation_transits", return_value=[]) as activation_scan:
                variables = resolve_all(
                    _payload_stub(),
                    {},
                    querent_name="Date Control Test",
                    report_start_date=report_date,
                )

        self.assertEqual(variables["display_date"], "January 01, 2026")
        self.assertEqual(variables["report_start_date"], "January 01, 2026")
        self.assertEqual(variables["day_ruler_name"], "Jupiter")

        station_start = scan_stations.call_args.args[1]
        station_end = scan_stations.call_args.args[2]
        self.assertEqual(station_start, report_date)
        self.assertEqual(station_end, report_date + timedelta(days=1))

        activation_moment = activation_scan.call_args.args[1]
        self.assertEqual(activation_moment, report_date)


if __name__ == "__main__":
    unittest.main(verbosity=2)
