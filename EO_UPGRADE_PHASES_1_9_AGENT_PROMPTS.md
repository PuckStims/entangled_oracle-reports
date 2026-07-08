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

## State as of Phase 6 completion (2026-07-08) — read this before starting Phase 7, 8, or 9

This section exists so any agent — Codex, Claude Code, Antigravity/Gemini,
or a future session of any of these — can pick up Phase 7-9 correctly
without needing prior conversation history. If you are that agent: read
this whole section before touching anything.

**What already exists and works, verified live on real charts, not just
unit-test fixtures (do not rebuild or duplicate any of this):**

| File | What it does | Wired into |
|---|---|---|
| `engine/asteroid_policy.py` | Loads/validates the 34-asteroid registry, exposes source/target/clock eligibility | `engine/predictive_engine.py` |
| `engine/returns.py` | Solar/Lunar/Jupiter/Saturn exact-moment returns | `engine/predictive_engine.py` |
| `engine/profections.py` | Annual whole-sign profection `TimeLordPeriod` records | `engine/predictive_engine.py` |
| `engine/solar_arc.py` | Naibod-adjusted Solar Arc directed contacts | `engine/predictive_engine.py` |
| `engine/progressions.py` | Classical one-day-per-year secondary progressions | `engine/predictive_engine.py` |
| `engine/lots.py` | Lot of Fortune/Spirit/Necessity, sect-aware | `engine/predictive_sidecar.py` (`natal_snapshot.lots`) |
| `engine/zodiacal_releasing.py` | L1-L4 period stack, peaks, LOB, per Fortune and Spirit | `engine/predictive_engine.py` |
| `engine/predictive_engine.py` | Central signal collector; every method above plugs in via a `_collect_*_signals()` function feeding a shared `signals` list, wrapped in try/except so one method's failure never breaks another | — |
| `engine/predictive_sidecar.py` | Writes `.eo_predictive.json` next to every `year_ahead`/`personal_forecast`/`predictive_sandbox` report; this is the ONLY place predictive evidence is currently surfaced. No report template renders any of it. | `generate.py` (post-render hook, non-fatal) |

Every one of `raw_events`' `method_family` values (`TRANSIT`, `PROPRIETARY_TRANSIT`,
`LUNATION`, `RETURN`, `SOLAR_ARC`, `PROGRESSION`, `PROFECTION`, `ZODIACAL_RELEASING`)
is live and produces real events on real charts today. `phase0/` contracts are
at: `01`=`phase0.1.1`, `02`=`phase0.1.1`, `03`=`phase0.1.2`, `06`=`phase0.1.1`
(all per-file versions — check each file's own header, don't assume `phase0.1.0`).

**`ForecastEvent.natal_anchor_ids` is empty on every event emitted so far, on
purpose** (per the Anchor Linkage Deferral note earlier in this document).
Phase 7 is where this gets populated — both prospectively for new events and
retroactively for the roughly 150-200 events already sitting in any given
report's sidecar. Building `NatalPromiseAnchor` without also backfilling
existing events would leave Phase 7 half-finished.

**The one bug pattern that has bitten three phases in a row — check for
this specifically before writing any new natal-data-reading code:**

`engine.natal_engine.generate_payload()`'s real output has NO top-level
`birth_date`, `date`, or `julian_day` keys. Those only exist nested inside
`payload["user_profile"]["local_datetime"]` (ISO string) and
`payload["user_profile"]["julian_day"]` (float). Every one of `returns.py`,
`solar_arc.py`, and `progressions.py` originally read the wrong top-level
keys, passed their own unit tests (because the test fixtures happened to
include a convenience top-level key the real engine never produces), and
silently returned zero results on every real chart — caught only by
generating an actual report and inspecting the sidecar, not by running
`unittest`. **Any new code in Phase 7, 8, or 9 that reads birth date,
Julian day, or other natal-payload fields must check `user_profile` first,
and must be verified against a real `generate_payload()` output — not just
a hand-built test fixture — before being considered done.**

