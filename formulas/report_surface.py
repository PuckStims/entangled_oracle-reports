"""
Internal layer-aware routing bundle for standard, established-niche, and EO outputs.
"""

from __future__ import annotations

from typing import Any, Callable

from formulas.established_niche import evaluate_selected_specialist_bodies
from formulas.governance_registry import (
    METHOD_STATUS_CORE_STANDARD,
    METHOD_STATUS_EO_PROPRIETARY,
    get_method_registry_record,
    get_report_layer_profile,
    layer_allows,
)
from formulas.standard.aspect_architecture import evaluate_aspect_architecture
from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.chart_structure import evaluate_chart_structure
from formulas.standard.forecast_activation import build_forecast_activation_profile
from formulas.standard.house_emphasis import evaluate_house_emphasis
from formulas.standard.named_configurations import evaluate_named_configurations
from formulas.standard.natal_convergence import evaluate_standard_natal_convergence
from formulas.standard.planetary_condition import evaluate_all_planetary_conditions
from formulas.standard.planetary_prominence import evaluate_prominence
from formulas.standard.rulership_network import evaluate_rulership_network

ROUTING_STATES = (
    "headline_section",
    "supporting_context",
    "modifier",
    "reference_table",
    "technical_appendix",
    "forecast_cross_reference",
    "held_for_eo_synthesis",
    "internal_trace_only",
    "suppressed",
)

CORE_CATEGORY_KEYS = (
    "chart_orientation",
    "planetary_conditions",
    "planetary_prominence",
    "chart_ruler",
    "house_emphasis",
    "luminary_structure",
    "aspect_architecture",
    "rulership_and_dispositors",
    "named_configurations",
    "natal_convergence",
    "forecast_natal_priority",
)


def _tag_proprietary_result(index_key: str, result: dict[str, Any], report_profile: str) -> dict[str, Any]:
    tagged = dict(result)
    tagged.setdefault("method_status", METHOD_STATUS_EO_PROPRIETARY)
    tagged.setdefault("report_eligibility", report_profile)
    tagged.setdefault("visibility_state", "eo_overlay_only")
    tagged.setdefault("method_name", get_method_registry_record(index_key).display_name if get_method_registry_record(index_key) else index_key)
    tagged.setdefault("routing_state", "held_for_eo_synthesis")
    return tagged


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def _methodology_from_payload(payload: dict) -> dict[str, Any]:
    profile = payload.get("user_profile", {}) if isinstance(payload, dict) else {}
    methodology = profile.get("methodology", {}) if isinstance(profile, dict) else {}
    return {
        "id": methodology.get("id") or profile.get("methodology_id") or "tropical_whole",
        "label": methodology.get("label") or profile.get("methodology_label") or "Tropical zodiac + Whole Sign houses",
        "zodiac": methodology.get("zodiac") or profile.get("zodiac") or "Tropical",
        "house_system": methodology.get("house_system") or profile.get("house_system") or "Whole Sign",
    }


def _birth_time_confidence(payload: dict) -> str:
    profile = payload.get("user_profile", {}) if isinstance(payload, dict) else {}
    return str(
        profile.get("birth_time_state")
        or profile.get("birth_time_confidence")
        or ("unknown" if bool(payload.get("simple_mode") or profile.get("simple_mode")) else "exact")
    )


def _serialize_conditions(records: dict[str, Any]) -> dict[str, dict[str, Any]]:
    serialized: dict[str, dict[str, Any]] = {}
    for body, record in (records or {}).items():
        if hasattr(record, "to_dict"):
            serialized[body] = record.to_dict()
        elif isinstance(record, dict):
            serialized[body] = dict(record)
    return serialized


def _prominence_lookup(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("body") or ""): item
        for item in raw.get("rankings", [])
        if isinstance(item, dict) and str(item.get("body") or "").strip()
    }


