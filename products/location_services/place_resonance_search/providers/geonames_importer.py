"""
GeoNames import helpers for Place Resonance Search.

GeoNames dump rows use the documented geoname table layout:
geonameid, name, asciiname, alternatenames, latitude, longitude,
feature_class, feature_code, country_code, cc2, admin1_code, admin2_code,
admin3_code, admin4_code, population, elevation, dem, timezone,
modification_date.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from products.location_services.place_resonance_search.candidate_catalog import (
    validate_search_candidate,
)


GEONAMES_SOURCE = "geonames_dump"

US_REGION_BY_STATE = {
    "AL": "Southeast",
    "AK": "Non-Contiguous",
    "AZ": "Southwest",
    "AR": "Southeast",
    "CA": "West Coast",
    "CO": "Mountain West",
    "CT": "Northeast",
    "DE": "Mid-Atlantic",
    "DC": "Mid-Atlantic",
    "FL": "Florida",
    "GA": "Southeast",
    "HI": "Non-Contiguous",
    "ID": "Mountain West",
    "IL": "Midwest",
    "IN": "Midwest",
    "IA": "Midwest",
    "KS": "Great Plains",
    "KY": "Appalachia",
    "LA": "Gulf South",
    "ME": "Northeast",
    "MD": "Mid-Atlantic",
    "MA": "Northeast",
    "MI": "Great Lakes",
    "MN": "Upper Midwest",
    "MS": "Gulf South",
    "MO": "Midwest",
    "MT": "Mountain West",
    "NE": "Great Plains",
    "NV": "Mountain West",
    "NH": "Northeast",
    "NJ": "Mid-Atlantic",
    "NM": "Southwest",
    "NY": "Northeast",
    "NC": "Southeast",
    "ND": "Great Plains",
    "OH": "Great Lakes",
    "OK": "Great Plains",
    "OR": "Pacific Northwest",
    "PA": "Mid-Atlantic",
    "RI": "Northeast",
    "SC": "Southeast",
    "SD": "Great Plains",
    "TN": "Southeast",
    "TX": "Texas",
    "UT": "Mountain West",
    "VT": "Northeast",
    "VA": "Mid-Atlantic",
    "WA": "Pacific Northwest",
    "WV": "Appalachia",
    "WI": "Great Lakes",
    "WY": "Mountain West",
}


def slugify_location_part(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"


def build_location_id(country_code: str, admin1_code: str, name: str) -> str:
    country = slugify_location_part(country_code)
    admin = slugify_location_part(admin1_code)
    city = slugify_location_part(name)
    return f"{country}-{admin}-{city}"


def population_tier(population: int | str | None) -> str:
    try:
        value = int(population or 0)
    except (TypeError, ValueError):
        value = 0
    if value >= 2_000_000:
        return "major_metro"
    if value >= 500_000:
        return "large_metro"
    if value >= 100_000:
        return "mid_metro"
    if value >= 25_000:
        return "small_metro"
    return "small_town"


def parse_geonames_row(line: str) -> dict[str, Any]:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 19:
        raise ValueError("GeoNames row must contain at least 19 tab-separated columns.")
    return {
        "geoname_id": parts[0],
        "name": parts[1],
        "ascii_name": parts[2],
        "alternate_names": parts[3],
        "latitude": parts[4],
        "longitude": parts[5],
        "feature_class": parts[6],
        "feature_code": parts[7],
        "country_code": parts[8],
        "cc2": parts[9],
        "admin1_code": parts[10],
        "admin2_code": parts[11],
        "admin3_code": parts[12],
        "admin4_code": parts[13],
        "population": parts[14],
        "elevation": parts[15],
        "dem": parts[16],
        "timezone": parts[17],
        "modification_date": parts[18],
    }


def geonames_row_to_candidate(row: dict[str, Any], *, active: bool = True) -> dict[str, Any]:
    country = str(row.get("country_code") or "").upper()
    admin1 = str(row.get("admin1_code") or "").upper()
    city = str(row.get("ascii_name") or row.get("name") or "").strip()
    if not city:
        raise ValueError("GeoNames row requires a city/name value.")

    candidate = {
        "location_id": build_location_id(country, admin1, city),
        "display_name": f"{city}, {admin1}, {country}",
        "city": city,
        "state": admin1,
        "country": country,
        "latitude": round(float(row["latitude"]), 4),
        "longitude": round(float(row["longitude"]), 4),
        "timezone": str(row.get("timezone") or "UTC"),
        "population_tier": population_tier(row.get("population")),
        "region": US_REGION_BY_STATE.get(admin1, "Provider Catalog"),
        "source": GEONAMES_SOURCE,
        "active": active,
        "notes": [
            f"GeoNames {row.get('feature_code')}",
            f"population:{int(row.get('population') or 0)}",
        ],
        "selection_classes": [],
        "place_archetypes": [],
        "collections": [],
        "geographic_hierarchy": [],
        "climate_sensory_tags": [],
        "interpretive_use_cases": [],
        "provider_metadata": {
            "provider": "geonames",
            "geoname_id": str(row.get("geoname_id") or ""),
            "feature_class": str(row.get("feature_class") or ""),
            "feature_code": str(row.get("feature_code") or ""),
            "population": int(row.get("population") or 0),
            "admin2_code": str(row.get("admin2_code") or ""),
        },
    }
    return validate_search_candidate(candidate)


def geonamescache_city_to_candidate(city: dict[str, Any], *, active: bool = True) -> dict[str, Any]:
    country = str(city.get("countrycode") or "").upper()
    admin1 = str(city.get("admin1code") or "").upper()
    name = str(city.get("name") or "").strip()
    if not name:
        raise ValueError("geonamescache city requires a name.")

    candidate = {
        "location_id": build_location_id(country, admin1, name),
        "display_name": f"{name}, {admin1}, {country}",
        "city": name,
        "state": admin1,
        "country": country,
        "latitude": round(float(city["latitude"]), 4),
        "longitude": round(float(city["longitude"]), 4),
        "timezone": str(city.get("timezone") or "UTC"),
        "population_tier": population_tier(city.get("population")),
        "region": US_REGION_BY_STATE.get(admin1, "Provider Catalog"),
        "source": "geonamescache",
        "active": active,
        "notes": [
            "geonamescache_city",
            f"population:{int(city.get('population') or 0)}",
        ],
        "selection_classes": [],
        "place_archetypes": [],
        "collections": [],
        "geographic_hierarchy": [],
        "climate_sensory_tags": [],
        "interpretive_use_cases": [],
        "provider_metadata": {
            "provider": "geonamescache",
            "geoname_id": str(city.get("geonameid") or ""),
            "population": int(city.get("population") or 0),
        },
    }
    return validate_search_candidate(candidate)


def dedupe_candidates_by_location_id(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        item = validate_search_candidate(candidate)
        location_id = item["location_id"]
        current = by_id.get(location_id)
        if current is None:
            by_id[location_id] = item
            continue
        current_population = int((current.get("provider_metadata") or {}).get("population") or 0)
        item_population = int((item.get("provider_metadata") or {}).get("population") or 0)
        if item_population > current_population:
            by_id[location_id] = item
    return list(by_id.values())


def load_geonamescache_candidates(
    *,
    country_code: str = "US",
    min_population: int = 0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    try:
        import geonamescache
    except ImportError as exc:
        raise RuntimeError("geonamescache is not installed; provider bootstrap is unavailable.") from exc

    cache = geonamescache.GeonamesCache()
    candidates: list[dict[str, Any]] = []
    for city in cache.get_cities().values():
        if str(city.get("countrycode") or "").upper() != country_code.upper():
            continue
        try:
            if int(city.get("population") or 0) < min_population:
                continue
            candidates.append(geonamescache_city_to_candidate(city))
        except (TypeError, ValueError):
            continue
    candidates = dedupe_candidates_by_location_id(candidates)
    candidates.sort(
        key=lambda item: item.get("provider_metadata", {}).get("population", 0),
        reverse=True,
    )
    return candidates[:limit] if limit is not None else candidates


def iter_geonames_candidates(
    rows: Iterable[str],
    *,
    country_code: str = "US",
    min_population: int = 0,
    feature_class: str = "P",
) -> Iterable[dict[str, Any]]:
    for line in rows:
        if not line.strip():
            continue
        row = parse_geonames_row(line)
        if str(row["country_code"]).upper() != country_code.upper():
            continue
        if feature_class and row["feature_class"] != feature_class:
            continue
        if int(row.get("population") or 0) < min_population:
            continue
        yield geonames_row_to_candidate(row)


def load_geonames_candidates(
    path: str | Path,
    *,
    country_code: str = "US",
    min_population: int = 0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        candidates = list(
            iter_geonames_candidates(
                handle,
                country_code=country_code,
                min_population=min_population,
            )
        )
    candidates = dedupe_candidates_by_location_id(candidates)
    candidates.sort(
        key=lambda item: item.get("provider_metadata", {}).get("population", 0),
        reverse=True,
    )
    return candidates[:limit] if limit is not None else candidates
