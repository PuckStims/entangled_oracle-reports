import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import _select_client_year_texture_events


def _texture_event(
    event_type: str,
    source: str,
    target: str,
    *,
    method_variant: str | None = None,
    score: float = 0.5,
    exactness: float = 0.9,
    month: int = 7,
) -> dict:
    if method_variant is None:
        method_variant = (
            "progression_body_aspect"
            if event_type == "progression"
            else "solar_arc_body_aspect"
        )
    return {
        "event_type": event_type,
        "clock_role": "chapter",
        "transit_planet": source,
        "natal_target": target,
        "aspect": "Trine",
        "method_variant": method_variant,
        "combined_intensity_score": score,
        "reader_facing_activity_score": score,
        "exactness": exactness,
        "peak_datetime": datetime(2026, month, 10, tzinfo=timezone.utc),
    }


class YearAheadTextureSelectionTests(unittest.TestCase):
    def test_filters_raw_sandbox_style_contacts_out_of_client_report(self):
        progression_events = [
            _texture_event("progression", "Sun", "Sun", score=0.52),
            _texture_event(
                "progression",
                "Mars",
                "Venus",
                method_variant="transit_to_progressed",
                score=0.55,
            ),
            _texture_event("progression", "Mercury", "DSC", score=0.55),
            _texture_event("progression", "Venus", "Moon", score=0.2),
        ]
        solar_arc_events = [
            _texture_event("solar_arc", "Moon", "MC", score=0.5),
            _texture_event(
                "solar_arc",
                "Mars",
                "Kassandra",
                method_variant="solar_arc_asteroid_aspect",
                score=0.55,
            ),
        ]

        progressions, solar_arcs = _select_client_year_texture_events(
            progression_events,
            solar_arc_events,
        )

        self.assertEqual([event["transit_planet"] for event in progressions], ["Sun"])
        self.assertEqual([event["transit_planet"] for event in solar_arcs], ["Moon"])

    def test_caps_and_diversifies_client_texture_highlights(self):
        progression_events = [
            _texture_event("progression", "Sun", "Sun", score=0.54, month=7),
            _texture_event("progression", "Sun", "Moon", score=0.53, month=8),
            _texture_event("progression", "Sun", "Mercury", score=0.52, month=9),
            _texture_event("progression", "Mercury", "Venus", score=0.51, month=10),
            _texture_event("progression", "Venus", "Mars", score=0.5, month=11),
            _texture_event("progression", "Mars", "Jupiter", score=0.49, month=12),
        ]
        solar_arc_events = [
            _texture_event("solar_arc", "Sun", "MC", score=0.54, month=7),
            _texture_event("solar_arc", "Moon", "Sun", score=0.53, month=8),
            _texture_event("solar_arc", "Jupiter", "Moon", score=0.52, month=9),
            _texture_event("solar_arc", "Saturn", "Venus", score=0.51, month=10),
        ]

        progressions, solar_arcs = _select_client_year_texture_events(
            progression_events,
            solar_arc_events,
        )

        self.assertLessEqual(len(progressions), 4)
        self.assertLessEqual(len(solar_arcs), 3)
        self.assertEqual(
            [event["natal_target"] for event in progressions],
            ["Sun", "Moon", "Venus", "Mars"],
        )
        self.assertEqual(
            [event["natal_target"] for event in solar_arcs],
            ["MC", "Sun", "Moon"],
        )


if __name__ == "__main__":
    unittest.main()
