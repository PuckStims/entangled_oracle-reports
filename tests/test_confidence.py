import unittest

from formulas.standard.confidence import (
    ANGLE_DEPENDENT_UNAVAILABLE,
    APPROXIMATE_BIRTH_TIME,
    EXACT_BIRTH_TIME,
    PROVISIONAL_NEAR_HORIZON,
    UNKNOWN_BIRTH_TIME,
    assess_birth_time_confidence,
    get_angle_unavailable_confidence,
    infer_birth_time_state,
    validate_confidence_state,
)


class ConfidenceTests(unittest.TestCase):
    def test_infer_birth_time_state_covers_controlled_states(self):
        self.assertEqual(
            infer_birth_time_state(has_birth_time=True),
            EXACT_BIRTH_TIME,
        )
        self.assertEqual(
            infer_birth_time_state(has_birth_time=True, is_approximate=True),
            APPROXIMATE_BIRTH_TIME,
        )
        self.assertEqual(
            infer_birth_time_state(has_birth_time=False),
            UNKNOWN_BIRTH_TIME,
        )
        self.assertEqual(
            infer_birth_time_state(has_birth_time=True, near_horizon=True),
            PROVISIONAL_NEAR_HORIZON,
        )

    def test_assess_birth_time_confidence_marks_unknown_as_ineligible(self):
        assessment = assess_birth_time_confidence(has_birth_time=False)
        self.assertEqual(assessment.state, UNKNOWN_BIRTH_TIME)
        self.assertFalse(assessment.is_angle_eligible)
        self.assertEqual(assessment.to_dict()["missing_inputs"], ["birth_time"])

    def test_get_angle_unavailable_confidence_uses_shared_state(self):
        assessment = get_angle_unavailable_confidence("birth_time", "angles")
        self.assertEqual(assessment.state, ANGLE_DEPENDENT_UNAVAILABLE)
        self.assertEqual(
            assessment.to_dict()["missing_inputs"],
            ["birth_time", "angles"],
        )

    def test_validate_confidence_state_rejects_unknown_values(self):
        with self.assertRaises(ValueError):
            validate_confidence_state("exact")


if __name__ == "__main__":
    unittest.main()
