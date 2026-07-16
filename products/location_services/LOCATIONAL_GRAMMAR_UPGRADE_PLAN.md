# Locational Grammar Upgrade Plan

**Status date:** 2026-07-16  
**Status:** Full-suite architecture plan. Do not treat this as a prose task.  
**Scope:** How Location Services evolves from a direct `LocationEvidenceRecord`
pipeline into a modular locational evidence grammar that can support Place
Profile, Place Resonance Search, Between Places, World Lines Companion, Local
Compass, and Living Map without flattening the product suite.

**Build outline companion:** When a phase below references a resolver, theme
clusterer, goal compatibility profile, report planner, provider catalog,
comparison layer, line engine, direction engine, timing overlay, or prose
expansion, use `products/location_services/BUILD_OUTLINE_DRIFT_GUARD.md` as the
implementation outline. Do not replace those referenced areas with one-file
stubs or prose labels.

## Core Mandate

This upgrade is not complete when a small adapter produces a few nicer labels.
It is complete only when Location Services has a real middle layer between
calculation and prose:

```text
Calculation -> Evidence -> Interpretation -> Synthesis -> Advice -> Presentation
```

Every module should emit structured evidence, not finished report prose. Prose
upgrades should wait until the evidence planner can explain why a location
matters for this chart, this place, this goal, and this time horizon.

## Anti-Downscope Rules

- Do not shrink this plan into "add one normalized evidence item object" and
  call the grammar implemented.
- Do not hide missing modules behind polished prose.
- Do not make Search scores smarter while leaving Place Profile, Between
  Places, and future products unable to inspect the same evidence grammar.
- Do not collapse `strong`, `supportive`, `comfortable`, and `worthwhile` into
  one score.
- Do not treat same-root confirmation as independent repetition.
- Do not wire future-method evidence before the computation exists.
- Do not let user goals change technical evidence; goals change relevance and
  advice.
- Do not let temporary timing rewrite permanent place baseline.

## Expanded Locational Grammar

The target grammar is:

```text
Location Interpretation =
    Geographic Context
  + Angularity
  + Angular Contact Geometry
  + Relocated House Expression
  + Natal Planet Condition
  + Natal Aspect Network
  + Chart-Ruler and Luminary Relevance
  + Local Horizon/Meridian Structure
  + Repetition and Convergence
  + Contradiction and Tradeoff
  + User Goal Compatibility
  + Temporal Activation
  + Confidence and Sensitivity
```

The first implementation should not attempt every line above. It should create
the normalized grammar seam and implement the modules already supported by
today's data.

## Evidence Object Contract

Every evidence module should move toward a normalized object shape:

```json
{
  "evidence_id": "location_body_interface_01",
  "family": "angularity",
  "subject": "venus",
  "interface": "mc",
  "strength": 0.86,
  "confidence": 0.94,
  "themes": ["public reception", "aesthetic visibility"],
  "supports": ["visibility", "creative_expression"],
  "costs": ["approval sensitivity", "public exposure"],
  "source_factors": {
    "distance_miles": 42,
    "distance_band": "close"
  },
  "calculation_status": "computed",
  "claim_boundary": "bounded_interpretation"
}
```

Required schema principles:

- `family` names the evidence family, not the prose section.
- `subject` names the body, point, house transition, direction, timing trigger,
  or geographic feature being interpreted.
- `interface` names the contact surface: `asc`, `dc`, `mc`, `ic`, house,
  line type, direction, timing target, or goal category.
- `strength` ranks technical prominence.
- `confidence` ranks calculation and sensitivity stability.
- `themes`, `supports`, and `costs` are structured interpretation inputs, not
  final prose.
- `source_factors` preserves the audit trail.
- Unsupported future methods must emit no computed evidence; they may appear
  only as explicit unavailable-method notes.

## Relationship Types

The resolver must distinguish:

### Independent Repetition

Different evidence families point to the same theme. This increases thematic
breadth and report priority.

### Same-Root Confirmation

Two observations describe the same underlying geometry, such as an
astrocartography line and the corresponding relocated angle conjunction. This
increases confidence and precision, not breadth.

### Contradictory Axis

Evidence points in different directions and should remain visible as a tradeoff
instead of being averaged into neutrality.

### Compensatory Structure

One factor helps contain, organize, or stabilize another factor's demand.

## Build Phases

### Phase 0: Preserve Current Working Surface

Goal: Make room for the grammar without breaking existing outputs.

Required work:

- Keep current `LocationEvidenceRecord` generation intact.
- Keep Place Profile and Place Resonance Search tests green.
- Keep provider-backed candidate catalog work separate from interpretation
  grammar.
