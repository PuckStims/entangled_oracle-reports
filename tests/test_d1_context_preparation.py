"""
tests/test_d1_context_preparation.py

Track D1 — Context Preparation: Personal Forecast and Daily Horoscope.

Covers:
  - _normalize_forecast_event produces a consistent shape for all event types
    and for None/missing input.
  - _personal_forecast_event_label produces correct human-readable strings.
  - Theme cards include normalized anchor_event and supporting_events even
    when no prose card exists for the theme+character combination.
  - _build_horoscope_context always returns secondary_activation_line.
"""

import os
import sys
import types
import unittest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import generate
from generate import (
    _normalize_forecast_event,
    _personal_forecast_event_label,
)


# ── Shared event stubs ─────────────────────────────────────────────────────────

def _transit_event(**overrides):
    base = {
        "event_type": "transit",
        "transit_planet": "Jupiter",
        "aspect": "Trine",
        "natal_target": "Moon",
        "natal_house": 4,
        "aspect_character": "flowing",
        "peak_date": "2026-08-15",
        "entry_date": "2026-08-01",
        "combined_intensity_score": 0.75,
    }
    base.update(overrides)
    return base


def _ingress_event(**overrides):
    base = {
        "event_type": "ingress",
        "transit_planet": "Saturn",
        "house_number": 8,
        "aspect_character": "challenging",
        "peak_date": "2026-09-01",
        "combined_intensity_score": 0.55,
    }
    base.update(overrides)
    return base


def _station_event(**overrides):
    base = {
        "event_type": "station",
        "transit_planet": "Mercury",
        "station_type": "Direct",
        "peak_date": "2026-07-20",
        "combined_intensity_score": 0.45,
    }
    base.update(overrides)
    return base


def _eclipse_event(**overrides):
    base = {
        "event_type": "eclipse",
        "eclipse_type": "solar",
        "natal_target": "Sun",
        "natal_house": 10,
        "peak_date": "2026-10-02",
        "combined_intensity_score": 0.88,
    }
    base.update(overrides)
    return base


# ── _personal_forecast_event_label ────────────────────────────────────────────

class TestEventLabel(unittest.TestCase):

    def test_transit_label(self):
        label = _personal_forecast_event_label(_transit_event())
        self.assertEqual(label, "Jupiter Trine Moon")

    def test_ingress_label(self):
        label = _personal_forecast_event_label(_ingress_event())
        self.assertEqual(label, "Saturn enters House 8")

    def test_station_direct_label(self):
        label = _personal_forecast_event_label(_station_event())
        self.assertEqual(label, "Mercury Direct")

    def test_station_retrograde_label(self):
        label = _personal_forecast_event_label(_station_event(station_type="Retrograde"))
        self.assertEqual(label, "Mercury Retrograde")

    def test_eclipse_label(self):
        label = _personal_forecast_event_label(_eclipse_event())
        self.assertEqual(label, "Solar Eclipse on Sun")

    def test_unknown_type_returns_empty(self):
        label = _personal_forecast_event_label({"event_type": "convergence"})
        self.assertEqual(label, "")

    def test_sparse_transit_omits_missing_parts(self):
        label = _personal_forecast_event_label({"event_type": "transit", "transit_planet": "Mars"})
        self.assertEqual(label, "Mars")

    def test_ingress_no_house_omits_house_token(self):
        label = _personal_forecast_event_label({"event_type": "ingress", "transit_planet": "Pluto"})
        self.assertEqual(label, "Pluto enters")


# ── _normalize_forecast_event ─────────────────────────────────────────────────

REQUIRED_KEYS = {
    "label", "event_type", "peak_date", "transit_planet",
    "aspect", "natal_target", "natal_house", "score", "character",
}


