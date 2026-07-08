"""
engine/lots.py - Phase 6 Lots (Fortune, Spirit, Necessity).

Lots are calculated natal points, computed once per chart. They are the
prerequisite substrate for Zodiacal Releasing (engine/zodiacal_releasing.py)
and are recorded in the predictive sidecar's natal_snapshot.lots (see
phase0/06_sidecar_and_export_contract.md section 2.2, added phase0.1.1).

Per phase0/03_method_charters.md C5:
  Lot of Fortune  (day):  ASC + Moon - Sun
  Lot of Fortune  (night): ASC + Sun - Moon
  Lot of Spirit   (day):  ASC + Sun - Moon
  Lot of Spirit   (night): ASC + Moon - Sun
  Lot of Necessity (day):  ASC + Fortune - Mercury
  Lot of Necessity (night): ASC + Mercury - Fortune

Sect is determined by formulas.standard.sect.evaluate_chart_sect(), the
chartered authoritative source. When sect is "unknown" (Sun exactly on the
ASC/DSC horizon axis), this module does not silently choose a sect: it
computes using the day-chart formula as a documented fallback and marks
sect_state = "unknown" with a materially reduced confidence, so a
consumer can tell the position was not sect-resolved. This matches C5
section 12's adversarial rule: raise a low-confidence flag, don't pretend
certainty.
"""

from __future__ import annotations

from typing import Any

from engine.natal_engine import whole_sign_house, zodiac_position
from formulas.standard.sect import evaluate_chart_sect

FORMULA_VERSION = "lots_phase6.0.0"
POLICY_VERSION = "phase0.1.1"

LOT_NAMES = ("Fortune", "Spirit", "Necessity")


def compute_lots(natal_payload: dict) -> dict[str, dict[str, Any]]:
    """
    Returns {"Fortune": {...}, "Spirit": {...}, "Necessity": {...}}.

    Each entry has the same shape as a natal_snapshot angle entry
    (longitude, sign, degree, minute, degree_decimal, formatted, house)
    plus "sect" ("day" | "night" | "unknown") and "sect_confidence"
    (1.0 for a resolved sect, reduced for "unknown").
    """
    sun_lon = _body_longitude(natal_payload, "standard_planets", "Sun")
    moon_lon = _body_longitude(natal_payload, "standard_planets", "Moon")
    mercury_lon = _body_longitude(natal_payload, "standard_planets", "Mercury")
    asc_lon = _body_longitude(natal_payload, "angles", "Ascendant")

    if sun_lon is None or moon_lon is None or mercury_lon is None or asc_lon is None:
        return {}

    sect = evaluate_chart_sect(natal_payload)
    sect_confidence = 1.0 if sect in ("day", "night") else 0.5
    # Fall back to the day-chart formula when sect is genuinely indeterminate
    # (Sun on the horizon axis) rather than silently picking a side.
    effective_sect = sect if sect in ("day", "night") else "day"
    is_day = effective_sect == "day"

    fortune_lon = (asc_lon + moon_lon - sun_lon) % 360.0 if is_day else (asc_lon + sun_lon - moon_lon) % 360.0
    spirit_lon = (asc_lon + sun_lon - moon_lon) % 360.0 if is_day else (asc_lon + moon_lon - sun_lon) % 360.0
    necessity_lon = (
        (asc_lon + fortune_lon - mercury_lon) % 360.0
        if is_day
        else (asc_lon + mercury_lon - fortune_lon) % 360.0
    )

    lots: dict[str, dict[str, Any]] = {}
    for name, longitude in (("Fortune", fortune_lon), ("Spirit", spirit_lon), ("Necessity", necessity_lon)):
        lots[name] = {
            "longitude": round(longitude, 4),
            **zodiac_position(longitude),
            "house": whole_sign_house(longitude, asc_lon),
            "sect": sect,
            "sect_confidence": sect_confidence,
            "formula_version": FORMULA_VERSION,
            "policy_version": POLICY_VERSION,
        }
    return lots


def lot_longitude(natal_payload: dict, lot_name: str) -> float | None:
    """Convenience accessor used by engine/zodiacal_releasing.py."""
    lots = compute_lots(natal_payload)
    entry = lots.get(lot_name)
    return float(entry["longitude"]) if entry else None


def _body_longitude(natal_payload: dict, section: str, name: str) -> float | None:
    group = natal_payload.get(section) if isinstance(natal_payload.get(section), dict) else {}
    data = group.get(name) if isinstance(group.get(name), dict) else {}
    value = data.get("longitude")
    return float(value) if isinstance(value, (int, float)) else None
