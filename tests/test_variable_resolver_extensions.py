import os
import sys
import unittest
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import generate
from selectors.variable_resolver import resolve_all


def _palette_stub():
    return {
        "bg": "#111111",
        "surface": "#1a1a1a",
        "surface_2": "#222222",
        "border": "#444444",
        "text": "#f3f3f3",
        "muted": "#bbbbbb",
        "subtle": "#999999",
        "identity": "#d6a756",
        "growth": "#8bc28b",
        "relationships": "#cf8bb7",
        "creativity": "#9b8cff",
        "vocation": "#66b6d9",
        "home": "#d98d66",
        "spiritual": "#86b6a0",
        "accent": "#9b8cff",
        "purple": "#9b8cff",
        "gold": "#d6a756",
        "rose": "#cf8bb7",
        "ember": "#d98d66",
        "blue": "#66b6d9",
    }


def _payload_stub():
    return {
        "simple_mode": True,
        "user_profile": {"house_system": "Whole Sign"},
        "standard_planets": {
            "Sun": {"sign": "Aries", "house": 1, "degree_decimal": 10.0, "longitude": 10.0},
            "Moon": {"sign": "Leo", "house": 5, "degree_decimal": 20.0, "longitude": 140.0},
            "Mercury": {"sign": "Aries", "house": 1, "degree_decimal": 11.0, "longitude": 11.0},
            "Venus": {"sign": "Taurus", "house": 2, "degree_decimal": 5.0, "longitude": 35.0},
            "Mars": {"sign": "Gemini", "house": 3, "degree_decimal": 15.0, "longitude": 75.0},
            "Jupiter": {"sign": "Cancer", "house": 4, "degree_decimal": 4.0, "longitude": 94.0},
            "Saturn": {"sign": "Aquarius", "house": 11, "degree_decimal": 18.0, "longitude": 318.0},
            "Uranus": {"sign": "Capricorn", "house": 10, "degree_decimal": 7.0, "longitude": 277.0},
            "Neptune": {"sign": "Capricorn", "house": 10, "degree_decimal": 8.0, "longitude": 278.0},
            "Pluto": {"sign": "Scorpio", "house": 8, "degree_decimal": 12.0, "longitude": 222.0},
            "Chiron": {"sign": "Virgo", "house": 6, "degree_decimal": 9.0, "longitude": 159.0},
            "North_Node": {"sign": "Sagittarius", "house": 9, "degree_decimal": 13.0, "longitude": 253.0},
            "South_Node": {"sign": "Gemini", "house": 3, "degree_decimal": 13.0, "longitude": 73.0},
            "Lilith_BML": {"sign": "Capricorn", "house": 1, "degree_decimal": 2.0, "longitude": 272.0},
        },
        "angles": {
            "Ascendant": {"sign": "Aries", "degree_decimal": 0.0, "longitude": 0.0},
            "Midheaven": {"sign": "Capricorn", "degree_decimal": 0.0, "longitude": 270.0},
            "Descendant": {"sign": "Libra", "degree_decimal": 0.0, "longitude": 180.0},
            "Imum_Coeli": {"sign": "Cancer", "degree_decimal": 0.0, "longitude": 90.0},
            "Vertex": {"sign": "Scorpio", "degree_decimal": 0.0, "longitude": 210.0},
        },
        "aspects": [],
    }


def _result(
    *,
    score,
    activation_score,
    archetype,
    expression,
    driver_body,
    driver_modality="cardinal",
    activation="Embodied",
    components=None,
    extra=None,
):
    result = {
        "score": score,
        "activation_score": activation_score,
        "raw_score": activation_score,
        "tier": "PRESENT",
        "archetype": archetype,
        "expression": expression,
        "driver_body": driver_body,
        "driver_modality": driver_modality,
        "activation": activation,
        "suppressed": False,
        "subtle_signal": False,
        "display_full": True,
        "components": components or {},
    }
    if extra:
        result.update(extra)
    return result


