import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from formulas.standard.aspect_architecture import evaluate_aspect_architecture
from formulas.standard.chart_structure import evaluate_chart_structure
from formulas.standard.natal_convergence import evaluate_standard_natal_convergence
from formulas.standard.named_configurations import evaluate_named_configurations
from formulas.standard.planetary_condition import evaluate_all_planetary_conditions
from formulas.standard.planetary_prominence import evaluate_prominence
from formulas.standard.rulership_network import evaluate_rulership_network
from phase2_fixtures import build_payload


class StandardNatalArchitecturePhase2Tests(unittest.TestCase):
    def test_rulership_network_supports_final_dispositors_loops_and_mutual_reception(self):
        single = build_payload(
            placements={
                "Sun": 70.0,
                "Moon": 5.0,
                "Mercury": 35.0,
                "Venus": 10.0,
                "Mars": 5.0,
                "Jupiter": 130.0,
                "Saturn": 155.0,
                "Uranus": 215.0,
                "Neptune": 250.0,
                "Pluto": 285.0,
                "Chiron": 355.0,
            }
        )
        single_result = evaluate_rulership_network(single)
        self.assertEqual(single_result["final_dispositors"], ["Mars"])
        self.assertEqual(single_result["dispositor_chains"]["Mercury"]["final_dispositor"], "Mars")
        self.assertEqual(single_result["house_rulers"][8]["traditional_ruler"], "Mars")
        self.assertEqual(single_result["house_rulers"][8]["modern_secondary_ruler"], "Pluto")
        self.assertEqual(single_result["houses_by_traditional_ruler"]["Mars"], [1, 8])

        multiple = build_payload(
            placements={
                "Sun": 70.0,
                "Moon": 35.0,
                "Mercury": 165.0,
                "Venus": 35.0,
                "Mars": 200.0,
                "Jupiter": 80.0,
                "Saturn": 200.0,
                "Uranus": 250.0,
                "Neptune": 300.0,
                "Pluto": 285.0,
                "Chiron": 355.0,
            }
        )
        multiple_result = evaluate_rulership_network(multiple)
        self.assertEqual(multiple_result["final_dispositors"], ["Mercury", "Venus"])

        looped = build_payload(
            placements={
                "Sun": 10.0,
                "Moon": 45.0,
                "Mercury": 215.0,
                "Venus": 10.0,
                "Mars": 35.0,
                "Jupiter": 120.0,
                "Saturn": 280.0,
                "Uranus": 333.0,
                "Neptune": 344.0,
                "Pluto": 317.0,
                "Chiron": 222.0,
            }
        )
        loop_result = evaluate_rulership_network(looped)
        self.assertTrue(loop_result["closed_loops"])
        self.assertIn(["Mars", "Venus"], [item["bodies"] for item in loop_result["mutual_receptions"]])

    def test_aspect_architecture_distinguishes_hubs_isolation_and_angle_links(self):
        payload = build_payload(
            placements={
                "Sun": 1.0,
                "Moon": 181.0,
                "Mercury": 91.0,
                "Venus": 121.0,
                "Mars": 271.0,
                "Jupiter": 97.0,
                "Saturn": 92.0,
                "Uranus": 211.0,
                "Neptune": 17.0,
                "Pluto": 300.0,
                "Chiron": 330.0,
            }
        )
        result = evaluate_aspect_architecture(payload)
        mercury_connectivity = result["connectivity"]["Mercury"]
        neptune_connectivity = result["connectivity"]["Neptune"]
        self.assertIn(mercury_connectivity["state"], {"hub", "high_connectivity"})
        self.assertEqual(neptune_connectivity["state"], "isolated")
        self.assertFalse(
            [
                item for item in result["connections"]
                if item["body_2"] in {"Descendant", "Imum_Coeli"}
            ]
        )

        luminary_angle = [
            item for item in result["connections"]
            if item["body_1"] == "Sun" and item["body_2"] == "Ascendant"
        ]
        self.assertTrue(luminary_angle)

        tight = next(
            item for item in result["connections"]
            if item["body_1"] == "Mercury" and item["body_2"] == "Saturn"
        )
        wide = next(
            item for item in result["connections"]
            if item["body_1"] == "Mercury" and item["body_2"] == "Jupiter"
        )
        self.assertGreater(tight["normalized_strength"], wide["normalized_strength"])

    def test_low_dignity_hub_and_well_conditioned_nonprominent_planet_can_coexist(self):
        payload = build_payload(
            asc_sign="Gemini",
            placements={
                "Sun": 1.0,
                "Moon": 181.0,
                "Mercury": 359.0,
                "Venus": 121.0,
                "Mars": 271.0,
                "Jupiter": 94.0,
                "Saturn": 96.0,
                "Uranus": 211.0,
                "Neptune": 300.0,
                "Pluto": 330.0,
                "Chiron": 150.0,
            }
        )
        aspect_result = evaluate_aspect_architecture(payload)
        conditions = evaluate_all_planetary_conditions(payload)
        prominence = evaluate_prominence(payload)
        prominence_map = {item["body"]: item for item in prominence["rankings"]}

        self.assertIn(aspect_result["connectivity"]["Mercury"]["state"], {"hub", "high_connectivity"})
        self.assertIn(conditions["Mercury"].condition_classification, {"challenged", "severely_challenged"})
        self.assertIn(conditions["Jupiter"].condition_classification, {"strong", "excellent"})
        self.assertLess(prominence_map["Jupiter"]["normalized_score"], prominence_map["Mercury"]["normalized_score"])

    def test_chart_structure_keeps_core_and_expanded_distributions_separate(self):
        payload = build_payload(simple_mode=True)
        result = evaluate_chart_structure(payload)
        self.assertEqual(
            result["hemisphere_and_quadrant"]["confidence"],
            "angle_dependent_unavailable",
        )
        self.assertIn("astronomical_phase_angle", result["lunar_phase"])
        self.assertIn("state", result["sun_moon_architecture"])
        self.assertEqual(
            {item["body"] for item in result["core_standard_distribution"]["included_bodies"]},
            {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"},
        )
        expanded = result["expanded_established_niche_distribution"]["included_bodies"]
        self.assertTrue(any(item["body"] == "Uranus" and item["status"] == "established_niche" for item in expanded))

    def test_named_configurations_handle_none_single_and_overlapping_cases(self):
        none_payload = build_payload(
            placements={
                "Sun": 3.0,
                "Moon": 29.0,
                "Mercury": 67.0,
                "Venus": 101.0,
                "Mars": 146.0,
                "Jupiter": 173.0,
                "Saturn": 217.0,
                "Uranus": 251.0,
                "Neptune": 289.0,
                "Pluto": 314.0,
                "Chiron": 341.0,
            }
        )
        self.assertEqual(evaluate_named_configurations(none_payload)["configurations"], [])

        stellium_payload = build_payload(
            placements={
                "Sun": 275.0,
                "Moon": 281.0,
                "Mercury": 288.0,
                "Venus": 138.0,
                "Mars": 184.0,
                "Jupiter": 233.0,
                "Saturn": 320.0,
                "Uranus": 321.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            }
        )
        stellium_types = [item["type"] for item in evaluate_named_configurations(stellium_payload)["configurations"]]
        self.assertIn("stellium", stellium_types)

        overlapping_payload = build_payload(
            placements={
                "Sun": 5.0,
                "Moon": 125.0,
                "Jupiter": 245.0,
                "Saturn": 65.0,
                "Mercury": 188.0,
                "Venus": 319.0,
                "Mars": 211.0,
                "Uranus": 333.0,
                "Neptune": 350.0,
                "Pluto": 278.0,
                "Chiron": 150.0,
            }
        )
        overlapping_types = [item["type"] for item in evaluate_named_configurations(overlapping_payload)["configurations"]]
        self.assertIn("grand_trine", overlapping_types)
        self.assertIn("kite", overlapping_types)

    def test_convergence_surfaces_traceable_structures_without_proprietary_inputs(self):
        vocational_payload = build_payload(
            placements={
                "Sun": 275.0,
                "Moon": 281.0,
                "Mercury": 288.0,
                "Venus": 138.0,
                "Mars": 279.0,
                "Jupiter": 95.0,
                "Saturn": 305.0,
                "Uranus": 321.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            }
        )
        convergence = evaluate_standard_natal_convergence(vocational_payload)
        vocational = convergence["vocational / public structure"]
        self.assertGreater(vocational["normalized_relevance_score"], 0.45)
        self.assertGreaterEqual(len(vocational["independent_supporting_factors"]), 2)
        self.assertIn("trace", convergence)
        self.assertNotIn("proprietary", str(convergence["trace"]).lower())

        relational_payload = build_payload(
            placements={
                "Sun": 15.0,
                "Moon": 195.0,
                "Mercury": 205.0,
                "Venus": 185.0,
                "Mars": 215.0,
                "Jupiter": 145.0,
                "Saturn": 305.0,
                "Uranus": 321.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            }
        )
        relational = evaluate_standard_natal_convergence(relational_payload)["relational structure"]
        self.assertGreater(relational["normalized_relevance_score"], 0.35)

        inner_life_payload = build_payload(
            placements={
                "Sun": 92.0,
                "Moon": 118.0,
                "Mercury": 334.0,
                "Venus": 345.0,
                "Mars": 101.0,
                "Jupiter": 155.0,
                "Saturn": 305.0,
                "Uranus": 321.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            }
        )
        inner_life = evaluate_standard_natal_convergence(inner_life_payload)["inner-life / restoration structure"]
        self.assertGreater(inner_life["normalized_relevance_score"], 0.35)

    def test_central_planets_and_life_domains_are_evidence_gated(self):
        payload = build_payload(
            placements={
                "Sun": 275.0,
                "Moon": 281.0,
                "Mercury": 288.0,
                "Venus": 138.0,
                "Mars": 279.0,
                "Jupiter": 95.0,
                "Saturn": 305.0,
                "Uranus": 321.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            }
        )
        convergence = evaluate_standard_natal_convergence(payload)
        self.assertTrue(convergence["central_planets"])
        for item in convergence["central_planets"]:
            self.assertGreaterEqual(len(item["independent_supporting_factors"]), 2)
        for item in convergence["central_life_domains"]:
            if item["normalized_relevance_score"] > 0:
                self.assertIn("methodology", item)
                self.assertIn("formula_version", item)


if __name__ == "__main__":
    unittest.main()
