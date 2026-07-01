"""
Offline place resolution for ordinary birthplace strings.

This module prefers packaged city data from geonamescache and determines
timezones locally with timezonefinder. It is designed to resolve common
consumer inputs such as "Peoria, IL" without requiring network access.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

try:
    import geonamescache
except ImportError:  # pragma: no cover - exercised in user env
    geonamescache = None

try:
    from timezonefinder import TimezoneFinder
except ImportError:  # pragma: no cover - exercised in user env
    TimezoneFinder = None


class LocationResolutionError(ValueError):
    """Base class for user-facing location resolution failures."""


class AmbiguousLocationError(LocationResolutionError):
    """Raised when more than one plausible place remains."""


class UnresolvedLocationError(LocationResolutionError):
    """Raised when a place cannot be found locally."""


US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

CANADA_PROVINCES = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba",
    "NB": "New Brunswick", "NL": "Newfoundland and Labrador", "NS": "Nova Scotia",
    "NT": "Northwest Territories", "NU": "Nunavut", "ON": "Ontario",
    "PE": "Prince Edward Island", "QC": "Quebec", "SK": "Saskatchewan",
    "YT": "Yukon",
}

AUSTRALIA_STATES = {
    "ACT": "Australian Capital Territory", "NSW": "New South Wales",
    "NT": "Northern Territory", "QLD": "Queensland", "SA": "South Australia",
    "TAS": "Tasmania", "VIC": "Victoria", "WA": "Western Australia",
}

UK_REGIONS = {
    "ENG": "England", "SCT": "Scotland", "WLS": "Wales", "NIR": "Northern Ireland",
}

IRELAND_COUNTIES = {
    "MAYO": "County Mayo",
}

COUNTRY_ALIAS_OVERRIDES = {
    "usa": "US",
    "us": "US",
    "u s a": "US",
    "u s": "US",
    "united states": "US",
    "united states of america": "US",
    "uk": "GB",
    "u k": "GB",
    "great britain": "GB",
    "britain": "GB",
    "united kingdom": "GB",
    "uae": "AE",
}

REGION_MAPS = {
    "US": US_STATES,
    "CA": CANADA_PROVINCES,
    "AU": AUSTRALIA_STATES,
    "GB": UK_REGIONS,
    "IE": IRELAND_COUNTIES,
}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.replace(".", " ")
    ascii_only = ascii_only.replace("-", " ")
    ascii_only = re.sub(r"\s*,\s*", ",", ascii_only)
    ascii_only = re.sub(r"\s+", " ", ascii_only)
    return ascii_only.strip().lower()


def _display_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _split_location(location_name: str) -> tuple[str, str | None, str | None]:
    cleaned = re.sub(r"\s+", " ", (location_name or "").replace(";", ",")).strip()
    cleaned = re.sub(r"\s*,\s*", ",", cleaned)
    parts = [_display_text(part) for part in cleaned.split(",") if part.strip()]

    if not parts:
        raise UnresolvedLocationError("Birth location is required.")

    city = parts[0]
    region = None
    country = None

    if len(parts) == 2:
        if _lookup_country_code(parts[1]):
            country = parts[1]
        else:
            region = parts[1]
    elif len(parts) >= 3:
        country = parts[-1] if _lookup_country_code(parts[-1]) else None
        if country:
            region = ", ".join(parts[1:-1]) or None
        else:
            region = ", ".join(parts[1:]) or None

    return city, region, country


def _lookup_country_code(country_text: str | None) -> str | None:
    if not country_text:
        return None
    world = _load_world_data()
    return world["country_alias_to_code"].get(_normalize_text(country_text))


def _lookup_region_codes(region_text: str | None, country_code: str | None) -> set[str]:
    if not region_text:
        return set()

    region_key = _normalize_text(region_text)
    world = _load_world_data()
    matches: set[str] = set()

    candidate_countries = [country_code] if country_code else list(world["region_alias_to_codes"])
    for candidate_country in candidate_countries:
        alias_map = world["region_alias_to_codes"].get(candidate_country, {})
        matches.update(alias_map.get(region_key, set()))

    return matches


def _region_matches(candidate: dict, region_text: str | None, country_code: str | None) -> bool:
    if not region_text:
        return True

    region_key = _normalize_text(region_text)
    admin1_code = _normalize_text(candidate.get("admin1code", ""))
    admin1_name = _normalize_text(candidate.get("admin1name", ""))
    if region_key and (region_key == admin1_code or region_key == admin1_name):
        return True

    codes = _lookup_region_codes(region_text, country_code or candidate.get("countrycode"))
    return candidate.get("admin1code") in codes


def _country_matches(candidate: dict, country_code: str | None) -> bool:
    return not country_code or candidate.get("countrycode") == country_code


def _sort_key(candidate: dict) -> tuple[int, int, int]:
    has_admin = 1 if candidate.get("admin1code") else 0
    population = int(candidate.get("population") or 0)
    geonameid = int(candidate.get("geonameid") or 0)
    return (has_admin, population, geonameid)


def _candidate_display_name(candidate: dict) -> str:
    country_name = candidate.get("countryname") or ""
    region_name = candidate.get("admin1name") or ""
    parts = [candidate.get("name") or ""]

    if region_name and _normalize_text(region_name) != _normalize_text(country_name):
        parts.append(region_name)

    if country_name:
        parts.append(country_name)

    return ", ".join(part for part in parts if part)


def _ambiguity_message(location_name: str, candidates: list[dict]) -> str:
    examples: list[str] = []
    for candidate in candidates[:3]:
        display_name = _candidate_display_name(candidate)
        if display_name not in examples:
            examples.append(display_name)

    if examples:
        example_text = " or ".join(f"\"{example}\"" for example in examples[:2])
        return (
            f"Could not uniquely resolve \"{location_name}\".\n"
            f"Please include a state/province or country, for example:\n"
            f"{example_text}."
        )

    return (
        f"Could not uniquely resolve \"{location_name}\".\n"
        "Please include a state/province or country."
    )


def resolve_timezone(latitude: float, longitude: float) -> str:
    if TimezoneFinder is None:
        raise UnresolvedLocationError(
            "Offline timezone resolution is unavailable because timezonefinder is not installed."
        )

    finder = TimezoneFinder()
    timezone_name = finder.timezone_at(lat=latitude, lng=longitude)
    if not timezone_name and hasattr(finder, "closest_timezone_at"):
        timezone_name = finder.closest_timezone_at(lat=latitude, lng=longitude)
    return timezone_name or "UTC"


@lru_cache(maxsize=1)
def _load_world_data() -> dict:
    if geonamescache is None:
        raise UnresolvedLocationError(
            "Offline place resolution is unavailable because geonamescache is not installed."
        )

    cache = geonamescache.GeonamesCache()
    countries = cache.get_countries()
    cities = cache.get_cities()

    country_alias_to_code: dict[str, str] = {}
    country_names_by_code: dict[str, str] = {}

    for country_code, country_data in countries.items():
        country_name = country_data.get("name", country_code)
        country_names_by_code[country_code] = country_name

        aliases = {
            _normalize_text(country_name),
            _normalize_text(country_code),
            _normalize_text(country_data.get("iso3", "")),
        }
        aliases.update(
            _normalize_text(alias)
            for alias, alias_code in COUNTRY_ALIAS_OVERRIDES.items()
            if alias_code == country_code
        )

        for alias in aliases:
            if alias:
                country_alias_to_code[alias] = country_code

    region_alias_to_codes: dict[str, dict[str, set[str]]] = {}
    region_names_by_country_code: dict[str, dict[str, str]] = {}

    for country_code, region_map in REGION_MAPS.items():
        alias_map: dict[str, set[str]] = {}
        name_map: dict[str, str] = {}
        for code, name in region_map.items():
            code_key = _normalize_text(code)
            name_key = _normalize_text(name)
            alias_map.setdefault(code_key, set()).add(code)
            alias_map.setdefault(name_key, set()).add(code)
            if name_key.startswith("county "):
                alias_map.setdefault(name_key.replace("county ", "", 1), set()).add(code)
            name_map[code] = name
        region_alias_to_codes[country_code] = alias_map
        region_names_by_country_code[country_code] = name_map

    normalized_city_index: dict[str, list[dict]] = {}

    for city_data in cities.values():
        city_name = city_data.get("name")
        country_code = city_data.get("countrycode")
        if not city_name or not country_code:
            continue

        candidate = {
            "geonameid": city_data.get("geonameid"),
            "name": city_name,
            "latitude": float(city_data.get("latitude")),
            "longitude": float(city_data.get("longitude")),
            "population": int(city_data.get("population") or 0),
            "countrycode": country_code,
            "countryname": country_names_by_code.get(country_code, country_code),
            "admin1code": city_data.get("admin1code") or "",
            "admin1name": "",
        }

        region_name = region_names_by_country_code.get(country_code, {}).get(candidate["admin1code"])
        if region_name:
            candidate["admin1name"] = region_name

        city_key = _normalize_text(city_name)
        normalized_city_index.setdefault(city_key, []).append(candidate)

    return {
        "country_alias_to_code": country_alias_to_code,
        "normalized_city_index": normalized_city_index,
        "region_alias_to_codes": region_alias_to_codes,
    }


def resolve_place(location_name: str) -> dict:
    """Resolves a human-readable place name using packaged local data only."""
    if not location_name or not str(location_name).strip():
        raise UnresolvedLocationError("Birth location is required.")

    city_text, region_text, country_text = _split_location(location_name)
    country_code = _lookup_country_code(country_text)

    world = _load_world_data()
    city_key = _normalize_text(city_text)
    candidates = list(world["normalized_city_index"].get(city_key, []))

    if not candidates:
        raise UnresolvedLocationError(
            f"Could not resolve location \"{location_name}\" offline. "
            "Please include a fuller city/state/country format."
        )

    country_filtered = [
        candidate for candidate in candidates
        if _country_matches(candidate, country_code)
    ]
    if not country_filtered:
        raise UnresolvedLocationError(
            f"Could not resolve location \"{location_name}\" offline. "
            "Please include a fuller city/state/country format."
        )

    if region_text:
        region_filtered = [
            candidate for candidate in country_filtered
            if _region_matches(candidate, region_text, country_code)
        ]
        candidates = region_filtered or country_filtered
    else:
        candidates = country_filtered

    candidates.sort(key=_sort_key, reverse=True)

    unique_places = {
        (
            _normalize_text(candidate["name"]),
            candidate.get("admin1code", ""),
            candidate.get("countrycode", ""),
        )
        for candidate in candidates
    }

    if len(unique_places) > 1:
        raise AmbiguousLocationError(_ambiguity_message(location_name, candidates))

    winner = candidates[0]
    timezone_name = resolve_timezone(winner["latitude"], winner["longitude"])

    return {
        "display_name": _candidate_display_name(winner),
        "latitude": round(winner["latitude"], 4),
        "longitude": round(winner["longitude"], 4),
        "timezone": timezone_name,
        "source": "offline_geonamescache",
    }