**The verification bar for every phase, restated because it is the single
most load-bearing habit in this whole program:** running `unittest` and
seeing `OK` is necessary but never sufficient. Before calling any phase
done: generate a real report via `generate.py <report_type> --name ... --date
... --time ... --location ... --report-date ... --output-dir tmp/... --no-browser`,
open the resulting `.eo_predictive.json`, and confirm the new phase's
output is actually present and looks correct — not just that no exception
was thrown. Every real bug found across Phases 2-6 was caught this way,
none by unit tests alone. Clean up `tmp/` output afterward (it's
gitignored, but keep the working tree tidy).

**Explicit anti-drift boundaries — read these even if you are confident
you already know the scope. They exist because a natural, well-intentioned
impulse to make the system "more complete" or "more impressive" has a
specific, named failure mode here, and this document is written to be
followed literally, not spiritually:**

1. **No client-facing report changes in Phases 7, 8, or 9.** Not a new
   template section, not a "just a small mention" in Year Ahead prose, not
   a teaser in the sandbox narrative preview beyond what already exists.
   The sidecar is the only surface. This is not a suggestion to be
   balanced against other goals — it is a hard boundary. If a phase's
   `Required outcomes` list doesn't say "template" or "prose," do not add
   template or prose changes, no matter how contained or "obviously fine"
   they seem in the moment.
2. **No new astronomical or interpretive methods beyond what each phase's
   `Required outcomes` list names.** Do not add harmonics, midpoints,
   antiscia, additional lots beyond Fortune/Spirit/Necessity, additional
   time-lord systems (Firdaria etc. — explicitly reserved for post-Phase-6
   per `phase0/03_method_charters.md` C6), or any other technique that
   "would fit naturally" alongside what's being built. If it's not listed,
   it's out of scope for this phase, full stop — propose it separately
   afterward if it seems valuable, do not fold it in.
3. **No score simplification.** Every component score (topic_coherence,
   method_family_diversity, counterforce, complexity, confidence, etc.)
   must remain individually visible in the output. Do not collapse
   multiple components into one summary number without also preserving
   the components. A single "star rating" or "confidence: high/medium/low"
   replacing the real component breakdown is exactly the kind of
   simplification this program was built to prevent.
