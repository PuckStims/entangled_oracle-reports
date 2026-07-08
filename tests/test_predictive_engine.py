"""
tests/test_predictive_engine.py
Lightweight smoke tests for the predictive engine (predictive_v0.3.1).

Design constraints:
  - No Swiss Ephemeris required. The transit engine call inside the predictive
    engine is wrapped in try/except, so failures produce empty-but-valid output
    rather than crashing. All contract-shape tests pass without a live ephemeris.
  - No I/O. Uses a minimal fake natal payload.
  - Tests 1–5 are pure unit tests; they prove the contract without a live engine.
  - Integration tests (Zendaya 2019) are skipped unless ENTANGLED_FULL_ENGINE=1.

Run with:
    python tests/test_predictive_engine.py
    python -m pytest tests/test_predictive_engine.py -v
"""

import os
import sys
import unittest
from datetime import datetime, timezone, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.predictive_engine import (
    compute_predictive_windows,
    PREDICTIVE_COMPONENT_REGISTRY,
    _event_to_signal,
    _build_daily_series,
    _detect_windows,
    calculate_exit_orb,
    compute_next_phase_state,
    _leading_index,
    _find_local_maxima,
    _compute_peak_prominence,
    _filter_by_distance,
    _STRUCTURAL_BODIES,
    _MIN_PEAK_DISTANCE,
    _MIN_PROMINENCE,
)

# ── Shared fixtures ────────────────────────────────────────────

# Minimal fake natal payload. The transit engine call will fail against this
# (no ephemeris), which is expected — the predictive engine catches that and
# returns the contract shape with empty signals.
_FAKE_PAYLOAD: dict = {
    "simple_mode": True,
    "angles": {
        "Ascendant": {"longitude": 15.0,  "sign": "Aries",       "house": 1},
        "Midheaven": {"longitude": 280.0, "sign": "Capricorn",   "house": 10},
    },
    "standard_planets": {
        "Sun":    {"longitude": 0.0,   "sign": "Aries",       "house": 1,  "retrograde": False, "speed": 1.0},
        "Moon":   {"longitude": 120.0, "sign": "Leo",         "house": 5,  "retrograde": False, "speed": 12.0},
        "Saturn": {"longitude": 240.0, "sign": "Sagittarius", "house": 9,  "retrograde": False, "speed": 0.1},
    },
    "custom_asteroids": {},
    "user_profile": {"julian_day": 2451545.0},
}

_FAKE_INDEX_RESULTS: dict = {
    "KVQ":     {"score": 0.8, "tier": "DOMINANT",  "archetype": "Vindicated Oracle"},
    "MKI":     {"score": 0.5, "tier": "PRESENT",   "archetype": "Lorekeeper"},
    "RWI":     {"score": 0.3, "tier": "SUBTLE",    "archetype": "Pattern Weaver"},
    "DFIS":    {"score": 0.2, "tier": "SUBTLE",    "archetype": "Shadow Integrator"},
    "CATALYST":{"score": 0.6, "tier": "PRESENT",   "archetype": "Impact Radius"},
    "AHL":     {"score": 0.4, "tier": "PRESENT",   "fires": True},
    "MAGNETIC":{"score": 0.1, "tier": "SUBTLE",    "deprecated": True},
}

_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
_END   = datetime(2026, 12, 31, tzinfo=timezone.utc)

# A fake transit event shaped like the transit engine's output
_FAKE_TRANSIT_EVENT: dict = {
    "event_type":     "transit",
    "transit_planet": "Saturn",
    "natal_target":   "Sun",
    "aspect":         "Conjunction",
    "peak_orb":       1.2,
    "peak_datetime":  datetime(2026, 3, 15, tzinfo=timezone.utc),
    "entry_datetime": datetime(2026, 2, 1,  tzinfo=timezone.utc),
    "leave_datetime": datetime(2026, 5, 1,  tzinfo=timezone.utc),
    "combined_intensity_score": 0.75,
}


# ── Tests ──────────────────────────────────────────────────────

class TestPredictiveEngineContract(unittest.TestCase):
    """Phase 1: contract shape is always returned."""

    def test_1_import(self):
        """Engine imports without error and exposes the public API."""
        self.assertTrue(callable(compute_predictive_windows))

    def test_2_return_keys(self):
        """Top-level keys match the Phase 1 contract."""
        result = compute_predictive_windows(
            natal_payload=_FAKE_PAYLOAD,
            index_results=_FAKE_INDEX_RESULTS,
            start_date=_START,
            end_date=_END,
        )
        expected = {"formula_version", "start_date", "end_date",
                    "windows", "daily_series", "signals", "debug"}
        self.assertTrue(expected.issubset(result.keys()),
                        f"Missing contract keys: {expected - result.keys()}")
        self.assertEqual(result["formula_version"], "predictive_v0.3.1")

    def test_3_empty_index_results(self):
        """Engine handles empty index_results without crashing."""
        result = compute_predictive_windows(
            natal_payload=_FAKE_PAYLOAD,
            index_results={},
            start_date=_START,
            end_date=_END,
        )
        self.assertIsInstance(result["windows"], list)
        self.assertIsInstance(result["signals"], list)
        self.assertIsInstance(result["daily_series"], list)

    def test_4_missing_asteroids_graceful(self):
        """Missing asteroid targets produce no crash, just absent or default signals."""
        payload_no_asteroids = {**_FAKE_PAYLOAD, "custom_asteroids": {}}
        result = compute_predictive_windows(
            natal_payload=payload_no_asteroids,
            index_results={},
            start_date=_START,
            end_date=_END,
        )
        self.assertIn("signals", result)
        # Engine must never raise — any failure is captured in debug
        self.assertIsInstance(result["debug"], dict)

    def test_5_empty_predictive_results_dont_crash_context(self):
        """Downstream context code reading empty predictive_results is safe."""
        empty: dict = {}
        self.assertEqual(empty.get("windows", []), [])
        self.assertEqual(empty.get("signals", []), [])
        self.assertEqual(empty.get("daily_series", []), [])

    def test_5b_date_strings_in_output(self):
        """start_date and end_date in output are YYYY-MM-DD strings."""
        result = compute_predictive_windows(
            natal_payload=_FAKE_PAYLOAD,
            index_results=_FAKE_INDEX_RESULTS,
            start_date=_START,
            end_date=_END,
        )
        self.assertEqual(result["start_date"], "2026-01-01")
        self.assertEqual(result["end_date"],   "2026-12-31")


