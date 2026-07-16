#!/usr/bin/env python3
"""
Generate a Living Map HTML draft from birth data and an anchor location.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.natal_engine import generate_payload
from products.location_services.living_map.renderer import (
    build_living_map_html,
    write_living_map_html,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Living Map HTML draft.")
    parser.add_argument("--name", required=True, help="Querent name")
    parser.add_argument("--date", required=True, help="Birth date in YYYY-MM-DD")
    parser.add_argument("--time", required=False, help="Birth time in HH:MM or HH:MM:SS")
    parser.add_argument("--location", required=True, help="Birth location for the natal chart")
    parser.add_argument("--simple", action="store_true", help="Use simple mode when birth time is unknown")
    parser.add_argument("--destination", required=True, help="Destination place name")
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
    
    html = build_living_map_html(
        natal_payload,
        {"location": args.destination, "display_name": args.destination},
    )
    output_path = write_living_map_html(html, args.output_filename)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
