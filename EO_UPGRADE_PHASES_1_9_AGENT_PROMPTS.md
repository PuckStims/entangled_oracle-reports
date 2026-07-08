# Entangled Oracle Upgrade Phases 1-9 Agent Prompts

Date: 2026-07-07
Status: coordination plan
Audience: Codex, Claude Code, and the human operator

This file turns the full predictive upgrade program into phase-specific
implementation prompts for non-interfering agent runs.

It complements:

- `EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md`
- `EO_MULTICLOCK_ASTEROID_PREDICTIVE_READINESS_AUDIT.md`
- `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md`
- `ENGINE_CAPABILITY_SURFACE_AUDIT.md`
- `phase0/`
- `agents/PLANNED_UPDATES.md`
- `agents/REVISIONS.md`

## Non-Negotiable Direction

The upgrade target is not a minimum viable patch. Entangled Oracle must
become a comprehensively upgraded, asteroid-rich, multi-clock forecasting
and research system.

The following are required scope, not optional future ideas:

- progressions
- Solar Arc
- returns
- profections
- time lords
- Lots
- Zodiacal Releasing
- all 34 asteroids as governed predictive participants
- discrete external-event candidate research
- sidecar-level evidence and validation infrastructure

The sequencing rule is:

1. calculate internally
2. preserve evidence in sidecars
3. validate
4. only then expose to client-facing prose

No phase may shrink the destination. A phase may only sequence, gate, or
validate it.

## Global Non-Interference Rules

Every agent run must begin with:

```powershell
git status --short --untracked-files=normal
```

If the intended files are already modified by another agent or by the
human operator, stop and report the conflict. Do not revert, overwrite,
rename, delete, or "clean up" work that is not yours.

Each run must write a short closeout note with:

- files changed
- tests run
- tests not run and why
- open risks
- exact next handoff

Use `agents/REVISIONS.md` only after a meaningful implementation lands.
Use `agents/PLANNED_UPDATES.md` only for current open work. Do not let
these files become speculative hype.

## Phase 0 Gate

Phase 1 does not touch any `phase0/` contract and may start immediately.

Phase 2 and every phase after it implements directly against `phase0/`
contracts. Per `phase0/README.md`'s own "Definition of Phase 0 done"
checklist, those contracts require an explicit operator sign-off note
in `agents/REVISIONS.md` before implementation begins. Do not start a
Phase 2+ prompt until that sign-off exists. If a phase's Claude review
pass surfaces a contract gap, resolve it in `phase0/` first, note the
resolution, and only then hand the phase to Codex.

## Anchor Linkage Deferral (Phases 4-6)

Every `ForecastEvent` carries a `natal_anchor_ids` field
(`phase0/01_predictive_object_schemas.md` §2), populated by an
anchor-matcher that reads `NatalPromiseAnchor` records
(`phase0/01_predictive_object_schemas.md` §1). That anchor-matcher is
not built until Phase 7.

This means Phases 4, 5, and 6 (returns, profections, Solar Arc,
progressions, Lots, Zodiacal Releasing) will each emit `ForecastEvent`
records before an anchor-matcher exists to populate that field. The
rule for those phases: leave `natal_anchor_ids` empty at emission and
do not build a phase-local, ad hoc anchor-matching shortcut to fill
it. Phase 7 backfills linkage for every previously emitted event when
its anchor-matcher lands, using each event's existing `source_body`,
`target_body`, and `method_family` fields, which are sufficient for
retroactive matching. Building three separate partial matchers across
Phases 4-6 would fragment the very linkage logic Phase 7 exists to
centralize.

## Phase Ownership Model

Codex should generally own runnable code, tests, integration seams, and
verification.

Claude Code should generally own audits, contract review, prompt-to-file
consistency checks, docs, schema critique, fixture design, and
implementation planning.

Both agents may work in the same phase only when their file ownership is
separate. If code and docs need the same file, do not run simultaneously.

## Phase 1 - Current Client Forecast Adequacy Repair

Purpose:
Repair defects found in `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md`
before advanced methods are surfaced.

Required outcomes:

