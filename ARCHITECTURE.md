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
- `weekly_horoscope`
- `personal_forecast`
- `soul_ecosystem`
- `identity_profile`
- `internal_architecture`
- `year_ahead`
- location services reports routed through `products.location_services`
- `synastry`

Most standard report types have:

- a context builder in `generate.py`
- a template under `products/<report>/templates/`
- one or more authored block libraries under `products/<report>/blocks/`

Location services reports use the product registry and rendering facade under
`products.location_services`. Synastry has a dedicated generation path.

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

## Predictive Sandbox: quarantined history

`predictive_sandbox` is not an active CLI or consumer report path. The former
engineering diagnostics surface and its tests were moved under
`quarantine/predictive_testable_v0_1/` and should be treated as historical R&D
unless explicitly revived. The historical runtime shape was:

1. natal payload generation
2. standard + proprietary index computation
3. transit-derived predictive signal collection in
   [engine/predictive_engine.py](C:/entangled_oracle/engine/predictive_engine.py)
4. daily resonance series with baseline / residual decomposition
5. localized window detection
6. dev-facing render of those windows in the dedicated sandbox template

The quarantined formula version was `predictive_v0.3.1`. Its real
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

## Shared document-output architecture

HTML remains the production source for the existing browser-to-PDF workflow.
DOCX is an additional output path; it does not replace or alter the Jinja
templates.

```text
domain/runtime computation -> completed report context
                                  |             |
                                  |             +-> report composer -> ReportDocument -> output renderer
                                  +-> existing Jinja HTML renderer
```

The context is not a document model. It is a broad template-facing collection
of computation results and selected prose. A composer adapts that completed
context into ordered, reusable semantic nodes such as `Section`, `Paragraph`,
`EventCard`, `DataTable`, and `Figure`. It must not recompute astrology or
select alternative prose.

`products.shared.document_model` is format-neutral and contains no
`python-docx` types. `products.shared.composers` is an explicit registry of
context-to-document adapters. The renderer receives only the shared document
model: renderers must never branch on report/product type. Conversely,
composers never branch on output format or specify fonts, Word borders,
colours, page margins, or table widths.

Output configuration is represented by `OutputOptions` and supplied separately
from birth data. `generate_report(..., formats=("html", "docx"))` retains HTML
as the default and can create a matched DOCX for a report with a registered
composer. The CLI mirrors this with repeatable `--format html` / `--format
docx` flags.

Semantic tones (for example `flowing`, `pressure`, `threshold`, and
`structure`) are retained on nodes. Renderer-level themes map them to actual
formatting. Figures preserve media type, source, alternative text, caption, and
fallback text; the current DOCX renderer uses the fallback for SVG while a
future renderer can add native SVG or raster support without composer changes.

Parity is explicit rather than inferred from a shared context. Composers attach
a small manifest of context paths and semantic section markers. The parity
validator flags any marker omitted while its context source is present. New
report types should add a composer, parity manifest, and composer test; new
formats should add a renderer for existing document nodes rather than per-report
renderers. Synastry and location-service runtimes remain independent until their
already-assembled contexts are ready to join this registry.

### Current composer coverage

The shared registry currently composes `year_ahead`, `personal_forecast`,
`soul_ecosystem`, `horoscope`, `weekly_horoscope`, `identity_profile`, and
`internal_architecture`. They retain their existing context builders and HTML
templates. `synastry` and location-service reports are intentionally deferred:
they have independent assemblers and must contribute a context-specific
composer rather than being forced through `generate_report`.
