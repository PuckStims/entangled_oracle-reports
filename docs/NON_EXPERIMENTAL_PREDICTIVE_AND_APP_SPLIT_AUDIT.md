# Non-Experimental Predictive Formula + Rune/Tarot Split Audit

Date: 2026-07-20

Scope:

- Included: `C:\entangled_oracle` report generator, active report products, predictive/formula modules, evidence/report-surface wiring, and `C:\Users\jarod\AndroidStudioProjects\EntangledOracle` rune/tarot Android apps.
- Excluded: the recent React/Vite divination desktop dashboard and its experimental UI surfaces.
- Product decision after review: asteroid predictive is also excluded from the active unlock scope. Asteroids remain appropriate in natal/soul/portrait layers unless a separately approved non-predictive surface already owns them.
- Review posture: implementation audit of what is unlocked, what is partially unlocked, and what remains before client-facing claims should expand.

## Executive Verdict

The report generator has moved beyond a transit-only client forecast engine. Returns, annual profections, Solar Arc, secondary progressions, Lots, Zodiacal Releasing, forecast synthesis, and Tier 5 Year Ahead surfaces are now present in code and covered by targeted tests. The current active product lane is non-asteroid predictive only: raw asteroid contacts may still exist in scanner internals, but the client Year Ahead texture selector rejects asteroid variants and targets before prose cards are created. The important caveat is that many methods still identify themselves as `internal_rd` / `engineering_diagnostic` at the raw event-contract level, and the manifest still does not export a full predictive evidence sidecar. In other words: the calculation layer is increasingly unlocked; the validation/export/governance layer is the remaining bottleneck.

Lead-design guardrail added on 2026-07-20: Year Ahead Tier 5 timing surfaces now own the forecast terrain/evidence prose lane. The older `predictive_report_surface` remains available as a fallback contract, but is disabled when Tier 5 has client cards so the same synthesis prose cannot double-render unintentionally. A targeted placeholder scan across the active non-asteroid predictive prose libraries now returns no TODO/missing markers.

The rune/tarot Android split is at a healthy transitional milestone. `:shared-core`, `:rune-app`, and `:tarot-app` exist, have separate app IDs, and assemble successfully. The split is not finished because the new modules still compile source lanes from the original combined `:app` tree rather than owning their final source directories. That is acceptable as a boundary proof, but not a store-ready extraction.

## Report Generator: Formula Status

| Method family | Current status | Evidence in code | What still needs unlocking |
| --- | --- | --- | --- |
| Natal/transit forecast base | Client-active | `compute_year_ahead_events()` scans transits, ingresses, stations, eclipses, lunations; Year Ahead and Personal Forecast consume these. | Keep improving trace packaging and reproducibility; this is the baseline. |
| Exact returns | Calculation unlocked, report-surfaced as timing notes | `engine/returns.py`; `compute_year_ahead_events()` calls `scan_return_events()`; Tier 5 Year Ahead surface renders exact returns. | Return-chart interpretation remains deliberately deferred; add sidecar provenance before stronger claims. |
| Annual profections | Calculation unlocked, report-surfaced as timing/context | `engine/profections.py`; `compute_year_ahead_events()` includes `time_lord_periods`; Tier 5 surfaces read annual profections. | Strengthen topic linkage so profection lord/house modifies candidate relevance rather than appearing mostly as a timing note. |
| Solar Arc | Calculation unlocked, selectively client-surfaced | `engine/solar_arc.py`; Year Ahead calls `compute_year_ahead_events(include_year_texture=True)` and selects a small client set. | Promote only after source policy, validation sidecar, and client copy boundaries are stable. |
| Secondary progressions | Calculation unlocked, selectively client-surfaced | `engine/progressions.py`; Personal Forecast can include Moon progressions; Year Ahead can include chapter-scale texture progressions. | Clarify which progression bodies are client-visible versus internal-only; keep angle gating strict. |
| Lots | Calculation unlocked as substrate | `engine/lots.py` computes Fortune, Spirit, Necessity; used by Zodiacal Releasing. | Add explicit sidecar natal snapshot export and user-facing methodology note if surfaced. |
| Zodiacal Releasing | Calculation unlocked, report-surfaced as chapter timing note | `engine/zodiacal_releasing.py`; `compute_year_ahead_events()` scans Fortune and Spirit periods/events; Tier 5 renders grouped notes. | Needs stronger topic-domain integration and sidecar records before it can become a major interpretive claim. |
| Forecast synthesis / cross-clock terrain | Calculation and prose bridge unlocked | `formulas.standard.forecast_synthesis`; `_build_tier5_year_ahead_surfaces()`; templates render forecast terrain. | Needs durable source-event export and explicit confidence/contradiction language for external validation. |
| Proprietary asteroid predictive scanner | Intentionally excluded from active unlock scope | `scan_proprietary_forecast_windows()` exists in `engine/transit_engine.py`, but it is not wired into the active predictive stream. Year Ahead client texture tests reject asteroid progression/Solar Arc variants. | Do not wire into client predictive prose now. Keep asteroid work in natal/soul/portrait layers unless separately approved. |
| Daily Horoscope | Partially active | Daily blocks exist; `_build_horoscope_context()` routes live sky/activation/ruler/proprietary copy. | Confirm `--report-date` reproducibility end-to-end. Prior audit flagged system-date coupling; do not use for scheduled/future replay until verified. |
| Weekly Horoscope | Implemented but content-maturity mixed | Weekly resolver has TODO sentinels and safe fallback to legacy prose. | Finish contact-level authored blocks and decide whether weekly becomes a real client forecast or remains a compact timing product. |

