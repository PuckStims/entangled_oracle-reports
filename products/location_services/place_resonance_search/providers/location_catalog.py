"""
Local provider catalog store for Place Resonance Search.

This module keeps the large place universe separate from the curated Search
fixture. Provider rows can be imported into SQLite, queried by broad filters,
then merged with curated EO overrides before scoring.
"""
from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from products.location_services.place_resonance_search.candidate_catalog import (
    OPTIONAL_ONTOLOGY_FIELDS,
    validate_candidate_catalog,
    validate_search_candidate,
)


CATALOG_SCHEMA_VERSION = "place_resonance_location_catalog_v0.1.0"


def _connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(path))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_location_catalog(path: str | Path) -> None:
    with _connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                location_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                country TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timezone TEXT NOT NULL,
                population INTEGER NOT NULL DEFAULT 0,
                population_tier TEXT NOT NULL,
                region TEXT NOT NULL,
                source TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_locations_country_state ON locations(country, state)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_locations_population ON locations(population DESC)")


def count_location_candidates(path: str | Path) -> int:
    initialize_location_catalog(path)
    with _connect(path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM locations").fetchone()
    return int(row["count"] if row else 0)


def _candidate_population(candidate: dict[str, Any]) -> int:
    metadata = candidate.get("provider_metadata")
    if isinstance(metadata, dict):
        try:
            return int(metadata.get("population") or 0)
        except (TypeError, ValueError):
            return 0
    for note in candidate.get("notes") or []:
        if isinstance(note, str) and note.startswith("population:"):
            try:
                return int(note.split(":", 1)[1])
            except ValueError:
                return 0
    return 0


def upsert_location_candidates(path: str | Path, candidates: Iterable[dict[str, Any]]) -> int:
    initialize_location_catalog(path)
    normalized = validate_candidate_catalog(list(candidates))
    with _connect(path) as connection:
        connection.executemany(
            """
            INSERT INTO locations (
                location_id, display_name, city, state, country, latitude,
                longitude, timezone, population, population_tier, region,
                source, active, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(location_id) DO UPDATE SET
                display_name=excluded.display_name,
                city=excluded.city,
                state=excluded.state,
                country=excluded.country,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                timezone=excluded.timezone,
                population=excluded.population,
                population_tier=excluded.population_tier,
                region=excluded.region,
                source=excluded.source,
                active=excluded.active,
                payload_json=excluded.payload_json
            """,
            [
                (
                    item["location_id"],
                    item["display_name"],
                    item["city"],
                    item["state"],
                    item["country"],
                    float(item["latitude"]),
                    float(item["longitude"]),
                    item["timezone"],
                    _candidate_population(item),
                    item["population_tier"],
                    item["region"],
                    item["source"],
                    1 if item["active"] else 0,
                    json.dumps(item, sort_keys=True),
                )
                for item in normalized
            ],
        )
    return len(normalized)


def query_location_candidates(
    path: str | Path,
    *,
    country: str = "US",
    states: Iterable[str] | None = None,
    min_population: int = 0,
    active_only: bool = True,
    limit: int = 500,
) -> list[dict[str, Any]]:
    initialize_location_catalog(path)
    clauses = ["country = ?", "population >= ?"]
    params: list[Any] = [country, int(min_population)]

    state_values = [str(state).upper() for state in states or [] if str(state).strip()]
    if state_values:
        clauses.append(f"state IN ({','.join('?' for _ in state_values)})")
        params.extend(state_values)
    if active_only:
        clauses.append("active = 1")

    sql = (
        "SELECT payload_json FROM locations WHERE "
        + " AND ".join(clauses)
        + " ORDER BY population DESC, display_name ASC LIMIT ?"
    )
    params.append(int(limit))

    with _connect(path) as connection:
        rows = connection.execute(sql, params).fetchall()
    if not rows:
        return []
    return validate_candidate_catalog([json.loads(row["payload_json"]) for row in rows])


def merge_curated_overlays(
    provider_candidates: Iterable[dict[str, Any]],
    curated_candidates: Iterable[dict[str, Any]],
    *,
    include_curated_only: bool = True,
) -> list[dict[str, Any]]:
    """
    Merge broad provider candidates with EO curated candidate overlays.

    Matching `location_id` entries are deep-merged with curated values winning.
    Curated-only entries are kept by default so hand-selected anchors remain
    available even if a provider import is filtered narrowly.
    """
    merged: dict[str, dict[str, Any]] = {
        item["location_id"]: copy.deepcopy(item)
        for item in validate_candidate_catalog(list(provider_candidates))
    }
    for overlay in validate_candidate_catalog(list(curated_candidates)):
        location_id = overlay["location_id"]
        if location_id not in merged:
            if include_curated_only:
                merged[location_id] = copy.deepcopy(overlay)
            continue
        combined = copy.deepcopy(merged[location_id])
        combined.update(copy.deepcopy(overlay))
        for field in OPTIONAL_ONTOLOGY_FIELDS:
            if overlay.get(field):
                combined[field] = copy.deepcopy(overlay[field])
        notes = []
        for note in [*(merged[location_id].get("notes") or []), *(overlay.get("notes") or [])]:
            if note not in notes:
                notes.append(note)
        combined["notes"] = notes
        merged[location_id] = combined

    return validate_candidate_catalog(list(merged.values()))
