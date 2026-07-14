import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import _build_annual_rhythm_quarters, _build_month_continuity


def _event(
    title: str,
    event_type: str,
    cycle_id: str = "",
    score: float = 0.8,
    duration_days: float = 30,
) -> dict:
    return {
        "title": title,
        "event_type": event_type,
        "cycle_id": cycle_id,
        "combined_intensity_score": score,
        "duration_days": duration_days,
    }


class YearAheadMonthContinuityTests(unittest.TestCase):
    def test_shared_cycle_continuity_uses_real_cycle(self):
        months = [
            {
                "name": "June 2026",
                "activated_domains": [{"domain": "Career / Public Life"}],
                "events": [_event("Saturn Sextile natal Saturn", "transit", "saturn-cycle")],
            },
            {
                "name": "July 2026",
                "activated_domains": [{"domain": "Career / Public Life"}],
                "events": [_event("Saturn Sextile natal Saturn", "transit", "saturn-cycle", 0.9, 45)],
            },
        ]
        landmarks = [{"cycle_id": "saturn-cycle", "title": "Saturn Sextile natal Saturn"}]

        result = _build_month_continuity(months, landmarks)
        july = result[1]

        self.assertIn("Saturn Sextile natal Saturn", july["continuity_from_previous"])
        self.assertEqual(july["continuity_signals"][0]["cycle_id"], "saturn-cycle")
        self.assertEqual(july["continuity_signals"][0]["kind"], "shared_cycle")

    def test_domain_shift_continuity_references_real_domains_and_family(self):
        months = [
            {
                "name": "June 2026",
                "activated_domains": [{"domain": "Home / Family"}],
                "events": [_event("Jupiter enters your 4th house", "ingress")],
            },
            {
                "name": "July 2026",
                "activated_domains": [{"domain": "Career / Public Life"}],
                "events": [_event("Saturn Sextile natal Saturn", "transit")],
            },
        ]

        result = _build_month_continuity(months, [])
        july = result[1]

        self.assertIn("Home / Family", july["continuity_from_previous"])
        self.assertIn("Career / Public Life", july["continuity_from_previous"])
        self.assertIn("natal transit activity", july["continuity_from_previous"])
        self.assertEqual(july["continuity_signals"][0]["kind"], "domain_shift")

    def test_no_signal_omits_continuity(self):
        months = [
            {
                "name": "June 2026",
                "activated_domains": [],
                "events": [],
            },
            {
                "name": "July 2026",
                "activated_domains": [],
                "events": [],
            },
        ]

        result = _build_month_continuity(months, [])
        self.assertEqual(result[0]["continuity_into_next"], "")
        self.assertEqual(result[1]["continuity_from_previous"], "")
        self.assertEqual(result[0]["continuity_signals"], [])
        self.assertEqual(result[1]["continuity_signals"], [])

    def test_annual_rhythm_cards_use_month_data_instead_of_static_seasons(self):
        months = [
            {
                "name": "March 2026",
                "short_name": "Mar",
                "arc_score": 0.22,
                "activated_domains": [{"domain": "Home / Family", "score": 0.20}],
            },
            {
                "name": "April 2026",
                "short_name": "Apr",
                "arc_score": 0.74,
                "activated_domains": [{"domain": "Career / Public Life", "score": 0.80}],
            },
            {
                "name": "May 2026",
                "short_name": "May",
                "arc_score": 0.38,
                "activated_domains": [{"domain": "Career / Public Life", "score": 0.30}],
            },
        ]

        cards = _build_annual_rhythm_quarters(months, all_events=[], house_domains={})

        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["season_name"], "April 2026 Carries the Emphasis")
        self.assertEqual(cards[0]["peak_month"], "April 2026")
        self.assertEqual(cards[0]["quiet_month"], "March 2026")
        self.assertIn("April 2026", cards[0]["summary"])
        self.assertIn("Career / Public Life", cards[0]["summary"])
        self.assertNotIn(cards[0]["season_name"], {"Winter", "Spring", "Summer", "Autumn"})


if __name__ == "__main__":
    unittest.main()