class TestSignalExtraction(unittest.TestCase):
    """Phase 2: _event_to_signal produces correct scored nodes."""

    def test_signal_fields(self):
        """Signal node has all required fields."""
        sig = _event_to_signal(_FAKE_TRANSIT_EVENT, 0)
        self.assertIsNotNone(sig)
        required = {
            "signal_id", "method_family", "source_body", "target_body",
            "aspect", "orb", "allowed_orb", "exactness",
            "event_weight", "target_relevance", "trigger_strength",
            "start_date", "peak_date", "end_date",
            "event_kind", "independence_group", "activation_route",
            "dominant_operation", "operation_profile", "operation_basis",
            "epistemic_confidence", "confidence_components",
            "confidence_state", "angle_eligibility",
        }
        self.assertTrue(required.issubset(sig.keys()),
                        f"Missing signal fields: {required - sig.keys()}")

    def test_method_normalization_fields(self):
        """Transit events normalize to a family/group/route tuple."""
        sig = _event_to_signal(_FAKE_TRANSIT_EVENT, 0)
        self.assertEqual(sig["method_family"], "TRANSIT")
        self.assertEqual(sig["event_kind"], "ASPECT")
        self.assertEqual(sig["independence_group"], "transit_clock")
        self.assertEqual(sig["activation_route"], "transit_to_body")

    def test_trigger_strength_formula(self):
        """TriggerStrength = Exactness × EventWeight × TargetRelevance."""
        sig = _event_to_signal(_FAKE_TRANSIT_EVENT, 0)
        self.assertIsNotNone(sig)
        expected = round(sig["exactness"] * sig["event_weight"] * sig["target_relevance"], 5)
        self.assertAlmostEqual(sig["trigger_strength"], expected, places=5)

    def test_exactness_range(self):
        """Exactness is always in [0, 1]."""
        sig = _event_to_signal(_FAKE_TRANSIT_EVENT, 0)
        self.assertGreaterEqual(sig["exactness"], 0.0)
        self.assertLessEqual(sig["exactness"], 1.0)

    def test_missing_peak_datetime_returns_none(self):
        """Events without a peak_datetime are dropped gracefully."""
        event = {**_FAKE_TRANSIT_EVENT, "peak_datetime": None}
        self.assertIsNone(_event_to_signal(event, 0))

    def test_missing_target_uses_default_relevance(self):
        """Unknown natal targets use the default relevance, not crash."""
        event = {**_FAKE_TRANSIT_EVENT, "natal_target": "Totally_Unknown_Asteroid"}
        sig = _event_to_signal(event, 0)
        self.assertIsNotNone(sig)
        self.assertGreater(sig["trigger_strength"], 0)

    def test_signal_dates_are_date_objects(self):
        """start_date / peak_date / end_date are datetime.date objects."""
        sig = _event_to_signal(_FAKE_TRANSIT_EVENT, 0)
        self.assertIsInstance(sig["start_date"], date)
        self.assertIsInstance(sig["peak_date"],  date)
        self.assertIsInstance(sig["end_date"],   date)

    def test_operation_profile_is_target_sensitive(self):
        """Changing the natal target should materially change the operation vector."""
        body_sig = _event_to_signal({**_FAKE_TRANSIT_EVENT, "natal_target": "Sun"}, 0, birth_time_status="exact")
        angle_sig = _event_to_signal({**_FAKE_TRANSIT_EVENT, "natal_target": "ASC"}, 0, birth_time_status="exact")
        self.assertNotEqual(body_sig["operation_profile"], angle_sig["operation_profile"])
        self.assertNotEqual(body_sig["operation_basis"]["target_substrate"], angle_sig["operation_basis"]["target_substrate"])

    def test_aspect_bias_changes_operation_profile(self):
        """Aspect geometry should bias the operation profile before any coherence math exists."""
        trine_sig = _event_to_signal({**_FAKE_TRANSIT_EVENT, "aspect": "Trine"}, 0, birth_time_status="exact")
        square_sig = _event_to_signal({**_FAKE_TRANSIT_EVENT, "aspect": "Square"}, 0, birth_time_status="exact")
        self.assertNotEqual(trine_sig["operation_profile"], square_sig["operation_profile"])
        self.assertEqual(trine_sig["operation_basis"]["aspect_family"], "TRINE")
        self.assertEqual(square_sig["operation_basis"]["aspect_family"], "SQUARE")

    def test_angle_confidence_is_withheld_without_exact_birth_time(self):
        """Angle-target epistemic scaffolding must fail gracefully when birth time is unknown."""
        angle_sig = _event_to_signal({**_FAKE_TRANSIT_EVENT, "natal_target": "ASC"}, 0, birth_time_status="unknown")
        self.assertEqual(angle_sig["angle_eligibility"], "withheld_without_exact_birth_time")
        self.assertEqual(angle_sig["confidence_state"], "withheld_angle_target")
        self.assertEqual(angle_sig["epistemic_confidence"], 0.0)

    def test_non_angle_signal_keeps_nonzero_confidence_when_birth_time_is_approximate(self):
        """Non-angle targets may remain inspectable under reduced confidence."""
        sig = _event_to_signal({**_FAKE_TRANSIT_EVENT, "natal_target": "Sun"}, 0, birth_time_status="approximate")
        self.assertEqual(sig["angle_eligibility"], "eligible")
        self.assertGreater(sig["epistemic_confidence"], 0.0)
        self.assertIn(sig["confidence_state"], {"provisional", "supported", "weak"})

    def test_interval_aware_confidence(self):
        """exact vs approximate vs withheld angle cases produce materially different confidence behavior."""
        event = {**_FAKE_TRANSIT_EVENT, "natal_target": "Ascendant", "allowed_orb": 3.0, "exactness": 1.0}
        
        exact_sig = _event_to_signal(event, 0, birth_time_status="exact")
        approx_sig = _event_to_signal(event, 0, birth_time_status="approximate")
        unknown_sig = _event_to_signal(event, 0, birth_time_status="unknown")
        
        self.assertGreater(exact_sig["epistemic_confidence"], approx_sig["epistemic_confidence"])
        self.assertGreater(approx_sig["epistemic_confidence"], unknown_sig["epistemic_confidence"])
        self.assertIn("interval_sampled_uncertainty", str(unknown_sig["confidence_components"].get("sampling_state")))

    def test_confidence_degradation_does_not_silently_reduce_intensity(self):
        """confidence degradation does not silently reduce `intensity`."""
        event = {**_FAKE_TRANSIT_EVENT, "natal_target": "Ascendant", "allowed_orb": 3.0, "exactness": 1.0}
        exact_sig = _event_to_signal(event, 0, birth_time_status="exact")
        approx_sig = _event_to_signal(event, 0, birth_time_status="approximate")
        
        # Their trigger strength and event weight should remain identical, decoupled from confidence
        self.assertEqual(exact_sig["trigger_strength"], approx_sig["trigger_strength"])
        self.assertEqual(exact_sig["event_weight"], approx_sig["event_weight"])


class TestDailySeries(unittest.TestCase):
    """Phase 4a: daily series construction."""

    def _make_signal(self, start_iso, end_iso, strength=0.5, source_body="Mars"):
        return {
            "signal_id":        "sig_test",
            "source_body":      source_body,   # required by v0.2 structural/trigger split
            "trigger_strength": strength,
            "start_date":       date.fromisoformat(start_iso),
            "peak_date":        date.fromisoformat(start_iso),
            "end_date":         date.fromisoformat(end_iso),
        }

    def test_series_length(self):
        """Series contains one entry per calendar day in [start, end]."""
        start = datetime(2026, 3, 1, tzinfo=timezone.utc)
        end   = datetime(2026, 3, 31, tzinfo=timezone.utc)
        series = _build_daily_series([], start, end)
        self.assertEqual(len(series), 31)

    def test_active_signal_adds_score(self):
        """Days inside a signal window accumulate trigger_strength."""
        start = datetime(2026, 3, 1,  tzinfo=timezone.utc)
        end   = datetime(2026, 3, 10, tzinfo=timezone.utc)
        sig   = self._make_signal("2026-03-03", "2026-03-05", strength=0.4)
        series = _build_daily_series([sig], start, end)
        active_days = [d for d in series if d["raw_score"] > 0]
        self.assertEqual(len(active_days), 3)  # Mar 3, 4, 5

    def test_zero_strength_signal_is_skipped(self):
        """Signals with zero trigger_strength contribute nothing."""
        start = datetime(2026, 3, 1, tzinfo=timezone.utc)
        end   = datetime(2026, 3, 5, tzinfo=timezone.utc)
        sig   = self._make_signal("2026-03-01", "2026-03-05", strength=0.0)
        series = _build_daily_series([sig], start, end)
        self.assertTrue(all(d["raw_score"] == 0.0 for d in series))

    def test_series_has_required_keys(self):
        """Each series entry has date, raw_score, smooth_score."""
        series = _build_daily_series([], _START, _END)
        for entry in series[:5]:
            self.assertIn("date",         entry)
            self.assertIn("raw_score",    entry)
            self.assertIn("smooth_score", entry)


