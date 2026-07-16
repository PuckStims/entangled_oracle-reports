# Location Services Remaining Method Boundaries Spec

Status date: 2026-07-16

Purpose: define the current method boundaries that remain after the v0.2
computation pass for World Lines Companion, Local Compass, and Living Map.
This file is the current source of truth for what is implemented, what is
still excluded, what evidence contract is required next, and what must be true
before prose may treat a method as live.

This spec does not replace the older historical contracts. It sits on top of
them and corrects their old all-or-nothing v0.1 assumption. When an older doc
says astrocartography, Local Space, or dynamic timing is unsupported in full,
read that as historical context unless a newer product or engine contract says
otherwise.

## Current Repo Truth

Implemented foundations:

- `engine/world_lines.py` computes v1 planetary ASC, DSC, MC, and IC line
  proximity with `FORMULA_VERSION = "world_lines_v0.2.0"`.
- `engine/local_space.py` computes v1 local-space azimuths, altitude,
  destination bearing, and cross-track distance with
  `FORMULA_VERSION = "local_space_v0.2.0"`.
- `engine/living_map.py` computes v1 date-bounded transits to relocated angles
  with `FORMULA_VERSION = "living_map_v0.2.0"`.
- The three product assemblers now resolve consumer place names into coordinate
  context and render evidence-backed prose bodies rather than computation
  placeholders.

Still excluded:

- parans
- remote activation
- line-crossing interpretation
- relocated returns
- dynamic astrocartography
- purpose-ranked timing

Global invariants that remain non-negotiable:

- Preserve the natal UTC instant.
- Never recompute natal condition from a relocated payload.
- Never substitute one method for another in prose.
- Never promote an unavailable method through implication, template wording, or
  fallback visuals.
- Every method must declare its own `unsupported_methods` or equivalent
  boundary language until the method is fully contracted and tested.

## Status Matrix

| Area | Current status | Current live evidence | Still excluded | Next required contract |
| --- | --- | --- | --- | --- |
| World line proximity | Implemented foundation | nearest point, distance, distance band, birth-time sensitivity | parans, remote activation, line-crossing interpretation | continuous strength policy and cluster/link schema only if needed |
| Local-space direction | Implemented foundation | azimuth, altitude, direction label, destination bearing, cross-track distance, weighted score, rank, route corridor geometry | none at the core geometry layer | route-aware weighting only if later needed |
| Relocated timing windows | Implemented foundation | date-bounded transits to relocated angles | relocated returns, dynamic astrocartography, purpose-ranked timing | stronger timing confidence contract and purpose-ranking contract |
| Parans | Not implemented | none | all interpretive use | paran evidence schema |
| Remote activation | Not implemented | none | all interpretive use | remote-activation evidence schema |
| Line-crossing interpretation | Not implemented | none | all interpretive use | crossing/cluster evidence schema |
| Route-corridor geometry | Not implemented | none beyond cross-track distance | travel or path claims | corridor geometry schema |
| Direction strength weighting | Not implemented | none beyond raw azimuth/cross-track | ranked directional claims | strength-weight contract |
| Relocated returns | Not implemented | none | return-chart timing claims | relocated-return baseline contract |
| Dynamic astrocartography | Not implemented | none | moving-map or evolving-line claims | time-varying map contract |
| Purpose-ranked timing | Not implemented | none beyond generic timing windows | purpose-fit timing claims | purpose ranking contract |

## Shared Release Gates

A remaining method is not ready for consumer prose until all of the following
exist:

- A named engine or evidence-layer contract with explicit input requirements.
- A stable output schema with typed field expectations.
- Product-level tests that assert both positive evidence shape and negative
  boundary behavior.
- Technical appendix language that describes the real method without implying
  adjacent unbuilt methods.
- Removal or narrowing of the method from the relevant `unsupported_methods`
  list.
- A generator or registry smoke path proving the method survives full report
  assembly.

## Method Specs

### 1. Parans

Definition:
Planetary relationships created by simultaneous angularity or near-simultaneous
angular events at a place, distinct from ordinary nearest-line proximity.