- Daily Horoscope respects requested `--report-date`.
- Weekly Horoscope is either genuinely chronological or clearly labeled
  as ranked top moments.
- Weekly Horoscope gains an authored interpretive layer or is explicitly
  scoped as a technical timing report until that layer lands.
- Personal Forecast timeline dots reflect actual date spacing.
- Year Ahead exact-birth-time policy remains explicit.
- Outward-facing claims do not mention inactive methods as active.

Codex file ownership:

- `generate.py`
- `selectors/variable_resolver.py`
- `engine/transit_engine.py`
- `products/daily_horoscope/`
- `products/weekly_horoscope/`
- `products/personal_forecast/templates/personal_forecast.html`
- `tests/test_daily_horoscope_activation.py`
- new focused tests under `tests/`

Claude file ownership:

- `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md`
- claim inventory notes in a new audit file if needed
- copy/doc review only, unless Codex is idle

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 1 of EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md.

Goal: implement the client forecast adequacy repairs from CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md without touching advanced method architecture.

Start by running git status and inspecting the current dirty files. Do not revert or overwrite unrelated changes. Then fix the highest-value Phase 1 items in this order:
1. Daily Horoscope must respect --report-date throughout resolver and activation selection.
2. Weekly Horoscope must stop presenting a ranked list as a chronology, either by chronological rendering after selection or by explicit "top moments" labeling.
3. Add or adjust focused tests proving the date-control and weekly-order behavior.
4. If safe in the same run, improve Personal Forecast timeline-dot positioning so visual spacing reflects real timing windows.

Do not edit phase0 contracts. Do not introduce progressions, Solar Arc, returns, profections, time lords, Lots, Zodiacal Releasing, or discrete candidate logic in this phase. Those are required later phases, not Phase 1 shortcuts.

Close with files changed, tests run, unresolved risks, and update agents/REVISIONS.md only for work actually completed.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 1 review support only.

Goal: perform a claim and presentation audit for current client forecast surfaces while Codex handles code. Do not edit generate.py, engine/, selectors/, product templates, or tests.

Start with git status. Read CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md, README.md, METHODS.md, ARCHITECTURE.md, agents/PLANNED_UPDATES.md, and product-facing docs. Identify any language claiming or implying active progressions, Solar Arc, returns, profections, time lords, Zodiacal Releasing, or concrete external-event prediction before those systems exist.

Deliver either:
1. a read-only report in chat, or
2. a new markdown audit file named CLIENT_FORECAST_CLAIM_CLEANUP_QUEUE.md if the operator explicitly allows file creation.

Do not modify source code. Do not rewrite existing docs unless specifically asked after the audit.
```

## Phase 2 - Predictive Evidence Infrastructure

Purpose:
Build the evidence layer that every advanced method must use before it
can become report prose.

Required outcomes:

- shared `ForecastEvent` object
- shared `PredictiveSignal` object or adapter
- internal `.eo_predictive.json` sidecar
- immutable natal snapshot section
- daily contributor provenance
- rejected-candidate registry
- method-policy and registry version capture
- reproducible run package shape

Codex file ownership:

- new evidence modules under `engine/` or a new `predictive/` package
- sidecar writer seam
- tests for sidecar shape and serialization
- minimal integration from existing Year Ahead / Personal Forecast events

Claude file ownership:

- `phase0/01_predictive_object_schemas.md`
- `phase0/06_sidecar_and_export_contract.md`
- schema conformance notes

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 2 evidence infrastructure.

Goal: create the internal predictive evidence layer required by EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md and EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md.

Start with git status. Read phase0/01_predictive_object_schemas.md and phase0/06_sidecar_and_export_contract.md. Implement the smallest complete evidence foundation that can serialize current transit-based Year Ahead / Personal Forecast events into a separate .eo_predictive.json sidecar without changing client report prose.

Required: ForecastEvent normalization, PredictiveSignal preservation/adaptation, immutable natal snapshot fields, method-policy version fields, rejected-candidate registry placeholder, and tests proving the sidecar writes valid JSON with stable required keys.

Do not implement new method clocks in this phase. Do not put advanced methods into templates. This phase is the evidence runway for every later method.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 2 contract review.

Goal: audit phase0/01_predictive_object_schemas.md and phase0/06_sidecar_and_export_contract.md for field completeness before Codex implements the sidecar.

Do not edit code. Check whether the contracts cover transits, asteroids, returns, Solar Arc, progressions, profections, Lots, Zodiacal Releasing, time-lord periods, discrete candidates, rejected candidates, validation run packages, and client/report gating.

If changes are needed, propose exact markdown patches or create a separate PHASE2_CONTRACT_REVIEW.md if allowed. Do not rewrite phase0 files during simultaneous Codex implementation unless the operator assigns you that ownership.
```

