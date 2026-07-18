from engine.karmic_engine import build_karmic_payload
from formulas.standard.karmic import evaluate_karmic_formulas
from formulas.standard.method_registry import MethodRegistry


def _payload(simple_mode: bool = False) -> dict:
    state = "unknown_birth_time" if simple_mode else "exact_birth_time"
    return {
        "simple_mode": simple_mode,
        "user_profile": {
            "queried_location": "Spokane, Washington, United States",
            "resolved_location": "Spokane, Washington, United States",
            "timezone": "America/Los_Angeles",
            "utc_datetime": "1990-01-01T20:00:00+00:00",
            "julian_day": 2447893.3333333335,
            "house_system": "Whole Sign",
            "simple_mode": simple_mode,
            "birth_time_state": state,
            "birth_time_confidence": state,
            "methodology_id": "tropical_whole",
            "methodology_label": "Tropical zodiac + Whole Sign houses",
            "zodiac": "Tropical",
        },
        "houses": {
            "House_12": {"sign": "Leo", "longitude": 120.0},
        },
        "standard_planets": {
            "Sun": {
                "longitude": 281.0,
                "sign": "Capricorn",
                "house": 6,
                "speed": 1.0,
                "retrograde": False,
            },
            "Moon": {
                "longitude": 15.0,
                "sign": "Aries",
                "house": 9,
                "speed": 12.0,
                "retrograde": False,
            },
            "Mercury": {
                "longitude": 290.0,
                "sign": "Capricorn",
                "house": 6,
                "speed": -0.8,
                "retrograde": True,
            },
            "Venus": {
                "longitude": 305.0,
                "sign": "Aquarius",
                "house": 7,
                "speed": 1.2,
                "retrograde": False,
            },
            "Mars": {
                "longitude": 120.0,
                "sign": "Leo",
                "house": 12,
                "speed": 0.6,
                "retrograde": False,
            },
            "Jupiter": {
                "longitude": 95.0,
                "sign": "Cancer",
                "house": 11,
                "speed": -0.1,
                "retrograde": True,
            },
            "Saturn": {
                "longitude": 282.0,
                "sign": "Capricorn",
                "house": 6,
                "speed": 0.1,
                "retrograde": False,
            },
            "Uranus": {
                "longitude": 276.0,
                "sign": "Capricorn",
                "house": 6,
                "speed": 0.0,
                "retrograde": False,
            },
            "Neptune": {
                "longitude": 282.0,
                "sign": "Capricorn",
                "house": 6,
                "speed": 0.0,
                "retrograde": False,
            },
            "Pluto": {
                "longitude": 227.0,
                "sign": "Scorpio",
                "house": 4,
                "speed": 0.0,
                "retrograde": False,
            },
            "Chiron": {
                "longitude": 105.0,
                "sign": "Cancer",
                "house": 11,
                "speed": 0.0,
                "retrograde": False,
            },
            "North_Node": {
                "longitude": 20.0,
                "sign": "Aries",
                "house": 9,
                "speed": -0.05,
                "retrograde": True,
            },
            "South_Node": {
                "longitude": 200.0,
                "sign": "Libra",
                "house": 3,
                "speed": -0.05,
                "retrograde": True,
            },
            "Lilith_BML": {
                "longitude": 140.0,
                "sign": "Leo",
                "house": 12,
                "speed": 0.1,
                "retrograde": False,
            },
        },
        "custom_asteroids": {},
        "aspects": [
            {
                "body_1": "South_Node",
                "body_2": "Saturn",
                "aspect": "Square",
                "orb": 2.0,
                "angle": 82.0,
            },
            {
                "body_1": "North_Node",
                "body_2": "Moon",
                "aspect": "Conjunction",
                "orb": 5.0,
                "angle": 5.0,
            },
        ],
    }


def test_karmic_payload_contract_and_trace_shape():
    result = build_karmic_payload(_payload())

    assert result["schema_version"] == "karmic.v1"
    assert result["methodology"]["literal_past_life_claims"] is False
    assert result["input_confidence"]["birth_time_state"] == "exact_birth_time"
    assert result["audit"]["source"] == "engine.karmic_engine.build_karmic_payload"
    assert result["evidence_records"]
    assert all("audit_data" in record for record in result["evidence_records"])
    assert all("claim_level" in record for record in result["evidence_records"])
    assert "karmic_carryover_index" in result["scores"]
    assert result["scores"]["karmic_carryover_index"]["visibility_state"] == "internal_only"


def test_karmic_engine_extracts_core_evidence_families():
    result = build_karmic_payload(_payload())
    families = {record["family"] for record in result["evidence_records"]}

    assert "south_node_axis" in families
    assert "south_node_axis_ruler" in families
    assert "nodal_aspect" in families
    assert "twelfth_house" in families
    assert "twelfth_house_ruler" in families
    assert "saturn_sign" in families
    assert "pluto_sign" in families
    assert "retrograde" in families


def test_unknown_birth_time_withholds_house_sensitive_evidence():
    result = build_karmic_payload(_payload(simple_mode=True))
    house_records = [
        record
        for record in result["evidence_records"]
        if record["birth_time_sensitivity"] == "exact_time_required"
    ]

    assert result["input_confidence"]["birth_time_state"] == "unknown_birth_time"
    assert result["input_confidence"]["houses_angles_eligible"] is False
    assert house_records
    assert all(record["confidence"] == "withheld" for record in house_records)
    assert "birth_time" in result["missing_inputs"]
    assert "simple_mode_uses_noon_placeholder_for_planet_math_only" in result["assumptions"]


def test_karmic_scores_are_confidence_adjusted_not_factual_booleans():
    result = build_karmic_payload(_payload())

    assert "is_past_life" not in result["scores"]
    assert "karmic_debt" not in result["scores"]
    for score in result["scores"].values():
        if isinstance(score, dict) and "audit_data" in score:
            assert score["audit_data"]["literal_past_life_claim"] is False
            assert score["method_status"] == "backend_computation"
            assert "score_supports_ranking_not_truth_claim" in score["assumptions"]


def test_karmic_formula_layer_returns_standard_formula_results():
    payload = build_karmic_payload(_payload())
    result = evaluate_karmic_formulas(
        payload["evidence_records"],
        payload["input_confidence"]["birth_time_state"],
    )

    assert result["formula_version"] == "1.0.0"
    assert result["karmic_carryover_index"]["id"] == "karmic_carryover_index"
    assert result["hidden_memory_load"]["classification"] == "private_or_unconscious_carryover_density"
    assert result["nodal_entanglement_rating"]["theoretical_max"] == 1.0
    assert result["present_echo_resonance"]["zodiac"] == "Tropical"
    assert result["retrograde_unfinished_cluster"]["components"]["family_weights"] == {"retrograde": 1.0}


def test_karmic_formula_registry_metadata_is_available():
    info = MethodRegistry.get_method_info("karmic_carryover_index")

    assert info["method_id"] == "karmic_carryover_index"
    assert info["category"] == "core_standard"
    assert info["time_requirement"] == "birth_time_optional_with_house_gating"
    assert "symbolic_evidence_density_not_literal_past_life_proof" in info["assumptions"]
