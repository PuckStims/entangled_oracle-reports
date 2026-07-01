"""
Shared result contracts for standard astrology modules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StandardFormulaResult:
    """Predictable, auditable output shape for report-facing standard modules."""

    id: str
    label: str
    method_status: str
    tradition_tags: list[str]
    score: float = 0.0
    raw_score: float = 0.0
    theoretical_max: float = 1.0
    tier: str = "BACKGROUND"
    visibility_state: str = "visible"
    classification: str = ""
    drivers: list[str] = field(default_factory=list)
    supporting_factors: list[str] = field(default_factory=list)
    challenging_factors: list[str] = field(default_factory=list)
    components: dict[str, Any] = field(default_factory=dict)
    missing_inputs: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    formula_version: str = "1.0.0"
    methodology_id: str = "tropical_whole"
    methodology_label: str = "Tropical zodiac + Whole Sign houses"
    zodiac: str = "Tropical"
    house_system: str = "Whole Sign"
    audit_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanetConditionRecord:
    """Unified per-body record shared across condition and prominence layers."""

    body: str
    overall_condition_score: float = 0.0
    prominence_score: float = 0.0
    condition_classification: str = "neutral"
    essential_dignity: dict[str, Any] = field(default_factory=dict)
    accidental_dignity: dict[str, Any] = field(default_factory=dict)
    sect_condition: dict[str, Any] = field(default_factory=dict)
    motion_condition: dict[str, Any] = field(default_factory=dict)
    angularity: str = "cadent"
    house_context: int = 0
    aspect_network: dict[str, Any] = field(default_factory=dict)
    rulership_context: dict[str, Any] = field(default_factory=dict)
    dispositor_context: dict[str, Any] = field(default_factory=dict)
    reception_context: dict[str, Any] = field(default_factory=dict)
    supporting_factors: list[str] = field(default_factory=list)
    pressure_factors: list[str] = field(default_factory=list)
    routing_tags: list[str] = field(default_factory=list)
    confidence: str = "exact"
    missing_inputs: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    formula_version: str = "1.0.0"
    methodology_id: str = "tropical_whole"
    methodology_label: str = "Tropical zodiac + Whole Sign houses"
    zodiac: str = "Tropical"
    house_system: str = "Whole Sign"
    audit_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
