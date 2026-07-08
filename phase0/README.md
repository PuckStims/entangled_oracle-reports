# Entangled Oracle — Phase 0: Charter and Freeze

Companion to [EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md](../EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md).
Baseline evidence in [EO_MULTICLOCK_ASTEROID_PREDICTIVE_READINESS_AUDIT.md](../EO_MULTICLOCK_ASTEROID_PREDICTIVE_READINESS_AUDIT.md).

**Status: charter. No production code (engines, formulas, templates, JSON block libraries, configs) is modified in Phase 0. All artifacts here are contracts, policies, and specifications — inputs to Phase 1+ implementation.**

Version: `phase0.1.0`
Date: 2026-07-07

## Purpose of Phase 0

Lock the *contracts* that every later phase must respect. When Phase 1 begins the sidecar writer, or Phase 2 wires the proprietary asteroid scanner, or Phase 4 adds return-moment scanners, they should be citing files in this directory, not inventing schemas on the fly.

Per the program: **"Do not code new methods before these are approved."** Approval means an operator sign-off on these documents. They are the "freeze" surface.

## What is here

| # | File | Purpose |
|---|---|---|
| — | `README.md` | This index. |
| 01 | `01_predictive_object_schemas.md` | Field-level contracts for `NatalPromiseAnchor`, `ForecastEvent`, `PredictiveSignal`, `ChapterState`, `MicroCandidate`, `TimeLordPeriod`. |
| 02 | `02_asteroid_predictive_registry.md` | Narrative + tier rationale for all 34 asteroids. |
| 02 | `02_asteroid_predictive_registry.json` | Machine-readable policy per asteroid. |
| 03 | `03_method_charters.md` | Charter set: returns, Solar Arc, secondary progressions, annual profections, Lots + Zodiacal Releasing, additional time-lord family. |
| 04 | `04_convergence_and_candidate_protocol.md` | Cross-clock evidence composition, anti-stacking rules, candidate classes (Weather / Chapter / Trigger / Discrete Candidate), component score preservation. |
| 05 | `05_validation_protocol.md` | Immutable run package, separate outcome ledger, matched-random baseline, research status categories. |
| 06 | `06_sidecar_and_export_contract.md` | `.eo_predictive.json` sidecar contract, daily contributor provenance, rejected-candidate registry, outcome ledger schema. |
| 07 | `07_versioning_and_regression_fixtures.md` | Version-string strategy, regression fixture chart specs, per-phase acceptance fixtures. |

## Reading order for review

1. **02 (asteroid registry)** — most controversial, most policy-dense. Approve first because it constrains every other file.
2. **01 (schemas)** — the object contracts. Every scanner in Phases 4–6 will build to these.
3. **03 (method charters)** — one per clock. Read for anti-double-counting boundaries and confidence policy per clock.
4. **04 (convergence and candidate protocol)** — the assembly logic downstream of everything else. Includes the trigger-derived candidate window rule (candidate width comes from its anchoring evidence, not a fixed cap; `predictive_sandbox` keeps its own separate six-day research cap).
5. **06 (sidecar contract)** — recordkeeping schema. Phase 1's deliverable.
6. **05 (validation protocol)** — how outcomes are coded separately from generation.
7. **07 (versioning and fixtures)** — regression-freeze charts and version-string conventions.

## Non-goals of Phase 0

- No calculation code.
- No new scanners.
- No template changes.
- No governance-registry changes.
- No modifications to `engine/`, `formulas/`, `selectors/`, `generate.py`, `config.py`, or product folders.
- No new dependencies.

## Locked design rules (reminder)

From the program:

1. Existing transit-weather products stay coherent throughout.
2. All 34 asteroids are explicitly governed predictive participants.
3. First-class does not mean identical.
4. Every clock emits the same evidence-grade event contract.
5. One method family, one independent vote.
6. Broad weather and narrow candidates are separate output types.
7. No new clock enters report prose before it enters sidecar and validation.
8. No simplification-by-deletion.

## Definition of "Phase 0 done"

- Every file in this directory has an operator sign-off note in a companion `agents/REVISIONS.md` entry.
- The asteroid registry JSON is machine-loadable and the count is exactly 34.
- The schema contracts have no missing or unresolved fields.
- The method charters each specify: astronomy, house/zodiac assumptions, sect/birth-time dependency, allowed bodies + asteroids, orb policy, event output type, chapter-vs-trigger role, anti-double-counting behavior, topic linkage, confidence limits, report-surface policy, validation rule.
- The sidecar contract specifies every field required for a reproducible predictive run.
- The validation protocol specifies the research status categories and the matched-random baseline procedure.
- Regression fixture specs enumerate at least the eight chart types the program requires.

When those are all true, Phase 1 (Evidence Infrastructure) can start on the sidecar writer.
