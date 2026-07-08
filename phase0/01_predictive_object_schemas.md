# Phase 0 — Predictive Object Schemas

Program: [EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md](../EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md)
Status: charter (Phase 0). Contracts. No implementation.
Version: `phase0.1.0`
Date: 2026-07-07

Every predictive object below is defined at the field level: name, type, cardinality, semantics, and provenance rule. Every implementation in Phases 1–8 builds against these contracts. When a scanner cannot supply a required field it must record why in `calculation_trace.missing_fields`, not silently drop it.

Type notation:

- `str` — string. Constrained values are noted inline as an enum.
- `int` — signed integer.
- `float` — 64-bit float. Angles are ecliptic degrees unless noted.
- `datetime` — ISO 8601 with timezone. All storage in UTC.
- `date` — ISO date.
- `bool` — boolean.
- `[T]` — ordered list of type T.
- `{K: V}` — mapping.
- `?T` — optional (nullable). Absence must be justified in `calculation_trace`.

Every object carries `schema_version: str` (default `phase0.1.0`) so downstream consumers can gate on shape without ambiguity.

---

## 1. `NatalPromiseAnchor`

A durable record of why a topic, domain, body, asteroid, angle, house, ruler, aspect pattern, or proprietary index is significant in a particular natal chart. Built once per natal snapshot and referenced by every downstream `PredictiveSignal`, `ChapterState`, and `MicroCandidate`.

### Fields

| Field | Type | Cardinality | Semantics |
|---|---|---|---|
| `schema_version` | `str` | 1 | `phase0.1.0` |
| `anchor_id` | `str` | 1 | Stable identifier scoped to the natal snapshot. Format `npa_<8-hex>`; generated from a canonical hash of `(natal_snapshot_id, topic_keys sorted, natal_bodies sorted, natal_asteroids sorted, houses sorted)`. |
| `natal_snapshot_id` | `str` | 1 | The natal snapshot this anchor was derived from (see sidecar contract §2). |
| `anchor_kind` | `str` | 1 | One of: `topic_focus`, `configuration`, `ruler_chain`, `index_signature`, `house_axis`, `angle_axis`, `named_pattern`. |
| `topic_keys` | `[str]` | 1..n | Archetypal topic tags (see topic taxonomy §7 below). |
| `domain_keys` | `[str]` | 0..n | House-domain tags: `identity`, `resources`, `communication`, `home`, `creativity`, `work`, `partnership`, `transformation`, `meaning`, `vocation`, `community`, `spirit`. |
| `natal_bodies` | `[str]` | 0..n | Planet or luminary names from natal payload (`Sun` … `Pluto`, `Chiron`, `North_Node`, `South_Node`, `Lilith_BML`). |
| `natal_asteroids` | `[str]` | 0..n | Asteroid names from `custom_asteroids`. |
| `houses` | `[int]` | 0..n | Whole-sign houses 1..12 relevant to this anchor. |
| `rulers` | `[str]` | 0..n | Body names that participate as domicile / exaltation / triplicity rulers of the relevant houses. |
| `dispositors` | `[str]` | 0..n | Bodies further up the dispositor chain from `rulers`, if the anchor invokes chain logic. |
| `aspects` | `[{body_a: str, body_b: str, aspect: str, orb: float}]` | 0..n | Aspects that constitute this anchor. Aspect names from `Conjunction`, `Sextile`, `Square`, `Trine`, `Opposition` (minor aspects reserved for future use). |
| `configurations` | `[str]` | 0..n | Named configurations from `formulas/standard/named_configurations.py` (e.g. `t_square`, `grand_trine`, `mystic_rectangle`). |
| `proprietary_index_links` | `[{index: str, dimension: str, driver_body: str, weight: float}]` | 0..n | Proprietary index references (KVQ, MKI, RWI, DFIS, CATALYST, AHL, NGE). |
| `strength` | `float` | 1 | Overall anchor salience in `[0.0, 1.0]`. Composed from constituent components; not opaque — see `strength_components`. |
| `strength_components` | `{str: float}` | 1 | Named contributors summed to `strength`: `body_prominence`, `aspect_tightness`, `configuration_bonus`, `index_link_bonus`, `angularity`, `sect_bonus`. |
| `confidence` | `float` | 1 | Independent of `strength`. In `[0.0, 1.0]`. Reduced by birth-time uncertainty when angular. |
| `birth_time_dependency` | `str` | 1 | One of: `none`, `soft` (house-only), `hard` (angle-required). |
| `evidence_trace` | `{str: any}` | 1 | Source rules that fired: index formula IDs, chart-structure findings, aspect-matrix cells. Must permit reconstruction. |
| `created_at` | `datetime` | 1 | Anchor computation timestamp. |
| `policy_version` | `str` | 1 | Policy file version used to derive this anchor. |

