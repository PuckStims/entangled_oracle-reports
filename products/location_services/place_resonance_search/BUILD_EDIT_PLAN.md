# Place Resonance Search Build Edit Plan

Status date: 2026-07-16

## Purpose

`Place Resonance Search` is the flagship discovery product for Location
Services. Its job is to evaluate a curated set of candidate places, surface the
locations whose symbolic field is most worth attention, and explain why each
selected place matters.

This is not a bulk ranking product. The intended report is a curated relocation
intelligence brief with clear buckets, direct guidance, and technical
traceability.

## Current Repo State

- This product folder exists and is registry-wired.
- It currently reuses the existing single-location Place Resonance context and
  render path through wrapper modules.
- The current implementation is transitional: it gives the search product a
  stable identity before candidate-pool, scoring, curation, and bucket logic are
  built.
- The wrapped single-location implementation should be understood as the
  reusable Place Profile engine.
- An expanded seeded U.S. candidate catalog now exists in
  `data/us_candidate_fixture.json`.
- The active bank now contains 156 deduplicated U.S. locations merged from the
  original seed file, Astrocartography fixture waves 1 and 2, ontology wave
  2026-07-15, and thin-state coverage wave 2026-07-16. The provider-backed
  catalog seam is the intended path beyond fixture scale.
- Batch evidence generation, deterministic first-pass scoring, curated
  selection, bucket assignment, and Search result context assembly now exist.
- Scoring now preserves raw symbolic evidence and normalizes displayed scores
  relative to the evaluated candidate pool using percentile-clipped min/max
  scaling. Score bars should be read as pool-relative indexes, not universal
  measurements.
- `place_resonance_search_blocks.json` now defines authored leaves for search
  summary, bucket intros, recommendation labels, and pattern synthesis.
- A true multi-location HTML renderer now exists for Search result contexts.
- `products/location_services/tooling/generate_place_resonance_search_ready.py`
  can generate a candidate-catalog Search HTML draft from birth data.

## Build Goal

Turn this package from a wrapper identity into a real search/discovery pipeline:

1. Evaluate a local candidate pool.
2. Generate one Place Profile evidence record per candidate.
3. Score candidates across resonance dimensions.
4. Select a curated set of locations.
5. Assign interpretive buckets.
6. Render search-level synthesis plus compact profile guidance.

Full provider/catalog build outline:
`products/location_services/BUILD_OUTLINE_DRIFT_GUARD.md` Build Area E.

## Search Dimensions

Initial scoring should support these dimensions:

- Visibility & Calling
- Belonging & Bonds
- Hearth & Restoration
- Study & Signal
- Creative Culture
- Long-Term Build
- Change & Aliveness
- Shadow Pressure

Search output should include multiple indexes rather than a single score:

- Resonance Score
- Theme Fit
- Complexity Index
- Novelty / Baseline Divergence
- Consensus Score
- Grounding Score

## Selection Buckets

- **Highest Resonance** - strongest multi-indicator support.
- **Goal-Specific Allies** - excellent for a defined theme, not universally easy.
- **Transformational / Demanding Places** - powerful, complex, high-pressure
  locations.
- **Quiet or Grounding Alternatives** - gentler support, lower drama, or
  stabilizing emphasis.
- **Pattern Outliers** - unusual chart shifts or surprising symbolic contrast.

## Build Sequence

1. Keep this package as a stable parallel product identity.
2. Preserve output compatibility with the reusable single-place profile engine.
3. Use the provider-backed catalog path for production-scale candidate pools;
   treat the JSON fixture as a curated EO overlay and regression fixture.
4. Keep batch profile generation covered by no-mutation tests for natal payloads
   and candidate records.
5. Refine scoring and bucket-assignment weights as the astrology model matures.
6. Strengthen curated selection rules to avoid near-duplicate outputs.
7. Keep expanding the multi-location renderer as the prose and section model
   mature.
8. Continue auditing and expanding the search-specific prose families for
   summary, buckets, recommendations, and pattern synthesis.
9. Route future interpretation refinements through the normalized evidence
   grammar before broad prose upgrades.

## Edit Rules

- Do not treat pool-relative score bars as universal measurements.
- Do not remove the current single-location interpretation path until its
  reusable profile role is stable.
- Keep naming clear so future agents do not confuse the search product with the
  single-location profile logic it currently wraps.
- Treat confidence as necessary. Avoid guarantees, commands, and universal
  verdicts, but do not dilute clear evidence into decorative ambiguity.
- Do not add practical city claims unless a reliable non-astrological data
  source is present and labeled separately.

## Immediate Next Edits

- Audit rendered Search prose in `place_resonance_search_blocks.json`.
- Decide which score weights should be content-approved versus engineering
  defaults.
- Review generated Search HTML after the first prose pass.
- Keep normalizing metadata vocabularies as new catalog waves are added.
- Use the provider-backed catalog path for 500+ candidate pools rather than
  continuing to hand-expand `us_candidate_fixture.json`.
- Preserve evaluated-pool metadata in the result context: provider source,
  filters, candidate limit, curated overlay status, selected count, and any
  regional collapse rules.
- Add any future Search interpretation upgrades through the normalized evidence
  grammar, resolver, theme clusterer, and report planner rather than adding
  direct prose-only score explanations.

## Verification

- `tests/test_location_services_product_registry.py`
- `tests/test_place_resonance_search_package_layout.py`
- `tests/test_place_resonance_search_contract.py`
- `tests/test_place_resonance_search_provider_catalog.py`
- `products/location_services/tooling/generate_place_resonance_search_ready.py`
- Provider catalog import/query tests should stay green before relying on
  500+ candidate pools.

## Sample Generation

Import a GeoNames-style provider dump into the local SQLite catalog:

```powershell
.\.venv\Scripts\python.exe products\location_services\tooling\import_location_catalog.py --geonames-path C:\data\geonames\cities500.txt --min-population 5000 --limit 5000
```

Generate from the provider catalog, with the curated JSON fixture merged as an
EO overlay:

```powershell
.\.venv\Scripts\python.exe products\location_services\tooling\generate_place_resonance_search_ready.py --name "Sample" --date 1990-06-15 --time 14:22 --location "Chicago, Illinois, United States" --location-catalog-db products\location_services\place_resonance_search\data\location_catalog.sqlite --min-population 5000 --candidate-limit 500 --purpose-lens "creative visibility" --relationship-to-place "possible_move" --selection-limit 8
```

Curated JSON-fixture generation still works for regression and small local
runs:

```powershell
.\.venv\Scripts\python.exe products\location_services\tooling\generate_place_resonance_search_ready.py --name "Sample" --date 1990-06-15 --time 14:22 --location "Chicago, Illinois, United States" --purpose-lens "creative visibility" --relationship-to-place "possible_move" --selection-limit 8
```
