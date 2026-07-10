import unittest
from datetime import datetime, timezone
from engine.forecast_event_adapter import normalize_to_forecast_event, _generate_event_id

class TestForecastEventAdapter(unittest.TestCase):
    def test_transit_enrichment(self):
        raw_event = {
            "event_type": "transit",
            "transit_planet": "Saturn",
            "natal_target": "Moon",
            "aspect": "Square",
            "peak_datetime": datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc),
            "entry_datetime": datetime(2026, 7, 5, 0, 0, tzinfo=timezone.utc),
            "leave_datetime": datetime(2026, 7, 15, 0, 0, tzinfo=timezone.utc),
            "combined_intensity_score": 0.85,
            "cycle_id": "saturn_moon_cycle",
            "exactness": 0.9,
            "confidence": 0.82,
            "confidence_components": {"calculation_integrity": 0.95},
            "report_surface_visibility": ["internal_rd"],
            "exact_datetimes": [datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)],
        }

        enriched = normalize_to_forecast_event(raw_event)

        # Legacy fields preserved
        self.assertEqual(enriched["transit_planet"], "Saturn")
        self.assertEqual(enriched["cycle_id"], "saturn_moon_cycle")

        # Canonical fields added
        self.assertEqual(enriched["schema_version"], "phase0.1.0")
        self.assertEqual(enriched["method_family"], "TRANSIT")
        self.assertEqual(enriched["method_variant"], "transit_cycle")
        self.assertEqual(enriched["independence_group"], "transit_family")
        self.assertEqual(enriched["source_body"], "Saturn")
        self.assertEqual(enriched["source_kind"], "planet")
        self.assertEqual(enriched["target_body"], "Moon")
        self.assertEqual(enriched["target_kind"], "luminary")
        self.assertEqual(enriched["activation_route"], "transit_to_body")
        self.assertEqual(enriched["start_at"], datetime(2026, 7, 5, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(enriched["peak_at"], datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(enriched["end_at"], datetime(2026, 7, 15, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(enriched["event_strength"], 0.85)
        
        self.assertEqual(enriched["confidence"], 0.82)
        self.assertEqual(
            enriched["exact_at"],
            [datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)],
        )
        self.assertEqual(enriched["report_surface_visibility"], ["internal_rd"])

        # ID deterministic check
        expected_id = _generate_event_id("TRANSIT", "transit_cycle", datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc), "Saturn", "Moon", "Square")
        self.assertEqual(enriched["event_id"], expected_id)

    def test_instant_event_policy(self):
        raw_event = {
            "event_type": "eclipse",
            "eclipse_type": "Total Solar",
            "source_body": "Sun",
            "peak_datetime": datetime(2026, 8, 12, 17, 30, tzinfo=timezone.utc),
            "score": 0.95
        }
        
        enriched = normalize_to_forecast_event(raw_event)
        
        self.assertEqual(enriched["start_at"], datetime(2026, 8, 12, 17, 30, tzinfo=timezone.utc))
        self.assertEqual(enriched["peak_at"], datetime(2026, 8, 12, 17, 30, tzinfo=timezone.utc))
        self.assertEqual(enriched["end_at"], datetime(2026, 8, 12, 17, 30, tzinfo=timezone.utc))
        
        self.assertEqual(enriched["phase"], "Total Solar")
        self.assertIsNone(enriched.get("orb"))
        self.assertEqual(enriched["temporal_precision"], "instant")
        self.assertEqual(enriched["method_family"], "LUNATION")
        self.assertEqual(enriched["source_kind"], "luminary")
        # The fixture does not provide a charter-approved lunation route. The
        # adapter records that gap instead of inventing a route outside the
        # canonical activation-route vocabulary.
        self.assertEqual(enriched["activation_route"], "unknown")
        self.assertIn("activation_route", enriched["calculation_trace"]["missing_fields"])

    def test_missing_evidence_is_conservative_not_fabricated(self):
        raw_event = {
            "event_type": "transit",
            "transit_planet": "Saturn",
            "natal_target": "Moon",
            "peak_datetime": datetime(2026, 7, 10, tzinfo=timezone.utc),
        }

        enriched = normalize_to_forecast_event(raw_event)

        self.assertIsNone(enriched["orb"])
        self.assertIsNone(enriched["distance"])
        self.assertIsNone(enriched["phase"])
        self.assertEqual(enriched["confidence"], 0.0)
        self.assertEqual(
            enriched["report_surface_visibility"],
            ["internal_rd"],
        )
        self.assertIn("confidence", enriched["calculation_trace"]["missing_fields"])

    def test_ingress_angle_event(self):
        # A simulated ingress into an angular house or ascendant
        raw_event = {
            "event_type": "ingress",
            "transit_planet": "Jupiter",
            "natal_target": "ASC",
            "peak_datetime": datetime(2027, 2, 1, 0, 0, tzinfo=timezone.utc),
            "entry_datetime": datetime(2027, 2, 1, 0, 0, tzinfo=timezone.utc),
            "leave_datetime": datetime(2028, 2, 1, 0, 0, tzinfo=timezone.utc),
        }
        
        enriched = normalize_to_forecast_event(raw_event)
        self.assertEqual(enriched["method_variant"], "ingress")
        self.assertEqual(enriched["source_kind"], "planet")
        self.assertEqual(enriched["target_kind"], "angle")
        self.assertEqual(enriched["activation_route"], "transit_to_angle")

    def test_solar_arc_event(self):
        raw_event = {
            "event_type": "solar_arc",
            "source_body": "MC",
            "natal_target": "Venus",
            "peak_datetime": datetime(2030, 5, 1, 0, 0, tzinfo=timezone.utc),
        }
        
        enriched = normalize_to_forecast_event(raw_event)
        self.assertEqual(enriched["method_family"], "SOLAR_ARC")
        self.assertEqual(enriched["source_kind"], "angle")
        self.assertEqual(enriched["target_kind"], "planet")
        self.assertEqual(enriched["activation_route"], "solar_arc_to_body")
        self.assertEqual(enriched["independence_group"], "solar_arc_family")

if __name__ == '__main__':
    unittest.main()