def _routing_view_for_report(report_type: str, category_key: str, raw: Any, simple_mode: bool) -> tuple[str, str, float, list[str], list[str]]:
    reasons: list[str] = []
    limitations: list[str] = []
    score = 0.0

    if category_key == "chart_ruler":
        if simple_mode:
            return "suppressed", "suppressed", 0.0, ["exact_time_dependent"], ["simple_mode_excludes_chart_ruler_claims"]
        if raw.get("status") != "success":
            return "suppressed", "suppressed", 0.0, ["chart_ruler_unavailable"], _coerce_list(raw.get("missing_inputs"))
        score = 0.76
        if report_type == "horoscope":
            return "headline_section", "visible", score, ["central_natal_governor"], []
        if report_type in {"year_ahead", "personal_forecast"}:
            return "forecast_cross_reference", "available", score, ["forecast_priority_context"], []
        if report_type == "soul_ecosystem":
            return "supporting_context", "available", score, ["baseline_orientation_before_eo"], []
        return "supporting_context", "available", score, ["standard_foundation"], []

    if category_key == "planetary_conditions":
        score = max((_safe_float(item.get("overall_condition_score")) for item in raw.values()), default=0.0)
        if simple_mode:
            reasons.append("retained_but_not_client_facing_in_simple_mode")
            return "internal_trace_only", "internal_only", score, reasons, []
        return "reference_table", "available", score, ["modifier_layer_for_other_sections"], []

    if category_key == "planetary_prominence":
        top = raw.get("rankings", [{}])[0] if raw.get("rankings") else {}
        score = _safe_float(top.get("normalized_score"))
        if simple_mode:
            return "internal_trace_only", "internal_only", score, ["exact_time_dependent"], ["simple_mode_excludes_prominence_claims"]
        if report_type == "horoscope" and score >= 0.45:
            return "supporting_context", "available", score, ["central_planet_ranking"], []
        if report_type in {"year_ahead", "personal_forecast"}:
            return "forecast_cross_reference", "available", score, ["forecast_target_weighting"], []
        return "supporting_context", "available", score, ["structural_centrality"], []

    if category_key == "house_emphasis":
        score = max((_safe_float(item.get("house_emphasis_normalized")) for item in raw.get("rankings", [])), default=0.0)
        if simple_mode:
            return "suppressed", "suppressed", score, ["exact_time_dependent"], ["simple_mode_excludes_house_emphasis_claims"]
        if report_type in {"year_ahead", "personal_forecast"}:
            return "forecast_cross_reference", "available", score, ["domain_repetition_explainer"], []
        return "supporting_context", "available", score, ["domain_structure"], []

    if category_key == "chart_orientation":
        score = max(
            _safe_float(raw.get("core_standard_distribution", {}).get("dominance_assessment", {}).get(axis, {}).get("structural_weights", {}).get(
                raw.get("core_standard_distribution", {}).get("dominance_assessment", {}).get(axis, {}).get("dominant_key", "")
            ))
            for axis in ("elements", "modalities", "polarities")
        )
        if report_type == "horoscope":
            return "headline_section", "available", score, ["foundational_natal_orientation"], []
        if report_type == "soul_ecosystem":
            return "supporting_context", "available", score, ["baseline_chart_orientation"], []
        return "supporting_context", "available", score, ["structural_baseline"], []

    if category_key == "luminary_structure":
        score = _safe_float(raw.get("sun_moon_architecture", {}).get("aspect_strength"))
        if report_type == "horoscope":
            return "supporting_context", "available", score, ["luminary_structure"], []
        if report_type == "soul_ecosystem":
            return "supporting_context", "available", score, ["baseline_luminary_foundation"], []
        return "modifier", "available", score, ["tone_modifier"], []

    if category_key == "aspect_architecture":
        score = max((_safe_float(item.get("structural_importance")) for item in raw.get("connections", [])), default=0.0)
        if score <= 0:
            return "suppressed", "suppressed", 0.0, ["no_major_connections"], ["no_connections"]
        if report_type == "horoscope":
            return "supporting_context", "available", score, ["support_tension_architecture"], []
        return "modifier", "available", score, ["relationship_to_central_factors"], []

    if category_key == "rulership_and_dispositors":
        score = min(1.0, len(raw.get("final_dispositors", [])) * 0.25 + len(raw.get("central_routing_planets", [])) * 0.15)
        if simple_mode:
            return "technical_appendix", "available", score, ["retained_for_reference"], []
        if report_type == "horoscope":
            return "supporting_context", "available", score, ["dispositorship_context"], []
        return "modifier", "available", score, ["rulership_modifier"], []

    if category_key == "named_configurations":
        count = len(raw.get("configurations", []))
        score = min(1.0, count * 0.2)
        if count == 0:
            return "suppressed", "suppressed", 0.0, ["no_named_patterns"], ["no_named_patterns_detected"]
        if report_type == "horoscope":
            return "supporting_context", "available", score, ["pattern_detection"], []
        return "technical_appendix", "available", score, ["available_but_not_primary"], []

    if category_key == "natal_convergence":
        domain_scores = [_safe_float(item.get("normalized_relevance_score")) for item in raw.get("central_life_domains", [])]
        score = max(domain_scores, default=0.0)
        if report_type in {"year_ahead", "personal_forecast"}:
            return "forecast_cross_reference", "available", score, ["forecast_theme_explainer"], []
        if report_type == "horoscope":
            return "supporting_context", "available", score, ["natal_theme_summary"], []
        if report_type == "soul_ecosystem":
            return "held_for_eo_synthesis", "available", score, ["eo_synthesis_support"], []
        return "supporting_context", "available", score, ["natal_theme_summary"], []

    if category_key == "forecast_natal_priority":
        score = max(raw.get("top_target_weights", {}).values(), default=0.0)
        if report_type in {"year_ahead", "personal_forecast"}:
            return "forecast_cross_reference", "available", score, ["forecast_priority_ready"], []
        if report_type == "soul_ecosystem":
            return "held_for_eo_synthesis", "available", score, ["available_but_not_surface_primary"], []
        return "internal_trace_only", "internal_only", score, ["forecast_only_context"], []

    return "internal_trace_only", "internal_only", score, ["uncategorized"], []


