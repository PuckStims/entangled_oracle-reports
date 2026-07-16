# Location Services Build Outline Drift Guard

**Status date:** 2026-07-16  
**Purpose:** Preserve full build outlines for referenced Location Services work
so future agents do not shrink a phase into a label, adapter, or prose pass.

This document is not a replacement for product specs. It is the implementation
shape that referenced plans should point back to when they say "resolver,"
"theme clusterer," "goal compatibility," "report planner," "provider catalog,"
"comparison layer," "line engine," "direction engine," or "timing overlay."

## Operating Rule

No referenced build area is complete because a file exists. It is complete when
it has:

- input contract
- output contract
- non-goals
- build sequence
- tests
- appendix or trace disclosure
- current-product integration point

If any of those are missing, the area remains partial.

## Current Foundation

Already implemented or started:

- `LocationEvidenceRecord` generation from relocated chart evidence.
- Place Profile / legacy Place Resonance one-location assembly and rendering.
- Place Resonance Search candidate fixture, provider-backed catalog seam,
  scoring, selection, buckets, and multi-location rendering.
- Phase 1 `products/location_services/evidence_grammar/` adapter that emits
  normalized evidence items from current evidence records.

Not yet complete:

- evidence resolver
- theme clusterer
- goal compatibility profile
- report planner
- real Between Places comparison engine
- astrocartography line geometry and distance engine
- Local Compass azimuth/direction engine
- Living Map relocated timing overlay

## Shared Grammar Pipeline

Build all interpretation through this order:

```text
Calculation
-> LocationEvidenceRecord
-> normalized evidence items
-> evidence resolver
-> theme clusters
-> goal compatibility profile
-> report plan
-> prose or rendered sections
```

Do not route raw calculations directly into expanded prose except in existing
stable report paths. Do not use goal inputs to rewrite technical evidence.

## Build Area A: Evidence Resolver

### Purpose

Turn normalized evidence items into relationship-aware evidence groups. The
resolver answers whether evidence is independent repetition, same-root
confirmation, contradiction, or compensation.

### Inputs

- normalized evidence items from `evidence_grammar`
- source evidence IDs
- family, subject, interface, themes, supports, costs
- strength and confidence
- source factors such as orb, house movement, birth-time confidence, and
  unavailable-method status

### Outputs

- `resolved_evidence_version`
- `resolved_groups`
- group fields:
  - `group_id`
  - `relationship_type`
  - `theme_keys`
  - `member_evidence_ids`
  - `representative_evidence_id`
  - `combined_strength`
  - `combined_confidence`
  - `breadth_score`
  - `precision_score`
  - `claim_boundary`
  - `resolution_note`

### Relationship Types

- `independent_repetition`: different families support the same theme.
- `same_root_confirmation`: multiple items describe the same geometry or root
  fact and should increase precision, not breadth.
- `contradictory_axis`: items support conflicting needs or conditions.
- `compensatory_structure`: one item helps contain or organize another.
- `single_signal`: meaningful but not repeated.
- `low_signal`: too weak or unstable to foreground.

### Build Sequence

1. Index items by `evidence_id`, `family`, `subject`, `interface`, and theme.
2. Mark unavailable-method items as appendix-only, never computed groups.
3. Detect same-root angle/house repetitions by shared body and source geometry.
4. Detect independent repetition by shared themes across different families.
5. Detect contradiction through explicit opposing theme pairs.
6. Detect compensation through stabilizing themes such as structure,
   containment, restoration, grounding, or boundary.
7. Emit deterministic groups sorted by priority.
8. Preserve all member evidence IDs for traceability.

### Non-Goals

- Do not author prose.
- Do not infer astrocartography, Local Space, parans, or timing.
- Do not average contradictions into neutral language.
- Do not treat same-body repetition as independent unless source families
  genuinely differ.

### Tests

