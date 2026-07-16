"""
Central taxonomy for the Location Services locational grammar.

This file defines the shared constants used across the evidence resolver,
theme clusterer, goal profile, and report planner. This ensures that
contradiction pairs, compensatory themes, goal mappings, and banding
thresholds are centrally managed.
"""

# Theme categories and pairs for the Resolver
CONTRADICTION_PAIRS = [
    ({"public_role", "visibility", "career"}, {"home", "privacy", "retreat", "solitude"}),
    ({"independence", "autonomy", "disruption"}, {"commitment", "structure", "limits", "roots"}),
    ({"action", "stamina", "boundary"}, {"rest", "healing", "restoration", "surrender"}),
    ({"expansion", "growth", "opportunity"}, {"contraction", "maintenance", "consolidation"}),
]

COMPENSATORY_THEMES = {
    "structure", "containment", "restoration", "grounding", "boundary", "limits", "commitment"
}

# Required goal dimensions for Goal Compatibility Profile
GOAL_DIMENSIONS = [
    "career_visibility",
    "creative_production",
    "artistic_reception",
    "study_and_writing",
    "partnership",
    "friendship_and_community",
    "family_life",
    "domestic_restoration",
    "healing_and_recovery",
    "spiritual_retreat",
    "activism",
    "reinvention",
    "financial_consolidation",
    "long_term_settlement",
    "short_term_catalytic_visit",
    "solitude",
    "adventure_and_exploration",
]

# Mapping themes to goal relevance weights (opportunity mapping)
GOAL_THEME_MAPPING = {
    "career_visibility": ["public_role", "visibility", "career", "authority", "contribution"],
    "creative_production": ["creativity", "imagination", "authorship", "creative_visibility"],
    "artistic_reception": ["aesthetics", "audience", "public_reception"],
    "study_and_writing": ["language", "learning", "study", "teaching", "communication"],
    "partnership": ["partnership", "relationship", "collaboration", "mirroring"],
    "friendship_and_community": ["community", "audience", "future_plans"],
    "family_life": ["home", "family_pattern_activation", "roots", "care"],
    "domestic_restoration": ["home", "rest", "privacy", "emotional_recovery"],
    "healing_and_recovery": ["healing", "wound_work", "restoration", "rest"],
    "spiritual_retreat": ["solitude", "retreat", "hidden_patterns", "surrender"],
    "activism": ["action", "purpose", "boundary", "community"],
    "reinvention": ["transformation", "deep_change", "disruption", "independence"],
    "financial_consolidation": ["resources", "value", "structure", "maintenance"],
    "long_term_settlement": ["roots", "commitment", "structure", "home"],
    "short_term_catalytic_visit": ["action", "disruption", "adventure_and_exploration", "opportunity"],
    "solitude": ["privacy", "solitude", "retreat", "enclosure"],
    "adventure_and_exploration": ["travel", "worldview", "experimentation", "growth"],
}

# Band Thresholds for the Theme Clusterer
STRENGTH_THRESHOLDS = {
    "defining": 0.85,
    "strong": 0.65,
    "supportive": 0.40,
    "background": 0.15,
}

CONFIDENCE_THRESHOLDS = {
    "high": 0.85,
    "medium": 0.60,
    "low": 0.30,
}
