"""Shared constants and validation helpers for EIA."""

from __future__ import annotations

SCHEMA_VERSION = "0.1"
REPORT_TYPE = "internal_architecture"

REGISTERS = (
    "ignition",
    "reception",
    "decision",
    "current",
    "boundary",
    "contact",
    "restoration",
)

BASELINE_WEIGHTS = {
    "natal_signature": 0.55,
    "eas_resonance": 0.20,
    "polarity_current": 0.15,
    "biophysical_metaphor": 0.10,
    "state_overlay": 0.00,
    "client_calibration": 0.00,
}

CONFIDENCE_MODIFIERS = {
    "exact": 1.00,
    "approximate": 0.85,
    "unknown": 0.65,
}

PUBLIC_FIELD_BANNED_TERMS = (
    "BodyGraph",
    "Type",
    "Strategy",
    "Authority",
    "Profile",
    "Centers",
    "Gates",
    "Channels",
    "Incarnation Cross",
    "Rave",
    "not-self",
)


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def validate_register_name(register: str) -> None:
    if register not in REGISTERS:
        raise ValueError(f"Unknown EIA register: {register}")


def validate_score(score: float) -> None:
    if score < 0.0 or score > 1.0:
        raise ValueError(f"EIA score must be between 0.0 and 1.0, got {score}")


def validate_public_text(value: object) -> None:
    if value is None:
        return
    if isinstance(value, dict):
        for item in value.values():
            validate_public_text(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            validate_public_text(item)
        return
    if not isinstance(value, str):
        return
    lower_value = value.lower()
    for term in PUBLIC_FIELD_BANNED_TERMS:
        if term.lower() in lower_value:
            raise ValueError(f"EIA public output contains avoided terminology: {term}")


def validate_report_dict(report: dict) -> None:
    if report.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unexpected EIA schema version")
    if report.get("report_type") != REPORT_TYPE:
        raise ValueError("Unexpected EIA report type")
    registers = report.get("registers", {})
    missing = [register for register in REGISTERS if register not in registers]
    if missing:
        raise ValueError(f"EIA report is missing registers: {', '.join(missing)}")
    for register, block in registers.items():
        validate_register_name(register)
        validate_score(float(block.get("score", -1.0)))
    validate_public_text(report)
