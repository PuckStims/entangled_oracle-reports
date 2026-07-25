import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.synastry import (
    SCHEMA_VERSION,
    build_pair_payload,
)
from formulas.standard.confidence import (
    APPROXIMATE_BIRTH_TIME,
    EXACT_BIRTH_TIME,
    UNKNOWN_BIRTH_TIME,
)


SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def sign_for(longitude):
    return SIGNS[int((longitude % 360.0) // 30.0)]


def whole_sign_house(longitude, ascendant):
    body_sign = int((longitude % 360.0) // 30.0)
    asc_sign = int((ascendant % 360.0) // 30.0)
    return ((body_sign - asc_sign) % 12) + 1


def body(longitude, ascendant):
    degree_decimal = longitude % 30.0
    return {
        "longitude": round(longitude % 360.0, 4),
        "speed": 1.0,
        "retrograde": False,
        "house": whole_sign_house(longitude, ascendant),
        "sign": sign_for(longitude),
        "degree": int(degree_decimal),
        "minute": int((degree_decimal % 1.0) * 60),
        "degree_decimal": round(degree_decimal, 4),
    }


def houses(ascendant):
    asc_index = int((ascendant % 360.0) // 30.0)
    return {
        f"House_{index + 1}": {
            "longitude": float(((asc_index + index) % 12) * 30),
            "sign": SIGNS[(asc_index + index) % 12],
            "degree": 0,
            "minute": 0,
            "degree_decimal": 0.0,
        }
        for index in range(12)
    }


def angles(ascendant):
    midheaven = 90.0
    return {
        "Ascendant": body(ascendant, ascendant),
        "Descendant": body(ascendant + 180.0, ascendant),
        "Midheaven": body(midheaven, ascendant),
        "Imum_Coeli": body(midheaven + 180.0, ascendant),
        "Vertex": body(210.0, ascendant),
    }


def natal_payload(placements, *, ascendant=0.0, state=EXACT_BIRTH_TIME):
    return {
        "simple_mode": state == UNKNOWN_BIRTH_TIME,
        "user_profile": {
            "name": f"Fixture {state}",
            "simple_mode": state == UNKNOWN_BIRTH_TIME,
            "birth_time_state": state,
            "birth_time_confidence": state,
            "house_system": "Whole Sign",
            "zodiac": "Tropical",
        },
        "standard_planets": {
            name: body(longitude, ascendant)
            for name, longitude in placements.items()
        },
        "angles": angles(ascendant),
        "houses": houses(ascendant),
        "aspects": [],
        "custom_asteroids": {},
    }


class SynastryComputationTests(unittest.TestCase):
    def test_exact_time_pair_produces_pair_payload(self):
        pair = build_pair_payload(
            natal_payload({"Sun": 10.0, "Venus": 15.0}, ascendant=0.0),
            natal_payload({"Moon": 130.0, "Mars": 20.0}, ascendant=30.0),
        )

        self.assertEqual(pair["schema_version"], SCHEMA_VERSION)
        self.assertEqual(pair["person_a"]["label"], "A")
        self.assertTrue(pair["person_a"]["angle_eligible"])
        self.assertTrue(pair["computations"]["directional_aspects"])
        self.assertIn("sidecar", pair)

    def test_unknown_person_a_withholds_b_in_a_overlays_and_a_owned_angle_contacts(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0}, ascendant=0.0, state=UNKNOWN_BIRTH_TIME),
            natal_payload({"Mars": 10.0}, ascendant=30.0),
        )

        overlays = pair["computations"]["house_overlays"]
        self.assertTrue(
            any(
                item["source_person"] == "B"
                and item["target_person"] == "A"
                and item["withheld"]
                for item in overlays
            )
        )
        directional = pair["computations"]["directional_aspects"]
        self.assertTrue(
            any(
                item["target_person"] == "A"
                and item["target_body"] == "Ascendant"
                and item["withheld"]
                for item in directional
            )
        )

    def test_unknown_person_b_withholds_a_in_b_overlays_and_b_owned_angle_contacts(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0}, ascendant=0.0),
            natal_payload({"Mars": 10.0}, ascendant=30.0, state=UNKNOWN_BIRTH_TIME),
        )

        overlays = pair["computations"]["house_overlays"]
        self.assertTrue(
            any(
                item["source_person"] == "A"
                and item["target_person"] == "B"
                and item["withheld"]
                for item in overlays
            )
        )
        directional = pair["computations"]["directional_aspects"]
        self.assertTrue(
            any(
                item["target_person"] == "B"
                and item["target_body"] == "Ascendant"
                and item["withheld"]
                for item in directional
            )
        )

    def test_body_to_body_aspects_compute_when_birth_time_is_unknown(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0}, state=UNKNOWN_BIRTH_TIME),
            natal_payload({"Mars": 14.0}),
        )

        live_contacts = [
            item
            for item in pair["computations"]["directional_aspects"]
            if not item["withheld"]
        ]
        self.assertTrue(
            any(
                item["source_body"] == "Venus"
                and item["target_body"] == "Mars"
                and item["aspect"] == "Conjunction"
                for item in live_contacts
            )
        )

    def test_synastry_aspects_respect_max_orb_synastry(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0}),
            natal_payload({"Mars": 15.1}),
        )

        self.assertFalse(
            [
                item
                for item in pair["computations"]["directional_aspects"]
                if not item["withheld"]
                and item["source_body"] == "Venus"
                and item["target_body"] == "Mars"
            ]
        )

    def test_midpoint_composite_handles_zero_aries_wrap(self):
        pair = build_pair_payload(
            natal_payload({"Sun": 359.0}),
            natal_payload({"Sun": 1.0}),
        )

        sun = next(
            item
            for item in pair["computations"]["composite"]["bodies"]
            if item["body"] == "Sun"
        )
        self.assertEqual(sun["longitude"], 0.0)
        self.assertFalse(sun["ambiguous"])
        self.assertEqual(sun["zodiac_position"]["sign"], "Aries")

    def test_opposite_point_composite_ambiguity_is_flagged(self):
        pair = build_pair_payload(
            natal_payload({"Moon": 0.0}),
            natal_payload({"Moon": 180.0}),
        )

        moon = next(
            item
            for item in pair["computations"]["composite"]["bodies"]
            if item["body"] == "Moon"
        )
        self.assertTrue(moon["ambiguous"])
        self.assertIsNone(moon["longitude"])
        self.assertEqual(moon["possible_midpoints"], [90.0, 270.0])

    def test_mutual_normalization_keeps_directional_evidence_and_salience_trace(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0}),
            natal_payload({"Mars": 14.0}),
        )

        mutual = next(
            item
            for item in pair["computations"]["mutual_aspects"]
            if {entry["body"] for entry in item["mutual_key"]} == {"Venus", "Mars"}
        )
        self.assertEqual(mutual["aspect"], "Conjunction")
        self.assertGreater(mutual["salience"], 0)
        self.assertEqual(len(mutual["directional_records"]), 2)
        self.assertTrue(
            all(record["record_type"] == "directional_aspect" for record in mutual["directional_records"])
        )

    def test_sidecar_distinguishes_live_withheld_and_unimplemented_layers(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0}, state=UNKNOWN_BIRTH_TIME),
            natal_payload({"Mars": 14.0}),
        )

        statuses = pair["sidecar"]["computation_status"]
        self.assertEqual(statuses["directional_aspects"], "implemented_verified")
        self.assertEqual(statuses["relationship_timing"], "not_implemented")
        self.assertGreater(pair["sidecar"]["withheld_summary"]["total"], 0)
        self.assertFalse(pair["sidecar"]["claim_safety"]["client_report_available"])

    def test_composite_aspects_compute_from_non_ambiguous_midpoints(self):
        pair = build_pair_payload(
            natal_payload({"Sun": 359.0, "Moon": 120.0}),
            natal_payload({"Sun": 1.0, "Moon": 120.0}),
        )

        composite = pair["computations"]["composite"]
        self.assertEqual(composite["status"]["composite_aspects"], "implemented_verified")
        self.assertTrue(
            any(
                aspect["body_1"] == "Sun"
                and aspect["body_2"] == "Moon"
                and aspect["aspect"] == "Trine"
                for aspect in composite["aspects"]
            )
        )
        self.assertEqual(pair["sidecar"]["computation_status"]["composite_aspects"], "implemented_verified")

    def test_repeated_natal_themes_detect_shared_sign_and_aspect_family(self):
        person_a = natal_payload(
            {"Sun": 1.0, "Moon": 2.0, "Venus": 45.0, "Saturn": 135.0}
        )
        person_b = natal_payload(
            {"Sun": 3.0, "Moon": 4.0, "Venus": 75.0, "Saturn": 165.0}
        )
        repeated_aspect = {
            "body_1": "Venus",
            "body_2": "Saturn",
            "aspect": "Square",
            "orb": 0.0,
            "angle": 90.0,
        }
        person_a["aspects"] = [repeated_aspect]
        person_b["aspects"] = [repeated_aspect]

        pair = build_pair_payload(person_a, person_b)
        themes = pair["computations"]["repeated_natal_themes"]
        theme_keys = {theme["theme_key"] for theme in themes}

        self.assertIn("shared_aries_emphasis", theme_keys)
        self.assertIn("shared_saturn_venus_square", theme_keys)
        self.assertTrue(all(theme["record_type"] == "repeated_theme" for theme in themes))
        self.assertEqual(pair["sidecar"]["computation_status"]["repeated_natal_themes"], "implemented_verified")

    def test_topic_signatures_and_convergence_are_traceable_not_verdicts(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0, "Mercury": 65.0}, ascendant=0.0),
            natal_payload({"Mars": 14.0, "Saturn": 190.0}, ascendant=0.0),
        )

        signatures = pair["computations"]["relationship_topic_signatures"]
        signature_keys = {signature["signature_key"] for signature in signatures}
        convergence = pair["computations"]["relationship_convergence"]

        self.assertIn("affection_value_attraction", signature_keys)
        self.assertIn("desire_friction_action", signature_keys)
        self.assertIn("communication", signature_keys)
        self.assertTrue(convergence)
        self.assertIn("trace", convergence[0])
        self.assertTrue(convergence[0]["independent_evidence_families"])
        self.assertEqual(
            pair["sidecar"]["computation_status"]["relationship_convergence"],
            "implemented_verified",
        )
        self.assertFalse(pair["sidecar"]["claim_safety"]["relationship_verdicts_supported"])

    def test_optional_chiron_requires_both_payloads(self):
        pair = build_pair_payload(
            natal_payload({"Sun": 10.0, "Chiron": 45.0}),
            natal_payload({"Moon": 130.0}),
        )

        all_bodies = {
            record["source_body"]
            for record in pair["computations"]["directional_aspects"]
        } | {
            record["target_body"]
            for record in pair["computations"]["directional_aspects"]
        }
        composite_bodies = {
            record["body"]
            for record in pair["computations"]["composite"]["bodies"]
        }

        self.assertNotIn("Chiron", all_bodies)
        self.assertNotIn("Chiron", composite_bodies)

    def test_malformed_longitude_is_skipped_without_blocking_pair_payload(self):
        person_a = natal_payload({"Venus": 10.0, "Mars": 12.0})
        person_b = natal_payload({"Mars": 14.0})
        person_a["standard_planets"]["Venus"]["longitude"] = "not-a-number"

        pair = build_pair_payload(person_a, person_b)
        live_contacts = [
            item
            for item in pair["computations"]["directional_aspects"]
            if not item.get("withheld")
        ]

        self.assertEqual(pair["schema_version"], SCHEMA_VERSION)
        self.assertFalse(
            any(
                item["source_body"] == "Venus" or item["target_body"] == "Venus"
                for item in live_contacts
            )
        )

    def test_house_overlay_falls_back_to_ascendant_sign_when_house_payload_missing_sign(self):
        person_a = natal_payload({"Moon": 102.0}, ascendant=0.0)
        person_b = natal_payload({"Sun": 15.0}, ascendant=90.0)
        person_b["houses"] = {}

        pair = build_pair_payload(person_a, person_b)
        overlay = next(
            item
            for item in pair["computations"]["house_overlays"]
            if item["source_person"] == "A"
            and item["target_person"] == "B"
            and item["source_body"] == "Moon"
        )

        self.assertFalse(overlay["withheld"])
        self.assertEqual(overlay["target_house"], 1)
        self.assertEqual(overlay["target_house_sign"], "Cancer")

    def test_missing_ascendant_with_exact_state_withholds_overlay_as_payload_field_gap(self):
        person_a = natal_payload({"Moon": 102.0}, ascendant=0.0)
        person_b = natal_payload({"Sun": 15.0}, ascendant=90.0)
        del person_b["angles"]["Ascendant"]

        pair = build_pair_payload(person_a, person_b)
        self.assertTrue(
            any(
                item["source_person"] == "A"
                and item["target_person"] == "B"
                and item["withheld"]
                and item["withheld_reason"] == "withheld_missing_payload_field"
                for item in pair["computations"]["house_overlays"]
            )
        )

    def test_approximate_birth_time_keeps_angle_and_house_layers_eligible(self):
        pair = build_pair_payload(
            natal_payload({"Venus": 10.0}, ascendant=0.0, state=APPROXIMATE_BIRTH_TIME),
            natal_payload({"Mars": 2.0}, ascendant=10.0),
        )

        self.assertTrue(pair["person_a"]["angle_eligible"])
        self.assertTrue(
            any(
                item["source_person"] == "B"
                and item["target_person"] == "A"
                and not item["withheld"]
                for item in pair["computations"]["house_overlays"]
            )
        )
        self.assertTrue(
            any(
                item["target_person"] == "A"
                and item["target_body"] == "Ascendant"
                and not item["withheld"]
                for item in pair["computations"]["directional_aspects"]
            )
        )

    def test_topic_signatures_cover_moon_fourth_saturn_and_pluto_eighth_families(self):
        pair = build_pair_payload(
            natal_payload({"Moon": 90.0, "Saturn": 40.0, "Pluto": 210.0}, ascendant=0.0),
            natal_payload({"Moon": 94.0, "Venus": 40.0, "Mars": 210.0, "Jupiter": 94.0}, ascendant=90.0),
        )

        signatures = {
            signature["signature_key"]: signature
            for signature in pair["computations"]["relationship_topic_signatures"]
        }

        self.assertIn("attachment_emotional_rhythm", signatures)
        self.assertIn("commitment_constraint_time", signatures)
        self.assertIn("intensity_merging_shared_resources", signatures)
        self.assertIn(
            "fourth_house_overlay",
            signatures["attachment_emotional_rhythm"]["independent_evidence_families"],
        )
        self.assertIn(
            "saturn_contacts",
            signatures["commitment_constraint_time"]["independent_evidence_families"],
        )
        self.assertIn(
            "eighth_house_overlay",
            signatures["intensity_merging_shared_resources"]["independent_evidence_families"],
        )


if __name__ == "__main__":
    unittest.main()
