# Revisions

A dated log of meaningful changes made to this codebase by AI sessions.
Newest entry on top. See `agents/README.md` for the convention.

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