4. **No fabricated example data presented as if real**, especially in
   Phase 9. The outcome ledger and matched-random baseline are
   infrastructure to be built — they do not yet have real historical
   outcome data in them, because no real historical review has happened.
   Do not populate test fixtures with data styled to look like a genuine
   validated prediction success ("candidate X correctly predicted event
   Y") unless that is explicitly labeled as synthetic test fixture data,
   clearly and repeatedly, everywhere it appears (variable names, docstrings,
   comments). A stray plausible-looking "hit" in a fixture can get quoted
   later as if it were a real result — guard against that specifically.
5. **`predictive_sandbox`'s six-calendar-day research cap is sandbox-only.**
   This was a real correction made earlier in this program (an operator
   caught it, not an agent) — the general system's `MicroCandidate` window
   width is trigger-derived, with no fixed maximum, per
   `phase0/04_convergence_and_candidate_protocol.md` section 4.2. Do not
   reintroduce a fixed day-count cap for the general system in Phase 8.
6. **When in doubt about scope, do less, not more, and say so explicitly**
   in the phase's closeout note (`agents/REVISIONS.md`) rather than silently
   filling a perceived gap. Every phase in this program so far has been a
   real, working foundation — not a finished, polished system — and that
   is intentional, not a shortcoming to compensate for.

---

## Phase 7 - Natal Promise Graph and Cross-Clock Convergence

Purpose:
Build the graph that explains why a forecast event matters for a
specific chart, then compose independent evidence without stacking.

Required outcomes:

- `NatalPromiseAnchor` construction (per `phase0/01_predictive_object_schemas.md` §1) from houses, house rulers, dispositors, natal planets, angles, all 34 asteroids (via `engine/asteroid_policy.py`), named configurations (`formulas/standard/named_configurations.py`), proprietary index driver links, and topic/domain keys (drawn only from the reserved namespace in `phase0/01_predictive_object_schemas.md` §7 — do not invent new topic or domain keys without a version bump and an operator note)
- an anchor-matcher that populates `ForecastEvent.natal_anchor_ids` and `PredictiveSignal.natal_anchor_ids` — **both retroactively for every event already in a report's sidecar and prospectively for new events**, matching by `source_body`/`target_body`/`method_family` against the anchors built for that chart
- topic coherence engine per `phase0/04_convergence_and_candidate_protocol.md` §3 (the seven coherence-graph rules, computed exactly as chartered, not approximated)
- method-family diversity logic using the composite-dedup rule in §2.2 (`transit_family`/`proprietary_transit_family` collapse on shared source+target; every other independence group counts independently)
- counterforce and complexity components per §6, each visible as its own field, not folded into one score
- `ChapterState` construction (per `phase0/01_predictive_object_schemas.md` §4) via the chapter builder order in `phase0/04_convergence_and_candidate_protocol.md` §8.1 — this is also where Return/Solar-Arc/Progression/ZR "chapter"-role `ForecastEvent`s finally get promoted into real `ChapterState` objects with the already-reserved `chapter_kind` values (`return_year`, `solar_arc_chapter`, `progressed_lunation_phase`, `zr_period`, `sustained_transit_chapter`, `long_transit_cycle`)
- transparent component scoring throughout — see anti-drift rule 3 above

Explicit non-goals for this phase specifically (in addition to the general anti-drift rules above): do not build `MicroCandidate` yet (that's Phase 8); do not build the outcome ledger (Phase 9); do not add a new clock family.

Codex file ownership:

- `engine/natal_promise.py` (new) — anchor construction and the anchor-matcher
- `engine/convergence.py` (new) — chapter builder, coherence graph, method-diversity/anti-stacking logic
- extends `engine/predictive_engine.py` (anchor-matching pass after signal collection) and `engine/predictive_sidecar.py` (emit `natal_promise_anchors` and `chapters` arrays, currently always empty per `phase0/06_sidecar_and_export_contract.md` §2.5/§2.10)
- tests

Claude file ownership:

- `phase0/04_convergence_and_candidate_protocol.md`
- graph/coherence contract review

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 7 natal promise graph and cross-clock convergence.

Before anything else, read the "State as of Phase 6 completion" section near the top of this file (EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md) in full. It names a real bug pattern that has hit three phases in a row and a verification requirement that is not optional.

Goal: build the internal graph and convergence engine that prevents forecast evidence from becoming context-free timing noise.

Start with git status. Read phase0/01_predictive_object_schemas.md sections 1 and 4, and phase0/04_convergence_and_candidate_protocol.md in full. Implement NatalPromiseAnchor construction from houses, rulers, dispositors, natal bodies, angles, all 34 asteroids, named configurations, proprietary indexes, and topic/domain keys drawn only from the reserved namespace. Build the anchor-matcher and use it to populate natal_anchor_ids on every ForecastEvent and PredictiveSignal already being produced by the six existing method families -- this must work retroactively on events already flowing through the pipeline, not just prospectively. Then implement the chapter builder (promoting existing chapter-role events into real ChapterState objects) and cross-clock convergence: method-family diversity via the composite-dedup rule, topic coherence via the seven coherence-graph rules, counterforce, and complexity.

Do not collapse component scores into one opaque number. Do not build MicroCandidate or the outcome ledger -- those are Phase 8 and 9. Do not add a new clock family. Do not touch any report template or add any client-facing prose. Add tests for anti-stacking, topic coherence, conflicting evidence, and asteroid-specific contribution. Before calling this done, generate a real report and confirm natal_promise_anchors and chapters are non-empty in the resulting .eo_predictive.json, and that existing events (returns, Solar Arc, progressions, ZR, transits) now carry populated natal_anchor_ids.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 7 convergence review.

Read the "State as of Phase 6 completion" section near the top of EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md first.

Goal: audit whether the proposed graph and convergence rules can distinguish real independent method convergence from repeated evidence.

Do not edit code. Review anti-stacking, topic coherence, chapter/trigger/weather separation, counterforce, complexity, asteroid specificity, and component-score preservation. Produce exact failure cases Codex must test.
```

## Phase 8 - Discrete Candidate Engine

Purpose:
Add discrete external-event candidate generation as internal R&D, not
client-facing prediction.

Required outcomes:

- `MicroCandidate` object per `phase0/01_predictive_object_schemas.md` §5
- trigger-derived candidate windows — **no fixed maximum width for the general system; see anti-drift rule 5 above and `phase0/04_convergence_and_candidate_protocol.md` §4.2 for the exact derivation rule**
- no retrospective date shrinking (§4.3 — `window_days` is fixed at emission, permanently)
- pre-registration timestamp (`pre_registered_at`, set once, never overwritten)
- candidate calendar assembly per §8.2 (candidate builder order: iterate trigger-signal peaks, scan a discovery buffer for coherent clustering, match anchors/chapter-support/trigger-support, compute component scores, check the ten hard requirements in §4.1, emit or reject)
- accepted candidates
- rejected/suppressed candidates with the locked `filter_reason` enum from `phase0/06_sidecar_and_export_contract.md` §2.12 (do not invent new reason strings outside that enum without a version bump)
- confidence bands
- candidate-specific sidecar export (`candidates` and `rejected_candidates` arrays, currently always empty)
- outcome ledger linkage (`report_run_id`, `candidate_id` — the ledger itself is Phase 9's job; Phase 8 only needs to emit candidates with stable, referenceable IDs)

Codex file ownership:

- `engine/candidates.py` (new) — candidate assembly, rejection logging
- extends `engine/predictive_sidecar.py` (emit `candidates` and `rejected_candidates`)
- tests

Claude file ownership:

- candidate protocol review
- discrete-prediction claim warnings

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 8 discrete candidate engine.

Before anything else, read the "State as of Phase 6 completion" section near the top of this file in full, especially anti-drift rule 5 about the six-day cap.

Goal: implement internal R&D MicroCandidate generation without adding client-facing prediction claims.

Start with git status. Read phase0/04_convergence_and_candidate_protocol.md in full, phase0/05_validation_protocol.md, and phase0/06_sidecar_and_export_contract.md sections 2.11 and 2.12. This phase depends on Phase 7's NatalPromiseAnchor and ChapterState objects already existing and being populated -- confirm that before starting; if Phase 7 is not actually done (not just planned), stop and say so rather than building Phase 8 on an assumed foundation.

Build MicroCandidate generation from chapter support, trigger support, method-family diversity, topic coherence, confidence, counterforce, and trigger-derived window boundaries per section 4.2 -- the window is the union of the natural span of qualifying trigger signals (temporal_precision in instant/day only), never a fixed cap. Preserve accepted and rejected candidates with reasons from the locked filter_reason enum. Write candidate-specific sidecar evidence before any outcome review exists.

Do not use post-hoc shrinking. Do not expose candidates in Year Ahead or Personal Forecast prose or any template. Do not introduce any fixed maximum window width for the general system. Add tests for pre-registration fields, rejected candidates, anti-stacking, trigger-derived width (including a test that a wide-window trigger produces a wide candidate, proving there is no hidden cap), and outcome-ledger ID linkage. Before calling this done, generate a real report with a chart/window likely to produce candidates and confirm the sidecar's candidates and rejected_candidates arrays are populated and inspectable.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 8 discrete-candidate protocol review.

Read the "State as of Phase 6 completion" section near the top of EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md first.

Goal: stress-test the MicroCandidate protocol before or alongside Codex implementation.

Do not edit code. Look for loopholes that would allow post-hoc shrinking, vague event domains, hidden outcome knowledge, evidence stacking, unresolved status inflation, a reintroduced fixed window cap, or client-facing overclaiming. Produce a failure-mode checklist and acceptance criteria.
```

## Phase 9 - Retrospective Validation Laboratory

Purpose:
Make the system testable against history without storytelling the
answer after the fact.

Required outcomes:

- immutable run packages (the sidecar itself, per `phase0/06_sidecar_and_export_contract.md` §4 — write-once per run, re-running produces a new sidecar rather than mutating the old one)
- separate outcome ledger per §3 (`<report_id>.eo_outcomes.json`, written by reviewer tooling, never by the generation engine)
- research status categories — **exactly** the five locked in `phase0/05_validation_protocol.md`: `supported_hit`, `supported_non_hit`, `unresolved`, `research_incomplete`, `excluded_by_protocol`. Do not add or rename categories.
- matched-random baseline generation
- transit-only baseline, asteroid-enabled comparison, returns/profections comparison, Solar Arc/progression comparison, full convergence comparison — these are **ablation runs**: the same chart/window run once with a method family disabled and once with it enabled, comparing candidate output, not runs against fabricated "ground truth"
- per-method ablation, per-asteroid contribution analysis
- quiet-period and non-hit review support — a report window producing zero candidates is a valid, expected, and important outcome to preserve and review, not a failure to hide

Codex file ownership:

- `engine/validation_harness.py` (new) — outcome ledger read/write, matched-random baseline generation, ablation runner
- tests

Claude file ownership:

- validation protocol audit
- historical case review design
- status-category discipline

Codex prompt:

```text
You are Codex working in C:\entangled_oracle on Phase 9 retrospective validation laboratory.

Before anything else, read the "State as of Phase 6 completion" section near the top of this file in full, especially anti-drift rule 4 about fabricated example data.

Goal: build the validation harness for EO predictive candidates and method layers. This phase builds infrastructure for validation -- it does not perform an actual historical validation study, because Phase 8's candidates are brand new and no real outcome review has happened yet. Do not create fixture data styled to look like a genuine validated hit; if you need example data for a test, label it as synthetic everywhere it appears (variable name, docstring, comment) and keep it obviously schematic (e.g. round numbers, placeholder names) rather than plausible-looking.

Start with git status. Read phase0/05_validation_protocol.md in full and phase0/06_sidecar_and_export_contract.md section 3 (the outcome ledger). This phase depends on Phase 8's MicroCandidate objects already existing -- confirm that before starting; if Phase 8 is not actually done, stop and say so.

Implement immutable run-package handling (the sidecar is already write-once; confirm and test this rather than rebuilding it), separate outcome-ledger read/write matching the exact schema in section 3, the five locked research status categories exactly as named, matched-random baseline generation that preserves candidate count/window-width conditions from the real run, per-method ablation (rerun with a method family's signals excluded, compare), and per-asteroid contribution analysis.

Do not use report prose or HTML scraping as validation input -- read from the sidecar's structured data only. Do not count unresolved as success or failure in any aggregate metric. Do not add a sixth status category. Add tests for status categories, matched-random preservation of period/candidate count/window conditions, ablation output, and reproducible run package IDs.
```

Claude Code prompt:

```text
You are Claude Code working in C:\entangled_oracle on Phase 9 validation design review.

Read the "State as of Phase 6 completion" section near the top of EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md first.

Goal: audit whether the validation laboratory can fairly evaluate candidates without retrofitting success.

Do not edit code. Review outcome categories, matched-random baseline design, quiet-period handling, non-hit treatment, unresolved treatment, research completeness, and ablation requirements. Specifically check for any fixture or example data that reads as a real historical result rather than clearly-labeled synthetic test data. Produce exact review findings and any required acceptance tests.
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
