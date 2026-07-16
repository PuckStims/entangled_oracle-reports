import json

from products.location_services.place_resonance_search.candidate_catalog import (
    load_candidate_catalog,
)
from products.location_services.place_resonance_search.providers.geonames_importer import (
    build_location_id,
    dedupe_candidates_by_location_id,
    geonames_row_to_candidate,
    geonamescache_city_to_candidate,
    iter_geonames_candidates,
    parse_geonames_row,
    population_tier,
)
from products.location_services.place_resonance_search.providers.location_catalog import (
    count_location_candidates,
    merge_curated_overlays,
    query_location_candidates,
    upsert_location_candidates,
)


GEONAMES_ROWS = [
    "5391959\tSan Francisco\tSan Francisco\t\t37.77493\t-122.41942\tP\tPPLA2\tUS\t\tCA\t075\t\t\t873965\t\t16\tAmerica/Los_Angeles\t2025-01-01\n",
    "5419384\tDenver\tDenver\t\t39.73915\t-104.9847\tP\tPPLA\tUS\t\tCO\t031\t\t\t715522\t\t1609\tAmerica/Denver\t2025-01-01\n",
    "5780993\tSalt Lake City\tSalt Lake City\t\t40.76078\t-111.89105\tP\tPPLA\tUS\t\tUT\t035\t\t\t199723\t\t1299\tAmerica/Denver\t2025-01-01\n",
    "2988507\tParis\tParis\t\t48.85341\t2.3488\tP\tPPLC\tFR\t\t11\t075\t\t\t2138551\t\t42\tEurope/Paris\t2025-01-01\n",
]


def test_geonames_row_maps_to_search_candidate_shape():
    row = parse_geonames_row(GEONAMES_ROWS[0])
    candidate = geonames_row_to_candidate(row)

    assert candidate["location_id"] == "us-ca-san-francisco"
    assert candidate["display_name"] == "San Francisco, CA, US"
    assert candidate["latitude"] == 37.7749
    assert candidate["longitude"] == -122.4194
    assert candidate["timezone"] == "America/Los_Angeles"
    assert candidate["population_tier"] == "large_metro"
    assert candidate["region"] == "West Coast"
    assert candidate["source"] == "geonames_dump"
    assert candidate["provider_metadata"]["geoname_id"] == "5391959"
    assert candidate["provider_metadata"]["population"] == 873965


def test_geonames_candidate_iterator_filters_country_and_population():
    candidates = list(iter_geonames_candidates(GEONAMES_ROWS, country_code="US", min_population=500_000))

    assert [candidate["location_id"] for candidate in candidates] == [
        "us-ca-san-francisco",
        "us-co-denver",
    ]


def test_location_catalog_store_queries_provider_candidates(tmp_path):
    db_path = tmp_path / "location_catalog.sqlite"
    candidates = list(iter_geonames_candidates(GEONAMES_ROWS, country_code="US", min_population=0))

    assert upsert_location_candidates(db_path, candidates) == 3

    queried = query_location_candidates(
        db_path,
        states=["CA", "CO", "UT"],
        min_population=150_000,
        limit=2,
    )

    assert [candidate["location_id"] for candidate in queried] == [
        "us-ca-san-francisco",
        "us-co-denver",
    ]
    assert all(candidate["country"] == "US" for candidate in queried)


def test_empty_location_catalog_query_initializes_without_crashing(tmp_path):
    db_path = tmp_path / "empty_location_catalog.sqlite"

    assert count_location_candidates(db_path) == 0
    assert query_location_candidates(db_path, min_population=1000, limit=10) == []
    assert count_location_candidates(db_path) == 0


def test_geonamescache_city_maps_to_provider_candidate_shape():
    candidate = geonamescache_city_to_candidate({
        "geonameid": 4046704,
        "name": "Fort Hunt",
        "latitude": 38.73289,
        "longitude": -77.05803,
        "countrycode": "US",
        "population": 16045,
        "timezone": "America/New_York",
        "admin1code": "VA",
    })

    assert candidate["location_id"] == "us-va-fort-hunt"
    assert candidate["population_tier"] == "small_town"
    assert candidate["source"] == "geonamescache"
    assert candidate["provider_metadata"]["population"] == 16045


def test_curated_overlay_overrides_provider_fields_without_losing_provider_reach(tmp_path):
    db_path = tmp_path / "location_catalog.sqlite"
    provider_candidates = list(iter_geonames_candidates(GEONAMES_ROWS, country_code="US"))
    upsert_location_candidates(db_path, provider_candidates)
    queried = query_location_candidates(db_path, min_population=100_000, limit=10)
    curated = [
        candidate
        for candidate in load_candidate_catalog()
        if candidate["location_id"] in {"us-ca-san-francisco", "us-wy-cheyenne"}
    ]

    merged = merge_curated_overlays(queried, curated)
    by_id = {candidate["location_id"]: candidate for candidate in merged}

    assert "us-ca-san-francisco" in by_id
    assert "us-co-denver" in by_id
    assert "us-ut-salt-lake-city" in by_id
    assert "us-wy-cheyenne" in by_id
    assert by_id["us-ca-san-francisco"]["display_name"] == "San Francisco, California, United States"
    assert by_id["us-ca-san-francisco"]["source"] == "manual_fixture"
    assert isinstance(by_id["us-ca-san-francisco"]["selection_classes"], list)
    assert by_id["us-wy-cheyenne"]["source"] == "manual_fixture"


def test_fixture_catalog_has_v04_scale_and_metadata():
    with open(
        "products/location_services/place_resonance_search/data/us_candidate_fixture.json",
        "r",
        encoding="utf-8",
    ) as handle:
        parsed = json.load(handle)

    candidates = load_candidate_catalog()

    assert parsed["catalog_version"] == "place_resonance_search_candidates_v0.4.0"
    assert len(candidates) >= 156
    assert sum(1 for candidate in candidates if candidate["selection_classes"]) >= 101
    assert any("2026-07-16" in note for note in parsed["notes"])


def test_provider_helpers_keep_stable_ids_and_tiers():
    assert build_location_id("US", "NY", "New York") == "us-ny-new-york"
    assert population_tier(2_000_000) == "major_metro"
    assert population_tier(500_000) == "large_metro"
    assert population_tier(100_000) == "mid_metro"
    assert population_tier(25_000) == "small_metro"
    assert population_tier(24_999) == "small_town"


def test_provider_dedupe_keeps_larger_duplicate_location_id():
    small = geonamescache_city_to_candidate({
        "geonameid": 1,
        "name": "Brentwood",
        "latitude": 37.0,
        "longitude": -121.0,
        "countrycode": "US",
        "population": 1000,
        "timezone": "America/Los_Angeles",
        "admin1code": "CA",
    })
    large = geonamescache_city_to_candidate({
        "geonameid": 2,
        "name": "Brentwood",
        "latitude": 37.9,
        "longitude": -121.7,
        "countrycode": "US",
        "population": 65000,
        "timezone": "America/Los_Angeles",
        "admin1code": "CA",
    })

    deduped = dedupe_candidates_by_location_id([small, large])

    assert len(deduped) == 1
    assert deduped[0]["provider_metadata"]["geoname_id"] == "2"
