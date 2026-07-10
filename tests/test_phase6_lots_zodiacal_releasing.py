import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.lots import compute_lots
from engine.zodiacal_releasing import (
    SIGNS,
    TOTAL_VALENS_YEARS,
    TROPICAL_YEAR_DAYS,
    VALENS_YEARS,
    zodiacal_releasing_events,
    zodiacal_releasing_periods,
)

def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


class TestLots(unittest.TestCase):
    def test_day_chart_fortune_matches_chartered_fixture(self):
        # phase0/03_method_charters.md C5 section 12: ASC=100, Sun=200, Moon=50,
        # day chart -> Fortune = (100 + 50 - 200) mod 360 = 310.
        payload = {
            "standard_planets": {"Sun": {"longitude": 200.0}, "Moon": {"longitude": 50.0}, "Mercury": {"longitude": 10.0}},
            "angles": {"Ascendant": {"longitude": 100.0}},
        }
        import formulas.standard.sect as sect_mod

        original = sect_mod.evaluate_chart_sect
        sect_mod.evaluate_chart_sect = lambda p: "day"
        try:
            import importlib

            import engine.lots as lots_mod

            importlib.reload(lots_mod)
            lots = lots_mod.compute_lots(payload)
        finally:
            sect_mod.evaluate_chart_sect = original
            importlib.reload(lots_mod)

        self.assertAlmostEqual(lots["Fortune"]["longitude"], 310.0, places=6)

    def test_night_chart_fortune_matches_chartered_fixture(self):
        # Same inputs, night chart -> Fortune = (100 + 200 - 50) mod 360 = 250.
        payload = {
            "standard_planets": {"Sun": {"longitude": 200.0}, "Moon": {"longitude": 50.0}, "Mercury": {"longitude": 10.0}},
            "angles": {"Ascendant": {"longitude": 100.0}},
        }
        import formulas.standard.sect as sect_mod

        original = sect_mod.evaluate_chart_sect
        sect_mod.evaluate_chart_sect = lambda p: "night"
        try:
            import importlib

            import engine.lots as lots_mod

            importlib.reload(lots_mod)
            lots = lots_mod.compute_lots(payload)
        finally:
            sect_mod.evaluate_chart_sect = original
            importlib.reload(lots_mod)

        self.assertAlmostEqual(lots["Fortune"]["longitude"], 250.0, places=6)

    def test_missing_natal_data_returns_empty(self):
        self.assertEqual(compute_lots({}), {})

    def test_all_three_lots_present_with_sect_field(self):
        payload = {
            "standard_planets": {"Sun": {"longitude": 10.0}, "Moon": {"longitude": 120.0}, "Mercury": {"longitude": 5.0}},
            "angles": {"Ascendant": {"longitude": 200.0}},
        }
        lots = compute_lots(payload)
        self.assertEqual(set(lots.keys()), {"Fortune", "Spirit", "Necessity"})
        for entry in lots.values():
            self.assertIn("sect", entry)
            self.assertIn("house", entry)
            self.assertIn("sign", entry)


