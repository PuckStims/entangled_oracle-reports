# Planned Updates

Known, not-yet-done work. Check here before scoping something new. Move an
item to `REVISIONS.md` when it is actually finished.

---

## Predictive Sandbox v0.3 - engine-first expansion plan (2026-07-06)

The current `predictive_sandbox` lane is real, runnable, and useful for
diagnostics, but it is still `predictive_v0.2`: transit-derived signals,
baseline/residual window segmentation, one `leading_index`, one
`gradient`, and placeholder `coherence` / `memory` fields. The user's
next-phase goal is now explicit: make the engine meaningfully
multi-clock and lifecycle-aware **without** letting semantic theory
outrun auditable signal mechanics.

This means the next expansion should not start with renderer prose or
JSON-routing proliferation. It should start by making the engine itself
smarter, while preserving several invariants:

- `intensity`, `coherence`, `memory`, and `gradient` remain separate
  fields; none is allowed to silently collapse into another.
- Chorus must be anti-double-counting: subtypes like stations and
  ingresses must not manufacture fake multi-clock convergence.
- Memory is episode-based, not duration-inside-orb based.
- Targets are modification vectors, not just relevance multipliers.
- High-polarity Crucibles remain intense; coherence must never act as an
  intensity downgrade.
- Renderers remain downstream of computed evidence; they do not invent
  meaning absent from the engine.

### Short pre-render constraints (lock these before implementation)

1. Render must not merge `intensity`, `coherence`, `memory`, and
   `gradient` into one visual "overall meaning" score.
2. Sandbox-only classifications such as `Convergent`, `Crucible`,
   `Braided`, and `Echo` are allowed later, but only when visibly marked
   as sandbox/provisional and accompanied by evidence.
3. Raw evidence, formula versioning, and route traceability must remain
   visible somewhere in sandbox output even after the renderer gets more
   ambitious.
4. Chorus displays must respect `independence_group`, not just event
   count, so a transit + its station + its ingress do not look like three
   independent clocks agreeing.

### Method normalization decision (do this before scoring grows)

Do **not** let every forecast-event subtype become its own predictive
`method_family`, or the engine will manufacture chorus through taxonomy
rather than genuine independence.

Normalize predictive evidence with four fields:

- `method_family`
- `event_kind`
- `independence_group`
- `activation_route`

Initial target taxonomy:

- `TRANSIT` family
  `ASPECT`, `STATION`, `INGRESS`
  `independence_group = transit_clock`
- `LUNATION` family
  `NEW_MOON`, `FULL_MOON`
  `independence_group = lunar_phase_clock`
- `ECLIPSE` remains active but must suppress a duplicate plain-lunation
  chorus vote for the same astronomical event.
- `RETURN` family
  `EXACT_RETURN`
  `independence_group = return_clock`
- `PROGRESSION` family
  sandbox macro only for now
  `independence_group = progression_clock`
- `SOLAR_ARC` family
  sandbox macro only for now
  `independence_group = solar_arc_clock`
- proprietary asteroid/component triggering is an `activation_route`,
  not its own timing clock

### In bounds now

1. **Lunations and eclipses**
   Add them as real predictive families, but only when they have a natal
   or component-level address. Do not emit a generic monthly moon event
   that lacks a qualified target or registered component activation.
2. **Exact returns**
   Start with event-level return hits, not full return-chart
   interpretation. Solar return, lunar return, Jupiter return, and
   Saturn return are the clearest first candidates.
3. **Solar Arc sandbox macro**
   Add as a deterministic macro clock with one declared convention only;
   do not mix arc conventions in the same formula version.
4. **Limited secondary progressions sandbox**
   Start narrower than Solar Arc: Sun, Moon, ASC, and MC first, with
   exact-time gating for angles.
5. **Episode-based memory**
   First activation vs recurrence, retrograde pass state, cumulative
   charge, and integration/aftermath are explicitly in bounds now.
6. **Target-sensitive operation typing**
   Highest-value conceptual expansion. Same source/aspect/method must be
   capable of materially different operation profiles when the natal
   substrate changes.
7. **Semantic coalition/counterforce sandbox**
   Allowed after operation typing exists. Keep sandbox-only until the
   registry and fixtures stabilize.

### Explicitly defer

1. Full return-chart interpretation and relocated-return logic.
2. Report-eligible Solar Arc / progression claims.
3. Epistemic pathway topology as active computation.
4. Primary directions, harmonics, time lords, asteroid seasons,
   electional timing, synastry prediction, and pathway-throughput style
   claims.

Pathway topology may remain present structurally as a deferred stub, but
the active engine should not calculate it yet.

