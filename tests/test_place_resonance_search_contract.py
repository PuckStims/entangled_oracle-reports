"""
Tests for the first Place Resonance Search contract layer.

This covers the candidate catalog, batch evidence generation, scoring,
bucket assignment, and authored search-level prose blocks.
"""
import copy
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from products.location_services.place_resonance_search.assembler import (
    assemble_place_resonance_search_results_context,
    build_search_evidence_records,
    build_scored_search_locations,
)
from products.location_services.place_resonance_search.candidate_catalog import (
    OPTIONAL_ONTOLOGY_FIELDS,
    REQUIRED_CANDIDATE_FIELDS,
    load_candidate_catalog,
)
from products.location_services.place_resonance_search.scoring import (
    BUCKET_KEYS,
    SCORE_KEYS,
    normalize_raw_scores,
    raw_score_location_record,
)
from products.location_services.place_resonance_search.renderer import (
    build_place_resonance_search_results_html,
    render_place_resonance_search_results_html,
)
from selectors.location_services_selector import select_place_resonance_search_leaf
from test_location_services_relocated_payload import _build_natal_payload


BLOCKS_DIR = Path(__file__).resolve().parent.parent / "products" / "location_services" / "blocks" / "plainspeak"
SEARCH_BLOCK_FILE = BLOCKS_DIR / "place_resonance_search_blocks.json"

SEARCH_SUMMARY_KEYS = {
    "visibility_calling",
    "belonging_bonds",
    "hearth_restoration",
    "study_signal",
    "creative_culture",
    "long_term_build",
    "change_aliveness",
    "shadow_pressure",
    "mixed_signature",
    "fallback",
}

BUCKET_INTRO_KEYS = {
    "highest_resonance",
    "goal_specific_allies",
    "transformational_demanding",
    "quiet_grounding_alternatives",
    "pattern_outliers",
    "fallback",
}

RECOMMENDATION_LABEL_KEYS = {
    "strongly_consider",
    "strongly_consider_belonging_restoration",
    "strongly_consider_belonging_aliveness",
    "strongly_consider_visibility",
    "strongly_consider_reinvention",
    "strongly_consider_coherent",
    "goal_specific_ally",
    "goal_specific_ally_creative",
    "goal_specific_ally_visibility",
    "goal_specific_ally_belonging",
    "powerful_but_demanding",
    "powerful_but_demanding_pressure",
    "powerful_but_demanding_reinvention",
    "powerful_but_demanding_private",
    "powerful_but_demanding_consequential",
    "powerful_but_demanding_visibility",
    "powerful_but_demanding_structure",
    "powerful_but_demanding_belonging",
    "gentle_alternative",
    "gentle_alternative_restorative",
    "gentle_alternative_visibility",
    "gentle_alternative_belonging",
    "gentle_alternative_steady",
    "useful_contrast",
    "useful_contrast_divergent",
    "useful_contrast_visibility",
    "useful_contrast_visibility_signal",
    "useful_contrast_visibility_signal_metro",
    "useful_contrast_visibility_signal_small_place",
    "stable_baseline",
    "low_signal_not_priority",
    "fallback",
}

PATTERN_SYNTHESIS_KEYS = {
    "convergent_theme",
    "split_need",
    "pressure_pattern",
    "quiet_counterweight",
    "outlier_reveal",
    "fallback",
}

TILE_DETAIL_KEYS = {
    "bucket_role_highest_resonance",
    "bucket_role_goal_specific_allies",
    "bucket_role_transformational_demanding",
    "bucket_role_quiet_grounding_alternatives",
    "bucket_role_pattern_outliers",
    "sibling_difference",
    "cluster_alternates",
    "best_use_case",
    "fallback",
}

FORBIDDEN_VAGUE_PHRASES = (
    "could mean many different things",
    "only you can know",
    "supportive and challenging qualities",
)


def _mini_catalog():
    return load_candidate_catalog()[:4]


def _leaf_dicts(node):
    if isinstance(node, dict):
        if "body" in node:
            yield node
        for value in node.values():
            yield from _leaf_dicts(value)