### Rules

- One anchor per meaningful natal focus. A chart with a Sun-Kassandra-MC configuration produces *one* anchor with three bodies, not three anchors.
- Anchors are additive to natal facts, not a replacement for aspect matrix, indexes, or configurations. Downstream consumers may still read those directly.
- Anchor IDs are stable across regenerations of the same natal snapshot. If a policy version changes and produces different anchors, the new anchors get new IDs — the old anchor IDs become historical and reappear only if the same chart is re-run against the old policy.

---

## 2. `ForecastEvent`

The shared evidence-grade object every predictive clock emits. Transit engine events (already produced), proprietary asteroid events (currently produced but unwired), return events (future), Solar Arc events (future), progression events (future), and profection year transitions (future) all normalize to this shape.

### Fields

| Field | Type | Cardinality | Semantics |
|---|---|---|---|
| `schema_version` | `str` | 1 | `phase0.1.0` |
| `event_id` | `str` | 1 | Globally unique within a report run. Format `fe_<method_family_code>_<8-hex>`. |
| `method_family` | `str` | 1 | One of: `TRANSIT`, `LUNATION`, `RETURN`, `PROGRESSION`, `SOLAR_ARC`, `PROFECTION`, `ZODIACAL_RELEASING`, `LOT`, `TIME_LORD`, `PROPRIETARY_TRANSIT`, `UNKNOWN`. Note: `PROPRIETARY_TRANSIT` is a distinct method family here for provenance, even though the predictive engine normalizes it under `TRANSIT` for anti-double-counting (see §5 anti-stacking policy). |
| `method_variant` | `str` | 1 | Sub-type inside the family. Examples: `transit_cycle`, `station`, `ingress`, `eclipse`, `plain_lunation`, `qualified_lunation`, `solar_return`, `lunar_return`, `jupiter_return`, `saturn_return`, `progression_body_aspect`, `progression_ingress`, `solar_arc_body_aspect`, `annual_profection`, `zr_l1_transition`, `zr_l2_transition`, `zr_lob`, `zr_peak`. |
| `clock_role` | `str` | 1 | One of: `chapter`, `modifier`, `trigger`, `return`, `time_lord`, `overlay`, `candidate_support`. Governs how the event is used downstream. See charter per clock (03) for defaults. |
| `source_body` | `str` | 1 | Name of the transiting / directed / progressed body driving the event. For a lot or ZR transition, this is the lot name or the incoming period lord. |
| `source_kind` | `str` | 1 | One of: `planet`, `luminary`, `angle`, `node`, `asteroid`, `lot`, `time_lord`. |
| `target_body` | `?str` | 0..1 | Natal target body if the event is a contact. Empty for standalone events (e.g. ZR transitions with no specific natal contact). |
| `target_kind` | `?str` | 0..1 | One of: `planet`, `luminary`, `angle`, `house`, `asteroid`, `lot`, `configuration`, `anchor`. |
| `natal_anchor_ids` | `[str]` | 0..n | Anchors this event activates. Populated by anchor-matcher after the event is emitted. |
| `topic_keys` | `[str]` | 0..n | Topic tags carried by the event. Inherited from `source_body`, `target_body`, and the method's topic policy. |
| `domain_keys` | `[str]` | 0..n | Domain tags: inherited from target house / relevant configuration. |
| `start_at` | `datetime` | 1 | Onset moment. For chapters, the period start. For triggers with orb-based windows, the entry moment. |
| `peak_at` | `datetime` | 1 | Peak or exact moment. |
| `end_at` | `datetime` | 1 | End moment. |
| `exact_at` | `[datetime]` | 0..n | Every exact contact inside the window (may be multiple for a retrograde-loop cycle). Empty for events without a well-defined exact instant. |
| `orb` | `?float` | 0..1 | Peak orb in degrees, if applicable. |
| `distance` | `?float` | 0..1 | For lot / ZR / profection events with no orb but a computed distance metric. |
| `phase` | `?str` | 0..1 | Retrograde phase or lunation phase, if applicable. Examples: `first_pass`, `retrograde_pass`, `third_pass`, `waxing_square`, `full`. |
| `event_strength` | `float` | 1 | Component-preserving strength in `[0.0, 1.0]`. Not opaque — see `strength_components`. |
| `strength_components` | `{str: float}` | 1 | Named contributors: `exactness`, `event_weight`, `target_relevance`, `structural_importance`, `theme_convergence`, `method_multiplier`, `asteroid_specificity`. |
| `temporal_precision` | `str` | 1 | One of: `instant` (sub-day, e.g. exact aspect moment), `day`, `week`, `month`, `season`, `year_or_longer`. |
| `independence_group` | `str` | 1 | Anti-double-counting key. See method charters and §5 policy. |
| `activation_route` | `str` | 1 | Route through the natal chart: `transit_to_body`, `transit_to_angle`, `transit_to_asteroid`, `return_moment`, `progression_to_body`, `progression_to_angle`, `progression_to_asteroid`, `solar_arc_to_body`, `solar_arc_to_angle`, `solar_arc_to_asteroid`, `profection_year_lord`, `zr_period_transition`, `lot_transit`. |
| `asteroid_participants` | `[str]` | 0..n | Every asteroid whose position, ruler-role, or aspect participates in this event. Never empty when either `source_body` or `target_body` is an asteroid. |
| `confidence` | `float` | 1 | Independent of `event_strength`. In `[0.0, 1.0]`. |
| `confidence_components` | `{str: float}` | 1 | `exactness_support`, `angle_support`, `calculation_integrity`, `target_uncertainty`, `birth_time_state`, `method_maturity`. |
| `calculation_trace` | `{str: any}` | 1 | Inputs sufficient for reproduction: JD, orb table row used, formula version, ephemeris file references, missing_fields list, notes. |
| `report_surface_visibility` | `[str]` | 0..n | Which report surfaces may see this event (subset of: `internal_rd`, `predictive_sandbox`, `soul_ecosystem`, `year_ahead_appendix`, `personal_forecast_context`, `discrete_candidate_surface`). Default derived from governance registry + method charter. |
| `provenance` | `{scanner: str, scanner_version: str, emitted_at: datetime}` | 1 | Which scanner produced this event. |