def _forecast_priority_result(payload: dict) -> dict[str, Any]:
    profile = build_forecast_activation_profile(payload)
    top_targets = dict(sorted(profile.get("target_weights", {}).items(), key=lambda item: item[1], reverse=True)[:8])
    top_houses = dict(sorted(profile.get("house_weights", {}).items(), key=lambda item: item[1], reverse=True)[:5])
    theme_records = []
    for item in profile.get("theme_records", []):
        theme_records.append(
            {
                "label": item.get("label", ""),
                "score": _safe_float(item.get("score")),
                "houses": sorted(int(value) for value in item.get("houses", set())),
                "planets": sorted(str(value) for value in item.get("planets", set())),
            }
        )
    return {
        "methodology": _methodology_from_payload(payload),
        "formula_version": "5.0.0",
        "chart_ruler": profile.get("chart_ruler") or "",
        "top_target_weights": top_targets,
        "top_house_weights": top_houses,
        "theme_records": theme_records,
        "central_house_rulers": sorted(profile.get("central_house_rulers", set())),
    }


def _safe_category(
    payload: dict,
    report_type: str,
    category_key: str,
    compute: Callable[[], Any],
    transform: Callable[[Any], Any] | None = None,
) -> dict[str, Any]:
    simple_mode = bool(payload.get("simple_mode") or payload.get("user_profile", {}).get("simple_mode"))
    try:
        raw = compute()
        raw = transform(raw) if transform else raw
        routing_state, visibility_state, score, reasons, limitations = _routing_view_for_report(
            report_type,
            category_key,
            raw,
            simple_mode,
        )
        formula_version = (
            raw.get("formula_version")
            if isinstance(raw, dict)
            else "5.0.0"
        ) or "5.0.0"
        confidence_state = (
            raw.get("confidence")
            or raw.get("confidence_state")
            or raw.get("hemisphere_and_quadrant", {}).get("confidence")
            or raw.get("lunar_phase", {}).get("confidence")
            or ("unknown" if simple_mode else "exact")
        )
        missing_inputs = _coerce_list(raw.get("missing_inputs")) if isinstance(raw, dict) else []
        supporting = []
        if category_key == "planetary_prominence":
            supporting = [item["body"] for item in raw.get("rankings", [])[:3]]
        elif category_key == "house_emphasis":
            supporting = [str(item.get("house")) for item in raw.get("rankings", [])[:3]]
        elif category_key == "named_configurations":
            supporting = [item.get("type", "") for item in raw.get("configurations", [])[:3]]
        elif category_key == "natal_convergence":
            supporting = [item.get("label", "") for item in raw.get("central_life_domains", [])[:3]]
        elif category_key == "forecast_natal_priority":
            supporting = list(raw.get("top_target_weights", {}).keys())[:4]
        return {
            "category": category_key,
            "method_status": METHOD_STATUS_CORE_STANDARD,
            "formula_version": formula_version,
            "confidence_state": confidence_state,
            "visibility_state": visibility_state,
            "routing_state": routing_state,
            "report_type": report_type,
            "score": round(score, 4),
            "supporting_factors": [item for item in supporting if item],
            "missing_inputs": missing_inputs,
            "limitations": limitations,
            "routing_reasons": reasons,
            "traceable_source_data": raw,
        }
    except Exception as exc:
        return {
            "category": category_key,
            "method_status": METHOD_STATUS_CORE_STANDARD,
            "formula_version": "5.0.0",
            "confidence_state": "unknown",
            "visibility_state": "suppressed",
            "routing_state": "internal_trace_only",
            "report_type": report_type,
            "score": 0.0,
            "supporting_factors": [],
            "missing_inputs": [],
            "limitations": [f"module_error:{exc.__class__.__name__}"],
            "routing_reasons": ["failed_non_fatally"],
            "traceable_source_data": {"error": str(exc)},
        }


