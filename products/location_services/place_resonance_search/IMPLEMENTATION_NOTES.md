# Place Resonance Search Implementation Notes

This product is the emerging discovery/search flagship for Location
Services.

## Key Principles

- **Discovery First**: This product should eventually surface a curated set
  of symbolically meaningful places rather than asking the user to begin
  with one already-chosen city.
- **Current Bootstrap State**: For now, this package reuses the existing
  single-location Place Resonance evidence and render path so the renamed
  product can exist structurally before the discovery pipeline is built.
- **Assimilation Target**: The current single-location Place Resonance
  report is expected to become a reusable place-profile unit inside this
  broader product.
- **No Bulk Ranking Theater**: The future product should present a curated
  set of locations and interpretable buckets, not a long ranked dump.
- **No Capability Inflation**: This package does not yet implement a
  candidate catalog, multi-location scoring, or bucket assignment. Those
  remain future work.
