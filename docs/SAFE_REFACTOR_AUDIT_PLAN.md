# Safe Refactor Audit Plan

Date: 2026-07-31

## Working Mindset

This is a preservation-first cleanup plan. The priority is to reduce cognitive load, make the stack feel professional and navigable, and protect the quality of computations, report wiring, manifests, templates, and rendered output.

No computation, selector, content, or rendering behavior should change without an explicit regression gate. During this review phase, visible `[TODO]`, `[BLOCK NOT FOUND]`, and `[MISSING BLOCK FILE]` markers are intentional: they are how the operator spots authoring and routing gaps.

## Current Reality

- `generate.py` is the main operational debt: about 10.6k lines, 280 top-level functions, and multiple report families in one module.
- The active runtime separation is real: `engine/`, `formulas/`, `selectors/`, `products/`, and `app/` already carry meaningful boundaries.
- Tests import many private helpers directly from `generate.py`, so extraction must keep compatibility shims until tests and call sites are migrated.
- Configured content paths in `config.CONTENT_PACKS`, `config.REPORT_BLOCK_DIRS`, and `product_versions.TEMPLATE_MAP` currently resolve successfully.
- CLI report choices include report types not represented in `product_versions.REPORT_TYPE_VERSIONS` and `TEMPLATE_MAP`, because location-services reports route through `products.location_services.routing` instead of the normal Jinja template map.
- `pytest --collect-only -q` is not clean from the repo root. Collection currently walks quarantined and temporary workspaces and raises import errors, including local `selectors` package collisions and duplicate test-module names under `tmp/yearahead_baseline_workspace`.
- Root and product docs include a mix of active public docs, agent/operator logs, historical predictive-sandbox work, duplicate README files, and future-method scaffolds.

## Immediate Audit Findings

### Truthfulness Gate Added In Phase 2.1

- Simple / DOB-only payloads may use a noon internal placeholder for
  planet-sign math, but that placeholder must not surface as natal house,
  angle, twelfth-house, or house-theme evidence.
- When exact birth time is unavailable, daily activation may still name a real
  activation planet, but house localization and natal house naming are
  withheld.
- Exact-birth-time payloads must keep their real houses and angles; the gate is
  intended to prevent fake precision, not reduce valid computation quality.
- Review builds should continue to show TODO / missing-block markers visibly
  so authoring and routing gaps are auditable.

### Preserve

These are active public/professional docs or close to it:

- `README.md`
- `ARCHITECTURE.md`
- `METHODS.md`
- `docs/SYNASTRY_ENGINE_CONTRACT.md`
- `docs/prose_guides/`
- `products/shared/CLIENT_METHOD_AND_LIMITS.md`
- `products/shared/LOCAL_GENERATION_PROCEDURE.md`
- `products/shared/PRE_DELIVERY_QC_CHECKLIST.md`
- `products/shared/REPORT_PDF_WORKFLOW.md`
- `products/shared/VERSIONING_POLICY.md`
- product-local schema and contract docs that match live tests

### Repaired In Place In Phase 1

- `README.md` no longer says to replace a payload stub; it identifies the live natal engine call.
- `generate.py` module docstring now includes `--location` in the simple horoscope example.
- `ARCHITECTURE.md` no longer lists `predictive_sandbox` as an active report path and now marks it as quarantined historical R&D.

### Still Repair In Place

- `product_versions.py` should either version all CLI-visible report types or explicitly document why location-services and synastry bypass the standard template/version registry.

### Moved To Miscellaneous / Historical In Phase 1

Moved to `docs/misc/historical-audits/`:

- root-level dated audits and phase prompts:
  - `CLIENT_FORECAST_CLAIM_CLEANUP_QUEUE.md`
  - `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md`
  - `CODEX_BRIEF_PHASE_D_YEAR_TEXTURE.md`
  - `ENGINE_CAPABILITY_SURFACE_AUDIT.md`
  - `ENGINE_CAPABILITY_SURFACE_AUDIT.json`
  - `EO_MULTICLOCK_ASTEROID_PREDICTIVE_READINESS_AUDIT.md`
  - `EO_MULTICLOCK_ASTEROID_PREDICTIVE_READINESS_AUDIT.json`
  - `EO_PHASE_D_E_REMAINING_WORK.md`
  - `EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md`
  - `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`
  - `HOROSCOPE_PROSE_COVERAGE_AUDIT.md`
  - `LIGHTWEIGHT_FORECAST_SURFACE_AUDIT.md`
  - `PHASE2_SIDECAR_BODY_CLASSIFICATION_FINDING.md`
  - `PHASE3_ASTEROID_POLICY_REVIEW.md`