## Phase 3 - All-34 Asteroid Predictive Activation

Purpose:
Make all 34 asteroids governed predictive participants, not accidental
natal-only data.

Required outcomes:

- machine-readable all-34 asteroid predictive registry is adopted
- registry-driven target eligibility
- registry-driven source eligibility
- registry-driven clock eligibility
- asteroid-aware event normalization
- proprietary asteroid scanner contributes to internal R&D evidence
- asteroid participation appears in sidecar provenance
- no asteroid silently disappears because a scanner forgot it exists

Codex file ownership:

- registry loader
- asteroid policy API
- scanner integration behind R&D gate
- sidecar asteroid provenance
- asteroid regression tests

Claude file ownership:

- `phase0/02_asteroid_predictive_registry.md`
- `phase0/02_asteroid_predictive_registry.json`
- asteroid policy review and missing-field queue

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 3 asteroid predictive activation.

Goal: wire the all-34 asteroid predictive registry into internal predictive evidence. Start with git status. Read phase0/02_asteroid_predictive_registry.md and .json plus EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md Workstream B.

Implement registry loading, validation that the count is exactly 34, and a registry-driven policy API for target/source/clock eligibility. Preserve current behavior while making exclusions explicit. Wire existing proprietary asteroid forecast windows into internal R&D evidence and sidecar provenance behind a feature gate.

Do not add asteroid claims to client prose. Do not replace existing natal asteroid interpretation. Add tests proving all 34 bodies are present, registry fields are required, and eligible asteroid activations can appear in evidence traces.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 3 asteroid policy review.

Goal: audit the all-34 asteroid registry for completeness, contradictions, and missing predictive policy.

Do not edit code. Check every asteroid for natal roles, topic keys, source eligibility, target eligibility, clock eligibility, allowed aspects, orb policy, weighting, confidence modifiers, report-surface permissions, and validation category.

Produce a precise issue list keyed by asteroid name and field. Do not generalize. If allowed to create a file, write PHASE3_ASTEROID_POLICY_REVIEW.md.
```

## Phase 4 - Returns and Annual Profections

Purpose:
Add the first required non-transit clock layer: return moments and
annual profection/time-lord relevance.

Required outcomes:

- exact Solar return moments
- exact Lunar return moments
- exact Jupiter return moments
- exact Saturn return moments
- annual profected house
- annual profected sign
- annual time lord
- time-lord natal condition summary
- return/profection ForecastEvents or TimeLordPeriod records
- `natal_anchor_ids` left empty per the Anchor Linkage Deferral note above; no phase-local anchor matching
- sidecar export and validation fixtures

Codex file ownership:

- returns calculation module
- profections calculation module
- `ForecastEvent` / `TimeLordPeriod` integration
- tests and fixtures

Claude file ownership:

- `phase0/03_method_charters.md`
- method-charter review for returns and profections

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 4 returns and annual profections.

Goal: implement exact return moments and annual profection/time-lord evidence as internal predictive clocks.

Start with git status. Read phase0/03_method_charters.md, phase0/01_predictive_object_schemas.md, and EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md Phase 4. Implement Solar, Lunar, Jupiter, and Saturn return moments as evidence events. Implement annual profected house/sign and time lord as a TimeLordPeriod or equivalent relevance object.

Everything must export to the .eo_predictive.json sidecar. Nothing enters client prose yet. Leave ForecastEvent.natal_anchor_ids empty — anchor-matching is Phase 7's job, not this phase's; do not build ad hoc anchor matching here. Add fixtures and tests proving exact date behavior, birth-time dependencies, method_family independence, and anti-double-counting boundaries.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 4 method-charter audit.

Goal: verify that the returns and profections charter is complete enough for implementation.

Do not edit code. Review calculation convention, zodiac/house assumptions, allowed bodies, asteroid compatibility, orb/buffer policy, chapter versus trigger role, anti-double-counting, topic linkage, confidence policy, and report-surface policy.

Return exact missing or ambiguous charter items before Codex promotes anything beyond internal evidence.
```

