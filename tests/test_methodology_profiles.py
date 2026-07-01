import unittest

from formulas.standard.methodology_profiles import (
    PROFILE_TROPICAL_WHOLE,
    get_active_methodology_metadata,
    list_methodology_profiles,
    validate_profile_id,
    validate_profile_payload,
)


class MethodologyProfilesTests(unittest.TestCase):
    def test_methodology_profiles_include_expected_ids(self):
        profile_ids = [profile.id for profile in list_methodology_profiles()]
        self.assertEqual(profile_ids, [PROFILE_TROPICAL_WHOLE])

    def test_profile_payload_defaults_to_tropical_whole(self):
        payload = validate_profile_payload({})
        self.assertEqual(payload["id"], PROFILE_TROPICAL_WHOLE)

    def test_nonproduction_profile_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_profile_id("sidereal_placidus")

    def test_active_methodology_metadata_matches_foundation(self):
        metadata = get_active_methodology_metadata()
        self.assertEqual(metadata["id"], PROFILE_TROPICAL_WHOLE)
        self.assertEqual(metadata["zodiac"], "Tropical")
        self.assertEqual(metadata["house_system"], "Whole Sign")
        self.assertEqual(
            metadata["label"],
            "Tropical zodiac + Whole Sign houses",
        )


if __name__ == "__main__":
    unittest.main()
