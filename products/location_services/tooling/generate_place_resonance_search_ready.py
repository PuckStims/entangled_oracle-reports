#!/usr/bin/env python3
"""
Generate a Place Resonance Search HTML draft from birth data and a candidate pool.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.natal_engine import generate_payload
from products.location_services.place_resonance_search.candidate_catalog import load_candidate_catalog
from products.location_services.place_resonance_search.providers.geonames_importer import (
    load_geonamescache_candidates,
)
from products.location_services.place_resonance_search.providers.location_catalog import (
    count_location_candidates,
    merge_curated_overlays,
    query_location_candidates,
    upsert_location_candidates,
)
from products.location_services.place_resonance_search.renderer import (
    build_place_resonance_search_results_html,
    write_place_resonance_search_html,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Place Resonance Search HTML draft.")
    parser.add_argument("--name", required=True, help="Querent name")
    parser.add_argument("--date", required=True, help="Birth date in YYYY-MM-DD")
    parser.add_argument("--time", required=False, help="Birth time in HH:MM or HH:MM:SS")
    parser.add_argument("--location", required=True, help="Birth location for the natal chart")
    parser.add_argument("--simple", action="store_true", help="Use simple mode when birth time is unknown")
    parser.add_argument("--candidate-catalog", dest="candidate_catalog", help="Optional candidate catalog JSON path")
    parser.add_argument("--location-catalog-db", dest="location_catalog_db", help="Optional provider SQLite catalog path")
    parser.add_argument("--country", default="US", help="Country code for provider catalog queries")
    parser.add_argument("--states", help="Comma-separated state codes for provider catalog queries")
    parser.add_argument("--min-population", dest="min_population", type=int, default=0, help="Minimum provider population")
    parser.add_argument("--candidate-limit", dest="candidate_limit", type=int, default=500, help="Maximum provider candidates")
    parser.add_argument(
        "--no-curated-overlay",
        dest="curated_overlay",
        action="store_false",
        default=True,
        help="Do not merge the curated fixture over provider catalog candidates",
    )
    parser.add_argument("--selection-limit", dest="selection_limit", type=int, default=20, help="Maximum selected locations")
    parser.add_argument("--purpose-lens", dest="purpose_lens", help="Optional Place Resonance Search purpose lens")
    parser.add_argument(
        "--relationship-to-place",
        dest="relationship_to_place",
        help="Optional relationship label such as possible_move, travel, or remote_connection",
    )
    parser.add_argument("--output-filename", dest="output_filename", help="Optional output HTML filename")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    birth_data = {
        "name": args.name,
        "date": args.date,
        "time": None if args.simple or not args.time else args.time,
        "location": args.location,
        "simple_mode": bool(args.simple or not args.time),
    }
    natal_payload = generate_payload(birth_data)
    candidates = None
    if args.location_catalog_db:
        states = [state.strip().upper() for state in (args.states or "").split(",") if state.strip()]
        if count_location_candidates(args.location_catalog_db) == 0:
            bootstrap_candidates = load_geonamescache_candidates(
                country_code=args.country,
                min_population=args.min_population,
            )
            imported_count = upsert_location_candidates(args.location_catalog_db, bootstrap_candidates)
            print(f"[Search] Bootstrapped {imported_count} provider locations from geonamescache.")
        provider_candidates = query_location_candidates(
            args.location_catalog_db,
            country=args.country,
            states=states,
            min_population=args.min_population,
            limit=args.candidate_limit,
        )
        if args.curated_overlay:
            curated = load_candidate_catalog(args.candidate_catalog) if args.candidate_catalog else load_candidate_catalog()
            candidates = merge_curated_overlays(provider_candidates, curated)
        else:
            candidates = provider_candidates
    elif args.candidate_catalog:
        candidates = load_candidate_catalog(args.candidate_catalog)
    html = build_place_resonance_search_results_html(
        natal_payload,
        candidates,
        purpose_lens=args.purpose_lens,
        relationship_to_place=args.relationship_to_place,
        selection_limit=args.selection_limit,
    )
    output_path = write_place_resonance_search_html(html, args.output_filename)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