class TestWindowDetection(unittest.TestCase):
    """Phase 4b: window grouping and labelling."""

    def _make_series(self, scores: list[float], start_iso="2026-01-01"):
        """
        Build a daily series with all required predictive fields.
        Uses baseline=0 so residual=smooth=scores, making these tests
        equivalent to direct peak-detection on the supplied score pattern.
        """
        import datetime as _dt
        start = date.fromisoformat(start_iso)
        return [
            {
                "date":           (start + _dt.timedelta(days=i)).isoformat(),
                "raw_score":      s,
                "smooth_score":   s,
                "baseline_score": 0.0,
                "residual_score": s,   # baseline=0, so residual=smooth
            }
            for i, s in enumerate(scores)
        ]

    def test_no_windows_below_threshold(self):
        """All-zero series produces no windows."""
        series = self._make_series([0.0] * 30)
        windows = _detect_windows(series, [], {})
        self.assertEqual(windows, [])

    def test_single_window_detected(self):
        """A clear isolated peak produces exactly one window."""
        scores = [0.0] * 5 + [0.3, 0.5, 0.4] + [0.0] * 5
        series = self._make_series(scores)
        windows = _detect_windows(series, [], {})
        self.assertEqual(len(windows), 1)

    def test_window_fields(self):
        """Each window has all required Phase 4 fields (v0.1 and v0.2)."""
        scores = [0.0] * 3 + [0.3, 0.5, 0.4] + [0.0] * 3
        series = self._make_series(scores)
        windows = _detect_windows(series, [], {})
        self.assertEqual(len(windows), 1)
        w = windows[0]
        # v0.1 backward-compatible fields
        v01_required = {
            "window_id", "start_date", "peak_date", "end_date",
            "intensity", "coherence", "memory", "gradient",
            "leading_index", "active_signals", "interpretive_tags",
        }
        self.assertTrue(v01_required.issubset(w.keys()),
                        f"Missing v0.1 fields: {v01_required - w.keys()}")
        # v0.2 new fields
        v02_required = {
            "local_peak_intensity", "structural_field_intensity",
            "total_intensity", "prominence",
            "active_slow_chapter_signals", "active_fast_trigger_signals",
        }
        self.assertTrue(v02_required.issubset(w.keys()),
                        f"Missing v0.2 fields: {v02_required - w.keys()}")

    def test_coherence_memory_are_none_without_signals(self):
        """Without active signals, coherence and memory stay unfilled."""
        scores = [0.0] * 2 + [0.3, 0.5, 0.4] + [0.0] * 2
        series = self._make_series(scores)
        windows = _detect_windows(series, [], {})
        self.assertIsNone(windows[0]["coherence"])
        self.assertIsNone(windows[0]["memory"])

    def test_memory_fields_populate_with_active_signal(self):
        """A live signal produces numeric memory plus lifecycle metadata."""
        scores = [0.0] * 3 + [0.2, 0.4, 0.5, 0.4, 0.2] + [0.0] * 3
        series = self._make_series(scores)
        sig = _event_to_signal({
            **_FAKE_TRANSIT_EVENT,
            "transit_planet": "Saturn",
            "natal_target": "Sun",
            "aspect": "Conjunction",
            "peak_orb": 1.2,
            "entry_datetime": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "peak_datetime": datetime(2026, 1, 5, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 1, 9, tzinfo=timezone.utc),
        }, 0, birth_time_status="exact")
        windows = _detect_windows(series, [sig], {})
        self.assertEqual(len(windows), 1)
        self.assertIsNotNone(windows[0]["memory"])
        self.assertGreater(windows[0]["memory"], 0.0)
        self.assertEqual(windows[0]["pass_state"], "APPROACH")
        self.assertEqual(windows[0]["lifecycle_route"], "active")
        self.assertTrue(windows[0]["activation_key"])
        self.assertIn("component_charge", windows[0]["memory_state"])
        self.assertEqual(windows[0]["coherence"], 1.0)
        self.assertEqual(windows[0]["semantic_state"], "reinforcing")
        self.assertTrue(windows[0]["semantic_profile"])
        self.assertTrue(windows[0]["dominant_operation"])
        self.assertTrue(any(tag.startswith("op_") for tag in windows[0]["interpretive_tags"]))

    def test_window_coherence_detects_conflicting_pressures(self):
        """Different dominant operations should reduce window coherence audibly."""
        scores = [0.0] * 3 + [0.3, 0.5, 0.4] + [0.0] * 3
        series = self._make_series(scores)
        sig_a = _event_to_signal({
            **_FAKE_TRANSIT_EVENT,
            "transit_planet": "Saturn",
            "natal_target": "Sun",
            "aspect": "Trine",
            "entry_datetime": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "peak_datetime": datetime(2026, 1, 5, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 1, 8, tzinfo=timezone.utc),
        }, 0, birth_time_status="exact")
        sig_b = _event_to_signal({
            **_FAKE_TRANSIT_EVENT,
            "transit_planet": "Neptune",
            "natal_target": "Moon",
            "aspect": "Conjunction",
            "peak_orb": 0.5,
            "entry_datetime": datetime(2026, 1, 3, tzinfo=timezone.utc),
            "peak_datetime": datetime(2026, 1, 5, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 1, 7, tzinfo=timezone.utc),
        }, 1, birth_time_status="exact")
        windows = _detect_windows(series, [sig_a, sig_b], {})
        self.assertEqual(len(windows), 1)
        self.assertLess(windows[0]["coherence"], 0.75)
        self.assertEqual(windows[0]["semantic_state"], "opposed")
        self.assertGreaterEqual(windows[0]["semantic_diagnostics"]["conflicting_pairs"], 1)
        
    def test_polarity_and_counterforce_cases(self):
        """polarity/counterforce cases do not collapse into generic 'mixed' behavior."""
        scores = [0.0] * 3 + [0.3, 0.5, 0.4] + [0.0] * 3
        series = self._make_series(scores)
        sig_a = _event_to_signal({
            **_FAKE_TRANSIT_EVENT,
            "transit_planet": "Saturn",
            "natal_target": "Sun",
            "aspect": "Trine",  # Constructive
            "entry_datetime": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "peak_datetime": datetime(2026, 1, 5, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 1, 8, tzinfo=timezone.utc),
        }, 0, birth_time_status="exact")
        sig_b = _event_to_signal({
            **_FAKE_TRANSIT_EVENT,
            "transit_planet": "Uranus",
            "natal_target": "Moon",
            "aspect": "Square",  # Dissolving
            "entry_datetime": datetime(2026, 1, 3, tzinfo=timezone.utc),
            "peak_datetime": datetime(2026, 1, 5, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 1, 7, tzinfo=timezone.utc),
        }, 1, birth_time_status="exact")
        windows = _detect_windows(series, [sig_a, sig_b], {})
        
        diag = windows[0]["semantic_diagnostics"]
        self.assertGreater(diag["polarity"], 0.0)
        self.assertGreater(diag["counterforce"], 0.0)
        self.assertEqual(windows[0]["semantic_state"], "opposed")

    def test_window_coherence_rewards_same_direction_reinforcement(self):
        """Compatible dominant operations should keep coherence high."""
        scores = [0.0] * 3 + [0.3, 0.5, 0.4] + [0.0] * 3
        series = self._make_series(scores)
        sig_a = _event_to_signal({
            **_FAKE_TRANSIT_EVENT,
            "transit_planet": "Saturn",
            "natal_target": "Sun",
            "aspect": "Trine",
            "entry_datetime": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "peak_datetime": datetime(2026, 1, 5, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 1, 8, tzinfo=timezone.utc),
        }, 0, birth_time_status="exact")
        sig_b = _event_to_signal({
            **_FAKE_TRANSIT_EVENT,
            "transit_planet": "Jupiter",
            "natal_target": "Moon",
            "aspect": "Conjunction",
            "peak_orb": 0.8,
            "entry_datetime": datetime(2026, 1, 3, tzinfo=timezone.utc),
            "peak_datetime": datetime(2026, 1, 5, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 1, 7, tzinfo=timezone.utc),
        }, 1, birth_time_status="exact")
        windows = _detect_windows(series, [sig_a, sig_b], {})
        self.assertEqual(len(windows), 1)
        self.assertGreaterEqual(windows[0]["coherence"], 0.75)
        self.assertEqual(windows[0]["semantic_state"], "reinforcing")
        self.assertGreaterEqual(windows[0]["semantic_diagnostics"]["compatible_pairs"], 1)

    def test_two_separate_windows(self):
        """
        Two peaks separated by more than MIN_PEAK_DISTANCE days become
        two distinct windows.  The series is 40 days long so the peaks
        (at indices 5 and 22) are 17 days apart (> MIN_PEAK_DISTANCE=14).
        """
        #          0   1   2    3    4    5    6    7     8..19    20   21   22   23   24   25..39
        scores = ([0.0]*3 + [0.2, 0.4, 0.5, 0.4, 0.2] +   # peak at index 5
                  [0.0]*12 +                                # gap (indices 8–19)
                  [0.2, 0.4, 0.6, 0.4, 0.2] +             # peak at index 22
                  [0.0]*15)                                 # (indices 25–39)
        series  = self._make_series(scores)
        windows = _detect_windows(series, [], {})
        self.assertEqual(len(windows), 2,
                         f"Expected 2 windows; got {len(windows)}. "
                         f"Peaks must be ≥ {_MIN_PEAK_DISTANCE} days apart.")

    def test_close_peaks_merge_to_one(self):
        """
        Two peaks only 7 days apart are within MIN_PEAK_DISTANCE and should
        collapse to a single window (the higher-prominence peak wins).
        """
        scores = [0.3, 0.5] + [0.0] * 5 + [0.4, 0.6]   # peaks at 1 and 8 (distance 7)
        series = self._make_series(scores)
        windows = _detect_windows(series, [], {})
        self.assertEqual(len(windows), 1,
                         "Peaks within MIN_PEAK_DISTANCE must merge to one window.")

    def test_window_ids_are_unique(self):
        """Each window gets a unique window_id."""
        scores = ([0.0]*3 + [0.2, 0.4, 0.5, 0.4, 0.2] +
                  [0.0]*12 +
                  [0.2, 0.4, 0.6, 0.4, 0.2] +
                  [0.0]*15)
        series = self._make_series(scores)
        windows = _detect_windows(series, [], {})
        ids = [w["window_id"] for w in windows]
        self.assertEqual(len(ids), len(set(ids)))