### Rules

- Every event carries **at least one** of `orb`, `distance`, or `phase`. An event with none of these is malformed and must be rejected by the sidecar writer.
- `event_id` is deterministic given `(source_body, target_body, aspect_or_variant, peak_at, method_family)` inside a report run. Regenerating the same report produces the same IDs.
- `activation_route = transit_to_asteroid` sets `report_surface_visibility` to a default of `[internal_rd, predictive_sandbox, soul_ecosystem]` — never `year_ahead` or `personal_forecast` unless a Phase 10 policy explicitly promotes it.
- The predictive engine must never *invent* fields beyond this schema. If an operation profile or semantic diagnostic is desired, it belongs on `PredictiveSignal` (§3), not on `ForecastEvent`.

---

## 3. `PredictiveSignal`

Normalized layer between raw `ForecastEvent` and downstream aggregation (daily series, chapters, candidates). Enriches events with operation semantics, epistemic confidence, and anchor linkage.

### Fields

| Field | Type | Cardinality | Semantics |
|---|---|---|---|
| `schema_version` | `str` | 1 | `phase0.1.0` |
| `signal_id` | `str` | 1 | `sig_<method_family_code>_<8-hex>`. Deterministic given source events. |
| `source_event_ids` | `[str]` | 1..n | `ForecastEvent.event_id`s this signal was normalized from. Length > 1 when multiple raw events (e.g. multi-pass contact) collapse into one signal. |
| `method_family` | `str` | 1 | Same domain as `ForecastEvent.method_family`. |
| `independence_group` | `str` | 1 | Copied from source. Used for method-family diversity counting. |
| `activation_route` | `str` | 1 | Copied from source. |
| `signal_role` | `str` | 1 | One of: `chapter_evidence`, `trigger_evidence`, `modifier_evidence`. Derived from `source_event.clock_role` and the signal's temporal precision. |
| `source_body` | `str` | 1 | |
| `target_body` | `?str` | 0..1 | |
| `aspect` | `?str` | 0..1 | |
| `natal_anchor_ids` | `[str]` | 0..n | Anchors this signal activates. |
| `topic_keys` | `[str]` | 0..n | |
| `domain_keys` | `[str]` | 0..n | |
| `asteroid_participants` | `[str]` | 0..n | Cumulative across source events. |
| `start_date` | `date` | 1 | Day-precision window start. |
| `peak_date` | `date` | 1 | Day-precision peak. |
| `end_date` | `date` | 1 | Day-precision window end. |
| `trigger_strength` | `float` | 1 | Base strength: `exactness × event_weight × target_relevance`. |
| `signal_strength` | `float` | 1 | Adjusted by structural / thematic modifiers. |
| `structural_importance` | `float` | 1 | |
| `theme_convergence` | `float` | 1 | |
| `operation_profile` | `{str: float}` | 1 | Six-axis: `stabilize`, `amplify`, `activate`, `disrupt`, `dissolve`, `reveal`. |
| `operation_basis` | `{source: {...}, substrate: {...}, aspect: {...}, method: {...}}` | 1 | Contribution breakdown of the operation profile. |
| `dominant_operation` | `str` | 1 | Argmax of `operation_profile`. |
| `epistemic_confidence` | `float` | 1 | In `[0.0, 1.0]`. |
| `confidence_components` | `{str: float}` | 1 | `exactness_support`, `angle_support`, `calculation_integrity`, `target_uncertainty`, `method_maturity`. |
| `confidence_state` | `str` | 1 | One of: `high`, `moderate`, `low`, `withheld`. `withheld` means angle-dependent + birth-time-unknown. |
| `angle_eligibility` | `bool` | 1 | Whether angle-dependent claims are permitted for this signal. |
| `routing_state` | `str` | 1 | Inherited from source event's activation pass state. |
| `pass_sequence` | `str` | 1 | For multi-pass contacts. |
| `cycle_id` | `str` | 1 | For contact cycles (retrograde loops). |
| `contact_count` | `int` | 1 | Number of exact contacts in the cycle. |
| `multiple_exact_passes` | `bool` | 1 | Convenience flag. |
| `formula_version` | `str` | 1 | `predictive_v?.?.?`. |
| `policy_version` | `str` | 1 | Aggregate policy version (asteroid registry + method charter versions). |

