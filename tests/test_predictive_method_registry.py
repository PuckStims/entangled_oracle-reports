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

    def test_report_surface_permission_distinguishes_production_from_scaffold(self):
        # Progressions and Solar Arc remain production report methods where
        # wired. Tier 5 promotes annual profections, returns, and Zodiacal
        # Releasing as visible scaffold/tracking surfaces, while Lots remain
        # an internal substrate for Zodiacal Releasing rather than standalone
        # report content.
        wired = get_predictive_method_record("progressions")
        self.assertIn("personal_forecast", wired.report_surface_permission)
        self.assertIn("year_ahead", wired.report_surface_permission)

        arc = get_predictive_method_record("solar_arc")
        self.assertIn("year_ahead", arc.report_surface_permission)
        self.assertNotIn("personal_forecast", arc.report_surface_permission)

        for method_key in ("annual_profections", "returns", "zodiacal_releasing"):
            record = get_predictive_method_record(method_key)
            self.assertIn("year_ahead", record.report_surface_permission)
            self.assertIn("personal_forecast", record.report_surface_permission)
            self.assertEqual(record.method_status, "scaffolded_report_surface")

        lots = get_predictive_method_record("lots")
        self.assertNotIn("year_ahead", lots.report_surface_permission)
        self.assertNotIn("personal_forecast", lots.report_surface_permission)
        self.assertEqual(lots.method_status, "internal")

    def test_to_dict_round_trips_list_fields(self):
        record = get_predictive_method_record("returns")
        data = record.to_dict()
        self.assertIsInstance(data["required_inputs"], list)
        self.assertIsInstance(data["supported_bodies_and_points"], list)
        self.assertIsInstance(data["report_surface_permission"], list)

    def test_every_method_answers_the_four_scope_questions(self):
        # Tier 2 requires each method to self-answer what it calculates, what
        # it doesn't, what it can claim, and what it merely contextualizes.
        # Enforce that the notes field actually carries this, not just a
        # generic description, so a future entry can't skip it silently.
        for method_key, record in PREDICTIVE_METHOD_REGISTRY.items():
            for phrase in ("Calculates:", "Does not calculate:", "Can claim:", "Merely contextualizes:"):
                self.assertIn(
                    phrase, record.notes,
                    f"{method_key} notes missing '{phrase}'",
                )


if __name__ == "__main__":
    unittest.main()
