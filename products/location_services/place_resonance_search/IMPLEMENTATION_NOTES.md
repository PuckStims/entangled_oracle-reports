# Place Resonance Search Implementation Notes

This product is the emerging discovery/search flagship for Location
Services.

## Key Principles

- **Discovery First**: This product should eventually surface a curated set
  of symbolically meaningful places rather than asking the user to begin
  with one already-chosen city.
- **Current Bootstrap State**: This package now has a real first-pass
  discovery pipeline: candidate loading, batch evidence generation,
  deterministic scoring, curated selection, bucket assignment, and a
  multi-location renderer. The single-location Place Resonance path still
  supplies the reusable place-profile evidence unit.
- **Assimilation Target**: The current single-location Place Resonance
  report is expected to become a reusable place-profile unit inside this
  broader product.
- **No Bulk Ranking Theater**: The future product should present a curated
  set of locations and interpretable buckets, not a long ranked dump.
- **Provider Catalog Path**: The bundled JSON fixture is a curated overlay,
  not the production universe. Use the provider-backed SQLite catalog path
  for 500+ candidate pools.
- **Grammar Alignment**: Future scoring/prose refinement should inspect the
  normalized evidence grammar in `products/location_services/evidence_grammar/`
  rather than adding one-off interpretation fields directly to Search.