class TestNormalizeForecastEvent(unittest.TestCase):

    def _assert_shape(self, result):
        self.assertIsInstance(result, dict)
        for key in REQUIRED_KEYS:
            self.assertIn(key, result, f"Key '{key}' missing from normalized event")

    def test_none_input_returns_empty_valid_shape(self):
        result = _normalize_forecast_event(None)
        self._assert_shape(result)
        self.assertEqual(result["label"], "")
        self.assertEqual(result["event_type"], "")
        self.assertEqual(result["natal_house"], 0)
        self.assertEqual(result["score"], 0.0)

    def test_non_dict_input_returns_empty_valid_shape(self):
        result = _normalize_forecast_event("not a dict")
        self._assert_shape(result)

    def test_transit_normalized_correctly(self):
        result = _normalize_forecast_event(_transit_event())
        self._assert_shape(result)
        self.assertEqual(result["label"], "Jupiter Trine Moon")
        self.assertEqual(result["event_type"], "transit")
        self.assertEqual(result["transit_planet"], "Jupiter")
        self.assertEqual(result["aspect"], "Trine")
        self.assertEqual(result["natal_target"], "Moon")
        self.assertEqual(result["natal_house"], 4)
        self.assertAlmostEqual(result["score"], 0.75)
        self.assertEqual(result["character"], "flowing")
        self.assertEqual(result["peak_date"], "2026-08-15")

    def test_ingress_normalized_correctly(self):
        result = _normalize_forecast_event(_ingress_event())
        self._assert_shape(result)
        self.assertEqual(result["label"], "Saturn enters House 8")
        self.assertEqual(result["natal_house"], 8)
        self.assertEqual(result["character"], "challenging")

    def test_station_direct_character_is_flowing(self):
        result = _normalize_forecast_event(_station_event())
        self.assertEqual(result["character"], "flowing")

    def test_station_retrograde_character_is_challenging(self):
        result = _normalize_forecast_event(_station_event(station_type="Retrograde"))
        self.assertEqual(result["character"], "challenging")

    def test_eclipse_normalized_correctly(self):
        result = _normalize_forecast_event(_eclipse_event())
        self._assert_shape(result)
        self.assertEqual(result["label"], "Solar Eclipse on Sun")

    def test_peak_date_falls_back_to_entry_date(self):
        event = _transit_event(peak_date=None, entry_date="2026-08-01")
        result = _normalize_forecast_event(event)
        self.assertEqual(result["peak_date"], "2026-08-01")

    def test_raw_event_fields_not_forwarded(self):
        # Only the normalized subset should appear — no raw engine fields.
        event = _transit_event()
        event["combined_intensity_score"] = 0.99
        result = _normalize_forecast_event(event)
        self.assertNotIn("combined_intensity_score", result)
        self.assertNotIn("entry_date", result)

    def test_score_uses_combined_intensity_score(self):
        event = _transit_event(combined_intensity_score=0.82)
        result = _normalize_forecast_event(event)
        self.assertAlmostEqual(result["score"], 0.82)


# ── Theme card consistent shape ────────────────────────────────────────────────