class TestPredictivePhaseFSM(unittest.TestCase):
    """Finite state machine fixtures for predictive episode continuity."""

    def test_calculate_exit_orb_expands_entry_orb(self):
        """Exit orb should always be slightly larger than enter orb."""
        self.assertAlmostEqual(calculate_exit_orb(2.0), 2.16, places=2)
        self.assertAlmostEqual(calculate_exit_orb(0.0), 0.10, places=2)

    def test_fsm_cannot_regress_to_prelude_from_approach(self):
        """Inside the hysteresis band, APPROACH cannot flicker back to PRELUDE."""
        next_state = compute_next_phase_state(
            current_state="APPROACH",
            current_orb=2.05,
            enter_orb=2.0,
            is_retrograde=False,
            prior_exact_hit=False,
        )
        self.assertEqual(next_state, "APPROACH")

    def test_fsm_hysteresis_band_maintains_state(self):
        """Small orb oscillations inside the exit band should preserve continuity."""
        state = compute_next_phase_state(
            current_state="PRELUDE",
            current_orb=1.99,
            enter_orb=2.0,
            is_retrograde=False,
            prior_exact_hit=False,
        )
        self.assertEqual(state, "APPROACH")

        state = compute_next_phase_state(
            current_state=state,
            current_orb=2.05,
            enter_orb=2.0,
            is_retrograde=False,
            prior_exact_hit=False,
        )
        self.assertEqual(state, "APPROACH")

    def test_fsm_retrograde_review_requires_prior_exact_hit(self):
        """Retrograde review is illegal before an exact contact has happened."""
        next_state = compute_next_phase_state(
            current_state="APPROACH",
            current_orb=1.3,
            enter_orb=2.0,
            is_retrograde=True,
            prior_exact_hit=False,
        )
        self.assertEqual(next_state, "APPROACH")

    def test_fsm_residual_field_only_reachable_after_resolution_or_aftermath(self):
        """Aborted approaches leaving orb do not fabricate a residual field."""
        next_state = compute_next_phase_state(
            current_state="APPROACH",
            current_orb=2.3,
            enter_orb=2.0,
            is_retrograde=False,
            prior_exact_hit=False,
        )
        self.assertEqual(next_state, "PRELUDE")

        resolved_state = compute_next_phase_state(
            current_state="AFTERMATH",
            current_orb=2.3,
            enter_orb=2.0,
            is_retrograde=False,
            prior_exact_hit=True,
        )
        self.assertEqual(resolved_state, "RESIDUAL_FIELD")


class TestRegistry(unittest.TestCase):
    """Phase 3: registry structure and leading_index resolution."""

    def test_registry_has_required_dimensions(self):
        """Registry contains at least KVQ, MKI, RWI, DFIS, CATALYST."""
        required = {"KVQ", "MKI", "RWI", "DFIS", "CATALYST"}
        self.assertTrue(required.issubset(PREDICTIVE_COMPONENT_REGISTRY.keys()))

    def test_registry_entries_have_required_keys(self):
        """Every component entry has targets, weight, activation_modes."""
        for dim, components in PREDICTIVE_COMPONENT_REGISTRY.items():
            for comp_key, comp in components.items():
                self.assertIn("targets",          comp, f"{dim}.{comp_key} missing targets")
                self.assertIn("weight",           comp, f"{dim}.{comp_key} missing weight")
                self.assertIn("activation_modes", comp, f"{dim}.{comp_key} missing activation_modes")

    def test_leading_index_fallback_to_highest_score(self):
        """When no registry targets match, falls back to highest natal index score."""
        result = _leading_index([], _FAKE_INDEX_RESULTS)
        # KVQ has score 0.8, highest non-legacy dimension
        self.assertEqual(result, "KVQ")

    def test_leading_index_default_fallback(self):
        """With no signals and empty index_results, returns 'KVQ'."""
        result = _leading_index([], {})
        self.assertEqual(result, "KVQ")

    def test_leading_index_prefers_registry_match(self):
        """A signal targeting a KVQ registry body lifts KVQ to leading."""
        kassandra_signal = {
            "signal_id":        "sig_test_0001",
            "target_body":      "Kassandra",
            "source_body":      "Saturn",
            "trigger_strength": 0.5,
        }
        result = _leading_index([kassandra_signal], {})
        self.assertEqual(result, "KVQ")


class TestProminenceHelpers(unittest.TestCase):
    """Unit tests for the prominence-based peak detection helpers (v0.2)."""

    def test_find_local_maxima_simple(self):
        """Returns correct indices for a simple triangle."""
        values = [0.0, 0.3, 0.5, 0.3, 0.0]
        self.assertEqual(_find_local_maxima(values), [2])

    def test_find_local_maxima_two_peaks(self):
        """Finds two separated peaks."""
        values = [0.0, 0.5, 0.0, 0.4, 0.0]
        maxima = _find_local_maxima(values)
        self.assertIn(1, maxima)
        self.assertIn(3, maxima)

    def test_find_local_maxima_flat_ignored(self):
        """A plateau (equal values) does not produce a spurious maximum."""
        values = [0.0, 0.5, 0.5, 0.5, 0.0]
        maxima = _find_local_maxima(values)
        self.assertEqual(len(maxima), 0,
                         "Equal neighbors should not qualify as strict maxima.")

    def test_prominence_isolated_peak(self):
        """An isolated peak's prominence equals its height when base is zero."""
        values    = [0.0, 0.0, 0.8, 0.0, 0.0]
        maxima    = _find_local_maxima(values)
        proms     = _compute_peak_prominence(values, maxima)
        self.assertEqual(len(proms), 1)
        self.assertAlmostEqual(proms[0], 0.8, places=5)

    def test_prominence_secondary_peak(self):
        """A secondary peak's prominence is bounded by the inter-peak valley."""
        # Primary peak at index 2 (height 1.0), secondary at index 6 (height 0.6)
        # Valley between them at 0.2 (index 4)
        values = [0.0, 0.5, 1.0, 0.5, 0.2, 0.3, 0.6, 0.3, 0.0]
        maxima = _find_local_maxima(values)   # should be [2, 6] (and maybe 5 depending)
        # Filter to just the two clear peaks
        top_maxima = [i for i in maxima if values[i] >= 0.5]
        proms = _compute_peak_prominence(values, sorted(top_maxima))
        prom_by_idx = dict(zip(sorted(top_maxima), proms))
        # Primary peak at 2 (height 1.0): no higher neighbor on either side — scan
        # reaches both series boundaries where the minimum is 0.0.
        # prominence = 1.0 - max(0.0, 0.0) = 1.0
        self.assertAlmostEqual(prom_by_idx[2], 1.0, places=4)
        # Secondary peak at 6 (height 0.6): leftward scan is blocked by the primary peak
        # at index 2 (height 1.0 > 0.6); left_min = valley at 0.2.
        # Rightward scan reaches the boundary; right_min = 0.0.
        # prominence = 0.6 - max(0.2, 0.0) = 0.4
        self.assertAlmostEqual(prom_by_idx[6], 0.4, places=4)

    def test_filter_by_distance_keeps_higher_prominence(self):
        """When two peaks are too close, the higher-prominence one wins."""
        qualified = [(10, 0.4), (15, 0.7)]   # 5 apart → only keep 15 (prom 0.7)
        result    = _filter_by_distance(qualified, min_distance=14)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 15)

    def test_filter_by_distance_keeps_both_when_far(self):
        """Peaks separated by more than min_distance are both kept."""
        qualified = [(5, 0.5), (22, 0.6)]    # 17 apart → both kept
        result    = _filter_by_distance(qualified, min_distance=14)
        indices   = sorted(r[0] for r in result)
        self.assertEqual(indices, [5, 22])

    def test_structural_bodies_set(self):
        """The structural-body set contains the four slow outer planets."""
        for body in ("Saturn", "Uranus", "Neptune", "Pluto"):
            self.assertIn(body, _STRUCTURAL_BODIES)

    def test_fast_bodies_not_structural(self):
        """Jupiter and Mars are not structural bodies."""
        self.assertNotIn("Jupiter", _STRUCTURAL_BODIES)
        self.assertNotIn("Mars",    _STRUCTURAL_BODIES)


