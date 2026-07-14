import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import _build_chart_characteristics, _build_natal_positions


def _card_map(characteristics: dict) -> dict[str, dict]:
    return {card["label"]: card for card in characteristics.get("cards", [])}


def _exact_payload() -> dict:
    planets = {
        "Sun": {"sign": "Aries", "degree": 1, "minute": 0, "house": 1},
        "Moon": {"sign": "Aries", "degree": 12, "minute": 0, "house": 1},
        "Mercury": {"sign": "Taurus", "degree": 5, "minute": 0, "house": 2},
        "Venus": {"sign": "Gemini", "degree": 7, "minute": 0, "house": 3},
        "Mars": {"sign": "Cancer", "degree": 9, "minute": 0, "house": 4},
        "Jupiter": {"sign": "Scorpio", "degree": 11, "minute": 0, "house": 10},
        "Saturn": {"sign": "Virgo", "degree": 13, "minute": 0, "house": 11},
        "Uranus": {"sign": "Libra", "degree": 15, "minute": 0, "house": 12},
        "Neptune": {"sign": "Scorpio", "degree": 17, "minute": 0, "house": 12},
        "Pluto": {"sign": "Scorpio", "degree": 19, "minute": 0, "house": 12},
    }
    for body in planets.values():
        body["formatted"] = f"{body['degree']}°{int(body['minute']):02d}' {body['sign']}"

    return {
        "user_profile": {"simple_mode": False},
        "standard_planets": planets,
        "angles": {
            "Ascendant": {"sign": "Aries", "degree": 10, "minute": 0, "formatted": "10°00' Aries"},
            "Midheaven": {"sign": "Capricorn", "degree": 5, "minute": 0, "formatted": "5°00' Capricorn"},
        },
    }


def _dob_only_payload() -> dict:
    payload = _exact_payload()
    payload["user_profile"] = {"simple_mode": True}
    return payload


class YearAheadChartCharacteristicsTests(unittest.TestCase):
    def test_exact_time_characteristics_are_available(self):
        characteristics = _build_chart_characteristics(_exact_payload())
        cards = _card_map(characteristics)

        self.assertTrue(characteristics["has_exact_birth_time"])
        self.assertEqual(characteristics["tracked_body_count"], 10)
        self.assertEqual(cards["Leading element"]["value"], "Water leads (4)")
        self.assertEqual(cards["Leading modality"]["value"], "Tie: Cardinal, Fixed (4 each)")
        self.assertEqual(cards["Hemisphere balance"]["value"], "Upper 5 · Lower 5")
        self.assertEqual(cards["Eastern / Western"]["value"], "Eastern 9 · Western 1")
        self.assertEqual(cards["House concentration"]["value"], "12th house (3)")
        self.assertEqual(cards["House stellium indicator"]["value"], "12th house (3)")
        self.assertEqual(cards["Sign stellium indicator"]["value"], "Scorpio (3)")

    def test_dob_only_withholds_house_and_angle_dependence(self):
        characteristics = _build_chart_characteristics(_dob_only_payload())
        cards = _card_map(characteristics)

        self.assertFalse(characteristics["has_exact_birth_time"])
        self.assertEqual(cards["Leading element"]["value"], "Water leads (4)")
        self.assertNotIn("Hemisphere balance", cards)
        self.assertNotIn("Angular emphasis", cards)
        self.assertNotIn("House concentration", cards)
        self.assertNotIn("House stellium indicator", cards)

    def test_dob_only_natal_positions_hide_houses_and_angles(self):
        positions = _build_natal_positions(_dob_only_payload())
        self.assertEqual(len(positions), 10)
        self.assertTrue(all(row["house"] == "—" for row in positions))
        self.assertNotIn("Ascendant", {row["name"] for row in positions})
        self.assertNotIn("Midheaven", {row["name"] for row in positions})


if __name__ == "__main__":
    unittest.main()
