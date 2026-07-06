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

The active formula version in code is `predictive_v0.2`. Its real
implemented strengths are:

- transit-derived signal scoring
- target-aware predictive component routing
- baseline/residual window segmentation
- `leading_index`
- `gradient`
- split between slow structural signals and fast trigger signals

Its deliberate limits are also important:

- `coherence` is currently a placeholder field
- `memory` is currently a placeholder field
- the renderer's narrative preview is a thin dev aid, not a claim system
- the sandbox currently reasons mostly from the transit engine rather
  than a broader multi-clock predictive field

### v0.3 architectural direction

The next predictive expansion should stay engine-first. The current
planning stance is:

- normalize predictive evidence before adding prose complexity
- make the engine multi-clock and lifecycle-aware before expanding
  semantic/pathway theory
- preserve the separation of `intensity`, `coherence`, `memory`, and
  `gradient`
- keep renderer meaning downstream of computed evidence

The strongest near-term path is:

1. normalize event taxonomy using method family vs event kind vs
   independence group
2. add bounded new clocks
   lunations, eclipses, exact returns, Solar Arc sandbox, limited
   secondary progressions sandbox
3. implement an episode-based memory layer
4. add target-sensitive operation typing
5. add sandbox-only semantic field metrics
   coherence, polarity, coalition, counterforce, complexity
6. leave epistemic pathway topology structurally deferred until the
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
