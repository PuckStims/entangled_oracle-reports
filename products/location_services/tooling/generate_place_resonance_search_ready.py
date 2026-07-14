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
    candidates = load_candidate_catalog(args.candidate_catalog) if args.candidate_catalog else None
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