def _category_map(payload: dict, report_type: str) -> dict[str, dict[str, Any]]:
    return {
        "chart_orientation": _safe_category(payload, report_type, "chart_orientation", lambda: evaluate_chart_structure(payload)),
        "planetary_conditions": _safe_category(
            payload,
            report_type,
            "planetary_conditions",
            lambda: evaluate_all_planetary_conditions(payload),
            transform=_serialize_conditions,
        ),
        "planetary_prominence": _safe_category(payload, report_type, "planetary_prominence", lambda: evaluate_prominence(payload)),
        "chart_ruler": _safe_category(payload, report_type, "chart_ruler", lambda: evaluate_chart_ruler(payload)),
        "house_emphasis": _safe_category(payload, report_type, "house_emphasis", lambda: evaluate_house_emphasis(payload)),
        "luminary_structure": _safe_category(
            payload,
            report_type,
            "luminary_structure",
            lambda: {
                "formula_version": evaluate_chart_structure(payload).get("formula_version", "2.0.0"),
                "sun_moon_architecture": evaluate_chart_structure(payload).get("sun_moon_architecture", {}),
                "lunar_phase": evaluate_chart_structure(payload).get("lunar_phase", {}),
            },
        ),
        "aspect_architecture": _safe_category(payload, report_type, "aspect_architecture", lambda: evaluate_aspect_architecture(payload)),
        "rulership_and_dispositors": _safe_category(payload, report_type, "rulership_and_dispositors", lambda: evaluate_rulership_network(payload)),
        "named_configurations": _safe_category(payload, report_type, "named_configurations", lambda: evaluate_named_configurations(payload)),
        "natal_convergence": _safe_category(payload, report_type, "natal_convergence", lambda: evaluate_standard_natal_convergence(payload)),
        "forecast_natal_priority": _safe_category(payload, report_type, "forecast_natal_priority", lambda: _forecast_priority_result(payload)),
    }


def _route_niche_results(niche_results: dict[str, dict[str, Any]], report_type: str) -> dict[str, dict[str, Any]]:
    routed: dict[str, dict[str, Any]] = {}
    for key, value in niche_results.items():
        routed_value = dict(value)
        visibility = str(routed_value.get("visibility_state") or "suppressed")
        if visibility == "suppressed":
            routing_state = "suppressed"
        elif report_type in {"year_ahead", "personal_forecast"}:
            routing_state = "forecast_cross_reference"
        elif report_type == "soul_ecosystem":
            routing_state = "held_for_eo_synthesis"
        elif report_type == "asteroid_portrait":
            routing_state = "supporting_context"
        else:
            routing_state = "technical_appendix"
        routed_value.setdefault("routing_state", routing_state)
        routed[key] = routed_value
    return routed


def _trace_summary(
    payload: dict,
    report_type: str,
    report_profile: str,
    standard_bundle: dict[str, Any],
    niche_results: dict[str, Any],
    eo_results: dict[str, Any],
) -> dict[str, Any]:
    routing_decisions = {
        key: value.get("routing_state", "internal_trace_only")
        for key, value in standard_bundle.items()
    }
    suppressed = [
        key
        for key, value in standard_bundle.items()
        if value.get("routing_state") == "suppressed"
    ]
    warnings = [
        {
            "category": key,
            "limitations": value.get("limitations", []),
        }
        for key, value in standard_bundle.items()
        if value.get("limitations")
    ]
    return {
        "report_type": report_type,
        "report_profile": report_profile,
        "generation_date": "",
        "methodology_marker": _methodology_from_payload(payload),
        "birth_time_confidence_state": _birth_time_confidence(payload),
        "standard_result_bundle_summary": {
            "category_count": len(standard_bundle),
            "categories": list(standard_bundle.keys()),
            "routing_decisions": routing_decisions,
        },
        "selected_routing_decisions": routing_decisions,
        "selected_block_files": [],
        "requested_block_keys": [],
        "resolved_block_keys": [],
        "fallback_use": [],
        "template_fields_populated": [],
        "suppressed_candidates": suppressed,
        "warnings_or_missing_data": warnings,
        "layer_counts": {
            "core_standard": len(standard_bundle),
            "established_niche": len(niche_results),
            "eo_proprietary": len(eo_results),
        },
    }


