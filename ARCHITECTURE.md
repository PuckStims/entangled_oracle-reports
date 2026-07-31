# Entangled Oracle Architecture

## Purpose

Entangled Oracle is a local-first report generator for astrology products.
The active production flow is:

1. Swiss Ephemeris and local chart utilities build a natal payload.
2. Standard and proprietary formula layers derive chart structures and EO indexes.
3. Variable-resolution and report-context builders translate those results into report-facing fields.
4. Block selectors route authored prose from JSON libraries.
5. Jinja templates render HTML.
6. HTML is optionally printed to PDF through the approved browser workflow.

The system is designed to run offline once dependencies and ephemeris files are installed.

## Active Pipeline

### 1. Payload generation

- Entry point: [generate.py](C:/entangled_oracle/generate.py)
- Natal engine: [engine/natal_engine.py](C:/entangled_oracle/engine/natal_engine.py)
- Transit engine: [engine/transit_engine.py](C:/entangled_oracle/engine/transit_engine.py)

The natal payload is the shared source object used by every report type.
It includes:

- standard planets
- selected specialist points and asteroids
- angles
- houses
- aspects
- user profile and birth-time confidence metadata

### 2. Calculation layers

- Standard layer: [formulas/standard_indexes.py](C:/entangled_oracle/formulas/standard_indexes.py) and [formulas/standard/](C:/entangled_oracle/formulas/standard)
- Proprietary layer: [formulas/proprietary_indexes.py](C:/entangled_oracle/formulas/proprietary_indexes.py)
- Trace bundling: [formulas/report_surface.py](C:/entangled_oracle/formulas/report_surface.py)

The standard layer handles core chart structure.
The EO layer extends that structure with proprietary indexes such as KVQ, MKI, RWI, DFIS, Catalyst, AHL, and NGE.

### 3. Resolution and routing

- Variable resolver: [selectors/variable_resolver.py](C:/entangled_oracle/selectors/variable_resolver.py)
- Block selection: [selectors/block_selector.py](C:/entangled_oracle/selectors/block_selector.py)

This stage turns chart data into report-ready fields and selects authored prose blocks using nested JSON key paths plus explicit fallback routing.

### 4. Report assembly

- Main orchestrator: [generate.py](C:/entangled_oracle/generate.py)
- Product assets: [products](C:/entangled_oracle/products)

Active report types:

- `horoscope`
- `personal_forecast`
- `predictive_sandbox`
- `soul_ecosystem`
- `weekly_horoscope`
- `year_ahead`

Each report type has:

- a context builder in `generate.py`
- a template under `products/<report>/templates/`
- one or more authored block libraries under `products/<report>/blocks/`

### 5. Output and traceability

Generated artifacts land in [output](C:/entangled_oracle/output).
Each report writes:

- HTML output
- adjacent manifest sidecar

The manifest records:

- report type and version
- methodology labels
- declared content inputs
- template and formula fingerprints
- trace summaries where available

## Predictive Sandbox: current state and next direction

`predictive_sandbox` is not a consumer report path. It is an
engineering-first diagnostics surface for predictive work. The current
runtime shape is:

1. natal payload generation
2. standard + proprietary index computation
3. transit-derived predictive signal collection in
   [engine/predictive_engine.py](C:/entangled_oracle/engine/predictive_engine.py)
4. daily resonance series with baseline / residual decomposition
5. localized window detection
6. dev-facing render of those windows in the dedicated sandbox template

The active formula version in code is `predictive_v0.3.1`. Its real
implemented strengths are:

- transit-derived signal scoring
- target-aware predictive component routing
- baseline/residual window segmentation
- predictive evidence normalization via
  `method_family`, `event_kind`, `independence_group`,
  `activation_route`
- `leading_index`
- `gradient`
- split between slow structural signals and fast trigger signals
- episode-based memory
- FSM / hysteresis phase continuity for predictive pass state
- signal-level operation profiles with bounded aspect bias
- target-sensitive substrate shaping
- signal-level epistemic confidence scaffolding
- window-level semantic aggregation, coherence scoring, and bounded
  diagnostics for polarity, coalition, counterforce, and complexity
