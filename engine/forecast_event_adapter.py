"""Add the canonical ForecastEvent contract to legacy forecast dictionaries.

The adapter is deliberately additive: existing keys remain available to current
report builders while canonical keys provide a stable evidence contract for
later serializers and synthesis work.  It does not promote visibility or
invent method evidence that a scanner did not calculate.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


UTC = timezone.utc
SCHEMA_VERSION = "phase0.1.0"
INTERNAL_ONLY_VISIBILITY = ["internal_rd"]
_CONFIDENCE_COMPONENT_KEYS = (
    "exactness_support",
    "angle_support",
    "calculation_integrity",
    "target_uncertainty",
    "birth_time_state",
    "method_maturity",
)


def _ensure_utc(value: Any) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _clamp(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)]


def _generate_event_id(
    method_family: str,
    method_variant: str,
    peak_at: datetime | None,
    source_body: str,
    target_body: str,
    aspect: str,
) -> str:
    peak_string = peak_at.isoformat() if peak_at else "unknown"
    basis = "|".join(
        (method_family, method_variant, peak_string, source_body, target_body, aspect)
    ).encode("utf-8")
    return f"fe_{method_family.lower()}_{hashlib.sha256(basis).hexdigest()[:8]}"


def _infer_body_kind(name: str) -> str | None:
    normalized = name.strip().lower().replace(" ", "_")
    if not normalized:
        return None
    if normalized in {"sun", "moon"}:
        return "luminary"
    if normalized in {
        "asc", "ascendant", "mc", "midheaven", "dsc", "descendant",
        "ic", "imum_coeli", "vertex",
    }:
        return "angle"
    if normalized in {
        "mercury", "venus", "mars", "jupiter", "saturn", "uranus",
        "neptune", "pluto",
    }:
        return "planet"
    if "lot_of_" in normalized:
        return "lot"
    if "node" in normalized or normalized in {"lilith_bml", "black_moon_lilith"}:
        return "node"
    return "asteroid"


def _method_fields(raw: dict[str, Any], event_type: str) -> tuple[str, str, str]:
    family = str(raw.get("method_family") or "").upper()
    variant = str(raw.get("method_variant") or "")
    independence = str(raw.get("independence_group") or "")
    if family and variant and independence:
        return family, variant, independence

    mappings = {
        "transit": ("TRANSIT", "transit_cycle", "transit_family"),
        "ingress": ("TRANSIT", "ingress", "transit_family"),
        "station": ("TRANSIT", "station", "transit_family"),
        "eclipse": ("LUNATION", "eclipse", "lunation_family"),
        "lunation": ("LUNATION", "plain_lunation", "lunation_family"),
        "progression": ("PROGRESSION", "progression_body_aspect", "progression_family"),
        "solar_arc": ("SOLAR_ARC", "solar_arc_body_aspect", "solar_arc_family"),
        "return": ("RETURN", "exact_return", "return_family"),
        "zodiacal_releasing": (
            "ZODIACAL_RELEASING", "zr_transition", "zodiacal_releasing_family"
        ),
    }
    mapped_family, mapped_variant, mapped_independence = mappings.get(
        event_type, ("UNKNOWN", event_type or "unknown", "unknown_family")
    )
    return (
        family or mapped_family,
        variant or mapped_variant,
        independence or mapped_independence,
    )


def _exact_moments(raw: dict[str, Any]) -> list[datetime]:
    moments: list[datetime] = []
    for value in raw.get("exact_datetimes") or []:
        moment = _ensure_utc(value)
        if moment is not None:
            moments.append(moment)
    for contact in raw.get("contacts") or []:
        if not isinstance(contact, dict):
            continue
        moment = _ensure_utc(
            contact.get("contact_datetime")
            or contact.get("exact_datetime")
            or contact.get("peak_datetime")
        )
        if moment is not None:
            moments.append(moment)
    return sorted(set(moments))


def _confidence_fields(raw: dict[str, Any], missing: list[str]) -> tuple[float, dict[str, float]]:
    raw_components = raw.get("confidence_components")
    components = dict(raw_components) if isinstance(raw_components, dict) else {}
    exactness = _clamp(raw.get("exactness"), 0.0)
    normalized = {
        "exactness_support": _clamp(components.get("exactness_support"), exactness),
        "angle_support": _clamp(components.get("angle_support"), 0.0),
        "calculation_integrity": _clamp(components.get("calculation_integrity"), 0.0),
        "target_uncertainty": _clamp(components.get("target_uncertainty"), 0.0),
        "birth_time_state": _clamp(components.get("birth_time_state"), 0.0),
        "method_maturity": _clamp(components.get("method_maturity"), 0.0),
    }
    if "confidence" not in raw:
        missing.append("confidence")
    if not isinstance(raw_components, dict):
        missing.append("confidence_components")
    return _clamp(raw.get("confidence"), 0.0), normalized


def normalize_to_forecast_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    """Return an additive, schema-shaped copy of ``raw_event``.

    Missing calculation evidence is recorded in ``calculation_trace`` and
    receives conservative values.  In particular, the adapter never supplies
    a synthetic zero orb merely to make an event appear exact.
    """
    enriched = dict(raw_event)
    missing_fields: list[str] = []
    event_type = str(raw_event.get("event_type") or "").strip().lower()
    method_family, method_variant, independence_group = _method_fields(
        raw_event, event_type
    )

    source_body = str(
        raw_event.get("source_body")
        or raw_event.get("transit_planet")
        or raw_event.get("return_body")
        or ""
    )
    target_body = str(
        raw_event.get("target_body")
        or raw_event.get("natal_target")
        or raw_event.get("natal_contact")
        or ""
    )
    aspect = str(raw_event.get("aspect") or "")

    peak_at = _ensure_utc(raw_event.get("peak_at") or raw_event.get("peak_datetime"))
    start_at = _ensure_utc(
        raw_event.get("start_at")
        or raw_event.get("entry_datetime")
        or raw_event.get("cycle_start_datetime")
    )
    end_at = _ensure_utc(
        raw_event.get("end_at")
        or raw_event.get("leave_datetime")
        or raw_event.get("cycle_end_datetime")
    )
    if peak_at is not None:
        start_at = start_at or peak_at
        end_at = end_at or peak_at
    for field_name, value in (("start_at", start_at), ("peak_at", peak_at), ("end_at", end_at)):
        if value is None:
            missing_fields.append(field_name)

    orb = raw_event.get("orb", raw_event.get("peak_orb"))
    distance = raw_event.get("distance")
    phase = raw_event.get("phase") or raw_event.get("station_type") or raw_event.get("eclipse_type")
    if orb is None and distance is None and phase is None:
        missing_fields.append("orb_or_distance_or_phase")

    strength = _clamp(
        raw_event.get(
            "event_strength",
            raw_event.get(
                "combined_intensity_score",
                raw_event.get("reader_facing_activity_score", raw_event.get("score", raw_event.get("raw_score", 0.0))),
            ),
        )
    )
    confidence, confidence_components = _confidence_fields(raw_event, missing_fields)

    source_kind = str(raw_event.get("source_kind") or _infer_body_kind(source_body) or "") or None
    target_kind = str(raw_event.get("target_kind") or _infer_body_kind(target_body) or "") or None
    asteroid_participants = _as_string_list(raw_event.get("asteroid_participants"))
    for body, kind in ((source_body, source_kind), (target_body, target_kind)):
        if body and kind == "asteroid" and body not in asteroid_participants:
            asteroid_participants.append(body)

    activation_route = str(raw_event.get("activation_route") or "")
    if not activation_route:
        prefix = {
            "TRANSIT": "transit",
            "PROGRESSION": "progression",
            "SOLAR_ARC": "solar_arc",
        }.get(method_family)
        if prefix:
            suffix = "angle" if target_kind == "angle" else "asteroid" if target_kind == "asteroid" else "body"
            activation_route = f"{prefix}_to_{suffix}"
        elif method_family == "RETURN":
            activation_route = "return_moment"
        elif method_family == "ZODIACAL_RELEASING":
            activation_route = "zr_period_transition"
        else:
            activation_route = "unknown"
            missing_fields.append("activation_route")

    visibility = raw_event.get("report_surface_visibility")
    if visibility is None:
        visibility = list(INTERNAL_ONLY_VISIBILITY)
        missing_fields.append("report_surface_visibility")
    else:
        visibility = _as_string_list(visibility)

    trace = dict(raw_event.get("calculation_trace") or {})
    prior_missing = _as_string_list(trace.get("missing_fields"))
    trace["missing_fields"] = sorted(set(prior_missing + missing_fields))
    if "formula_version" in raw_event:
        trace.setdefault("formula_version", raw_event["formula_version"])

    provenance = dict(raw_event.get("provenance") or {})
    provenance.setdefault("scanner", f"engine.{event_type or 'unknown'}")
    provenance.setdefault("scanner_version", str(raw_event.get("formula_version") or "unknown"))
    # Keep regeneration deterministic when the scanner has not supplied an
    # emission timestamp. The event peak is the nearest reproducible value.
    provenance.setdefault("emitted_at", peak_at.isoformat() if peak_at else "unknown")

    duration_days = 0.0
    if start_at is not None and end_at is not None:
        duration_days = max(0.0, (end_at - start_at).total_seconds() / 86400.0)
    precision = (
        "instant" if duration_days == 0
        else "day" if duration_days <= 2
        else "week" if duration_days <= 14
        else "month" if duration_days <= 60
        else "season" if duration_days <= 180
        else "year_or_longer"
    )

    enriched.update(
        {
            "schema_version": SCHEMA_VERSION,
            "event_id": raw_event.get("event_id") or _generate_event_id(
                method_family, method_variant, peak_at, source_body, target_body, aspect
            ),
            "method_family": method_family,
            "method_variant": method_variant,
            "clock_role": raw_event.get("clock_role") or "modifier",
            "source_body": source_body,
            "source_kind": source_kind,
            "target_body": target_body or None,
            "target_kind": target_kind,
            "natal_anchor_ids": _as_string_list(raw_event.get("natal_anchor_ids")),
            "topic_keys": _as_string_list(raw_event.get("topic_keys", raw_event.get("shared_life_domains"))),
            "domain_keys": _as_string_list(raw_event.get("domain_keys")),
            "start_at": start_at,
            "peak_at": peak_at,
            "end_at": end_at,
            "exact_at": _exact_moments(raw_event),
            "orb": orb,
            "distance": distance,
            "phase": phase,
            "event_strength": strength,
            "strength_components": {
                "exactness": _clamp(raw_event.get("exactness"), 0.0),
                "event_weight": _clamp(raw_event.get("event_weight"), 0.0),
                "target_relevance": _clamp(raw_event.get("target_relevance", raw_event.get("natal_relevance")), 0.0),
                "structural_importance": _clamp(raw_event.get("structural_importance"), 0.0),
                "theme_convergence": _clamp(raw_event.get("theme_convergence"), 0.0),
                "method_multiplier": _clamp(raw_event.get("method_multiplier"), 0.0),
                "asteroid_specificity": _clamp(raw_event.get("asteroid_specificity"), 0.0),
            },
            "temporal_precision": raw_event.get("temporal_precision") or precision,
            "independence_group": independence_group,
            "activation_route": activation_route,
            "asteroid_participants": asteroid_participants,
            "confidence": confidence,
            "confidence_components": confidence_components,
            "calculation_trace": trace,
            "report_surface_visibility": visibility,
            "provenance": provenance,
        }
    )
    return enriched
