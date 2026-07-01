"""
Controlled birth-time and angle-confidence states for standard calculations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


EXACT_BIRTH_TIME = "exact_birth_time"
APPROXIMATE_BIRTH_TIME = "approximate_birth_time"
UNKNOWN_BIRTH_TIME = "unknown_birth_time"
ANGLE_DEPENDENT_UNAVAILABLE = "angle_dependent_unavailable"
PROVISIONAL_NEAR_HORIZON = "provisional_near_horizon"

VALID_CONFIDENCE_STATES = {
    EXACT_BIRTH_TIME,
    APPROXIMATE_BIRTH_TIME,
    UNKNOWN_BIRTH_TIME,
    ANGLE_DEPENDENT_UNAVAILABLE,
    PROVISIONAL_NEAR_HORIZON,
}


@dataclass(frozen=True)
class ConfidenceAssessment:
    """Serializable confidence object for time-sensitive calculations."""

    state: str
    is_time_known: bool
    is_angle_eligible: bool
    is_provisional: bool = False
    missing_inputs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["missing_inputs"] = list(self.missing_inputs)
        data["assumptions"] = list(self.assumptions)
        return data


def validate_confidence_state(state: str) -> str:
    """Validates and returns a controlled confidence state."""
    if state not in VALID_CONFIDENCE_STATES:
        raise ValueError(f"Invalid confidence state '{state}'.")
    return state


def infer_birth_time_state(
    *,
    has_birth_time: bool,
    is_approximate: bool = False,
    near_horizon: bool = False,
) -> str:
    """Maps basic birth-time facts into the controlled state set."""
    if not has_birth_time:
        return UNKNOWN_BIRTH_TIME
    if near_horizon:
        return PROVISIONAL_NEAR_HORIZON
    if is_approximate:
        return APPROXIMATE_BIRTH_TIME
    return EXACT_BIRTH_TIME


def assess_birth_time_confidence(
    *,
    has_birth_time: bool,
    is_approximate: bool = False,
    near_horizon: bool = False,
) -> ConfidenceAssessment:
    """Returns a standard confidence assessment for time-dependent methods."""
    state = infer_birth_time_state(
        has_birth_time=has_birth_time,
        is_approximate=is_approximate,
        near_horizon=near_horizon,
    )

    if state == UNKNOWN_BIRTH_TIME:
        return ConfidenceAssessment(
            state=state,
            is_time_known=False,
            is_angle_eligible=False,
            missing_inputs=("birth_time",),
        )

    if state == PROVISIONAL_NEAR_HORIZON:
        return ConfidenceAssessment(
            state=state,
            is_time_known=True,
            is_angle_eligible=True,
            is_provisional=True,
            assumptions=("birth_time_near_horizon",),
        )

    return ConfidenceAssessment(
        state=state,
        is_time_known=True,
        is_angle_eligible=True,
        is_provisional=(state == APPROXIMATE_BIRTH_TIME),
    )


def get_angle_unavailable_confidence(*missing_inputs: str) -> ConfidenceAssessment:
    """Returns the shared unavailable state for angle-dependent methods."""
    return ConfidenceAssessment(
        state=ANGLE_DEPENDENT_UNAVAILABLE,
        is_time_known=False,
        is_angle_eligible=False,
        missing_inputs=tuple(missing_inputs) or ("birth_time",),
    )