### Recommended build order for `predictive_v0.3`

1. Normalize all forecast evidence into a common predictive-event layer.
2. Add `independence_group` and enforce anti-double-counting chorus.
3. Add lunation/eclipse and exact-return event extraction.
4. Add Solar Arc and limited secondary progressions as sandbox macro
   methods.
5. Build the activation-episode ledger, pass-state model, charge decay,
   and lifecycle route classifier.
6. Add target-sensitive operation profiles using:
   source force + target substrate + aspect geometry + method temporal
   behavior + pair bridge.
7. Add sandbox semantic metrics:
   coherence, polarity, coalition, counterforce, complexity.
8. Leave pathway topology structurally present but inactive.

### Memory model to preserve

The user explicitly wants all four of these meanings:

- first activation vs recurrence
- retrograde pass state
- cumulative episode charge
- integration / aftermath

The key restriction: charge must remain episode-based and method-aware,
never a disguised "time spent in orb" counter for slow bodies.

### Coherence model to preserve

Coherence should detect:

- same-direction reinforcement
- conflicting symbolic pressures
- source/target/aspect/method composition

"Narrative compatibility" should **not** mean prose similarity. It must
mean declared operation compatibility, computed from a real operation
profile rather than from downstream wording.

### Target priority stack

1. Core immediate targets:
   `Sun`, `Moon`, `ASC`, `MC`, `IC`
2. High-value proprietary sensitivity layer:
   `Kassandra`, `Chaos`, `Destinn`, `Karma`, `North_Node`, `Vertex`
3. Specialist controlled-expansion layer:
   `Lilith_BML`, `Medea`, `Kaali`, `Hermes`

Houses should stay contextual modifiers first rather than becoming
independent predictive targets in this phase.

### Acceptance fixtures to require before renderer expansion

1. `station` does not create a second transit-clock chorus vote.
2. `ingress` does not create a second transit-clock chorus vote.
3. `eclipse` supersedes a duplicate plain-lunation diversity vote for the
   same sky event.
4. Retrograde three-pass structures create episodes, not raw-duration
   charge.
5. Changing the natal target can materially change the operation profile
   for the same source/aspect/method.
6. Crucible windows remain high-intensity when polarity is high.
7. Relational modes never mutate core semantic metrics.
8. Angle-dependent targets fail gracefully when exact birth time is not
   available.
9. Sandbox macro methods cannot silently surface in production reports
   without an explicit gate.

### Sequence reminder

The repo should get more structurally intelligent before it gets more
metaphysically ambitious. `predictive_v0.3` should first become
multi-clock, lifecycle-aware, and target-sensitive; renderer style and
broader pathway theory can follow once those mechanics survive fixtures.

---

## Weekly Horoscope - foundation built, everything above it is not (2026-07-05)