class TestDailySeriesV02(unittest.TestCase):
    """v0.2: Two-layer series fields."""

    def _make_signal(self, source, start_iso, end_iso, strength=0.5):
        return {
            "signal_id":        "sig_test",
            "source_body":      source,
            "trigger_strength": strength,
            "start_date":       date.fromisoformat(start_iso),
            "peak_date":        date.fromisoformat(start_iso),
            "end_date":         date.fromisoformat(end_iso),
        }

    def test_series_has_v02_keys(self):
        """v0.2 series entries expose baseline_score and residual_score."""
        start = datetime(2026, 3, 1, tzinfo=timezone.utc)
        end   = datetime(2026, 3, 10, tzinfo=timezone.utc)
        series = _build_daily_series([], start, end)
        for entry in series[:3]:
            self.assertIn("baseline_score", entry)
            self.assertIn("residual_score", entry)
            self.assertIn("structural_raw", entry)
            self.assertIn("trigger_raw",    entry)

    def test_structural_signal_goes_to_structural_raw(self):
        """A Saturn signal contributes to structural_raw, not trigger_raw."""
        start = datetime(2026, 4, 1, tzinfo=timezone.utc)
        end   = datetime(2026, 4, 10, tzinfo=timezone.utc)
        sig   = self._make_signal("Saturn", "2026-04-03", "2026-04-05", 0.6)
        series = _build_daily_series([sig], start, end)
        active = [d for d in series if d["structural_raw"] > 0]
        self.assertEqual(len(active), 3)
        for d in active:
            self.assertAlmostEqual(d["structural_raw"], 0.6, places=4)
            self.assertAlmostEqual(d["trigger_raw"],    0.0, places=4)

    def test_fast_signal_goes_to_trigger_raw(self):
        """A Mars signal contributes to trigger_raw, not structural_raw."""
        start = datetime(2026, 4, 1, tzinfo=timezone.utc)
        end   = datetime(2026, 4, 10, tzinfo=timezone.utc)
        sig   = self._make_signal("Mars", "2026-04-03", "2026-04-05", 0.4)
        series = _build_daily_series([sig], start, end)
        active = [d for d in series if d["trigger_raw"] > 0]
        self.assertEqual(len(active), 3)
        for d in active:
            self.assertAlmostEqual(d["trigger_raw"],    0.4, places=4)
            self.assertAlmostEqual(d["structural_raw"], 0.0, places=4)

    def test_baseline_is_never_greater_than_smooth(self):
        """
        The baseline (wide MA) can never exceed the smooth score (narrow MA)
        for a non-negative signal series — both are non-negative averages of
        the same raw values.
        """
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end   = datetime(2026, 12, 31, tzinfo=timezone.utc)
        sig   = self._make_signal("Saturn", "2026-01-01", "2026-12-31", 0.5)
        series = _build_daily_series([sig], start, end)
        for d in series:
            self.assertLessEqual(
                d["baseline_score"],
                d["smooth_score"] + 1e-9,
                "Baseline exceeded smooth score — edge-clamping asymmetry?"
            )


