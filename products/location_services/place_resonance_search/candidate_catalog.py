"""
Candidate catalog helpers for Place Resonance Search.

The default catalog is now an expanded U.S. seed bank. It still uses curated
fixture-style coordinates, but the candidate volume is large enough to exercise
real search selectivity and ranking behavior.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


CATALOG_VERSION = "place_resonance_search_candidates_v0.4.0"
PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
DEFAULT_US_CATALOG_PATH = DATA_DIR / "us_candidate_fixture.json"

REQUIRED_CANDIDATE_FIELDS = {
    "location_id",
    "display_name",
    "city",
    "state",
    "country",
    "latitude",
    "longitude",
    "timezone",
    "population_tier",
    "region",
    "source",
    "active",
    "notes",
}

OPTIONAL_ONTOLOGY_FIELDS = {
    "selection_classes",
    "place_archetypes",
    "collections",
    "geographic_hierarchy",
    "climate_sensory_tags",
    "interpretive_use_cases",
}


def validate_search_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("Search candidate must be a dict.")

    missing = REQUIRED_CANDIDATE_FIELDS - set(candidate)
    if missing:
        raise ValueError(f"Search candidate is missing required field(s): {sorted(missing)}")

    location_id = candidate.get("location_id")
    if not isinstance(location_id, str) or not location_id.strip():
        raise ValueError("Search candidate location_id must be a non-empty string.")

    display_name = candidate.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        raise ValueError(f"Search candidate {location_id!r} requires display_name.")

    try:
        latitude = float(candidate["latitude"])
        longitude = float(candidate["longitude"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Search candidate {location_id!r} requires numeric coordinates.") from exc

    if not -90 <= latitude <= 90:
        raise ValueError(f"Search candidate {location_id!r} latitude is out of range.")
    if not -180 <= longitude <= 180:
        raise ValueError(f"Search candidate {location_id!r} longitude is out of range.")

    timezone = candidate.get("timezone")
    if not isinstance(timezone, str) or "/" not in timezone:
        raise ValueError(f"Search candidate {location_id!r} requires an IANA-style timezone.")

    if not isinstance(candidate.get("active"), bool):
        raise ValueError(f"Search candidate {location_id!r} active must be boolean.")

    if not isinstance(candidate.get("notes"), list):
        raise ValueError(f"Search candidate {location_id!r} notes must be a list.")

    normalized = copy.deepcopy(candidate)
    normalized["latitude"] = latitude
    normalized["longitude"] = longitude
    for field in OPTIONAL_ONTOLOGY_FIELDS:
        value = normalized.get(field)
        if value is None:
            normalized[field] = []
        elif not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError(f"Search candidate {location_id!r} {field} must be a list of non-empty strings.")
    return normalized


def validate_candidate_catalog(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Candidate catalog must be a non-empty list.")

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for candidate in candidates:
        item = validate_search_candidate(candidate)
        location_id = item["location_id"]
        if location_id in seen:
            raise ValueError(f"Duplicate search candidate location_id: {location_id}")
        seen.add(location_id)
        normalized.append(item)
    return normalized


def load_candidate_catalog(path: str | Path = DEFAULT_US_CATALOG_PATH) -> list[dict[str, Any]]:
    catalog_path = Path(path)
    with catalog_path.open("r", encoding="utf-8") as handle:
        parsed = json.load(handle)

    if isinstance(parsed, dict):
        candidates = parsed.get("candidates")
    else:
        candidates = parsed

    return validate_candidate_catalog(candidates)


def active_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [copy.deepcopy(candidate) for candidate in validate_candidate_catalog(candidates) if candidate["active"]]


def candidate_to_destination(candidate: dict[str, Any]) -> dict[str, Any]:
    item = validate_search_candidate(candidate)
    return {
        "display_name": item["display_name"],
        "location": item["display_name"],
        "latitude": item["latitude"],
        "longitude": item["longitude"],
        "timezone": item["timezone"],
        "coordinate_source": item["source"],
    }
