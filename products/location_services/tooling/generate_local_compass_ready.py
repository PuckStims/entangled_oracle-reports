#!/usr/bin/env python3
"""
Generate a Local Compass HTML draft from birth data and an anchor location.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.natal_engine import generate_payload
from products.location_services.local_compass.renderer import (
    build_local_compass_html,
    write_local_compass_html,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Local Compass HTML draft.")
    parser.add_argument("--name", required=True, help="Querent name")
    parser.add_argument("--date", required=True, help="Birth date in YYYY-MM-DD")
    parser.add_argument("--time", required=False, help="Birth time in HH:MM or HH:MM:SS")
    parser.add_argument("--location", required=True, help="Birth location for the natal chart")
    parser.add_argument("--simple", action="store_true", help="Use simple mode when birth time is unknown")
    parser.add_argument("--anchor", required=True, help="Anchor place name (e.g., current home)")
    parser.add_argument("--destination", required=False, help="Optional destination place name")
    parser.add_argument("--route-waypoints", required=False, dest="route_waypoints", help="Optional route as 'lat,lon;lat,lon;...'.")
    parser.add_argument("--route-corridor-km", required=False, dest="route_corridor_km", type=float, default=150.0, help="Optional route corridor width in kilometers.")
    parser.add_argument("--route-id", required=False, dest="route_id", help="Optional route identifier.")
    parser.add_argument("--output-filename", dest="output_filename", help="Optional output HTML filename")
    return parser.parse_args()


def _parse_route_waypoints(value: str | None) -> list[dict] | None:
    if not value:
        return None
    waypoints: list[dict] = []
    for chunk in value.split(";"):
        text = chunk.strip()
        if not text:
            continue
        parts = [part.strip() for part in text.split(",")]
        if len(parts) != 2:
            raise ValueError("--route-waypoints must use 'lat,lon;lat,lon;...' format.")
        waypoints.append({"latitude": float(parts[0]), "longitude": float(parts[1])})
    if len(waypoints) < 2:
        raise ValueError("--route-waypoints requires at least two waypoint pairs.")
    return waypoints


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

    anchor = {"location": args.anchor, "display_name": args.anchor}
    destination = {"location": args.destination, "display_name": args.destination} if args.destination else None
    route_waypoints = _parse_route_waypoints(args.route_waypoints)
    route = None
    if route_waypoints:
        route = {
            "route_id": args.route_id or "cli-route",
            "corridor_width_km": args.route_corridor_km,
            "waypoints": route_waypoints,
        }

    html = build_local_compass_html(
        natal_payload,
        anchor,
        destination=destination,
        route=route,
    )
    output_path = write_local_compass_html(html, args.output_filename)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
