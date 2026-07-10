import unittest

from formulas.governance_registry import (
    PREDICTIVE_METHOD_REGISTRY,
    get_predictive_method_record,
)


class TestPredictiveMethodRegistry(unittest.TestCase):
    def test_registry_covers_all_tier_2_methods(self):
        expected = {
            "annual_profections",
            "progressions",
            "solar_arc",
            "returns",
            "lots",
            "zodiacal_releasing",
        }
        self.assertEqual(set(PREDICTIVE_METHOD_REGISTRY.keys()), expected)

    def test_get_predictive_method_record_returns_dataclass(self):
        record = get_predictive_method_record("progressions")
        self.assertIsNotNone(record)
        self.assertEqual(record.internal_key, "progressions")
        self.assertEqual(record.method_status, "production")

    def test_get_predictive_method_record_unknown_key_returns_none(self):
        self.assertIsNone(get_predictive_method_record("not_a_real_method"))

    def test_report_surface_permission_distinguishes_wired_from_unwired(self):
        # Progressions and Solar Arc are already computed into report context
        # today (moon-progression contacts -> personal_forecast, year-texture
        # progressions/solar-arc -> year_ahead); returns, lots, zodiacal
        # releasing, and annual profections are not consumed by either active
        # report path. The registry must not flatten that distinction.
        wired = get_predictive_method_record("progressions")
        self.assertIn("personal_forecast", wired.report_surface_permission)
        self.assertIn("year_ahead", wired.report_surface_permission)

        arc = get_predictive_method_record("solar_arc")
        self.assertIn("year_ahead", arc.report_surface_permission)
        self.assertNotIn("personal_forecast", arc.report_surface_permission)

        for method_key in ("annual_profections", "returns", "lots", "zodiacal_releasing"):
            record = get_predictive_method_record(method_key)
            self.assertNotIn("year_ahead", record.report_surface_permission)
            self.assertNotIn("personal_forecast", record.report_surface_permission)
            self.assertEqual(record.method_status, "internal")

    def test_to_dict_round_trips_list_fields(self):
        record = get_predictive_method_record("returns")
        data = record.to_dict()
        self.assertIsInstance(data["required_inputs"], list)
        self.assertIsInstance(data["supported_bodies_and_points"], list)
        self.assertIsInstance(data["report_surface_permission"], list)


if __name__ == "__main__":
    unittest.main()