### Rules

- `PredictiveSignal` never loses `source_event_ids`. Post-hoc validation must be able to reach every raw event that produced this signal.
- `signal_role` is set by rule, not narrative preference: `chapter_evidence` for events with `temporal_precision ∈ {season, year_or_longer}` OR `clock_role = chapter`; `trigger_evidence` for `temporal_precision ∈ {instant, day, week}` AND `clock_role ∈ {trigger, return, overlay}`; `modifier_evidence` for `clock_role = modifier` OR `time_lord`; ties broken toward `trigger_evidence`.
- A signal's `natal_anchor_ids` is the union of anchor IDs matched by any source event, deduplicated.

---

## 4. `ChapterState`

A broad period generated from long clocks and sustained transit structures. Never counted as a discrete-event hit.

### Fields

| Field | Type | Cardinality | Semantics |
|---|---|---|---|
| `schema_version` | `str` | 1 | `phase0.1.0` |
| `chapter_id` | `str` | 1 | `chap_<8-hex>`. |
| `start_at` | `datetime` | 1 | |
| `peak_range` | `[datetime, datetime]` | 1 | Inclusive interval of peak dates within the chapter. May be a zero-width interval when peak is a single day. |
| `end_at` | `datetime` | 1 | |
| `chapter_kind` | `str` | 1 | One of: `zr_period`, `profection_year`, `return_year`, `progressed_lunation_phase`, `sustained_transit_chapter`, `solar_arc_chapter`, `long_transit_cycle`. |
| `active_long_clocks` | `[str]` | 0..n | Contributing method families. |
| `active_structural_transits` | `[str]` | 0..n | `signal_id`s of structural transits contributing baseline field. |
| `contributing_signal_ids` | `[str]` | 0..n | Every signal that participates in the chapter. |
| `contributing_event_ids` | `[str]` | 0..n | Every event that participates. |
| `natal_anchor_ids` | `[str]` | 0..n | Anchors under active weight during the chapter. |
| `topic_keys` | `[str]` | 0..n | Union across contributing signals. |
| `domain_keys` | `[str]` | 0..n | Union across contributing signals. |
| `asteroid_participants` | `[str]` | 0..n | |
| `coherence` | `float` | 1 | In `[0.0, 1.0]`. Higher = signal operations reinforce each other. |
| `counterforce` | `float` | 1 | In `[0.0, 1.0]`. Higher = active conflicting pressure inside the chapter. |
| `complexity` | `float` | 1 | In `[0.0, 1.0]`. Number and diversity of active operation axes. |
| `polarity` | `float` | 1 | In `[-1.0, 1.0]`. Constructive vs. dissolving tilt. |
| `confidence` | `float` | 1 | |
| `confidence_components` | `{str: float}` | 1 | |
| `birth_time_dependency` | `str` | 1 | `none` / `soft` / `hard`. |
| `chapter_summary_score` | `float` | 1 | Composite in `[0.0, 1.0]`. Non-opaque per component list above. |
| `report_surface_visibility` | `[str]` | 0..n | Default `[internal_rd, predictive_sandbox]`. Year Ahead promotion is Phase 10. |
| `provenance` | `{...}` | 1 | Chapter-builder version, emission timestamp. |

