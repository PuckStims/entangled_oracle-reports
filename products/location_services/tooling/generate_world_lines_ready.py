#!/usr/bin/env python3
"""
Generate a World Lines Companion HTML draft from birth data and one destination.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.natal_engine import generate_payload
from products.location_services.world_lines_companion.renderer import (
    build_world_lines_html,
    write_world_lines_html,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a World Lines Companion HTML draft.")
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
    
    html = build_world_lines_html(
        natal_payload,
        {"location": args.destination},
    )
    output_path = write_world_lines_html(html, args.output_filename)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
