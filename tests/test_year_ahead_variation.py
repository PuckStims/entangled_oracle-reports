import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import (
    _apply_year_ahead_prose_variation,
    _choose_stable_variant,
    _stable_variant_index,
    _year_ahead_condition_family,
    _year_ahead_event_identity,
)


class YearAheadVariationTests(unittest.TestCase):
    def test_same_event_is_stable(self):
        event = {
            "event_type": "transit",
            "aspect": "Trine",
            "aspect_character": "flowing",
            "transit_planet": "Jupiter",
            "natal_target": "Sun",
            "peak_date": "June 28, 2026",
        }
        text = (
            "The focus is your sense of self, confidence, and the shape of a life that feels recognizably yours. "
            "Keep an eye on declaring a new self before the daily life to support it exists. "
            "Let this be a season of practical permission: deepen what is already aligned and test what wants to grow."
        )
        first = _apply_year_ahead_prose_variation(text, event)
        second = _apply_year_ahead_prose_variation(text, event)
        self.assertEqual(first, second)

    def test_different_events_can_select_different_variants(self):
        variants = (
            "The live emphasis is your ",
            "Attention gathers around your ",
            "This current lands most clearly in your ",
        )
        key_a = _year_ahead_event_identity(
            {"event_type": "transit", "aspect": "Trine", "transit_planet": "Jupiter", "natal_target": "Sun", "peak_date": "June 28, 2026"}
        )
        key_b = _year_ahead_event_identity(
            {"event_type": "transit", "aspect": "Trine", "transit_planet": "Jupiter", "natal_target": "Moon", "peak_date": "July 18, 2026"}
        )
        choice_a = _choose_stable_variant(f"{key_a}|domain_focus|1|prefix|The focus is your ", variants)
        choice_b = _choose_stable_variant(f"{key_b}|domain_focus|1|prefix|The focus is your ", variants)
        self.assertNotEqual(choice_a, choice_b)

    def test_output_is_never_empty_when_input_has_copy(self):
        event = {
            "event_type": "eclipse",
            "eclipse_type": "Solar",
            "peak_date": "August 12, 2026",
        }
        text = (
            "A new direction becomes available around communication, learning, logistics, and the stories that organize your days. "
            "Let early information remain information."
        )
        result = _apply_year_ahead_prose_variation(text, event)
        self.assertTrue(result.strip())

    def test_variation_preserves_semantic_tail_and_polarity(self):
        event = {
            "event_type": "transit",
            "aspect": "Square",
            "aspect_character": "challenging",
            "transit_planet": "Mars",
            "natal_target": "Mercury",
            "peak_date": "September 02, 2026",
        }
        text = (
            "Pressure gathers around communication, learning, logistics, and the stories that organize your days. "
            "Here, urgency can look like letting urgency, pressure, or imagination outrun clear communication. "
            "Let the pressure sharpen your priorities without turning it into a demand for self-punishment."
        )
        result = _apply_year_ahead_prose_variation(text, event)
        self.assertIn("communication, learning, logistics, and the stories that organize your days.", result)
        self.assertIn("clear communication", result)
        self.assertIn("self-punishment", result)
        self.assertEqual(_year_ahead_condition_family(event), "challenging")

    def test_variant_index_is_deterministic(self):
        idx_a = _stable_variant_index("demo-key", 5)
        idx_b = _stable_variant_index("demo-key", 5)
        self.assertEqual(idx_a, idx_b)

    def test_prefix_variation_does_not_create_ungrammatical_action_joins(self):
        supportive_event = {
            "event_type": "transit",
            "aspect": "Trine",
            "aspect_character": "flowing",
            "transit_planet": "Jupiter",
            "natal_target": "Sun",
            "peak_date": "October 10, 2026",
        }
        supportive_text = (
            "Follow the line of least unnecessary resistance, but do not let comfort substitute for participation."
        )
        supportive_result = _apply_year_ahead_prose_variation(supportive_text, supportive_event)
        self.assertNotIn("to do not let comfort", supportive_result)

        challenging_event = {
            "event_type": "transit",
            "aspect": "Square",
            "aspect_character": "challenging",
            "transit_planet": "Mars",
            "natal_target": "MC",
            "peak_date": "November 03, 2026",
        }
        challenging_text = (
            "A square can create urgency, but urgency is not the same as clarity; make room for information before forcing a final answer. "
            "Let the pressure sharpen your priorities without turning it into a demand for self-punishment."
        )
        challenging_result = _apply_year_ahead_prose_variation(challenging_text, challenging_event)
        self.assertNotIn("reveals where make room", challenging_result)
        self.assertNotIn("Choose the shift that your priorities", challenging_result)
        self.assertIn("urgency", challenging_result)


if __name__ == "__main__":
    unittest.main()