Required inputs:

- destination latitude and longitude
- preserved natal Julian Day
- standard planet set used by the map engine
- explicit angular event definition and tolerance policy

Minimum output contract:

- `id`
- `body_1`
- `body_2`
- `event_pair`
- `latitude_band` or equivalent spatial anchor
- `orb_or_time_delta`
- `strength`
- `birth_time_sensitivity`
- `geometry_method`
- `claim_boundary`

Claim boundary:

- Do not infer parans from line proximity alone.
- Do not collapse parans into line clusters or crossings.
- Do not use SVG overlap as paran evidence.

Verification gate:

- tests for at least one positive paran case
- tests proving line proximity does not generate false paran evidence
- product appendix disclosure of tolerance policy

### 2. Remote Activation

Definition:
Non-local engagement with a line or place signature without physically being at
the destination.

Required inputs:

- declared activation model
- explicit place-to-object or place-to-practice linkage rules
- confidence policy separate from physical-location evidence

Minimum output contract:

- `id`
- `target_line_or_place_id`
- `activation_channel`
- `evidence_basis`
- `confidence`
- `claim_boundary`

Claim boundary:

- No remote activation claims may be generated from destination coordinates
  alone.
- No consumer prose may imply symbolic contact at a distance until a distinct
  method exists.

Verification gate:

- standalone contract doc before any engine work
- tests proving ordinary map evidence cannot emit remote-activation language

### 3. Line-Crossing Interpretation

Definition:
A localized multi-line concentration or crossing event that is stronger or more
complex than a single nearest line.

Required inputs:

- computed line geometry for the participating bodies and angles
- crossing or cluster definition
- distance and clustering tolerances

Minimum output contract:

- `id`
- `members`
- `crossing_type`
- `anchor_point`
- `distance_to_destination`
- `strength`
- `interpretive_priority`
- `claim_boundary`

Claim boundary:

- Do not treat two nearby entries in the nearest-line list as a crossing.
- Do not describe clusters until a real cluster or intersection method exists.

Verification gate:

- geometry tests for true intersection or cluster cases
- negative tests where close but non-intersecting lines do not produce a
  crossing

### 4. Route-Corridor Geometry

Status:
Implemented in v1 for Local Compass.

Definition:
A directional-path method that compares a real route or movement corridor to
local-space planetary rays, rather than comparing only a point destination.

Required inputs:

- anchor coordinates
- route polyline or ordered waypoint list
- local-space azimuth model
- corridor width policy

Minimum output contract:

- `id`
- `body`
- `route_id`
- `closest_route_segment`
- `minimum_offset_km`
- `overlap_length_km` or corridor-presence boolean
- `strength`
- `claim_boundary`

Claim boundary:

- Cross-track distance to a single destination is not route geometry.
- No travel-optimization prose until route evidence exists.

Current implementation:

- `engine/local_space.py` accepts an optional route polyline as waypoint pairs.
- It emits `route_geometry` per direction with `route_id`,
  `closest_route_segment`, `minimum_offset_km`, `overlap_length_km`,
  `strength`, `claim_boundary`, and `geometry_method`.
- Anchor-only and point-destination reports remain valid when no route is
  supplied.

Still excluded:

- route optimization
- path recommendation
- route-aware strength weighting

Verification gate:

- tests for route overlap and non-overlap
- tests that anchor-only mode remains valid without fake route evidence

### 5. Direction Strength Weighting

Status:
Implemented in v1 for Local Compass.

Definition:
A ranking model that says which local-space directions should count more than
others, beyond simple azimuth presence.

Required inputs:

- explicit weighting factors
- priority order across altitude, angular relevance, natal condition, and
  destination alignment
- normalization policy

Minimum output contract:

- `id`
- `body`
- `raw_inputs`
- `weighted_score`
- `weight_components`
- `rank`
- `claim_boundary`

Claim boundary:

- Do not imply that earlier or lower azimuth values are stronger.
- Do not use practical mode labels as hidden strength labels.

