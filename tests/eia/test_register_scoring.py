from eia_engine.feature_extraction import extract_astrology_features
from eia_engine.register_scoring import score_register_modes


def test_fire_cardinal_chart_scores_direct_spark_highest():
    features = extract_astrology_features(
        {
            "standard_planets": {
                "Sun": {"sign": "Aries", "house": 1},
                "Mars": {"sign": "Leo", "house": 5},
                "Moon": {"sign": "Cancer", "house": 4},
                "Mercury": {"sign": "Gemini", "house": 3},
                "Saturn": {"sign": "Capricorn", "house": 10},
            },
            "angles": {"Ascendant": {"sign": "Aries", "house": 1}},
            "aspects": [{"body1": "Mars", "body2": "Uranus", "aspect": "trine"}],
            "birth_time_confidence": "exact",
        }
    )

    scores = score_register_modes(
        "ignition",
        ["Direct Spark", "Responsive Pull", "Structured Commitment"],
        features,
    )

    assert scores["Direct Spark"] > scores["Responsive Pull"]
    assert scores["Direct Spark"] > 0.5


def test_unknown_birth_time_reduces_scores():
    exact = extract_astrology_features(
        {"standard_planets": {"Sun": {"sign": "Aries", "house": 1}}, "birth_time_confidence": "exact"}
    )
    unknown = extract_astrology_features(
        {"standard_planets": {"Sun": {"sign": "Aries", "house": 1}}, "birth_time_confidence": "unknown"}
    )

    exact_scores = score_register_modes("ignition", ["Direct Spark"], exact)
    unknown_scores = score_register_modes("ignition", ["Direct Spark"], unknown)

    assert unknown_scores["Direct Spark"] < exact_scores["Direct Spark"]
