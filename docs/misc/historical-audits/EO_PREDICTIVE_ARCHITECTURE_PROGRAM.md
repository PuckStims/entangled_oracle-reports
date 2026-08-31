# Entangled Oracle Predictive Architecture Program

Source-of-truth program document. Locked design rules and workstream contracts belong here; per-session notes belong in `agents/REVISIONS.md` and open work belongs in `agents/PLANNED_UPDATES.md`.

## Purpose

Build Entangled Oracle into an asteroid-rich, multi-clock forecasting and discrete-event research system without flattening its existing complexity or forcing every method into the same role.

This program does not replace EO's current natal, transit, Year Ahead, or Personal Forecast engines. It extends them into a layered predictive architecture:

```text
Immutable Natal Snapshot
    ↓
Natal Promise + Topic Graph
    ↓
Long-Clock Chapters
    ↓
Transit / Short-Clock Triggers
    ↓
Cross-Method Convergence
    ↓
Narrow Candidate Windows
    ↓
Versioned Evidence Sidecar
    ↓
Retrospective Validation + Controlled Report Surfaces
```

The desired end state is not "an astrology app that predicts everything." It is a system that can distinguish:

- enduring natal relevance;
- broad background weather;
- long developmental chapters;
- exact or near-exact triggers;
- independent method convergence;
- and narrow, falsifiable candidate periods.

## Locked Design Rules

1. EO keeps its existing transit-weather products. Year Ahead and Personal Forecast remain valid chapter/timing products while the advanced stack is built.
2. All 34 asteroids become explicitly governed predictive participants. "First-class" means every asteroid receives a declared predictive profile. No asteroid may disappear merely because a scanner, serializer, target list, or template forgot that `custom_asteroids` exists.
3. First-class does not mean identical. Each asteroid may have its own declared roles, aspect policy, clock eligibility, source/target behavior, relevance weighting, and topic relationships. The important rule is that differences are explicit policy, never accidental exclusion.
4. Every clock emits the same evidence-grade event contract. A return, Solar Arc contact, progression, profection year, zodiacal-releasing transition, transit, or asteroid trigger must be comparable without being falsely treated as equivalent.
5. A method family gets one independent vote. A transit, station, ingress, and retrograde pass describing the same underlying transit cycle cannot become four independent confirmations.
6. Broad weather and narrow candidates remain separate output types. A chapter window may be long. A discrete-event candidate must be generated prospectively under a fixed narrow-window rule and never created by shrinking a broad window after an event is known.
7. No new clock enters report prose before it enters the evidence sidecar and validation harness.
8. No simplification-by-deletion. Complexity is retained when it is traceable, mechanically active, inspectable, and capable of being tested.

## Target Architecture

### 1. Canonical predictive objects

EO should standardize these objects before adding more scanners.

#### A. `NatalPromiseAnchor`

A durable record of why a topic, domain, body, asteroid, angle, house, ruler, aspect pattern, or proprietary index is significant in a particular natal chart.

Required fields:

```text
anchor_id
topic_keys
domain_keys
natal_bodies
natal_asteroids
houses
rulers / dispositors
aspects / configurations
proprietary_index_links
strength
confidence
birth_time_dependency
evidence_trace
```

This becomes the bridge between "a transit is happening" and "this transit activates something specifically meaningful in this chart."

#### B. `ForecastEvent`

Every predictive clock emits this shared event object.

```text
event_id
method_family
method_variant
clock_role
source_body
target_body
target_kind
natal_anchor_ids
topic_keys
start_at
peak_at
end_at
exact_at
orb / distance / phase
event_strength
temporal_precision
independence_group
activation_route
asteroid_participants
confidence
calculation_trace
```

`clock_role` must be one of: `chapter`, `modifier`, `trigger`, `return`, `time_lord`, `overlay`, `candidate_support`.

#### C. `PredictiveSignal`

The existing signal model remains the normalized layer, but it must preserve:

- source `ForecastEvent` IDs;
- natal-anchor links;
- all asteroid participants;
- method-family diversity;
- topic/domain keys;
- confidence components;
- and whether the signal is chapter, trigger, or modifier evidence.

#### D. `ChapterState`

A broad period generated from long clocks and sustained transit structures.

```text
chapter_id
start_at
peak_range
end_at
active_long_clocks
active_structural_transits
natal_anchor_ids
topic_keys
asteroid_participants
coherence
counterforce
confidence
```

A `ChapterState` is never counted as a discrete-event hit.

#### E. `MicroCandidate`

A separate, narrow object for empirical prediction research.