def _leaf_paths(node, path=()):
    if isinstance(node, dict):
        if "body" in node:
            yield path, node
        for key, value in node.items():
            yield from _leaf_paths(value, (*path, key))


def test_candidate_catalog_has_required_shape():
    candidates = load_candidate_catalog()

    assert len(candidates) >= 140
    assert {candidate["state"] for candidate in candidates} >= {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD",
        "ME", "MI", "MN", "MS", "MO", "MT", "NC", "ND", "NE", "NH",
        "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY",
        "DC",
    }
    for candidate in candidates:
        assert REQUIRED_CANDIDATE_FIELDS <= set(candidate)
        assert candidate["location_id"].startswith("us-")
        assert candidate["country"] == "US"
        assert isinstance(candidate["latitude"], float)
        assert isinstance(candidate["longitude"], float)
        assert "/" in candidate["timezone"]
        for field in OPTIONAL_ONTOLOGY_FIELDS:
            assert field in candidate
            assert isinstance(candidate[field], list)


def test_candidate_catalog_has_seed_place_ontology_for_exemplars():
    candidates = {candidate["location_id"]: candidate for candidate in load_candidate_catalog()}
    enriched = [
        candidate for candidate in candidates.values()
        if candidate["selection_classes"]
    ]

    assert len(enriched) >= 90
    assert "regional_anchor" in candidates["us-mn-duluth"]["selection_classes"]
    assert "great_lakes_port" in candidates["us-mn-duluth"]["place_archetypes"]
    assert "spiritual_destinations" in candidates["us-az-sedona"]["collections"]
    assert "difficult_important_place" in candidates["us-mi-detroit"]["selection_classes"]
    assert "river_systems" in candidates["us-la-new-orleans"]["collections"]
    assert "remote_service_hub" in candidates["us-ak-anchorage"]["place_archetypes"]
    assert "state_coverage_anchor" in candidates["us-de-dover"]["selection_classes"]
    assert "state_capitals" in candidates["us-ms-jackson"]["collections"]
    assert "borderlands" in candidates["us-tx-el-paso"]["collections"]


def test_batch_search_evidence_generation_does_not_mutate_inputs():
    natal = _build_natal_payload()
    candidates = _mini_catalog()
    natal_before = copy.deepcopy(natal)
    candidates_before = copy.deepcopy(candidates)

    records = build_search_evidence_records(
        natal,
        candidates,
        purpose_lens="creative visibility",
        relationship_to_place="possible_move",
    )

    assert natal == natal_before
    assert candidates == candidates_before
    assert len(records) == len(candidates)
    for record, candidate in zip(records, candidates):
        assert record["search_candidate"]["location_id"] == candidate["location_id"]
        assert record["destination_context"]["display_name"] == candidate["display_name"]
        assert record["purpose_lens"] == "creative visibility"


def test_scored_search_locations_have_scores_buckets_and_recommendations():
    records = build_search_evidence_records(_build_natal_payload(), _mini_catalog())
    scored = build_scored_search_locations(records)

    assert len(scored) == len(records)
    for location in scored:
        assert set(SCORE_KEYS) <= set(location["scores"])
        assert location["bucket"] in BUCKET_KEYS
        assert location["bucket_label"]
        assert location["recommendation_key"]
        assert location["recommendation_prose_key"]
        assert location["recommendation_label"]
        assert isinstance(location["dominant_themes"], list)
        assert isinstance(location["prose_variation_traits"], dict)
        for value in location["scores"].values():
            assert 0 <= value <= 100


def test_scored_search_locations_preserve_relative_score_spread():
    records = build_search_evidence_records(_build_natal_payload(), load_candidate_catalog())
    scored = build_scored_search_locations(records)

    overall_scores = [location["scores"]["overall_resonance"] for location in scored]
    complexity_scores = [location["scores"]["complexity_index"] for location in scored]
    consensus_scores = [location["scores"]["consensus_score"] for location in scored]
    buckets = {location["bucket"] for location in scored}

    assert len(set(overall_scores)) >= 3
    assert len(set(complexity_scores)) >= 3
    assert len(set(consensus_scores)) >= 3
    assert len(buckets) >= 3
    assert overall_scores.count(100) < len(overall_scores) // 2
    assert consensus_scores.count(100) < len(consensus_scores) // 2
    assert all("raw_scores" in location for location in scored)
    assert all("normalization_profile" in location for location in scored)