## What Needs Unlocked Next

1. Predictive evidence sidecar

   Create a separate `.eo_predictive.json` output per run. It should include raw events, normalized events, rejected peaks/candidates, daily contributors, time-lord periods, return moments, progression/Solar Arc texture, formula versions, policy versions, ephemeris metadata, confidence components, and report-surface visibility decisions. The current manifest is useful for delivery provenance but is not enough for retrospective validation.

2. Report-surface visibility policy

   Many non-experimental methods still emit `report_surface_visibility: ["internal_rd", "engineering_diagnostic"]` while the Year Ahead template can now display selected outputs. That mismatch needs a formal promotion mechanism, such as:

   - `internal_rd`
   - `technical_appendix`
   - `client_timing_note`
   - `client_contextual_chapter`
   - `client_candidate_support`

   Promotion should require tests, sidecar export, confidence language, and approved copy.

3. Cross-clock topic linkage

   Returns, profections, progressions, Solar Arc, and Zodiacal Releasing should not just coexist in synthesis. They need a shared topic-anchor layer that explains why a method is relevant to a specific natal topic before it contributes to a forecast claim.

4. Asteroid predictive exclusion

   Keep asteroid predictive out of the active unlock path. If it is revisited later, it should start as a separately approved R&D track with sidecar provenance and validation, not as an automatic addition to client prose.

5. Public-safe manifest split

   Current manifests include operational and querent data. Keep the local manifest for private generation, but add a public/partner-safe manifest that strips PII and focuses on method, version, and evidence summaries.

6. Daily and weekly hardening

   Daily needs report-date replay proof. Weekly needs contact-level content completion or a deliberate product-positioning decision that fallback prose is the intended MVP.

## Rune/Tarot Apps: Current State

### What is working

- `:shared-core`, `:rune-app`, and `:tarot-app` are declared in `settings.gradle.kts`.
- Rune and Tarot have distinct app IDs: `com.entangledoracle.rune` and `com.entangledoracle.tarot`.
- `:rune-app:assembleDebug` and `:tarot-app:assembleDebug` both pass.
- Boundary tests confirm the new app modules do not compile each other's UI lane.
- Rune and Tarot preserve distinct identities:
  - Rune: live field cast, entropy lock, Nine Worlds map, rune interpretation, field journal.
  - Tarot: spread picker, locked spread, validated Tarot content pack, reading journal.
- Shared reading records include modality, entropy hash, seed, symbols, positions, orientations, content pack ID, notes, favorite flag, and usefulness feedback.
- Tarot content loading validates card count, card IDs, contiguous indices, spreads, suits, journal prompts, message templates, and learning modules, and blocks TODO/placeholder text.

