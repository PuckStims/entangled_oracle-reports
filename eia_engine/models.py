"""Dataclass models for structured EIA output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from eia_engine.schema import REPORT_TYPE, SCHEMA_VERSION, REGISTERS, validate_public_text, validate_register_name, validate_score


@dataclass(frozen=True)
class EIASourceEvidence:
    source_layer: str
    signal: str
    weight: float

    def __post_init__(self) -> None:
        validate_score(self.weight)
        validate_public_text(asdict(self))


@dataclass(frozen=True)
class EIARegisterBlock:
    register: str
    dominant_mode: str
    secondary_mode: str | None
    score: float
    mechanism: str
    distortion: str
    restoration: str
    experiment: str
    source_evidence: list[EIASourceEvidence] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_register_name(self.register)
        validate_score(self.score)
        validate_public_text(asdict(self))


@dataclass(frozen=True)
class EIAPressurePattern:
    name: str
    trigger: str
    presentation: str
    what_it_distorts: str
    correction: str

    def __post_init__(self) -> None:
        validate_public_text(asdict(self))


@dataclass(frozen=True)
class EIAStateSnapshot:
    method: str | None
    seed_id: str
    active_register: str
    symbol: str
    state_message: str
    experiment: str

    def __post_init__(self) -> None:
        validate_register_name(self.active_register)
        validate_public_text(asdict(self))


@dataclass(frozen=True)
class EIAReport:
    client: dict[str, Any]
    method: dict[str, Any]
    architecture_summary: dict[str, Any]
    registers: dict[str, EIARegisterBlock]
    pressure_patterns: list[EIAPressurePattern]
    technical_appendix: dict[str, Any]
    mythic_overlay_optional: dict[str, Any] | None = None
    state_snapshot_optional: EIAStateSnapshot | None = None
    advanced_layers_optional: dict[str, Any] | None = None
    schema_version: str = SCHEMA_VERSION
    report_type: str = REPORT_TYPE

    def __post_init__(self) -> None:
        missing = [register for register in REGISTERS if register not in self.registers]
        if missing:
            raise ValueError(f"EIA report is missing registers: {', '.join(missing)}")
        validate_public_text(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