def build_report_bundle_context_view(bundle: dict[str, Any], report_type: str) -> dict[str, Any]:
    standard_bundle = bundle.get("standard_result_bundle", {})
    report_states = {state: [] for state in ROUTING_STATES}
    for category_key, record in standard_bundle.items():
        state = str(record.get("routing_state") or "internal_trace_only")
        report_states.setdefault(state, []).append(category_key)
    return {
        "report_type": report_type,
        "headline_sections": report_states.get("headline_section", []),
        "supporting_context": report_states.get("supporting_context", []),
        "modifiers": report_states.get("modifier", []),
        "reference_tables": report_states.get("reference_table", []),
        "technical_appendix": report_states.get("technical_appendix", []),
        "forecast_cross_reference": report_states.get("forecast_cross_reference", []),
        "held_for_eo_synthesis": report_states.get("held_for_eo_synthesis", []),
        "internal_trace_only": report_states.get("internal_trace_only", []),
        "suppressed": report_states.get("suppressed", []),
        "selected_supporting_categories": [
            category
            for category in (
                report_states.get("headline_section", [])
                + report_states.get("supporting_context", [])
                + report_states.get("forecast_cross_reference", [])
            )
        ],
    }


def build_layered_report_bundle(
    payload: dict,
    report_type: str,
    *,
    index_results: dict[str, Any] | None = None,
    specialist_body_keys: list[str] | None = None,
) -> dict[str, Any]:
    report_profile = get_report_layer_profile(report_type)

    core_standard_categories = (
        _category_map(payload, report_type)
        if layer_allows(METHOD_STATUS_CORE_STANDARD, report_profile)
        else {}
    )
    niche_results = (
        _route_niche_results(
            evaluate_selected_specialist_bodies(payload, report_type, specialist_body_keys, report_profile),
            report_type,
        )
        if layer_allows("established_niche", report_profile)
        else {}
    )
    eo_results = (
        {
            key: _tag_proprietary_result(key, value, report_profile)
            for key, value in (index_results or {}).items()
            if layer_allows(METHOD_STATUS_EO_PROPRIETARY, report_profile)
        }
        if index_results
        else {}
    )

    standard_result_bundle = dict(core_standard_categories)
    standard_result_bundle["established_niche_results"] = {
        "category": "established_niche_results",
        "method_status": "established_niche",
        "formula_version": "5.0.0",
        "confidence_state": _birth_time_confidence(payload),
        "visibility_state": "available" if niche_results else "suppressed",
        "routing_state": "held_for_eo_synthesis" if niche_results and report_type == "soul_ecosystem" else (
            "forecast_cross_reference" if niche_results and report_type in {"year_ahead", "personal_forecast"} else (
                "supporting_context" if niche_results and report_type == "asteroid_portrait" else (
                    "technical_appendix" if niche_results else "suppressed"
                )
            )
        ),
        "report_type": report_type,
        "score": round(min(1.0, len(niche_results) * 0.2), 4),
        "supporting_factors": list(niche_results.keys())[:4],
        "missing_inputs": [],
        "limitations": [] if niche_results else ["no_established_niche_results_selected"],
        "routing_reasons": ["specialist_results_remain_distinct"],
        "traceable_source_data": niche_results,
    }

    trace = _trace_summary(
        payload,
        report_type,
        report_profile,
        standard_result_bundle,
        niche_results,
        eo_results,
    )

    return {
        "report_type": report_type,
        "report_profile": report_profile,
        "methodology": _methodology_from_payload(payload),
        "birth_time_confidence_state": _birth_time_confidence(payload),
        "core_standard": core_standard_categories,
        "standard_result_bundle": standard_result_bundle,
        "established_niche": niche_results,
        "eo_proprietary": eo_results,
        "report_context_view": build_report_bundle_context_view(
            {"standard_result_bundle": standard_result_bundle},
            report_type,
        ),
        "trace": trace,
    }