class TestVariableResolverExtensions(unittest.TestCase):

    def test_resolve_all_exposes_component_flats_weights_and_ranked_eas_fields(self):
        index_results = {
            "NGE": _result(
                score=0.92,
                activation_score=9.2,
                archetype="The Epic",
                expression="Epic expression",
                driver_body="Apollo",
                components={
                    "apollo": 1.2,
                    "themis": 0.8,
                    "terpsichore": 0.8,
                    "sirene": 0.3,
                    "aphrodite": 0.1,
                },
                extra={
                    "genre": "The Epic",
                    "dominant_body": "Apollo",
                    "dominant_facet": "Solar Leadership",
                    "narrative_question": "What is the larger call here?",
                    "facets": {
                        "Apollo": {
                            "Solar Leadership": 1.2,
                            "Creative Risk": 0.7,
                        },
                        "Themis": {
                            "Civic Strategy": 0.8,
                            "Witness": 0.4,
                        },
                        "Terpsichore": {
                            "Performance": 0.8,
                        },
                        "Sirene": {
                            "Magnetic Test": 0.3,
                        },
                        "Aphrodite": {
                            "Embodiment": 0.1,
                        },
                    },
                },
            ),
            "KVQ": _result(
                score=0.81,
                activation_score=8.1,
                archetype="Vindicated Oracle",
                expression="KVQ expression",
                driver_body="Kassandra",
                components={
                    "kass_angle": 1.1,
                    "kass_merc_easy": 0.25,
                    "kass_uran_hard": 0.8,
                },
                extra={"clear_translator": True},
            ),
            "MKI": _result(
                score=0.73,
                activation_score=7.3,
                archetype="The Archivist",
                expression="MKI expression",
                driver_body="Mnemosyne",
                components={"mnemosyne": 0.7},
            ),
            "RWI": _result(
                score=0.52,
                activation_score=5.2,
                archetype="The World Weaver",
                expression="RWI expression",
                driver_body="Arachne",
                components={"arachne": 0.5},
            ),
            "DFIS": _result(
                score=0.61,
                activation_score=6.1,
                archetype="The Sovereign Queen",
                expression="DFIS expression",
                driver_body="Lilith_BML",
                components={"lilith": 0.55, "kaali": 0.2},
                extra={"lilith_source": "Lilith_BML"},
            ),
            "CATALYST": _result(
                score=0.41,
                activation_score=4.1,
                archetype="The Awakener",
                expression="Catalyst expression",
                driver_body="Uranus",
                components={"uranus": 0.4},
            ),
            "AHL": {
                "score": 0.24,
                "normalized_score": 2.4,
                "raw_score": 2.4,
                "activation_score": 2.4,
                "tier": "PRESENT",
                "fires": True,
                "suppressed": False,
                "subtle_signal": False,
                "display_full": True,
                "components": {"lineage": 2.4},
            },
            "MAGNETIC": {
                "score": 0.3,
                "tier": "SUBTLE",
                "archetype": "The Magnetic Field",
                "framing": "COMBINED",
                "deprecated": True,
                "successor": "NGE",
            },
        }

        variables = resolve_all(
            _payload_stub(),
            index_results,
            querent_name="Resolver Test",
            current_location="Chicago, IL",
        )

        self.assertEqual(variables["kvq_components"]["kass_angle"], 1.1)
        self.assertEqual(variables["kvq_kass_angle"], 1.1)
        self.assertEqual(variables["kvq_kass_uran_hard"], 0.8)
        self.assertEqual(variables["mki_mnemosyne"], 0.7)
        self.assertEqual(variables["dfis_lilith"], 0.55)
        self.assertEqual(variables["ahl_lineage"], 2.4)

        self.assertEqual(variables["nge_apollo_weight"], 1.2)
        self.assertEqual(variables["nge_themis_weight"], 0.8)
        self.assertEqual(variables["nge_terpsichore_weight"], 0.8)
        self.assertEqual(variables["nge_secondary_body"], "Themis")
        self.assertEqual(variables["nge_secondary_facet"], "Civic Strategy")

        self.assertTrue(variables["kvq_clear_translator"])
        self.assertEqual(variables["kvq_clear_translator_strength"], 0.25)
        self.assertEqual(variables["dfis_lilith_source"], "Lilith_BML")

        self.assertEqual(variables["secondary_eas_dimension"], "KVQ")
        self.assertEqual(
            variables["secondary_eas_dimension_name"],
            "Your Foresight Pattern",
        )
        self.assertEqual(variables["secondary_eas_dimension_score"], 0.81)
        self.assertEqual(
            variables["secondary_eas_dimension_archetype"],
            "Vindicated Oracle",
        )
        self.assertEqual(
            variables["secondary_eas_dimension_expression"],
            "KVQ expression",
        )
        self.assertEqual(variables["tertiary_eas_dimension"], "MKI")
        self.assertEqual(variables["tertiary_eas_dimension_score"], 0.73)

        self.assertIsInstance(variables["kvq_activation_score"], float)
        self.assertIsInstance(variables["ahl_activation_score"], float)

    def test_soul_ecosystem_kvq_routing_uses_flat_archetype_key_depth(self):
        captured = []

        def fake_select_block_traced(report_type, block_file, *keys, fallback=""):
            captured.append((report_type, block_file, keys))
            return ("stub text", list(keys), False)

        variables = {
            "simple_mode": True,
            "sun_moon_relationship": "flowing",
            "dominant_element": "fire",
            "south_node_sign": "Gemini",
            "south_node_house": 3,
            "saturn_sign": "Aquarius",
            "pluto_sign": "Scorpio",
            "planets_in_12th": [],
            "north_node_sign": "Sagittarius",
            "north_node_house": 9,
            "mc_sign": "Capricorn",
            "jupiter_sign": "Cancer",
            "sun_sign_element": "fire",
            "moon_sign_element": "fire",
            "sun_moon_aspect_character": "flowing",
            "chiron_house": 6,
            "north_node_element": "fire",
            "mc_element": "earth",
            "palette": "vibrant",
            "querent_name": "Routing Test",
            "soul_ecosystem_dominant_index": "KVQ",
        }
        index_results = {
            "KVQ": {
                "archetype": "Vindicated Oracle",
                "tier": "DOMINANT",
                "score": 0.8,
                "expression": "KVQ expression",
                "activation": "Sovereign",
                "driver_body": "Kassandra",
                "driver_modality": "cardinal",
                "components": {},
            },
            "AHL": {"fires": False},
        }

        with patch("selectors.block_selector.select_block_traced", side_effect=fake_select_block_traced):
            with patch("engine.chart_wheel.build_chart_wheel_data", return_value=None):
                with patch("engine.chart_wheel.render_natal_wheel_svg", return_value=""):
                    generate._build_soul_ecosystem_context(
                        variables,
                        index_results,
                        _payload_stub(),
                    )

        proprietary_calls = [
            call for call in captured
            if call[1] == "foresight_pattern"
        ]
        self.assertTrue(proprietary_calls, "Expected KVQ proprietary routing call")
        self.assertIn(
            ("soul_ecosystem", "foresight_pattern", ("vindicated_oracle",)),
            proprietary_calls,
        )

    def test_soul_ecosystem_context_tolerates_missing_optional_index_dicts(self):
        def fake_select_block_traced(report_type, block_file, *keys, fallback=""):
            return ("stub text", list(keys), False)

        variables = {
            "simple_mode": True,
            "sun_moon_relationship": "flowing",
            "dominant_element": "fire",
            "south_node_sign": "",
            "south_node_house": 0,
            "saturn_sign": "",
            "pluto_sign": "",
            "planets_in_12th": [],
            "north_node_sign": "",
            "north_node_house": 0,
            "mc_sign": "",
            "jupiter_sign": "",
            "sun_sign_element": "fallback",
            "moon_sign_element": "fallback",
            "sun_moon_aspect_character": "unaspected",
            "chiron_house": 0,
            "north_node_element": "fallback",
            "mc_element": "fallback",
            "palette": "vibrant",
            "querent_name": "Safety Test",
            "soul_ecosystem_dominant_index": "KVQ",
        }
        index_results = {
            "KVQ": None,
            "AHL": None,
        }

        with patch("selectors.block_selector.select_block_traced", side_effect=fake_select_block_traced):
            with patch("engine.chart_wheel.build_chart_wheel_data", return_value=None):
                with patch("engine.chart_wheel.render_natal_wheel_svg", return_value=""):
                    context = generate._build_soul_ecosystem_context(
                        variables,
                        index_results,
                        _payload_stub(),
                    )

        self.assertEqual(context["proprietary_section_title"], "Your Foresight Pattern")
        self.assertEqual(context["soul_ecosystem_eas_archetype"], "")
        self.assertEqual(context["soul_ecosystem_eas_components"], {})
        self.assertEqual(context["soul_ecosystem_eas_depth"]["available_slots"], ["dominant"])
        self.assertFalse(context["soul_ecosystem_eas_depth"]["secondary"]["available"])
        self.assertIsNone(context["ancestral_block"])

    def test_soul_ecosystem_depth_payload_exposes_ranked_metadata(self):
        variables = {
            "simple_mode": True,
            "sun_moon_relationship": "flowing",
            "dominant_element": "fire",
            "south_node_sign": "Gemini",
            "south_node_house": 3,
            "saturn_sign": "Aquarius",
            "pluto_sign": "Scorpio",
            "planets_in_12th": [],
            "north_node_sign": "Sagittarius",
            "north_node_house": 9,
            "mc_sign": "Capricorn",
            "jupiter_sign": "Cancer",
            "sun_sign_element": "fire",
            "moon_sign_element": "fire",
            "sun_moon_aspect_character": "flowing",
            "chiron_house": 6,
            "north_node_element": "fire",
            "mc_element": "earth",
            "palette": "vibrant",
            "querent_name": "Depth Test",
            "soul_ecosystem_dominant_index": "NGE",
            "secondary_eas_dimension": "KVQ",
            "secondary_eas_dimension_name": "Your Foresight Pattern",
            "secondary_eas_dimension_score": 0.81,
            "secondary_eas_dimension_archetype": "Vindicated Oracle",
            "secondary_eas_dimension_expression": "KVQ expression",
            "tertiary_eas_dimension": "MKI",
            "tertiary_eas_dimension_name": "Your Knowledge Legacy",
            "tertiary_eas_dimension_score": 0.73,
            "tertiary_eas_dimension_archetype": "The Archivist",
            "tertiary_eas_dimension_expression": "MKI expression",
            "nge_secondary_body": "Themis",
            "nge_secondary_facet": "Civic Strategy",
            "nge_activation_score": 9.2,
            "kvq_activation_score": 8.1,
            "mki_activation_score": 7.3,
        }
        index_results = {
            "NGE": _result(
                score=0.92,
                activation_score=9.2,
                archetype="The Epic",
                expression="Epic expression",
                driver_body="Apollo",
                components={"apollo": 1.2, "themis": 0.8},
                extra={
                    "activation": "Embodied",
                    "genre": "The Epic",
                    "dominant_facet": "Solar Leadership",
                    "narrative_question": "What is the larger call here?",
                },
            ),
            "KVQ": _result(
                score=0.81,
                activation_score=8.1,
                archetype="Vindicated Oracle",
                expression="KVQ expression",
                driver_body="Kassandra",
                components={"kass_angle": 1.1},
            ),
            "MKI": _result(
                score=0.73,
                activation_score=7.3,
                archetype="The Archivist",
                expression="MKI expression",
                driver_body="Mnemosyne",
                components={"mnemosyne": 0.7},
            ),
            "AHL": {"fires": False},
        }

        with patch("selectors.block_selector.select_block_traced", return_value=("stub text", [], False)):
            with patch("engine.chart_wheel.build_chart_wheel_data", return_value=None):
                with patch("engine.chart_wheel.render_natal_wheel_svg", return_value=""):
                    context = generate._build_soul_ecosystem_context(
                        variables,
                        index_results,
                        _payload_stub(),
                    )

        depth = context["soul_ecosystem_eas_depth"]
        self.assertEqual(depth["available_slots"], ["dominant", "secondary", "tertiary"])
        self.assertEqual(depth["dominant"]["index"], "NGE")
        self.assertEqual(depth["dominant"]["score"], 0.92)
        self.assertEqual(depth["dominant"]["activation_score"], 9.2)
        self.assertEqual(depth["dominant"]["nge"]["dominant_facet"], "Solar Leadership")
        self.assertEqual(depth["dominant"]["nge"]["secondary_body"], "Themis")
        self.assertEqual(depth["secondary"]["index"], "KVQ")
        self.assertEqual(depth["secondary"]["archetype"], "Vindicated Oracle")
        self.assertEqual(depth["tertiary"]["index"], "MKI")
        self.assertTrue(depth["has_optional_depth"])

    def test_year_ahead_curated_summaries_stay_reader_facing_and_small(self):
        curated = generate._build_year_ahead_curated_summaries(
            {
                "label": "Crescendo",
                "peak_month": "May 2026 - Peak",
                "quiet_month": "August 2026 - Quiet",
                "peak_season": "Building Season",
                "curve_note": "Momentum gathers before cresting midyear.",
                "confidence_note": "Built from the current report's existing month-level concentration values.",
            },
            {
                "highest_concentration_period": "May 2026 - Peak",
                "quietest_period": "August 2026 - Quiet",
                "long_cycle_emphasis": "Saturn carries the strongest long-range emphasis in this forecast.",
                "shape_explanation": "This label summarizes the year's existing month-by-month intensity pattern.",
            },
            [
                {
                    "title": "Opening Season",
                    "months_label": "Jan, Feb, Mar",
                    "summary": "A deliberate start with rising concentration.",
                    "peak_month": "March 2026",
                    "dominant_domains": "Identity, Work",
                    "unused": "ignored",
                }
            ],
            {
                "fields": [
                    {
                        "field_key": "identity",
                        "field_label": "Identity and Vitality",
                        "band_label": "Strong",
                        "signal_family_label": "Sustained cycle emphasis",
                        "summary_line": "Domains: Identity",
                        "normalized_score": 84,
                        "raw_score": 2.4,
                        "supporting_events": [{"title": "Saturn trine Sun"}, {"title": "Mars ingress"}],
                        "selected_block_key_path": ["identity", "strong", "sustained"],
                    },
                    {
                        "field_key": "work",
                        "field_label": "Work and Craft",
                        "band_label": "Moderate",
                        "signal_family_label": "Clustered pressure",
                        "summary_line": "Domains: Work",
                        "normalized_score": 62,
                        "raw_score": 1.8,
                        "supporting_events": [{"title": "Jupiter sextile MC"}],
                    },
                ]
            },
        )

        self.assertEqual(curated["forecast_shape"]["label"], "Crescendo")
        self.assertEqual(curated["orientation"]["long_cycle_emphasis"], "Saturn carries the strongest long-range emphasis in this forecast.")
        self.assertEqual(curated["seasonal_highlights"][0]["title"], "Opening Season")
        self.assertNotIn("unused", curated["seasonal_highlights"][0])
        self.assertEqual(curated["climate_highlights"][0]["field_key"], "identity")
        self.assertEqual(curated["climate_highlights"][0]["supporting_event_titles"], ["Saturn trine Sun", "Mars ingress"])
        self.assertNotIn("selected_block_key_path", curated["climate_highlights"][0])

    def test_soul_ecosystem_template_renders_clear_translator_hook_safely(self):
        html = generate.render_template(
            "soul_ecosystem",
            {
                "palette": _palette_stub(),
                "palette_name": "vibrant",
                "querent_name": "Template Test",
                "birth_date_display": "",
                "birth_time_display": "",
                "birth_location": "",
                "generation_date": "June 29, 2026",
                "birth_time_status": "unknown",
                "ecosystem_overview_block": "",
                "souls_story_block": "",
                "chart_wheel_svg": "",
                "core_pattern_title": "",
                "core_pattern_note": "",
                "growth_pattern_title": "",
                "growth_pattern_note": "",
                "world_pattern_title": "",
                "world_pattern_note": "",
                "core_nature_block": "",
                "sun_moon_integration_block": "",
                "core_identity_block": "",
                "hidden_resources_block": "",
                "twelfth_house_blocks": [],
                "ancestral_block": None,
                "ahl_fires": False,
                "saturn_block": "",
                "chiron_block": "",
                "growth_edge_block": "",
                "south_node_sign_block": "",
                "south_node_house_block": "",
                "inherited_pattern_block": "",
                "north_node_sign_block": "",
                "north_node_house_block": "",
                "jupiter_block": "",
                "meaning_direction_block": "",
                "midheaven_block": "Public direction text.",
                "pluto_generation_block": "",
                "proprietary_section_title": "Your Foresight Pattern",
                "proprietary_section_block": "Primary proprietary prose.",
                "world_interface_block": "",
                "living_integration_block": "",
                "souls_promise_block": "",
                "primary_archetype_name": "",
                "primary_archetype_block": "",
                "secondary_archetype_name": "",
                "secondary_archetype_block": "",
                "natal_index_data": "",
                "nge_apollo_weight": 0.0,
                "nge_themis_weight": 0.0,
                "nge_terpsichore_weight": 0.0,
                "nge_sirene_weight": 0.0,
                "nge_aphrodite_weight": 0.0,
                "nge_dominant_body": "",
                "nge_secondary_body": "",
                "nge_dominant_facet": "",
                "nge_secondary_facet": "",
                "dominant_eas_dimension": "KVQ",
                "secondary_eas_dimension": "",
                "kvq_activation_score": 8.1,
                "mki_activation_score": 0.0,
                "rwi_activation_score": 0.0,
                "dfis_activation_score": 0.0,
                "nge_activation_score": 0.0,
                "catalyst_activation_score": 0.0,
                "kvq_tier": "present",
                "mki_tier": "",
                "rwi_tier": "",
                "dfis_tier": "",
                "nge_tier": "",
                "catalyst_tier": "",
                "kvq_clear_translator": True,
                "kvq_clear_translator_strength": 0.8,
                "soul_ecosystem_eas_depth": {
                    "available_slots": ["dominant"],
                    "dominant": {
                        "available": True,
                        "index": "KVQ",
                        "title": "Your Foresight Pattern",
                        "archetype": "Vindicated Oracle",
                        "expression": "KVQ expression",
                        "activation": "Embodied",
                        "score": 0.81,
                        "activation_score": 8.1,
                        "driver": {"body": "Kassandra", "modality": "cardinal"},
                        "nge": {"dominant_facet": "", "narrative_question": ""},
                    },
                    "secondary": {"available": False},
                    "tertiary": {"available": False},
                },
            },
        )

        self.assertIn("Pattern Depth", html)
        self.assertIn("translate complexity into usable language", html)
        self.assertNotIn("Representative cycles</span><strong></strong>", html)

    def test_year_ahead_template_renders_curated_summaries_without_internal_keys(self):
        html = generate.render_template(
            "year_ahead",
            {
                "palette": _palette_stub(),
                "palette_name": "vibrant",
                "querent_name": "Template Test",
                "birth_date_display": "",
                "birth_time_display": "",
                "birth_location": "",
                "generation_date": "June 29, 2026",
                "year_overview_block": "Orientation prose.",
                "forecast_shape": "Crescendo",
                "forecast_shape_details": {
                    "label": "Crescendo",
                    "short_explanation": "Shape summary.",
                    "distribution_note": "Momentum gathers before cresting midyear.",
                    "curve_note": "Momentum gathers before cresting midyear.",
                    "legend_label": "Relative month concentration",
                    "peak_month": "May 2026 - Peak",
                    "quiet_month": "August 2026 - Quiet",
                    "peak_season": "Building Season",
                    "confidence_note": "Built from existing month-level concentration values.",
                    "months": [],
                },
                "show_forecast_shape_visuals": False,
                "orientation_summary": {
                    "long_cycle_emphasis": "Saturn carries the strongest long-range emphasis in this forecast.",
                    "long_cycle_explanation": "Long-cycle explanation.",
                    "highest_concentration_period": "May 2026 - Peak",
                    "highest_concentration_explanation": "Highest concentration explanation.",
                    "quietest_period": "August 2026 - Quiet",
                    "quietest_period_explanation": "Quiet explanation.",
                    "strongest_annual_themes": [],
                    "themes_explanation": "Theme explanation.",
                },
                "year_ahead_curated_summaries": {
                    "forecast_shape": {
                        "label": "Crescendo",
                        "curve_note": "Momentum gathers before cresting midyear.",
                    },
                    "orientation": {
                        "long_cycle_emphasis": "Saturn carries the strongest long-range emphasis in this forecast.",
                        "highest_concentration_period": "May 2026 - Peak",
                        "quietest_period": "August 2026 - Quiet",
                    },
                    "seasonal_highlights": [
                        {
                            "title": "Opening Season",
                            "months_label": "Jan, Feb, Mar",
                            "summary": "A deliberate start with rising concentration.",
                            "peak_month": "March 2026",
                            "dominant_domains": "Identity, Work",
                        }
                    ],
                    "climate_highlights": [
                        {
                            "field_label": "Identity and Vitality",
                            "band_label": "Strong",
                            "summary_line": "Domains: Identity",
                            "signal_family_label": "Sustained cycle emphasis",
                            "supporting_event_titles": ["Saturn trine Sun", "Mars ingress"],
                        }
                    ],
                },
                "forecast_climate": {
                    "prominence_note": "Climate intro.",
                    "certainty_note": "Certainty note.",
                    "confidence_note": "",
                    "fields": [],
                },
                "archetypal_opening_section": None,
                "landmarks": [],
                "months": [],
                "chart_characteristics": {},
                "natal_positions": [],
                "house_system": "Whole Sign",
                "timeline_start": "",
                "timeline_end": "",
                "timeline_event_count": 0,
                "turning_point_timeline": [],
                "year_integration_block": "",
                "year_integration_theme": "",
                "dominant_slow_planet": "",
                "dominant_aspect_type": "",
                "dominant_aspect_character": "",
                "annual_arc": [],
                "year_arc_sort_basis": "ordinary_salience_duration_then_timing",
                "season_summaries": [],
                "raw_cycle_ledger": {},
                "calculation_record": {},
                "ledger_months": [],
                "active_transit_count": 0,
                "chart_wheel_data": None,
                "chart_wheel_svg": "",
                "birth_time_status": "unknown",
                "birth_time_confidence": "unknown",
                "predictive_results": {},
                "report_version": "Year Ahead v2.0",
                "show_landmark_visuals": False,
            },
        )

        self.assertIn("Seasonal Highlights", html)
        self.assertIn("Field Highlights", html)
        self.assertIn("Identity and Vitality", html)
        self.assertNotIn("field_key", html)
        self.assertEqual(html.count("Dominant long cycle"), 1)

    def test_year_ahead_template_omits_curated_summary_shell_when_empty(self):
        html = generate.render_template(
            "year_ahead",
            {
                "palette": _palette_stub(),
                "palette_name": "vibrant",
                "querent_name": "Template Test",
                "birth_date_display": "",
                "birth_time_display": "",
                "birth_location": "",
                "generation_date": "June 29, 2026",
                "year_overview_block": "Orientation prose.",
                "forecast_shape": "Still forming",
                "forecast_shape_details": {
                    "label": "Still forming",
                    "short_explanation": "Shape summary.",
                    "distribution_note": "No month-level concentration data is available yet.",
                    "curve_note": "No month-level concentration data is available yet.",
                    "legend_label": "Relative month concentration",
                    "peak_month": "",
                    "quiet_month": "",
                    "peak_season": "",
                    "confidence_note": "",
                    "months": [],
                },
                "show_forecast_shape_visuals": False,
                "orientation_summary": {
                    "long_cycle_emphasis": "No sustained long-cycle emphasis is available yet.",
                    "long_cycle_explanation": "Long-cycle explanation.",
                    "highest_concentration_period": "Still forming",
                    "highest_concentration_explanation": "Highest concentration explanation.",
                    "quietest_period": "Still forming",
                    "quietest_period_explanation": "Quiet explanation.",
                    "strongest_annual_themes": [],
                    "themes_explanation": "Theme explanation.",
                },
                "year_ahead_curated_summaries": {
                    "forecast_shape": {},
                    "orientation": {},
                    "seasonal_highlights": [],
                    "climate_highlights": [],
                },
                "forecast_climate": {
                    "prominence_note": "Climate intro.",
                    "certainty_note": "Certainty note.",
                    "confidence_note": "",
                    "fields": [],
                },
                "archetypal_opening_section": None,
                "landmarks": [],
                "months": [],
                "chart_characteristics": {},
                "natal_positions": [],
                "house_system": "Whole Sign",
                "timeline_start": "",
                "timeline_end": "",
                "timeline_event_count": 0,
                "turning_point_timeline": [],
                "year_integration_block": "",
                "year_integration_theme": "",
                "dominant_slow_planet": "",
                "dominant_aspect_type": "",
                "dominant_aspect_character": "",
                "annual_arc": [],
                "year_arc_sort_basis": "ordinary_salience_duration_then_timing",
                "season_summaries": [],
                "raw_cycle_ledger": {},
                "calculation_record": {},
                "ledger_months": [],
                "active_transit_count": 0,
                "chart_wheel_data": None,
                "chart_wheel_svg": "",
                "birth_time_status": "unknown",
                "birth_time_confidence": "unknown",
                "predictive_results": {},
                "report_version": "Year Ahead v2.0",
                "show_landmark_visuals": False,
            },
        )

        self.assertNotIn("Seasonal Highlights", html)
        self.assertNotIn("Field Highlights", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
