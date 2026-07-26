"""Compatibility routing facade for Location Services products."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import products.location_services  # noqa: F401 - imports plugins for registry side effects
from engine.location_services import resolve_destination_context
from products.location_services.registry import get_location_product, list_location_products


def is_location_report_type(report_type: str) -> bool:
    return report_type in set(list_location_products())


def location_report_window(report_type: str, birth_data: dict[str, Any]) -> tuple[datetime, datetime]:
    if birth_data.get("report_date"):
        start = datetime.strptime(birth_data["report_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start = datetime.now(timezone.utc)
    if birth_data.get("report_end_date"):
        end = datetime.strptime(birth_data["report_end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    elif report_type == "living_map":
        end = start + timedelta(days=30)
    else:
        end = start
    return start, end


def build_location_report_artifacts(report_type: str, payload: dict[str, Any], birth_data: dict[str, Any]) -> dict[str, Any]:
    product = get_location_product(report_type)
    purpose_lens = birth_data.get("purpose_lens")
    relationship_to_place = birth_data.get("relationship_to_place")

    if report_type == "place_resonance_search" and hasattr(product, "build_search_context"):
        context = product.build_search_context(
            payload,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )
    else:
        destination = _destination_from_birth_data(report_type, birth_data)
        context = product.build_context(
            payload,
            destination,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )
    html = product.render_html(context)
    return {
        "html": html,
        "context": context,
        "public_report_type": report_type,
    }


def _destination_from_birth_data(report_type: str, birth_data: dict[str, Any]) -> dict[str, Any]:
    name = birth_data.get("destination") or birth_data.get("anchor_location") or birth_data.get("current_location")
    if not name:
        raise ValueError(f"{report_type} requires a destination.")
    destination = resolve_destination_context({"location": name, "display_name": name})
    if birth_data.get("route"):
        destination["route"] = birth_data["route"]
    return destination