```text
candidate_id
start_at
peak_at
end_at
maximum_window_days
candidate_domain
natal_promise_links
chapter_support
trigger_support
independent_method_families
asteroid_participants
convergence_score
counterforce
confidence
candidate_status
pre_registered_at
```

A `MicroCandidate`'s window is not an arbitrary fixed cap. Its start/end derive from the natural window of the trigger event(s) that anchor it — a station's own date, an eclipse's or lunation's own orb window, an exact transit contact's own entry/exit, a return moment's own buffer. Each method charter (Workstream C) already defines this per clock; no universal ceiling is imposed on top of it. `predictive_sandbox` may additionally enforce its own tighter research-protocol cap (currently six calendar days) as an internal stress-testing constraint, but that cap is scoped to the sandbox and is never treated as the general system's candidate-width rule.

## Workstream A — Predictive Evidence and Reproducibility Foundation

This is not optional plumbing. It is the recordkeeping layer that prevents every later method from becoming untraceable complexity.

### Deliverables

**1. Versioned predictive sidecar.** Create a separate internal artifact `<report_id>.eo_predictive.json`. Do not overload the current manifest. The manifest can remain operational and delivery-oriented; the predictive sidecar is an internal R&D evidence record.

It must preserve:

- immutable natal snapshot;
- birth data and birth-time state;
- resolved location and timezone;
- Swiss Ephemeris version and calculation settings;
- asteroid registry version;
- method-policy version;
- formula/index version hashes;
- every raw `ForecastEvent`;
- every normalized `PredictiveSignal`;
- daily series;
- contributor IDs and contribution strengths for each day;
- chapter windows;
- accepted micro-candidates;
- rejected candidate peaks;
- rejection reason;
- detector thresholds;
- convergence composition;
- report-generation timestamp;
- engine version and Git commit, where available.

**2. Daily provenance.** Extend daily series rows so they retain:

```text
contributing_signal_ids
contributing_event_ids
structural_contributors
trigger_contributors
per_contributor_strength
```

**3. Rejected-candidate registry.** Every peak or prospective micro-candidate that is filtered, merged, or suppressed must be recorded.

```text
candidate_date
residual
prominence
candidate_width
filter_reason
merged_into
suppressed_by
signal_ids
method_families
```

**4. Baseline freeze suite.** Freeze representative charts and report dates as regression fixtures:

- exact birth time;
- uncertain birth time;
- asteroid-heavy chart;
- quiet transit year;
- dense transit year;
- known retrograde loop;
- eclipse-heavy period;
- multiple simultaneous long-clock period.

Every new clock must be tested against this fixed suite.

**Exit condition:** EO can recreate a predictive run later and show exactly what it calculated, what it rejected, and why.

## Workstream B — Full 34-Asteroid Predictive Policy

EO currently has 34 natal asteroids, but only eight have latent predictive hooks. The goal is not merely to activate the existing eight. The goal is to give all 34 explicit forecast behavior.

### Deliverable: `asteroid_predictive_registry`

Create one policy record per asteroid.

```text
asteroid_name
ephemeris_id
natal_roles
topic_keys
proprietary_index_links
target_eligibility
source_eligibility
clock_eligibility
allowed_aspects_by_clock
orb_policy_by_clock
weight_policy
house_relevance_policy
angle_relevance_policy
rulership / dispositor policy, if applicable
transit_speed / source constraints
confidence modifiers
report-surface permissions
validation category
```

### Required asteroid rules

Every asteroid must be explicitly classified for:

- natal-target eligibility;
- transit-source eligibility;
- progression eligibility;
- Solar Arc eligibility;
- return compatibility, if applicable;
- profection / topic relevance;
- time-lord or ZR relevance;
- aspect behavior;
- allowable orbs;
- source / target weighting;
- forecast-domain tags;
- and provenance display.

No asteroid may silently default to "not included."

### Implementation sequence

**B1. Preserve and wire the existing proprietary scanner.** `scan_proprietary_forecast_windows()` is a valid vertical slice, not the complete asteroid program. Wire it into the internal predictive stream first, behind an R&D feature flag. It should contribute to raw events, normalized signals, daily provenance, signal semantics, chapter and trigger analysis, sidecar export, and validation output. It should not automatically enter consumer-facing Year Ahead or Personal Forecast prose.

**B2. Replace hard-coded asteroid groups with registry-driven policy.** Migrate the existing eight-body configuration into the new registry. Preserve current behavior exactly during migration, then expand from a traceable policy file rather than scattered source-code exceptions.

**B3. Expand all 34 asteroid targets.** All 34 become eligible natal targets under declared policies. A body may have different source policy than target policy, but every asteroid must be able to appear in a forecast trace when a qualifying predictive method activates it.

