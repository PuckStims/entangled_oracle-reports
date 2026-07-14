"""
engine/astrocartography_svg.py - Static SVG contract for future astrocartography visuals.

This module does not compute astrocartography line geometry. It establishes
the visual contract and a truthful placeholder SVG so location-facing report
surfaces can wire the map slot before planetary angularity lines exist.
"""
from __future__ import annotations

import copy
import html
from typing import Any


CONTRACT_VERSION = "astrocartography_svg_contract_v0.1.0"
VIEWBOX = "0 0 960 540"
SVG_WIDTH = 960
SVG_HEIGHT = 540
_MAP_MARGIN_X = 48
_MAP_MARGIN_Y = 42
_MAP_WIDTH = SVG_WIDTH - (_MAP_MARGIN_X * 2)
_MAP_HEIGHT = SVG_HEIGHT - (_MAP_MARGIN_Y * 2)


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _project_equirectangular(latitude: float, longitude: float) -> dict[str, float]:
    """
    Project a latitude/longitude pair into the contract's SVG canvas.

    This is intentionally simple and explicit: the contract advertises an
    equirectangular projection so future line geometry can target a stable,
    documented coordinate system.
    """
    lat = _clamp(float(latitude), -90.0, 90.0)
    lon = ((float(longitude) + 180.0) % 360.0) - 180.0
    x = _MAP_MARGIN_X + ((lon + 180.0) / 360.0) * _MAP_WIDTH
    y = _MAP_MARGIN_Y + ((90.0 - lat) / 180.0) * _MAP_HEIGHT
    return {
        "x": round(x, 3),
        "y": round(y, 3),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
    }


