#!/usr/bin/env python3
"""
Import a provider place dump into the local Place Resonance Search catalog.

Example:
  python products/location_services/tooling/import_location_catalog.py \
    --geonames-path C:/data/geonames/cities500.txt --min-population 5000 --limit 5000
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from products.location_services.place_resonance_search.providers.geonames_importer import (
    load_geonamescache_candidates,
    load_geonames_candidates,
)
from products.location_services.place_resonance_search.providers.location_catalog import (
    upsert_location_candidates,
)


DEFAULT_DB_PATH = (
    PROJECT_ROOT
    / "products"
    / "location_services"
    / "place_resonance_search"
    / "data"
    / "location_catalog.sqlite"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import GeoNames places into the Search location catalog.")
    parser.add_argument("--geonames-path", help="Path to a GeoNames tab-delimited dump file.")
    parser.add_argument("--from-geonamescache", action="store_true", help="Import from the installed geonamescache package.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Output SQLite catalog path.")
    parser.add_argument("--country", default="US", help="ISO country code to import.")
    parser.add_argument("--min-population", type=int, default=0, help="Minimum provider population.")
    parser.add_argument("--limit", type=int, help="Optional maximum imported rows after population sorting.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.from_geonamescache:
        candidates = load_geonamescache_candidates(
            country_code=args.country,
            min_population=args.min_population,
            limit=args.limit,
        )
    elif args.geonames_path:
        candidates = load_geonames_candidates(
            args.geonames_path,
            country_code=args.country,
            min_population=args.min_population,
            limit=args.limit,
        )
    else:
        raise SystemExit("Provide --geonames-path or --from-geonamescache.")
    count = upsert_location_candidates(args.db_path, candidates)
    print(f"Imported {count} {args.country.upper()} provider locations into {args.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