**B4. Add asteroid-aware lunation and eclipse policy.** The current lunation / eclipses target lists exclude asteroids. Add registry-based target eligibility so a lunation or eclipse can activate a natal asteroid when that asteroid's profile permits it.

**Exit condition:** every asteroid can be audited from natal position → forecast policy → produced or deliberately excluded event → normalized signal → sidecar provenance.

## Workstream C — Multi-Clock Method Suite

Every method needs a written method charter before code implementation.

Each charter must declare:

- astronomical calculation convention;
- house system and zodiac assumptions;
- sect or birth-time dependency;
- allowed bodies, angles, and asteroids;
- exactness and orb policy;
- output event types;
- chapter versus trigger role;
- anti-double-counting behavior;
- topic / natal-anchor linkage;
- confidence limits;
- report-surface policy;
- and validation rule.

### C1. Returns

Implement in two layers.

Layer 1: **exact return moments** — event-level returns: Solar return, lunar return, Jupiter return, Saturn return, optionally other planetary returns through declared policy. These produce dated `ForecastEvent` records. They do not require full return-chart interpretation at first.

Layer 2: **return-chart structures** — once event-level returns are stable, add return-chart interpretation as a separate analytical layer rather than conflating it with the return moment itself.

Role: chapter / annual or monthly contextual activation.

### C2. Solar Arc directions

Implement a declared Solar Arc convention and store it in method metadata.

Minimum scope: directed natal planets; directed angles; directed asteroid positions; Solar Arc contacts to natal planets, angles, and asteroid targets; entry, exact, and exit periods; explicit angle-confidence gating.

Role: long-clock chapter activation with potentially strong topic specificity.

### C3. Secondary progressions

Implement a progressed-chart constructor with: one day of ephemeris motion per year of life; progressed planets and selected progressed asteroids; progressed angles only where birth-time confidence permits; progressed-to-natal contacts; progressed ingresses; progressed lunation phase; explicit date mapping and precision metadata.

Role: developmental chapter plus candidate-topic activation.

### C4. Annual profections

Implement annual profections as a relevance and topic-weighting layer, not as an event scanner.

Required outputs:

```text
profected_house
profected_sign
time_lord
time_lord_condition
time_lord_natal_links
activated_house_topics
annual_start / end
```

Use this to elevate or suppress natal-topic anchors and related transits, returns, Solar Arcs, progressions, and asteroid activity.

Role: annual topic prior and relevance modifier.

### C5. Lots and Zodiacal Releasing

Build Lots before Zodiacal Releasing.

**Lots layer.** At minimum: Lot of Fortune; Lot of Spirit; Lot of Necessity; documented sect-dependent formulas; explicit day/night logic; versioned calculation convention.

**Zodiacal Releasing layer.** Then implement L1 through L4 periods; peak and transition states; loosing-of-the-bond markers; period rulers; domain assignment; Fortune versus Spirit mode; date-bounded period records.

Role: nested chapter hierarchy and long-period context.

### C6. Additional time-lord systems

After the above are stable, add time-lord systems through a common `TimeLordPeriod` contract. Do not build unrelated one-off implementations. Possible later modules: Firdaria; primary directions; additional lots; harmonics; asteroid seasons; electional timing; synastry prediction.

**Exit condition:** every active clock emits a valid `ForecastEvent` or `TimeLordPeriod`, carries method metadata, accepts asteroid policy where appropriate, and appears in the evidence sidecar.

## Workstream D — Natal Promise and Topic Graph

A predictive system cannot responsibly say "this is a relationship candidate" because a transit has a Venus word attached to it. EO needs an explicit graph tying forecast evidence back to natal relevance.

### Build `NatalPromiseGraph`

For each chart, construct topic anchors from houses; house rulers; dispositorship; natal planets; angles; nodes; asteroids; natal aspect configurations; proprietary indexes; named configurations; natal convergence; standard chart-structure findings.

Each anchor should contain:

```text
topic_keys
domain_keys
bodies
asteroids
houses
rulers
aspects
index_links
strength
birth_time_dependency
confidence
```

### Topic coherence rules

A future candidate is coherent when evidence converges on the same natal target; a connected natal configuration; the same house / ruler network; the same proprietary index family; or a defined domain graph. It is not coherent merely because several things happen in the same week.

**Exit condition:** every predictive candidate can explain why this topic belongs to this chart before it claims a period of activation.

## Workstream E — Cross-Clock Convergence and Candidate Assembly

The existing convergence detector is a transit-family overlay. Replace or extend it with a proper evidence-composition layer.

### Candidate classes

