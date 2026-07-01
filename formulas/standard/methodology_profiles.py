"""
Methodology profile definitions for the standard astrology foundation layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PROFILE_TROPICAL_WHOLE = "tropical_whole"
PROFILE_SIDEREAL_PLACIDUS = "sidereal_placidus"
PROFILE_SYNTHESIS = "synthesis"

VALID_PROFILE_IDS = (PROFILE_TROPICAL_WHOLE,)


@dataclass(frozen=True)
class MethodologyProfile:
    """Intentional zodiac-plus-house methodology, never a free mix-and-match."""

    id: str
    label: str
    zodiac: str
    house_system: str
    ayanamsa: str | None = None
    source_profile_ids: tuple[str, ...] = ()
    comparison_mode: bool = False
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_profile_ids"] = list(self.source_profile_ids)
        return data


METHODOLOGY_PROFILES: dict[str, MethodologyProfile] = {
    PROFILE_TROPICAL_WHOLE: MethodologyProfile(
        id=PROFILE_TROPICAL_WHOLE,
        label="Tropical zodiac + Whole Sign houses",
        zodiac="Tropical",
        house_system="Whole Sign",
        description="Tropical zodiac with Whole Sign houses.",
    ),
    PROFILE_SIDEREAL_PLACIDUS: MethodologyProfile(
        id=PROFILE_SIDEREAL_PLACIDUS,
        label="Sidereal / Placidus",
        zodiac="Sidereal",
        house_system="Placidus",
        ayanamsa="unconfigured",
        description="Sidereal zodiac with Placidus houses and one declared ayanamsa.",
    ),
    PROFILE_SYNTHESIS: MethodologyProfile(
        id=PROFILE_SYNTHESIS,
        label="Synthesis",
        zodiac="comparison",
        house_system="comparison",
        source_profile_ids=(
            PROFILE_TROPICAL_WHOLE,
            PROFILE_SIDEREAL_PLACIDUS,
        ),
        comparison_mode=True,
        description="Compare the two source layers without creating a hybrid chart.",
    ),
}

PRODUCTION_METHODOLOGY = METHODOLOGY_PROFILES[PROFILE_TROPICAL_WHOLE]


def get_methodology_profile(profile_id: str) -> MethodologyProfile:
    """Returns the declared methodology profile or raises for unknown ids."""
    try:
        return METHODOLOGY_PROFILES[profile_id]
    except KeyError as error:
        raise ValueError(f"Unknown methodology profile '{profile_id}'.") from error


def list_methodology_profiles() -> list[MethodologyProfile]:
    """Returns all methodology profiles in stable declaration order."""
    return [METHODOLOGY_PROFILES[profile_id] for profile_id in VALID_PROFILE_IDS]


def get_active_methodology_profile() -> MethodologyProfile:
    """Returns the single active production methodology profile."""
    return PRODUCTION_METHODOLOGY


def get_active_methodology_metadata() -> dict[str, Any]:
    """Returns the active production methodology as serializable metadata."""
    return get_active_methodology_profile().to_dict()


def validate_profile_id(profile_id: str) -> str:
    """Validates and returns a profile id."""
    if profile_id != PROFILE_TROPICAL_WHOLE:
        raise ValueError(
            f"Unsupported production methodology '{profile_id}'. "
            f"Only '{PROFILE_TROPICAL_WHOLE}' is currently active."
        )
    return PROFILE_TROPICAL_WHOLE


def validate_profile_payload(profile_payload: dict[str, Any] | None) -> dict[str, Any]:
    """
    Validates profile metadata carried in payloads or resolver contexts.

    Returns a normalized dictionary suitable for serialization.
    """
    profile_payload = profile_payload or {}
    profile_id = validate_profile_id(str(profile_payload.get("id", PROFILE_TROPICAL_WHOLE)))
    return get_active_methodology_profile().to_dict()
