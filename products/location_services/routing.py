"""
Routing helpers for the Location Services product family.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from products.location_services.registry import get_location_product


LOCATION_REPORT_TYPE_MAP = {
    "place_resonance": "location_services.place_resonance",
    "place_resonance_search": "location_services.place_resonance_search",
    "between_places": "location_services.between_places",
    "world_lines": "location_services.world_lines",
    "local_compass": "location_services.local_compass",
    "living_map": "location_services.living_map",
}

LOCATION_REPORT_TYPE_ALIASES = {
    **LOCATION_REPORT_TYPE_MAP,
    **{value: key for key, value in LOCATION_REPORT_TYPE_MAP.items()},
}


def is_location_report_type(report_type: str) -> bool:
    return report_type in LOCATION_REPORT_TYPE_ALIASES


def resolve_location_report_type(report_type: str) -> str:
    if report_type in LOCATION_REPORT_TYPE_MAP:
        return LOCATION_REPORT_TYPE_MAP[report_type]
    if report_type in LOCATION_REPORT_TYPE_ALIASES:
        public_key = LOCATION_REPORT_TYPE_ALIASES[report_type]
        return LOCATION_REPORT_TYPE_MAP[public_key]
    raise ValueError(f"Unknown location report type: {report_type}")


def public_location_report_type(report_type: str) -> str:
    if report_type in LOCATION_REPORT_TYPE_MAP:
        return report_type
    if report_type in LOCATION_REPORT_TYPE_ALIASES:
        return LOCATION_REPORT_TYPE_ALIASES[report_type]
    raise ValueError(f"Unknown location report type: {report_type}")


def location_report_window(report_type: str, birth_data: dict[str, Any]) -> tuple[datetime, datetime]:
    if birth_data.get("report_date"):
        report_start = datetime.strptime(birth_data["report_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        report_start = datetime.now(timezone.utc)
    if public_location_report_type(report_type) == "living_map":
        if birth_data.get("report_end_date"):
            report_end = datetime.strptime(birth_data["report_end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            report_end = report_start + timedelta(days=365)
        return report_start, report_end
    return report_start, report_start


def build_location_report_artifacts(
    report_type: str,
    natal_payload: dict[str, Any],
    birth_data: dict[str, Any],
) -> dict[str, Any]:
    full_report_type = resolve_location_report_type(report_type)
    public_report_type = public_location_report_type(report_type)
    product = get_location_product(full_report_type)
    purpose_lens = birth_data.get("purpose_lens")
    relationship_to_place = birth_data.get("relationship_to_place")

    if public_report_type == "place_resonance_search":
        context = product.build_search_context(
            natal_payload,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
            selection_limit=int(birth_data.get("selection_limit") or 20),
        )
    elif public_report_type == "between_places":
        destination_a = _destination_dict(
            birth_data.get("destination_a") or birth_data.get("destination") or birth_data.get("current_location") or birth_data.get("location")
        )
        destination_b_value = birth_data.get("destination_b")
        if not destination_b_value:
            raise ValueError("Between Places requires destination_b.")
        destination_b = _destination_dict(destination_b_value)
        context = product.build_context(
            natal_payload,
            destination_a,
            destination_b,
            purpose_lens=purpose_lens,
        )
    elif public_report_type == "local_compass":
        anchor = _destination_dict(
            birth_data.get("anchor_location") or birth_data.get("current_location") or birth_data.get("location")
        )
        destination_value = birth_data.get("destination")
        destination = _destination_dict(destination_value) if destination_value else None
        context = product.build_context(
            natal_payload,
            anchor,
            destination=destination,
            route=birth_data.get("route"),
            purpose_lens=purpose_lens,
        )
    elif public_report_type == "living_map":
        destination = _destination_dict(
            birth_data.get("destination") or birth_data.get("current_location") or birth_data.get("location")
        )
        context = product.build_context(
            natal_payload,
            destination,
            purpose_lens=purpose_lens,
            start_date=birth_data.get("report_date"),
            end_date=birth_data.get("report_end_date"),
        )
    else:
        destination = _destination_dict(
            birth_data.get("destination") or birth_data.get("current_location") or birth_data.get("location")
        )
        build_kwargs = {"purpose_lens": purpose_lens}
        if public_report_type == "place_resonance":
            build_kwargs["relationship_to_place"] = relationship_to_place
        context = product.build_context(natal_payload, destination, **build_kwargs)

    html = product.render_html(context)
    return {
        "public_report_type": public_report_type,
        "full_report_type": full_report_type,
        "context": context,
        "html": html,
    }


def _destination_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = str(value or "").strip()
    return {"location": text, "display_name": text}