class TestPersonalForecastThemeShape(unittest.TestCase):
    """
    Verifies that every theme returned by _build_personal_forecast_context
    carries a consistent structure regardless of whether a prose card exists.
    """

    def _make_blocks(self, include_card=True):
        card = {
            "title": "The Test Title",
            "body": "The Test Body",
            "action": "Take action.",
        } if include_card else None

        return {
            "theme_metadata": {
                "career_visibility": {"label": "Public Emergence", "closing_reframe": "test reframe"},
            },
            "theme_cards": {
                "public_emergence": {"flowing": card} if card else {},
            },
            "opening_snapshot": {
                "fallback": {
                    "dominant": "fallback dominant",
                    "secondary": "fallback secondary",
                    "relational": "fallback relational",
                },
                "dominant": {},
                "dominant_development": {},
                "secondary": {},
                "relational": {},
                "closing_template": "closing {closing_reframe}",
            },
            "featured_event": {
                "domain_core": {},
                "fallback": {"title": "", "body_1": "", "action": ""},
                "character_adjustment": {},
            },
            "timing_windows": {
                "fallback": {"flowing": {"theme": "", "best_use": ""}},
            },
            "guidance": {
                "theme_focus": {},
                "fallback": {"professional": "", "relationships": "", "capacity": ""},
                "character_adjustment": {},
            },
            "closing_integration": {
                "theme_core": {},
                "fallback": "",
                "character_finish": {},
            },
        }

    def _run_builder(self, include_card=True):
        blocks = self._make_blocks(include_card=include_card)

        # One qualified event that will form a career_visibility theme
        event = _transit_event(
            natal_target="MC",
            natal_house=10,
            combined_intensity_score=0.70,
        )

        payload = {"simple_mode": True, "birth_date": "1990-01-01"}
        variables = {"simple_mode": True, "palette": "vibrant"}
        index_results = {}

        transit_engine_stub = types.ModuleType("engine.transit_engine")
        transit_engine_stub.compute_year_ahead_events = lambda *args, **kwargs: {"all_events": [event]}
        chart_wheel_stub = types.ModuleType("engine.chart_wheel")
        chart_wheel_stub.build_chart_wheel_data = lambda *args, **kwargs: None
        chart_wheel_stub.render_natal_wheel_svg = lambda *args, **kwargs: ""

        with patch.object(generate, "_load_personal_forecast_blocks", return_value=blocks), \
             patch.dict(
                 sys.modules,
                 {
                     "engine.transit_engine": transit_engine_stub,
                     "engine.chart_wheel": chart_wheel_stub,
                 },
             ):
            return generate._build_personal_forecast_context(
                variables, index_results, payload
            )

    def test_theme_present_when_card_exists(self):
        ctx = self._run_builder(include_card=True)
        themes = ctx["themes"]
        self.assertEqual(len(themes), 1)
        t = themes[0]
        self.assertEqual(t["title"], "The Test Title")
        self.assertEqual(t["body"], "The Test Body")

    def test_theme_present_when_card_missing(self):
        """A theme without a prose card must still appear with empty prose fields."""
        ctx = self._run_builder(include_card=False)
        themes = ctx["themes"]
        # Theme is NOT dropped even though no prose card was found.
        self.assertEqual(len(themes), 1)
        t = themes[0]
        self.assertEqual(t["title"], "")
        self.assertEqual(t["body"], "")
        self.assertEqual(t["action"], "")

    def test_anchor_event_has_consistent_shape(self):
        ctx = self._run_builder(include_card=True)
        anchor = ctx["themes"][0]["anchor_event"]
        for key in REQUIRED_KEYS:
            self.assertIn(key, anchor, f"anchor_event missing '{key}'")

    def test_supporting_events_is_list_of_normalized_dicts(self):
        ctx = self._run_builder(include_card=True)
        supporting = ctx["themes"][0]["supporting_events"]
        self.assertIsInstance(supporting, list)
        # With one event total, supporting_events is always empty for this case.
        # The structure assertion is on the list itself; shape tests are in
        # TestNormalizeForecastEvent above.

    def test_theme_score_and_character_present(self):
        ctx = self._run_builder(include_card=True)
        t = ctx["themes"][0]
        self.assertIn("theme_score", t)
        self.assertIn("character", t)
        self.assertIsInstance(t["theme_score"], float)
        self.assertIn(t["character"], {"flowing", "challenging"})


# ── Horoscope secondary_activation_line hook ──────────────────────────────────

class TestHoroscopeSecondaryActivationHook(unittest.TestCase):

    def _run_horoscope_builder(self, secondary_activation_line=""):
        variables = {
            "moon_phase_descriptor": "Full Moon",
            "moon_sign_element": "fire",
            "activation_planet": "Moon",
            "activation_house_number": 5,
            "day_ruler_name": "Sun",
            "dominant_eas_dimension": "NGE",
            "dimension_names": {"NGE": "Your Narrative Genre"},
            "palette": "vibrant",
            "secondary_activation_line": secondary_activation_line,
        }
        with patch("selectors.block_selector.select_block", return_value="stub block"):
            return generate._build_horoscope_context(variables, {}, {})

    def test_secondary_activation_line_always_in_context(self):
        """secondary_activation_line must be present in every horoscope context."""
        ctx = self._run_horoscope_builder()
        self.assertIn("secondary_activation_line", ctx)

    def test_secondary_activation_line_blank_by_default(self):
        """The key must be blank when the resolver emits no content."""
        ctx = self._run_horoscope_builder(secondary_activation_line="")
        self.assertEqual(ctx["secondary_activation_line"], "")

    def test_secondary_activation_line_passthrough_when_populated(self):
        """
        If a future rule populates the resolver value, the builder forwards it unchanged.
        This test documents the passthrough contract without implementing a rule.
        """
        ctx = self._run_horoscope_builder(secondary_activation_line="Moon activates your 5th house.")
        self.assertEqual(ctx["secondary_activation_line"], "Moon activates your 5th house.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