### What is transitional, not finished

- `:shared-core` compiles source directories from `../app/src/main/java/...` rather than owning files under `shared-core/src/main/...`.
- `:rune-app` and `:tarot-app` also compile UI lanes from the combined app tree.
- The combined `:app` remains a comparison harness and still owns the old shell that imports both rune and tarot.
- Store/release metadata is placeholder-level: version `1.0`, default themes, debug signing, and no release polish.
- Runtime permission flow is not finished. Both standalone apps declare Bluetooth scan/connect permissions, while `EntropyHarvester` suppresses missing-permission lint and starts BLE scanning directly. On modern Android this should be guarded by runtime permission checks or a no-BLE fallback.
- Export/share infrastructure is not implemented despite trust copy saying "unless you choose to export or sync." The copy is careful enough for now only because export/sync do not exist, but future claims need matching flows.
- Notification scheduling is still deferred. Daily prompt preference exists, but Android notification permission, scheduler, and restrained copy are not implemented.
- Persistence is SharedPreferences JSON. This is acceptable for prototype/beta, but Room or another migration-friendly store is better before long-term journals, export, sync, or multiple content packs.

## App Split Finish List

1. Physically relocate source ownership

   Move:

   - `core`, `data`, `storage`, neutral `content`, and `ui/shared` into `shared-core/src/main/...`
   - `ui/rune` into `rune-app/src/main/...`
   - `ui/tarot` into `tarot-app/src/main/...`

   Keep the current boundary tests and add tests that fail if modules point back into `../app/src/main`.

2. Decide content ownership

   Rune should not package Tarot assets. Tarot should package Tarot assets. Shared core should own only neutral models/loaders, or split loaders so Tarot-specific validation does not become shared required weight for Rune.

3. Add runtime permission strategy

   BLE and sensor collection should degrade cleanly:

   - sensors available + BLE unavailable
   - BLE permission denied
   - no Bluetooth adapter
   - background/resume lifecycle

4. Finish journal product layer

   Notes/favorites/usefulness feedback exist. Next useful additions:

   - tags UI
   - export/share reading image or text
   - per-app journal defaults
   - deletion confirmation
   - schema/version migration for saved records

5. Add release checks per standalone app

   Separate smoke tests should assemble and run:

   - `:rune-app:assembleDebug`
   - `:tarot-app:assembleDebug`
   - `:shared-core:testDebugUnitTest` or equivalent
   - app-boundary tests that inspect Gradle source sets

## Highest-Priority Recommendations

1. Build the predictive sidecar before expanding claims.

   The formulas are no longer the slowest part. Evidence export and validation governance are.

2. Treat returns/profections/ZR as "timing/context notes" until topic linkage is stronger.

   They can honestly enrich Year Ahead, but should not yet carry discrete predictive claims.

3. Promote Solar Arc/progressions carefully.

   The code has scoring, gating, and tests. The report copy should stay curated and sparse until source-event evidence is exported and reviewed.

4. Finish physical Android separation next.

   The module split compiles, which is excellent. The next meaningful step is source ownership, not more UI decoration.

5. Fix Android runtime permission handling before outside beta.

   Entropy harvesting is the signature mechanic. It should never fail mysteriously because BLE permission was not granted.

## Verification Run

Report generator:

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.test_phase4_returns_profections `
  tests.test_phase5_solar_arc_progressions `
  tests.test_phase6_lots_zodiacal_releasing `
  tests.test_tier4_forecast_synthesis `
  tests.test_tier5_report_scaffolding `
  tests.test_progression_solar_arc_angle_dedup -v
```

Result: 41 tests passed.

Android:

```powershell
.\gradlew.bat :app:testDebugUnitTest --no-daemon --max-workers=1 --console=plain
.\gradlew.bat :rune-app:assembleDebug :tarot-app:assembleDebug --no-daemon --max-workers=1 --console=plain
```

Result: app unit tests exited successfully; standalone Rune and Tarot debug builds succeeded.
