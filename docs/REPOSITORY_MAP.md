# Repository Map

This map reflects the current production shape. It is intentionally practical:
what runs, what owns what, and what should be treated carefully.

## Main Execution Paths

- `generate.py`: CLI entrypoint, input parsing, report orchestration, context
  building, template rendering, output writing, and manifest writing.
- `run_app.py` and `app/`: local Flask app. `app.services.report_service`
  calls `generate.generate_report`.
- `scripts/`: operator and fixture utilities. New preservation checks should
  live here unless they become test fixtures.

## Production Source

- `engine/`: computational engines for natal charts, transits, forecast
  events, location services, synastry, progressions, returns, lots, local
  space, living map, world lines, chart wheels, and SVG contracts.
- `formulas/`: scoring and formula layers, including standard astrological
  modules, EO proprietary indexes, governance registry, and report-surface
  trace bundling.
- `selectors/`: block selection, fallback routing, synastry selection,
  location-services selection, and variable resolution.
- `products/`: product-owned report assets. Most active report types have
  `blocks/` and `templates/`; some newer products also have local
  `assembler.py`, `renderer.py`, and `plugin.py` files.
- `content/eia/`: Internal Architecture content catalogs and public copy.
- `eia_engine/`: Internal Architecture models, feature extraction, scoring,
  mode selection, state overlay, content loading, and report building.
- `visuals/`: shared visual helpers, currently including synastry SVG support.
- `config.py`: central path constants, report block directories, thresholds,
  mappings, palettes, and content-pack wiring.
- `product_versions.py`: report versions, template paths, content/file
  fingerprinting, manifest registry construction, and JSON writing.

## Tests And Verification

- `tests/`: active regression and contract tests.
- `tests/eia/`: EIA-specific tests.
- `test_offline_location.py`: root-level offline location and ephemeris-path
  tests.
- `scripts/compare_preservation_outputs.py`: representative report diff gate
  for preservation refactors.

## Generated Or Local Material

- `output/`: generated HTML/PDF reports and manifest sidecars.
- `tmp/`: scratch baselines, browser profiles, layout checks, temporary PDFs,
  and old workspaces.
- `audit_output/`: generated audit samples.
- `runtime/`: local runtime state.
- `__pycache__/`, `.pytest_cache/`, `.venv/`: Python local artifacts.
- `outputs/`: currently separate from the active `output/` report directory;
  treat as generated/local unless a human owner promotes it.

## Historical, Draft, And Research Areas

- `archive/`: historical audits, bundles, docs, staging material, and content
  orphans.
- `quarantine/`: isolated predictive sandbox history. Keep physically present
  until explicitly archived or removed by the owner.
- `agents/`: cross-session notes, revision logs, prompts, and upgrade planning.
- `phase0/`: predictive architecture specifications and registries.
- Root audit docs: current evidence and planning records. Index before moving.
- `eia_concept_research_v0_1/`: untracked research package; owner decision
  needed before production integration or archive placement.
- `entangled-dashboard-v0.1/` and `entangled-astrology-v0.1/`: untracked
  frontend/mobile subprojects; owner decision needed before tracking or
  ignoring as external workspaces.

## High-Risk Boundaries

- Do not edit formulas, ranking/scoring weights, transit logic, ephemeris
  behavior, selector fallback paths, content libraries, templates, public copy,
  or rendered output without explicit review.
- Do not move product paths until imports, manifest fingerprints, and generated
  output diffs are understood.
- Do not split `generate.py` by rewriting logic. Extract small, mechanical
  helpers first and preserve legacy imports from `generate.py`.
