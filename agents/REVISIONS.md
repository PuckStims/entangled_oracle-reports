# Revisions

A dated log of meaningful changes made to this codebase by AI sessions.
Newest entry on top. See `agents/README.md` for the convention.

---

## 2026-07-10 - Professional-grade upgrade directive added (Codex / GPT-5)

**Context:** the operator asked for the speculative formula/computation
upgrade plan to be fleshed out as durable directives for future agents,
with professional controls, specialist branches, and locational astrology
kept optional for now, and synastry acknowledged as necessary but
separately daunting.

**What changed:**

- Added `agents/PROFESSIONAL_GRADE_UPGRADE_DIRECTIVES.md`, a tiered
  future-agent handoff covering audit bedrock, core forecast computation
  hardening, advanced-method internal promotion, formula intelligence,
  synthesis backend, report-surface promotion, synastry substrate, and
  optional professional expansion.
- Expanded that directive with a formal builder/review-crew model:
  Gemini/Antigravity as candidate-construction engine, Codex/ChatGPT and
  Claude Code as alignment/detail authority.
- Added Gemini-safe global guardrails and per-tier "allowed / do not
  access / review required" boundaries so future high-throughput build
  runs can be contained without flattening EO distinctions.
- Added `agents/HIGH_THROUGHPUT_AGENT_PROMPTS.md` with reusable startup
  prompts for Gemini/Antigravity and Claude Code, including mandatory
  read order, file-seam placeholders, handoff requirements, and review
  priorities for the builder-plus-review-crew model.
- Added a pointer at the top of `agents/PLANNED_UPDATES.md` so future
  sessions check the directive before launching large formula,
  computation, synthesis, or synastry upgrades.

**Verification:** documentation-only change. No source code, templates,
  content blocks, generated outputs, or tests were changed.

**Open, not implemented here:** the directive recommends the first real
  project as a Forecast Computation Ledger plus Canonical Forecast Event
  Schema/adapters, but that work has not started.

---

## 2026-07-08 - Progression/solar-arc scoring gap fixed: real scores replace flat 0.0 (Claude / Sonnet 5)

**Context:** surfaced during live-review of the Year Ahead texture-wiring
pass below — every `year_texture_progressions`/`year_texture_solar_arc`
event came back with `score` (`reader_facing_activity_score` /
`combined_intensity_score`) hard-stuck at `0.0`, regardless of real
exactness or natal relevance. Root cause: `engine/progressions.py` and
`engine/solar_arc.py` already compute a concentration-like value
(`trigger_strength`) per event, but never exposed it under any of the
field names `enrich_forecast_event()`'s fallback chain
(`concentration_score` -> `combined_intensity_score` -> `raw_score`)
actually checks — so `concentration` silently defaulted to `0.0`. On top
of that, `formulas/standard/forecast_activation.py`'s
`_reader_activity_score()` and `EVENT_TYPE_BASELINES` had no case for
`"progression"`/`"solar_arc"` event types at all, falling back to bare
`_clamp(concentration)` with no natal-relevance/theme weighting even
if concentration had been populated.

**What changed:**