def test_search_scoring_discounts_custom_bodies_against_major_planets():
    def _record_for(body):
        return {
            "relocated_angle_contacts": [
                {
                    "id": f"angle_contact:{body}:Midheaven",
                    "body": body,
                    "angle": "Midheaven",
                    "orb": 0.5,
                    "contact_strength": "tight",
                }
            ],
            "planet_house_changes": [
                {
                    "id": f"house_change:{body}",
                    "body": body,
                    "house_changed": True,
                    "relocated_house": 10,
                    "movement_type": "newly_angular",
                }
            ],
            "evidence_ranking": {
                "primary_evidence": [
                    f"angle_contact:{body}:Midheaven",
                    f"house_change:{body}",
                ],
                "supporting_evidence": [],
                "contradictory_evidence": [],
            },
        }

    major = raw_score_location_record(_record_for("Sun"))
    custom = raw_score_location_record(_record_for("Kassandra"))

    assert custom["visibility_calling"] < major["visibility_calling"]
    assert custom["consensus_score"] < major["consensus_score"]
    assert custom["baseline_divergence"] < major["baseline_divergence"]


def test_search_normalization_uses_actual_upper_bound_to_reduce_saturation():
    normalized = normalize_raw_scores([
        {"visibility_calling": 0, "consensus_score": 0, "baseline_divergence": 0},
        {"visibility_calling": 10, "consensus_score": 10, "baseline_divergence": 10},
        {"visibility_calling": 20, "consensus_score": 20, "baseline_divergence": 20},
        {"visibility_calling": 30, "consensus_score": 30, "baseline_divergence": 30},
    ])

    visibility_scores = [item["visibility_calling"] for item in normalized]
    assert visibility_scores[-1] == 100
    assert visibility_scores[-2] < 100


def test_search_results_context_selects_locations_and_profile_contexts():
    context = assemble_place_resonance_search_results_context(
        _build_natal_payload(),
        _mini_catalog(),
        purpose_lens="creative visibility",
        relationship_to_place="possible_move",
        selection_limit=3,
    )

    assert context["context_version"] == "place_resonance_search_context_v0.2.0"
    assert context["report_type"] == "location_services.place_resonance_search"
    assert context["product_name"] == "Place Resonance Search"
    assert context["search_mode"] == "candidate_catalog_pool"
    assert context["normalization_profile"]["method"] == "candidate_pool_percentile_minmax"
    assert context["candidate_pool"]["evaluated_count"] == len(_mini_catalog())
    assert len(context["selected_locations"]) == 3
    assert context["selected_leaves"]["search_summary"]["body"] != "TODO"
    assert context["selected_leaves"]["pattern_synthesis"]["body"] != "TODO"
    assert context["tile_detail_leaves"]

    for location in context["selected_locations"]:
        assert location["profile_context"]["product_name"] == "Place Resonance Search"
        assert location["profile_context"]["source_product"] == "location_services.place_resonance"
        assert "regional_role" in location
        assert "cluster_alternates" in location
        assert "similarity_signature" in location
        assert location["location_id"] in context["recommendation_leaves"]
        assert location["location_id"] in context["tile_detail_leaves"]
        assert context["recommendation_leaves"][location["location_id"]]["body"] != "TODO"


def test_recommendation_prose_varies_within_repeated_buckets():
    context = assemble_place_resonance_search_results_context(
        _build_natal_payload(),
        purpose_lens="creative visibility",
        relationship_to_place="possible_move",
        selection_limit=8,
    )

    bodies_by_bucket: dict[str, set[str]] = {}
    keys_by_bucket: dict[str, set[str]] = {}
    counts_by_bucket: dict[str, int] = {}
    for location in context["selected_locations"]:
        bucket = location["bucket"]
        body = context["recommendation_leaves"][location["location_id"]]["body"]
        bodies_by_bucket.setdefault(bucket, set()).add(body)
        keys_by_bucket.setdefault(bucket, set()).add(location["recommendation_prose_key"])
        counts_by_bucket[bucket] = counts_by_bucket.get(bucket, 0) + 1

    assert len({
        location["recommendation_prose_key"]
        for location in context["selected_locations"]
    }) >= 4
    for bucket, count in counts_by_bucket.items():
        if count > 1:
            assert all(body != "TODO" for body in bodies_by_bucket[bucket])
            if len(keys_by_bucket[bucket]) > 1:
                assert len(bodies_by_bucket[bucket]) > 1


