import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from formulas.established_niche import evaluate_selected_specialist_bodies, evaluate_specialist_body
from formulas.governance_registry import (
    ASTEROID_ELIGIBILITY_REGISTRY,
    METHOD_STATUS_EO_PROPRIETARY,
    REPORT_PROFILE_CORE_STANDARD_ONLY,
    REPORT_PROFILE_CORE_STANDARD_PLUS_ESTABLISHED_NICHE,
    REPORT_PROFILE_FULL_ENTANGLED_ORACLE,
    authoritative_catalog,
    get_body_registry_record,
    get_report_layer_profile,
)
from formulas.proprietary_indexes import compute_all_indexes
from formulas.report_surface import build_layered_report_bundle
from formulas.standard.chart_structure import evaluate_chart_structure
from formulas.standard.dignity import evaluate_dignity
from formulas.standard.planetary_prominence import evaluate_prominence
from tests.phase2_fixtures import build_payload, make_body


class EstablishedNicheGovernancePhase3Tests(unittest.TestCase):
    def _payload_with_specialists(self, simple_mode: bool = False):
        payload = build_payload(
            simple_mode=simple_mode,
            custom_asteroids={
                "Lilith_Asteroid": make_body(45.0, 0.0, speed=0.08),
                "Kassandra": make_body(90.0, 0.0, speed=0.04),
                "Apollo": make_body(120.0, 0.0, speed=0.03),
                "Themis": make_body(150.0, 0.0, speed=0.03),
            },
        )
        payload["standard_planets"]["Lilith_BML"] = make_body(210.0, 0.0, speed=0.0)
        payload["standard_planets"]["Chiron"] = make_body(305.0, 0.0, speed=-0.01)
        payload["aspects"].extend(
            [
                {"body_1": "Lilith_Asteroid", "body_2": "Venus", "aspect": "Sextile", "orb": 0.0, "angle": 60.0},
                {"body_1": "Lilith_BML", "body_2": "Saturn", "aspect": "Square", "orb": 0.0, "angle": 90.0},
                {"body_1": "Chiron", "body_2": "Moon", "aspect": "Trine", "orb": 5.0, "angle": 120.0},
                {"body_1": "Kassandra", "body_2": "Mercury", "aspect": "Conjunction", "orb": 2.0, "angle": 2.0},
            ]
        )
        return payload

    def test_authoritative_registries_classify_bodies_methods_and_asteroids(self):
        catalog = authoritative_catalog()
        self.assertIn("Lilith_BML", catalog["bodies_and_points"])
        self.assertIn("Lilith_Asteroid", catalog["bodies_and_points"])
        self.assertEqual(
            get_body_registry_record("Chiron").method_status,
            "established_niche",
        )
        self.assertEqual(
            ASTEROID_ELIGIBILITY_REGISTRY["Kassandra"].eo_proprietary_uses,
            ("KVQ",),
        )
        self.assertIn("KVQ", catalog["methods"])

    def test_chiron_and_both_lilith_forms_remain_distinct(self):
        payload = self._payload_with_specialists()
        chiron = evaluate_specialist_body(payload, "Chiron", "soul_ecosystem")
        bml = evaluate_specialist_body(payload, "Lilith_BML", "soul_ecosystem")
        asteroid_lilith = evaluate_specialist_body(payload, "Lilith_Asteroid", "soul_ecosystem")

        self.assertEqual(chiron["method_status"], "established_niche")
        self.assertEqual(bml["body_or_point"], "Lilith_BML")
        self.assertEqual(asteroid_lilith["body_or_point"], "Lilith_Asteroid")
        self.assertNotEqual(bml["data"]["sign"], asteroid_lilith["data"]["sign"])

    def test_present_and_absent_specialists_and_no_fallback_between_lilith_forms(self):
        payload = self._payload_with_specialists()
        absent_payload = build_payload(custom_asteroids={})
        absent_payload["standard_planets"].pop("Lilith_BML", None)

        present = compute_all_indexes(payload)
        absent = compute_all_indexes(absent_payload)

        self.assertEqual(present["DFIS"]["lilith_source"], "Lilith_BML")
        self.assertEqual(absent["DFIS"]["lilith_source"], "Lilith_BML")
        self.assertEqual(absent["DFIS"]["components"]["lilith"], 0.0)

    def test_asteroid_can_be_available_but_report_ineligible_or_suppressed(self):
        payload = self._payload_with_specialists()
        core_result = evaluate_specialist_body(payload, "Kassandra", "horoscope")
        expanded_result = evaluate_specialist_body(payload, "Kassandra", "soul_ecosystem")

        self.assertEqual(core_result["visibility_state"], "suppressed")
        self.assertIn("body_not_report_eligible", core_result["limitations"])
        self.assertNotEqual(expanded_result["visibility_state"], "suppressed")

    def test_layer_profiles_distinguish_core_niche_and_eo_outputs(self):
        payload = self._payload_with_specialists()
        index_results = compute_all_indexes(payload)

        core_bundle = build_layered_report_bundle(payload, "horoscope", index_results=index_results)
        niche_bundle = build_layered_report_bundle(payload, "soul_ecosystem", index_results=None, specialist_body_keys=["Kassandra"])
        eo_bundle = build_layered_report_bundle(payload, "soul_ecosystem", index_results=index_results, specialist_body_keys=["Kassandra"])

        self.assertEqual(core_bundle["report_profile"], REPORT_PROFILE_CORE_STANDARD_ONLY)
        self.assertFalse(core_bundle["eo_proprietary"])
        self.assertFalse(core_bundle["established_niche"])

        self.assertEqual(niche_bundle["report_profile"], REPORT_PROFILE_FULL_ENTANGLED_ORACLE)
        self.assertTrue(niche_bundle["established_niche"])
        self.assertFalse(niche_bundle["eo_proprietary"])

        self.assertTrue(eo_bundle["core_standard"])
        self.assertTrue(eo_bundle["eo_proprietary"])
        self.assertTrue(eo_bundle["established_niche"])

    def test_individual_asteroid_and_eo_formula_paths_remain_distinct(self):
        payload = self._payload_with_specialists()
        individual = evaluate_specialist_body(payload, "Kassandra", "soul_ecosystem")
        eo = compute_all_indexes(payload)["KVQ"]

        self.assertEqual(individual["method_status"], "established_niche")
        self.assertEqual(eo["method_status"], METHOD_STATUS_EO_PROPRIETARY)
        self.assertNotIn("archetype", individual["data"])
        self.assertIn("archetype", eo)

    def test_core_standard_calculations_do_not_become_specialist_dependent(self):
        payload = self._payload_with_specialists()
        without_specialists = build_payload()
        with_structure = evaluate_chart_structure(payload)
        without_structure = evaluate_chart_structure(without_specialists)

        self.assertNotIn("Lilith_Asteroid", str(with_structure["core_standard_distribution"]))
        self.assertEqual(
            set(with_structure["core_standard_distribution"]["included_bodies"][0].keys()),
            {"body", "status", "sign"},
        )
        self.assertEqual(
            with_structure["core_standard_distribution"]["element_counts"],
            without_structure["core_standard_distribution"]["element_counts"],
        )

        dignity = evaluate_dignity(payload, "Chiron")
        prominence = evaluate_prominence(payload)
        self.assertFalse(dignity.get("is_triplicity", False))
        self.assertNotIn("Lilith_Asteroid", {item["body"] for item in prominence["rankings"]})

    def test_missing_data_birth_time_dependency_and_confidence_are_exposed(self):
        payload = self._payload_with_specialists(simple_mode=True)
        lilith = evaluate_specialist_body(payload, "Lilith_Asteroid", "soul_ecosystem")

        self.assertEqual(lilith["confidence_state"], "angle_dependent_unavailable")
        self.assertIn("angle_contacts_unavailable_without_exact_birth_time", lilith["limitations"])

        missing = evaluate_specialist_body(build_payload(), "Lilith_Asteroid", "soul_ecosystem")
        self.assertEqual(missing["visibility_state"], "suppressed")
        self.assertIn("body_missing_from_payload", missing["limitations"])

    def test_metadata_survives_trace_and_serialization(self):
        payload = self._payload_with_specialists()
        bundle = build_layered_report_bundle(
            payload,
            "soul_ecosystem",
            index_results=compute_all_indexes(payload),
            specialist_body_keys=["Chiron", "Lilith_BML", "Lilith_Asteroid"],
        )
        serialized = json.dumps(bundle)
        self.assertIn("method_status", serialized)
        self.assertIn("report_eligibility", serialized)
        self.assertIn("visibility_state", serialized)
        self.assertIn("confidence_state", serialized)


if __name__ == "__main__":
    unittest.main()
