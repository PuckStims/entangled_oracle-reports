"""Legacy test compatibility wrapper for formulas.standard.angularity."""

from formulas.standard.angularity import HOUSE_TYPES, evaluate_angularity
from formulas.standard.normalization import ANGLE_ALIAS_MAP, CANONICAL_ANGLE_NAMES


CANONICAL_ANGLES = tuple(CANONICAL_ANGLE_NAMES)
ANGLE_ALIASES = dict(ANGLE_ALIAS_MAP)

__all__ = [
    "ANGLE_ALIASES",
    "CANONICAL_ANGLES",
    "HOUSE_TYPES",
    "evaluate_angularity",
]