Current implementation:

- `engine/local_space.py` emits `raw_inputs`, `weight_components`,
  `weighted_score`, and `rank` per direction.
- Current factors are altitude relevance, natal angular relevance, natal
  condition strength, and destination alignment.
- Tie-break policy is deterministic: higher `weighted_score` first, then body
  name ascending.

Still excluded:

- route-aware weighting
- corridor or travel-path ranking
- user-purpose reranking of directions

Verification gate:

- ranking determinism tests
- tests for stable tie handling
- appendix disclosure of score components

### 6. Relocated Returns

Definition:
Return charts or return-like timing charts calculated for a destination-aware
relocated context.

Required inputs:

- preserved natal baseline
- explicit return type definition
- destination coordinates
- clock and timezone policy for return timing

Minimum output contract:

- `id`
- `return_type`
- `return_datetime_utc`
- `destination`
- `linked_static_evidence_ids`
- `timing_window`
- `confidence`
- `claim_boundary`

Claim boundary:

- Transit-to-relocated-angle timing is not a relocated return.
- No return-chart prose should appear inside Living Map until this method is
  separately contracted.

Verification gate:

- return calculation tests
- proof that static baseline bytes remain unchanged when return evidence is
  added

### 7. Dynamic Astrocartography

Definition:
Time-varying map behavior where line relevance changes across a date range or
moving chart state, rather than static natal line proximity.

Required inputs:

- static world-line baseline
- explicit temporal driver
- date range
- refresh cadence

Minimum output contract:

- `id`
- `body`
- `angle`
- `time_window`
- `map_state_type`
- `delta_from_static_baseline`
- `confidence`
- `claim_boundary`

Claim boundary:

- Static line distance is not dynamic map evidence.
- Living Map timing windows do not authorize moving-line or map animation
  claims.

Verification gate:

- tests for time-window state transitions
- tests distinguishing static map evidence from dynamic map evidence

### 8. Purpose-Ranked Timing

Definition:
A method that ranks timing windows by purpose lens such as career, rest,
partnership, retreat, or travel strategy.

Required inputs:

- timing windows
- static place baseline
- purpose taxonomy
- ranking model tying timing to supported evidence

Minimum output contract:

- `id`
- `purpose_lens`
- `window_id`
- `support_score`
- `reasons`
- `contraindications`
- `claim_boundary`

Claim boundary:

- Generic timing windows do not yet justify purpose-fit claims.
- Do not rank by purpose until the taxonomy and ranking evidence are both
  stable.

Verification gate:

- tests proving each ranked output cites real static and dynamic evidence
- tests for disagreement or mixed-signal cases

## Product-Specific Guidance

World Lines Companion:

- Consumer-ready today for line proximity.
- Not consumer-ready for parans, remote activation, or line-crossing
  interpretation.
- Any future crossing or paran work must remain downstream of tested geometry,
  not template grouping.

Local Compass:

- Consumer-ready today for azimuth-led directional interpretation,
  destination-point comparison, v1 strength-ranked direction summaries, and
  route-corridor geometric alignment.
- Not consumer-ready for route optimization or travel-advice claims.

Living Map:

- Consumer-ready today for transits to relocated angles over a bounded date
  range.
- Not consumer-ready for return-chart timing, moving-map logic, or purpose-fit
  timing recommendations.
- Static place baseline must remain the interpretive anchor even after future
  timing layers are added.

## Recommended Next Build Order

1. Line-crossing interpretation
2. Purpose-ranked timing
3. Parans
4. Relocated returns
5. Dynamic astrocartography
6. Remote activation

Rationale:

- The first two build most directly on evidence already present in the repo.
- Parans and relocated returns are meaningful but require more careful method
  design and testing.
- Dynamic astrocartography and remote activation are the highest-risk areas for
  claim drift and should stay later.

## Completion Signal

This spec should be updated whenever one of the remaining methods:

- gains a real output schema
- loses or narrows its unsupported status
- becomes available to prose
- changes the recommended build order