## Phase 5 - Solar Arc and Secondary Progressions

Purpose:
Add long-clock developmental and directional methods.

Required outcomes:

- one declared Solar Arc convention
- directed natal planets
- directed angles with birth-time gating
- directed asteroids where policy allows
- Solar Arc contacts to natal planets, angles, and asteroid targets
- secondary progressed chart constructor
- progressed planets and selected asteroids
- progressed angles where eligible
- progressed-to-natal contacts
- progressed ingresses
- progressed lunation phase
- `natal_anchor_ids` left empty per the Anchor Linkage Deferral note above; no phase-local anchor matching
- sidecar export and validation fixtures

Codex file ownership:

- Solar Arc module
- secondary progressions module
- evidence integration
- tests and fixtures

Claude file ownership:

- method-charter review for Solar Arc and progressions
- fixture critique

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 5 Solar Arc and secondary progressions.

Goal: implement Solar Arc directions and secondary progressions as internal long-clock evidence.

Start with git status. Read phase0/03_method_charters.md and the evidence contracts. Implement exactly one declared Solar Arc convention and one declared secondary progression convention. Include directed/progressed asteroids only through registry policy. Gate angles by birth-time confidence. Emit evidence records and sidecar traces.

Do not surface these methods in client prose. Leave ForecastEvent.natal_anchor_ids empty — anchor-matching is Phase 7's job, not this phase's; do not build ad hoc anchor matching here. Add tests for exact/approximate/unknown birth-time behavior, asteroid policy compatibility, method_family distinction, and sidecar serialization.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 5 long-clock review.

Goal: audit the Solar Arc and progression method charters plus planned fixtures before code promotion.

Do not edit code. Identify any ambiguity in convention, date mapping, angle handling, asteroid eligibility, orb policy, confidence, anti-double-counting, or validation criteria. Produce exact findings and recommended acceptance fixtures.
```

## Phase 6 - Lots, Zodiacal Releasing, and Time-Lord Infrastructure

Purpose:
Build nested time-lord context rather than only transit/progression
weather.

Required outcomes:

- Lot of Fortune
- Lot of Spirit
- Lot of Necessity
- sect-aware lot formulas
- reusable `TimeLordPeriod` contract
- Zodiacal Releasing L1-L4 periods
- peak periods
- loosing-of-the-bond markers
- period rulers
- Fortune vs Spirit domain mode
- `natal_anchor_ids` left empty per the Anchor Linkage Deferral note above; no phase-local anchor matching
- sidecar export and validation fixtures

Codex file ownership:

- lots calculation module
- Zodiacal Releasing module
- TimeLordPeriod integration
- tests and fixtures

Claude file ownership:

- Lots/ZR charter review
- time-lord terminology and claims audit

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 6 Lots, Zodiacal Releasing, and time-lord infrastructure.

Goal: implement Lots and Zodiacal Releasing as internal time-lord evidence.

Start with git status. Read phase0/03_method_charters.md (C5 Lots and C5b Zodiacal Releasing charters) and phase0/01_predictive_object_schemas.md §6 (the TimeLordPeriod contract). Implement Lot of Fortune, Lot of Spirit, and Lot of Necessity with sect-aware formulas. Then implement ZR period generation through L1-L4, including period rulers, peak/transition states, loosing-of-the-bond markers, and domain mode.

All output must go to sidecar evidence. Do not add client-facing ZR claims. Leave ForecastEvent.natal_anchor_ids empty — anchor-matching is Phase 7's job, not this phase's; do not build ad hoc anchor matching here. Add tests for sect formulas, known period boundaries, birth-time dependencies, and serialization.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 6 time-lord review.

Goal: audit the Lots and ZR charter for formula clarity, sect handling, domain assignment, period nesting, peak logic, loosing markers, and report-surface restrictions.

Do not edit code during Codex implementation. Produce a precise review with fixture recommendations and claim-language warnings.
```

