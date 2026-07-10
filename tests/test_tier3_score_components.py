import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from formulas.standard.forecast_activation import (
    SCORE_COMPONENT_KEYS,
    build_forecast_activation_profile,
    build_ranking_diagnostics,
    enrich_forecast_event,
)
from generate import _build_month_timing_windows, _monthly_peak_diagnostics
from phase2_fixtures import build_payload


class Tier3ScoreComponentTests(unittest.TestCase):
    def setUp(self):
        payload = build_payload(
            asc_sign="Leo",
            placements={
                "Sun": 5.0,
                "Moon": 12.0,
                "Mercury": 8.0,
                "Venus": 42.0,
                "Mars": 98.0,
                "Jupiter": 122.0,
                "Saturn": 275.0,
                "Uranus": 281.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            },
        )
        self.profile = build_forecast_activation_profile(payload)

    def _transit(
        self,
        target: str,
        *,
        score: float = 0.6,
        orb: float = 0.4,
        day: int = 1,
        conflict: float | None = None,
    ) -> dict:
        peak = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=day)
        event = {
            "event_type": "transit",
            "transit_planet": "Saturn",
            "aspect": "Square",
            "natal_target": target,
            "natal_house": 1 if target in {"Sun", "Moon"} else 6,
            "maximum_orb": 3.0,
            "orb": orb,
            "concentration_score": score,
            "combined_intensity_score": score,
            "raw_score": score,
            "entry_datetime": peak - timedelta(days=3),
            "peak_datetime": peak,
            "leave_datetime": peak + timedelta(days=3),
            "peak_date": peak.date().isoformat(),
            "date_label": peak.strftime("%B %d, %Y"),
            "duration_days": 6,
            "contact_count": 1,
            "title": f"Saturn Square natal {target}",
        }
        if conflict is not None:
            event["counterforce_conflict"] = conflict
        return event

    def test_event_exposes_complete_named_component_contract(self):
        enriched = enrich_forecast_event(
            self._transit("Sun", score=0.72, orb=0.15),
            self.profile,
        )

        self.assertEqual(set(enriched["score_components"]), set(SCORE_COMPONENT_KEYS))
        totals = enriched["score_component_totals"]
        contribution_total = round(
            sum(component["contribution"] for component in enriched["score_components"].values()),
            4,
        )
        self.assertEqual(totals["raw_total"], contribution_total)
        self.assertEqual(enriched["combined_intensity_score"], totals["aggregate_score"])

        diagnostics = enriched["ranking_diagnostics"]
        self.assertEqual(diagnostics["context"], "reader_activity")
        self.assertTrue(diagnostics["top_components"])
        self.assertIn(
            diagnostics["top_components"][0]["component"],
            SCORE_COMPONENT_KEYS,
        )

    def test_dense_synthetic_period_keeps_meaningful_score_distribution(self):
        targets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Saturn"]
        raw_events = []
        for index in range(36):
            target = targets[index % len(targets)]
            concentration = 0.18 + (index % 9) * 0.08
            orb = [0.05, 0.25, 0.75, 1.4, 2.3, 2.8][index % 6]
            conflict = 0.7 if index in {8, 17, 26} else None
            raw_events.append(
                self._transit(
                    target,
                    score=concentration,
                    orb=orb,
                    day=index,
                    conflict=conflict,
                )
            )

        enriched = [enrich_forecast_event(event, self.profile) for event in raw_events]
        scores = [event["combined_intensity_score"] for event in enriched]
        decile_bands = {int(score * 10) for score in scores}
        ceiling_cluster = [score for score in scores if score >= 0.90]

        self.assertGreater(max(scores) - min(scores), 0.30)
        self.assertGreaterEqual(len(decile_bands), 5)
        self.assertLessEqual(len(ceiling_cluster), 1)
        top_event = max(enriched, key=lambda event: event["combined_intensity_score"])
        self.assertIn(top_event["natal_target"], {"Sun", "Moon"})
        self.assertNotIn("counterforce_conflict", top_event)

    def test_counterforce_conflict_reduces_otherwise_identical_event(self):
        base = enrich_forecast_event(
            self._transit("Sun", score=0.76, orb=0.12),
            self.profile,
        )
        conflicted = enrich_forecast_event(
            self._transit("Sun", score=0.76, orb=0.12, conflict=0.8),
            self.profile,
        )

        self.assertLess(conflicted["combined_intensity_score"], base["combined_intensity_score"])
        self.assertLess(
            conflicted["score_components"]["counterforce_conflict"]["contribution"],
            0.0,
        )
        self.assertEqual(
            conflicted["ranking_diagnostics"]["conflict_component"]["status"],
            "supported",
        )

    def test_one_strong_component_does_not_force_overactivation(self):
        exact_but_low_context = enrich_forecast_event(
            self._transit("Saturn", score=0.08, orb=0.0),
            self.profile,
        )

        self.assertEqual(
            exact_but_low_context["score_components"]["timing_exactness"]["value"],
            1.0,
        )
        self.assertLess(exact_but_low_context["combined_intensity_score"], 0.35)

    def test_ranked_and_monthly_diagnostics_use_component_records(self):
        period_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        period_end = datetime(2026, 2, 1, tzinfo=timezone.utc)
        events = [
            enrich_forecast_event(self._transit("Sun", score=0.82, orb=0.1, day=5), self.profile),
            enrich_forecast_event(self._transit("Saturn", score=0.34, orb=0.3, day=8), self.profile),
            enrich_forecast_event(self._transit("Moon", score=0.52, orb=1.8, day=12), self.profile),
        ]

        month_diag = _monthly_peak_diagnostics(events, period_start, period_end)
        self.assertEqual(month_diag["context"], "year_ahead_monthly_peak")
        self.assertTrue(month_diag["top_contributors"])
        self.assertTrue(month_diag["top_event_diagnostics"]["top_components"])

        ranked_windows = _build_month_timing_windows({"events": events})
        self.assertTrue(ranked_windows)
        self.assertEqual(
            ranked_windows[0]["ranking_diagnostics"]["context"],
            "year_ahead_month_timing_window",
        )
        self.assertTrue(ranked_windows[0]["ranking_diagnostics"]["top_components"])

        direct_diag = build_ranking_diagnostics(
            events[0],
            context="direct_test",
            rank_score=events[0]["combined_intensity_score"],
        )
        self.assertEqual(
            direct_diag["top_components"],
            events[0]["ranking_diagnostics"]["top_components"],
        )


if __name__ == "__main__":
    unittest.main()
