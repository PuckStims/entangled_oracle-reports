import copy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import CONTENT_PACKS, HOUSE_DOMAINS
from generate import _build_forecast_climate


def _pack() -> dict:
    return CONTENT_PACKS["plainspeak"]


def _base_events():
    transit_saturn = {
        "event_type": "transit",
        "cycle_id": "saturn-1",
        "transit_planet": "Saturn",
        "aspect": "Sextile",
        "natal_target": "Saturn",
        "natal_house": 6,
        "combined_intensity_score": 0.8,
        "structural_score": 1.1,
        "duration_days": 120,
        "peak_date": "2026-08-10",
        "title": "Saturn Sextile natal Saturn",
    }
    transit_connection = {
        "event_type": "transit",
        "cycle_id": "venus-1",
        "transit_planet": "Venus",
        "aspect": "Conjunction",
        "natal_target": "Moon",
        "natal_house": 7,
        "combined_intensity_score": 0.62,
        "structural_score": 0.7,
        "duration_days": 18,
        "peak_date": "2026-07-12",
        "title": "Venus Conjunct natal Moon",
    }
    angle_event = {
        "event_type": "transit",
        "cycle_id": "mc-1",
        "transit_planet": "Mars",
        "aspect": "Square",
        "natal_target": "MC",
        "natal_house": 10,
        "combined_intensity_score": 0.75,
        "structural_score": 0.82,
        "duration_days": 16,
        "peak_date": "2026-09-01",
        "title": "Mars Square natal MC",
    }
    station_connection = {
        "event_type": "station",
        "transit_planet": "Venus",
        "natal_target": "Moon",
        "natal_house": 7,
        "combined_intensity_score": 0.55,
        "peak_date": "2026-07-14",
        "title": "Venus station near natal Moon",
    }
    ingress_visibility = {
        "event_type": "ingress",
        "transit_planet": "Jupiter",
        "house_number": 10,
        "combined_intensity_score": 0.4,
        "peak_date": "2026-10-01",
        "title": "Jupiter ingress into the tenth house",
    }
    convergence = {
        "event_type": "convergence",
        "constituent_events": [transit_connection, station_connection],
    }
    landmarks = [{"cycle_id": "saturn-1"}]
    return {
        "transit_events": [transit_saturn, transit_connection, angle_event],
        "all_events": [station_connection, ingress_visibility],
        "convergence_events": [convergence],
        "landmarks": landmarks,
    }


def _field_map(climate: dict) -> dict[str, dict]:
    return {field["field_key"]: field for field in climate["fields"]}


def test_forecast_climate_is_deterministic_and_resolves_block_path():
    events = _base_events()
    first = _build_forecast_climate(
        events["transit_events"],
        events["all_events"],
        events["convergence_events"],
        events["landmarks"],
        HOUSE_DOMAINS,
        "exact",
        _pack(),
    )
    second = _build_forecast_climate(
        copy.deepcopy(events["transit_events"]),
        copy.deepcopy(events["all_events"]),
        copy.deepcopy(events["convergence_events"]),
        copy.deepcopy(events["landmarks"]),
        HOUSE_DOMAINS,
        "exact",
        _pack(),
    )

    assert first == second
    for field in first["fields"]:
        assert len(field["selected_block_key_path"]) == 3
        assert field["block"]


def test_forecast_climate_deduplicates_transit_cycles_and_ignores_landmark_aliases():
    events = _base_events()
    duplicated_transits = list(events["transit_events"]) + [copy.deepcopy(events["transit_events"][0])]

    baseline = _build_forecast_climate(
        events["transit_events"],
        events["all_events"],
        events["convergence_events"],
        events["landmarks"],
        HOUSE_DOMAINS,
        "exact",
        _pack(),
    )
    duplicated = _build_forecast_climate(
        duplicated_transits,
        events["all_events"],
        events["convergence_events"],
        events["landmarks"],
        HOUSE_DOMAINS,
        "exact",
        _pack(),
    )
    no_landmark_alias = _build_forecast_climate(
        events["transit_events"],
        events["all_events"],
        events["convergence_events"],
        [],
        HOUSE_DOMAINS,
        "exact",
        _pack(),
    )

    assert baseline == duplicated
    baseline_map = _field_map(baseline)
    no_landmark_map = _field_map(no_landmark_alias)
    assert baseline_map["capacity"]["raw_score"] == no_landmark_map["capacity"]["raw_score"]


def test_reduced_confidence_withholds_houses_angles_and_ingresses():
    events = _base_events()
    climate = _build_forecast_climate(
        events["transit_events"],
        events["all_events"],
        events["convergence_events"],
        events["landmarks"],
        HOUSE_DOMAINS,
        "unknown",
        _pack(),
    )
    fields = _field_map(climate)

    assert climate["confidence"] == "reduced"
    assert "house- and angle-based routing is withheld" in climate["confidence_note"].lower()
    assert fields["visibility"]["top_domains"] == []
    # `reason_tags` was replaced by curated display fields (title/event_label/
    # timing_note) in the current _build_forecast_climate; check those instead
    # for the same raw-metadata-leakage concern.
    assert all(
        "domain:" not in " ".join([event["title"], event["event_label"], event["timing_note"]])
        for event in fields["visibility"]["supporting_events"]
    )
    assert all("House Ingress" != event["event_label"] for field in climate["fields"] for event in field["supporting_events"])
    assert all("Midheaven" not in field["summary_line"] for field in climate["fields"])


def test_convergence_bonus_is_capped_and_scores_normalize():
    events = _base_events()
    events["convergence_events"] = events["convergence_events"] * 3
    climate = _build_forecast_climate(
        events["transit_events"],
        events["all_events"],
        events["convergence_events"],
        events["landmarks"],
        HOUSE_DOMAINS,
        "exact",
        _pack(),
    )
    fields = _field_map(climate)

    assert fields["connection"]["score_components"]["convergence_bonus"] == 0.16
    assert max(field["normalized_score"] for field in climate["fields"]) == 100
    assert any(field["band_key"] == "most_visible" for field in climate["fields"])


if __name__ == "__main__":
    test_forecast_climate_is_deterministic_and_resolves_block_path()
    test_forecast_climate_deduplicates_transit_cycles_and_ignores_landmark_aliases()
    test_reduced_confidence_withholds_houses_angles_and_ingresses()
    test_convergence_bonus_is_capped_and_scores_normalize()