- same-root angle plus related house item increases precision but not breadth
- Venus angle plus Venus house uses same-root confirmation when appropriate
- MC visibility versus IC privacy emits contradictory axis
- Saturn structure can compensate Neptune/Moon sensitivity when both are present
- unavailable methods never enter computed groups
- output order is deterministic
- input items are not mutated

## Build Area B: Theme Clusterer

### Purpose

Convert resolved evidence groups into reader-facing interpretive clusters while
still remaining pre-prose.

### Inputs

- resolved evidence groups
- normalized evidence items
- optional product context: profile, search, comparison, map, compass, timing

### Outputs

- `theme_cluster_version`
- `clusters`
- cluster fields:
  - `cluster_id`
  - `cluster_type`
  - `headline_key`
  - `theme_keys`
  - `supporting_group_ids`
  - `tension_group_ids`
  - `strength_band`
  - `confidence_band`
  - `opportunity_tags`
  - `pressure_tags`
  - `duration_hint`
  - `omit_from_primary_report`

### Cluster Types

- `convergent_theme`
- `contradictory_axis`
- `compensatory_structure`
- `mixed_location`
- `low_signal`
- `technical_context`
- `time_sensitive_overlay`

### Build Sequence

1. Gather groups by theme key and relationship type.
2. Assign cluster type from the strongest relationship pattern.
3. Band strength as `defining`, `strong`, `supportive`, `background`, or
   `unstable`.
4. Band confidence as `high`, `medium`, `low`, or `sensitive`.
5. Preserve pressure and opportunity separately.
6. Mark low-signal clusters as appendix or omitted material.
7. Emit deterministic clusters for report planning.

### Non-Goals

- Do not decide a city is "best."
- Do not create final paragraphs.
- Do not hide pressure tags when opportunity is strong.

### Tests

- convergent themes form from independent repetition
- contradiction clusters retain both sides
- low-confidence clusters cannot become defining
- technical warnings stay technical
- ordering is stable for identical inputs

## Build Area C: Goal Compatibility Profile

### Purpose

Rank relevance for user purposes without changing technical evidence.

### Inputs

- theme clusters
- normalized evidence items
- user purpose lens
- optional relationship to place
- optional future constraints: time horizon, avoidances, sensory needs,
  practical requirements

### Outputs

- `goal_profile_version`
- per-goal records with:
  - `goal_key`
  - `opportunity`
  - `ease`
  - `demand`
  - `durability`
  - `volatility`
  - `supporting_cluster_ids`
  - `caution_cluster_ids`
  - `fit_label`
  - `fit_explanation_key`

### Required Goal Dimensions

- career visibility
- creative production
- artistic reception
- study and writing
- partnership
- friendship and community
- family life
- domestic restoration
- healing and recovery
- spiritual retreat
- activism
- reinvention
- financial consolidation
- long-term settlement
- short-term catalytic visit
- solitude
- adventure and exploration

### Build Sequence

1. Create a static taxonomy mapping themes to goal dimensions.
2. Score each dimension across opportunity, ease, demand, durability, and
   volatility.
3. Apply purpose lens as relevance weighting only.
4. Emit labels such as `strong_but_demanding`, `supportive_and_stable`,
   `promising_but_volatile`, `quietly_useful`, or `low_relevance`.
5. Keep all cluster IDs attached for audit.

### Non-Goals

- Do not use goals to alter evidence strength.
- Do not say a place guarantees success, healing, love, or safety.
- Do not collapse opportunity and ease into one score.

### Tests

- same evidence with different purpose lens changes relevance, not evidence
- strong visibility evidence can be high opportunity and high demand
- quiet restorative evidence can outrank public evidence for rest purposes
- missing purpose emits neutral multi-goal profile

## Build Area D: Report Planner

### Purpose

Create an ordered narrative plan that prose can later fill. This is the bridge
between structured evidence and report sections.

### Inputs

- theme clusters
- goal compatibility profile
- product type
- source contexts: profile, search, comparison, map, compass, timing

### Outputs