### Still Candidate For Miscellaneous / Historical

- `phase0/` predictive planning docs, unless still cited by live code or tests.
- `products/location_services/gemini_expansion_pass_01/`, clearly labeled as historical draft material.
- duplicate identity-profile tooling README: keep one canonical file, move `README_FIRST (1).md`.
- `products/past_life/` docs if the product is not exposed in CLI, app registry, or tests.
- `agents/MUSINGS.md` and high-throughput prompt archives if the professional stack should not surface internal agent culture by default.

Recommended destination: `docs/misc/` with subfolders:

- `docs/misc/historical-audits/`
- `docs/misc/internal-agent-notes/`
- `docs/misc/predictive-sandbox-history/`
- `docs/misc/draft-product-lanes/`

Do not move files from `quarantine/`, `tmp/`, `archive/`, or generated output as part of documentation cleanup until test discovery and `.gitignore` boundaries are fixed.

## Refactor Strategy For `generate.py`

### Phase 0: Stabilize The Floor

1. Add or update pytest configuration so root test runs exclude `quarantine/`, `tmp/`, build outputs, generated outputs, and app package build products.
2. Confirm a clean collection boundary for active tests only.
3. Add a smoke-test command matrix for active CLI reports:
   - `horoscope`
   - `weekly_horoscope`
   - `year_ahead`
   - `personal_forecast`
   - `soul_ecosystem`
   - `identity_profile`
   - `internal_architecture`
   - location-services reports
   - `synastry`
4. Capture output-manifest fingerprints before extraction where feasible.

### Phase 1: Documentation Hygiene

1. Fix stale public docs in place.
2. Create the `docs/misc/` structure.
3. Move historical/internal docs in small batches.
4. After each batch, run `rg` for moved filenames and update live references.
5. Keep one root-level orientation path: `README.md` -> `ARCHITECTURE.md` -> `METHODS.md` -> product docs.

### Phase 2: Extract Low-Risk Utilities

Move pure helpers first, keeping re-export imports in `generate.py`:

- report windows, output filenames, ephemeris reset, env flags, verbose
  logging, and atomic writes -> `engine/report_io.py` (completed
  2026-07-31)
- input parsing and validation -> `engine/report_inputs.py` (completed
  2026-08-01)
- manifest writing helpers -> a dedicated report manifest module
- formatting helpers with no report-specific state -> a dedicated formatting module

Regression gate: active unit tests plus representative CLI smoke tests must produce equivalent visible output and expected manifest fields.

### Phase 3: Extract Report Context Builders

Move context logic product by product:

- horoscope -> `products/daily_horoscope/runtime/context.py`
- weekly -> `products/weekly_horoscope/runtime/context.py`
- personal forecast -> `products/personal_forecast/runtime/context.py`
- soul ecosystem -> `products/soul_ecosystem/runtime/context.py`
- year ahead -> split into smaller modules under `products/year_ahead/runtime/`

Keep `generate.py` as a facade that imports and re-exports private helper names until tests are migrated.

Regression gate: product-specific tests must pass before starting the next product extraction.

### Phase 4: Normalize Registries

Create one authoritative report registry that answers:

- CLI availability
- app availability
- consumer/internal status
- template/rendering path
- report version
- content-pack support
- manifest identity

Then make `generate.py`, `app/services/report_registry.py`, and `product_versions.py` consume it.

### Phase 5: Retire Compatibility Shims

Only after imports and tests are migrated:

- remove private-helper imports from tests where possible
- keep public API names stable
- shrink `generate.py` to CLI, high-level orchestration, and backwards-compatible entry points

## Safety Gates

- Raw `[TODO]`, `[BLOCK NOT FOUND]`, and `[MISSING BLOCK FILE]` markers remain visible in operator review output until the owner explicitly changes the policy.
- No accidental marker suppression in client-facing review builds.
- No configured content path missing.
- Active pytest collection excludes quarantine and scratch directories.
- Smoke reports generate without opening the browser.
- Report manifests still include content, formula, template, and generation-code fingerprints.
- Any intentional output change is reviewed as a product change, not hidden inside refactor work.

## Suggested First Implementation Batch

1. Add pytest collection exclusions for `quarantine/`, `tmp/`, build output, generated output, and node/build artifacts.
2. Fix the two stale public statements in `README.md` and `generate.py`.
3. Update `ARCHITECTURE.md` to mark predictive sandbox as quarantined/historical unless intentionally revived.
4. Create `docs/misc/` and move the root-level historical audits in one batch.
5. Run reference checks and active smoke tests.
