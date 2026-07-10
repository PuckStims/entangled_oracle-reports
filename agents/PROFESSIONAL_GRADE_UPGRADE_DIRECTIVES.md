# Professional-Grade Upgrade Directives

Date: 2026-07-10
Status: exploratory directive / future-agent handoff
Audience: Codex, Claude Code, Gemini/Antigravity, and the human operator

This file captures the speculative-but-actionable upgrade direction for
making Entangled Oracle too advanced for its indie creator category while
staying survivable for an indie, disabled, non-coding-led operator.

It is not an implementation claim. Future agents must verify current code
before acting. Treat this as a sequencing and decision framework for
formula, computation, and backend upgrades.

## Governing Intention

The first serious upgrade lane is not visual polish, professional
controls, locational astrology, or specialist branches. The first serious
upgrade lane is:

1. make formulas and computations coherent
2. make backend evidence and traceability robust enough to hold them
3. make synthesis smarter than raw method breadth
4. only then widen client-facing surfaces

The long-term target is not merely "an astrology app with reports." The
better target is a professional-grade astrological reasoning observatory
where every interpretive claim can trace back to its computational
ancestry.

## Current Starting Assumptions

Future agents must re-check these before implementation, but this is the
baseline for this directive:

- Current strongest client surfaces are `year_ahead` and
  `personal_forecast`.
- Current live forecasting includes transits, house ingresses, stations,
  eclipses, lunations, activation stacking, and selected progression /
  Solar Arc texture.
- Progressions, Solar Arc, returns, profections, Lots, and Zodiacal
  Releasing exist at different levels of implementation or scaffolding,
  but not all are first-class report surfaces.
- Profections have been used quietly for weighting/linkage in at least
  some paths, but visible time-lord output is not yet a mature product
  layer.
- `generate.py` remains the main orchestration bottleneck.
- `engine/transit_engine.py`, advanced method engines, formulas, report
  context builders, selectors, templates, and sidecars must not be blurred
  together casually.
- Professional controls, specialist branches, and locational astrology
  are explicitly optional for now unless the operator reopens them.
- Synastry is known necessary, but should be treated as its own mountain,
  not smuggled into forecast hardening.

## Non-Negotiable Operating Rules

1. Start every implementation run with `git status --short
   --untracked-files=normal`.
2. Do not overwrite human or other-agent changes.
3. Distinguish these states everywhere:
   - computed internally
   - preserved in evidence/sidecar
   - used for scoring/linkage
   - visible in client reports
   - described in docs only
4. Never promote a method to prose before its calculation convention,
   confidence policy, event schema, and regression fixtures are clear.
5. Keep raw computation, formula scoring, synthesis, content selection,
   and rendering as separate layers.
6. Do not let templates invent meaning absent from engine evidence.
7. Do not use "professional-grade" to justify uncontrolled scope
   expansion. Professional-grade means traceable, accurate, and
   configurable where necessary.
8. Specialist methods such as horary, electional, rectification,
   relocation, astrocartography, mundane ingress work, and professional
   UI controls are deferred unless explicitly assigned.
9. When a method is experimental, label it as experimental in evidence,
   docs, and any future prose.
10. Update `agents/REVISIONS.md` only after work actually lands. Keep
    speculative direction here or in `agents/PLANNED_UPDATES.md`.

## Builder And Review Crew Model

When token limits, speed, or breadth make a high-throughput builder
useful, the preferred role split is:

- Gemini/Antigravity: candidate construction
- Codex/ChatGPT and Claude Code: alignment authority

This is a valid operating model only if the split is explicit.

### Powerhouse-then-refine, not propose-then-build

Gemini/Antigravity's job is to power through and build real scaffolding and
pathways inside its assigned tier -- including runtime code -- even in
places everyone already expects it to get partially wrong. The point of
the crew model is that Codex/ChatGPT and Claude Code refine and correct
what Gemini actually built, in place, rather than Gemini staying confined
to planning documents until someone else builds the real thing from
scratch. Treat every Gemini pass as a working first draft of runtime code
to be hardened, not merely a proposal to be approved or rejected wholesale.