- `report_plan_version`
- `product_type`
- `thesis_key`
- `dominant_pattern_cluster_id`
- `primary_tradeoff_cluster_id`
- `supporting_cluster_ids`
- `best_use_goal_keys`
- `mismatched_use_goal_keys`
- `duration_profile`
- `confidence_classification`
- `section_plan`
- `appendix_inputs`

### Section Plan Fields

Each section plan item should include:

- `section_id`
- `purpose`
- `source_cluster_ids`
- `source_evidence_ids`
- `required_disclosures`
- `prose_status`
- `claim_boundary`

### Build Sequence

1. Select dominant pattern from highest-priority clusters.
2. Select primary tradeoff when contradiction exists.
3. Select practical use guidance from goal profile.
4. Decide which evidence remains appendix-only.
5. Build section plan per product.
6. Emit enough traceability for renderer, prose composer, and appendix.

### Non-Goals

- Do not generate final report text.
- Do not invent missing sections to satisfy a template.
- Do not suppress uncertainty.

### Tests

- planner chooses dominant cluster deterministically
- contradiction creates a tradeoff section
- low-confidence evidence cannot be thesis material
- appendix input lists every excluded method and warning group

## Build Area E: Provider Catalog And Search Scale

### Purpose

Let Search evaluate large candidate pools without making the curated JSON
fixture pretend to be the whole world.

### Inputs

- provider-backed SQLite catalog
- optional GeoNames-style dump
- optional `geonamescache` bootstrap
- curated EO JSON overlay
- country/state/population filters

### Outputs

- query result candidates in Search candidate shape
- stable provider location IDs
- merged curated overlay fields
- appendix trace of provider source and filters

### Build Sequence

1. Keep `us_candidate_fixture.json` as curated overlay and regression fixture.
2. Import or bootstrap provider rows into SQLite.
3. Query by country, state, minimum population, active status, and limit.
4. Merge curated ontology fields by stable location ID.
5. Deduplicate by location ID and, later, geographic proximity.
6. Emit evaluated pool metadata in Search output.

### Non-Goals

- Do not hand-expand JSON to production scale.
- Do not make provider population or place names interpretive evidence.
- Do not call provider catalog coverage complete without source disclosure.

### Tests

- empty SQLite catalog initializes safely
- provider import deduplicates stable IDs
- query filters country/state/population correctly
- curated overlay merges without losing provider candidates
- generator works with and without `--location-catalog-db`

## Build Area F: Between Places Comparison Engine

### Purpose

Compare two to five real destinations using normalized evidence and goal
profiles without turning the output into a universal ranking.

### Inputs

- one immutable `LocationEvidenceRecord` per destination
- normalized evidence items per destination
- theme clusters per destination
- optional goal compatibility profile

### Outputs

- `comparison_record_version`
- destination summaries
- shared theme groups
- divergent theme groups
- strongest differences
- purpose fit comparison
- tradeoff map
- per-destination appendix traces

### Build Sequence

1. Build evidence record for each destination independently.
2. Normalize each record through `evidence_grammar`.
3. Resolve and cluster each destination independently.
4. Compare cluster keys, strength bands, confidence bands, and goal profiles.
5. Emit shared themes where multiple destinations activate similar material.
6. Emit divergent themes where strength, pressure, or goal fit differs.
7. Keep all destination evidence IDs namespaced by destination ID.
8. Render comparison sections from the comparison record.

### Non-Goals

- Do not declare a universal best place.
- Do not mutate the source records.
- Do not reuse one-place prose as if it were comparison prose.

### Tests

- identical destinations produce high overlap and low difference
- asymmetric angle contact appears as strongest difference
- purpose lens changes relevance labels but not evidence
- missing destination metadata surfaces technical note

## Build Area G: World Lines Companion Engine

### Purpose

Add real astrocartography line evidence only after geometry exists.

### Inputs

- natal chart data and birth-time confidence
- destination or region
- computed line geometry for ASC, DSC, MC, IC lines
- projection metadata

### Outputs