1. **Weather.** Broad structural activity. May use sustained transits; retrograde cycles; ZR periods; progressions; Solar Arc; long returns; profection-year emphasis. Not countable as a discrete-event prediction.
2. **Chapter.** A bounded but potentially long arc with strong natal / topic relevance. Requires at least one long-clock source; natal-promise linkage; topic coherence; retained start / end basis.
3. **Trigger.** An exact or short-lived event such as transit exactness; station; lunation; eclipse; return moment; direct asteroid contact; exact daily timeline contact. A trigger alone is not a discrete-event candidate.
4. **Discrete Candidate.** A prospectively generated narrow interval whose width is derived from the natural boundaries of its own anchoring trigger evidence — no fixed universal maximum. (`predictive_sandbox` separately enforces its own internal research cap of six calendar days as a stress-testing constraint; that cap is scoped to the sandbox, not a general rule.) Minimum requirements:
   1. at least one natal-promise anchor;
   2. at least one chapter-level or long-clock support;
   3. at least one short trigger;
   4. at least two independent method families;
   5. topic coherence across the evidence;
   6. no unresolved anti-double-counting conflict;
   7. documented confidence and birth-time eligibility;
   8. retained alternative / conflicting evidence;
   9. predeclared candidate width;
   10. full evidence sidecar written before outcomes are reviewed.

### Anti-stacking rules

- Transit, ingress, station, and retrograde phase from one underlying cycle belong to one transit family.
- A return does not automatically count independently if it is only restating the same transit condition without a distinct calculated relation.
- Multiple asteroid contacts can increase topic specificity or internal coherence, but cannot inflate method-family count by themselves.
- A progression and Solar Arc may both contribute independently only when their calculations and contacts are genuinely distinct.
- Profections and ZR function primarily as contextual / chapter evidence unless a predeclared rule gives them a narrower timing role.

### Candidate score dimensions

Do not reduce everything to a single opaque number. Preserve component scores:

```text
natal_promise_strength
long_clock_support
trigger_precision
method_family_diversity
topic_coherence
temporal_convergence
asteroid_specificity
confidence
counterforce
complexity
window_width
```

A summary score may rank candidates, but the components must remain visible.

**Exit condition:** EO can create a narrow, trigger-derived candidate without retrospective date shrinking and show exactly which independent sources justified it and why its window has the width it has.

## Workstream F — Validation Laboratory

Validation is built alongside method development, not after the system becomes too complicated to inspect.

### Validation artifacts

**1. Immutable run package.** For every R&D run: natal snapshot; asteroid registry version; method-policy versions; all raw events; all signals; chapters; candidates; rejected peaks / candidates; timing thresholds; engine version; outcome status initially blank.

**2. Separate outcome ledger.** Outcomes must live outside the generation artifact.

```text
candidate_id
research_subject
candidate_window
candidate_domain
pre_registered_evidence
chronology_source
outcome_category
event_date
match_precision
research_completeness
non_hit / unresolved rationale
reviewer_notes
```

**3. Distinct evaluation metrics.** Track separately: candidate precision; event coverage; rank sensitivity; topic-domain accuracy; window-width calibration; method-family contribution; asteroid contribution; false-positive rate; quiet-period behavior; and matched-random baseline performance.

**4. Matched baseline.** For every historical test: preserve report year; preserve candidate count; preserve window width; preserve chart / event density conditions; shift or randomize candidates within the same period; compare observed alignment against matched random candidates.

**5. Research status categories.** Use only: `supported_hit`, `supported_non_hit`, `unresolved`, `research_incomplete`, `excluded_by_protocol`. Do not count unresolved as either success or failure.

**Exit condition:** EO can test discrete candidates without HTML scraping, memory-based reconstruction, or a post-hoc definition of success.

## Workstream G — Controlled Product Surfaces

The advanced system does not automatically belong in every report.

- **Internal R&D** receives full sidecar; signals; chapters; candidates; rejected peaks; asteroid provenance; diagnostics; validation ledger links.
- **Soul Ecosystem** remains the principal natal-asteroid narrative surface. It may expose natal promise anchors; asteroid domain structures; configurations; topic networks. It should not claim future event prediction merely because it supplies predictive context.
- **Year Ahead** eventually may receive chapter summaries; advanced timing overlays; notable convergence periods; optional practitioner-facing technical appendix. It should not receive raw diagnostic density by default.
- **Personal Forecast** eventually may receive active chapter context; near-term triggers; reflective timing guidance; clearly labeled "heightened convergence period" language.
- **Discrete candidate surface** — do not add to general client products until candidate generation is stable; validation sidecars are active; a retrospective protocol exists; and claim language is predeclared. A future advanced practitioner or research edition may expose candidates first.