## Phase 7 - Natal Promise Graph and Cross-Clock Convergence

Purpose:
Build the graph that explains why a forecast event matters for a
specific chart, then compose independent evidence without stacking.

Required outcomes:

- `NatalPromiseAnchor` construction
- topic/domain keys
- house/ruler/dispositor links
- planet/angle/asteroid links
- natal configuration links
- proprietary index links
- topic coherence engine
- method-family diversity logic
- counterforce and complexity components
- chapter / trigger / weather separation
- transparent component scoring

Codex file ownership:

- natal promise graph module
- convergence module
- scoring components
- tests

Claude file ownership:

- `phase0/04_convergence_and_candidate_protocol.md`
- graph/coherence contract review

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 7 natal promise graph and cross-clock convergence.

Goal: build the internal graph and convergence engine that prevents forecast evidence from becoming context-free timing noise.

Start with git status. Read phase0/01_predictive_object_schemas.md and phase0/04_convergence_and_candidate_protocol.md. Implement NatalPromiseAnchor construction from houses, rulers, dispositors, natal bodies, angles, asteroids, configurations, proprietary indexes, and topic/domain keys. Then implement cross-clock convergence with method-family diversity, anti-stacking, topic coherence, counterforce, complexity, and component scores.

Do not collapse component scores into one opaque number. Do not expose discrete-event predictions yet. Add tests for anti-stacking, topic coherence, conflicting evidence, and asteroid-specific contribution.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 7 convergence review.

Goal: audit whether the proposed graph and convergence rules can distinguish real independent method convergence from repeated evidence.

Do not edit code. Review anti-stacking, topic coherence, chapter/trigger/weather separation, counterforce, complexity, asteroid specificity, and component-score preservation. Produce exact failure cases Codex must test.
```

## Phase 8 - Discrete Candidate Engine

Purpose:
Add discrete external-event candidate generation as internal R&D, not
client-facing prediction.

Required outcomes:

- `MicroCandidate` object
- trigger-derived candidate windows
- no retrospective date shrinking
- pre-registration timestamp
- candidate calendar
- accepted candidates
- rejected/suppressed candidates
- rejection reasons
- confidence bands
- candidate-specific sidecar export
- outcome ledger linkage

Important width rule:

General EO candidate windows are derived from the natural boundaries of
their anchoring trigger evidence. `predictive_sandbox` may keep a
separate six-calendar-day cap as an internal stress-test rule, but that
cap is not the general system rule.

Codex file ownership:

- candidate assembly module
- rejected-candidate registry
- sidecar candidate export
- validation hooks
- tests

Claude file ownership:

- candidate protocol review
- discrete-prediction claim warnings

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 8 discrete candidate engine.

Goal: implement internal R&D MicroCandidate generation without adding client-facing prediction claims.

Start with git status. Read phase0/04_convergence_and_candidate_protocol.md, phase0/05_validation_protocol.md, and phase0/06_sidecar_and_export_contract.md. Build MicroCandidate generation from chapter support, trigger support, method-family diversity, topic coherence, confidence, counterforce, and trigger-derived window boundaries. Preserve accepted and rejected candidates with reasons. Write candidate-specific sidecar evidence before outcome review.

Do not use post-hoc shrinking. Do not expose candidates in Year Ahead or Personal Forecast prose. Add tests for pre-registration fields, rejected candidates, anti-stacking, trigger-derived width, and outcome-ledger separation.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 8 discrete-candidate protocol review.

Goal: stress-test the MicroCandidate protocol before or alongside Codex implementation.

Do not edit code. Look for loopholes that would allow post-hoc shrinking, vague event domains, hidden outcome knowledge, evidence stacking, unresolved status inflation, or client-facing overclaiming. Produce a failure-mode checklist and acceptance criteria.
```

## Phase 9 - Retrospective Validation Laboratory