- line evidence items in normalized grammar shape
- nearest point and distance to destination
- distance band and continuous strength
- line clusters
- map trace metadata
- appendix disclosure

### Build Sequence

1. Define line evidence schema and tests before prose.
2. Implement or wrap line geometry generation.
3. Implement nearest-point and distance calculation.
4. Handle antimeridian, polar, and projection edge cases.
5. Define distance bands only after distance math is tested.
6. Emit line evidence through normalized grammar.
7. Render map sections from computed line evidence only.

### Non-Goals

- Do not infer lines from relocated angle contacts.
- Do not claim remote activation without a method contract.
- Do not show distance bands before distance computation exists.

### Tests

- known chart produces stable line geometry
- nearest-point distance is deterministic
- antimeridian cases do not flip lines
- birth-time sensitivity can mark line evidence unstable
- no line evidence appears when geometry is unavailable

## Build Area H: Local Compass Direction Engine

### Purpose

Compute Local Space style directional evidence instead of using relocation
evidence with compass language.

### Inputs

- natal chart data
- anchor location
- optional destination or route
- altitude/azimuth convention

### Outputs

- directional evidence items in normalized grammar shape
- planet azimuths
- direction sectors
- optional great-circle/ray geometry
- destination or route relationship to each direction
- confidence and convention disclosure

### Build Sequence

1. Decide and document the altitude/azimuth convention.
2. Compute planet azimuths from anchor location.
3. Bucket azimuths into cardinal/intercardinal sectors.
4. If destination is supplied, compute bearing and cross-track relationship.
5. Emit directional evidence through normalized grammar.
6. Render only computed directional evidence.

### Non-Goals

- Do not fake azimuths.
- Do not treat relocated houses as Local Space evidence.
- Do not provide practical guarantees about directions.

### Tests

- azimuth wraparound near 0/360 is stable
- sector bucketing is deterministic
- missing destination still supports anchor-only direction report
- unsupported convention emits technical note

## Build Area I: Living Map Timing Overlay

### Purpose

Attach date-bounded timing to static location evidence without rewriting the
permanent place baseline.

### Inputs

- static Place Profile evidence record
- normalized evidence, resolved groups, and clusters
- date range
- approved timing method
- transit or timing payload

### Outputs

- timing window records
- links from timing windows to static evidence IDs or cluster IDs
- baseline-vs-weather classification
- intensity and confidence
- timing appendix disclosure

### Build Sequence

1. Select one approved timing method for v1.
2. Define timing-window schema.
3. Compute timing triggers against relocated angles, houses, or evidence
   targets only where method is approved.
4. Link each window to static evidence IDs.
5. Separate `baseline` from `temporary_activation`.
6. Render timing windows with explicit date bounds.

### Non-Goals

- Do not use ordinary natal timing as relocated timing without governance.
- Do not make temporary activation sound permanent.
- Do not compute relocated returns until return method exists.

### Tests

- windows have start/end dates and linked evidence IDs
- overlapping windows sort deterministically
- missing timing data produces appendix note, not prose guess
- static baseline remains unchanged when timing is added

## Build Area J: Prose Expansion

### Purpose

Author prose only after the evidence planner can supply ordered, bounded
section plans.

### Inputs

- report plan
- section plan
- source evidence IDs
- claim boundaries
- product voice guides

### Outputs

- prose leaves or rendered section drafts
- source trace per section
- safety/disclosure notes

### Build Sequence

1. Keep placeholder `_note` guidance until report planner exists.
2. Author prose for sections with stable source clusters first.
3. Keep future-method and low-confidence areas appendix-only.
4. Add tests that no raw `TODO` appears in reader output.
5. Expand content banks after taxonomy is stable.

### Non-Goals

- Do not use prose to compensate for missing resolver/planner logic.
- Do not author large combination banks before taxonomy exists.
- Do not remove source trace from generated prose.

### Tests

- rendered output has no raw TODO
- section prose cites source evidence IDs or cluster IDs
- unsupported methods remain disclosed
- safety language blocks deterministic claims