def _extract_birth_anchor(natal_payload: dict) -> dict | None:
    profile = natal_payload.get("user_profile") or {}
    coords = profile.get("resolved_coordinates") or {}
    if not isinstance(coords, dict):
        return None
    try:
        latitude = float(coords["latitude"])
        longitude = float(coords["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    projected = _project_equirectangular(latitude, longitude)
    projected.update(
        {
            "label": "Birth",
            "display_name": profile.get("location") or profile.get("birth_location") or "Birth location",
            "source": "natal_payload.user_profile.resolved_coordinates",
        }
    )
    return projected


def _extract_destination_anchor(place_context: dict) -> dict | None:
    destination = place_context.get("destination_context") or {}
    if not isinstance(destination, dict):
        return None
    try:
        latitude = float(destination["latitude"])
        longitude = float(destination["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    projected = _project_equirectangular(latitude, longitude)
    projected.update(
        {
            "label": "Destination",
            "display_name": destination.get("display_name") or "Destination",
            "source": "place_context.destination_context",
        }
    )
    return projected


def _build_layer_status(*, birth_anchor: dict | None, destination_anchor: dict | None, exact_birth_time: bool) -> list[dict]:
    return [
        {
            "id": "projection_frame",
            "status": "rendered",
            "detail": "Equirectangular map frame with fixed viewBox for future line geometry.",
        },
        {
            "id": "graticule",
            "status": "rendered",
            "detail": "Latitude/longitude reference grid rendered.",
        },
        {
            "id": "birth_anchor",
            "status": "rendered" if birth_anchor else "unavailable",
            "detail": "Birth-place marker projected into SVG coordinates." if birth_anchor else "Birth coordinates unavailable.",
        },
        {
            "id": "destination_anchor",
            "status": "rendered" if destination_anchor else "unavailable",
            "detail": "Destination marker projected into SVG coordinates." if destination_anchor else "Destination coordinates unavailable.",
        },
        {
            "id": "planetary_lines",
            "status": "future_method",
            "detail": (
                "Planetary ASC/DSC/MC/IC line geometry is not computed yet."
                if exact_birth_time
                else "Planetary ASC/DSC/MC/IC line geometry is not computed yet and exact birth time would still be required."
            ),
        },
        {
            "id": "distance_bands",
            "status": "future_method",
            "detail": "Distance-to-line bands and nearest-point calculations are not computed yet.",
        },
    ]


def _graticule_lines() -> list[str]:
    lines: list[str] = []
    for longitude in range(-120, 181, 60):
        projected = _project_equirectangular(0.0, float(longitude))
        x = projected["x"]
        lines.append(
            f'<line x1="{x}" y1="{_MAP_MARGIN_Y}" x2="{x}" y2="{_MAP_MARGIN_Y + _MAP_HEIGHT}" '
            'stroke="rgba(78,96,96,0.16)" stroke-width="1" />'
        )
    for latitude in (-60, -30, 0, 30, 60):
        projected = _project_equirectangular(float(latitude), 0.0)
        y = projected["y"]
        lines.append(
            f'<line x1="{_MAP_MARGIN_X}" y1="{y}" x2="{_MAP_MARGIN_X + _MAP_WIDTH}" y2="{y}" '
            'stroke="rgba(78,96,96,0.16)" stroke-width="1" />'
        )
    return lines


def _longitude_label(longitude: int) -> str:
    if longitude == 0:
        return "0"
    return f"{abs(longitude)}{'W' if longitude < 0 else 'E'}"


def _latitude_label(latitude: int) -> str:
    if latitude == 0:
        return "0"
    return f"{abs(latitude)}{'S' if latitude < 0 else 'N'}"


def _route_arc_svg(start: dict, end: dict) -> str:
    x1 = start["x"]
    y1 = start["y"]
    x2 = end["x"]
    y2 = end["y"]
    cx = round((x1 + x2) / 2.0, 3)
    cy = round(min(y1, y2) - max(54.0, abs(x2 - x1) * 0.08), 3)
    return (
        f'<path d="M {x1} {y1} Q {cx} {cy} {x2} {y2}" '
        'fill="none" stroke="url(#routeGlow)" stroke-width="2.6" '
        'stroke-linecap="round" stroke-dasharray="7 7" opacity="0.95" />'
    )


def _anchor_svg(anchor: dict, *, kind: str) -> str:
    x = anchor["x"]
    y = anchor["y"]
    label = html.escape(anchor.get("label") or kind.title())
    title = html.escape(anchor.get("display_name") or label)
    color = "#b06a3c" if kind == "birth" else "#325c56"
    halo = "rgba(176,106,60,0.18)" if kind == "birth" else "rgba(50,92,86,0.18)"
    text_anchor = "start" if x <= SVG_WIDTH / 2 else "end"
    text_dx = 12 if text_anchor == "start" else -12
    return (
        f'<g class="anchor anchor-{kind}">'
        f'<circle cx="{x}" cy="{y}" r="13" fill="{halo}" />'
        f'<circle cx="{x}" cy="{y}" r="5.5" fill="{color}" stroke="#fffaf3" stroke-width="2" />'
        f'<text x="{x + text_dx}" y="{y - 10}" text-anchor="{text_anchor}" '
        'font-family="Inter, Arial, sans-serif" font-size="13" font-weight="600" '
        f'fill="{color}">{label}</text>'
        f'<text x="{x + text_dx}" y="{y + 8}" text-anchor="{text_anchor}" '
        'font-family="Inter, Arial, sans-serif" font-size="11" '
        'fill="rgba(31,29,25,0.74)">'
        f"{title}</text>"
        "</g>"
    )


def render_astrocartography_contract_svg(contract: dict) -> str:
    """
    Render the contract's current SVG state.

    The visual is honest about capability: it shows the projection frame and
    available anchors, and labels the uncomputed astrocartography line layer
    as future work instead of implying it exists.
    """
    anchors = contract.get("anchors") or {}
    birth_anchor = anchors.get("birth")
    destination_anchor = anchors.get("destination")
    warnings = contract.get("warnings") or []

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEWBOX}" width="100%" '
        'role="img" aria-label="Astrocartography contract preview">',
        "<defs>",
        '<linearGradient id="mapBg" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#18353b" />',
        '<stop offset="55%" stop-color="#234a4e" />',
        '<stop offset="100%" stop-color="#6d4f40" />',
        "</linearGradient>",
        '<linearGradient id="mapPanel" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0%" stop-color="#fffdf8" />',
        '<stop offset="100%" stop-color="#f0e2cf" />',
        "</linearGradient>",
        '<linearGradient id="routeGlow" x1="0" y1="0" x2="1" y2="0">',
        '<stop offset="0%" stop-color="#d8a062" />',
        '<stop offset="100%" stop-color="#9fd0ca" />',
        "</linearGradient>",
        '<filter id="contract-glow" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="8" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>',
        "</defs>",
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" rx="18" fill="url(#mapBg)" />',
        f'<rect x="{_MAP_MARGIN_X}" y="{_MAP_MARGIN_Y}" width="{_MAP_WIDTH}" height="{_MAP_HEIGHT}" '
        'rx="18" fill="url(#mapPanel)" stroke="rgba(255,245,231,0.50)" stroke-width="1.5" />',
        * _graticule_lines(),
        f'<rect x="{_MAP_MARGIN_X + 18}" y="{_MAP_MARGIN_Y + 18}" width="304" height="66" rx="14" '
        'fill="rgba(24,53,59,0.78)" stroke="rgba(255,245,231,0.18)" />',
        '<text x="72" y="78" font-family="Inter, Arial, sans-serif" font-size="24" '
        'font-weight="600" fill="#fff7ed">Astrocartography Visual Contract</text>',
        '<text x="72" y="104" font-family="Inter, Arial, sans-serif" font-size="13" '
        'fill="rgba(255,247,237,0.84)">Projection and anchor layer wired. Planetary angularity lines reserved for future computation.</text>',
        f'<rect x="72" y="{SVG_HEIGHT - 112}" width="348" height="68" rx="12" fill="rgba(24,53,59,0.72)" stroke="rgba(255,245,231,0.16)" />',
        f'<text x="90" y="{SVG_HEIGHT - 80}" font-family="Inter, Arial, sans-serif" font-size="12" '
        'font-weight="600" fill="#fff7ed">Future map layers</text>',
        f'<text x="90" y="{SVG_HEIGHT - 60}" font-family="Inter, Arial, sans-serif" font-size="11" '
        'fill="rgba(255,247,237,0.82)">ASC, DSC, MC, and IC planetary line geometry</text>',
    ]

    for longitude in range(-120, 181, 60):
        projected = _project_equirectangular(0.0, float(longitude))
        lines.append(
            f'<text x="{projected["x"]}" y="{_MAP_MARGIN_Y + _MAP_HEIGHT + 24}" text-anchor="middle" '
            'font-family="Inter, Arial, sans-serif" font-size="10.5" fill="rgba(255,247,237,0.82)">'
            f'{_longitude_label(longitude)}</text>'
        )
    for latitude in (-60, -30, 0, 30, 60):
        projected = _project_equirectangular(float(latitude), 0.0)
        lines.append(
            f'<text x="{_MAP_MARGIN_X - 12}" y="{projected["y"] + 4}" text-anchor="end" '
            'font-family="Inter, Arial, sans-serif" font-size="10.5" fill="rgba(255,247,237,0.82)">'
            f'{_latitude_label(latitude)}</text>'
        )

    if birth_anchor and destination_anchor:
        lines.append(_route_arc_svg(birth_anchor, destination_anchor))
        mid_x = round((birth_anchor["x"] + destination_anchor["x"]) / 2.0, 3)
        mid_y = round(min(birth_anchor["y"], destination_anchor["y"]) - 52.0, 3)
        lines.append(
            f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" '
            'font-family="Inter, Arial, sans-serif" font-size="11" font-weight="600" '
            'fill="#f4e0bf">Relocation arc</text>'
        )

    if birth_anchor:
        lines.append(_anchor_svg(birth_anchor, kind="birth"))
    if destination_anchor:
        lines.append(_anchor_svg(destination_anchor, kind="destination"))

    if warnings:
        y = SVG_HEIGHT - 150
        for warning in warnings[:2]:
            lines.append(
                f'<text x="72" y="{y}" font-family="Inter, Arial, sans-serif" font-size="11" '
                f'fill="rgba(31,29,25,0.68)">{html.escape(str(warning))}</text>'
            )
            y += 16

    lines.append("</svg>")
    return "".join(lines)


def build_astrocartography_svg_contract(natal_payload: dict, place_context: dict) -> dict:
    """
    Build the structured SVG contract consumed by Location Services report surfaces.
    """
    birth_context = place_context.get("birth_context") or {}
    exact_birth_time = birth_context.get("birth_time_confidence") == "exact_birth_time"
    birth_anchor = _extract_birth_anchor(natal_payload)
    destination_anchor = _extract_destination_anchor(place_context)

    warnings: list[str] = []
    if not exact_birth_time:
        warnings.append("Exact birth time is still required before any angularity line geometry can be trusted.")
    if not birth_anchor:
        warnings.append("Birth coordinates were unavailable, so the natal anchor could not be plotted.")
    if not destination_anchor:
        warnings.append("Destination coordinates were unavailable, so the destination anchor could not be plotted.")

    contract = {
        "contract_version": CONTRACT_VERSION,
        "title": "Astrocartography Visual",
        "status": "contract_ready_future_method",
        "projection": "equirectangular",
        "viewbox": VIEWBOX,
        "width": SVG_WIDTH,
        "height": SVG_HEIGHT,
        "note": (
            "Projection frame and anchor plotting are wired. Planetary ASC/DSC/MC/IC "
            "line geometry and distance bands remain intentionally uncomputed in this pass."
        ),
        "capability_boundary": {
            "line_geometry": "not_computed",
            "distance_to_line": "not_computed",
            "nearest_point": "not_computed",
        },
        "anchors": {
            "birth": _deepcopy(birth_anchor),
            "destination": _deepcopy(destination_anchor),
        },
        "layers": _build_layer_status(
            birth_anchor=birth_anchor,
            destination_anchor=destination_anchor,
            exact_birth_time=exact_birth_time,
        ),
        "warnings": warnings,
    }
    contract["svg"] = render_astrocartography_contract_svg(contract)
    return contract