- qualified lunation extraction with eclipse duplicate suppression
- a flat predictive sandbox JSON library routed by computed window
  evidence rather than the retired single-file block map

Its deliberate limits are also important:

- relay / shear topology is not yet implemented
- full interval-sampled epistemic robustness is not yet implemented;
  current `relation_robustness` still includes an exactness-derived
  term with a target-uncertainty modifier
- the renderer's narrative preview is a thin dev aid, not a claim system
- the sandbox currently reasons mostly from transits plus the qualified
  lunation stress-test clock, not a broad multi-clock predictive field

### v0.3 architectural direction

The next predictive expansion should stay engine-first. The current
planning stance is:

- normalize predictive evidence before adding prose complexity
- make the engine multi-clock and lifecycle-aware before expanding
  semantic/pathway theory
- preserve the separation of `intensity`, `coherence`, `memory`, and
  `gradient`
- keep renderer meaning downstream of computed evidence

The strongest near-term path after `v0.3` core is:

1. add bounded semantic atomic mechanics
   target-sensitive operation vectors, aspect bias, epistemic
   confidence scaffolding
2. replace exactness-proxy confidence with real interval robustness
3. harden sandbox-only semantic and content routing coverage against
   real output distributions
4. add bounded new clocks
   exact returns, Solar Arc sandbox, limited secondary progressions
   sandbox
5. leave relay / shear / pathway topology structurally deferred until the
   semantic registry and fixtures stabilize

This direction treats predictive work as a layered computational system:
signal mechanics first, semantic topology second, pathway theory later.

## Methodology and production stance

The active production methodology is:

- Tropical zodiac
- Whole Sign houses
- local Swiss Ephemeris calculation

Angles and specialist bodies are available where supported, but report claims should stay inside the actual birth-time confidence state carried by the payload.

## Current architectural reality

The runtime separation between engine, formulas, selectors, products, and rendering is real.
The main architectural debt is that report orchestration and report-specific helpers still live in a large shared [generate.py](C:/entangled_oracle/generate.py) module rather than product-local context modules.

That is a refactor target, not a statement that the active runtime path is broken.

## Repository boundaries and cleanup posture

This repository is currently preservation-first. The system has working
runtime paths and a broad regression suite, so professionalization should
start with documentation, test discovery, and import-compatible extraction
before any source moves.

### Stable production boundaries

- `generate.py` remains the public CLI and shared report orchestration module.
  Tests and the Flask app import public helpers from this file directly.
- `engine/` owns chart, transit, location, synastry, progression, return,
  local-space, and world-line computation.
- `formulas/` owns standard and EO scoring/ranking layers. Formula behavior
  must not be edited during structural cleanup.
- `selectors/` owns variable resolution and authored-block fallback routing.
  Selector changes are output-affecting and require dedicated verification.
- `products/` owns report templates, product-local assemblers/renderers,
  authored blocks, product docs, and product tooling.
- `content/eia/` owns Internal Architecture content packs; `eia_engine/`
  owns the bounded EIA scoring/report-building subsystem.
- `app/` owns the local Flask workflow and delegates report generation back
  through `generate.generate_report`.

### Generated, local, and historical areas

- `output/`, `tmp/`, `audit_output/`, `runtime/`, Python caches, frontend
  build artifacts, and mobile build artifacts are generated/local material.
- `archive/` and `quarantine/` are historical or intentionally isolated
  material. They should be documented before being moved or removed.
- Untracked large folders such as `entangled-dashboard-v0.1/`,
  `entangled-astrology-v0.1/`, and `eia_concept_research_v0_1/` need an
  owner decision before they become production source, documented research,
  or ignored local workspaces.

### Refactor order

1. Keep current paths stable and make tests collect predictably.
2. Add preservation output comparisons for representative reports.
3. Extract from `generate.py` only through import-compatible wrappers.
4. Move product docs/drafts/generated files only after path usage is proven.
5. Require human review for formulas, selectors, content libraries,
   templates, report copy, astrology methodology, and rendered output changes.