Tier boundaries still gate *what* Gemini is allowed to build -- a Tier 0/1
pass should not create a Tier 2 method registry or a Tier 3 scoring
formula -- they do not gate *whether* Gemini may touch runtime code within
its assigned tier. A containment brief that reduces a Tier 1-inclusive run
to "documentation only, do not change runtime behavior" is under-scoping
the model, not correctly applying it; see `agents/HIGH_THROUGHPUT_AGENT_PROMPTS.md`
for the corrected concrete brief.

Gemini/Antigravity is well suited for:

- large mechanical scaffolds
- repetitive adapters and mappings
- fixture scaffolds
- schema expansions
- JSON/content coverage maps
- broad-but-bounded implementation passes
- normalization work

Gemini/Antigravity is not final authority for:

- astrological method correctness
- formula semantics
- scoring thresholds
- claim language
- architecture boundary decisions
- whether a feature is "done"
- whether a surface is client-safe
- whether EO voice survived the pass

Every Gemini/Antigravity build run should start from a containment brief
that states:

- exact files allowed
- exact files forbidden
- source-of-truth docs to read first
- what counts as success
- what must remain unchanged
- what must stay internal-only
- tests required
- handoff evidence required
- what the builder is not allowed to decide

Every Gemini/Antigravity handoff should include:

- files changed
- tests run
- tests not run
- assumptions made
- places where it guessed
- open uncertainty
- recommended next review

Codex/ChatGPT review responsibilities:

- architecture coherence
- EO alignment
- schema/event/model sanity
- fixture sufficiency
- practical handoff quality
- targeted correction patching

Claude Code review responsibilities:

- prompt-to-implementation fidelity
- drift and flattening detection
- hidden scope expansion
- claim/doc/code inconsistency
- untested behavior changes
- precision and nuance loss

Treat Gemini/Antigravity output as a candidate build, not as merge-ready
truth.

## Gemini-Safe Global Guardrails

Unless the operator says otherwise, Gemini/Antigravity should not:

- decide astrological conventions from scratch
- widen scope beyond the assigned tier
- edit multiple unrelated report types in one run
- promote internal methods into client prose
- rewrite product-positioning docs
- declare a feature production-ready
- edit both core engine logic and narrative/report claims in the same run
- silently reorganize architecture for elegance
- replace nuanced EO distinctions with flattened generalized wording
- change policy/contract docs while another builder is implementing from
  them
- invent a new registry, schema, or contract module without first
  searching the repo for one that already covers the same concept and
  reusing or extending it (this is the specific failure mode from the
  first Tier 0/1 run: a new `engine/method_registry.py` duplicated both
  `formulas/standard/method_registry.py` and
  `formulas/governance_registry.py` without checking either)

Preferred Gemini/Antigravity lane:

- bounded construction inside a predeclared seam
- explicit internal-only work
- mechanical normalization
- repetitive expansion that is expensive in human tokens but easy to
  review

Preferred Codex/Claude lane:

- method charters
- formula review
- architecture review
- claim-safety review
- final promotion decisions
- corrective narrowing after drift

## Summit Filters

Use these five Observatory roles when reviewing upgrade proposals:

- Astra: method coherence, tradition versus EO design choice,
  interpretive proportionality.
- Meridian: formulas, scoring, variance, calibration, ranking usefulness.
- Mason: architecture boundaries, maintainability, interfaces, test seams.
- Sentinel: claim integrity, provenance, confidence, disclosure, release
  safety.
- Gardener: scope discipline, founder capacity, staged maturity.

Optional second-pass reviewers:

- Ephemeris for time, position, station, ingress, eclipse, and exactness
  risk.
- Weaver for content-library schema and fallback behavior.
- Scribe for client-facing language once data is proven.
- Lumen for visual systems after synthesis objects exist.
- Catalyst for fixtures, regression tests, and release-readiness gates.

## Tier 0 - Audit Bedrock

Goal: make the current system impossible to misunderstand before adding
more method weight.

Note: Tier 0 alone is audit-only by definition, not by distrust -- there
is nothing to build yet, only to inventory. In practice the recommended
first real project spans Tier 0 and Tier 1 together (see below); when a
run is scoped that way, Tier 1's guardrails govern the buildable half of
it. Don't downgrade Tier-1-appropriate implementation work to
documentation-only just because "Tier 0" is in the run's label.