Purpose:
Make the system testable against history without storytelling the
answer after the fact.

Required outcomes:

- immutable run packages
- separate outcome ledger
- research status categories
- matched-random baseline
- transit-only baseline
- asteroid-enabled comparison
- returns/profections comparison
- Solar Arc/progression comparison
- full convergence comparison
- per-method ablation
- per-asteroid contribution analysis
- quiet-period and non-hit review

Codex file ownership:

- validation harness
- baseline runner
- outcome ledger schema
- matched-random comparison code
- tests

Claude file ownership:

- validation protocol audit
- historical case review design
- status-category discipline

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 9 retrospective validation laboratory.

Goal: build the validation harness for EO predictive candidates and method layers.

Start with git status. Read phase0/05_validation_protocol.md and phase0/06_sidecar_and_export_contract.md (the sidecar contract). Implement immutable run-package handling, separate outcome-ledger loading, research status categories, matched-random baselines, method ablations, asteroid contribution analysis, and quiet-period/non-hit review support.

Do not use report prose or HTML scraping as validation input. Do not count unresolved as success or failure. Add tests for status categories, matched-random preservation of period/candidate count/window conditions, ablation output, and reproducible run package IDs.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 9 validation design review.

Goal: audit whether the validation laboratory can fairly evaluate candidates without retrofitting success.

Do not edit code. Review outcome categories, matched-random baseline design, quiet-period handling, non-hit treatment, unresolved treatment, research completeness, and ablation requirements. Produce exact review findings and any required acceptance tests.
```

## Safe Parallel Run Matrix

Use this matrix to avoid file collisions.

| Pair | Safe to run simultaneously? | Reason |
| --- | --- | --- |
| Phase 1 Codex + Phase 1 Claude | Yes, if Claude is read-only or writes only a new audit file | Code and claim audit can proceed separately |
| Phase 2 Codex + Phase 2 Claude | Yes, if Claude does not edit `phase0/` while Codex is coding from it | Contract review can be parallel as advisory |
| Phase 3 Codex + Phase 3 Claude | Yes, if Claude only reviews registry and does not edit it | Registry implementation and policy audit can run separately |
| Phase 4 Codex + Phase 4 Claude | Yes, if Claude is review-only | Method code and charter critique are separate |
| Phase 5 Codex + Phase 5 Claude | Yes, if Claude is review-only | Long-clock implementation and fixture critique are separate |
| Phase 6 Codex + Phase 6 Claude | Yes, if Claude is review-only | Time-lord implementation and formula audit are separate |
| Phase 7 Codex + Phase 7 Claude | Caution | Graph contracts and convergence code are tightly coupled |
| Phase 8 Codex + Phase 8 Claude | Caution | Candidate protocol changes can invalidate implementation |
| Phase 9 Codex + Phase 9 Claude | Yes, if Claude only audits validation design | Harness code and design critique can proceed separately |

Unsafe combinations:

- two agents editing `generate.py`
- two agents editing `engine/transit_engine.py`
- two agents editing the same `phase0/` contract
- one agent changing contracts while another implements from those
  contracts
- one agent updating `agents/REVISIONS.md` before another has completed
  its closeout

## Operator Handoff Checklist

Before launching any pair:

1. choose the phase
2. choose one Codex prompt and one Claude Code prompt
3. confirm file ownership
4. tell both agents whether file creation is allowed
5. tell Claude whether it is review-only or may patch docs
6. tell Codex whether it may update `agents/REVISIONS.md`
7. after both finish, run a reconciliation pass before starting the next
   phase

## Reconciliation Prompt

Use this after any simultaneous run:

```text
You are reconciling simultaneous Codex and Claude Code work in C:\entangled_oracle.

Start with git status. Identify every changed file and classify it as Codex-owned, Claude-owned, human-owned, generated artifact, or conflict. Do not revert anything. Compare the actual changes against EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md and the relevant phase acceptance criteria.

Report:
1. what landed
2. what is verified
3. what remains unverified
4. whether any source-of-truth docs need updating
5. whether the next phase is unblocked

Only update agents/REVISIONS.md or agents/PLANNED_UPDATES.md if explicitly asked.
```
