from eia_engine.models import EIARegisterBlock
from eia_engine.report_builder import build_eia_report, _pressure_pattern_for
from eia_engine.schema import REGISTERS, validate_report_dict


def sample_natal_chart():
    return {
        "client": {
            "name": "EIA Fixture",
            "birth_datetime": "1992-03-21T08:11:00-06:00",
            "birth_location": "Peoria, IL",
            "birth_time_confidence": "exact",
        },
        "standard_planets": {
            "Sun": {"sign": "Aries", "degree": 1.2, "house": 1},
            "Moon": {"sign": "Cancer", "degree": 12.5, "house": 4},
            "Mercury": {"sign": "Pisces", "degree": 28.0, "house": 12},
            "Venus": {"sign": "Taurus", "degree": 6.4, "house": 2},
            "Mars": {"sign": "Leo", "degree": 17.9, "house": 5},
            "Jupiter": {"sign": "Libra", "degree": 21.0, "house": 7},
            "Saturn": {"sign": "Aquarius", "degree": 14.0, "house": 11},
            "Uranus": {"sign": "Capricorn", "degree": 18.0, "house": 10},
            "Neptune": {"sign": "Capricorn", "degree": 19.0, "house": 10},
            "Pluto": {"sign": "Scorpio", "degree": 22.0, "house": 8},
        },
        "angles": {"Ascendant": {"sign": "Aries", "house": 1}, "Midheaven": {"sign": "Capricorn", "house": 10}},
        "aspects": [{"body1": "Mars", "body2": "Uranus", "aspect": "trine"}],
        "birth_time_confidence": "exact",
    }


def test_build_eia_report_returns_all_registers_and_valid_schema():
    report = build_eia_report(
        sample_natal_chart(),
        eas_indexes={"dominant_current": "Catalyst Index", "expression": "Narrative translation"},
        state_overlay={
            "method": "tarot_entropy",
            "seed_id": "fixture-seed",
            "active_register": "decision",
            "symbol": "Temperance",
            "state_message": "Current state asks for pacing.",
            "experiment": "Wait one sleep cycle.",
            "mode_hints": ["Tidal Knowing"],
        },
    )
    payload = report.to_dict()

    validate_report_dict(payload)
    assert set(payload["registers"]) == set(REGISTERS)
    assert payload["state_snapshot_optional"]["active_register"] == "decision"
    assert payload["mythic_overlay_optional"]["eas_current"] == "Catalyst Index"


def test_report_output_avoids_public_human_design_terms():
    payload = build_eia_report(sample_natal_chart()).to_dict()
    rendered = str(payload).lower()

    for term in ["bodygraph", "authority", "strategy", "profile", "incarnation cross"]:
        assert term not in rendered


def test_pressure_patterns_name_affected_register_instead_of_self_reference():
    cases = [
        (
            "ignition",
            "Quiet Accumulation",
            "Forced Emergence",
            "The ignition register: private preparation, timing, and the point at which readiness becomes visible.",
        ),
        (
            "current",
            "Pulse Current",
            "Surge Burn",
            "The current register: energy pacing, recovery, and the difference between a true surge and a sustainable rhythm.",
        ),
        (
            "decision",
            "Immediate Knowing",
            "False Certainty",
            "The decision register: first knowing, context checking, and the space between recognition and commitment.",
        ),
    ]

    for register, mode, pattern_name, expected in cases:
        pattern = _pressure_pattern_for(
            EIARegisterBlock(
                register=register,
                dominant_mode=mode,
                secondary_mode=None,
                score=0.9,
                mechanism="Mechanism",
                distortion=pattern_name,
                restoration="Repair practice",
                experiment="Experiment",
            )
        )

        assert pattern.name == pattern_name
        assert pattern.what_it_distorts == expected
        assert pattern.what_it_distorts != pattern.name