**Exit condition:** internal complexity is available where needed without overwhelming current reports or overstating what has been validated.

## Full Program Sequence

**Phase 0 — Charter and Freeze.** Create and lock method charters; predictive object schemas; asteroid predictive registry specification; convergence rules; candidate protocol; validation protocol; versioning strategy; regression fixtures. Do not code new methods before these are approved.

**Phase 1 — Evidence Infrastructure.** Build `.eo_predictive.json`; daily contributor provenance; rejected-candidate registry; immutable natal snapshot; configuration / version capture; outcome-ledger schema. This phase makes later complexity inspectable.

**Phase 2 — Asteroid Forecast Activation.** Build all-34 asteroid predictive registry; registry-driven target / source policy; existing proprietary scanner integration under R&D governance; asteroid-aware event normalization; asteroid-aware provenance; asteroid regression suite. This phase makes asteroids predictively real rather than natal-only.

**Phase 3 — Shared Clock Framework.** Build common `ForecastEvent` contract; `TimeLordPeriod` contract; method-family taxonomy; anti-double-counting policy; cross-clock confidence policy; topic-anchor linkage API. This ensures every later clock enters the same architecture.

**Phase 4 — Returns and Annual Profections.** Implement exact return moments; annual profections; time-lord relevance modifiers; return / profection evidence traces; validation fixtures. Returns add a clean dated event source. Profections establish annual topical focus.

**Phase 5 — Solar Arc and Secondary Progressions.** Implement Solar Arc convention and directed contacts; secondary progressed-chart construction; progressed natal contacts; progressed angles with birth-time gating; asteroid-compatible policy; long-clock chapter output. This phase creates the first meaningful non-transit chapter layer.

**Phase 6 — Lots, Zodiacal Releasing, and Time-Lord Infrastructure.** Implement Lots of Fortune, Spirit, and Necessity; sect-aware formulas; Zodiacal Releasing period stack; L1–L4 transitions; loosing-of-the-bond markers; `TimeLordPeriod` integration; topic-domain linkage. This phase makes EO capable of nested chapter timing rather than only transit and progression weather.

**Phase 7 — Cross-Clock Convergence.** Build natal-promise graph; method-family diversity logic; topic coherence logic; conflict / counterforce handling; asteroid-specific contribution logic; chapter / trigger / candidate classification; transparent component scoring.

**Phase 8 — Discrete Candidate Engine.** Build micro-candidate object; exact-contact aggregation; trigger-derived window construction (no fixed universal maximum; sandbox retains its own separate research cap); candidate calendar; candidate suppression / rejection log; no-post-hoc-shrinking enforcement; candidate-specific validation exports.

**Phase 9 — Retrospective Validation Program.** Run transit-only baseline; asteroid-enabled transit comparison; returns / profections comparison; Solar Arc / progression comparison; full convergence comparison; matched-random baseline; per-method ablation tests; per-asteroid contribution analysis; quiet-period and non-hit review.

**Phase 10 — Controlled Surface Expansion.** Only after the prior phases are operational: practitioner technical appendix; advanced Year Ahead overlays; Personal Forecast convergence language; optional research-grade output; eventual discrete-candidate surface under strict claim controls.

## Definition of "Comprehensively Upgraded"

EO reaches the intended architecture only when all of the following are true:

- all 34 asteroids have explicit predictive profiles;
- asteroid participation is traceable in every relevant forecast artifact;
- transits, returns, Solar Arc, progressions, profections, Lots, and Zodiacal Releasing are active clock families rather than vocabulary hooks;
- every clock emits shared evidence-grade objects;
- natal promise is mechanically linked to predictive claims;
- chapter, trigger, and discrete candidate outputs are separate;
- discrete candidates are generated at a trigger-derived narrow width without retrospective shrinking;
- independent method families are counted without evidence stacking;
- every candidate and rejection is preserved;
- outcomes can be coded separately from the engine run;
- matched-random baselines can be calculated;
- current EO reports remain coherent throughout;
- and no client-facing language outruns the currently validated layer.

## Immediate First Build Package

The first comprehensive package is not "add one feature." It is:

1. predictive object schemas;
2. asteroid predictive registry for all 34 bodies;
3. sidecar / export contract;
4. daily contributor and rejected-peak provenance;
5. existing proprietary asteroid scanner wired into R&D;
6. method-charter set for returns, Solar Arc, progressions, profections, Lots, and Zodiacal Releasing;
7. regression fixtures and validation ledger schema.

Once that package exists, every new clock can be added into a system that already knows how to retain, compare, explain, and test it.