- `engine/progressions.py::_progression_contact_event()` and
  `engine/solar_arc.py::_solar_arc_event()` — added a `"raw_score"` key
  equal to the already-computed `trigger_strength` value. (Confirmed the
  other progression-event constructors — `_progression_ingress_event()`,
  `_progressed_lunation_event()` — are `clock_role: "trigger"`, not
  `"chapter"`, so they never reach the texture path and don't need this.)
- `formulas/standard/forecast_activation.py` — added `"progression": 0.20`
  and `"solar_arc": 0.20` to `EVENT_TYPE_BASELINES` (between ingress's
  0.14 and eclipse/station's 0.30), and a new `_reader_activity_score()`
  branch for both event types: `concentration*0.22 + exactness*0.08 +
  natal_relevance*0.40 + theme_convergence*0.30`, capped at `high=0.55`
  — weighted toward natal relevance/theme over raw concentration (these
  are season-scale ambient texture per the method charter, not
  point-forecast drivers), and capped below every point-event type's
  ceiling so texture can never outrank the methods it's meant to
  contextualize.

**Verification:** re-ran against the same real chart used in the texture
pass below (1990-06-15, Peoria, IL). `year_texture_progressions` (208
events): scores now range 0.123-0.55, zero events stuck at 0.0.
`year_texture_solar_arc` (14 events): 0.028-0.55, same. As an unplanned
bonus, the already-shipped Personal Forecast Moon-progression events (30
per this chart) also went from all-zero to a real 0.4093-0.55 range, with
no separate code change needed since they share the same enrichment path.
Full suite: 226 passed, no regressions.

**Open, not decided here:** this gives the 208-event volume question from
the texture pass below a real axis to sort/trim by, but doesn't decide
anything about a cap itself — that's still a separate call for whenever
volume-limiting is actually taken up.

---

## 2026-07-08 - Year Ahead progressions/solar-arc "texture" wired backend-only (Gemini, live-verified by Claude / Sonnet 5)

**Context:** the other half of Phase D — the progressed-Moon half landed
same-day in the entry below. Operator decision: Year Ahead's 12-month
scope gets progression and solar-arc events too, framed as ambient
developmental "texture" (season-scale terrain/mood), not point-forecast
claims. This pass was explicitly scoped backend-only: wire the data,
verify it against real charts, no templates or new prose yet — get real
data to react to before anyone writes client-facing language for it.
Implemented by Gemini from a written brief (Codex was unavailable this
session); independently re-reviewed and re-verified line-by-line by
Claude before landing, per the operator's "rigorous post-review" call
for non-Claude-authored changes.

**What changed:**

- `engine/transit_engine.py`: `compute_year_ahead_events()` gained an
  `include_year_texture: bool = False` parameter (default preserves
  existing behavior for every current caller). When `True`, it calls
  `scan_progression_events()` and filters to `clock_role == "chapter"`
  via a new `_filter_texture_progression_events()` helper (the
  complement of the existing Moon-only `_filter_moon_progression_events()`),
  and calls `scan_solar_arc_events()` directly (no filtering needed —
  every event it emits is already `"chapter"`-tagged). Both pass through
  the existing `link_related_forecast_events(..., progression_events=...,
  solar_arc_events=...)` scaffolding for standard enrichment, then are
  split back out (season-scale windows are deliberately kept out of
  `all_events`'s chronological sort — mixing months-wide windows into a
  day-scale transit list would read as broken ordering, not richer
  content). Added `"year_texture_progressions"` and
  `"year_texture_solar_arc"` keys to the return dict.
- `generate.py`: `_build_year_ahead_context()` now passes
  `include_year_texture=True` and pulls both new keys into the report
  context dict for inspection only — neither is wired into any template,
  content-pack block, or rendered HTML section.

**Verification:** re-ran independently (not just trusting the reported
numbers) against the same real natal chart (1990-06-15, Peoria, IL) —
confirmed 208 `year_texture_progressions` and 14 `year_texture_solar_arc`
events over the 12-month window, with genuine season-scale spans (e.g.
Sun Conj ASC: entry 2026-05-09 -> peak 2026-07-08 -> leave 2026-09-06;
Mars Opp Pluto solar arc: entry 2026-04-09 -> peak 2026-07-08 -> leave
2026-10-06), matching the design assumption these run 9mo-2yr, not days.
Confirmed the `False`-default path is behavior-identical to pre-change
code. Grepped `products/`, `selectors/`, `formulas/` for `year_texture` —
zero hits, confirming no template/content wiring happened. Full suite:
325 passed / 19 failed, all 19 confirmed pre-existing on clean `master`
via stash-and-rerun (5 known-broken test-module imports already logged
below, offline-geocoding-data failures, and quarantine/predictive-sandbox
failures) — zero regressions from this change.

**Known gap surfaced, not fixed this pass:** every progression/solar-arc
event's `score` (`reader_facing_activity_score` / `combined_intensity_score`)
comes out `0.0` regardless of real exactness or natal relevance.
`_reader_activity_score()` and `EVENT_TYPE_BASELINES` in
`formulas/standard/forecast_activation.py` have no case for
`"progression"`/`"solar_arc"` event types, so they fall back to
`_clamp(concentration)`, and neither scanner emits a `concentration_score`.
This is pre-existing (identical for the already-shipped Moon-progression
events in Personal Forecast, not introduced here) and out of scope for
this backend-wiring pass, but it means `score` cannot be used as the axis
for any future volume-limiting decision on the 208-event count below
until this scoring gap is addressed.

**Open, not decided here:** 208 `year_texture_progressions` in a single
12-month window is a real density finding, reported raw and unfiltered
per the operator's explicit instruction not to invent a cap. Whether/how
to bound this (and by what real astrological convention, not a picked
number) is a separate decision for a future session.

---

## 2026-07-08 - Progressed Moon wired into Personal Forecast, gated to Moon only (Claude / Sonnet 5)

**Context:** operator decision on the standard-forecasting phased map's
Phase D: directed-timeline content (progressions/solar arc) generally
runs too slow for Personal Forecast's 90-day window (solar arc and
progressed Sun/Mercury/Venus contacts stay "current" for 9 months to 2
years), but progressed Moon specifically is fast enough (~2-4 week orb
window) to fit. Operator confirmed: include progressed Moon in Personal
Forecast; everything else in the progression family stays out for now.
The broader Year Ahead progressions/solar-arc "texture" placement (the
rest of Phase D) is a separate, still-open decision — not resolved by
this change.

**What changed:**

- `engine/transit_engine.py`: `compute_year_ahead_events()` gained an
  `include_moon_progressions: bool = False` parameter (default preserves
  existing behavior for every current caller). When `True`, it calls
  `engine.progressions.scan_progression_events()` and filters the result
  through a new `_filter_moon_progression_events()` helper, which keeps
  only Moon-involved contacts/ingresses (`transit_planet == "Moon"`, or
  Moon-involved `progressed_to_progressed`/`transit_to_progressed`
  pairs) and explicitly excludes `progression_lunation_phase` — the
  progressed Sun-Moon phase cycle, a much slower (~29.5-year) phenomenon
  that happens to also carry `transit_planet == "Moon"` and would
  otherwise slip through a naive "Moon" filter. Filtered events pass
  through `link_related_forecast_events(..., progression_events=...)`
  (already-existing scaffolding, previously unused) and join `all_events`.
  Added a `"progressions"` key to the return dict.
- `generate.py`: `_build_personal_forecast_context()` now passes
  `include_moon_progressions=True`. Year Ahead's context builder is
  untouched and still gets zero progression events by default.

**Verification:** confirmed Year Ahead's progression count is exactly 0
(unaffected) while Personal Forecast's 90-day window picks up ~30+ real
Moon-involved events per chart, spanning all three relevant method
variants, with genuine ~28-day contact windows (matching the code's
existing ±14-day Moon-specific window) safely inside the 90-day scope.
Full suite green (226 passed); both Year Ahead and Personal Forecast
reports generated live with no errors.

---

## 2026-07-08 - Annual Profections wired into Year Ahead as a transit weight modifier (Claude / Sonnet 5)

**Context:** `phase0/03_method_charters.md` C4 §7 specifies annual profection
as "a weight modifier for its year. It elevates signals whose anchors
involve the time lord, its ruled houses, or its natal aspects... It does
not by itself justify a MicroCandidate." This had never been executed —
`engine/profections.py` computed correct `TimeLordPeriod` records but
nothing in `generate.py`'s live path ever called it.

**What changed:**

- `formulas/standard/forecast_activation.py`: added `_covering_period()`
  and `_parse_period_datetime()` helpers, and a new block in
  `link_related_forecast_events()` that, for each transit event whose
  `peak_datetime` falls inside an active `annual_profection` period,
  checks whether the transiting body is the period's time lord, aspects
  the time lord, or activates the profected house — and if so,
  multiplies that event's `structural_importance` and `theme_convergence`
  by the period's own already-declared `weight_modifier` (currently
  `1.12`, computed in `engine/profections.py`, not invented here). Tags
  the event with `annual_profection_linkage` naming which condition(s)
  matched. Deterministic, bounded (`_clamp`'d), fully explainable — no
  statistical synthesis, nothing resembling the quarantined convergence
  apparatus.
- `engine/transit_engine.py`: `compute_year_ahead_events()` now calls
  `annual_profection_periods()` and passes the result to
  `link_related_forecast_events(..., time_lord_periods=profection_periods)`
  — using the correct existing parameter name this time (an earlier,
  reverted attempt crashed by passing `profection_events=`/`zr_events=`
  keywords that didn't exist on the function). Profection periods are
  *not* added to `all_events` — they aren't point events and don't carry
  `peak_datetime`, so forcing them into that flat, sorted list would
  reproduce the same crash. Per the charter's "does not... produce client
  prose" instruction, nothing new is surfaced to report templates yet;
  this only changes the scores transits already carry.

**Verification:** confirmed the multiplier applies exactly (`×1.120`,
matching the period's declared `weight_modifier`) only to matching
transits, leaves non-matching transits untouched, and generated a live
Year Ahead report end-to-end with no crash. Full suite green (226 passed).

---

## 2026-07-08 - Zodiacal Releasing Loosing of the Bond fix; progressed-angle Swiss Ephemeris precision; progression orb correction (Codex / GPT-5, Claude / Sonnet 5)

**Context:** A prior audit (Codex) found `engine/zodiacal_releasing.py`'s
Loosing of the Bond (LOB) was not merely rare but structurally impossible:
`is_loosing_of_the_bond` was hardcoded `False`, and the proportional
sub-period construction always summed exactly to the parent's duration by
construction, leaving no residue for LOB to ever key off of. This
contradicted the charter's own definition (`phase0/03_method_charters.md`
C5b §1), which describes LOB as a real, structural sign-sequence event.

**What changed (Codex):**

- `engine/zodiacal_releasing.py`: replaced proportional sub-period
  construction with the classical mechanism — each level (L2/L3/L4) reads
  the same fixed Valens sign-year values used for L1, but in the next
  smaller time unit (months at L2, days at L3, hours at L4). Sub-periods
  accumulate in zodiacal order, wrapping past Pisces as needed, until the
  enclosing parent's actual duration is exhausted. When a full 12-sign
  pass completes with parent duration still remaining, the next sub-period
  jumps to the sign opposite the one that just completed the lap, marked
  `is_loosing_of_the_bond = True`, emitting a new `zr_lob` event variant.
- `phase0/03_method_charters.md` C5b §1: reworded the L2-L4 and LOB
  description to state the fixed-value/next-smaller-unit/wrap-and-jump
  mechanism explicitly, since the prior "proportional to the L1 sign's
  total years" wording had the same latent ambiguity as the bug itself.
- `tests/test_phase6_lots_zodiacal_releasing.py`: added two hand-computed
  fixtures independently deriving the expected LOB moment from first
  principles (a Cancer L1 period's L2 cycle completes its 12-sign lap at
  `211/12` years in, landing on Gemini as the 12th sign; LOB fires into
  Gemini's opposite, Sagittarius) rather than deriving the expectation
  from the function under test.
- Also changed `report_surface_visibility` on ZR period/event records from
  `["internal_rd", "predictive_sandbox"]` to
  `["internal_rd", "engineering_diagnostic"]` — `predictive_sandbox` no
  longer exists as a live report surface after the quarantine above.

**What changed (Claude, verification pass):** independently re-derived the
LOB boundary math and sign-opposition logic rather than trusting the
summary; ran the full recursion (`_collect_periods` → `_subdivide`) to
confirm `level` is passed as the child's own level at every recursion
depth (no off-by-one in which divisor applies); ran the fixture and full
suite. Found and fixed one unrelated collision: the same test file still
imported `engine.predictive_sidecar` (quarantined earlier the same day)
via a standalone `TestSidecarIntegration.test_natal_snapshot_carries_lots`
test that had nothing to do with Zodiacal Releasing and was already
duplicated by the quarantined `test_phase2_predictive_sidecar.py` — removed
that one test class and the broken import; did not touch anything else in
the file Codex had just added.

**Also this session (Claude, Phase B — progressions):**

- `engine/progressions.py`: progressed angles (Ascendant/Midheaven/IC/
  Descendant) previously used a flat `natal_longitude + age_years`
  approximation (~1°/year) for both position and applying/separating
  speed. Replaced with genuine `swe.houses()` evaluated at the progressed
  Julian day and natal birth coordinates, mirroring the exact house-angle
  calculation and Porphyry polar fallback already used in
  `engine/natal_engine.py`. Confirmed non-uniform, latitude-dependent
  motion against a real chart (Ascendant/Descendant ≈1.72°/day vs.
  Midheaven/IC ≈0.91°/day for the same chart) rather than a flat constant.
- Progressed-to-progressed and transit-to-progressed orb limits: an
  earlier pass had scaled each body's *natal* orb by an arbitrary `× 0.1`
  factor with no basis in actual astrological convention. Per an explicit
  operator rule (no EO-internal fixed number overrides real astrological
  research for prediction functions), replaced with the existing flat
  `CONTACT_ORB = 1.0` / `ANGLE_ORB = 0.5` ceiling already used for
  progressed-to-natal contacts in the same module — independently
  corroborated by external research converging on "very tight, roughly
  ≤1°, tighter still for transit-to-progressed" rather than picking either
  the old ad hoc scaling or the charter's number by default.

**Verification:** full suite green (226 passed) after all of the above,
including Codex's two new LOB fixtures and a live, non-mocked
`scan_progression_events` run producing sensible event counts across all
five method variants.

**Context:** The operator was reviewing a fresh "Professional Forecasting
Domain Audit" (traditional-technique completeness) alongside this repo's
own Phase 0-9b predictive upgrade program when a deeper problem surfaced:
the `predictive_sandbox` report type has no calculation logic of its own
(confirmed — `generate.py`'s `_build_predictive_sandbox_context()` only
reformats already-computed data), which raised the question of what the
Phase 0-9b engine work was actually built on. The operator supplied two
source specifications for direct comparison:

- `Entangled_Oracle_Proprietary_Interpretive_Algorithms_Spec_v0.2` — the
  real, synced, operational specification for
  `formulas/proprietary_indexes.py` (KVQ, MKI, RWI, DFIS, Catalyst, NGE,
  AHL + legacy MCQ/SIREN/MAGNETIC bridge). Confirmed acceptable as a
  system reference.
- `Entangled_Oracle_Testable_Predictive_Formulas_Experimental_v0.1` — the
  actual design source for `engine/predictive_engine.py` and
  `engine/convergence.py`. This document's own header states "Document
  status: Experimental source-of-truth design specification" and
  "Implementation status: Pre-implementation; fixture validation required
  before production deployment." Confirmed **not** acceptable as a system
  reference by the operator.

Cross-referencing the two documents against the live code confirmed the
Testable v0.1 spec's sections map directly onto what Phases 2-9b built and
shipped: §4 (trigger strength) → predictive_engine.py signal
normalization; §5 (Chorus Intensity, Natal Index Echo) → target-relevance
scoring; §6 (window detection, gradient, activation episode ledger) →
`_detect_windows()`'s FSM/lifecycle/memory; §7-9 (semantic topology,
coalition/counterforce, operation ontology, cluster relation matrix) →
`convergence.py`'s coherence/polarity/coalition/counterforce/complexity
math. Phase 9b (2026-07-08, same day) had wired this directly into real
Year Ahead / Personal Forecast client output under hedged "research
signal" framing — an experimental, pre-implementation statistical
invention, not an established astrological technique, reaching real
report output. Operator's own framing: "if an astrologist read my files
currently they'd think i literally hallucinated all that then treated it
as fact."

**Operator decision:** quarantine the whole apparatus — not delete, not
partially rewire to "keep convergence active" (an intermediate plan
floated mid-session and explicitly retracted once it became clear
`convergence.py`'s own semantic-topology logic is itself Testable v0.1
content, not merely downstream of predictive_engine.py).

**What changed (this session, Claude / Sonnet 5):**

- Moved (via `git mv`, history preserved) into
  `quarantine/predictive_testable_v0_1/`: `engine/predictive_engine.py`,
  `engine/convergence.py`, `engine/candidates.py`,
  `engine/predictive_sidecar.py`, the entire `products/predictive_sandbox/`
  product (templates + JSON block library), `tools/extract_sandbox_ledger.py`,
  and the Phase 2/3/7/8/9/9b test files
  (`test_predictive_engine.py`, `test_phase2_predictive_sidecar.py`,
  `test_phase3_asteroid_predictive_activation.py`,
  `test_phase7_natal_promise_convergence.py`, `test_phase8_candidates.py`,
  `test_phase9_validation_harness.py`, `test_phase9b_report_surface.py`).
  See `quarantine/predictive_testable_v0_1/README.md` for the full
  rationale and inventory.
- Moved (untracked, plain `mv`) previously-rendered `predictive_sandbox`
  HTML/manifest samples, `.eo_predictive.json` sidecar exports, and
  `tmp/phase*_real/` scratch runs into the same quarantine directory.
- `generate.py`: removed the predictive-engine/sidecar computation block,
  the `predictive_sandbox` report-type dispatch branch and CLI choice, the
  sandbox-specific template error page, and `_build_predictive_report_
  surface()` / `_build_predictive_sandbox_context()` plus their private
  helpers. `variables["predictive_results"]` / `["predictive_sidecar"]`
  are kept present but always empty so any stray template reference
  degrades to blank instead of a Jinja `UndefinedError`.
- `config.py`, `product_versions.py`: removed `predictive_sandbox`
  report-type registration.
- `products/year_ahead/templates/active/year_ahead.html`,
  `products/personal_forecast/templates/personal_forecast.html`: removed
  the Phase 9b "Predictive / experimental layer" sections outright
  (they were already dead once `predictive_report_surface.enabled` was
  hardcoded `False`, but left-in disallowed-content markup was itself
  part of the problem being fixed).
- `formulas/governance_registry.py`, `formulas/established_niche.py`:
  removed `predictive_sandbox` from `eligible_report_types` tuples and the
  report-profile map (vestigial once the report type no longer exists).
- `engine/returns.py`, `engine/profections.py`, `engine/solar_arc.py`,
  `engine/progressions.py`, `engine/zodiacal_releasing.py`: renamed the
  `report_surface_visibility` tag value `"predictive_sandbox"` →
  `"engineering_diagnostic"` (their only consumer, the now-quarantined
  sidecar, is gone; the old name pointed at a product that no longer
  exists). Updated the two Phase 4/5/6 test files' matching assertions.
  Also removed the one integration test method in each of
  `test_phase4_returns_profections.py` and
  `test_phase5_solar_arc_progressions.py` that called into the quarantined
  `predictive_engine`/`predictive_sidecar` modules, and the one sidecar
  integration test in `test_phase6_lots_zodiacal_releasing.py` — the
  remaining tests in all three files, which test the real technique
  engines directly, are untouched.

**Explicitly NOT touched, confirmed still legitimate:**
`engine/returns.py`, `engine/profections.py`, `engine/solar_arc.py`,
`engine/progressions.py`, `engine/lots.py`, `engine/zodiacal_releasing.py`,
`engine/transit_engine.py` (established technique, fixture-tested,
never Testable-derived), and `formulas/proprietary_indexes.py` (EO's own
proprietary layer, confirmed acceptable by the operator against its own
synced v0.2 specification).

**Open follow-up, not done this session:** per-instance client-facing
disclosure that the proprietary EAS layer (KVQ/MKI/RWI/DFIS/etc.) is EO's
own interpretive system, not standard astrology — currently only
disclosed generically at the document level
(`products/shared/CLIENT_METHOD_AND_LIMITS.md`). `EO_UPGRADE_PHASE11_
TOTAL_READINESS.md`'s Phase 11a section, written earlier the same session
under the "rewire convergence to stay active" plan, is now superseded by
this entry and needs a follow-up edit before it's actionable.

---

## 2026-07-08 - Phase 9b predictive-content blocks filled in (operator content pass, Claude verification)

**Context:** Operator wrote real prose into all three Phase 9b scaffold
files (prioritizing coverage over polish, as stated), replacing every
`[TODO]` placeholder. Verified the result rather than taking the file
count on faith.

**Verified:**

- All three files remain valid JSON with the original scaffold shape
  intact (94/94/159 leaves counting `_note`/`_version`, i.e. 92/92/157
  content leaves as scaffolded) — `0` `[TODO]` markers remaining in any
  of the three files.
- Spot-read several leaves directly (not just grepped): consistently
  second person, consistently carries the required hedged/research
  framing ("The system flags...", "research signal", "not a settled
  claim"/"not a fixed outcome"), right in the target word-count range.
- Live-generated a real Year Ahead and a real Personal Forecast report:
  rendered HTML shows `0` `[TODO]`, `0` `[BLOCK NOT FOUND]`, `0`
  `[MISSING BLOCK FILE]` markers. Read the actual rendered chapter card
  and candidate card text directly and confirmed it's real, on-topic,
  correctly routed prose (e.g. the Personal Forecast candidate card
  correctly used the `communication`/`lunation_family`+`progression_family`
  leaning content for a window whose real independent method families
  were lunation/progression-led).
- Fixed `tests/test_phase9b_report_surface.py`'s candidate assertion a
  second time — it had been pinned to the scaffold's literal `[TODO]`
  string in the previous entry, which broke now that real content exists
  (expected and correct: the test was over-fit to a temporary state).
  Rewrote it to assert real-content *behavior* instead of exact prose:
  non-empty, not a `[TODO]`/`[BLOCK NOT FOUND]`/`[MISSING BLOCK FILE]`
  marker, and not equal to the block file's top-level generic fallback
  (confirming the specific `(identity, transit_family)` leaf itself
  resolved, not just some fallback catching a miss).

**Verification:** Full phase 1-9b regression suite (60 tests) passes.

---

## 2026-07-08 - Phase 9b predictive-content blocks wired live, TODOs surface unfiltered by design (Claude / Sonnet 5)

**Context:** Immediately following the scaffold above, operator confirmed
they want the wiring done now (not deferred) and explicitly want
unfilled `[TODO]` blocks to surface visibly in generated reports rather
than being filtered — this is a deliberate product-development choice,
not an oversight: operator batch-generates free reports specifically to
find gaps, since they don't write code themselves and this is how they
audit content coverage.

**What changed, in `generate.py`:**

- `_format_predictive_chapter(chapter, report_type)` and
  `_format_predictive_candidate(candidate, report_type)` now take
  `report_type` and call `selectors.block_selector.select_block()`
  instead of building the old inline f-string. Chapters route on
  `(chapter_kind, domain_keys[0])` against `predictive_chapters.json`;
  candidates route on `(candidate_domain[0], independent_method_families[0])`
  against `predictive_candidates.json` — matching the scaffold built one
  entry above.
- `_build_predictive_report_surface()` now passes `report_type` through
  to both formatters (it already had `report_type` itself; this just
  threads it one level deeper).
- No filtering was added. `select_block()`'s own fallback-key
  degradation (exact match → domain/family-level `"fallback"` → file
  top-level `"fallback"`) is the only safety net — an unfilled leaf
  renders its literal `"[TODO: ~N words -- ...]"` string directly in the
  rendered report HTML, on purpose.
- Updated `tests/test_phase9b_report_surface.py`'s candidate assertion,
  which had checked for the old hardcoded phrase ("research prompt")
  that no longer exists in the code now that content is block-driven.

**Verification:**

- Full phase 1-9b regression suite (60 tests) passes.
- Live-generated a real Year Ahead report and confirmed the rendered
  HTML shows `"[TODO: ~65 words -- solar_arc_chapter chapter, creativity
  domain]"` directly in the predictive-chapter card body — confirming
  the wiring is real (routes to the correct chapter_kind/domain
  combination for that chart's actual data) and that the TODO surfaces
  exactly as the operator wants for now.

**Next step, operator's own:** fill in `predictive_chapters.json` (both
copies) and `predictive_candidates.json` with real prose, then batch-run
reports to find which combinations actually occur on real charts and
prioritize those first. No further engine or generate.py work is needed
for this to work end-to-end — filling the JSON is the entire remaining
task.

---

## 2026-07-08 - Phase 9b predictive-content block scaffold (Claude / Sonnet 5)

**Context:** Operator wants to move from engine work to content work next:
Phase 9b's predictive/experimental section currently renders from two
generic inline Python f-strings (`_format_predictive_chapter()` /
`_format_predictive_candidate()` in `generate.py`), not from the
hand-authored JSON block libraries every other section of Year Ahead and
Personal Forecast uses via `selectors/block_selector.py`'s
`select_block()`. This entry is the scaffold only — no prose written, no
`generate.py` wiring changed. That's a deliberate, separate next step.

**Routing keys, confirmed against engine code (not charter prose, which
in one case is wrong):**

- Chapters: `chapter_kind` (7 values, from
  `engine/convergence.py`'s `_chapter_kind_for_period`/
  `_chapter_kind_for_signal`) × `domain_keys` (12 values, from
  `engine/candidates.py`'s `DOMAIN_KEYS`).
- Candidates (Personal Forecast only, per
  `phase0/04_convergence_and_candidate_protocol.md` §10): `candidate_domain`
  × leading `independent_method_families` entry (12 real families).
  Found and noted a charter/code mismatch while pulling the real family
  list: `phase0/03_method_charters.md` describes return independence
  groups as `return_family_solar`/`return_family_lunar`, but
  `engine/returns.py` actually emits `f"return_family_{body.lower()}"` —
  i.e. `return_family_sun`, `return_family_moon`,
  `return_family_jupiter`, `return_family_saturn`. Used the code's real
  values for the scaffold; the charter text still needs its own fix
  separately (not done in this entry — flagging it here so it doesn't
  get lost).

**Files added, all JSON-valid, zero code changes:**

- `products/year_ahead/blocks/plainspeak/predictive_chapters.json` — 92
  `[TODO: ~65 words -- ...]` leaves (7 kinds × 12 domains + 7 per-kind
  fallbacks + 1 top fallback).
- `products/personal_forecast/blocks/shared/predictive_chapters.json` —
  same 92-leaf shape, `~60 words` target, personal_forecast voice.
- `products/personal_forecast/blocks/shared/predictive_candidates.json`
  — 157 `[TODO: ~50 words -- ...]` leaves (12 domains × 12 non-generic
  families + 12 per-domain fallbacks + 1 top fallback).
  `return_family_generic` / `zr_family_generic` (rare code fallbacks,
  not real leading families in practice) deliberately do NOT get their
  own full domain grid — they route through the existing per-domain
  `"fallback"` key instead, consistent with `select_block()`'s own
  fallback-key degradation, so nothing 404s at runtime without doubling
  scaffold size for values that almost never occur.

Every `_note` field states the hedged/research-framing requirement
explicitly (this is the one product section that must NOT read as a
settled claim, per the Phase 9b operator decision) so that requirement
survives even if a different session or tool fills these in later
without this conversation's context.

**Not done yet, on purpose:** `generate.py` is not wired to call
`select_block()` for these files — `_format_predictive_chapter()` /
`_format_predictive_candidate()` still generate their original inline
sentence. Wiring them up (and deciding whether unfilled `[TODO]` blocks
should surface visibly in dev/preview generation the way the operator
wants for now, or be filtered the way `products/identity_profile`'s
`_safe_select()` filters them for paid output) is a deliberate separate
next step, not done here.

---

## 2026-07-08 - Phase 9b report-integration live-verification (Claude / Sonnet 5)

**Context:** Standard post-Codex verification of Phase 9b — the one
authorized report-facing slice in this program. Read every changed file
(`generate.py`, both templates, the sidecar addition, all four `phase0/`
version bumps) before running anything, then ran the full regression
suite, then independently generated real Year Ahead and Personal Forecast
reports and inspected the rendered HTML directly, not just Codex's own
closeout claims.

**What was checked and confirmed correct:**

- `generate.py` builds `predictive_sidecar_payload` once in memory (via
  `build_predictive_sidecar()`) and both the template context and the
  written `.eo_predictive.json` (via the new
  `write_predictive_sidecar_payload()`) consume that same object — no
  duplicated scoring logic, no re-parsing the written file, exactly as
  Phase 9b's charter required.
- `_build_predictive_report_surface()` / `_format_predictive_chapter()` /
  `_format_predictive_candidate()` read `chapter_summary_score`,
  `coherence`, `counterforce`, `complexity`, `confidence`, and full
  `component_scores` straight from the sidecar's own `ChapterState` /
  `MicroCandidate` objects — confirmed no new, separately-invented display
  score exists anywhere in this diff.
- `_build_predictive_report_surface` is called from exactly two places
  (`_build_personal_forecast_context`, `_build_year_ahead_context`) —
  confirmed by grep that Daily Horoscope, Weekly Horoscope, Soul
  Ecosystem, and `predictive_sandbox` context builders do not call it at
  all, matching the "Year Ahead and Personal Forecast only" scope.
- Generated a real Year Ahead report and a real Personal Forecast report
  independently (not reusing Codex's `tmp/` output) and read the rendered
  HTML directly: both contain the "Predictive / experimental" labeled
  section and the required hedged language ("not a settled prediction or
  an outcome claim," "not a promise of an external event"), with the
  component-score detail block present and populated (not collapsed
  away). Cross-checked one specific rendered card against that same
  report's own sidecar rather than trusting the render alone: the first
  Personal Forecast candidate card ("Research-flagged window - Aug 28,
  2026," convergence score `0.7401`) matches sidecar candidate
  `cand_04db68ba` (`peak_at: 2026-08-28`, `convergence_score: 0.7401`)
  exactly — confirming the template is reading real per-candidate sidecar
  data, not a placeholder or a value common to every card (`0.7401`
  recurs across several distinct candidates in this sidecar, so this
  also confirmed it wasn't a coincidental match).
- Confirmed the `phase0/01`, `02`, `03`, `04` version bumps are pure
  `report_surface_visibility` documentation updates consistent with the
  2026-07-08 operator decision — no new fields, no new methods, no
  scoring-rule changes hiding inside the visibility-language edits.

**No bugs found this pass.** Full phase 1-9b regression suite (60 tests)
passes.

---

## 2026-07-08 - Phase 9 harness live-verification, plus a leftover six-day-cap charter bug found and fixed (Claude / Sonnet 5)

**Context:** Standard post-Codex verification of the Phase 9 validation
harness — full regression suite, then reading the actual harness code
(not just its own summary) and live-testing every public function
against a real sidecar, not just the synthetic unit fixtures.

**Charter bug found (in the charter, not the code):**
`phase0/05_validation_protocol.md` §5.10 step 2 still said "Preserve the
window width (6 days)" for matched-random baseline generation — a
leftover instance of the exact fixed-cap error the operator caught and
corrected everywhere else in this program on 2026-07-07 (`01`, `04`,
`06`, `07`, `README`, and the top-level program doc all got fixed; `05`
was missed). Checked whether Codex's implementation had inherited the
stale charter language: it had not —
`engine/validation_harness.py`'s `build_matched_random_baseline()` and
`_candidate_width_seconds()` correctly read each real candidate's own
`window_days`/actual `[start_at, end_at]` span, per candidate, exactly
as its own closeout note claimed ("preserving report period, candidate
count, and each candidate's emitted window width"). Fixed the charter
text to match the (correct) code, bumped `05` `phase0.1.1` →
`phase0.1.2`.

**Live verification, against a real `year_ahead` sidecar (41
candidates), not just `tests/test_phase9_validation_harness.py`'s
synthetic fixtures:**

- `sidecar_run_package()` and `initialize_outcome_ledger()` produce
  identical `run_package_id` / matched-random baseline candidates across
  two independent calls on the same sidecar (reproducibility per §9).
- Matched-random baseline's per-candidate `window_days` set matched the
  real candidates' `window_days` set exactly (sorted-list equality) —
  confirms width preservation is real, not just documented.
- `append_outcome_entry()` correctly rejected: an invalid
  `outcome_category` string, a `reviewed_at` timestamp before the
  candidate's own `pre_registered_at`, and a `supported_hit` entry
  missing `event_date` — all three are hard requirements from
  `phase0/05_validation_protocol.md` §1.2 and §3, and all three raised
  `ValueError` as expected rather than silently accepting bad data.
- `build_ablation_report()` and `asteroid_contribution_report()` ran
  against the same real sidecar without error; ablation removing
  `transit_family` dropped all 41 candidates, consistent with the
  broad-chapter-support pattern already documented in the Phase 8
  verification entry below (every candidate in this particular report
  shares the same handful of long-duration chapters) — not a new
  finding, just confirms the two phases' data agree.
- Outcome ledger round-tripped through `write_outcome_ledger()` /
  `read_outcome_ledger()` correctly, including shape validation on
  reload.

**No code bugs found in `engine/validation_harness.py` this pass.**
Confirmed it is fully decoupled from report generation (`generate.py`
and `engine/predictive_sidecar.py` have zero references to it) — outcome
ledgers are never written during normal report generation, matching
§1's "outcomes live outside the generation artifact."

**Verification:** Full phase 1-9 regression suite (58 tests) passes.

---

## 2026-07-08 - Phase 9b report integration implementation (Codex / GPT-5)

**Context:** Operator asked Codex to implement Phase 9b after Phase 9's
validation harness landed. This is the one authorized report-facing slice
in the predictive architecture program: expose already-built
`ChapterState` / `MicroCandidate` evidence in Year Ahead and Personal
Forecast, framed as predictive/experimental, while preserving the Phase 9
validation harness as the outcome-tracking layer.

**What changed:**

- Updated generation flow so `build_predictive_sidecar()` runs once before
  report context rendering for Year Ahead, Personal Forecast, and
  Predictive Sandbox. The resulting in-memory sidecar feeds templates and
  is then written unchanged after HTML render, keeping rendered modules and
  `.eo_predictive.json` synchronized without re-parsing the written file.
- Added `write_predictive_sidecar_payload()` in
  `engine/predictive_sidecar.py` for writing the already-built sidecar.
- Added `generate.py` Phase 9b report-surface formatting:
  - Year Ahead receives chapter cards only;
  - Personal Forecast receives chapter cards plus research-flagged
    candidate-window cards;
  - component score details remain present in expandable detail data;
  - visible prose uses "flags," "research prompt," "observation," and
    "not a settled prediction/outcome claim" framing.
- Added additive template sections:
  - `products/year_ahead/templates/active/year_ahead.html`: Predictive /
    experimental chapter module after Forecast Climate.
  - `products/personal_forecast/templates/personal_forecast.html`:
    Predictive / Experimental Layer with chapters and candidate windows.
- Updated Phase 0 report-surface visibility contracts:
  `phase0/01_predictive_object_schemas.md` `phase0.1.2 -> phase0.1.3`,
  `phase0/02_asteroid_predictive_registry.json`
  `phase0.1.1 -> phase0.1.2`,
  `phase0/03_method_charters.md` `phase0.1.3 -> phase0.1.4`, and
  `phase0/04_convergence_and_candidate_protocol.md`
  `phase0.1.2 -> phase0.1.3`.
- Added `tests/test_phase9b_report_surface.py` for report-type gating and
  component-score retention.
- Updated the Phase 3 asteroid registry test for the intentional
  `phase0.1.2` registry version bump.

**Verification:**

- `python -m py_compile generate.py engine\predictive_sidecar.py tests\test_phase9b_report_surface.py`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_phase9b_report_surface`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_phase2_predictive_sidecar tests.test_phase3_asteroid_predictive_activation tests.test_phase4_returns_profections tests.test_phase5_solar_arc_progressions tests.test_phase6_lots_zodiacal_releasing tests.test_phase7_natal_promise_convergence tests.test_phase8_candidates tests.test_phase9_validation_harness tests.test_phase9b_report_surface`
- Real Year Ahead run:
  `python .\generate.py year_ahead --name "Phase Nine B" --date 1990-01-01 --time 12:00 --location "Peoria, Illinois, USA" --report-date 2026-01-01 --output-dir tmp\phase9b_real --output-filename phase9b_year.html --no-browser`
- Real Personal Forecast run:
  `python .\generate.py personal_forecast --name "Phase Nine B" --date 1990-01-01 --time 12:00 --location "Peoria, Illinois, USA" --report-date 2026-01-01 --output-dir tmp\phase9b_real --output-filename phase9b_personal.html --no-browser`
- Rendered HTML inspection confirmed:
  - Year Ahead contains "Predictive / experimental layer," "Emerging
    Chapters Flagged by the Research Engine," and "not a settled
    prediction or an outcome claim."
  - Personal Forecast contains "Predictive / Experimental Layer,"
    "Research-flagged window," "Component detail," and "not a promise of
    an external event."

**Boundary notes:** Phase 9b does not touch Daily Horoscope, Weekly
Horoscope, or Soul Ecosystem prose. It does not add methods, retune
scores, read rendered HTML as validation input, or present candidates as
settled predictions. Candidate cards are restricted to Personal Forecast;
Year Ahead surfaces chapters only.

---

## 2026-07-08 - Phase 9 retrospective validation harness implementation (Codex / GPT-5)

**Context:** Operator asked Codex to implement Phase 9 after the passive
JSON/content-block review. Claude had also added a Phase 9b/report-
integration charter carve-out, but Phase 9b depends on the validation
harness half of Phase 9 being present first. This entry covers the
harness only: no report-template changes, no historical validation
claims, and no fabricated outcome data.

**What changed:**

- Added `engine/validation_harness.py` for sidecar-native validation
  infrastructure:
  - immutable run-package descriptors with reproducible `run_package_id`
    and sidecar hash;
  - outcome-ledger initialization, read/write, validation, and append-only
    reviewer entries;
  - the five locked outcome categories exactly as chartered;
  - deterministic matched-random baselines preserving report period,
    candidate count, and each candidate's emitted window width;
  - outcome summaries that keep `unresolved`, `research_incomplete`, and
    `excluded_by_protocol` out of precision denominators;
  - sidecar-native method-family ablation summaries;
  - per-asteroid contribution summaries with the chartered publication
    threshold reminder.
- Added `tests/test_phase9_validation_harness.py` with deliberately
  synthetic fixture names and subjects so no test data can be mistaken for
  a real historical hit/non-hit.

**Verification:**

- `python -m py_compile engine\validation_harness.py tests\test_phase9_validation_harness.py`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_phase9_validation_harness`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_phase2_predictive_sidecar tests.test_phase3_asteroid_predictive_activation tests.test_phase4_returns_profections tests.test_phase5_solar_arc_progressions tests.test_phase6_lots_zodiacal_releasing tests.test_phase7_natal_promise_convergence tests.test_phase8_candidates tests.test_phase9_validation_harness`
- Real report run:
  `python .\generate.py predictive_sandbox --name "Phase Nine" --date 1990-01-01 --time 12:00 --location "Peoria, Illinois, USA" --report-date 2026-01-01 --output-dir tmp\phase9_real --output-filename phase9_real.html --no-browser`
- Real sidecar harness inspection for
  `tmp\phase9_real\phase9_real.eo_predictive.json`: 40 candidates, 3
  rejected/suppressed candidates, 40 matched-random baseline candidates,
  `quiet_period = False`, transit-family ablation removes 40 candidates,
  and 40 candidates carry asteroid participation on this chart/run.

**Boundary notes:** Phase 9 does not code any real outcomes, does not
write outcome ledgers during normal report generation, does not use report
HTML/prose as validation input, does not count unresolved outcomes as hits
or misses, and does not add a sixth outcome status. Phase 9b report
integration remains a separate next implementation slice.

---

## 2026-07-08 - Operator decision: Phase 10 gate lifted, folded into new Phase 9b (Claude / Sonnet 5)

**Context:** Before prompting Codex for Phase 9, the operator explicitly
asked to remove the standing "no client-facing report changes" guardrail
for this phase specifically, reasoning: Phase 9 is the last actively-
scoped phase in this program, there is no separate Phase 10 effort
planned, and trying to both hedge (keep waiting on a hypothetical future
phase) and upgrade (actually ship report integration) at the same time
would split focus for no benefit. Asked the operator one clarifying
question on gating mechanics before touching any charter file: whether
promoted evidence should be gated on completed outcome-ledger validation,
or exposed immediately with predictive/experimental framing while
validation runs alongside. Operator chose the latter ("expose now,
validate alongside") — matches "after phase 9 completes we'll want
generated reports to automatically include updates" actually happening
soon, rather than after months of real-world outcome tracking.

**What changed:** This is a charter patch, not an implementation. No
engine or template code was touched.

- `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`: anti-drift rule 1 ("no
  client-facing report changes in Phases 7, 8, or 9") now reads "Phases 7
  or 8" only, with an explicit dated carve-out note for Phase 9. Added a
  new `## Phase 9b - Report Integration` section (this program's original
  "Phase 10 — Controlled Surface Expansion" from
  `EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md`, never previously turned into
  real agent prompts) with its own required outcomes, file ownership, and
  Codex/Claude prompts — scoped to Year Ahead and Personal Forecast only,
  additive template sections, hedged/research-framed prose only, reading
  directly from the same in-memory predictive-results object that already
  feeds the sidecar (no duplicated scoring logic, no re-parsing the
  written `.eo_predictive.json`).
- `phase0/04_convergence_and_candidate_protocol.md` §10 (report-surface
  routing): the "Phase 10 governance" gate on `Weather`, `ChapterState`,
  and `MicroCandidate` promotion to Year Ahead / Personal Forecast is
  lifted, with an operator-decision note and updated per-class routing
  language. `phase0.1.1` → `phase0.1.2`.
- `phase0/01_predictive_object_schemas.md`, `02_asteroid_predictive_
  registry.md`, `03_method_charters.md`, `05_validation_protocol.md`:
  each file's header now carries a dated pointer note that its own
  "Phase 10" promotion-gate references are superseded by this decision
  (cross-referencing `04` §10 and the new Phase 9b section) rather than
  rewriting every individual line — the per-field default
  `report_surface_visibility` values documented in those files are
  unchanged and still accurate; only the *promotion-beyond-default* gate
  moved. `01` `phase0.1.1` → `phase0.1.2`, `02` `phase0.1.1` →
  `phase0.1.2`, `03` `phase0.1.2` → `phase0.1.3`, `05` `phase0.1.0` →
  `phase0.1.1`.

**Explicitly unaffected:** anti-drift rules 2-6 (no new methods, no
score simplification in the underlying data/sidecar, no fabricated
validation data, no reintroduced sandbox cap, no silent scope-filling).
Phase 9's validation harness (outcome ledger, status categories,
ablation runs) is unchanged — Phase 9b is additive alongside it, not a
replacement.

**Next step:** ready to prompt Codex for Phase 9 (validation harness) and
Phase 9b (report integration) — Claude's pre-implementation review of
both is done; this entry and the charter patches above are that review's
output.

---

## 2026-07-08 - Phase 8 live-verification: two real bugs found and fixed (Claude / Sonnet 5)

**Context:** Standard post-Codex verification pass on the Phase 8 landing —
full regression suite, then a live `year_ahead` report generation with
direct inspection of `.eo_predictive.json`'s new `candidates` array,
since every real bug found this whole program has come from that live
check, never from unit tests alone. Both bugs below were confirmed the
same way: an actual field value in a real report that couldn't be
explained by intended behavior.

**Bug 1 — ZR trigger events could carry a peak date outside the report
window.** A real candidate (`cand_d8858b73`) had `peak_at =
2024-03-07`, entirely outside its report's `[2026-07-08, 2027-07-08]`
window. Root cause: `engine/zodiacal_releasing.py`'s
`zodiacal_releasing_events()` collects L1/L2 `TimeLordPeriod` records
that *overlap* the window (correct — a period can be active before the
window starts) but then emitted a `zr_l1_transition`/`zr_l2_transition`/
`zr_peak` `ForecastEvent` at that period's true `start_at`, even when
the period had started years before the window and only its *tail*
overlapped it. The function's own docstring already promised events
"intersecting [start_date, end_date]" — the implementation didn't
enforce that. Fixed by filtering emitted events to
`window_start <= peak_datetime <= window_end` inside
`zodiacal_releasing_events()`, after generating them per-period.
Periods themselves are unaffected (still correctly represent ongoing
`TimeLordPeriod` context regardless of when they started); only the
discrete transition/peak *events* are now window-scoped, which is what
Phase 8's candidate builder actually consumes as trigger evidence.

**Bug 2 — `method_family_diversity()` inflated its own `count` field,
silently defeating the anti-stacking rule it exists to enforce.**
Every candidate in the same live report showed `component_scores
["method_family_diversity_count"] = 72` while `independent_method_
families` (the actual list of distinct family names) had only 8
entries — an internal contradiction. Root cause in
`engine/convergence.py`'s `method_family_diversity()`: after building
the composite-dedup `winners` dict (correctly keyed by
`(independence_group, source_body, target_body)` per
`phase0/04_convergence_and_candidate_protocol.md` §2.2, to collapse
`transit_family`/`proprietary_transit_family` pairs targeting the same
body), the function reported `count = len(winners)` — the number of
distinct dedup *keys* — instead of the number of distinct *family
labels* among them. Per §2.9 of that same charter (using almost this
exact example): "Multiple asteroid contacts ... do **not** inflate
`independent_method_families` count on their own. They belong to the
same `transit_family` (or `proprietary_transit_family`) vote." Any
candidate with several distinct asteroid or multi-target contacts
within one family therefore had its diversity count silently inflated,
which feeds directly into `component_scores.method_family_diversity`
(and would have fed the `|independent_method_families| >= 2` hard
emission gate had a report ever had fewer than 2 genuine families
present). Fixed by computing `count` and `anti_stacking_ratio` from
`len(groups)` (the deduplicated family-label set already computed for
`independent_method_families`) instead of `len(winners)`. Also fixed
`tests/test_phase7_natal_promise_convergence.py`'s
`test_asteroid_specificity_contributes_without_extra_method_vote` —
it asserted `diversity["count"] == 2` for the *exact* two-asteroid,
one-family example from charter §2.9, contradicting its own next
assertion that `independent_method_families == ["proprietary_transit_
family"]` (length 1) and its own test name ("...without extra method
vote"). Corrected to assert `count == 1`, matching both the charter's
explicit example and the test's own stated intent.

**Verification:** Full phase 1-8 regression suite (52 tests) passes
after both fixes. Re-ran the same real `year_ahead` report: 41
candidates, zero outside the report window, `method_family_diversity_
count` now equals the length of `independent_method_families` on every
candidate checked, rejected-candidate registry unchanged in shape
(`superseded_by_later_candidate` merges still recorded correctly).

---

## 2026-07-08 - Phase 8 discrete MicroCandidate engine implementation (Codex / GPT-5)

**Context:** Operator asked Codex to implement Phase 8 after Claude's
pre-review found and fixed the blocking `signal_role` derivation bug.
Scope stayed internal R&D only: no client-facing report prose, no
template changes, no outcome ledger, and no fixed general candidate
window cap.

**What changed:**

- Added `engine/candidates.py` for Phase 8 `MicroCandidate` assembly:
  trigger-derived natural windows, pre-registration timestamps,
  stable `candidate_id` generation, chapter/trigger/anchor support,
  method-family anti-stacking, topic coherence, component score
  preservation, confidence handling, alternative evidence retention,
  accepted candidates, and locked-enum rejected/suppressed candidates.
- Wired `engine/predictive_sidecar.py` to emit `candidates` and
  `rejected_candidates` arrays and append candidate-specific
  convergence-composition records with `candidate_id` linkage.
- Added `temporal_precision` to serialized `PredictiveSignal` records
  so Phase 8 can enforce the contract's trigger qualification rule
  (`signal_role = trigger_evidence` and `temporal_precision` in
  `instant`/`day`) after sidecar normalization.
- Added `tests/test_phase8_candidates.py` for pre-registration fields,
  outcome-ledger linkage fields, rejected candidates, composite
  anti-stacking, trigger-derived wide windows with no hidden cap, and
  sidecar export.
- Updated the Phase 7 sidecar integration test so it no longer freezes
  `candidates` to the pre-Phase-8 empty placeholder.

**Verification:**

- `python -m py_compile engine\candidates.py engine\predictive_sidecar.py tests\test_phase8_candidates.py tests\test_phase7_natal_promise_convergence.py`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_phase2_predictive_sidecar tests.test_phase3_asteroid_predictive_activation tests.test_phase4_returns_profections tests.test_phase5_solar_arc_progressions tests.test_phase6_lots_zodiacal_releasing tests.test_phase7_natal_promise_convergence tests.test_phase8_candidates`
- Real report run:
  `python .\generate.py predictive_sandbox --name "Phase Eight" --date 1990-01-01 --time 12:00 --location "Peoria, Illinois, USA" --report-date 2026-01-01 --output-dir tmp\phase8_real --output-filename phase8_real.html --no-browser`
- Real sidecar check for `tmp\phase8_real\phase8_real.eo_predictive.json`:
  72 natal-promise anchors, 63 chapters, 38 pre-registered
  candidates, 5 rejected/suppressed candidates, 38 candidate-specific
  convergence records, `maximum_window_days = null`, and locked
  rejection reason `superseded_by_later_candidate` for merged trigger
  peaks.

**Boundary notes:** Phase 8 does not write `<report>.eo_outcomes.json`,
does not score any candidate as hit/non-hit, does not scrape report
HTML, and does not expose candidate claims in Year Ahead, Personal
Forecast, or Predictive Sandbox prose.

---

## 2026-07-08 - Phase 8 pre-review finding: `signal_role` was never actually derived, only echoed (Claude / Sonnet 5)

**Context:** Doing the pre-implementation review of
`phase0/04_convergence_and_candidate_protocol.md` before prompting Codex
for Phase 8 (the same pattern used before every phase since Phase 3),
checking whether Phase 8's hard requirements against Phase 7's output
are actually satisfiable. Phase 8's MicroCandidate rule requires
`|trigger_support| >= 1`, defined as signals with `signal_role ==
"trigger_evidence"`.

**Root cause, confirmed by reading, not assumed:** `signal_role` is a
three-value enum (`chapter_evidence` / `trigger_evidence` /
`modifier_evidence`) defined by a specific derivation rule in
`phase0/01_predictive_object_schemas.md` section 3 (based on
`temporal_precision` and `clock_role`). Two separate bugs meant no real
signal ever actually carried a correct value:

1. `engine/predictive_engine.py`'s `_event_to_signal()` (the shared
   adapter for transit/return/solar_arc/progression/ZR signals) set
   `clock_role` and `temporal_precision` on every signal but never set
   `signal_role` at all. `_proprietary_event_to_signal()` (the Phase 3
   asteroid adapter) set neither `clock_role` nor `signal_role`.
2. `engine/predictive_sidecar.py`'s `_signal_role()` — the only place
   that *did* compute a `signal_role` value, at sidecar-serialization
   time — didn't implement the schema rule at all. It returned
   `clock_role` back verbatim (e.g. the literal string `"chapter"`),
   which never matches any of the three valid enum values. Under this
   logic, `trigger_support` could never be non-empty on any real
   report, no matter what Phase 8 built on top of it.

**Fix:** Added `_derive_signal_role(temporal_precision, clock_role,
*, source_body="", duration_days=None)` to `engine/predictive_engine.py`,
implementing the schema's rule directly (chapter_evidence for
`temporal_precision in {season, year_or_longer}` or `clock_role ==
chapter`; trigger_evidence for `temporal_precision in {instant, day,
week}` and `clock_role in {trigger, return, overlay}`; modifier_evidence
for `clock_role in {modifier, time_lord}`; ties toward trigger_evidence).
Wired it into `_event_to_signal()` and `_proprietary_event_to_signal()`
so `signal_role` is set once, in-memory, at signal construction time —
not just at sidecar export. Raw `TRANSIT` scan events (from
`transit_engine.py`) never carry `clock_role`/`temporal_precision` at
all, so added an explicit fallback for that one case only (both fields
blank): structural outer-planet source body or >90-day duration ->
chapter_evidence, else trigger_evidence — the same heuristic
`convergence.py`'s own `_is_long_clock_signal()` already used
independently, so this isn't a new invented rule, just making the
existing one available earlier and consistently.
`predictive_sidecar.py`'s `_signal_role()` now prefers the upstream
`signal_role` if already one of the three valid values, and only
falls back to re-deriving (with the same structural/duration fallback)
for signals built outside the engine, e.g. test fixtures.

**Verification:** Full phase 1-7 regression suite (47 tests) passes.
Live-generated a real `year_ahead` report and inspected
`.eo_predictive.json` directly: 127 signals, `signal_role` distribution
`{trigger_evidence: 64, chapter_evidence: 54, modifier_evidence: 9}`
across all method families (TRANSIT, LUNATION, RETURN, SOLAR_ARC,
PROGRESSION, ZODIACAL_RELEASING) — the first time this field has ever
held a schema-correct value on a real report. Phase 8's
`trigger_support` requirement is now satisfiable. Clear to prompt Codex
for Phase 8.

---

## 2026-07-08 - Phase 7 performance fix: convergence composition took 2+ minutes on a real report (Claude / Sonnet 5)

**Context:** Reviewing Codex's Phase 7 landing (both roles were
available today), the standard live-generation check this program
requires before any phase counts as done -- generate a real report,
inspect the sidecar -- caught something Codex's own live check on
`predictive_sandbox` had not: a `personal_forecast` report hung for
over two minutes (confirmed via `ps`/timeout, not just "felt slow")
where every other report type in this program has taken 2-5 seconds.
`predictive_sandbox`'s smaller signal count on Codex's own test chart
happened not to trigger the scale at which this became visible.

**Root cause, confirmed by profiling (`cProfile`), not guessed at:**
`coherence_graph()` (the seven-rule topic-coherence check from
`phase0/04_convergence_and_candidate_protocol.md` section 3.1) is
invoked once per chapter and once per anchor-group -- ~900+ times on
a real report -- and each invocation independently recomputed, from
scratch, an O(signal_count squared) all-pairs comparison. Two
compounding costs inside that: (1) `_natal_aspect_orb()` rescanned the
full natal aspect list (500+ entries) and `_index_driver_sets()`
rescanned the full anchor list (70+ entries) on every single pair, on
every one of those ~900 calls; (2) each pairwise check also
re-derived a signal's anchor/topic/domain sets from raw dicts via
`_string_list()` every time that signal appeared in any pair, in any
cluster -- profiled at 8.6 million redundant calls on one real report.

**Fix, in three layers, each verified by timing the same real report
before and after:**

1. Precompute `{frozenset(body_pair): orb}` and `{anchor_id: index_links}`
   lookup dicts once instead of rescanning the raw aspect/anchor lists
   on every pairwise check. (2+ minutes, unmeasured upper bound -> 35s)
2. Precompute each signal's derived coherence data (anchor/topic/domain
   sets, target house, index-driver set) once per signal_id, cached on
   the same shared lookup object so it survives across all ~900
   `coherence_graph` calls in one report run instead of being rebuilt
   from raw signal dicts on every pairwise comparison inside every one
   of those calls. (35s -> 18.7s)
3. Memoize `coherence_reasons` results by unordered signal-ID pair on
   that same shared lookup object, since the same pair of signals
   recurs across many overlapping chapters and anchor-groups within
   one report -- most pairs were being scored more than once.
   (18.7s -> 13.3s)

All three fixes thread an optional `lookups`/`derived` parameter
through the existing call chain (`coherence_graph`, `coherence_reasons`,
`_natal_aspect_orb`, `_index_driver_sets`, `component_scores`,
`_composition_record`, `_coherent_subset`, `_chapter_from_parts`),
built once at the top of `build_chapter_states` and
`build_convergence_composition` and passed down -- not a global
`id()`-keyed cache, which would have been unsafe given the test suite
runs many report generations in one process and Python can reuse
object IDs after garbage collection.

**Honest residual:** 13.3 seconds is a real, verified ~90% reduction
from the original hang, and the sidecar output was independently
re-verified as correct after the fix (154/154 events and signals
carrying populated `natal_anchor_ids`, matching Codex's own reported
counts on a different chart) -- but it is still noticeably slower
than every other report type's 2-5 seconds. The remaining cost is
structural (coherence is still computed per composition group rather
than once globally with subgraphs queried per group), not a
correctness bug. Worth a further pass if report generation time
becomes a real constraint, but not blocking Phase 7 from being
considered done -- the fix converts an effectively broken feature (a
report that would not complete in reasonable time) into a working,
if not yet fully optimized, one.

**Verification:** 120 tests across the full relevant suite pass, no
regressions, both before identifying the bug and after each of the
three fix layers.

**Files changed:** `engine/convergence.py`.

---

## 2026-07-08 - Phase 7 natal promise graph and convergence implementation (Codex / GPT-5)

**Context:** Operator asked Codex to implement Phase 7 after Phase 6
completion and Claude's convergence-contract review. Scope stayed
sidecar-only: no report templates, no client prose, no MicroCandidate
generation, and no outcome ledger.

**What changed:**

- Added `engine/natal_promise.py` to build `NatalPromiseAnchor`
  records from whole-sign houses, rulers/dispositors, natal planets,
  angles, custom asteroids through the 34-body asteroid registry,
  named configurations, proprietary-index links, and reserved
  topic/domain keys.
- Added anchor matching that backfills `natal_anchor_ids` onto every
  existing predictive event/signal path, including source-body
  fallback for standalone Solar/Lunar eclipse records.
- Added `engine/convergence.py` for Phase 7 chapter promotion and
  transparent convergence composition: composite anti-stacking,
  the seven-rule topic-coherence graph, counterforce, complexity,
  method-family diversity, asteroid specificity, confidence, and
  other component scores remain visible instead of being collapsed.
- Wired the predictive engine and predictive sidecar to emit
  `natal_promise_anchors`, `chapters`, and
  `convergence_composition`; the sidecar rebuilds the final graph
  against its own natal snapshot ID so anchors/events/signals/chapters
  are internally coherent.
- Added `tests/test_phase7_natal_promise_convergence.py` for asteroid
  registry-informed anchors, retroactive anchor matching,
  anti-stacking, topic coherence, conflicting evidence, asteroid
  specificity, and sidecar export.

**Verification:**

- `python -m py_compile engine\natal_promise.py engine\convergence.py engine\predictive_engine.py engine\predictive_sidecar.py tests\test_phase7_natal_promise_convergence.py`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_phase2_predictive_sidecar tests.test_phase3_asteroid_predictive_activation tests.test_phase4_returns_profections tests.test_phase5_solar_arc_progressions tests.test_phase7_natal_promise_convergence`
- Real report run:
  `python .\generate.py predictive_sandbox --name "Phase Seven" --date 1990-01-01 --time 12:00 --location "Peoria, Illinois, USA" --report-date 2026-01-01 --output-dir tmp\phase7_real --output-filename phase7_real.html --no-browser`
- Real sidecar check for `tmp\phase7_real\phase7_real.eo_predictive.json`:
  72 natal-promise anchors, 104 chapters, 150 convergence-composition
  records, and all 152 raw events / all 152 predictive signals carried
  populated `natal_anchor_ids` across TRANSIT, LUNATION, RETURN,
  SOLAR_ARC, PROGRESSION, and ZODIACAL_RELEASING.

**Boundary notes:** Phase 7 does not emit `MicroCandidate` or outcome
ledger records, does not retune prior scanner orbs/weights, and does
not promote any predictive evidence into client-facing report prose.

---

## 2026-07-08 - Phase 7 method-charter review, before Codex implementation: phase0.1.0 -> phase0.1.1 (Claude / Sonnet 5)

**Context:** Ahead of Codex's Phase 7 implementation, done same-day
per the coordination doc's own "Caution" flag on this phase (graph
contracts and convergence code are tightly coupled, so review must
land before parallel work starts, not during it).

**Four gaps found and fixed in `phase0/04_convergence_and_candidate_protocol.md`:**

1. **No explicit build order.** The chapter builder's own step 3
   ("cluster signals by shared anchor") depends on `natal_anchor_ids`
   being populated, but anchor construction is listed as a separate,
   unordered "required outcome" of the same phase -- a real
   chicken-and-egg risk. Added an explicit sequence: anchors ->
   anchor-matching (retroactive, not just prospective) -> chapter
   builder -> convergence/candidates.
2. **No `TimeLordPeriod`-to-`ChapterState` granularity rule.** With
   real ZR data now existing (Phase 6: L1/L2/L3/L4 records per lot),
   "aggregate active TimeLordPeriod records into their durations" was
   ambiguous about whether every period record becomes its own
   chapter or whether levels nest under one. Fixed: one `ChapterState`
   per top-level occurrence (one per profection year, one per ZR L1),
   child levels contribute as supporting evidence, not separate
   chapters.
3. **Unquantified "shared time window" for chapter clustering.**
   Fixed: overlap or within 30 days of the chapter's own range --
   deliberately wider than the candidate builder's +/-3-day discovery
   buffer, since chapters operate at month/year scale.
4. **`ChapterState.confidence`/`counterforce`/`complexity` had no
   stated formula**, risking a second, inconsistent derivation
   alongside `MicroCandidate`'s already-specified ones. Fixed:
   explicitly reuse the same formulas, applied to the chapter's own
   contributing signals.

**Files changed:** `phase0/04_convergence_and_candidate_protocol.md`.

---

## 2026-07-08 - Phase 7-9 prompts hardened against scope drift, no implementation started (Claude / Sonnet 5)

**Context:** Operator asked to stop after Phase 6 rather than risk a
mid-Phase-7 cutoff from token limits, and specifically asked that
Phases 7-9 be made explicit enough that a different, less
session-aware tool (Antigravity/Gemini was named specifically) can't
drift from scope on "excitement" about the project. No Phase 7
implementation was started.

**What changed:** added a new "State as of Phase 6 completion" section
to `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`, positioned right before
Phase 7, that any agent (not just one with this session's context) can
read cold: a table of every engine file that exists and works today
and what it's wired into; that `natal_anchor_ids` is empty everywhere
on purpose and Phase 7 must backfill it, not just populate it
prospectively; the exact recurring bug pattern (`user_profile` nesting
for birth date / Julian day) that has hit three phases in a row,
stated as a specific thing to check for rather than a story to
remember; and the live-verification requirement restated as
non-optional, since every real bug found in this program was caught
that way and none by unit tests alone.

Added six explicit, numbered anti-drift rules covering the specific
failure modes an "excited" agent could plausibly produce: no
client-facing report changes in Phases 7-9 under any framing; no new
astronomical/interpretive methods beyond each phase's named required
outcomes; no collapsing component scores into one opaque number; no
fabricated example data in Phase 9 presented as if it were a real
historical result; no reintroduction of the six-day candidate-window
cap (the earlier, corrected mistake) for the general system; and "do
less and say so" over silently filling a perceived gap.

Rewrote all six Phase 7-9 prompts (three Codex, three Claude Code) to
reference the new section explicitly at the top, name concrete new
file paths matching the established `engine/*.py` convention rather
than vague "module" language, add phase-specific non-goals, and
require a live-generated-report check with a specific pass condition
before any phase can be called done -- not just "add tests."

**Files changed:** `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`.

---

## 2026-07-08 - Phase 6 Lots and Zodiacal Releasing foundation (Claude / Sonnet 5, both Codex and Claude roles)

**Context:** Codex was unavailable for the rest of the night, so at the
operator's request Claude implemented Phase 6 directly rather than
producing a review-only queue for a separate implementation session.
Followed the C5 (Lots) and C5b (Zodiacal Releasing) charters in
`phase0/03_method_charters.md` and the `phase0.1.2` contracts, applying
the same verification discipline used to review every prior phase:
live generation on real charts, not just unit tests against synthetic
fixtures.

**Lots:** Added `engine/lots.py` -- Fortune, Spirit, and Necessity,
sect-aware via `formulas.standard.sect.evaluate_chart_sect()` (the
chartered authoritative source), with an explicit `sect_state` /
reduced-confidence fallback when sect is genuinely indeterminate
(Sun on the horizon axis) rather than silently choosing a side.
Verified bit-exact against C5 section 12's own fixture values (day
chart Fortune = 310 degrees, night chart = 250 degrees, from
ASC=100/Sun=200/Moon=50).

**Zodiacal Releasing:** Added `engine/zodiacal_releasing.py` -- L1-L4
period generation via one recursive proportional-subdivision function
(each level's twelve sub-periods scaled to the parent's duration by
that sign's own Valens year-count over the 211-year total), peak
detection (period sign angular from the lot's own sign), and
`TimeLordPeriod` records for all four levels, window-filtered so only
periods intersecting the report window are computed -- this keeps L3/L4
record counts bounded instead of enumerating a chart's full
multi-century period tree. Only L1/L2 generate trigger-role
`ForecastEvent`s (transitions, peaks) per C5b section 7; L3/L4 are
period-only (modifier scale).

**Corrected in the charter while implementing:** C5b section 12's
validation fixture said "246-year cycle" for the L1 total; the actual
sum of the twelve Valens year-counts is 211
(15+8+20+25+19+20+8+15+12+27+30+12), the standard cited total in ZR
literature. Fixed the arithmetic slip before building the test fixture
against it.

**Loosing of the Bond:** implemented and wired, but honestly
documented as a rare/edge-case trigger under the proportional
construction used here (twelve sub-periods sum exactly to the parent
duration by construction, so the charter's own literal condition --
"a sub-period completes but the parent has not" -- has no routine
occasion to fire). The field and mechanism are present and correct;
it simply did not fire on either test chart, and that is expected
given the algorithm, not a bug being hidden.

**Integration:** Updated `engine/predictive_engine.py` to adapt ZR
transition events into `ZODIACAL_RELEASING` predictive signals
alongside transit, asteroid, return, Solar Arc, and progression
evidence, and to add Fortune and Spirit ZR periods to
`time_lord_periods` alongside annual profections. Updated
`engine/predictive_sidecar.py` to compute Lots directly inside the
sidecar writer (`natal_snapshot.lots`) rather than touching the shared
`generate.py`/natal-engine payload pipeline used by every product --
keeps the change scoped to the sidecar, matching every prior phase's
"additive, sidecar-only" pattern. No report templates or client prose
changed.

**Two real bugs found and fixed via live verification, not caught by
unit tests alone:**

1. `zodiacal_releasing_events()`'s sort used a `peak_at` key that does
   not exist on the raw event dict shape (`peak_datetime` is the real
   key, matching the convention every other Phase 4/5 scanner uses) --
   a `KeyError` on the very first live run. Fixed immediately.
2. Before wiring, confirmed `_natal_snapshot()` in
   `engine/predictive_sidecar.py` already expected a
   `payload.get("lots")` field from an earlier phase0/06 contract
   patch, but nothing computed it. Rather than inject lot computation
   into the shared natal-payload pipeline, added a scoped
   `_computed_lots()` helper inside the sidecar writer itself.

**Tests:** Added `tests/test_phase6_lots_zodiacal_releasing.py` (10
tests): the two chartered Lot fixtures bit-exact, missing-data graceful
handling for both Lots and ZR, the corrected 211-year Valens sum, the
Cancer-25-year L1 fixture from C5b section 12, peak-angularity
verification, L1/L2-only event emission, and sidecar natal_snapshot
integration.

**Verification:** 113 tests across the full relevant suite pass, no
regressions. Live-verified end to end on two different real charts
(not just the tests' synthetic fixtures) -- confirmed `natal_snapshot.lots`
populated, all six method families (`TRANSIT`, `LUNATION`, `RETURN`,
`SOLAR_ARC`, `PROGRESSION`, `ZODIACAL_RELEASING`) present in
`raw_events`, and `time_lord_periods` correctly split across
`annual_profection`, `zodiacal_releasing_fortune`, and
`zodiacal_releasing_spirit` systems.

**Files changed:** `engine/lots.py` (new), `engine/zodiacal_releasing.py`
(new), `engine/predictive_engine.py`, `engine/predictive_sidecar.py`,
`tests/test_phase6_lots_zodiacal_releasing.py` (new),
`phase0/03_method_charters.md` (246->211 fix).

---

## 2026-07-08 - Phase 5 method-charter review, before Codex implementation: phase0.1.1 -> phase0.1.2 (Claude / Sonnet 5)

**Context:** Ahead of Codex's Phase 5 (Solar Arc + Secondary
Progressions), Claude's method-charter review found C2 and C3 both
state a blanket orb/aspect policy without flagging that asteroid
contacts should defer to the registry's tighter per-tier values
instead (anchor tier: same 1.0° orb but conjunction-only for Solar
Arc; 0.5° orb, tighter than the 1.0° body-to-body ceiling, for
Progressions). Without that note, an implementer could reasonably
apply the wider blanket rule to asteroids too, understating the
intended precision bar for asteroid-based predictive claims. Fixed
in both C2 §5 and C3 §5 with a one-line precedence rule pointing at
`phase0/02_asteroid_predictive_registry.json`.

**Files changed:** `phase0/03_method_charters.md`.

---

## 2026-07-08 - Phase 4 method-charter review, before Codex implementation: phase0.1.0 -> phase0.1.1 (Claude / Sonnet 5)

**Context:** Ahead of the operator prompting Codex for Phase 4 (Returns
and Annual Profections), Claude did its Phase 4 method-charter review
per `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`'s Claude ownership
("verify that the returns and profections charter is complete enough
for implementation... do not edit code"), mirroring the pattern that
already caught real gaps ahead of Phases 2 and 3.

**One load-bearing gap found and fixed, affecting three charters:**

Neither C1 (Returns), C4 (Annual Profections), nor C5b (Zodiacal
Releasing, Phase 6) specified a value for `orb`, `distance`, or
`phase` on their emitted `ForecastEvent`s. `phase0/01_predictive_object_schemas.md`
§2 has a hard rule: every `ForecastEvent` must carry at least one of
those three fields, or the sidecar writer must reject it as malformed.
As charted, every return moment, every annual profection handoff, and
every ZR period transition would have been silently rejected the
first time the sidecar writer actually ran against them -- a blocker
that would only have surfaced at validation time, not at
implementation-read time.

**Fix:** all three now set `distance = 0.0` for their exact-moment
`ForecastEvent`s -- a genuine value (zero residual/zero deviation at
an astronomically exact instant), not a placeholder, and consistent
across all three charters so the convention doesn't fragment.

**Two smaller precision fixes, also patched:**

1. C1's independence-group enum trailed with an unexplained "..." for
   the "secondary" body return list (Mercury, Venus, Mars, Uranus,
   Neptune, Pluto, Chiron -- off by default in Phase 4). Clarified
   that if ever enabled, those collectively use
   `return_family_generic` (already reserved in
   `phase0/01_predictive_object_schemas.md` §9) rather than
   fragmenting into per-body groups ahead of demand.
2. C1's "chapter" role language could be read as the Return scanner
   constructing a `ChapterState` object directly. Clarified that the
   scanner only emits `ForecastEvent`s; promotion to a proper
   `ChapterState` (with the already-reserved `chapter_kind =
   "return_year"`) happens downstream in the shared chapter builder
   (`phase0/04_convergence_and_candidate_protocol.md` §8.1), not in
   the Return scanner itself.
3. C4's time-lord ruler table (`Mars, Venus, Mercury, Moon, Sun,
   Mercury, Venus, Mars, Jupiter, Saturn, Saturn, Jupiter`) was
   correct but unlabeled -- confirmed it's the classical/traditional
   domicile rulers in zodiacal sign order (Aries through Pisces), not
   a house-number lookup, and added that framing explicitly so a
   fast read can't misinterpret it as house-indexed.

**Files changed:** `phase0/03_method_charters.md`.

---

## 2026-07-08 - Phase 5 Solar Arc and secondary progressions evidence foundation (Codex / GPT-5)

**Context:** Initiated Phase 5 from the live post-Phase-4 worktree. The
implementation followed `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`, the C2
Solar Arc and C3 Secondary Progressions charters in
`phase0/03_method_charters.md`, and the evidence-object contracts in
`phase0/01_predictive_object_schemas.md`. Scope remained internal evidence
only; no client report prose or templates were changed.

**Solar Arc:** Added `engine/solar_arc.py`, implementing the single declared
Naibod-adjusted secondary-Sun Solar Arc convention:
`arc(t) = progressed_Sun.longitude(t) - natal_Sun.longitude`, with
progressed Sun using the one-ephemeris-day-per-year mapping. Directed sources
include natal planets, exact-birth-time angles, and anchor-tier asteroids
only where the Phase 3 asteroid registry permits source eligibility. Natal
targets include planets, angles, and registry-eligible asteroid targets.
Solar Arc events emit `method_family = "SOLAR_ARC"`,
`independence_group = "solar_arc_family"`, chartered activation routes, angle
confidence gating, and `[internal_rd, predictive_sandbox]` visibility.

**Secondary progressions:** Added `engine/progressions.py`, implementing the
classical one-ephemeris-day-per-year progressed chart constructor, progressed
planet contacts, exact-birth-time progressed angles, registry-gated anchor
asteroid compatibility, progressed ingresses, and progressed lunation phase
events. Progression events emit `method_family = "PROGRESSION"`,
`independence_group = "progression_family"`, chartered variants/routes, angle
confidence gating, and `[internal_rd, predictive_sandbox]` visibility.

**Integration:** Updated `engine/predictive_engine.py` to adapt Solar Arc and
secondary progression scanner events into predictive signals alongside the
existing transit, asteroid, return, and profection evidence. Updated
`engine/predictive_sidecar.py` to record Phase 5 scanner provenance through
`scan_solar_arc` and `scan_secondary_progressions` in `.eo_predictive.json`.
`ForecastEvent.natal_anchor_ids` remains empty; anchor matching is still
deferred to Phase 7.

**Tests:** Added `tests/test_phase5_solar_arc_progressions.py` covering Solar
Arc exact contact behavior, angle withholding under approximate birth time,
anchor-only asteroid source eligibility, secondary progressed chart date
mapping, progression/Solar Arc method-family separation, progressed-angle
gating, and sidecar serialization.

**Verification:** all of the following passed:

```powershell
python -m py_compile engine\solar_arc.py engine\progressions.py engine\predictive_engine.py engine\predictive_sidecar.py tests\test_phase5_solar_arc_progressions.py
python -m unittest tests.test_phase5_solar_arc_progressions tests.test_phase4_returns_profections tests.test_phase3_asteroid_predictive_activation tests.test_phase2_predictive_sidecar
$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_predictive_engine tests.test_phase2_predictive_sidecar tests.test_phase3_asteroid_predictive_activation tests.test_phase4_returns_profections tests.test_phase5_solar_arc_progressions
```

Base-Python focused runs log expected non-fatal skips for live Swiss
Ephemeris-dependent scanners when `swisseph` is unavailable. The venv-backed
run imports Swiss Ephemeris and completes `OK (skipped=1)`. The broader
predictive run still prints the pre-existing sandbox-template `signal_count`
traceback during one test path, but remains passing.

---

## 2026-07-08 - Phase 4 returns and annual profections evidence foundation (Codex / GPT-5)

**Context:** Initiated Phase 4 from the live post-Phase-3 worktree. The
implementation followed `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`, the C1
Returns and C4 Annual Profections charters in
`phase0/03_method_charters.md`, the `ForecastEvent` and `TimeLordPeriod`
contracts in `phase0/01_predictive_object_schemas.md`, and the program's
Phase 4 requirement that returns/profections become internal evidence rather
than client prose.

**Returns:** Added `engine/returns.py`, an event-level return scanner for
Solar, Lunar, Jupiter, and Saturn returns. It uses Swiss Ephemeris when
available, bisection to the chartered `0.01` degree tolerance, body-specific
scan steps/windows, and emits return scanner events with
`activation_route = "return_moment"`, body-specific return variants, exact
timestamps, confidence components, and `[internal_rd, predictive_sandbox]`
visibility. Return-chart interpretation is still deferred.

**Annual profections:** Added `engine/profections.py`, a whole-sign annual
profection period builder. It computes profected house, profected sign,
traditional domicile time lord, activated house topics, and a
`TimeLordPeriod` record with `system = "annual_profection"`,
`level = "year"`, `birth_time_dependency = "none"`, lord natal state, weight
modifier, confidence components, and `[internal_rd, predictive_sandbox]`
visibility. When the Ascendant sign is unavailable, it refuses to compute
rather than inventing a profection.

**Integration:** Updated `engine/predictive_engine.py` so return moments are
adapted into `RETURN` predictive signals and annual profections are exported
as `time_lord_periods`. Updated `engine/predictive_sidecar.py` so return
metadata, exact instants, explicit report-surface visibility, Phase 4 scanner
provenance, and `TimeLordPeriod` records are written into
`.eo_predictive.json`. No report templates or client prose were changed.

**Tests:** Added `tests/test_phase4_returns_profections.py` covering exact
return bisection with mocked longitude math, monotonic lunar return sequence,
annual profection house/sign/lord cycling, refusal without Ascendant sign, and
predictive-engine/sidecar export.

**Verification:** all of the following passed:

```powershell
python -m py_compile engine\returns.py engine\profections.py engine\predictive_engine.py engine\predictive_sidecar.py tests\test_phase4_returns_profections.py
python -m unittest tests.test_phase4_returns_profections tests.test_phase3_asteroid_predictive_activation tests.test_phase2_predictive_sidecar
$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_predictive_engine tests.test_phase2_predictive_sidecar tests.test_phase3_asteroid_predictive_activation tests.test_phase4_returns_profections
```

The no-venv focused test pass logs non-fatal return-scanner skips because
`swisseph` is unavailable to that Python; the venv-backed pass exercises live
Swiss Ephemeris imports. The broader predictive run still prints the
pre-existing sandbox-template `signal_count` traceback during one test path,
but completes `OK (skipped=1)`.

---

## 2026-07-08 - Phase 3 all-34 asteroid predictive activation foundation (Codex / GPT-5)

**Context:** After both parallel Phase 2 lanes completed and the Phase 2
body-classification blocker was fixed, Codex initiated the Phase 3
implementation lane from the refreshed `phase0.1.1` asteroid registry.
Claude's Phase 3 registry review had already moved Sirene/Themis source
restrictions into structured policy fields and added explicit
proprietary-transit normalization guidance.

**Implementation:** Added `engine/asteroid_policy.py`, a machine-readable
registry loader and policy API that validates exactly 34 asteroid records,
enforces required fields, exposes source/target/clock eligibility, preserves
the migration-map target weights for the existing eight anchor asteroids,
and evaluates the structured Sirene/Themis `{allowed_aspects,
restricted_targets}` rules directly. Updated `engine/predictive_engine.py`
so the existing `scan_proprietary_forecast_windows()` output can be adapted
into internal R&D evidence behind `options["enable_asteroid_rd"]`,
`options["include_proprietary_asteroids"]`, `EO_ASTEROID_RD=1`, or
`EO_PREDICTIVE_ASTEROID_RD=1`. The adapter preserves the scanner's existing
triggers, orbs, weights, and scores while normalizing events as
`method_family = "PROPRIETARY_TRANSIT"`, lowercase formula-group
`method_variant`, and `independence_group = "proprietary_transit_family"`.

**Sidecar:** `engine/predictive_sidecar.py` now preserves asteroid
topic/domain keys, per-signal asteroid policy traces, proprietary scanner
gate state, and registry-declared asteroid diagnostics. Sidecar inclusion
remains separate from client prose; no templates or consumer report prose
were changed.

**Tests:** Added `tests/test_phase3_asteroid_predictive_activation.py`
covering exact all-34 registry loading, required fields, migration-map
weights, Sirene/Themis restriction checks, R&D gate behavior,
`PROPRIETARY_TRANSIT` signal normalization, and sidecar provenance.

**Verification:** all of the following passed:

```powershell
python -m py_compile engine\asteroid_policy.py engine\predictive_engine.py engine\predictive_sidecar.py tests\test_phase3_asteroid_predictive_activation.py
python -m unittest tests.test_phase3_asteroid_predictive_activation tests.test_phase2_predictive_sidecar
$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_predictive_engine tests.test_phase2_predictive_sidecar tests.test_phase3_asteroid_predictive_activation
```

The broader focused run still prints the pre-existing sandbox-template
`signal_count` traceback during one test path, but the suite completes
`OK (skipped=1)`.

---

## 2026-07-07 - Phase 2 sidecar body-classification blocker fixed (Codex / GPT-5)

**Context:** Before Phase 3 implementation, Claude flagged
`PHASE2_SIDECAR_BODY_CLASSIFICATION_FINDING.md` as a hard blocker:
the Phase 2 sidecar writer classified any body outside the known
planet/node/angle lists as `"asteroid"`, which would corrupt eclipse
labels such as `Solar`/`Lunar`, calculated points such as `Lilith_BML`,
and Phase 3's all-asteroid accounting.

**Fix:** `engine/predictive_sidecar.py` now derives asteroid identity
from the actual `payload["custom_asteroids"]` key set. Unknown labels
remain `"unknown"`, `Lilith_BML` is treated as a calculated point, and
real custom asteroid keys still receive asteroid participants,
asteroid specificity, diagnostics counts, and sidecar surface
visibility. The sidecar contract version was bumped to `phase0.1.1`
while individual `ForecastEvent` and `PredictiveSignal` object schema
versions remain `phase0.1.0`, matching the refreshed phase0 contracts.

**Verification:** all of the following passed:

```powershell
python -m py_compile engine\predictive_sidecar.py tests\test_phase2_predictive_sidecar.py
python -m unittest tests.test_phase2_predictive_sidecar
$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_phase1_client_forecast_adequacy tests.test_phase2_predictive_sidecar
```

---

## 2026-07-07 - Phase 3 asteroid registry review, before Codex implementation: phase0.1.0 -> phase0.1.1 (Claude / Sonnet 5)

**Context:** Ahead of handing Codex the Phase 3 prompt, the operator
asked Claude to do its Phase 3 registry review now (per
`EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`'s Claude ownership: "asteroid
policy review and missing-field queue") rather than after Codex starts
coding from `phase0/02_asteroid_predictive_registry.json`, mirroring
the Phase 2 pattern that already caught two real gaps before
implementation began.

**Three findings, all patched, both registry files bumped `phase0.1.0`
-> `phase0.1.1`:**

1. **Unstructured source-eligibility overrides.** Sirene and Themis
   each had a `source_eligibility_override.transit` value that was a
   free-text condition string (e.g.
   `"conjunction_only_when_aspecting_angle_or_Venus"`) with no defined
   grammar. A registry-driven policy API needs something directly
   checkable, not prose to parse. Fixed: both now use a structured
   `{allowed_aspects: [...], restricted_targets: [...]}` shape --
   Sirene restricted to angles + Venus, Themis restricted to Destinn
   only -- so the policy API can do a plain membership check.
2. **Undocumented `method_variant` for proprietary-transit events.**
   `phase0/01_predictive_object_schemas.md`'s `ForecastEvent.method_family`
   already has a dedicated `PROPRIETARY_TRANSIT` value, but nothing
   specified what `method_variant` those events should carry, and
   `phase0/03_method_charters.md` has no chartered section for
   proprietary asteroid transits (it covers C1-C6; this is Workstream
   B territory, never given its own charter number). Added
   `forecast_event_normalization_guidance` to the registry: use the
   lowercase formula_group name (`disruption` / `sovereignty` /
   `catalyst`) as `method_variant`, `PROPRIETARY_TRANSIT` as
   `method_family`, `proprietary_transit_family` as
   `independence_group`. Flagged as a stopgap worth promoting to a
   real charter section later if the asteroid-transit method grows
   beyond the three existing formula groups.
3. **Stale field-path reference.** The narrative doc's "ephemeris
   resilience" rule pointed to `debug.asteroids_ephemeris_missing`,
   which does not exist in `phase0/06_sidecar_and_export_contract.md`
   -- the real field is `asteroid_diagnostics.ephemeris_missing`.
   Confirmed via Codex's live Phase 2 sidecar output, which already
   implements the correct path (and surfaced a real observed case:
   `Anubis`'s ephemeris file is unavailable in this local environment).
   Fixed the reference and clarified that a per-chart ephemeris
   failure is not a "silent disappearance" violation of the registry's
   own rule -- the asteroid is declared and its absence is explicit
   and traceable, not scanner oversight.

**Also confirmed, not a gap:** the Phase 2 body-classification finding
(`PHASE2_SIDECAR_BODY_CLASSIFICATION_FINDING.md`) is directly enabling
for Phase 3, not just blocking it -- the recommended fix (check
`payload["custom_asteroids"].keys()` instead of guessing "asteroid" by
exclusion) is exactly what Phase 3 needs to correctly classify all 34
asteroids as sources/targets, not just the 8 already wired in
`scan_proprietary_forecast_windows()`. Should land before Phase 3
implementation begins.

**Files changed:** `phase0/02_asteroid_predictive_registry.json`,
`phase0/02_asteroid_predictive_registry.md`.

---

## 2026-07-07 - Phase 2 contract-conformance patch: phase0.1.0 -> phase0.1.1 (Claude / Sonnet 5)

**Context:** Immediately after operator sign-off on `phase0/`, Claude
Code began its Phase 2 lane per `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`
("audit phase0/01_predictive_object_schemas.md and
phase0/06_sidecar_and_export_contract.md for field completeness before
Codex implements the sidecar"). This is exactly what Phase 2 Claude
review is for, done same-day and before any evidence there of Codex
having started coding from these files, per the Safe Parallel Run
Matrix's condition ("Yes, if Claude does not edit phase0/ while Codex
is coding from it").

**Two gaps found and patched, both files bumped `phase0.1.0` ->
`phase0.1.1`:**

1. **No home for computed natal Lot positions.** Lots (Fortune,
   Spirit, Necessity) are natal-chart-derived points, but neither
   `NatalPromiseAnchor` nor the sidecar's `natal_snapshot` had
   anywhere to store them — every other referenceable point (planets,
   asteroids, angles) had a canonical home; Lots did not. This would
   have blocked Phase 6 Codex with nowhere defined to resolve
   `ForecastEvent`s with `source_kind`/`target_kind = "lot"` against.
   Fixed: added `NatalPromiseAnchor.natal_lots` and
   `natal_snapshot.lots` (canonical home, same shape as an `angles`
   entry plus a `sect` field).
2. **`TimeLordPeriod` missing `report_surface_visibility`.** Every
   sibling evidence object (`ForecastEvent`, `ChapterState`,
   `MicroCandidate`) has this field for client/report gating;
   `TimeLordPeriod` did not, despite the profections charter
   (`phase0/03_method_charters.md` §C4) explicitly anticipating a
   Phase 10 Year Ahead promotion decision this field is needed to
   gate. Fixed: added the field, defaulting to
   `[internal_rd, predictive_sandbox]`.

**Versioning:** per-object, not global — only `NatalPromiseAnchor` and
`TimeLordPeriod` moved to `phase0.1.1` (each gained one field);
`ForecastEvent`, `PredictiveSignal`, `ChapterState`, `MicroCandidate`
are unchanged and remain `phase0.1.0`. Both fields default to safe,
inert values, so this patch changes nothing for Phases 2-5 — it only
closes a gap Phase 6 would otherwise have hit.

**Files changed:** `phase0/01_predictive_object_schemas.md`,
`phase0/06_sidecar_and_export_contract.md`.

---

## 2026-07-07 - Phase 0 predictive architecture contracts approved (operator sign-off)

**Context:** `phase0/` (README, predictive object schemas, asteroid
predictive registry, method charters, convergence and candidate
protocol, validation protocol, sidecar and export contract, versioning
and regression fixtures) was drafted and corrected across two Claude
Code sessions on 2026-07-07, including a correction to the discrete
candidate window rule (trigger-derived, not a fixed six-day maximum,
which was only ever meant as `predictive_sandbox`'s own internal
research cap).

**Decision:** the operator explicitly approved the `phase0/` contracts
as final, satisfying `phase0/README.md`'s "Definition of Phase 0 done"
sign-off requirement and `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`'s
Phase 0 Gate. Phase 2 (predictive evidence infrastructure) may now
begin implementation directly against these contracts for both the
Codex and Claude Code lanes.

**Also resolved this session:** the one open item from
`CLIENT_FORECAST_CLAIM_CLEANUP_QUEUE.md` (the "personal progressions"
overclaim on `entangled_oracle_SITE.html`'s Year Ahead card) was fixed
directly at the operator's request — see that file for detail. The
queue is now fully closed.

---

## 2026-07-07 - Phase 2 predictive evidence sidecar foundation (Codex / GPT-5)

**Context:** The user confirmed Phase 0 contract sign-off and initiated
Phase 2 after both systems completed their Phase 1 lanes. Claude Code is
handling the Phase 2 contract-review prompt; this Codex pass implemented
the additive evidence sidecar lane only.

**What changed:**

- Added [engine/predictive_sidecar.py](C:/entangled_oracle/engine/predictive_sidecar.py), a dedicated writer for
  `.eo_predictive.json` sidecars defined by the Phase 0 sidecar/export
  contract.
- Added a `ForecastEvent` adapter for current transit-backed predictive
  signals. This creates deterministic `fe_*` event IDs, preserves method
  family, method variant, source/target, timing, orb/phase, strength
  components, confidence components, independence group, activation route,
  and provenance.
- Added a `PredictiveSignal` adapter that preserves source event linkage,
  signal role, operation profile, epistemic confidence, dates, and
  formula/policy versions.
- Added daily contributor provenance: each daily row now records
  contributing signal IDs, contributing event IDs, and structural versus
  trigger contributors in the sidecar.
- Added immutable natal snapshot, environment, policy-version,
  detector-threshold, asteroid-diagnostic, debug, and provenance sections
  to the sidecar shape.
- Wired predictive report generation so `year_ahead`,
  `personal_forecast`, and `predictive_sandbox` write a sibling
  `.eo_predictive.json` after the normal HTML and delivery manifest are
  written. Sidecar failure remains non-fatal to report delivery.

**Files changed by this Codex pass:**

- [engine/predictive_sidecar.py](C:/entangled_oracle/engine/predictive_sidecar.py)
- [generate.py](C:/entangled_oracle/generate.py)
- [tests/test_phase2_predictive_sidecar.py](C:/entangled_oracle/tests/test_phase2_predictive_sidecar.py)

**Verification:**

- `python -m py_compile engine\predictive_sidecar.py generate.py tests\test_phase2_predictive_sidecar.py`
- `python -m unittest tests.test_phase2_predictive_sidecar`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_daily_horoscope_activation tests.test_phase1_client_forecast_adequacy tests.test_phase2_predictive_sidecar`

Result:

- `22` focused tests passed.

**Deliberately not implemented in Phase 2:** no new method clocks, no
progressions, no Solar Arc, no returns, no profections, no time-lord
systems, no Lots, no Zodiacal Releasing, no discrete candidate engine,
and no client-facing prose promotion. This phase is the evidence runway
for those later required phases.

**Coordination note:** `phase0/01_predictive_object_schemas.md` and
`phase0/06_sidecar_and_export_contract.md` were already modified in the
worktree by the parallel Claude/contract lane and were not edited by this
Codex implementation pass.

---

## 2026-07-07 - Phase 1 client forecast adequacy repairs (Codex / GPT-5)

**Context:** The user approved implementing Phase 1 from
`EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md` while Claude Code handled the
Claude-side prompt lane. This pass stayed inside the client forecast
adequacy scope from `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md` and did
not add advanced method clocks.

**What changed:**

- Daily Horoscope date control now follows the requested report date
  instead of switching back to the system date inside
  `selectors/variable_resolver.py`.
- Daily display date, day ruler, Moon phase, sky Moon sign/element, station
  scan window, and same-day activation scan now all derive from the
  report start date.
- Daily template sky copy now uses the calculated sky Moon sign while
  preserving the natal Moon sign as a fallback.
- Weekly Horoscope keeps the engine's ranked top-moment selection, then
  renders those selected exact contacts in chronological order and labels
  the section as selected exact contacts rather than an unqualified
  timeline.
- Personal Forecast timing dots now use each event's real position inside
  the 90-day report window instead of even loop-index spacing.

**Files changed:**

- [selectors/variable_resolver.py](C:/entangled_oracle/selectors/variable_resolver.py)
- [generate.py](C:/entangled_oracle/generate.py)
- [products/daily_horoscope/templates/daily_horoscope.html](C:/entangled_oracle/products/daily_horoscope/templates/daily_horoscope.html)
- [products/weekly_horoscope/templates/weekly_horoscope.html](C:/entangled_oracle/products/weekly_horoscope/templates/weekly_horoscope.html)
- [products/personal_forecast/templates/personal_forecast.html](C:/entangled_oracle/products/personal_forecast/templates/personal_forecast.html)
- [tests/test_daily_horoscope_activation.py](C:/entangled_oracle/tests/test_daily_horoscope_activation.py)
- [tests/test_phase1_client_forecast_adequacy.py](C:/entangled_oracle/tests/test_phase1_client_forecast_adequacy.py)

**Verification:**

- `python -m py_compile generate.py selectors\variable_resolver.py tests\test_daily_horoscope_activation.py tests\test_phase1_client_forecast_adequacy.py`
- `$env:PYTHONPATH='C:\entangled_oracle\.venv\Lib\site-packages'; python -m unittest tests.test_daily_horoscope_activation tests.test_phase1_client_forecast_adequacy`

Result:

- `17` focused tests passed.

**Still out of scope:** Weekly Horoscope still needs a real authored
interpretive content layer before it should be treated as a mature client
narrative product. Progressions, Solar Arc, returns, profections, time
lords, Lots, Zodiacal Releasing, and discrete candidate research remain
required later phases, not Phase 1 work.

---

## 2026-07-06 - Predictive Sandbox heavy audit and targeted repair pass (Codex / GPT-5)

**Context:** The user asked for a heavy code audit and repair pass over
`predictive_sandbox`, explicitly excluding the full activation pipeline
because the local environment is unstable. The pass focused on source
truth: engine mechanics, sandbox routing, tests, JSON library shape, and
agent-note accuracy.

**Audit ledger:**

- **confirmed:** method normalization, episode memory, FSM / hysteresis
  lifecycle fields, signal operation profiles, target-sensitive aspect
  bias, and sandbox context forwarding are present in code.
- **confirmed:** window semantic diagnostics now include coherence plus
  bounded `polarity`, `coalition`, `counterforce`, and `complexity`.
- **confirmed:** qualified lunation scanning exists and is wired with
  eclipse duplicate suppression.
- **confirmed:** the sandbox JSON library now loads from the flat
  `products/predictive_sandbox/blocks/` registry rather than the deleted
  `predictive_window_blocks.json` file.
- **partial:** confidence is not full interval sampling yet.
  `relation_robustness` still includes an exactness-derived term, with
  target uncertainty applied as a modifier.
- **partial:** sandbox-native content wins eligible ties, but content
  coverage is still uneven and legacy converted blocks remain a valid
  fallback.
- **not implemented:** exact returns, Solar Arc, progressions, Relay
  Gate, Structural Shear, and pathway topology.

**What changed in code and tests:**

- Removed the stale `_PREDICTIVE_SANDBOX_BLOCK_PATH` constant from
  [generate.py](C:/entangled_oracle/generate.py); the single JSON file it
  referenced has been deleted and is no longer the active loader path.
- Added `TestLunationClockFamily` and the previously omitted
  `TestPredictivePhaseFSM` to the manual
  [tests/test_predictive_engine.py](C:/entangled_oracle/tests/test_predictive_engine.py)
  runner so direct file execution matches normal unittest discovery more
  closely.
- Added JSON-library guard tests requiring active blocks to meet the
  minimum schema and route only on fields exposed by sandbox window
  context.
- Added a direct `method_family` routing test so
  method-family-conditioned blocks cannot silently become unreachable
  again.

**What changed in source-of-truth docs:**

- [ARCHITECTURE.md](C:/entangled_oracle/ARCHITECTURE.md) now describes
  polarity / coalition / counterforce / complexity and qualified
  lunations as current implemented mechanics, while preserving the
  warning that full interval-sampled confidence is not implemented yet.
- [agents/PLANNED_UPDATES.md](C:/entangled_oracle/agents/PLANNED_UPDATES.md)
  now has a current audit ledger and no longer treats landed lunation and
  semantic diagnostic work as future-only.

**Boundary preserved:** no dependency installs, no activation-pipeline
audit, no Relay / Shear / topology expansion, and no content rewrite
based only on observed PDF symptoms.

**Verification:** the default `python` still does not see the repo
packages directly, and the `.venv` executable is blocked with
`Access is denied` from this sandbox. Using the default Python with
`PYTHONPATH=C:\entangled_oracle\.venv\Lib\site-packages`, both focused
paths passed:

- `python -m unittest tests.test_predictive_engine`
- `python tests\test_predictive_engine.py`

Result: `76` tests run, `OK`, `1` skipped.

## 2026-07-06 - Predictive Sandbox testing-resumption notes synced in agents files (Codex / GPT-5)

**Context:** After the `v0.3.1` signal-level and window-level semantic
passes landed, the user asked what the cleanest next steps would be to
get `predictive_sandbox` upgraded enough to resume meaningful testing,
then asked for the relevant `agents/` files to be brought fully up to
date.

**What actually changed in the repo this pass:** agent notes only. No
runtime code, templates, engine logic, or tests were modified. The
update landed in:

- [agents/REVISIONS.md](C:/entangled_oracle/agents/REVISIONS.md)
- [agents/PLANNED_UPDATES.md](C:/entangled_oracle/agents/PLANNED_UPDATES.md)

**What was clarified for source-of-truth planning:**

- the most direct next move for testing-readiness is still
  **interval-aware epistemic robustness first**
- after that, the next bounded testing-value layer is additional window
  semantics:
  `polarity`, `coalition`, `counterforce`, `complexity`
- only after those are stable should the sandbox widen into an added
  method family such as lunations/eclipses
- relay / shear / topology remain explicitly deferred until those prior
  layers are fixture-supported

**Why this matters:** the sandbox now has enough structure that the
remaining question is no longer "what should predictive work become in
the abstract?" but "what is the smallest next engine addition that makes
testing honest again?" This note locks in that answer so a later session
does not skip from fresh semantic scaffolding straight into topology or
macro-method sprawl.

## 2026-07-06 - Predictive Sandbox v0.3.1 second slice implemented: window-level semantic aggregation (Codex / GPT-5)

**Context:** After the first `v0.3.1` pass added bounded signal-level
operation profiles and confidence scaffolding, the user asked to keep
going. The next honest slice was to aggregate those signal semantics at
the window layer without jumping to new clocks, relay logic, Structural
Shear, or topology.

**What actually changed in code:**

- [engine/predictive_engine.py](C:/entangled_oracle/engine/predictive_engine.py)
- [generate.py](C:/entangled_oracle/generate.py)
- [tests/test_predictive_engine.py](C:/entangled_oracle/tests/test_predictive_engine.py)
- [ARCHITECTURE.md](C:/entangled_oracle/ARCHITECTURE.md)
- [agents/PLANNED_UPDATES.md](C:/entangled_oracle/agents/PLANNED_UPDATES.md)

**What this second slice now concretely includes:**

- Window-level semantic aggregation from the existing per-signal
  `operation_profile` fields.
- A real engine-derived `coherence` value for windows when semantic
  signals are present, instead of a placeholder.
- Window-level:
  `semantic_profile`, `dominant_operation`, `semantic_state`, and
  `semantic_diagnostics`.
- Compatibility scoring that stays bounded and auditable: it compares
  declared dominant operations rather than downstream prose.
- Interpretive tags now reflect semantic state and dominant operation,
  but remain derived from engine evidence rather than invented by the
  renderer.

**What was deliberately *not* implemented yet:**

- interval-sampled epistemic robustness
- macro-method additions like lunations, returns, Solar Arc, or
  progressions
- coalition / counterforce / complexity metrics
- Relay Gate / Target Continuity
- Structural Shear
- pathway topology

That boundary was kept on purpose. This pass aggregates the semantic
signals already present; it does not widen the theoretical scope.

**Tests and verification:** focused predictive coverage was extended to
include:

- single-signal coherence population
- low-coherence conflicting-pressure fixtures
- high-coherence reinforcing fixtures
- sandbox-context forwarding of the new window semantic fields

Verified locally with:

- `python -m unittest tests.test_predictive_engine`

Result at closeout:

- `66` tests run
- `OK`
- `4` skips

The same non-fatal local Codex-environment warnings remained for missing
`swisseph` and `jinja2`; the focused predictive suite still passed
cleanly.

**Why this matters:** the predictive sandbox now has its first real
window-level semantic metric, and `coherence` finally means something
computed from operation structure rather than from placeholder nulls or
future intent. That is a meaningful step forward, while still staying
inside the user’s rule not to outrun auditable mechanics with semantic
theory.

## 2026-07-06 - Predictive Sandbox v0.3.1 first slice implemented: operation vectors + confidence scaffolding (Codex / GPT-5)

**Context:** The user asked to continue `predictive_sandbox` from the
newly completed `v0.3` core, but with a strict rule: do not outrun
auditable mechanics with semantic theory. The requested order was
explicit: implement the semantic atomic layer first, prioritizing
Aspect Bias Operator, target-sensitive operation vectors, and epistemic
confidence scaffolding, while continuing to defer relay, shear,
topology, and renderer inflation.

**What actually changed in code:**

- [engine/predictive_engine.py](C:/entangled_oracle/engine/predictive_engine.py)
- [generate.py](C:/entangled_oracle/generate.py)
- [tests/test_predictive_engine.py](C:/entangled_oracle/tests/test_predictive_engine.py)
- [ARCHITECTURE.md](C:/entangled_oracle/ARCHITECTURE.md)
- [agents/PLANNED_UPDATES.md](C:/entangled_oracle/agents/PLANNED_UPDATES.md)

**What `predictive_v0.3.1` now concretely includes:**

- A bounded signal-level semantic atomic layer with explicit operation
  axes:
  `stabilize`, `amplify`, `activate`, `disrupt`, `dissolve`, `reveal`
- Source-body operation bases for the currently active predictive
  bodies, rather than free-form semantic tagging.
- Target-sensitive substrate shaping so the same source/aspect/method
  can produce a materially different operation profile depending on the
  natal target class.
- Aspect Bias Operator mechanics that bias operation mass by aspect
  geometry before any coherence or coalition math is attempted.
- Method-behavior multipliers kept light and explicit; this stays a
  bounded per-signal profile, not a narrative system.
- Epistemic confidence scaffolding at the signal level:
  `epistemic_confidence`, `confidence_components`,
  `confidence_state`, and `angle_eligibility`.
- Exact-birth-time gating for angle-sensitive signals so they fail
  gracefully instead of pretending equal confidence.
- Sandbox context forwarding of the new signal diagnostics without
  upgrading the renderer into a broader interpretive layer.

**What was deliberately *not* implemented yet:**

- window-level coherence math
- coalition / counterforce metrics
- Relay Gate / Target Continuity
- Structural Shear
- pathway topology
- interval-sampled confidence robustness
- expanded sandbox prose or report-grade renderer logic

That was intentional. The slice stops at auditable signal semantics and
confidence edges.

**Tests and verification:** focused predictive coverage was extended to
include:

- target-sensitive operation-profile non-regression fixtures
- aspect-bias profile differentiation fixtures
- angle-confidence withholding fixtures for reduced birth-time states
- sandbox-context forwarding fixtures for the new signal fields

Verified locally with:

- `python -m unittest tests.test_predictive_engine`

**Why this matters:** `predictive_sandbox` now has a real first semantic
atomic layer rather than empty placeholders, but it still stays inside
the user’s requested guardrail. The engine can express *how* a signal is
acting and *how trustworthy* that edge is without claiming higher-order
coherence, relay, or topology that have not been fixture-supported yet.

## 2026-07-06 - Predictive Sandbox v0.3 core implemented: method normalization, episode memory, and FSM hysteresis (Codex / GPT-5)

**Context:** After the earlier planning-only pass for `predictive_sandbox`,
the user explicitly asked to move from architecture into implementation,
while still keeping the work engine-first and auditably bounded. The
governing constraint remained the same: make the predictive engine more
multi-clock and lifecycle-aware **without** letting semantic/pathway
theory outrun trustworthy mechanics.

**What actually changed in code:**

- [engine/predictive_engine.py](C:/entangled_oracle/engine/predictive_engine.py)
- [generate.py](C:/entangled_oracle/generate.py)
- [tests/test_predictive_engine.py](C:/entangled_oracle/tests/test_predictive_engine.py)

**What `predictive_v0.3` now concretely includes:**

- Predictive signal normalization into:
  `method_family`, `event_kind`, `independence_group`, and
  `activation_route`.
- A memory layer that is episode-based rather than duration-in-orb based.
- Window-level memory diagnostics:
  `memory`, `memory_state`, `activation_key`, `pass_state`,
  `lifecycle_route`.
- A real finite state machine for phase continuity, including hysteresis
  via an expanded exit orb. `pass_state` is no longer inferred from a
  peak-position gradient alone; it is replayed chronologically per
  activation route/history.
- New FSM states carried by sandbox windows:
  `PRELUDE`, `APPROACH`, `EXACTNESS`, `AFTERMATH`,
  `RETROGRADE_REVIEW`, `RESOLUTION`, `RESIDUAL_FIELD`.
- Context-builder forwarding of the new signal/window diagnostics into
  the predictive sandbox render context.

**What was deliberately *not* implemented yet:**

- real coherence / polarity / coalition / counterforce math
- operation-vector semantics / Aspect Bias Operator
- target continuity / Relay Gate
- Structural Shear
- interval-sampled epistemic confidence
- active pathway topology
- renderer redesign or report-grade interpretive expansion

That deferral was intentional. The session explicitly prioritized
load-bearing timing mechanics before topology and semantic theory.

**Tests and verification:** focused predictive-engine coverage was
extended to include:

- method normalization fixtures
- numeric memory population fixtures
- FSM hysteresis / non-regression fixtures:
  no flicker back to `PRELUDE`, retrograde review requires prior exact
  hit, residual field requires post-exactness routing

Verified locally with:

- `python -m unittest tests.test_predictive_engine`

Result at closeout:

- `59` tests run
- `OK`
- `4` skips

The Codex runtime still emitted non-fatal warnings for missing
`swisseph` and `jinja2`, but the user clarified those are locally
installed outside the Codex environment and the focused suite still
passed cleanly.

**Why this matters:** this closes the original `v0.3` upgrading goal in
an honest way. The predictive sandbox is no longer just transit windows
with louder labels; it now has normalized evidence categories, episode
memory, and lifecycle continuity enforced by state transitions instead of
gradient guesswork.

---

## 2026-07-06 - Predictive Sandbox v0.3 planning update: engine-first, render-constrained (Codex / GPT-5)

**Context:** The user asked to push the `predictive_sandbox` lane forward,
but explicitly wanted the next phase framed around the **maximum viable
formulaic and engine expansion** first, not around JSON shape or renderer
copy. Two local Word docs were reviewed during the session:

- `Professional_Astrological_Calculation_System_v2 (1).docx`
- `Entangled_Oracle_Proprietary_Predictive_Formulas_Experimental_v0.1.docx`

The second doc turned out to be the more direct architectural guide for
next steps; the first remains useful as a payload/math substrate audit.

**What was actually changed in the repo this pass:** planning and
architecture notes only. No runtime code, templates, formulas, or tests
were modified. The update landed in:

- `agents/PLANNED_UPDATES.md`
- `ARCHITECTURE.md`

**Planning decisions now recorded as source-of-truth:**

- `predictive_v0.3` should start with method normalization + episode
  memory + sandbox macro clocks, not with renderer expansion.
- `station` and `ingress` are active predictive routes but **not**
  independent chorus clocks; they must normalize under the transit clock.
- `eclipse` remains active but must not create a duplicate diversity vote
  alongside the plain lunation record for the same astronomical event.
- proprietary asteroid/component routing is an activation route, not a
  timing family.
- memory remains episode-based rather than orb-duration-based.
- coherence must be computed from declared operation compatibility, not
  from prose resemblance or renderer wording.
- houses stay contextual modifiers first, not primary predictive targets
  in this phase.
- high-polarity Crucibles remain intense; coherence must never function
  as an intensity downgrade.

**Short pre-render constraint pass was also locked in before deeper
implementation work:** renderer output must preserve the separation of
`intensity`, `coherence`, `memory`, and `gradient`; sandbox-only
classifications may exist later but only with evidence and explicit
provisional labeling; raw evidence and formula traceability remain
visible somewhere in sandbox output.

**Why this matters:** the repo already has a real `predictive_v0.2`
engine (`engine/predictive_engine.py`) with transit-derived signals,
baseline/residual window segmentation, `leading_index`, `gradient`, and
placeholder `coherence` / `memory` fields. The planning update turns the
next step into a bounded engineering problem instead of a loose
"predictive ideas" cloud.

**Deliberately left alone:** no attempt was made yet to implement the
new method taxonomy, episode ledger, Solar Arc / progression sandbox
clocks, lunation routing, return events, semantic coalition metrics, or
pathway stubs. This was a planning/architecture stabilization pass, not
a code pass.

---

## 2026-07-04/05 - Weekly Horoscope: new report type, foundation-only, wired end to end (Claude / Sonnet 5)

**Context:** User wants weekly horoscopes as a stepping stone toward B2B
group products (classes, programs, recovery groups). Explicitly scoped as
wiring/foundation only for this pass - content blocks and tiering were
deferred on purpose, and the user was clear content packs are still being
actively refined separately.

**What "exact time" means here:** clarified by the user mid-session - it
means the querent's *exact birth time is known* (vs. DOB-only `--simple`
mode), not a claim about minute-precision transit timing. That distinction
already existed in the codebase (`simple_mode`, used by Daily Horoscope's
`include_angles` gating) - no new toggle was needed, just reuse.

**Wiring added:** a sixth report type, `weekly_horoscope`, plumbed through
every layer that the existing five already touch: CLI `choices`,
`config.py` (`REPORT_BLOCK_DIRS`), `product_versions.py`
(`REPORT_TYPE_VERSIONS`, `TEMPLATE_MAP`, `_report_block_paths`),
`generate.py`'s `build_report_context` dispatch and `render_template`'s
local template map, plus a new `products/weekly_horoscope/` directory
(`blocks/` empty for now, a minimal stub `templates/weekly_horoscope.html`
that lists computed timeline moments with no prose).

**Engine reuse, not new engine work:** `_build_weekly_horoscope_context()`
calls the existing `engine/transit_engine.py`'s `compute_daily_timeline()`
unmodified, pointed at a multi-day window instead of a single day. That
function was already fully date-range-agnostic (built during the Daily
Horoscope "Today's Timeline" work, 2026-07-02) - no engine changes were
needed to generalize it to a week. `include_angles=not simple_mode` reuses
the exact-vs-simple gating described above.

**Bug caught during verification:** the template initially read "your
your Sun" for angle targets - `_target_display()` in transit_engine.py
already prepends "your" (e.g. "your Ascendant"), so the template's own
"your" prefix was a duplicate. Fixed by trusting the engine's display
string as-is.

**Calendar-week alignment (added same session, after user follow-up):**
initially shipped as a rolling 7-day window from generation time; user
asked for Monday-Friday calendar alignment as the default instead, with
clinical/theory/off-day custom schedules flagged as a likely later ask.
Added `_align_to_week_start()` (rounds back to the Monday 00:00 UTC of the
calendar week containing `report_start`) and `_report_window()` (returns
Monday through the following Saturday 00:00 UTC - i.e. a Mon-Fri window -
for `weekly_horoscope`; unchanged 1-year window for every other report
type). This means a whole cohort generated together, regardless of what
moment generation actually runs at, shares identical week boundaries -
which matters for the B2B batch-export model described below. Verified
live: a report generated on a Saturday correctly aligned to that same
week's Monday-Friday, with the header showing the right date range and
zero timeline moments falling on the excluded Sat/Sun.

**B2B distribution model (learned from user, not yet built):** the
intended workflow once a partner agreement exists is a **batch export**,
not a live API - bulk-generate every cohort member's weekly report and
hand the educator/institution a single file/batch to send out themselves
each week. No batch/bulk generation entry point exists yet (today's
`generate.py` is one querent per CLI invocation); see Planned Updates.

**Verified via live CLI runs** (exact-time and `--simple`, plus a
post-alignment run), output HTML inspected directly, test artifacts
cleaned up afterward. No test files written for the new context builder
or window-alignment helpers - flagged in Planned Updates.

---

## 2026-07-04 - Year Ahead PDF: from "web dashboard exported to PDF" toward book-like pagination (Claude / Sonnet 5)

**Context:** User asked for an implementation audit of the Year Ahead PDF
pipeline first (no code changes), then three sequential, explicitly-scoped
passes against the findings. All work touched exactly one file across all
three passes: `products/year_ahead/templates/active/year_ahead.html`. No
calculation logic, JSON schemas, content/text, or other report type was
touched at any point. Title page/frontispiece work was explicitly deferred
by the user each time and remains undone (see Planned Updates).

**Audit finding (no code changed):** the template's print pagination was
governed by four separate, overlapping `@media print` blocks written at
different times ("PDF print recovery," an orphaned one-line block,
"reader-first v2 print recovery," "Browser print"), several directly
contradicting each other on the same selectors (`.month-section`,
`.event-card`, a self-contradicting `.chronology-divider` inside one
block). `.section { break-before: page }` forced every one of 13 sections
onto a fresh page regardless of remaining space - the primary source of
large trailing blank areas. A structural bug was also found: the "Monthly
Chapters" section wrapper contains only a header (the 12 actual
`.month-section` chapters are siblings outside it), so it was rendering as
a near-empty page under the old forced-break rule.

**Phase 0 - consolidation (stabilization only, no visual redesign):**
Merged all four print blocks into one authoritative `@media print` block,
organized under labeled sections (page geometry, global flow, intentional
chapter starts, protected indivisible units, table behavior, color/print
rendering). Genuine break-behavior conflicts were resolved per explicit
user-given rules (long prose flows naturally; event cards split only to
avoid stranding whitespace; headings stay with their first line; no
element forced to break merely for being a generic card/section; hard
breaks reserved for explicitly named boundaries) rather than by source
order. Dropped the blanket `.section`/`.month-section` forced-break rule
and one internal self-contradiction on `.chronology-divider`. All color,
geometry, and typography values were carried over as-is - visually
unchanged. Verified via real render: generated Angelia's Year Ahead HTML
through `generate.py`, converted with `chrome.exe --headless
--print-to-pdf` (the project's approved `browser_print` route), and
inspected page count plus rendered PNGs of flagged pages.
**Result: 100 -> 84 pages** (a byproduct of removing the indiscriminate
per-section break, not an optimization target).

**Phase 1.5 - card density and flow triage:** Within the single
consolidated block, removed `.reader-guide` and `.climate-field` from the
"protected indivisible unit" list (they were being pushed whole to a new
page as atomic blocks, the biggest remaining whitespace source after
Phase 0) and added `align-items: start` to five reference/highlight grids
(`.characteristics-grid`, `.characteristics-strip`, `.reader-principles`,
`.season-summary-grid`, `.climate-highlight-grid`) so a shorter sibling
card no longer stretches to match its tallest row partner. No min-height
rules existed inside the four target modules (Natal Reference, Reading
This Forecast, Year Orientation, Forecast Climate), so none were removed.
Verified via the same render+PDF-to-PNG method.
**Result: 84 -> 83 pages.** Confirmed visually: the "How to Use This Book"
guide and the natal-foundation reader-guide now flow onto the same pages
as the content before them instead of each claiming its own mostly-empty
page; multiple Forecast Climate fields now share a page instead of one
field per page.

**Discovered, not fixed (flagged to user):** a real rendering bug in Year
Orientation where the "Field Highlights" panel visually overlaps and cuts
off the "Seasonal Highlights" panel above it (`.curated-summary-stack` /
`.curated-summary-panel` row-sizing). Confirmed present byte-for-byte in
the Phase 0 baseline PDF too, so it predates this work and was not caused
by the `align-items` changes. Left untouched - fixing it means touching
container-level grid logic beyond a per-card alignment tweak, so it was
surfaced rather than silently expanded into.

**Focused pass - Section VI (Forecast Climate) and Section VII (Year
Arcs) only:** Removed `.arc-story + .arc-story { break-before: page }`
(the rule forcing one Year Arc chapter per page regardless of length) and
zeroed the fixed `min-height: 8.15in` on `.arc-story` and `min-height:
100%` on `.arc-story-layout` (print-only; the unrelated screen-only base
rule, `min-height: 7.95in`, was left untouched - out of scope for a
PDF-focused pass). De-boxed `.climate-field-support` (removed background/
border/border-radius, replaced with a single top divider) so each field's
representative-cycles list reads as a compact reference list instead of a
second nested card; increased `.forecast-climate-pairs` gap to the
existing `--space-6` token for calmer spacing between fields now that
they share pages. Field titles/tags and Arc title/kicker/subtitle
groupings were left exactly as they were - already visually distinct, not
part of the ask.
**Result: 83 -> 80 pages.** Verified via render+PNG: Forecast Climate now
fits 2 fields per page across most of the section (previously ~1 per
page); Year Arcs now fits 3 chapter entries on the section's opening page
and the remaining 2 on the next, down from roughly one entry per page.
Remaining trailing whitespace on the last page of each section (the final,
shortest field/arc before the next section starts) was identified and
deliberately left alone - it's section-end whitespace tied to that
specific field/arc's content length, not a rigid-container problem.

**Deliberately left alone across all three passes:** title page /
frontispiece (explicitly deferred each time, still doesn't exist -
page 1 is not yet a true cover); Monthly Chapters section and month-opener
padding; Annual Rhythm quarter-grid; Natal Reference, Reading This
Forecast structural markup beyond the Phase 1.5 grid/protection tweaks;
Technical Appendix; the `.curated-summary-stack` overlap bug above; all
calculation logic, JSON block content, and every non-year_ahead report
template.

---

## 2026-07-03 - Vibrant print/PDF fix, take two: the actual body-copy variables (Claude / Sonnet 5)

**Context:** User reported the same-day print/PDF contrast fix below (Codex /
GPT-5) hadn't worked — vibrant-palette reports were still printing as
functionally blank pages. Root cause: that fix introduced new
`--print-ink-*` tokens and repointed a curated list of selectors to them
(labels, eyebrows, footers, table headers), but never touched `--text`,
`--muted`, `--subtle` — the actual palette variables that the *bulk* of
report copy uses directly (`.theme-body`, `.opening`, `.guidance-text`,
`.closing`, `.block`, and dozens of paragraph/table-cell rules across all
four templates). Those three vars are the vibrant screen palette's near-white
values (`#E6E2DA` / `#8B8798` / `#555266`, from `config.py`'s
`PALETTE_VIBRANT`) and were never redefined for print, so the majority of
each report's actual interpretive text stayed pale-on-white — i.e. looked
blank — regardless of the first fix.

**What changed:**
- `products/shared/report_visual_system.css`: the existing
  `@media print { body.report-shell[data-palette="vibrant"] { ... } }`
  block now also overrides `--text`, `--muted`, `--subtle` to the same dark
  navy family as `--print-ink-*`. This covers `personal_forecast`,
  `soul_ecosystem`, and `year_ahead` (all three link this shared stylesheet
  and carry `report-shell` + `data-palette` on `<body>`), fixing the bulk
  copy without touching every individual selector.
- `products/daily_horoscope/templates/daily_horoscope.html`: this template
  never includes `shared_report_css` at all and its `<body>` has no
  `report-shell` class, so the shared-CSS fix above doesn't reach it. Added
  a local `body[data-palette="vibrant"] { --text; --muted; --subtle; }`
  override inside its own existing `@media print` block. This is what
  actually fixes `.block` — the div wrapping Today's Sky / Activation /
  Day's Ruler / Proprietary / Closing content, i.e. nearly the entire
  report — which was previously untouched by any print override.

**Verified (real render, not just code-reading):** generated one vibrant
report per type via `generate.py`, printed each to PDF with
`chrome.exe --headless --print-to-pdf` (the project's approved
`browser_print` route, automated), and rendered the resulting PDF pages to
PNG to inspect directly. Confirmed body-copy paragraphs that were
previously on the missed-selector list (`.opening`/`.theme-body` in
personal_forecast, `.block` in daily_horoscope, the world-interface prose
in soul_ecosystem, the record/characteristic cards in year_ahead) now
render dark navy and legible, not pale. Test artifacts were generated
under a scratch dir and deleted after verification; no repo files were
added.

**Deliberately left alone:** no non-print styling changed; no muted-palette
behavior touched; no other selectors beyond the variable definitions above
were added, since redefining `--text`/`--muted`/`--subtle` themselves
cascades to every existing consumer rather than requiring a growing list of
per-selector patches.

---

## 2026-07-03 - Vibrant report print/PDF text contrast fix (Codex / GPT-5)

**Context:** The user reported that vibrant-style reports were rendering
majority text in a pale silver/gray during print/PDF conversion, leaving
sections physically unreadable. Scope was intentionally narrow: fix the
print-time text color only, without altering layout, screen styling, or
the muted palette's established look.

**What changed:**
- `products/shared/report_visual_system.css` now defines print-only ink
  variables (`--print-ink-strong`, `--print-ink-muted`,
  `--print-ink-soft`, `--print-ink-faint`). Default print values stay in
  the existing grayscale range, but `body.report-shell[data-palette="vibrant"]`
  now swaps those variables to a dark navy family during `@media print`.
- Active template-specific print overrides that previously hardcoded pale
  gray text were repointed to those variables in:
  - `products/personal_forecast/templates/personal_forecast.html`
  - `products/soul_ecosystem/templates/soul_ecosystem.html`
  - `products/daily_horoscope/templates/daily_horoscope.html`
  - `products/year_ahead/templates/active/year_ahead.html`
- Year Ahead had a second, deeper print-recovery block still using
  hardcoded gray text; that block was updated too so the navy treatment
  is consistent through the full printed/PDF report, not just the top
  sections.

**Verified:**
- Code-level verification only in this pass: confirmed the shared print
  ink variables exist, the vibrant palette gets the navy override, and
  the active print selectors in the templates above now reference the
  shared print variables rather than hardcoded pale gray values.

**Deliberately left alone:**
- No non-print styling changed.
- No muted-palette behavior was intentionally altered.
- No fresh browser/PDF render was run in this pass, so visual QA remains
  worth doing against a real vibrant report output.

---

## 2026-07-02 — Daily Horoscope: built the "Today's Timeline" engine layer (Claude / Sonnet 5, engine only — no content or template work yet)

**Context:** Follow-on to the same-day "today's activation" work below. User wants
a second Daily Horoscope feature — a short list of dated "key hour" moments
across the day, the way Year Ahead names when in the *month* something
peaks, but for a single day. Eventually tiered (3/6/9, paying-tier
depth), but tiers are explicitly deferred (see Open below) since gating
needs an account system that doesn't exist yet.

**First design was wrong, caught before any content was written:** the
initial `compute_daily_timeline()` reused `DAILY_ACTIVATION_PLANETS`
(Sun through Pluto, no Moon) and `_find_exact_contacts()` to find when
each contact peaks within the day. Tested against a real chart:
Sun-square-natal-Mercury "peaked" exactly at the scan window's boundary
even at 1-hour sampling — confirmed via direct test this is a
`_find_exact_contacts()` fallback artifact (no true interior local
minimum exists in the window), not a real moment. **Root cause:** only a
body fast enough to fully approach and separate from an aspect within
~24 hours can have a genuine intra-day peak. The Moon (~13 deg/day)
can; Sun/Mercury/Venus/Mars/outer planets mostly can't — confirmed by
the same test returning a genuine interior peak (12:24:57 UTC) for a
same-day Moon-square-natal-Moon check.

**Rebuilt Moon-primary:**
- `engine/transit_engine.py`: `MOON_TIMELINE_ORB`/`MOON_TIMELINE_SIGNIFICANCE`,
  `_is_boundary_artifact()` (filters any contact landing within 5 minutes
  of the scan window's start/end — the boundary-artifact signature found
  above), and `compute_daily_timeline(natal_payload, day_start, day_end,
  count, include_angles, include_slow_planet_peaks)`. Moon is the primary
  source; `include_slow_planet_peaks=True` (default) also checks
  Sun-through-Pluto for the rare day they *do* have a genuine peak, so
  they're not structurally excluded, just not relied on.
- `compute_daily_activation_transits()` (existing, from the prior entry)
  gained an `include_angles` parameter, reused here — `False` excludes
  Ascendant/Midheaven/Vertex from the natal target pool for querents
  without exact birth time, without turning the feature off (Sun through
  Pluto, or Moon here, stay eligible). `_natal_targets()` already tags
  each target `"kind": "planet"` vs `"kind": "angle"`, so this was a
  small filter, not new categorization logic.
- **Orb-widening didn't help density — minor aspects did.** Widening
  `MOON_TIMELINE_ORB` from 2.0 to 4.5 degrees produced byte-identical
  daily counts every time (tested); the real constraint was how many
  fixed aspect points exist to cross, not proximity threshold. Adding
  the three hard minor aspects (semisquare, sesquiquadrate, quincunx) as
  a separate `TIMELINE_ASPECT_ANGLES`/`TIMELINE_ASPECT_CHARACTERS`
  (deliberately not merged into the shared `ASPECT_ANGLES`, which Year
  Ahead's week/month-scale scanning depends on) raised the 14-day
  average from 2.6 genuine peaks/day (7/14 days short of even 3) to
  5.0/day (0/14 days short of 3).

**Tier-reliability data (21-day sweep, real chart), for whenever tiers
come back:** tier-1 depth (3) met 21/21 days (100%); tier-2 depth (6)
met 13/21 (62%); tier-3 depth (9) met 3/21 (14%), average 6.2 genuine
peaks/day. Widening orbs further will not close this gap (see above);
what will help on the days it's available is void-of-course/station
merging (see Open below).

**Verified:** full pytest suite after the engine changes — 240 passed,
1 skipped, same 11 pre-existing unrelated failures as every prior entry,
0 new failures. No dedicated tests added yet for `compute_daily_timeline`
itself (see Open).

**Open / explicitly not done this pass:**
- No tiering logic. User's direct call: "no tiers just 'if 7 are active
  that's cool for you' vibes" — ship uncapped (or a generous, purely
  defensive ceiling, not a product-shaping one) for now; real 3/6/9
  tiers return once there's an account system to gate them on.
- Void-of-course and station merging into the timeline output — agreed
  to do this, not yet wired. Both are already genuinely time-stamped
  (`detect_void_of_course_windows`, `scan_stations`) with existing
  authored content (station content is directly reusable as-is:
  `products/year_ahead/blocks/plainspeak/station_blocks.json` is keyed
  `{planet: {Retrograde/Direct: text}}`, exactly matching
  `scan_stations()`'s output — zero new authoring needed there).
- Content: 26 new blocks needed (13 natal targets x 2 aspect characters
  — flowing/challenging — per the user's explicit "target x aspect
  character now, target x specific aspect type later" phased call).
  Voice: plainspeak, matching the rest of Daily Horoscope — user
  confirmed this is intentional and permanent for the EO-branded content
  pack specifically (a separate future "archetypal-mythic" pack and
  white-label "generic astrological tone" packs are the planned home for
  other voices, not this feature).
- Slower-planet single-day activations (from `compute_daily_activation_transits`,
  no specific hour attached) folding into the timeline as filler entries
  on quiet days — user explicitly approved this as sound ("formulaic
  decision rather than a lie," since it's still attached to real in-orb
  data) but it's not wired into `compute_daily_timeline`'s output yet.
- No template section, no resolver/`generate.py` wiring at all yet —
  this pass was engine-layer only, deliberately stopped here rather than
  writing content or template code in the same push.

---

## 2026-07-02 — Daily Horoscope: rewrote `your_activation.json`, built real "today's activation" selection (Claude / Sonnet 5)

**Context:** `products/daily_horoscope/blocks/your_activation.json` (120
house blocks across 10 planets, per the file's own `_note`) was
confirmed to be mad-libs — three sentence skeletons and a word bank,
not independently authored prose. Separately, `selectors/variable_resolver.py`
hardcoded `activation_planet = "Moon"` unconditionally, meaning only
Moon's 12 blocks were ever actually reachable; the other 9 planets'
108 blocks were dead weight regardless of content quality.

**Content rewrite:** All 131 entries (10 planets x 12 houses + fallback,
plus the top-level fallback) rewritten from scratch — genuinely distinct
per block, no shared connector sentences, no shared house-domain
sentence reused across planets. Verified mechanically: zero exact-repeated
sentences file-wide, zero dash-interruption constructions (per user
preference — plain commas/periods/colons instead), word counts 38-78
(avg 53), valid JSON. Style grounded in the user-provided "Anti-Monotony
& Redundancy Protocol" doc (guidance-mode and metaphor-family variety,
avoided banned opener/closer phrase families, avoided generic caution
and forced healing-arc framing).

**Selection logic — replaced the Moon hardcode with a real priority chain:**
1. A planet stationing (retrograde/direct) today, via `scan_stations()`.
2. Else the highest-scoring same-day transit-to-natal contact across
   all planets but the Moon, via a new `compute_daily_activation_transits()`
   in `engine/transit_engine.py`.
3. Else Moon-in-house (the original mechanic), as the always-available
   fallback.

**New engine code, kept isolated from Year Ahead's infrastructure:**
`DAILY_ACTIVATION_PLANETS` / `DAILY_ACTIVATION_ORB` / `DAILY_ACTIVATION_SIGNIFICANCE`
and `compute_daily_activation_transits()` in `transit_engine.py` —
deliberately separate from `TRANSIT_PLANETS`/`TRANSIT_ORB`, which are
correctly sized for Year Ahead's week/month-scale forecasting but wrong
for a same-day decision. First attempt reused the wide Year Ahead orbs
directly and was empirically wrong: a 120-day sweep against a real
chart showed Neptune (orb 3.0, significance 0.95) winning 62% of days
outright, because at Neptune's near-standstill daily motion a 3-degree
orb keeps it "in range" for weeks or months; the Moon fallback never
fired once in the sweep. Fixed with graduated, same-day-appropriate
orbs (1.0 degrees for Sun/Mercury/Venus/Mars down to 0.15 for Pluto,
tighter for slower bodies specifically because they linger longer at
any given orb width) — orb sizing grounded in researched transit-astrology
convention (personal planets read at roughly 1-2 degrees for daily-scale
use), not invented. Re-run of the same 180-day sweep after the fix:
max single-planet share 18% (Mars), all 9 non-Moon planets represented,
Moon fallback ~3%, stations ~2%. See `compute_daily_activation_transits()`'s
docstring for the full reasoning.

**Bug fix found and corrected along the way:** the pre-existing Moon-house
computation (`int((_moon_lon - _asc_lon) % 360 // 30) + 1`) was Equal
House math, not Whole Sign — it gave a different (wrong) house number
than `transit_engine._whole_sign_house()` (the correct, sign-based
formula already used elsewhere in the engine for ingresses and eclipses)
whenever the Ascendant wasn't near 0 degrees of its sign. Confirmed via
direct test: ASC at 25 degrees Aries, body at 5 degrees Aries (same
sign) — old formula said house 12, correct Whole Sign answer is house 1.
Given METHODS.md declares Whole Sign as the sole active production
methodology, this was a live correctness bug in a shipping feature, not
a style choice. Fixed by reusing `_whole_sign_house()` for every tier of
the new selection chain, including the Moon fallback.

**Verification:** house-formula fix confirmed via direct unit check;
full pipeline confirmed via live `generate.py horoscope` runs (auto-
detected and used the project's own `.venv/Scripts/python.exe` — the
bare `python` on PATH does not have `pyswisseph`, which is expected and
not a missing-dependency problem); 180-day empirical distribution sweep;
full pytest suite (`pip install pytest` into `.venv` first, since it
wasn't present) — 227 passed, 1 skipped, 11 failed, and all 11 failures
are the same pre-existing ones already documented above (`test_eclipse_house_fix.py`,
the Year Ahead forecast-climate/shape/ledger tests, `--location "Peoria, IL"`
offline-geocoding failures) — none touch anything changed in this pass.

**Permanent regression coverage added:** `tests/test_daily_horoscope_activation.py`
(13 tests) — locks in the Whole Sign house fix (including a test that
documents the old Equal House formula's specific wrong answer), asserts
`DAILY_ACTIVATION_ORB` stays graduated tighter for slower planets (the
exact property whose absence caused the Neptune-dominance bug), a
distribution-balance guard (no planet wins more than half of a sampled
month) as a permanent regression check for that same bug class, and
mock-based tests of the full station-beats-transit-beats-Moon priority
chain via `resolve_all()`. Full suite after adding this file: 240
passed, 1 skipped, the same 11 pre-existing unrelated failures as
before, 0 new failures.

**Deliberately not done:** the other 9 planets' block content was
already fully written in this same pass (not deferred), so no further
content work is blocked. Not built: dedicated new template sections for
station/void-of-course/retrograde-cluster alerts (a real option, scoped
and discussed, explicitly deferred at the user's request rather than
folded into this pass) — the existing "Your Activation" card's header
line already reads correctly regardless of which tier won, so no
template change was required for this to ship.

---

## 2026-07-02 — Storefront Partner API readiness audit (Claude / Sonnet 5, research only — no code changed)

**Context:** User asked whether/how Entangled Oracle could be exposed to
storefront partners through an API or account-based access system, so
partners could submit consumer report requests, generate/retrieve reports
themselves, and only contact the team for updates, billing, content-pack
changes, or technical issues. Four-agent parallel review covering: current
generation flow/orchestration, the engine/data-input layer, config/product/
content-pack structure, and security/testing/dev-notes.

**Verdict:** Feasible, not close. The calculation core (`engine/`,
`formulas/`, `selectors/`) is clean, pure-function, genuinely reusable as-is.
Everything above it — request handling, async, multi-tenancy, a security
boundary, ops/observability — is greenfield. `generate.py` is CLI tooling
(argparse → synchronous call chain → local file write → `webbrowser.open()`),
not service-shaped, and needs an extraction pass before any API wraps it.

**Concrete blockers found** (full actionable list moved to
PLANNED_UPDATES.md):
- Jinja2 autoescape confirmed OFF in `generate.py`'s `Environment()` call
  (~line 7731) — safe today only because all template input is
  operator-typed locally; becomes a live XSS vector the moment
  `--name`/`--location`-equivalent fields are externally supplied.
- Hardcoded absolute path `ephemeris/backend_data.py:12`
  (`EPHE_PATH = r"C:\entangled_oracle\ephemeris"`) — not derived from
  `BASE_DIR` like the rest of `config.py`; breaks on any other deployment
  root.
- `ephemeris/backend_payload_debug.json` exists in the repo, unreviewed
  this pass — filename suggests it may hold a real/realistic birth
  payload. Flagged for inspection, not confirmed either way.
- Birth coordinates and resolution details are printed to stdout in plain
  text in `natal_engine.py` — a PII-in-logs risk if any future deployment
  centralizes stdout.
- No `requirements.txt`/`pyproject.toml` anywhere in the repo — nothing
  pins geopy/pyswisseph/jinja2/timezonefinder versions.
- `identity_profile` has its own product folder and runtime module but is
  NOT in `generate.py`'s argparse `choices` or dispatch chain — orphaned,
  not a live 5th report type. (Confirms the CLI's live report-type surface
  is exactly the 4 active types + dev-only `predictive_sandbox`, now that
  Asteroid Portrait is gone per the entry below.)
- Filename convention (`{name}_{report_type}_{timestamp-to-the-minute}.html`,
  no UUID, no lock) has a real collision/clobber risk under concurrent load.
- Manifest sidecar embeds raw querent PII next to internal trace/versioning
  data — not a safe shape to hand back through a partner-facing endpoint
  as-is.
- `CONTENT_PACKS` (`config.py`) is wired only to `year_ahead` today, not a
  general per-report mechanism — "content packs" reads as more general in
  the docs than the code actually implements.
- System is fully single-tenant: `CONTENT_PACKS` / `REPORT_BLOCK_DIRS` /
  `PALETTES` are module-level constants loaded once at import; no
  per-request or per-caller parameterization exists anywhere.

**Also confirmed clean:** zero hardcoded secrets/credentials anywhere in
the codebase. The only outbound network call anywhere is Nominatim
geocoding, and it's only reached when the bundled offline place-resolver
(`geonamescache`/`timezonefinder`) has no match. Ephemeris data is bundled
in-repo — no runtime download dependency.

**Deliberately not done:** no code changed — this was scoping/research
only, at the user's explicit request. `agents/` had zero prior notes on
API exposure or multi-tenancy going into this — confirmed via a full read
of this folder — so the storefront-partner-API angle is genuinely new
scope for the project, not a continuation of existing thinking. Full API
architecture recommendation, MVP-vs-future endpoint scope, and a phased
rollout plan were produced and shared with the user directly; the
actionable subset lives in PLANNED_UPDATES.md.

---

## 2026-07-02 — Asteroid Portrait removed (Claude / Sonnet 5)

**Context:** Asteroid Portrait was being phased out. Before deleting it,
did a migration audit: (1) does AP have any archetype/content Soul
Ecosystem doesn't already cover, and (2) do any of the 4 active report
types route anything through AP's files or code at runtime?

**Audit findings:**
- Every AP archetype has an identical-key Soul Ecosystem counterpart
  (`impact_radius`, `knowledge_legacy`, `reality_field`,
  `legacy_foresight_pattern`↔`foresight_pattern`,
  `ancestral_thread`↔`ancestral_layer` — same archetype names, same
  tiers, independently authored prose). Spot-checked "Vindicated Oracle"
  specifically — SE's version is better-suited for a commercial product
  (drops AP's shadow/melodrama framing, adds psychological-safety
  language AP lacks). Nothing worth porting.
- AP's two exclusive files (`portrait_overview.json`/`portrait_synthesis.json`)
  are AP's own opening/closing wrappers — SE already has its own
  (`souls_promise.json`/`souls_story.json`).
- `magnetic_frequency.json` (MAGNETIC/MCQ/SIREN legacy index) was already
  tagged `successor: "NGE"` in the code — Soul Ecosystem already uses NGE.
  Not a migration target, it's the thing NGE already replaced.
- Confirmed AP was fully self-contained: every reference in `generate.py`
  was either the dispatch branch or inside `_build_asteroid_portrait_context()`
  itself. No template, no config entry, no other report builder touched it.

**Removed:**
- `products/asteroid_portrait/` (blocks + templates) via `git rm`.
- `_build_asteroid_portrait_context()` and its dispatch branch in `generate.py`;
  `asteroid_portrait` dropped from CLI `choices`, `render_template()`'s
  `template_map`, `config.py`'s `REPORT_BLOCK_DIRS`, `product_versions.py`
  (`REPORT_TYPE_VERSIONS`, `TEMPLATE_MAP`, block-path lookup).
- `asteroid_portrait` dropped from eligibility tuples in
  `formulas/established_niche.py` and `formulas/governance_registry.py`
  (`REPORT_TYPE_TO_PROFILE`, `ASTEROID_ELIGIBILITY_REGISTRY`); two
  now-unreachable branches simplified in `formulas/report_surface.py`.
- Bonus cleanup (fully dead once AP was gone): `compute_mcq()`,
  `compute_siren()`, `compute_magnetic_frequency()`, and
  `get_dimension_order()` removed from `formulas/proprietary_indexes.py`;
  the `magnetic_*` variable block removed from `selectors/variable_resolver.py`;
  MCQ/SIREN/MAGNETIC entries removed from `governance_registry.py`'s
  `METHOD_REGISTRY_CATALOG`.
- `tests/test_asteroid_portrait_tier_routing.py` deleted (9 AP-specific
  tests). `test_established_niche_governance_phase3.py`,
  `test_standard_report_wiring_phase5.py`, `test_transit_cycles.py`,
  `test_phase8_quality_assurance.py` updated to use `soul_ecosystem` in
  place of `asteroid_portrait` as their "niche-eligible" test fixture —
  same governance profile, so same test intent, just not pointing at a
  deleted report type.
- Docs updated: `ARCHITECTURE.md`, `README.md`,
  `products/shared/LOCAL_GENERATION_PROCEDURE.md`,
  `products/shared/B2B_DEMO_AND_EARLY_RECIPIENT_PACKAGE.md`,
  `tests/PHASE8_QA_WORKFLOW.md`, `scripts/build_phase9_baseline.py`,
  `scripts/generate_review_pack.py`. Daily Horoscope's soft-sell line
  ("Full context in your Asteroid Portrait") repointed to Soul Ecosystem.
- `output/` and `tmp/` contents cleared (both gitignored, never tracked —
  dev/test artifacts only, no customer deliverables).

**One real regression caught mid-pass, worth remembering:** removing
`get_dimension_order()` broke 15 tests across files that had nothing to
do with Asteroid Portrait — it turned out `selectors/variable_resolver.py`
still imported and called it to populate `variables["dimension_order"]`/
`["dominant_dimension"]`, a call site my first grep pass missed (I'd only
checked `generate.py` and `formulas/proprietary_indexes.py`). Confirmed
those two variables were genuinely unused by any live template before
removing the resolver's call too. Lesson: when deleting a function,
grep the *whole* active tree for its name, not just the files you expect
to reference it — an internal library import can be an invisible caller.

**Verification:** full pytest suite before/after every stage of this
removal — consistently landed back at 216 passed / 16 failed / 1 skipped
(225 minus the 9 deleted AP tests; the 16 failures are the same
pre-existing set from the prior entry, unrelated to this work). All 4
active report types (`year_ahead`, `personal_forecast`, `soul_ecosystem`,
`horoscope`) generated cleanly after every stage. `asteroid_portrait` as
a CLI argument now fails with a clean argparse "invalid choice" error.

---

## 2026-07-02 — Pre-launch readiness pass (Claude / Sonnet 5)

**Context:** Full readiness review ahead of first commercial launch of
Year Ahead, Personal Forecast, Soul Ecosystem, and Horoscope-beta.
Four-agent parallel review (pipeline integrity, block library/voice,
live report generation, malformed-input testing) produced a prioritized
findings list; this session then implemented the fixes.

**Phase 1 — contained bug fixes (Personal Forecast, Soul Ecosystem, Year Ahead only):**
- Removed a leaked internal QA disclaimer ("not the finalized... weighting
  model") from Year Ahead's Cycle Ledger and Technical Appendix sections
  — replaced with real client-facing methodology copy.
- `--location` is now a required CLI argument. Previously a missing
  location silently fell back to the literal string `"Unknown location"`,
  which defeated `natal_engine.py`'s own `if not location_name: raise`
  guard and got geocoded to an arbitrary real place via online fallback.
- Removed raw numeric score dumps (`Pattern score0.26`, etc.) from Soul
  Ecosystem's template — kept the qualitative tier/driver/facet labels,
  dropped the `"%.2f"|format(score)` lines.
- Added DST spring-forward gap detection (`_is_nonexistent_local_time` in
  `engine/natal_engine.py`) — a birth time that never existed locally
  (e.g. 2:30 AM on a US spring-forward date) now downgrades birth-time
  confidence to `approximate_birth_time` instead of silently picking one
  side of the gap.
- Guarded the extreme-latitude Placidus crash: `swe.houses(..., b"P")` in
  `natal_engine.py` now retries with Porphyry (`b"O"`) on `swe.Error`
  before giving up with a clean `ChartCalculationError` instead of a raw
  traceback. Verified against Longyearbyen, Svalbard (78°N).
- Extended `_usable_block()` to also scrub `[BLOCK NOT FOUND: ...]` /
  `[MISSING BLOCK FILE: ...]` markers (previously only `[TODO]`), and
  applied it to Soul Ecosystem's block selection (previously only
  Year Ahead / Personal Forecast were filtered).
- Gated the SVG chart wheel in Personal Forecast and Soul Ecosystem
  behind `_has_exact_birth_time()`, matching what Year Ahead already did
  — the wheel no longer renders a confident house layout in `--simple`
  mode while the adjacent text is hedging.

**Phase 2/3 — new capabilities (Personal Forecast, then Year Ahead):**
- `detect_retrograde_clusters()` (`engine/transit_engine.py`) — samples
  the 8 outer/inner planets daily across a report window, finds stretches
  where 2+ are simultaneously retrograde, tiers `two_retrograde` /
  `three_plus_retrograde`. Content: `products/personal_forecast/blocks/shared/retrograde_cluster_blocks.json`.
- `detect_void_of_course_windows()` (`engine/transit_engine.py`) —
  single-pass scan tracking the Moon's sign and its last exact aspect to
  the seven classical bodies (Sun–Saturn), tiers `brief_void` /
  `extended_void` (6+ hours or crosses a calendar day). Content:
  `products/personal_forecast/blocks/shared/void_of_course_moon_blocks.json`.
- Both wired into Personal Forecast directly, and into Year Ahead by
  reusing the *same* block files via new `CONTENT_PACKS` entries in
  `config.py` (`retrograde_cluster_blocks`, `void_of_course_moon_blocks`)
  — no content duplication between the two report types.

**Phase 4 — chart wheel retrograde glyph:**
- `current_retrograde_planets()` snapshot helper in `transit_engine.py`.
- `build_chart_wheel_data()` in `engine/chart_wheel.py` gained an optional
  `current_retrograde` parameter; matching natal placements get a small
  cyan ring — deliberately distinct from the existing orange natal-Rx
  label (natal retrograde and transit-right-now retrograde are different
  facts). Wired into all three wheel-bearing products with a
  plain-language legend caption.

**Cleanup round:**
- `render_template()` now raises a clear error on an unrecognized
  `report_type` instead of silently rendering the Daily Horoscope
  template; non-sandbox template-render failures now print a full
  traceback (previously one line) before degrading to the fallback page.
- `predictive_engine.py`'s three swallowed-exception phases
  (transit-signal collection, daily series, window detection) now print a
  console warning in addition to recording the error in `debug` — that
  dict was never read anywhere, so the failures were functionally silent.
- `_load_json_file()` now distinguishes a missing file (normal, silent)
  from a file that exists but fails to parse (now logged — was silently
  degrading to blank content).
- `_generate_archetypal_opening()`'s catch-all `except Exception: return {}`
  now logs before dropping the section.
- Malformed `--date` / `--time` and empty/whitespace `--name` now fail
  with a clean one-line `SystemExit` message instead of a raw Python
  traceback (new `InputValidationError`, validated in `parse_birth_data`).
- Verified Soul Ecosystem's "generational inheritance" (Pluto-sign)
  paragraph is *intentionally* identical across anyone sharing a Pluto
  sign — it's keyed purely on `pluto_sign` and the block's own `_note`
  says "Generational framing." Not a bug.

**Deliberately left alone (explicit scope exclusion):** Daily Horoscope
and Asteroid Portrait were excluded from this pass. Known open issues
there are tracked in PLANNED_UPDATES.md.

**Verification:** every fix and feature was checked against live-generated
reports (positive and negative cases), and the full pytest suite was run
at multiple checkpoints throughout — consistently 225 passed / 16 failed /
1 skipped, before and after every change, with zero new failures
introduced. The 16 failures are pre-existing and unrelated to this work
(timing/field-name mismatches in transit-cycle, eclipse-labeling, and
Year Ahead forecast-climate/raw-cycle-ledger tests). Separately, 5 test
modules (`test_angularity.py`, `test_dignity.py`,
`test_phase7_rendering_system.py`, `test_planetary_condition.py`,
`test_sect.py`) fail to even *import* — they reference modules
(`planetary_angularity_algorithm`, `expanded_dignity_matrix`,
`oracle_to_pdf`, `planetary_condition`, `sect_calculation_algorithm`)
that don't exist at their expected import paths. Excluded via `--ignore`
rather than investigated — worth a look (see PLANNED_UPDATES.md).
## 2026-07-02 - Phase 0 hardening pass closeout (Codex / GPT-5)

**Context:** Follow-through implementation from the same-date readiness
audits. Scope stayed intentionally narrow: harden the current local report
generator before any future API, partner, packaging, or white-label work.
No service extraction, no product/content refactor, no UI build.

**Updated readiness verdict:** materially improved. The local generation
pipeline is now much closer to a stable single-operator tool than it was
at the start of the day. The highest-risk Phase 0 blockers identified in
the audit are fixed or reduced to follow-up work. Remaining work is now
mostly about broader smoke coverage and future product direction, not
emergency stabilization of the local generator.

**Implemented in this pass:**
- Renderer hardening in `generate.py` and the duplicated
  `identity_profile` renderer.
- Fallback HTML escaping in `_render_fallback()`.
- Root `pyproject.toml` for reproducible dependency installs.
- PII/log hygiene in `engine/natal_engine.py`,
  `ephemeris/backend_data.py`, and `generate.py`.
- Repo-relative ephemeris path in `ephemeris/backend_data.py`.
- Quieter default stdout with opt-in verbose/trace channels.
- Atomic HTML and manifest writes plus collision-resistant default output
  filenames.
- Live transit verification repair in `tests/test_transit_cycles.py`.

**Verification actually run:**
- `.\.venv\Scripts\python.exe -m unittest tests.test_renderer_autoescape -v`
- `.\.venv\Scripts\python.exe -m unittest tests.test_renderer_autoescape test_offline_location -v`
- `.\.venv\Scripts\python.exe -m unittest tests.test_renderer_autoescape test_offline_location tests.test_phase9_operational_readiness -v`
- `.\.venv\Scripts\python.exe tests\test_transit_cycles.py`
  - initially failed on missing `.venv` dependencies
  - then failed on stale test-helper assumptions
  - finally passed fully: `9 passed, 0 failed`

**Important operational note:** the project `.venv` can drift away from
the user-level Python installs. The reliable repo pattern is to install
into and run with `.\.venv\Scripts\python.exe`, not plain `pip` / plain
`python`.

**Still deliberately not done:**
- No service/API seam extraction from `generate.py`.
- No multi-tenant / partner / white-label branding system.
- No local input shell / desktop wrapper.
- No manifest PII redesign; manifests still intentionally include
  querent fields for local traceability.
- No structured logger abstraction yet; stdout gating was the smallest
  practical hardening step.

**Net result:** the original Phase 0 blocker list from the storefront/API
audit is no longer current as-written. The severe items there
(autoescape off, hardcoded ephemeris path, unsafe default path logging,
same-minute filename collisions, unreproducible dependency setup) were
addressed in this pass.

---
