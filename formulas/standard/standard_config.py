"""
Configuration constants for the standard astrology foundation layer.
"""

from __future__ import annotations

from formulas.standard.confidence import VALID_CONFIDENCE_STATES
from formulas.standard.methodology_profiles import (
    PROFILE_TROPICAL_WHOLE,
    VALID_PROFILE_IDS,
    get_active_methodology_metadata,
)

AUTHORITATIVE_STANDARD_PACKAGE = "formulas.standard"
ACTIVE_METHODOLOGY = get_active_methodology_metadata()
PRODUCTION_METHODOLOGY_ID = PROFILE_TROPICAL_WHOLE
PRODUCTION_METHODOLOGY_LABEL = ACTIVE_METHODOLOGY["label"]
PRODUCTION_ZODIAC = ACTIVE_METHODOLOGY["zodiac"]
PRODUCTION_HOUSE_SYSTEM = ACTIVE_METHODOLOGY["house_system"]

SUPPORTED_ZODIACS = [PRODUCTION_ZODIAC]
SUPPORTED_HOUSE_SYSTEMS = [PRODUCTION_HOUSE_SYSTEM]
SUPPORTED_METHODOLOGY_PROFILES = list(VALID_PROFILE_IDS)
SUPPORTED_CONFIDENCE_STATES = sorted(VALID_CONFIDENCE_STATES)

DIGNITY_LAYERS = {
    "domicile": {"weight": 5.0, "type": "major_strength"},
    "exaltation": {"weight": 4.0, "type": "major_strength"},
    "triplicity": {"weight": 3.0, "type": "moderate_strength"},
    "term_bound": {"weight": 2.0, "type": "minor_strength"},
    "face_decan": {"weight": 1.0, "type": "minor_strength"},
    "detriment": {"weight": -5.0, "type": "major_debility"},
    "fall": {"weight": -4.0, "type": "major_debility"},
    "peregrine": {"weight": -1.0, "type": "wandering"},
}

MODERN_RULERSHIPS = {
    "Uranus": "Aquarius",
    "Neptune": "Pisces",
    "Pluto": "Scorpio",
}

PROMINENCE_TIERS = {
    "DOMINANT": 0.85,
    "PROMINENT": 0.65,
    "PRESENT": 0.35,
    "BACKGROUND": 0.0,
}

ANGULARITY_WEIGHTS = {
    "angular": {"houses": [1, 4, 7, 10], "multiplier": 1.5},
    "succedent": {"houses": [2, 5, 8, 11], "multiplier": 1.0},
    "cadent": {"houses": [3, 6, 9, 12], "multiplier": 0.5},
}
