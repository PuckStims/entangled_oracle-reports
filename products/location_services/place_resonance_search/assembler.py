"""
Place Resonance Search context wrapper.

This package currently reuses the single-location Place Resonance evidence
path while presenting a distinct report identity for the emerging search
product.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Any

from engine.location_services import build_location_evidence_record
from products.location_services.place_resonance.assembler import (
    assemble_place_resonance_context as _assemble_place_resonance_context,
)
from products.location_services.place_resonance.assembler import (
    build_place_resonance_context as _build_place_resonance_context,
)
from products.location_services.place_resonance.assembler import (
    select_synthesis_category,
)
from products.location_services.place_resonance_search.candidate_catalog import (
    active_candidates,
    candidate_to_destination,
    load_candidate_catalog,
    validate_candidate_catalog,
)
from products.location_services.place_resonance_search.scoring import (
    SCORING_VERSION,
    NORMALIZATION_PROFILE,
    bucket_distribution,
    build_scored_locations,
    select_curated_locations,
)
from selectors.location_services_selector import select_place_resonance_search_leaf


CONTEXT_VERSION = "place_resonance_search_context_v0.2.0"
REPORT_TYPE = "location_services.place_resonance_search"
PRODUCT_NAME = "Place Resonance Search"


def _retitle_context(context: dict) -> dict:
    updated = copy.deepcopy(context)
    updated["context_version"] = CONTEXT_VERSION
    updated["report_type"] = REPORT_TYPE
    updated["product_name"] = PRODUCT_NAME
    updated["source_product"] = "location_services.place_resonance"
    return updated


def assemble_place_resonance_search_context(evidence_record: dict) -> dict:
    return _retitle_context(_assemble_place_resonance_context(evidence_record))


def build_place_resonance_search_context(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> dict:
    return _retitle_context(
        _build_place_resonance_context(
            natal_payload,
            destination,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )
    )


def _dominant_search_theme(selected_locations: list[dict[str, Any]]) -> str:
    totals: Counter = Counter()
    for item in selected_locations:
        for theme in item.get("dominant_themes", []) or []:
            totals[theme] += item.get("scores", {}).get(theme, 0)
    if not totals:
        return "fallback"
    theme, score = totals.most_common(1)[0]
    return theme if score > 0 else "fallback"


def _pattern_synthesis_key(selected_locations: list[dict[str, Any]]) -> str:
    if not selected_locations:
        return "fallback"

    distribution = bucket_distribution(selected_locations)
    if distribution.get("transformational_demanding", 0) >= 2:
        return "pressure_pattern"
    if distribution.get("quiet_grounding_alternatives", 0) >= 2:
        return "quiet_counterweight"
    if distribution.get("pattern_outliers", 0):
        return "outlier_reveal"

    top_themes = {
        theme
        for item in selected_locations[:5]
        for theme in (item.get("dominant_themes") or [])[:1]
    }
    if len(top_themes) >= 2:
        return "split_need"
    return "convergent_theme"


def build_search_evidence_records(
    natal_payload: dict,
    candidates: list[dict[str, Any]],
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in active_candidates(candidates):
        destination = candidate_to_destination(candidate)
        record = build_location_evidence_record(
            natal_payload,
            destination,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )
        record = copy.deepcopy(record)
        record["search_candidate"] = copy.deepcopy(candidate)
        records.append(record)
    return records


def build_scored_search_locations(
    evidence_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records_with_candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, record in enumerate(evidence_records):
        candidate = record.get("search_candidate")
        if not isinstance(candidate, dict):
            raise ValueError("Search evidence record is missing search_candidate metadata.")
        records_with_candidates.append((record, candidate))
    return build_scored_locations(records_with_candidates)


def assemble_place_resonance_search_results_context(
    natal_payload: dict,
    candidates: list[dict[str, Any]] | None = None,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
    selection_limit: int = 20,
) -> dict[str, Any]:
    """
    Build the first real multi-location Search context.

    This evaluates a candidate catalog through the existing
    single-place evidence builder, scores each candidate, and selects a curated
    result set. Rendering is intentionally still future work.
    """
    if candidates is None:
        candidates = load_candidate_catalog()
    candidates = validate_candidate_catalog(candidates)

    evidence_records = build_search_evidence_records(
        natal_payload,
        candidates,
        purpose_lens=purpose_lens,
        relationship_to_place=relationship_to_place,
    )
    scored_locations = build_scored_search_locations(evidence_records)
    selected_locations = select_curated_locations(scored_locations, limit=selection_limit)

    for item in selected_locations:
        item["profile_context"] = _retitle_context(
            _assemble_place_resonance_context(item["evidence_record"])
        )

    dominant_theme = _dominant_search_theme(selected_locations)
    pattern_key = _pattern_synthesis_key(selected_locations)

    return {
        "context_version": CONTEXT_VERSION,
        "report_type": REPORT_TYPE,
        "product_name": PRODUCT_NAME,
        "source_product": "location_services.place_resonance",
        "search_contract_version": CONTEXT_VERSION,
        "scoring_version": SCORING_VERSION,
        "normalization_profile": copy.deepcopy(NORMALIZATION_PROFILE),
        "search_mode": "candidate_catalog_pool",
        "purpose_lens": purpose_lens,
        "relationship_to_place": relationship_to_place,
        "candidate_pool": {
            "evaluated_count": len(evidence_records),
            "active_count": len(active_candidates(candidates)),
            "selection_limit": selection_limit,
            "catalog_scope": "runtime_candidate_catalog",
        },
        "dominant_search_theme": dominant_theme,
        "bucket_distribution": bucket_distribution(selected_locations),
        "selected_locations": selected_locations,
        "evaluated_locations": scored_locations,
        "selected_leaves": {
            "search_summary": select_place_resonance_search_leaf("search_summary", dominant_theme),
            "pattern_synthesis": select_place_resonance_search_leaf("pattern_synthesis", pattern_key),
        },
        "bucket_leaves": {
            bucket: select_place_resonance_search_leaf("bucket_intro", bucket)
            for bucket, count in bucket_distribution(selected_locations).items()
            if count
        },
        "recommendation_leaves": {
            item["location_id"]: select_place_resonance_search_leaf(
                "recommendation_label",
                item.get("recommendation_prose_key") or item["recommendation_key"],
            )
            for item in selected_locations
        },
    }
