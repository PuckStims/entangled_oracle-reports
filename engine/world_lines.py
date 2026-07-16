from __future__ import annotations

import math
import os
from typing import List, TypedDict

import swisseph as swe


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")
swe.set_ephe_path(EPHE_PATH)

CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
FORMULA_VERSION = "world_lines_v0.2.0"
EARTH_RADIUS_KM = 6371.0088

BODY_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

ANGLE_TYPES = ("Ascendant", "Descendant", "Midheaven", "Imum_Coeli")


class NearestPoint(TypedDict):
    latitude: float
    longitude: float


class LineEvidenceItem(TypedDict):
    id: str
    body: str
    angle: str
    distance_km: float
    strength_band: str
    nearest_point: NearestPoint
    birth_time_sensitivity: str
    natal_condition: dict
    house_rulerships: List[int]
    geometry_method: str


class WorldLinesEvidenceRecord(TypedDict):
    formula_version: str
    destination: dict
    lines: List[LineEvidenceItem]
    line_clusters: List[dict]
    unsupported_methods: List[str]
    warnings: List[str]
    appendix_trace: dict


def _normalize_longitude(longitude: float) -> float:
    return ((float(longitude) + 180.0) % 360.0) - 180.0


def _angle_difference(a: float, b: float) -> float:
    diff = abs((a - b) % 360.0)
    return min(diff, 360.0 - diff)


