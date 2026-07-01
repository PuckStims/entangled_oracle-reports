import unittest

from formulas.standard.normalization import (
    normalize_angle_name,
    normalize_angle_payload,
)
from selectors.utils import get_angle_data


class AngleNormalizationTests(unittest.TestCase):
    def test_normalize_angle_name_maps_required_aliases(self):
        self.assertEqual(normalize_angle_name("ASC"), "Ascendant")
        self.assertEqual(normalize_angle_name("MC"), "Midheaven")
        self.assertEqual(normalize_angle_name("DSC"), "Descendant")
        self.assertEqual(normalize_angle_name("IC"), "Imum_Coeli")

    def test_normalize_angle_payload_rekeys_aliases(self):
        angles = normalize_angle_payload(
            {"ASC": {"longitude": 10.0}, "MC": {"longitude": 100.0}}
        )
        self.assertIn("Ascendant", angles)
        self.assertIn("Midheaven", angles)
        self.assertNotIn("ASC", angles)

    def test_get_angle_data_accepts_aliases(self):
        payload = {
            "angles": {
                "Ascendant": {"longitude": 15.0},
                "Midheaven": {"longitude": 270.0},
            }
        }
        self.assertEqual(get_angle_data(payload, "ASC")["longitude"], 15.0)
        self.assertEqual(get_angle_data(payload, "MC")["longitude"], 270.0)


if __name__ == "__main__":
    unittest.main()
