from __future__ import annotations

import math
import os
from typing import List, TypedDict

import swisseph as swe

from formulas.standard.planetary_condition import evaluate_all_planetary_conditions


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")
swe.set_ephe_path(EPHE_PATH)

CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
FORMULA_VERSION = "local_space_v0.3.0"
EARTH_RADIUS_KM = 6371.0088
DESTINATION_ALIGNMENT_MAX_KM = 2000.0

WEIGHT_FACTORS = {
    "altitude_relevance": 0.35,
    "angular_relevance": 0.25,
    "natal_condition": 0.25,
    "destination_alignment": 0.15,
}

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

PRACTICAL_MODES = {
    "Sun": "Visibility",
    "Moon": "Restoration",
    "Mercury": "Study",
    "Venus": "Relationship",
    "Mars": "Movement",
    "Jupiter": "Expansion",
    "Saturn": "Structure",
    "Uranus": "Experimentation",
    "Neptune": "Retreat",
    "Pluto": "Deep Work",
}


class DirectionEvidenceItem(TypedDict):
    id: str
    body: str
    azimuth: float
    altitude: float
    direction_label: str
    cross_track_distance_km: float | None
    bearing_to_destination: float | None
    natal_condition: dict
    practical_mode: str
    raw_inputs: dict
    weight_components: dict
    weighted_score: float
    rank: int
    route_geometry: dict | None


class LocalSpaceEvidenceRecord(TypedDict):
    formula_version: str
    anchor_context: dict
    destination_context: dict
    route_context: dict
    directions: List[DirectionEvidenceItem]
    unsupported_methods: List[str]
    warnings: List[str]
    appendix_trace: dict


def _coordinates(place: dict, label: str) -> tuple[float, float]:
    try:
        return float(place["latitude"]), float(place["longitude"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Local Compass requires {label} latitude and longitude.") from exc


def _julian_day(natal_payload: dict) -> float:
    jd = (natal_payload.get("user_profile") or {}).get("julian_day")
    if not isinstance(jd, (int, float)):
        raise ValueError("Local Compass requires natal_payload.user_profile.julian_day.")
    return float(jd)


def _sidereal_degrees(jd: float) -> float:
    return (float(swe.sidtime(jd)) * 15.0) % 360.0


def _body_equatorial(jd: float, body_id: int) -> tuple[float, float]:
    coords, _flags = swe.calc_ut(jd, body_id, CALC_FLAGS)
    return float(coords[0] % 360.0), float(coords[1])


def _normalize_degrees(value: float) -> float:
    return float(value % 360.0)


def _angular_difference(a: float, b: float) -> float:
    diff = abs((a - b) % 360.0)
    return min(diff, 360.0 - diff)


def _azimuth_altitude(jd: float, latitude: float, longitude: float, ra: float, declination: float) -> tuple[float, float]:
    lat = math.radians(latitude)
    dec = math.radians(declination)
    lst = (_sidereal_degrees(jd) + longitude) % 360.0
    hour_angle = math.radians(((lst - ra + 180.0) % 360.0) - 180.0)

    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(hour_angle)
    altitude = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))

    azimuth = math.degrees(
        math.atan2(
            -math.sin(hour_angle),
            math.tan(dec) * math.cos(lat) - math.sin(lat) * math.cos(hour_angle),
        )
    )
    return round(_normalize_degrees(azimuth), 1), round(altitude, 1)