See REVISIONS.md ("Weekly Horoscope: new report type, foundation-only,
wired end to end") for the full story. `weekly_horoscope` is a real,
runnable report type: CLI/config/dispatch wiring done, engine reuse
(`compute_daily_timeline()` over a Monday-Friday window) done and verified
live, exact-vs-simple birth time gating done. What's still open, roughly
in the order a next session should probably pick up:

1. **Content blocks.** The template currently renders raw computed
   timeline data (planet, aspect, target, house, timestamp) with no
   prose - same shape of work as Daily Horoscope's still-open "26 content
   blocks" item below, but not yet scoped in detail for the weekly cadence.
   User is still actively refining content pack contents generally - don't
   assume `plainspeak`/`entangled_oracle` are final before writing weekly
   copy.
2. **B2B batch/bulk generation entry point.** The user's actual intended
   distribution model: generate every member of a cohort's weekly report
   in one batch and hand the educator/institution a single file to send
   out themselves each week - not a live per-request API. `generate.py`
   is still one querent per CLI invocation; nothing loops over a roster
   yet. Calendar-week alignment (done) matters directly here: a cohort
   generated together now shares identical Mon-Fri boundaries regardless
   of when the batch job actually runs.
3. **Custom weekly schedules.** Monday-Friday is only the default. User
   has flagged wanting clinical / theory / off-day schedule variants later
   for different group contexts - not scoped yet, just flagged.
4. **Tiering.** Explicitly undecided by the user - do not assume a 3/6/9
   pattern will carry over from the Daily Horoscope precedent without
   asking.
5. **No test coverage** for `_build_weekly_horoscope_context()`,
   `_align_to_week_start()`, or `_report_window()`. Only verified via live
   CLI runs + manual HTML inspection this session.

---

## Year Ahead PDF layout - remaining work (2026-07-04)

Three completed passes (Phase 0 consolidation, Phase 1.5 card-density
triage, and a focused Forecast Climate / Year Arcs pass) took the Year
Ahead PDF from 100 to 80 pages and from a "web dashboard exported to PDF"
feel toward book-like flow. See REVISIONS.md 2026-07-04 for full detail.
Still open, roughly in order of what a next session should probably pick
up first:

1. **Title page / frontispiece.** Explicitly deferred in every pass so
   far. Page 1 is not yet a true cover (client name, report title, dates,
   brand identity, star-chart element) - the current `<header>` is just
   the top of page 1's main content. Section content still starts on
   page 1, not page 2. This is the one piece of the original ask that has
   not been started at all.
2. **`.curated-summary-stack` overlap bug (Year Orientation).** The
   "Field Highlights" panel visually overlaps and clips the "Seasonal
   Highlights" panel above it in print. Confirmed present in the Phase 0
   baseline too, so it predates all three passes - not a regression, but
   a real visible defect, not just whitespace. Needs container/row-sizing
   investigation on `.curated-summary-stack` / `.curated-summary-panel`,
   not just the per-card `align-items` tweak already applied to the grids
   inside those panels.
3. **Monthly Chapters section + month-opener padding.** Explicitly out of
   scope for all three passes so far (user asked it not be touched).
   Likely still has some of the same "generic card forced to a fixed
   shape" whitespace pattern that Forecast Climate and Year Arcs had.
4. **Annual Rhythm quarter-grid.** Also explicitly out of scope so far;
   flagged in the original Phase 0 audit as splitting mid-grid (2 of 4
   quarter-cards spilling to a new page) but not touched since.
5. **`.arc-story`'s screen-only base rule still has `min-height: 7.95in`**
   (unconditional, not print-scoped). Only the print-context min-height
   was zeroed on 2026-07-04, deliberately, since all three passes were
   scoped to PDF/print layout only. Worth a look if the on-screen HTML
   view of Year Arcs is ever in scope.

---

## Updated readiness snapshot (2026-07-02 post-hardening)

For the current single-operator local workflow, the major stabilization
pass is largely complete:
- renderer escaping is on
- fallback escaping is on
- the duplicated identity-profile renderer is hardened too
- dependency installation is reproducible via `pyproject.toml`
- sensitive stdout was reduced materially
- default report/manifest path logging is safer
- writes are atomic and default filenames are collision-resistant
- the live transit verification script is back to passing in a correctly
  provisioned `.venv`

This means the codebase is in a better state for continued local use than
it was at the start of the day. Remaining work is optional/product-
direction work, not emergency hardening of the local report generator.

---

## Storefront Partner API - still-relevant pre-work

The original 2026-07-02 audit blocker list is no longer fully current.
These are the items that still matter before any partner-facing API work:

1. **Inspect `ephemeris/backend_payload_debug.json`**. The helper now
   redacts by default, but the existing debug artifact itself still
   deserves explicit inspection, deletion, or a firm local-only policy.
2. **Extract an API-shaped seam from `generate.py`**. Argparse parsing,
   report generation, file I/O, and delivery are still fused into one
   synchronous call chain. A pure generation function is still needed
   before any HTTP layer can wrap this cleanly.
3. **Manifest sidecar is not a safe partner-facing response shape**. It
   still embeds raw querent PII alongside internal trace/versioning data.
4. **`CONTENT_PACKS` is not yet a general per-report mechanism**. It still
   reads broader in docs than in code.
5. **System is still single-tenant**. No account / partner / tenant
   concept exists anywhere in the runtime.
6. **Structured logging is still immature**. Default stdout is quieter
   now, but a real partner/API surface still wants a proper logger,
   failure taxonomy, and auditable request/result records.

Condensed future rollout if the API idea resumes:
1. Extract generation seam + adversarial-input tests.
2. MVP API for the cheaper report types only.
3. Multi-tenancy / partner schema.
4. Async delivery and job handling.
5. Operational maturity: structured logging, rate limiting, audit logs.

---

## Local-only workflow - reasonable next improvements

If the product direction stays local-only for personal/operator use:

1. **Inspect or purge legacy debug payload artifacts** in `ephemeris/`.
2. **Add a broader one-command smoke script** for the real `.venv`,
   covering one end-to-end generation path per active report type.
3. **Re-audit old failing-test counts before citing them**. The prior
   "16 failing tests" assumption is now stale because
   `tests/test_transit_cycles.py` was repaired and brought back to 9/9
   passing during the hardening stream.
4. **Build a local input shell only if/when requested**. This is no
   longer blocked by the Phase 0 hardening items that were addressed.

---

## Deliberately deferred - Daily Horoscope

The 2026-07-02 readiness pass explicitly excluded this report type.
Two of the three findings from that review were fixed in a later
2026-07-02 pass (see REVISIONS.md, "rewrote your_activation.json, built
real today's activation selection"). What's still open:

- Daily Horoscope `select_block()` calls still do not benefit from the
  expanded `_usable_block()` safety net that now protects other report
  paths. Not touched by either activation-selection or timeline work.

~~`your_activation.json` reads as mad-libs~~ — fixed, all 131 entries
rewritten. ~~`variable_resolver.py` has the silent
Ascendant-default-to-0-degree pattern~~ — the whole selection mechanism
was replaced; a real priority chain now runs (station > same-day
transit > Moon fallback), and a genuine Whole-Sign-vs-Equal-House bug
in the house computation was found and fixed along the way.

### "Today's Timeline" — engine done, everything above it is not

See REVISIONS.md ("built the 'Today's Timeline' engine layer") for the
full story, including two real design corrections found and fixed
during development (boundary-artifact peaks, orb-widening not helping
density — minor aspects did). `engine/transit_engine.py`'s
`compute_daily_timeline()` is built, tested, and empirically tuned.
Concrete next steps, in the order they were scoped:

1. **Write 26 content blocks**: 13 natal targets (10 planets + ASC/MC/
   Vertex) x 2 aspect characters (flowing/challenging). Voice: plainspeak,
   confirmed intentional and permanent for this content pack specifically
   (see REVISIONS.md entry — a separate archetypal-mythic pack and
   white-label generic-tone packs are the planned home for other voices).
   Follow-up phase (later, not this pass): expand to target x specific
   aspect type (50-65 blocks) per the user's explicit "character now,
   specific type later" call.
2. **Merge void-of-course + station events into the timeline output.**
   Both already exist and are genuinely time-stamped
   (`detect_void_of_course_windows`, `scan_stations`); station content
   is directly reusable from `products/year_ahead/blocks/plainspeak/station_blocks.json`
   with zero new authoring (key structure already matches
   `scan_stations()`'s output exactly). VOC content already exists too,
   shared with `personal_forecast`/`year_ahead` via `config.py`.
3. **Fold in slower-planet single-day activations as quiet-day filler**
   (from `compute_daily_activation_transits`, no specific hour attached).
   User explicitly approved this as sound, not fabricated — still real
   in-orb data, just without hour-level timing. Not wired in yet.
4. **No tiering.** User's explicit call: ship uncapped for now ("no
   tiers just 'if 7 are active that's cool for you' vibes"), with at
   most a generous defensive ceiling (not a product-shaping one). Real
   3/6/9 paying-tier depth returns once there's an account system to
   gate it on — see the Storefront Partner API audit entries for that
   still-nonexistent piece.
5. **New template section + resolver/`generate.py` wiring** — none of
   this exists yet. Engine-only pass, deliberately stopped there.
6. **Test coverage for `compute_daily_timeline`** — none written yet,
   unlike the activation-selection work (which has
   `tests/test_daily_horoscope_activation.py`). Worth the same treatment:
   a boundary-artifact regression test in particular, given that was a
   real bug caught by hand.

---

## Open test/debt items from the same period

1. **Investigate the 5 test modules that fail to import**:
   `test_angularity.py`, `test_dignity.py`,
   `test_phase7_rendering_system.py`, `test_planetary_condition.py`,
   `test_sect.py`. They reference modules that are missing, moved, or no
   longer importable at their expected paths.
2. **Recount the remaining importable failing tests from scratch** before
   reusing older readiness numbers in docs or planning.

---

## Ideas floated but not committed to

- Extend retrograde-cluster / VOC climate notes into Daily Horoscope if
  that product comes back into scope.
- Add richer wheel-state indicators around retrograde / station timing.

~~Re-render at least one vibrant PDF per active report template after
print-style edits when a visual QA pass is requested, since code-level
color fixes do not prove converter behavior by themselves.~~ — this
stopped being hypothetical on 2026-07-03: the same-day Codex/GPT-5 print
fix looked correct on code review (see REVISIONS.md) but missed that
`--text`/`--muted`/`--subtle` — not just the new `--print-ink-*` tokens —
drive the bulk of report copy, so most paragraph text was still pale on
white. Only caught because the user pushed back that it "still doesn't
work," which prompted an actual `chrome --headless --print-to-pdf` +
PDF-to-PNG render pass across all four report types this time (see the
follow-up REVISIONS.md entry same day). Recommend this becomes standard
practice for any print/PDF CSS change, not just an "if requested" idea —
code-level variable reasoning alone was not sufficient here.
