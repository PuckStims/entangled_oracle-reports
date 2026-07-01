"""
Registry metadata for standard astrology methods.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from formulas.standard.methodology_profiles import PROFILE_TROPICAL_WHOLE


class MethodRegistry:
    """Central registry for method lineage, requirements, and activation state."""

    CATEGORIES = ("core_standard", "established_niche", "eo_proprietary")
    _registry: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        method_id: str,
        category: str,
        lineage_tags: list[str],
        requires_exact_time: bool = True,
        *,
        required_data: list[str] | None = None,
        time_requirement: str | None = None,
        location_requirement: str | None = None,
        active: bool = True,
        formula_version: str = "1.0.0",
        limitations: list[str] | None = None,
        assumptions: list[str] | None = None,
        methodology_id: str = PROFILE_TROPICAL_WHOLE,
    ) -> None:
        """Registers method metadata with compatibility for older callers."""
        if category not in cls.CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Must be one of {cls.CATEGORIES}."
            )

        if not time_requirement:
            time_requirement = "exact_birth_time" if requires_exact_time else "birth_time_optional"
        if not location_requirement:
            location_requirement = "required"

        cls._registry[method_id] = {
            "method_id": method_id,
            "category": category,
            "lineage_tags": list(lineage_tags),
            "required_data": list(required_data or []),
            "requires_exact_time": bool(requires_exact_time),
            "time_requirement": time_requirement,
            "location_requirement": location_requirement,
            "is_active": bool(active),
            "formula_version": formula_version,
            "limitations": list(limitations or []),
            "assumptions": list(assumptions or []),
            "methodology_id": methodology_id,
        }

    @classmethod
    def get_method_info(cls, method_id: str) -> dict[str, Any]:
        """Returns a safe copy of registered metadata."""
        return deepcopy(cls._registry.get(method_id, {}))

    @classmethod
    def get_all_methods(cls, include_inactive: bool = True) -> dict[str, dict[str, Any]]:
        """Returns all registered methods keyed by method id."""
        if include_inactive:
            return {key: deepcopy(value) for key, value in cls._registry.items()}
        return {
            key: deepcopy(value)
            for key, value in cls._registry.items()
            if value.get("is_active")
        }

    @classmethod
    def set_active(cls, method_id: str, active: bool) -> None:
        """Toggles a method's active state."""
        if method_id in cls._registry:
            cls._registry[method_id]["is_active"] = bool(active)

    @classmethod
    def is_core_standard(cls, method_id: str) -> bool:
        """Returns True when a registered method is core standard."""
        return cls._registry.get(method_id, {}).get("category") == "core_standard"


MethodRegistry.register(
    method_id="sect_evaluation",
    category="core_standard",
    lineage_tags=["hellenistic", "traditional"],
    required_data=["angles", "standard_planets"],
    time_requirement="exact_birth_time_or_provisional",
)
MethodRegistry.register(
    method_id="essential_dignity_expanded",
    category="core_standard",
    lineage_tags=["traditional", "medieval", "renaissance"],
    requires_exact_time=False,
    required_data=["standard_planets"],
    time_requirement="birth_time_optional",
)
MethodRegistry.register(
    method_id="modern_dispositors",
    category="core_standard",
    lineage_tags=["modern_psychological"],
    required_data=["standard_planets", "houses"],
)
MethodRegistry.register(
    method_id="asteroid_goddesses",
    category="established_niche",
    lineage_tags=["modern", "feminist_astrology"],
    requires_exact_time=False,
    required_data=["custom_asteroids"],
    time_requirement="birth_time_optional",
)