def _direction_label(azimuth: float) -> str:
    labels = [
        "North", "North-Northeast", "Northeast", "East-Northeast",
        "East", "East-Southeast", "Southeast", "South-Southeast",
        "South", "South-Southwest", "Southwest", "West-Southwest",
        "West", "West-Northwest", "Northwest", "North-Northwest",
    ]
    index = int((azimuth + 11.25) // 22.5) % 16
    return labels[index]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return EARTH_RADIUS_KM * 2.0 * math.asin(min(1.0, math.sqrt(a)))


def _bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)
    y = math.sin(d_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    return _normalize_degrees(math.degrees(math.atan2(y, x)))


def _cross_track_distance_km(anchor_lat: float, anchor_lon: float, dest_lat: float, dest_lon: float, azimuth: float) -> tuple[float, float]:
    distance = _haversine_km(anchor_lat, anchor_lon, dest_lat, dest_lon)
    bearing = _bearing_degrees(anchor_lat, anchor_lon, dest_lat, dest_lon)
    angle_delta = math.radians(_angular_difference(bearing, azimuth))
    return round(abs(math.sin(angle_delta) * distance), 1), round(bearing, 1)


def _along_track_distance_km(anchor_lat: float, anchor_lon: float, point_lat: float, point_lon: float, azimuth: float) -> float:
    distance = _haversine_km(anchor_lat, anchor_lon, point_lat, point_lon)
    bearing = _bearing_degrees(anchor_lat, anchor_lon, point_lat, point_lon)
    signed_delta = ((bearing - azimuth + 180.0) % 360.0) - 180.0
    return distance * math.cos(math.radians(signed_delta))


def _route_waypoints(route: dict | None) -> list[dict]:
    if not isinstance(route, dict):
        return []
    waypoints = route.get("waypoints")
    if not isinstance(waypoints, list):
        return []
    cleaned: list[dict] = []
    for waypoint in waypoints:
        if not isinstance(waypoint, dict):
            continue
        try:
            cleaned.append({
                "latitude": float(waypoint["latitude"]),
                "longitude": float(waypoint["longitude"]),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return cleaned


def _route_geometry(
    anchor_lat: float,
    anchor_lon: float,
    azimuth: float,
    route: dict | None,
) -> dict | None:
    waypoints = _route_waypoints(route)
    if len(waypoints) < 2:
        return None

    corridor_width_km = float((route or {}).get("corridor_width_km") or 150.0)
    route_id = str((route or {}).get("route_id") or "route")

    samples: list[tuple[float, float, int]] = []
    overlap_length_km = 0.0
    closest_segment_index = 0
    closest_segment_offset = None

    for index, start in enumerate(waypoints[:-1]):
        end = waypoints[index + 1]
        segment_length = _haversine_km(
            start["latitude"], start["longitude"], end["latitude"], end["longitude"]
        )
        midpoint = {
            "latitude": (start["latitude"] + end["latitude"]) / 2.0,
            "longitude": (start["longitude"] + end["longitude"]) / 2.0,
        }
        sample_points = (start, midpoint, end)
        sample_offsets: list[float] = []
        sample_ahead = False
        for point in sample_points:
            cross_track, bearing = _cross_track_distance_km(
                anchor_lat, anchor_lon, point["latitude"], point["longitude"], azimuth
            )
            along_track = _along_track_distance_km(
                anchor_lat, anchor_lon, point["latitude"], point["longitude"], azimuth
            )
            samples.append((cross_track, along_track, index))
            sample_offsets.append(cross_track)
            if along_track >= 0:
                sample_ahead = True

        segment_min_offset = min(sample_offsets)
        if closest_segment_offset is None or segment_min_offset < closest_segment_offset:
            closest_segment_offset = segment_min_offset
            closest_segment_index = index

        if sample_ahead and segment_min_offset <= corridor_width_km:
            overlap_length_km += segment_length

    if not samples:
        return None

    min_offset, _, _ = min(samples, key=lambda item: item[0])
    if min_offset <= 50.0:
        strength = "high"
    elif min_offset <= corridor_width_km:
        strength = "medium"
    else:
        strength = "low"

    return {
        "route_id": route_id,
        "corridor_width_km": round(corridor_width_km, 1),
        "minimum_offset_km": round(min_offset, 1),
        "overlap_length_km": round(overlap_length_km, 1),
        "closest_route_segment": closest_segment_index,
        "strength": strength,
        "claim_boundary": (
            "Route-corridor geometry compares the supplied route polyline to the local-space ray. "
            "It does not optimize travel or guarantee experiential outcome."
        ),
        "geometry_method": "waypoint_and_midpoint_sampling_against_anchor_ray",
    }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _altitude_relevance(altitude: float) -> float:
    """
    Directional emphasis is strongest nearer the horizon line and weakest
    near zenith/nadir, where the experience is less direction-like.
    """
    return round(_clamp01(1.0 - (abs(float(altitude)) / 90.0)), 4)


def _angular_relevance(natal_house: int | None) -> float:
    if natal_house in {1, 4, 7, 10}:
        return 1.0
    if natal_house in {2, 5, 8, 11}:
        return 0.65
    if natal_house in {3, 6, 9, 12}:
        return 0.35
    return 0.5


def _natal_condition_strength(condition_score: float | None) -> float:
    if not isinstance(condition_score, (int, float)):
        return 0.5
    return round(_clamp01((float(condition_score) + 8.0) / 16.0), 4)


def _destination_alignment_strength(cross_track_distance_km: float | None) -> float:
    if cross_track_distance_km is None:
        return 0.5
    return round(_clamp01(1.0 - (float(cross_track_distance_km) / DESTINATION_ALIGNMENT_MAX_KM)), 4)


def _weight_components(
    *,
    altitude: float,
    natal_house: int | None,
    natal_condition_score: float | None,
    cross_track_distance_km: float | None,
) -> tuple[dict[str, float], dict[str, float], float]:
    raw_inputs = {
        "altitude_relevance": _altitude_relevance(altitude),
        "angular_relevance": _angular_relevance(natal_house),
        "natal_condition": _natal_condition_strength(natal_condition_score),
        "destination_alignment": _destination_alignment_strength(cross_track_distance_km),
    }
    weighted = {
        key: round(raw_inputs[key] * weight, 4)
        for key, weight in WEIGHT_FACTORS.items()
    }
    weighted_score = round(sum(weighted.values()), 4)
    return raw_inputs, weighted, weighted_score


def _rank_directions(directions: list[DirectionEvidenceItem]) -> list[DirectionEvidenceItem]:
    ranked = sorted(
        directions,
        key=lambda item: (-item["weighted_score"], item["body"]),
    )
    for index, direction in enumerate(ranked, start=1):
        direction["rank"] = index
    return ranked


def build_local_space_evidence(
    natal_payload: dict,
    anchor: dict,
    destination: dict | None = None,
    route: dict | None = None,
) -> LocalSpaceEvidenceRecord:
    """
    Build v1 Local Space evidence: planetary azimuths from an anchor place at
    the preserved natal instant, optionally compared with a destination bearing.
    """
    anchor_lat, anchor_lon = _coordinates(anchor, "anchor")
    jd = _julian_day(natal_payload)
    destination_context = dict(destination or {})
    route_context = dict(route or {})
    destination_coords = None
    if destination:
        try:
            destination_coords = _coordinates(destination, "destination")
        except ValueError:
            destination_coords = None
    if route and len(_route_waypoints(route)) < 2:
        warnings = ["Route corridor geometry requires at least two valid waypoints."]
    else:
        warnings = []
    natal_conditions = evaluate_all_planetary_conditions(natal_payload)
    directions: list[DirectionEvidenceItem] = []
    for body, body_id in BODY_IDS.items():
        try:
            ra, dec = _body_equatorial(jd, body_id)
            azimuth, altitude = _azimuth_altitude(jd, anchor_lat, anchor_lon, ra, dec)
        except swe.Error as exc:
            warnings.append(f"{body} direction unavailable: {exc}")
            continue

        cross_track = None
        bearing = None
        if destination_coords is not None:
            cross_track, bearing = _cross_track_distance_km(
                anchor_lat,
                anchor_lon,
                destination_coords[0],
                destination_coords[1],
                azimuth,
            )

        natal_body = (natal_payload.get("standard_planets") or {}).get(body) or {}
        condition_record = natal_conditions.get(body)
        condition_score = (
            condition_record.overall_condition_score
            if condition_record is not None
            else None
        )
        raw_inputs, weight_components, weighted_score = _weight_components(
            altitude=altitude,
            natal_house=natal_body.get("house"),
            natal_condition_score=condition_score,
            cross_track_distance_km=cross_track,
        )
        route_geometry = _route_geometry(anchor_lat, anchor_lon, azimuth, route)
        directions.append({
            "id": f"direction:{body}",
            "body": body,
            "azimuth": azimuth,
            "altitude": altitude,
            "direction_label": _direction_label(azimuth),
            "cross_track_distance_km": cross_track,
            "bearing_to_destination": bearing,
            "natal_condition": {
                "natal_house": natal_body.get("house"),
                "natal_sign": natal_body.get("sign"),
                "overall_condition_score": condition_score,
            },
            "practical_mode": PRACTICAL_MODES.get(body, "Orientation"),
            "raw_inputs": raw_inputs,
            "weight_components": weight_components,
            "weighted_score": weighted_score,
            "rank": 0,
            "route_geometry": route_geometry,
        })

    directions = _rank_directions(directions)
    return {
        "formula_version": FORMULA_VERSION,
        "anchor_context": dict(anchor),
        "destination_context": destination_context,
        "route_context": route_context,
        "directions": directions,
        "unsupported_methods": [],
        "warnings": warnings,
        "appendix_trace": {
            "methodology": "Swiss Ephemeris equatorial positions projected to local horizon azimuth at the anchor place.",
            "azimuth_convention": "0 degrees is North; values increase clockwise through East.",
            "sector_count": 16,
            "weighting_policy": {
                "score_range": "0.0 to 1.0",
                "weights": dict(WEIGHT_FACTORS),
                "altitude_relevance": "1 - abs(altitude)/90; horizon-proximate directions rank higher than zenith/nadir directions.",
                "angular_relevance": "Natal angular houses > succedent houses > cadent houses.",
                "natal_condition": "Natal overall_condition_score normalized from an expected -8 to +8 band and clamped to 0..1.",
                "destination_alignment": "1 - cross_track_distance_km/2000, clamped to 0..1; anchor-only reports use a neutral 0.5.",
                "tie_break": "Higher weighted_score first, then body name ascending for deterministic ranking.",
            },
            "route_geometry_policy": {
                "corridor_width_default_km": 150.0,
                "sample_points": "segment start, midpoint, and end",
                "overlap_rule": "segment contributes when any sampled point is ahead of the anchor ray and the minimum sampled offset is inside the corridor width",
            },
            "unsupported_methods": [],
            "warnings": warnings,
        },
    }