def _destination_coordinates(destination: dict) -> tuple[float, float]:
    try:
        return float(destination["latitude"]), float(destination["longitude"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("World Lines requires destination latitude and longitude.") from exc


def _julian_day(natal_payload: dict) -> float:
    jd = (natal_payload.get("user_profile") or {}).get("julian_day")
    if not isinstance(jd, (int, float)):
        raise ValueError("World Lines requires natal_payload.user_profile.julian_day.")
    return float(jd)


def _birth_time_sensitivity(natal_payload: dict, angle: str) -> str:
    state = (natal_payload.get("user_profile") or {}).get("birth_time_state")
    if state != "exact_birth_time":
        return "high"
    return "medium" if angle in {"Ascendant", "Descendant"} else "low"


def _body_equatorial(jd: float, body_id: int) -> tuple[float, float]:
    coords, _flags = swe.calc_ut(jd, body_id, CALC_FLAGS)
    return float(coords[0] % 360.0), float(coords[1])


def _sidereal_degrees(jd: float) -> float:
    return (float(swe.sidtime(jd)) * 15.0) % 360.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(_normalize_longitude(lon2 - lon1))
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return EARTH_RADIUS_KM * 2.0 * math.asin(min(1.0, math.sqrt(a)))


def _strength_band(distance_km: float) -> str:
    if distance_km <= 100:
        return "tight"
    if distance_km <= 300:
        return "moderate"
    if distance_km <= 600:
        return "wide"
    return "background"


def _mc_ic_nearest_point(
    *,
    jd: float,
    ra: float,
    angle: str,
    destination_lat: float,
    destination_lon: float,
) -> tuple[float, float, float]:
    gst = _sidereal_degrees(jd)
    offset = 0.0 if angle == "Midheaven" else 180.0
    line_lon = _normalize_longitude((ra + offset) - gst)
    distance = _haversine_km(destination_lat, destination_lon, destination_lat, line_lon)
    return round(destination_lat, 4), round(line_lon, 4), distance


def _asc_dsc_candidates(jd: float, ra: float, declination: float, angle: str) -> list[tuple[float, float]]:
    gst = _sidereal_degrees(jd)
    dec_rad = math.radians(declination)
    candidates: list[tuple[float, float]] = []
    sin_dec = math.sin(dec_rad)
    cos_dec = math.cos(dec_rad)

    for lon in range(-180, 181, 2):
        lst = (gst + lon) % 360.0
        hour_angle = math.radians(((lst - ra + 180.0) % 360.0) - 180.0)

        if abs(sin_dec) < 1e-6:
            if abs(math.cos(hour_angle)) > 0.02:
                continue
            latitude = 0.0
        else:
            latitude = math.degrees(math.atan2(-cos_dec * math.cos(hour_angle), sin_dec))

        rising = math.sin(hour_angle) < 0
        if (angle == "Ascendant" and rising) or (angle == "Descendant" and not rising):
            candidates.append((max(-89.5, min(89.5, latitude)), float(lon)))
    return candidates


def _asc_dsc_nearest_point(
    *,
    jd: float,
    ra: float,
    declination: float,
    angle: str,
    destination_lat: float,
    destination_lon: float,
) -> tuple[float, float, float] | None:
    candidates = _asc_dsc_candidates(jd, ra, declination, angle)
    if not candidates:
        return None
    lat, lon = min(
        candidates,
        key=lambda item: _haversine_km(destination_lat, destination_lon, item[0], item[1]),
    )
    return round(lat, 4), round(_normalize_longitude(lon), 4), _haversine_km(destination_lat, destination_lon, lat, lon)


def _line_item(
    natal_payload: dict,
    body: str,
    angle: str,
    nearest_lat: float,
    nearest_lon: float,
    distance: float,
) -> LineEvidenceItem:
    natal_body = (natal_payload.get("standard_planets") or {}).get(body) or {}
    return {
        "id": f"line:{body}:{angle}",
        "body": body,
        "angle": angle,
        "distance_km": round(distance, 1),
        "strength_band": _strength_band(distance),
        "nearest_point": {"latitude": nearest_lat, "longitude": nearest_lon},
        "birth_time_sensitivity": _birth_time_sensitivity(natal_payload, angle),
        "natal_condition": {
            "natal_house": natal_body.get("house"),
            "natal_sign": natal_body.get("sign"),
        },
        "house_rulerships": [],
        "geometry_method": (
            "sidereal_meridian_longitude"
            if angle in {"Midheaven", "Imum_Coeli"}
            else "sampled_horizon_rise_set_curve_2deg"
        ),
    }


def build_line_evidence(natal_payload: dict, destination: dict) -> WorldLinesEvidenceRecord:
    """
    Build v1 astrocartography line-proximity evidence.

    This computes ASC/DSC/MC/IC angularity line proximity for standard planets
    using Swiss Ephemeris equatorial positions at the preserved natal Julian
    Day. Parans, crossings, and remote activation remain explicitly unsupported.
    """
    destination_lat, destination_lon = _destination_coordinates(destination)
    jd = _julian_day(natal_payload)

    warnings: list[str] = []
    lines: list[LineEvidenceItem] = []
    for body, body_id in BODY_IDS.items():
        try:
            ra, dec = _body_equatorial(jd, body_id)
        except swe.Error as exc:
            warnings.append(f"{body} line geometry unavailable: {exc}")
            continue

        for angle in ANGLE_TYPES:
            if angle in {"Midheaven", "Imum_Coeli"}:
                nearest_lat, nearest_lon, distance = _mc_ic_nearest_point(
                    jd=jd,
                    ra=ra,
                    angle=angle,
                    destination_lat=destination_lat,
                    destination_lon=destination_lon,
                )
            else:
                nearest = _asc_dsc_nearest_point(
                    jd=jd,
                    ra=ra,
                    declination=dec,
                    angle=angle,
                    destination_lat=destination_lat,
                    destination_lon=destination_lon,
                )
                if nearest is None:
                    warnings.append(f"{body} {angle} line could not be sampled for this chart.")
                    continue
                nearest_lat, nearest_lon, distance = nearest
            lines.append(_line_item(natal_payload, body, angle, nearest_lat, nearest_lon, distance))

    lines.sort(key=lambda item: (item["distance_km"], item["body"], item["angle"]))
    closest = lines[:12]

    return {
        "formula_version": FORMULA_VERSION,
        "destination": dict(destination),
        "lines": closest,
        "line_clusters": [],
        "unsupported_methods": ["parans", "remote_activation", "line_crossing_interpretation"],
        "warnings": warnings,
        "appendix_trace": {
            "methodology": "Swiss Ephemeris equatorial positions; MC/IC meridian longitude plus sampled ASC/DSC horizon curves.",
            "distance_band_policy_km": {
                "tight": "0-100",
                "moderate": "100-300",
                "wide": "300-600",
                "background": "600+",
            },
            "sample_step_degrees": 2,
            "unsupported_methods": ["parans", "remote_activation", "line_crossing_interpretation"],
            "warnings": warnings,
        },
    }
