import unittest

from engine.transit_engine import _filter_moon_progression_events


class PersonalForecastMoonProgressionFilterTests(unittest.TestCase):
    def test_keeps_only_modifier_scale_moon_progressions(self):
        events = [
            {
                "event_type": "progression",
                "transit_planet": "Moon",
                "natal_target": "Sun",
                "method_variant": "progression_body_aspect",
                "clock_role": "modifier",
            },
            {
                "event_type": "progression",
                "transit_planet": "Sun",
                "natal_target": "Moon",
                "method_variant": "transit_to_progressed",
                "clock_role": "chapter",
            },
            {
                "event_type": "progression",
                "transit_planet": "Moon",
                "natal_target": "Sun",
                "method_variant": "progression_lunation_phase",
                "clock_role": "trigger",
            },
        ]

        kept = _filter_moon_progression_events(events)

        self.assertEqual(kept, [events[0]])


if __name__ == "__main__":
    unittest.main()
