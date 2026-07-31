"""Legacy test compatibility wrapper for formulas.standard.planetary_condition."""

from formulas.standard.planetary_condition import (  # noqa: F401
    STATION_THRESHOLDS,
    _classify_condition,
    _is_stationary,
    evaluate_all_planetary_conditions,
)

__all__ = [
    "STATION_THRESHOLDS",
    "_classify_condition",
    "_is_stationary",
    "evaluate_all_planetary_conditions",
]