class TestWindowDetectionRegression(unittest.TestCase):
    """
    v0.2 regression tests: verify that the prominence-based algorithm
    does not collapse an entire forecast year into a single window.
    """

    def _make_full_series(
        self,
        smooth: list[float],
        baseline: list[float],
        start_iso: str = "2019-01-01",
    ) -> list[dict]:
        """Build a series with all required predictive fields from explicit smooth/baseline arrays."""
        import datetime as _dt
        start = date.fromisoformat(start_iso)
        return [
            {
                "date":           (start + _dt.timedelta(days=i)).isoformat(),
                "raw_score":      smooth[i],
                "smooth_score":   smooth[i],
                "baseline_score": baseline[i],
                "residual_score": smooth[i] - baseline[i],
                "structural_raw": baseline[i],
                "trigger_raw":    max(0.0, smooth[i] - baseline[i]),
            }
            for i in range(len(smooth))
        ]

    def test_sustained_floor_does_not_produce_mega_window(self):
        """
        Regression: a persistent elevated structural floor (simulating a
        year-long outer-planet transit) must not collapse into a single window.

        Scenario: constant baseline of 0.4 all year (Saturn through MC),
        with three distinct activation spikes at months ~2, ~6, ~10.
        """
        n        = 365
        baseline = [0.40] * n
        smooth   = [0.40] * n

        # Three activation peaks well separated (days 55, 180, 305 ≈ months 2, 6, 10)
        for center, height in [(55, 0.30), (180, 0.28), (305, 0.32)]:
            for offset in range(-10, 11):
                idx = center + offset
                if 0 <= idx < n:
                    spike  = height * max(0.0, 1.0 - abs(offset) / 11.0)
                    smooth[idx] = baseline[idx] + spike

        series  = self._make_full_series(smooth, baseline)
        windows = _detect_windows(series, [], {})

        # Core regression assertion: not a single mega-window
        self.assertNotEqual(
            len(windows), 1,
            "Regression FAILURE: sustained structural floor collapsed into a "
            "single mega-window. The prominence-based algorithm should have "
            "detected multiple distinct activation peaks.",
        )
        # Should find roughly 3 windows (allow 2–5 for edge effects)
        self.assertGreaterEqual(len(windows), 2,
            f"Too few windows ({len(windows)}) — algorithm may be over-suppressing.")
        self.assertLessEqual(len(windows), 5,
            f"Too many windows ({len(windows)}) — algorithm may be over-splitting.")

    def test_quiet_year_produces_few_windows(self):
        """A year with only a single genuine activation peak yields 1 window."""
        n       = 365
        smooth  = [0.05] * n
        baseline = [0.03] * n
        # One real peak at day 180
        for offset in range(-8, 9):
            idx = 180 + offset
            if 0 <= idx < n:
                smooth[idx] = 0.03 + 0.25 * max(0.0, 1.0 - abs(offset) / 9.0)
        series  = self._make_full_series(smooth, baseline)
        windows = _detect_windows(series, [], {})
        self.assertEqual(len(windows), 1,
            "A single genuine peak should produce exactly one window.")

    def test_no_window_wider_than_half_year(self):
        """
        Any individual window must be narrower than 183 days.
        A year-long (or half-year-long) window is symptomatic of the old
        run-grouper bug.
        """
        n        = 365
        baseline = [0.35] * n
        smooth   = [0.35] * n
        for center, height in [(60, 0.25), (150, 0.22), (240, 0.28), (330, 0.20)]:
            for offset in range(-10, 11):
                idx = center + offset
                if 0 <= idx < n:
                    smooth[idx] = baseline[idx] + height * max(0.0, 1.0 - abs(offset)/11.0)
        series  = self._make_full_series(smooth, baseline)
        windows = _detect_windows(series, [], {})
        for w in windows:
            start_d = date.fromisoformat(w["start_date"])
            end_d   = date.fromisoformat(w["end_date"])
            span    = (end_d - start_d).days
            self.assertLess(span, 183,
                f"Window {w['window_id']} spans {span} days — likely a mega-window remnant.")

    def test_intensity_fields_present_and_consistent(self):
        """total_intensity == local_peak_intensity + structural_field_intensity."""
        n        = 30
        baseline = [0.2] * n
        smooth   = [0.2] * n
        smooth[15] = 0.6   # single spike
        series  = self._make_full_series(smooth, baseline)
        windows = _detect_windows(series, [], {})
        self.assertEqual(len(windows), 1)
        w = windows[0]
        expected_total = round(w["local_peak_intensity"] + w["structural_field_intensity"], 4)
        self.assertAlmostEqual(
            w["total_intensity"], expected_total, places=3,
            msg="total_intensity must equal local_peak_intensity + structural_field_intensity",
        )

    def test_slow_fast_signal_split(self):
        """Windows correctly split signals into slow-chapter vs fast-trigger lists."""
        import datetime as _dt
        n      = 365
        smooth = [0.0] * n
        for offset in range(-7, 8):
            idx = 180 + offset
            if 0 <= idx < n:
                smooth[idx] = 0.3 * max(0.0, 1.0 - abs(offset) / 8.0)
        series = [
            {
                "date":           (date(2026, 1, 1) + _dt.timedelta(days=i)).isoformat(),
                "raw_score":      smooth[i],
                "smooth_score":   smooth[i],
                "baseline_score": 0.0,
                "residual_score": smooth[i],
            }
            for i in range(n)
        ]
        saturn_sig = {
            "signal_id":        "sig_sat",
            "source_body":      "Saturn",
            "target_body":      "Sun",
            "trigger_strength": 0.4,
            "start_date":       date(2026, 1, 1),
            "peak_date":        date(2026, 6, 29),
            "end_date":         date(2026, 12, 31),
        }
        mars_sig = {
            "signal_id":        "sig_mar",
            "source_body":      "Mars",
            "target_body":      "MC",
            "trigger_strength": 0.3,
            "start_date":       date(2026, 6, 20),
            "peak_date":        date(2026, 6, 29),
            "end_date":         date(2026, 7, 8),
        }
        windows = _detect_windows(series, [saturn_sig, mars_sig], {})
        self.assertGreaterEqual(len(windows), 1)
        w = windows[0]
        self.assertIn("sig_sat", w["active_slow_chapter_signals"])
        self.assertIn("sig_mar", w["active_fast_trigger_signals"])
        self.assertNotIn("sig_sat", w["active_fast_trigger_signals"])
        self.assertNotIn("sig_mar", w["active_slow_chapter_signals"])

    # ── Zendaya 2019 integration test ──────────────────────────

    def test_zendaya_2019_no_mega_window(self):
        """
        Integration: Zendaya (b. 1996-09-01, Oakland CA), Year Ahead 2019.

        Primary regression: engine must NOT return a single January-to-January
        window. It must return multiple localized windows without touching any
        customer-facing report.

        Skipped unless ENTANGLED_FULL_ENGINE=1 (requires live ephemeris).
        """
        if not os.environ.get("ENTANGLED_FULL_ENGINE"):
            self.skipTest("Requires live ephemeris — set ENTANGLED_FULL_ENGINE=1 to run.")

        zendaya_birth = {
            "name":     "Zendaya",
            "date":     "1996-09-01",
            "time":     "06:01",
            "location": "Oakland, CA",
        }

        try:
            from engine.natal_engine import generate_payload
            payload = generate_payload(zendaya_birth)
        except Exception as exc:
            self.skipTest(f"Natal engine unavailable: {exc}")

        try:
            from formulas.proprietary_indexes import compute_all_indexes
            index_results = compute_all_indexes(payload)
        except Exception as exc:
            index_results = {}

        start = datetime(2019, 1,  1, tzinfo=timezone.utc)
        end   = datetime(2019, 12, 31, tzinfo=timezone.utc)

        result  = compute_predictive_windows(
            natal_payload=payload,
            index_results=index_results,
            start_date=start,
            end_date=end,
        )
        windows = result["windows"]

        # ── Regression assertions ──────────────────────────────

        # 1. Formula version updated
        self.assertEqual(result["formula_version"], "predictive_v0.3.1",
            "Formula version must be predictive_v0.3.1.")

        # 2. Not a single mega-window
        self.assertNotEqual(len(windows), 1,
            "Regression FAILURE: single January-to-January mega-window still "
            "detected for Zendaya 2019. The segmentation algorithm is not "
            "separating distinct activation peaks.")

        # 3. Not zero windows (a full year should produce some activity)
        self.assertGreater(len(windows), 0,
            "No windows detected at all — engine may have failed silently.")

        # 4. Count in calibration target range (allow slack: 4–20)
        self.assertGreaterEqual(len(windows), 4,
            f"Only {len(windows)} window(s) found; expected ≥ 4 for an active year.")
        self.assertLessEqual(len(windows), 20,
            f"{len(windows)} windows found; algorithm may be over-segmenting.")

        # 5. No individual window spans more than 70 % of the year
        year_days = (end - start).days
        for w in windows:
            span = (date.fromisoformat(w["end_date"]) -
                    date.fromisoformat(w["start_date"])).days
            self.assertLess(span, int(year_days * 0.70),
                f"Window {w['window_id']} spans {span} days — mega-window remnant?")

        # 6. v0.2 fields present on all windows
        v02_fields = {
            "local_peak_intensity", "structural_field_intensity",
            "total_intensity", "prominence",
            "active_slow_chapter_signals", "active_fast_trigger_signals",
        }
        for w in windows:
            missing = v02_fields - w.keys()
            self.assertFalse(missing,
                f"Window {w['window_id']} missing v0.2 fields: {missing}")

        # 7. No window's total_intensity is zero (would indicate a scoring bug)
        for w in windows:
            self.assertGreater(w["total_intensity"], 0.0,
                f"Window {w['window_id']} has zero total_intensity.")


