# Synastry Engine Contract

Status: engine evidence layer implemented; round-1 selector, assembly, and
HTML preview wiring implemented for testing; client-facing product integration
still not live.

Formula version: `synastry_computation_v0.2.0`

Schema version: `synastry_pair_v0.1`

## Purpose

The synastry engine turns two already-built natal payloads into a pair-chart
evidence object. It preserves the separateness of both source charts and does
not create a relationship verdict, compatibility score, diagnosis, prediction,
or client-facing interpretation.

This layer exists so later report and prose systems can select material from
traceable computations instead of asking prose to infer structure on its own.

## Entry Points

- `engine/synastry.py::build_pair_payload`
- `engine/synastry.py::generate_pair_payload`

Both entry points accept:

- `person_a_natal_payload`
- `person_b_natal_payload`
- optional `relationship_meta`

The natal payloads should come from `engine/natal_engine.py::generate_payload`
or deterministic tests that preserve the same key structure.

## Implemented Layers

The following sidecar statuses are expected to be `implemented_verified`:

- `pair_payload`
- `directional_aspects`
- `mutual_aspects`
- `house_overlays`
- `composite_midpoint_bodies`
- `composite_aspects`
- `repeated_natal_themes`
- `relationship_topic_signatures`
- `relationship_convergence`

The following remain `not_implemented`:

- `composite_houses`
- `davison`
- `relationship_timing`

## Pair Payload Shape

Top-level keys:

- `schema_version`
- `person_a`
- `person_b`
- `relationship_meta`
- `computations`
- `confidence`
- `sidecar`
- `provenance`

Each person record includes:

- `label`
- `natal_payload`
- `birth_time_state`
- `angle_eligible`

The pair payload does not mutate either source natal payload.

## Confidence And Withholding Policy

Birth-time states are read from natal payload `user_profile` fields:

- `exact_birth_time`
- `approximate_birth_time`
- `provisional_near_horizon`
- `unknown_birth_time`

Angle eligibility is true for exact, approximate, and provisional states. It is
false for unknown birth time.

Body-to-body contacts remain computable when one or both charts have unknown
birth time, as long as both body longitudes exist.

Angle contacts require the chart that owns the angle to be angle-eligible.
Unavailable angle-dependent records are emitted as withheld records with:

- `withheld: true`
- `confidence_state: angle_dependent_unavailable`
- `withheld_reason: withheld_angle_dependency`
- `missing_inputs`

House overlays require the chart that owns the houses to be angle-eligible. If
the house owner's birth time is unknown, overlays into that person's houses are
withheld with:

- `withheld_reason: withheld_missing_birth_time`

If the target Ascendant field is missing even though the chart is marked
angle-eligible, overlays are withheld with:

- `withheld_reason: withheld_missing_payload_field`

## Body And Point Eligibility

Core bodies:

- Sun
- Moon
- Mercury
- Venus
- Mars
- Jupiter
- Saturn
- Uranus
- Neptune
- Pluto

Optional bodies are included only when present in both payloads:

- Chiron
- North_Node
- South_Node

Angles and points:

- Ascendant
- Descendant
- Midheaven
- Imum_Coeli
- Vertex

Asteroids are intentionally not included in this first synastry contract.

## Directional Aspects

Directional aspects are emitted for A-to-B and B-to-A routes. Direction is a
routing property, not a blame or causality claim.

Each live record includes:

- source and target person/body
- aspect
- exact angle
- measured distance
- orb
- max orb
- orb fraction
- source and target domains
- dependency type
- confidence state

The current synastry orb cap is:

- `config.ORB_CONFIG["max_orb_synastry"]`

No synastry aspect should exceed that cap.

## Mutual Aspects

Mutual records group directional body pairs into one traceable contact. They:

- preserve directional records
- expose one canonical aspect identity
- classify body-only vs angle-dependent contact
- compute salience for ranking

Salience is a ranking signal only. It is not a truth claim and must not be
displayed as a compatibility percentage.

## House Overlays

House overlays are directional:

- A body in B house
- B body in A house

Whole Sign localization uses the house owner's Ascendant sign and existing
house payload where available. If the house payload is missing a sign, the
engine falls back to the Ascendant sign order.

## Composite

The implemented composite method is:

- `midpoint_composite`

The engine computes:

- matching body midpoints
- midpoint ambiguity flags for exact opposite points
- composite body-to-body aspects among non-ambiguous midpoint bodies

Composite houses are not implemented. A midpoint composite does not inherit one
person's houses.

Davison is not implemented and should remain separate from midpoint composite
work.

## Repeated Natal Themes

Repeated natal themes compare existing natal structures without interpretation.
Implemented theme families:

- shared sign emphasis
- shared element concentration
- shared modality concentration
- repeated natal aspect family
- shared house emphasis when both charts are angle-eligible

These records identify evidence from each natal payload and include salience
for ranking.

## Relationship Topic Signatures

Topic signatures aggregate evidence families into report-selectable structures.
Implemented initial topics:

- attachment/emotional rhythm
- affection/value/attraction
- desire/friction/action
- communication
- commitment/constraint/time
- visibility/public path
- growth/meaning
- intensity/merging/shared resources

Each signature exposes:

- contributing record references
- supportive/tensional/mixed distribution
- confidence by evidence family
- evidence family scores
- localization type
- score
- polarity

These are not prose summaries.

## Relationship Convergence

Relationship convergence ranks topic signatures for later report selection.

Each convergence record includes:

- `signature_key`
- `score`
- `polarity`
- `evidence_count`
- `independent_evidence_families`
- `confidence_state`
- `trace`

Convergence must not be converted into labels such as compatible, doomed,
soulmate, destined, or any deterministic relationship judgment.

## Sidecar Claim Safety

The sidecar includes:

- computation statuses
- withheld summary
- claim safety flags

Current required claim-safety values:

- `client_report_available: false`
- `relationship_verdicts_supported: false`

Report surfaces must read the sidecar before claiming a synastry layer is live.

## Prose And Template Boundary

No client product template should call synastry available until a separate
integration pass promotes the draft selector/preview surface into a supported
report route and verifies output behavior there.

Round-1 prose blocks are now authored and can be exercised through the draft
selector, context assembler, and HTML preview surface. That preview remains a
testing lane rather than a product claim.