- Document this plan from the active build plan, content handoff, and product
  stack.

Exit criteria:

- Existing Location Services suite remains green.
- Future agents can find this plan before starting prose expansion.

### Phase 1 Initial Implementation Note

The initial Phase 1 foundation lives in:

```text
products/location_services/evidence_grammar/
```

The current adapter consumes a `LocationEvidenceRecord` and emits normalized
evidence items for:

- relocated angle contacts
- relocated house expression
- natal condition inheritance
- birth-time confidence notes
- warning summary notes
- unsupported-method unavailable notes

This is a real grammar seam, but it is not the completed upgrade. The adapter
does not yet include a resolver, theme clusterer, goal compatibility profile,
or report planner. Do not mark the broader locational grammar upgrade complete
until those later phases exist and are tested.

### Phase 1: Normalized Evidence Grammar Foundation

Goal: Build the adapter layer that consumes today's `LocationEvidenceRecord`
and emits normalized evidence items.

Implement now from existing data:

- Relocated angle-contact evidence from `relocated_angle_contacts`.
- Relocated house expression evidence from `planet_house_changes`.
- Natal condition inheritance from `natal_modifiers`.
- Technical warning/confidence notes from `warning_summary`,
  `birth_context.birth_time_confidence`, and `appendix_trace`.
- Source trace metadata for every emitted item.

Do not implement yet:

- Astrocartography line proximity.
- Local Space directions.
- Parans.
- Dynamic timing.
- Multi-house-system sensitivity.

Exit criteria:

- A tested `evidence_grammar` package can consume a real
  `LocationEvidenceRecord` without mutating it.
- Every evidence item has stable IDs, family, subject, strength, confidence,
  themes/supports/costs, and source factors.
- Existing report paths remain unchanged unless explicitly opted in.

### Phase 2: House Transition and Relocated Structure Module

Goal: Replace thin house-change wording with reusable transition grammar.

Required work:

- Define house domain groups as content-approved taxonomy.
- Classify transitions such as:
  - `private_to_public`
  - `public_to_private`
  - `personal_to_relational`
  - `relational_to_personal`
  - `hidden_to_visible`
  - `cadent_to_angular`
  - `angular_to_cadent`
  - `restorative_to_productive`
  - `productive_to_restorative`
- Preserve current `movement_type` as a structural field.
- Add chart-wide relocated structure summaries:
  - above/below horizon concentration
  - eastern/western emphasis
  - angular-house concentration
  - clustered houses
  - public/private/relational/self-directed emphasis

Exit criteria:

- House transitions can be used across Place Profile, Search, and Between
  Places without bespoke body-by-body prose.
- No engine field invents final house-domain taxonomy before content approval.

### Phase 3: Natal Condition, Aspect-Network, and Rulership Propagation

Goal: Make line/contact interpretation personal to the natal chart instead of
generic planet grammar.

Required work:

- Extend emphasized-body profiles with:
  - natal sign and house
  - sect and condition classification
  - natal angularity
  - retrograde/motion state
  - major natal aspect network
  - ruled natal houses
  - safe relocated-house rulership lookup where approved
- Classify aspect-network roles:
  - `reinforcing`
  - `regulating`
  - `complicating`
  - `redirecting`
  - `polarizing`
  - `releasing`
  - `background`
- Add chart-ruler and luminary priority:
  - natal chart ruler
  - relocated Ascendant ruler by pure sign lookup only
  - Sun/Moon
  - MC ruler where relevant to goal
  - focal bodies in configurations where already computed

Guardrails:

- Do not run condition-bearing formulas on relocated payloads.
- Do not call full chart-ruler evaluators against relocated charts unless
  Astra/Ephemeris/Mason approve the method.
- Rulership propagation is interpretation context, not a guarantee of events.

Exit criteria:

- An angularized planet can carry its natal condition, natal aspects, and ruled
  domains into the evidence planner.
- Same planet/contact evidence reads differently when natal condition differs.

### Phase 4: Evidence Resolver and Theme Clusterer

Goal: Make synthesis real before prose expands.

Full build outline: `BUILD_OUTLINE_DRIFT_GUARD.md` Build Areas A and B.

Required work:

- Deduplicate same-root evidence.
- Identify independent repetition across angle contacts, house shifts, natal
  condition, rulership, and later line geometry.
- Emit theme clusters:
  - `convergent_theme`
  - `contradictory_axis`
  - `compensatory_structure`
  - `mixed_location`
  - `low_signal`
  - `time_sensitive_overlay`