### Rules

- `ChapterState` cannot be re-labeled as a `MicroCandidate`. They are distinct types with distinct downstream policies.
- `active_long_clocks` must include at least one entry from `{RETURN, PROGRESSION, SOLAR_ARC, PROFECTION, ZODIACAL_RELEASING, TIME_LORD}` OR at least one sustained transit whose duration exceeds 90 days. A chapter derived from *only* short transits is not a valid chapter.

---

## 5. `MicroCandidate`

A narrow, prospectively generated candidate object for discrete-event research. **Window width is derived from the natural boundaries of its anchoring trigger evidence — there is no fixed universal maximum.** See [04_convergence_and_candidate_protocol.md](./04_convergence_and_candidate_protocol.md) §4.2 for the derivation rule. (`predictive_sandbox` separately enforces its own internal research cap, currently 6 calendar days, scoped to that surface only — not a general-system rule.) Never generated by shrinking a broader window after outcomes are known.

### Fields

| Field | Type | Cardinality | Semantics |
|---|---|---|---|
| `schema_version` | `str` | 1 | `phase0.1.0` |
| `candidate_id` | `str` | 1 | `cand_<8-hex>`. Deterministic within a report run. |
| `report_run_id` | `str` | 1 | The run that produced this candidate. |
| `start_at` | `datetime` | 1 | |
| `peak_at` | `datetime` | 1 | |
| `end_at` | `datetime` | 1 | |
| `window_days` | `float` | 1 | `(end_at - start_at).days`. Derived from the natural span of the qualifying trigger signal(s); not compared against a fixed ceiling. |
| `maximum_window_days` | `?float` | 0..1 | Only populated when a surface-specific research cap applies (e.g. `predictive_sandbox`'s internal stress-testing constant, currently `6.0`). Null for the general system, where the window is trigger-derived with no imposed ceiling. |
| `candidate_domain` | `[str]` | 1..n | Domain keys (`identity`, `partnership`, etc.) the candidate is *about*. |
| `candidate_topic_keys` | `[str]` | 1..n | Topic keys derived from anchor + signal topic coherence. |
| `natal_promise_links` | `[str]` | 1..n | `NatalPromiseAnchor.anchor_id` list. Length ≥ 1 is a hard requirement. |
| `chapter_support` | `[str]` | 1..n | `ChapterState.chapter_id` OR long-clock signal IDs. Length ≥ 1 is a hard requirement. |
| `trigger_support` | `[str]` | 1..n | Trigger `signal_id`s. Length ≥ 1 is a hard requirement. |
| `independent_method_families` | `[str]` | 2..n | Distinct method families contributing. Length ≥ 2 is a hard requirement. |
| `asteroid_participants` | `[str]` | 0..n | |
| `component_scores` | `{str: float}` | 1 | See §6. Non-opaque. |
| `convergence_score` | `float` | 1 | Composite in `[0.0, 1.0]`. Ranking only; not the primary evidence. |
| `counterforce` | `float` | 1 | |
| `counterforce_notes` | `[str]` | 0..n | Human-readable summary of conflicting evidence retained. |
| `complexity` | `float` | 1 | |
| `confidence` | `float` | 1 | |
| `confidence_components` | `{str: float}` | 1 | |
| `birth_time_dependency` | `str` | 1 | `none` / `soft` / `hard`. If `hard` and birth time is not exact, `candidate_status = withheld`. |
| `candidate_status` | `str` | 1 | One of: `pre_registered`, `active`, `expired`, `withheld`, `voided`. `pre_registered` is the state when the sidecar is first written. `voided` requires a documented reason (e.g. calculation error corrected). |
| `pre_registered_at` | `datetime` | 1 | Sidecar-write timestamp for this candidate. This is *the* clock for the "no post-hoc shrinking" rule: the outcome ledger may not accept an outcome dated before `pre_registered_at`. |
| `alternative_evidence` | `[str]` | 0..n | Signal or event IDs that were considered but did not enter the qualifying set. Retained for review. |
| `report_surface_visibility` | `[str]` | 0..n | Default `[internal_rd]`. Phase 10 gates any promotion beyond that. |
| `provenance` | `{...}` | 1 | Candidate-builder version, emission timestamp. |

### Rules (hard)

- `window_days` reflects the natural boundary of the qualifying trigger evidence at emission time (see [04_convergence_and_candidate_protocol.md](./04_convergence_and_candidate_protocol.md) §4.2). Where `maximum_window_days` is populated (surface-specific research cap), `window_days ≤ maximum_window_days` also holds. Cannot be relaxed after outcome either way.
- Minimum evidence: ≥1 anchor, ≥1 chapter support, ≥1 trigger, ≥2 independent method families (deduplicated by `independence_group`).
- `pre_registered_at` is set once and never overwritten. If the same candidate would be regenerated, it is either matched to the existing candidate by `candidate_id` or emitted as a new candidate with a new ID (with the old `voided` if superseded).
- `alternative_evidence` retention is mandatory. A candidate that discards its non-qualifying near-misses cannot be evaluated in the retrospective program.

---

## 6. `TimeLordPeriod`

Shared contract for profection years, zodiacal-releasing L1–L4 periods, and other time-lord family periods (Firdaria etc. under a later charter).

### Fields

| Field | Type | Cardinality | Semantics |
|---|---|---|---|
| `schema_version` | `str` | 1 | `phase0.1.0` |
| `period_id` | `str` | 1 | `tlp_<system_code>_<8-hex>`. |
| `system` | `str` | 1 | One of: `annual_profection`, `monthly_profection`, `zodiacal_releasing_fortune`, `zodiacal_releasing_spirit`, `firdaria`, `custom`. |
| `level` | `str` | 1 | For hierarchical systems: `L1`, `L2`, `L3`, `L4`, or `year`, `month`. |
| `parent_period_id` | `?str` | 0..1 | Reference to the containing period at the next level up. |
| `start_at` | `datetime` | 1 | |
| `end_at` | `datetime` | 1 | |
| `period_lord` | `?str` | 0..1 | Body / lot / sign name of the ruling lord. |
| `period_sign` | `?str` | 0..1 | If applicable. |
| `period_house` | `?int` | 0..1 | If applicable. |
| `lord_natal_state` | `{condition: str, house: int, aspects: [...]}` | 0..1 | Snapshot of lord's natal condition at generation time. |
| `is_peak` | `bool` | 1 | Peak period flag (ZR peaks in particular). |
| `is_loosing_of_the_bond` | `bool` | 1 | Loosing-of-the-bond marker (ZR). |
| `activated_house_topics` | `[str]` | 0..n | Domain / topic keys under emphasis. |
| `natal_anchor_ids` | `[str]` | 0..n | Anchors whose weight is modified by this period. |
| `weight_modifier` | `float` | 1 | Multiplier applied to signals whose anchors intersect `natal_anchor_ids`. Default `1.0`. |
| `confidence` | `float` | 1 | |
| `confidence_components` | `{str: float}` | 1 | |
| `birth_time_dependency` | `str` | 1 | `none` for whole-sign profection; `hard` for degree-precise; `soft` for lot-based ZR. |
| `formula_version` | `str` | 1 | |
| `policy_version` | `str` | 1 | |
| `provenance` | `{...}` | 1 | |

### Rules

- `TimeLordPeriod` records emit `weight_modifier` only. They do not emit standalone `ForecastEvent`s of variant `annual_profection` and simultaneously modify signal weight — a period contributes evidence *either* through emitted transitions (`method_variant = zr_l1_transition` etc., which are proper `ForecastEvent`s of `method_family = ZODIACAL_RELEASING` or `PROFECTION`) *or* through weight modification, but not both for the same activation. The charter for each system (03) specifies which mode.
- Nested periods must nest cleanly: `L2.start_at ≥ L1.start_at` and `L2.end_at ≤ L1.end_at`. The sidecar writer must validate this at emission.

---

## 7. Topic taxonomy (reserved key namespace)

Every schema above uses `topic_keys` and `domain_keys`. Phase 0 locks the following namespaces. New keys require an operator note in `agents/REVISIONS.md`.

### `domain_keys` (12 keys, one per whole-sign house)

`identity`, `resources`, `communication`, `home`, `creativity`, `work`, `partnership`, `transformation`, `meaning`, `vocation`, `community`, `spirit`.

### `topic_keys` (open enum with reserved base set)

Reserved base set — every asteroid registry, method charter, and natal promise anchor may only draw from this set in Phase 0. Additions are versioned.

Archetypal / functional:

- `voice`, `attraction`, `desire`, `harmony`, `clarity`, `oracle`, `radiance`, `prophecy`
- `truth_under_doubt`, `warning`, `insight_validation`, `disclosure`, `unconcealment`
- `karmic_thread`, `cause_effect`, `obligation`, `destined_encounter`, `catalyst`, `threshold_person`
- `memory`, `remembrance`, `ancestral_thread`, `submerged_knowledge`, `lost_pattern`, `hidden_lineage`
- `wisdom`, `gnosis`, `deep_knowing`
- `pattern_weaving`, `hubris`, `structural_construction`
- `rupture`, `generative_void`, `primal_reorganization`
- `message`, `translation`, `boundary_crossing`
- `natural_law`, `right_order`, `oath`
- `lyric`, `melody`, `delight`
- `celestial_mapping`, `cosmology`, `big_picture`
- `sacred_song`, `silent_prayer`
- `transformation`, `enchantment`, `potion`
- `restoration`, `magical_sovereignty`, `gathering`
- `practice`, `rehearsal`, `meditation`
- `intimate_lyric`, `eros`, `tender_expression`
- `dance`, `rhythm`, `movement`
- `strategy`, `craft`, `tactical_wisdom`
- `crossroads`, `threshold`, `keys`, `night_wisdom`
- `sacrifice`, `ruthless_devotion`, `cost_of_love`
- `labor`, `sustained_effort`, `industry`
- `soul`, `essence`, `animating_spark`
- `fate`, `thread`, `allotment`
- `refusal`, `exile_return`, `unbound_self`
- `psychopomp`, `weighing`, `transition`
- `fierce_protection`, `destruction_of_illusion`, `war_against_falsehood`
- `innocence`, `inner_child`, `becoming`
- `grace`, `luminous_aid`, `guardianship`
- `inheritance`, `essential_code`, `lineage`

Timing / structural (method-side):

- `chapter_opening`, `chapter_climax`, `chapter_close`, `chapter_reversal`
- `trigger_exactness`, `trigger_station`, `trigger_ingress`, `trigger_lunation`, `trigger_eclipse`, `trigger_return_moment`
- `long_clock_activation`, `long_clock_transition`, `time_lord_handoff`
- `pressure_system`, `reorganization`, `revelation`, `disruption`, `collision`, `opportunity`, `aftermath`, `background_field`, `timing_shift`, `threshold_event`

Mode (expression-side):

- `situational`, `interpersonal`, `practical`, `environmental`, `institutional`, `material`, `atmospheric`

---

## 8. Object relationships

```
NatalPromiseAnchor  ←── referenced by ──  ForecastEvent
                                              │
                                              ▼
                                       PredictiveSignal
                                              │
                     ┌────────────────────────┼───────────────┐
                     ▼                        ▼               ▼
                ChapterState             MicroCandidate    (daily series
                                                            aggregation)

TimeLordPeriod ──── weight_modifier or ForecastEvent emission ──▶ PredictiveSignal / ChapterState
```

Rules:

- Every `ForecastEvent` may reference 0..n anchors.
- Every `PredictiveSignal` inherits the union of its source events' anchors.
- `ChapterState` and `MicroCandidate` reference signals (not raw events directly) except for `contributing_event_ids` on `ChapterState`, which is a convenience field.
- `TimeLordPeriod` never directly appears in a `MicroCandidate.chapter_support` — a chapter-level object is required as intermediary.

---

## 9. Anti-double-counting policy (schema layer)

Independence groups are the primary anti-stacking mechanism at the schema layer. The following are the reserved `independence_group` values:

- `transit_family` — every transit, ingress, station, eclipse, plain lunation, qualified lunation, retrograde-cycle-phase from the same underlying transit contact.
- `proprietary_transit_family` — asteroid-aware proprietary transits. **Belongs to the same anti-stacking bucket as `transit_family` when the same natal target and same transit source are involved** (e.g. Uranus square Sun via `scan_transit_windows` and Uranus square Sun via `scan_proprietary_forecast_windows` cannot both count as independent votes).
- `lunation_family` — new/full moons and eclipses. Eclipse suppression of same-date plain lunation is enforced upstream (already implemented). At schema level, treated as one family.
- `return_family_solar`, `return_family_lunar`, `return_family_jupiter`, `return_family_saturn`, `return_family_generic` — each return type is its own family.
- `progression_family` — all secondary progressions.
- `solar_arc_family` — all Solar Arc directed contacts.
- `profection_family` — annual + monthly profections.
- `zr_family_fortune`, `zr_family_spirit` — each ZR lot has its own family.
- `time_lord_family_generic` — reserved for later time-lord systems.

Rules:

- A `MicroCandidate`'s `independent_method_families` must contain ≥2 *distinct* values from the above list.
- `transit_family` and `proprietary_transit_family` count as one family when they share both `source_body` and `target_body` — the schema stores the raw `independence_group` on each signal, but the candidate builder deduplicates on the composite key `(independence_group, source_body, target_body)` before counting.

---

## 10. Fields the engine already produces that map to these schemas

For Phase 3's implementation planning:

- `ForecastEvent.event_id` — new. Generate from existing event tuple + peak_at hash.
- `ForecastEvent.method_family` — already normalized by `engine/predictive_engine._normalize_method_family()`. Extend to include `PROFECTION`, `ZODIACAL_RELEASING`, `LOT`, `TIME_LORD` when those clocks land.
- `ForecastEvent.method_variant` — new. Derive from `event_type` string.
- `ForecastEvent.clock_role` — new. Assigned by charter per method.
- `ForecastEvent.source_body`, `target_body`, `aspect`, `orb` — already present.
- `ForecastEvent.start_at / peak_at / end_at` — currently `entry_datetime / peak_datetime / leave_datetime`. Rename at the adapter layer.
- `ForecastEvent.exact_at` — currently `contacts` (list of exact moments in a cycle).
- `ForecastEvent.independence_group` — already computed (`engine/predictive_engine._independence_group_for_family`). Extend per new method families.
- `ForecastEvent.activation_route` — already computed (`_activation_route_for_signal`). Extend for asteroid, lot, time-lord routes.
- `ForecastEvent.asteroid_participants` — new. Populate from source/target body kind + any ruler-chain traversal.
- `ForecastEvent.confidence` and components — already present at the signal layer as `epistemic_confidence`; needs to be lifted to the event layer for consistency.
- `ForecastEvent.calculation_trace` — new. Populate at scanner time.
- `PredictiveSignal` fields already in `engine/predictive_engine._event_to_signal()` and `_compute_signal_operation_profile()` / `_compute_signal_epistemic_confidence()`.

The adapter recommended in the Phase 0 → Phase 1 handoff is `formulas/report_surface.py`-style but targeting event normalization: `_to_forecast_event(raw_event) → ForecastEvent`. This is the point of Phase 3.