Required directives:

- Build or update a method ledger that records every active, partial,
  hidden, quarantined, and absent predictive method.
- For every report type, map:
  - generator entry point
  - computation functions called
  - formula/scoring functions called
  - context fields emitted
  - template sections consuming those fields
  - sidecars/manifests written
  - hidden fields computed but not displayed
- For every advanced method, classify it as:
  - active surfaced
  - active hidden weighting/linkage
  - active sidecar/internal evidence only
  - implemented but unwired
  - scaffold/reference only
  - absent
- Create or refresh golden test charts for:
  - exact birth time
  - approximate birth time
  - unknown birth time
  - high-density transit year
  - quiet transit period
  - retrograde multi-pass period
  - angular emphasis chart
  - chart with strong sect/dignity contrasts
- Preserve golden generated reports for current `year_ahead` and
  `personal_forecast` before large computation changes.
- Add event-trace snapshots where feasible so future agents can compare
  the shape of raw evidence, not only rendered prose.

Acceptance threshold:

- A future agent can answer "what computes this paragraph?" and "why did
  this event rank here?" without reconstructing the whole repo from
  scratch.

Do not:

- Add new methods.
- Rewrite report prose.
- Move template sections.
- Rebrand docs around unverified capabilities.

Gemini-safe guardrails:

- Allowed:
  - inventories
  - ledgers
  - call-path maps
  - event-field extraction tables
  - fixture manifests
- Do not access or modify:
  - templates
  - client-facing prose blocks
  - formula thresholds
  - method-charter decisions
- Review requirement:
  - Codex or Claude must confirm the ledger matches current code reality
    before any build work starts from it.

## Tier 1 - Core Forecast Computation Hardening

Goal: make the active transit/forecast layer professional-trustworthy.

Scope:

- natal-to-transit contacts
- applying / exact / separating logic
- retrograde multi-pass handling
- station detection
- sign and house ingresses
- lunations and eclipses
- void-of-course Moon, if retained
- Whole Sign house activation
- angular activation
- natal condition modifiers:
  - sect
  - essential dignity
  - angularity
  - house rulership
  - chart ruler / dominant planet
  - planetary condition

Backend directives:

- Establish one canonical forecast event shape for all active event
  families. If the repo already has a newer object contract, reuse it
  rather than inventing a competing one.
- Normalize required event fields:
  - `event_id`
  - `method_family`
  - `event_kind`
  - `source_body`
  - `target_body`
  - `aspect`
  - `house`
  - `sign`
  - `peak_date`
  - `entry_date`
  - `leave_date`
  - `orb`
  - `exactness`
  - `direction`
  - `birth_time_dependency`
  - `confidence`
  - `score_components`
  - `render_visibility`
- Make local/UTC assumptions explicit in event computation and output.
- Add tests that prove the same event does not drift between Year Ahead
  and Personal Forecast because two paths compute timing differently.
- Ensure stations, ingresses, lunations, and eclipses cannot fake
  independent method convergence when they are subtypes of the same sky
  condition.
- Keep reader-facing intensity separate from structural importance.

Acceptance threshold:

- Current active reports remain functionally stable, but every core event
  carries enough structured evidence to support later synthesis and audit.

Do not:

- Add another clock family before event shape and timing confidence are
  stable.
- Treat a station plus a transit from the same planet as two independent
  "votes" unless the method policy explicitly says so.

Gemini-safe guardrails:

- Allowed:
  - canonical event adapters
  - field normalization
  - test scaffolds
  - serializer updates
  - timing-field plumbing already implied by existing calculations
- Do not access or modify without explicit approval:
  - client templates
  - prose block libraries
  - report marketing/readiness docs
  - method-charter files that define conventions
- Review requirement:
  - Codex or Claude must inspect anti-double-counting, timing semantics,
    and exactness behavior before acceptance.

## Tier 2 - Promote Existing Advanced Engines To First-Class Internals

Goal: stop treating advanced methods as scattered side engines.

Scope:

- annual profections
- monthly profections if explicitly chosen
- Lord of the Year / time lord
- progressed Moon
- progressed lunation phase
- progressed ingresses
- secondary progression contacts
- Solar Arc contacts
- solar, lunar, Jupiter, and Saturn returns
- Lots of Fortune, Spirit, and Necessity
- Zodiacal Releasing periods and peak markers

Backend directives:

- Create or reuse a method registry with:
  - method id
  - calculation convention
  - required inputs
  - birth-time dependency
  - supported bodies/points
  - orb/window policy
  - confidence policy
  - report-surface permission
  - status: production, internal, experimental, scaffold
- Use common period/event formats:
  - `ForecastEvent` for dateable contacts/triggers
  - `TimeLordPeriod` for profections/ZR/time-lord spans
  - return-chart objects only when full return interpretation is truly
    in scope
- Preserve method source labels:
  - transit
  - progression
  - solar_arc
  - return
  - profection
  - zodiacal_releasing
  - lot
- Keep all advanced outputs internally inspectable before making them
  visible.
- Add method-specific fixtures independent of report generation.
- Require each method to answer:
  - What does it calculate?
  - What does it not calculate?
  - What can it claim?
  - What does it merely contextualize?
  - What birth-data confidence does it require?

Acceptance threshold:

- Advanced methods can be run, serialized, traced, and tested without
  requiring a template or prose section.

Do not:

- Surface time-lord language before the method payload can explain the
  profected house/sign/lord and its natal condition.
- Treat Lots as interpretive prose decorations; make them reusable chart
  factors first.
- Build full return-chart interpretation in the same pass as exact return
  moment extraction.

Gemini-safe guardrails:

- Allowed:
  - internal method modules
  - registry loading
  - sidecar/evidence serialization
  - fixture generation
  - reusable object plumbing
- Do not access or modify without explicit approval:
  - report templates
  - client-facing block selection logic for new methods
  - report-surface visibility defaults
  - methodology/claim docs that imply activation
- Review requirement:
  - Astra/Meridian-style review by Codex or Claude before any advanced
    method is described as meaningful beyond internal evidence.

## Tier 3 - Formula Intelligence And Signal Hierarchy

Goal: make EO better than software that merely calculates everything.

Scope:

- multi-clock convergence scoring
- time-lord weighting
- natal condition weighting
- return-chart emphasis modifiers, once return charts exist
- repeat-pattern detection
- method-family independence
- single signal versus stacked signal classification
- structural importance versus emotional intensity versus practical
  timing
- calibrated reader-facing intensity labels

Backend directives:

- Every score must expose components. Do not collapse everything into one
  unexplained number.
- Use separate components for:
  - timing exactness
  - natal relevance
  - method weight
  - time-lord support
  - repetition/echo
  - house/topic relevance
  - angularity
  - dignity/condition
  - convergence
  - counterforce/conflict
  - confidence
- Require before/after score distributions when changing formula
  thresholds.
- Add calibration fixtures where many events cluster so agents can see
  whether all months become overactivated.
- Preserve low, medium, high, and peak labels only if score ranges
  actually produce useful variance.
- Create "why this ranked high" diagnostics for any ranked timeline or
  monthly peak.

Acceptance threshold:

- A high-ranked event can explain itself without prose invention:
  "This ranked high because..." followed by structured score components.

Do not:

- Let elegant math override astrological salience.
- Let astrological salience bypass distribution testing.
- Use more score categories than the data can support.

Gemini-safe guardrails:

- Allowed:
  - score component plumbing
  - trace fields
  - diagnostics objects
  - distribution test scaffolds
- Do not access or modify without explicit approval:
  - score label prose
  - threshold naming in client copy
  - high-level methodological claims about what a score "proves"
- Review requirement:
  - Codex or Claude must review variance, inflation, and visible report
    consequences before accepting formula changes.

## Tier 4 - Synthesis Backend

Goal: turn many clocks into coherent interpretive terrain before adding
more prose.

Scope:

- annual terrain map
- monthly pressure/opening/recovery zones
- peak-window clustering
- contradiction detection between methods
- technique agreement labels
- repeating natal themes
- chapter assembly based on evidence
- forecast terrain by topic and time