- Preserve both sides of a contradiction. Do not average them away.
- Compute report priority from strength, confidence, repetition, and goal
  relevance.
- Emit resolver groups before theme clusters, not one combined opaque object.
- Preserve member evidence IDs on every group and cluster so reports can trace
  each synthesis claim back to computed evidence.

Exit criteria:

- The report planner can name a dominant pattern, primary tradeoff, supporting
  patterns, and omitted low-signal material from evidence objects alone.

### Phase 5: Multidimensional Goal Compatibility

Goal: Evaluate places for uses, not universal bestness.

Full build outline: `BUILD_OUTLINE_DRIFT_GUARD.md` Build Area C.

Required work:

- Define purpose categories:
  - career visibility
  - entrepreneurship
  - stable employment
  - public leadership
  - creative production
  - artistic reception
  - writing and study
  - partnership
  - dating
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
  - sensory sustainability
  - solitude
  - adventure and exploration
- For each category, distinguish:
  - `opportunity`
  - `ease`
  - `demand`
  - `durability`
  - `volatility`
- Add user-constraint inputs later:
  - primary goals
  - avoidances
  - time horizon
  - life stage
- Keep opportunity, ease, demand, durability, and volatility as separate
  dimensions. Do not collapse them into one score.
- Apply `purpose_lens` as relevance weighting only; it must not alter
  technical evidence strength or confidence.

Exit criteria:

- Search and Between Places can say "strong but demanding for X" instead of
  "best overall."
- User goals rerank relevance without rewriting technical evidence.

### Phase 6: Report Planner Before Prose Composer

Goal: Turn structured evidence into a narrative plan before authoring prose.

Full build outline: `BUILD_OUTLINE_DRIFT_GUARD.md` Build Area D.

Required report plan fields:

- one-sentence place thesis
- dominant place pattern
- structural shift from natal baseline
- opportunity architecture
- pressure architecture
- relational climate
- vocation/visibility relevance
- home/body/sensory relevance
- best uses
- poor or mismatched uses
- duration profile
- confidence classification
- technical appendix inputs
- section plan with source cluster IDs, source evidence IDs, claim boundaries,
  and required disclosures

Exit criteria:

- Prose can be generated from a report plan rather than from raw evidence
  lists.
- The planner can state when evidence is defining, strong, supported,
  possible, background, or too unstable to foreground.

### Phase 7: Future Method Modules

Goal: Add methods only after their computation and contracts are real.

Full build outlines: `BUILD_OUTLINE_DRIFT_GUARD.md` Build Areas G, H, and I.

World Lines:

- line generation
- nearest point / distance
- distance bands and continuous strength
- line clusters
- same-root confirmation with relocated angle contacts

Local Compass:

- altitude/azimuth convention
- directional rays
- cross-track distance
- direction bands
- use-mode compatibility

Living Map:

- static baseline plus date-bounded activation
- transits to relocated angles/houses
- timing windows
- baseline vs temporary distinction

Birth-Time Sensitivity:

- tested offsets, such as +/-2, +/-5, +/-10, +/-15 minutes
- stable findings
- sensitive findings
- angle/house changes
- overall confidence

Geographic Context:

- provider-sourced place facts
- climate/environment/infrastructure fields where sourced
- explicit separation from astrological evidence

Exit criteria:

- Every future-method module has independent tests and appendix disclosure.
- No future method appears as computed evidence before its method exists.

## Prose Upgrade Gate

Do not begin broad prose creation until at least Phases 1, 4, and 6 have an
initial tested implementation.

Permitted before then:

- schema notes
- `_note` guidance
- report-plan field names
- placeholder prose slots
- sample prose experiments clearly marked as non-authoritative

Not permitted before then:

- final high-volume combination prose
- large new content banks that assume unbuilt taxonomy
- prose that hides missing evidence-resolution logic

## Minimum Viable Non-Flattened Update

The smallest acceptable implementation of this plan is:

1. `evidence_grammar` package with normalized evidence item schema.
2. Adapters for current angle contacts, house changes, natal modifiers, and
   confidence notes.
3. Evidence resolver that separates same-root confirmation from independent
   repetition.
4. Theme clusterer that emits convergence and contradiction objects.
5. Goal compatibility profile with opportunity/ease/demand/durability/volatility.
6. Report planner skeleton that chooses thesis, dominant pattern, primary
   tradeoff, best uses, and confidence.
7. Tests proving current `LocationEvidenceRecord` can feed this pipeline
   without breaking existing renderers.

Anything less is a prototype, not completion.
