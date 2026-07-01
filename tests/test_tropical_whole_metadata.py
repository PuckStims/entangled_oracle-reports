import unittest

from selectors.variable_resolver import resolve_all


class TropicalWholeMetadataTests(unittest.TestCase):
    def test_resolver_reads_methodology_and_simple_mode_from_user_profile(self):
        payload = {
            "simple_mode": False,
            "user_profile": {
                "simple_mode": True,
                "birth_time_state": "unknown_birth_time",
                "house_system": "Whole Sign",
                "zodiac": "Tropical",
                "methodology_id": "tropical_whole",
                "methodology_label": "Tropical zodiac + Whole Sign houses",
                "methodology": {
                    "id": "tropical_whole",
                    "label": "Tropical zodiac + Whole Sign houses",
                    "zodiac": "Tropical",
                    "house_system": "Whole Sign",
                },
            },
            "standard_planets": {
                "Sun": {"sign": "Aries", "house": 1, "degree_decimal": 10.5, "retrograde": False},
                "Moon": {"sign": "Cancer", "house": 4, "degree_decimal": 2.25, "retrograde": False},
                "Mercury": {"sign": "Aries", "house": 1, "degree_decimal": 12.0, "retrograde": False},
                "Venus": {"sign": "Taurus", "house": 2, "degree_decimal": 3.0, "retrograde": False},
                "Mars": {"sign": "Leo", "house": 5, "degree_decimal": 18.0, "retrograde": False},
                "Jupiter": {"sign": "Libra", "house": 7, "degree_decimal": 9.0, "retrograde": False},
                "Saturn": {"sign": "Capricorn", "house": 10, "degree_decimal": 1.0, "retrograde": False},
                "Uranus": {"sign": "Aquarius", "house": 11, "degree_decimal": 4.0, "retrograde": False},
                "Neptune": {"sign": "Pisces", "house": 12, "degree_decimal": 7.0, "retrograde": False},
                "Pluto": {"sign": "Scorpio", "house": 8, "degree_decimal": 11.0, "retrograde": False},
                "Chiron": {"sign": "Gemini", "house": 3, "degree_decimal": 5.0, "retrograde": False},
                "North_Node": {"sign": "Sagittarius", "house": 9, "degree_decimal": 14.0, "retrograde": True},
                "South_Node": {"sign": "Gemini", "house": 3, "degree_decimal": 14.0, "retrograde": True},
                "Lilith_BML": {"sign": "Virgo", "house": 6, "degree_decimal": 21.0, "retrograde": False},
            },
            "angles": {
                "Ascendant": {"sign": "Aries", "degree_decimal": 1.0, "longitude": 1.0},
                "Midheaven": {"sign": "Capricorn", "degree_decimal": 1.0, "longitude": 271.0},
                "Descendant": {"sign": "Libra", "degree_decimal": 1.0, "longitude": 181.0},
                "Imum_Coeli": {"sign": "Cancer", "degree_decimal": 1.0, "longitude": 91.0},
                "Vertex": {"sign": "Scorpio", "degree_decimal": 1.0, "longitude": 211.0},
            },
            "houses": {f"House_{index}": {"sign": sign} for index, sign in enumerate(
                [
                    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
                ],
                start=1,
            )},
            "aspects": [],
        }

        variables = resolve_all(payload, {}, querent_name="Test")

        self.assertTrue(variables["simple_mode"])
        self.assertEqual(variables["birth_time_state"], "unknown_birth_time")
        self.assertEqual(variables["methodology_id"], "tropical_whole")
        self.assertEqual(
            variables["methodology_label"],
            "Tropical zodiac + Whole Sign houses",
        )
        self.assertEqual(variables["zodiac"], "Tropical")
        self.assertEqual(variables["house_system"], "Whole Sign")


if __name__ == "__main__":
    unittest.main()