def test_search_selection_clusters_nearby_similar_locations_as_alternates():
    context = assemble_place_resonance_search_results_context(
        _build_natal_payload(),
        purpose_lens="creative visibility",
        relationship_to_place="possible_move",
        selection_limit=20,
    )

    clustered = [
        location for location in context["selected_locations"]
        if location.get("cluster_alternates")
    ]

    assert clustered, "expected at least one nearby similar location to collapse into alternates"
    for location in clustered:
        assert location["regional_role"] == "cluster_lead"
        for alternate in location["cluster_alternates"]:
            assert alternate["distance_from_representative_miles"] <= 500
            assert alternate["sibling_difference"]


def test_place_resonance_search_block_file_has_expected_scaffold_keys():
    data = json.loads(SEARCH_BLOCK_FILE.read_text(encoding="utf-8"))

    assert data["_version"] == "0.1.0-authored"
    assert set(data["search_summary"]) - {"_note"} == SEARCH_SUMMARY_KEYS
    assert set(data["bucket_intro"]) - {"_note"} == BUCKET_INTRO_KEYS
    assert set(data["recommendation_label"]) - {"_note"} == RECOMMENDATION_LABEL_KEYS
    assert set(data["tile_detail"]) - {"_note"} == TILE_DETAIL_KEYS
    assert set(data["pattern_synthesis"]) - {"_note"} == PATTERN_SYNTHESIS_KEYS


def test_place_resonance_search_leaves_are_authored_and_structured():
    data = json.loads(SEARCH_BLOCK_FILE.read_text(encoding="utf-8"))

    for path, leaf in _leaf_paths(data):
        assert isinstance(leaf["body"], str) and leaf["body"].strip()
        if path and path[0] == "tile_detail":
            assert leaf["body"] == "TODO"
        else:
            assert leaf["body"] != "TODO"
        assert isinstance(leaf["_note"], str) and leaf["_note"].strip()
        assert leaf["claim_level"] == "bounded_interpretation"
        assert isinstance(leaf["requires_evidence"], list) and leaf["requires_evidence"]


def test_place_resonance_search_leaves_do_not_use_empty_vague_escape_phrases():
    data = json.loads(SEARCH_BLOCK_FILE.read_text(encoding="utf-8"))

    for path, leaf in _leaf_paths(data):
        if path and path[0] == "tile_detail":
            continue
        body = leaf["body"].lower()
        for phrase in FORBIDDEN_VAGUE_PHRASES:
            assert phrase not in body, leaf


def test_place_resonance_search_selector_returns_family_leaf():
    leaf = select_place_resonance_search_leaf("bucket_intro", "highest_resonance")

    assert leaf["body"] != "TODO"
    assert "multi-indicator" in leaf["_note"]


def test_search_results_renderer_outputs_multi_location_shell_without_raw_todo():
    context = assemble_place_resonance_search_results_context(
        _build_natal_payload(),
        _mini_catalog(),
        selection_limit=3,
    )

    html = render_place_resonance_search_results_html(context)

    assert "Place Resonance Search" in html
    assert "Scores are relative indexes within this evaluated pool" in html
    assert "Bucket Distribution" in html
    assert "Place texture:" in html
    assert "Draft Slot" in html
    assert ">TODO<" not in html
    for location in context["selected_locations"]:
        assert location["display_name"] in html
        assert location["recommendation_label"] in html


def test_build_search_results_html_wrapper_uses_candidate_catalog():
    html = build_place_resonance_search_results_html(
        _build_natal_payload(),
        _mini_catalog(),
        purpose_lens="creative visibility",
        selection_limit=2,
    )

    assert "Place Resonance Search" in html
    assert "Selected" in html
    assert "Draft Slot" in html
    assert "candidate_catalog_pool" in html