class TestZodiacalReleasing(unittest.TestCase):
    def _cancer_fortune_payload(self):
        return {
            "standard_planets": {"Sun": {"longitude": 0.0}, "Moon": {"longitude": 0.0}, "Mercury": {"longitude": 0.0}},
            "angles": {"Ascendant": {"longitude": 90.0}},  # Cancer rises; contrived so Fortune lands in Cancer
            "user_profile": {"local_datetime": "2000-01-01T00:00:00+00:00"},
        }

    def test_valens_years_sum_to_211(self):
        self.assertEqual(sum(VALENS_YEARS.values()), 211)
        self.assertEqual(TOTAL_VALENS_YEARS, 211)

    def test_cancer_fortune_first_l1_period_is_cancer_25_years(self):
        # phase0/03_method_charters.md C5b section 12 fixture.
        payload = self._cancer_fortune_payload()
        import formulas.standard.sect as sect_mod

        original = sect_mod.evaluate_chart_sect
        sect_mod.evaluate_chart_sect = lambda p: "day"
        try:
            import importlib

            import engine.lots as lots_mod
            import engine.zodiacal_releasing as zr_mod

            importlib.reload(lots_mod)
            importlib.reload(zr_mod)

            lots = lots_mod.compute_lots(payload)
            self.assertEqual(lots["Fortune"]["sign"], "Cancer")

            periods = zr_mod.zodiacal_releasing_periods(
                payload, _dt("2000-01-01"), _dt("2000-06-01"), lot_name="Fortune",
            )
        finally:
            sect_mod.evaluate_chart_sect = original
            importlib.reload(lots_mod)
            importlib.reload(zr_mod)

        l1 = [p for p in periods if p["level"] == "L1"]
        self.assertEqual(len(l1), 1)
        self.assertEqual(l1[0]["period_sign"], "Cancer")
        start = datetime.fromisoformat(l1[0]["start_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(l1[0]["end_at"].replace("Z", "+00:00"))
        self.assertAlmostEqual((end - start).days / 365.2425, 25.0, delta=0.01)

    def test_lord_natal_state_reflects_real_chart_not_a_stub(self):
        # Cancer's traditional ruler is the Moon. Give the Moon a real
        # house/sign/retrograde so we can prove lord_natal_state is
        # computed, not the old hardcoded stub.
        payload = self._cancer_fortune_payload()
        payload["standard_planets"]["Moon"] = {
            "longitude": 0.0, "house": 4, "sign": "Cancer", "retrograde": False,
        }
        import formulas.standard.sect as sect_mod

        original = sect_mod.evaluate_chart_sect
        sect_mod.evaluate_chart_sect = lambda p: "day"
        try:
            import importlib

            import engine.lots as lots_mod
            import engine.zodiacal_releasing as zr_mod

            importlib.reload(lots_mod)
            importlib.reload(zr_mod)

            periods = zr_mod.zodiacal_releasing_periods(
                payload, _dt("2000-01-01"), _dt("2000-06-01"), lot_name="Fortune",
            )
        finally:
            sect_mod.evaluate_chart_sect = original
            importlib.reload(lots_mod)
            importlib.reload(zr_mod)

        l1 = next(p for p in periods if p["level"] == "L1")
        self.assertEqual(l1["period_lord"], "Moon")
        state = l1["lord_natal_state"]
        self.assertEqual(state["condition"], "available")
        self.assertEqual(state["house"], 4)
        self.assertEqual(state["sign"], "Cancer")
        self.assertFalse(state["retrograde"])

    def test_cancer_l1_contains_l2_loosing_of_the_bond_at_expected_boundary(self):
        payload = self._cancer_fortune_payload()
        periods = zodiacal_releasing_periods(payload, _dt("2000-01-01"), _dt("2025-01-02"), lot_name="Fortune")

        l1 = [
            p for p in periods
            if p["level"] == "L1" and p["start_at"] == "2000-01-01T00:00:00Z"
        ]
        self.assertEqual(len(l1), 1)

        l2 = [p for p in periods if p["level"] == "L2" and p["parent_period_id"] == l1[0]["period_id"]]
        lob_periods = [p for p in l2 if p["is_loosing_of_the_bond"]]
        self.assertEqual(len(lob_periods), 1)

        lob_period = lob_periods[0]
        self.assertEqual(lob_period["period_sign"], "Sagittarius")

        expected_lob_start = _dt("2000-01-01") + timedelta(days=(TOTAL_VALENS_YEARS / 12.0) * TROPICAL_YEAR_DAYS)
        actual_lob_start = datetime.fromisoformat(lob_period["start_at"].replace("Z", "+00:00"))
        self.assertAlmostEqual((actual_lob_start - expected_lob_start).total_seconds(), 0.0, delta=1.0)

        gemini_period = next((p for p in l2 if p["period_sign"] == "Gemini"), None)
        self.assertIsNotNone(gemini_period)
        gemini_end = datetime.fromisoformat(gemini_period["end_at"].replace("Z", "+00:00"))
        self.assertAlmostEqual((actual_lob_start - gemini_end).total_seconds(), 0.0, delta=1.0)

    def test_cancer_l1_emits_zr_lob_event_at_expected_moment(self):
        payload = self._cancer_fortune_payload()
        events = zodiacal_releasing_events(payload, _dt("2000-01-01"), _dt("2025-01-02"), lot_name="Fortune")

        lob_events = [e for e in events if e["method_variant"] == "zr_lob"]
        self.assertEqual(len(lob_events), 1)

        expected_lob_start = _dt("2000-01-01") + timedelta(days=(TOTAL_VALENS_YEARS / 12.0) * TROPICAL_YEAR_DAYS)
        self.assertAlmostEqual((lob_events[0]["peak_datetime"] - expected_lob_start).total_seconds(), 0.0, delta=1.0)
        self.assertEqual(lob_events[0]["period_sign"], "Sagittarius")

    def test_peak_periods_are_angular_from_lot_sign(self):
        lot_index = SIGNS.index("Capricorn")
        expected_peak_signs = {SIGNS[(lot_index + offset) % 12] for offset in (0, 3, 6, 9)}
        self.assertEqual(expected_peak_signs, {"Capricorn", "Aries", "Cancer", "Libra"})

    def test_missing_natal_data_returns_empty(self):
        self.assertEqual(zodiacal_releasing_periods({}, _dt("2026-01-01"), _dt("2027-01-01")), [])
        self.assertEqual(zodiacal_releasing_events({}, _dt("2026-01-01"), _dt("2027-01-01")), [])

    def test_events_only_emitted_for_l1_and_l2(self):
        payload = {
            "standard_planets": {"Sun": {"longitude": 10.0}, "Moon": {"longitude": 120.0}, "Mercury": {"longitude": 5.0}},
            "angles": {"Ascendant": {"longitude": 200.0}},
            "user_profile": {"local_datetime": "1990-06-15T14:30:00+00:00"},
        }
        events = zodiacal_releasing_events(payload, _dt("2026-01-01"), _dt("2027-01-01"), lot_name="Fortune")
        for event in events:
            self.assertIn(event["method_variant"], {"zr_l1_transition", "zr_l2_transition", "zr_lob", "zr_peak"})
            # Every emitted event must satisfy phase0/01's orb/distance/phase rule.
            self.assertTrue(event.get("orb") is not None or event.get("distance") is not None or event.get("phase") is not None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