Backend directives:

- Build a synthesis layer that consumes normalized evidence rather than
  raw engine-specific shapes.
- Keep synthesis objects separate from templates.
- Recommended synthesis labels:
  - convergent
  - supportive
  - isolated
  - ambiguous
  - contradictory
  - background
  - trigger
  - chapter
  - aftermath
- Detect whether methods agree by declared operation compatibility, not
  by prose similarity.
- Preserve contradictions. Do not smooth them into fake coherence.
- Record which methods support a chapter and which methods oppose or
  complicate it.
- Require provenance chains from synthesis section back to source events
  and periods.
- Build debug views or trace dumps before visual/report polish.

Acceptance threshold:

- EO can describe a month/year as terrain, not merely an event list, and
  each terrain claim remains traceable to structured evidence.

Do not:

- Let a beautiful chapter title become a substitute for method support.
- Merge all clock signals into a single vibe field.

Gemini-safe guardrails:

- Allowed:
  - synthesis objects
  - provenance links
  - debug views
  - evidence aggregation plumbing
- Do not access or modify without explicit approval:
  - final prose wording
  - visual hierarchy decisions
  - template storytelling
- Review requirement:
  - Codex or Claude must confirm the synthesis layer preserves
    disagreement and provenance rather than flattening it into generic
    summary fields.

## Tier 5 - Report Surface Promotion

Goal: expose only the computation/synthesis that has earned visibility.

Scope:

- Year Ahead upgrades
- Personal Forecast upgrades
- optional later Daily/Weekly upgrades
- method transparency notes
- traceable "based on" disclosures

Backend/report directives:

- Promote evidence to reports by adapter, not by template scraping.
- Every new visible section must state its basis in report context data.
- Keep experimental predictive content visibly labeled if not validated.
- Do not present candidates, chapters, or time-lord periods as certainty.
- Use a report adapter that can filter methods by:
  - report type
  - birth-time confidence
  - method status
  - client usefulness
  - operator/product choice
- Preserve full score components in data even if prose narrates only the
  human-readable subset.

Acceptance threshold:

- Client-facing reports become richer without losing claim integrity.

Do not:

- Add visible methods because they are impressive.
- Hide weak confidence behind poetic language.

Gemini-safe guardrails:

- Allowed only if explicitly authorized in the brief:
  - additive report context fields
  - adapter-layer gating
  - experimental section wiring
- Do not access or modify by default:
  - `products/*/templates/`
  - prose block libraries
  - outward-facing product docs
  - language that changes what the product claims to do
- Review requirement:
  - Claude/Codex claim-safety review is mandatory before any new method
    becomes client-visible.

## Tier 6 - Synastry As A Separate Mountain

Goal: make synastry climbable by building two-chart computation grammar
first.

Synastry must not be treated as a minor report variant. It is a second
architecture because it requires two natal payloads, directional meaning,
privacy/consent framing, relationship-specific synthesis, and eventually
relationship timing.

First substrate:

- two-chart input schema
- Person A natal payload
- Person B natal payload
- shared metadata and birth-time confidence for both people
- directional aspects:
  - A planet/point to B planet/point
  - B planet/point to A planet/point
- mutual aspect normalization
- house overlays:
  - A bodies in B houses
  - B bodies in A houses
- angle dependency and withheld-angle behavior
- repeated natal themes between charts

Second substrate:

- composite chart computation
- optional Davison chart only if explicitly chosen
- composite aspects and houses
- composite chart condition summary
- relationship topic signatures
- relationship-specific convergence scoring

Third substrate:

- current transits to each natal chart
- current transits to composite
- progressions/Solar Arc to composite only after single-chart methods are
  mature
- relationship timing windows
- event objects that identify whether the signal belongs to:
  - Person A
  - Person B
  - the relationship/composite
  - shared timing

Synastry backend requirements:

- Pair chart schema.
- Directional versus mutual handling.
- Composite payload.
- Relationship-specific event schema.
- Separate confidence and privacy policy.
- Consent-aware output framing.
- Tests for missing/approximate birth time on either side.

Acceptance threshold:

- A future relationship report can be built from a reliable two-chart
  grammar without forcing all synastry logic through one-chart forecast
  assumptions.

Do not:

- Begin by writing the relationship report.
- Treat synastry aspects as symmetric when the house overlay or angle
  dependency is directional.
- Let relationship prose diagnose, prescribe, or moralize.

Gemini-safe guardrails:

- Allowed:
  - pair-chart schemas
  - directional aspect computation
  - composite payload scaffolds
  - relationship event objects
  - two-chart fixtures
- Do not access or modify without explicit approval:
  - relationship prose libraries
  - final relationship templates
  - therapeutic/guidance framing
  - privacy-policy or consent language without review
- Review requirement:
  - Codex or Claude must verify directional logic, privacy framing, and
    missing-birth-time behavior before promotion.

## Tier 7 - Specialist Branches And Deep-Cut Research

Goal: widen method breadth only after the core observatory is stable.
Sequencing decision (2026-07-10, operator): this tier finalizes
specialist branches and advanced professional research. Locational work
is not part of this tier - see Tier 8.

Suites in scope:

- specialist branches:
  - electional
  - horary
  - rectification
  - mundane ingress/national chart work
- advanced professional research:
  - primary directions
  - firdaria
  - decennials
  - distributions through bounds
  - fixed stars
  - midpoints
  - harmonics

Directive:

- Treat these as widening moves, not deepening moves.
- Do not start here unless the operator explicitly chooses a suite.
- If opened, each suite needs its own method charter, input model,
  confidence policy, and report-surface policy.

Gemini-safe guardrails:

- Allowed only with suite-specific authorization.
- Do not access by default: specialist branch docs, new UI/config
  toggles.
- Review requirement: treat each suite as its own initiative with fresh
  guardrails, not as "extra work attached to an existing tier."

## Tier 8 - Locational Suite

Goal: relocation-aware chart work, opened only after Tier 7 is settled.

Suites in scope:

- relocation charts
- astrocartography
- relocated returns

Directive: same widening-move discipline as Tier 7 - operator must
explicitly choose to open this, each piece gets its own method charter,
confidence policy, and report-surface policy.

Gemini-safe guardrails:

- Allowed only with suite-specific authorization.
- Do not access by default: locational suite files, new UI/config
  toggles.
- Review requirement: same as Tier 7 - its own initiative, fresh
  guardrails.

## Deprioritized indefinitely: professional controls

House systems, orb profiles, aspect sets, alternate zodiac modes, method
toggles, dignity scheme toggles - the operator has explicitly deprioritized
this suite below Tiers 6/7/8. Do not open it speculatively. The bar to
revisit: a concrete business case (a partner or client need), not
"it would round out the professional feature set."

## Recommended First Real Project

The cleanest first project is:

**Forecast Computation Ledger + Canonical Event Schema**

Deliverables:

1. A ledger documenting current method state and report consumption.
2. A canonical event schema or adapter plan anchored to existing objects.
3. A gap list for fields missing from current transits, progressions,
   Solar Arc, returns, profections, Lots, and ZR outputs.
4. A focused fixture set proving current events can be serialized
   consistently.
5. No client-facing prose changes.

Why this first:

- It gives every later method a place to land.
- It reduces future-agent guesswork.
- It prevents advanced engines from becoming brilliant loose wires.
- It makes synastry easier later by establishing schema discipline now.

## Handoff Format For Future Agents

When picking up any tier, report:

ISSUE:
WHAT I VERIFIED:
WHAT I CHANGED:
WHAT I DID NOT CHANGE:
WHAT IS COMPUTED INTERNALLY:
WHAT IS PRESERVED IN EVIDENCE/SIDECAR:
WHAT IS CLIENT-VISIBLE:
TESTS RUN:
OPEN RISKS:
NEXT SAFE HANDOFF:

## Final Orientation

The repo should get more structurally intelligent before it gets more
metaphysically ambitious.

Professional-grade means the calculations are trustworthy. Advanced means
the system can explain why a signal matters. Unacceptably advanced means
the system can compare clocks, preserve disagreement, show provenance,
and still give a human a useful forecast without making the operator hold
the whole cosmos in working memory.