class TestSandboxEndToEnd(unittest.TestCase):
    """
    Smoke tests for the full predictive_sandbox rendering pipeline.

    No ephemeris required: these tests construct a known-good context dict
    manually and verify that:
      (a) _build_predictive_sandbox_context forwards all required window fields
      (b) render_template("predictive_sandbox", ctx) returns the dedicated
          template HTML — not the generic fallback
      (c) The rendered HTML contains every required section header and field name

    The tests import from generate.py, so they also catch any import-time
    issues in that module.
    """

    # ── Shared minimal predictive_results fixture ──────────────

    _FAKE_PREDICTIVE_RESULTS = {
        "formula_version": "predictive_v0.3.1",
        "start_date": "2019-01-01",
        "end_date":   "2019-12-31",
        "windows": [
            {
                "window_id":                   "pw_001",
                "start_date":                  "2019-03-01",
                "peak_date":                   "2019-03-15",
                "end_date":                    "2019-03-28",
                "local_peak_intensity":        0.3142,
                "structural_field_intensity":  0.4100,
                "total_intensity":             0.7242,
                "intensity":                   0.7242,
                "prominence":                  0.2800,
                "gradient":                    "plateau",
                "leading_index":               "KVQ",
                "active_slow_chapter_signals": ["sig_sat_0001"],
                "active_fast_trigger_signals": ["sig_mar_0042"],
                "active_signals":              ["sig_sat_0001", "sig_mar_0042"],
                "coherence":                   0.82,
                "semantic_profile": {
                    "stabilize": 0.34,
                    "amplify": 0.12,
                    "activate": 0.16,
                    "disrupt": 0.11,
                    "dissolve": 0.08,
                    "reveal": 0.19,
                },
                "dominant_operation":          "stabilize",
                "semantic_state":              "reinforcing",
                "semantic_diagnostics": {
                    "participating_signal_count": 2,
                    "pair_count": 1,
                    "compatible_pairs": 1,
                    "conflicting_pairs": 0,
                    "average_signal_confidence": 0.84,
                    "polarity": 0.0,
                    "coalition": 0.5,
                    "counterforce": 0.0,
                    "complexity": 0.0,
                },
                "memory":                      0.7242,
                "memory_state": {
                    "activation_key": "transit_clock:TRANSIT:ASPECT:Saturn:Sun:Conjunction:transit_to_body",
                    "first_seen_date": "2019-03-15",
                    "episode_count": 1,
                    "prior_episode_count": 0,
                    "current_episode_id": "transit_clock:TRANSIT:ASPECT:Saturn:Sun:Conjunction:transit_to_body:episode_01",
                    "pass_state": "APPROACH",
                    "component_charge": 0.7242,
                    "lifecycle_route": "active",
                    "formula_version": "predictive_v0.3.1",
                },
                "activation_key":               "transit_clock:TRANSIT:ASPECT:Saturn:Sun:Conjunction:transit_to_body",
                "pass_state":                   "APPROACH",
                "lifecycle_route":              "active",
                "interpretive_tags":           [],
            }
        ],
        "signals": [
            {
                "signal_id":        "sig_sat_0001",
                "method_family":    "TRANSIT",
                "event_kind":       "ASPECT",
                "independence_group": "transit_clock",
                "activation_route": "transit_to_body",
                "source_body":      "Saturn",
                "target_body":      "Sun",
                "aspect":           "Conjunction",
                "orb":              0.8,
                "allowed_orb":      3.0,
                "exactness":        0.7333,
                "event_weight":     0.85,
                "target_relevance": 0.90,
                "trigger_strength": 0.56025,
                "dominant_operation": "stabilize",
                "operation_profile": {
                    "stabilize": 0.52,
                    "amplify": 0.07,
                    "activate": 0.12,
                    "disrupt": 0.13,
                    "dissolve": 0.07,
                    "reveal": 0.23,
                },
                "operation_basis": {
                    "source_profile": "Saturn",
                    "target_substrate": "luminary",
                    "aspect_family": "CONJUNCTION",
                    "method_behavior": "TRANSIT",
                },
                "epistemic_confidence": 0.88,
                "confidence_components": {
                    "availability_gate": 1.0,
                    "record_integrity": 1.0,
                    "calculation_integrity": 1.0,
                    "relation_robustness": 0.88,
                    "sampling_state": "exactness_proxy_scaffold",
                },
                "confidence_state": "supported",
                "angle_eligibility": "eligible",
                "start_date":       date(2019, 1, 1),
                "peak_date":        date(2019, 3, 15),
                "end_date":         date(2019, 6, 30),
            }
        ],
        "daily_series": [
            {
                "date":           "2019-03-15",
                "raw_score":      0.56025,
                "smooth_score":   0.52000,
                "baseline_score": 0.41000,
                "residual_score": 0.11000,
                "structural_raw": 0.56025,
                "trigger_raw":    0.00000,
            }
        ],
        "debug": {
            "raw_event_count":              28,
            "signal_count":                 1,
            "window_count":                 1,
            "peaks_found_in_residual":      3,
            "peaks_after_prominence_filter": 2,
            "peaks_after_distance_filter":  1,
            "baseline_window_days":         35,
            "smooth_window_days":           7,
            "min_peak_distance":            14,
            "min_prominence":               0.05,
        },
    }

    _FAKE_PALETTE = {
        "bg": "#07070B", "surface": "#101018", "surface_2": "#151522",
        "border": "#242436", "text": "#E8E0D0", "muted": "#6B6580",
        "subtle": "#9088A0", "accent": "#C4A882", "purple": "#B088FF",
        "gold": "#FFD700", "rose": "#FF6BAE", "ember": "#FF9868", "blue": "#88DDFF",
        "identity": "#C4A882", "growth": "#88DDFF", "relationships": "#FF6BAE",
        "creativity": "#FFD700", "vocation": "#B088FF", "home": "#88BBFF",
        "spiritual": "#9088A0",
    }

    def _make_variables(self):
        return {
            "querent_name": "Test User",
            "palette":      "vibrant",
            "predictive_results": self._FAKE_PREDICTIVE_RESULTS,
        }

    def _make_payload(self):
        return {
            "name":           "Test User",
            "birth_date":     "1996-09-01",
            "birth_time":     "18:01:00",
            "birth_location": "Oakland, CA",
            "simple_mode":    False,
        }

    # 1. Context builder forwards required predictive window fields

    def test_context_builder_window_v03_fields(self):
        """
        _build_predictive_sandbox_context must forward every required window field.
        Missing fields are what caused the 'dict has no attribute' Jinja error.
        """
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _build_predictive_sandbox_context
        from datetime import timezone

        start = datetime(2019, 1,  1, tzinfo=timezone.utc)
        end   = datetime(2019, 12, 31, tzinfo=timezone.utc)

        ctx = _build_predictive_sandbox_context(
            variables=self._make_variables(),
            index_results={},
            payload=self._make_payload(),
            report_start=start,
            report_end=end,
        )

        self.assertIn("windows",      ctx)
        self.assertIn("signals",      ctx)
        self.assertIn("daily_series", ctx)
        self.assertEqual(len(ctx["windows"]), 1)

        w = ctx["windows"][0]
        required_window_fields = {
            "local_peak_intensity",
            "structural_field_intensity",
            "total_intensity",
            "prominence",
            "active_slow_chapter_signals",
            "active_fast_trigger_signals",
        }
        missing = required_window_fields - w.keys()
        self.assertFalse(
            missing,
            f"Context builder dropped these required window fields: {missing}\n"
            "This causes a Jinja2 AttributeError and a silent fallback to the generic renderer."
        )
        self.assertIn("memory_state", w)
        self.assertIn("pass_state", w)
        self.assertIn("lifecycle_route", w)
        self.assertEqual(w["pass_state"], "APPROACH")
        self.assertIn("semantic_profile", w)
        self.assertIn("dominant_operation", w)
        self.assertIn("semantic_state", w)
        self.assertIn("semantic_diagnostics", w)
        self.assertEqual(w["semantic_state"], "reinforcing")

    def test_context_builder_daily_series_v03_fields(self):
        """Daily series entries must include all required predictive fields."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _build_predictive_sandbox_context
        from datetime import timezone

        start = datetime(2019, 1,  1, tzinfo=timezone.utc)
        end   = datetime(2019, 12, 31, tzinfo=timezone.utc)

        ctx = _build_predictive_sandbox_context(
            variables=self._make_variables(),
            index_results={},
            payload=self._make_payload(),
            report_start=start,
            report_end=end,
        )
        self.assertGreater(len(ctx["daily_series"]), 0)
        d = ctx["daily_series"][0]
        for field in ("baseline_score", "residual_score", "structural_raw", "trigger_raw"):
            self.assertIn(field, d,
                f"daily_series entry missing '{field}' — template will raise AttributeError.")

    def test_context_builder_forwards_signal_v031_fields(self):
        """Signal-level semantic scaffolding must survive context building untouched."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _build_predictive_sandbox_context
        from datetime import timezone

        start = datetime(2019, 1,  1, tzinfo=timezone.utc)
        end   = datetime(2019, 12, 31, tzinfo=timezone.utc)

        ctx = _build_predictive_sandbox_context(
            variables=self._make_variables(),
            index_results={},
            payload=self._make_payload(),
            report_start=start,
            report_end=end,
        )
        self.assertEqual(len(ctx["signals"]), 1)
        sig = ctx["signals"][0]
        for field in (
            "dominant_operation",
            "operation_profile",
            "operation_basis",
            "epistemic_confidence",
            "confidence_components",
            "confidence_state",
            "angle_eligibility",
        ):
            self.assertIn(field, sig, f"context builder dropped signal field '{field}'")

    # ── 2. Template renders with dedicated layout ───────────────

    def test_sandbox_template_renders_dedicated_layout(self):
        """
        render_template('predictive_sandbox', ctx) must return the dedicated
        sandbox HTML — not the generic _render_fallback output.

        Failure here means the template raised an exception that was silently
        swallowed (the original bug).
        """
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _build_predictive_sandbox_context, render_template
        from datetime import timezone

        try:
            from jinja2 import Environment
        except ImportError:
            self.skipTest("Jinja2 not installed.")

        start = datetime(2019, 1,  1, tzinfo=timezone.utc)
        end   = datetime(2019, 12, 31, tzinfo=timezone.utc)

        ctx = _build_predictive_sandbox_context(
            variables=self._make_variables(),
            index_results={},
            payload=self._make_payload(),
            report_start=start,
            report_end=end,
        )
        # Inject palette (normally added earlier in generate_report)
        ctx["palette"] = self._FAKE_PALETTE

        html = render_template("predictive_sandbox", ctx)

        # Must not be the generic fallback (which outputs "House 1 Theme" etc.)
        self.assertNotIn("House 1 Theme",       html, "Generic fallback was rendered.")
        self.assertNotIn("NGE Narrative",        html, "Generic fallback was rendered.")
        self.assertNotIn("Saturn House Theme",   html, "Generic fallback was rendered.")

        # Must be the dedicated sandbox template
        self.assertIn("Predictive Sandbox", html,
            "Dedicated sandbox template title not found in output.")

    # ── 3. Required strings present in rendered HTML ────────────

    def test_rendered_html_contains_required_strings(self):
        """
        The generated sandbox HTML must contain all required section headers
        and field names so calibration data is visible without reading console output.
        """
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _build_predictive_sandbox_context, render_template
        from datetime import timezone

        try:
            from jinja2 import Environment
        except ImportError:
            self.skipTest("Jinja2 not installed.")

        start = datetime(2019, 1,  1, tzinfo=timezone.utc)
        end   = datetime(2019, 12, 31, tzinfo=timezone.utc)

        ctx = _build_predictive_sandbox_context(
            variables=self._make_variables(),
            index_results={},
            payload=self._make_payload(),
            report_start=start,
            report_end=end,
        )
        ctx["palette"] = self._FAKE_PALETTE

        html = render_template("predictive_sandbox", ctx)
        html_upper = html.upper()

        required_strings = [
            # Section headers (rendered upper-case in the template)
            "PREDICTIVE WINDOWS",
            "PREDICTIVE SIGNALS",
            "DAILY RESONANCE",
            # Field names — must appear as column headers in the tables
            "local_peak_intensity",
            "structural_field_intensity",
            "total_intensity",
            "prominence",
        ]
        for s in required_strings:
            self.assertIn(
                s.upper(), html_upper,
                f"Required string not found in rendered HTML: '{s}'\n"
                "Either the template is wrong or the context builder is dropping the field."
            )

    # ── 4. No fallback for sandbox on context error ─────────────

    def test_sandbox_error_renders_diagnostic_page_not_fallback(self):
        """
        When the sandbox template raises, the output must be an explicit
        diagnostic page — not the generic _render_fallback output.
        """
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import render_template

        try:
            from jinja2 import Environment
        except ImportError:
            self.skipTest("Jinja2 not installed.")

        # Pass a context that is guaranteed to trigger a template error
        # by omitting all expected keys so Jinja2 undefined-variable errors fire.
        bad_ctx = {"palette": self._FAKE_PALETTE}
        html = render_template("predictive_sandbox", bad_ctx)

        # Must be the sandbox error page, not the generic fallback
        self.assertIn("SANDBOX TEMPLATE ERROR", html,
            "Expected sandbox error diagnostic page but got something else.")
        self.assertNotIn("House 1 Theme", html,
            "Generic fallback was used instead of sandbox error page.")


# ── Manual debug runner ────────────────────────────────────────

from unittest.mock import patch
from engine.transit_engine import scan_lunations

class TestLunationClockFamily(unittest.TestCase):
    @patch("engine.transit_engine._find_lunations")
    def test_eclipse_suppresses_duplicate_lunation(self, mock_find_lunations):
        """eclipse suppresses duplicate plain lunation vote for the same event"""
        eclipse_date = datetime(2026, 8, 12, tzinfo=timezone.utc)
        mock_find_lunations.return_value = [
            (eclipse_date, 15.0, "NEW_MOON")
        ]

        natal_payload = {
            "angles": {"Ascendant": {"longitude": 15.0}},
            "standard_planets": {"Moon": {"longitude": 15.0, "house": 1}},
        }

        eclipse_events = [{
            "event_type": "eclipse",
            "eclipse_type": "Solar",
            "peak_date": "August 12, 2026",
        }]

        lunations = scan_lunations(
            natal_payload,
            start_date=eclipse_date,
            end_date=eclipse_date,
            eclipse_events=eclipse_events
        )
        self.assertEqual(len(lunations), 0, "Duplicate lunation was not suppressed")

    @patch("engine.transit_engine._find_lunations")
    def test_second_clock_family_does_not_break_anti_double_counting(self, mock_find_lunations):
        """a second clock family does not break anti-double-counting rules"""
        lunation_date = datetime(2026, 8, 26, tzinfo=timezone.utc)
        mock_find_lunations.return_value = [
            (lunation_date, 15.0, "FULL_MOON")
        ]

        natal_payload = {
            "angles": {"Ascendant": {"longitude": 15.0}},
            "standard_planets": {"Moon": {"longitude": 15.0, "house": 1}},
        }

        eclipse_events = [{
            "event_type": "eclipse",
            "eclipse_type": "Solar",
            "peak_date": "August 12, 2026",
        }]

        lunations = scan_lunations(
            natal_payload,
            start_date=lunation_date,
            end_date=lunation_date,
            eclipse_events=eclipse_events
        )
        self.assertEqual(len(lunations), 2, "Valid lunation on different date was suppressed")

class TestSandboxJSONLibrary(unittest.TestCase):
    _WINDOW_ROUTING_KEYS = {
        "window_id",
        "start_date",
        "peak_date",
        "end_date",
        "local_peak_intensity",
        "structural_field_intensity",
        "total_intensity",
        "intensity",
        "prominence",
        "gradient",
        "leading_index",
        "active_slow_chapter_signals",
        "active_fast_trigger_signals",
        "active_signals",
        "active_signal_count",
        "coherence",
        "semantic_profile",
        "dominant_operation",
        "semantic_state",
        "semantic_diagnostics",
        "memory",
        "memory_state",
        "activation_key",
        "pass_state",
        "lifecycle_route",
        "method_family",
        "interpretive_tags",
    }

    def test_schema_validation_and_skip(self):
        """Test safe fallback behavior when no block matches."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _predictive_window_narrative

        res = _predictive_window_narrative({"leading_index": "foo", "gradient": "bar"}, [])
        self.assertEqual(res["title"], "An Unclassified Window")
        self.assertEqual(res["dimension"], "foo")

    def test_strong_condition_override(self):
        """Test that a block with more conditions overrides a weaker block."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _predictive_window_narrative

        blocks = [
            {
                "id": "weak",
                "title": "Weak Block",
                "conditions": {"semantic_state": ["reinforcing"]}
            },
            {
                "id": "strong",
                "title": "Strong Block",
                "conditions": {"semantic_state": ["reinforcing"], "gradient": ["rising"]}
            }
        ]

        # Match only the weak condition
        res1 = _predictive_window_narrative({"semantic_state": "reinforcing", "gradient": "plateau"}, blocks)
        self.assertEqual(res1["dimension"], "weak")

        # Match the strong condition (2 conditions > 1 condition)
        res2 = _predictive_window_narrative({"semantic_state": "reinforcing", "gradient": "rising"}, blocks)
        self.assertEqual(res2["dimension"], "strong")

    def test_real_blocks_directory_loads_new_writes(self):
        """Test that the real blocks directory loads and contains entries from 30_new_writes."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _load_predictive_window_blocks

        blocks = _load_predictive_window_blocks()
        self.assertGreater(len(blocks), 0)

        # Check that we found one of the new blocks from 30_new_writes
        # (e.g. ps_frictional_plateau from pressure_system.json)
        found_new_write = any(b.get("id") == "ps_frictional_plateau" for b in blocks)
        self.assertTrue(found_new_write, "Could not find 'ps_frictional_plateau' from 30_new_writes in loaded blocks")

    def test_real_blocks_meet_minimum_schema_and_route_on_window_fields(self):
        """Active block files must parse to the scaffold schema and route on exposed window keys."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _load_predictive_window_blocks

        required = {"id", "scope", "family", "mode", "conditions", "title", "body", "tags", "notes"}
        blocks = _load_predictive_window_blocks()
        self.assertGreater(len(blocks), 0)

        for block in blocks:
            with self.subTest(block_id=block.get("id", "<missing>")):
                self.assertTrue(required.issubset(block.keys()))
                self.assertIsInstance(block["conditions"], dict)
                unknown_keys = set(block["conditions"]) - self._WINDOW_ROUTING_KEYS
                self.assertFalse(
                    unknown_keys,
                    f"Block {block.get('id')} routes on non-window keys: {sorted(unknown_keys)}"
                )

    def test_method_family_condition_can_match_window_context(self):
        """method_family-gated blocks are reachable once window context forwards that field."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from generate import _predictive_window_narrative

        blocks = [
            {
                "id": "return_exactness",
                "family": "threshold_event",
                "title": "Return Exactness",
                "body": "",
                "notes": "",
                "conditions": {"method_family": ["RETURN"], "pass_state": ["EXACTNESS"]},
            }
        ]

        res = _predictive_window_narrative(
            {"method_family": "RETURN", "pass_state": "EXACTNESS", "gradient": "plateau"},
            blocks,
        )
        self.assertEqual(res["dimension"], "return_exactness")


if __name__ == "__main__":
    print("=" * 60)
    print("Predictive Engine Tests (predictive_v0.3.1)")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        TestPredictiveEngineContract,
        TestSignalExtraction,
        TestDailySeries,
        TestWindowDetection,
        TestPredictivePhaseFSM,
        TestRegistry,
        TestProminenceHelpers,
        TestDailySeriesV02,
        TestWindowDetectionRegression,
        TestSandboxEndToEnd,
        TestLunationClockFamily,
        TestSandboxJSONLibrary,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
