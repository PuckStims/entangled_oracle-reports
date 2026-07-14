# Location Services Build Plan

Status date: 2026-07-14

This is the working build plan for getting Location Services out of scattered
scaffolding and into a reverse-engineered production pipeline. It is
intentionally not a lean plan. The goal is to protect the depth of all products
while keeping the build order grounded in what the repo can actually run.

## Current Repo Truth

- Place Resonance Search is now the intended flagship discovery product.
- The existing Place Resonance implementation is the reusable single-place
  profile engine. It has the real relocated payload path, selector coverage,
  assembler tests, renderer tests, and astrocartography SVG coverage.
- `products/location_services/place_resonance_search/` is registry-wired, but
  currently wraps the existing single-place profile output until candidate
  catalog, scoring, curation, and bucket logic are built.
- Between Places, World Lines Companion, Local Compass, and Living Map have
  draft product shells, assemblers, renderers, templates, and registry plugins.
- The registry is useful as a product-family entry point, but it is not yet the
  production report-generation path.
- The four newer product shells currently render premium draft HTML from shaped
  placeholder contexts. They do not yet consume production
  `LocationEvidenceRecord` data.
- The central `generate.py` report-type router has not been expanded for these
  products, which is correct until evidence contracts are real.

## Build Principle

Reverse-engineer the pipeline from the working single-place profile outward:

1. Preserve the current Place Resonance implementation as the known-good
   single-place profile engine.
2. Extract and keep testing the evidence contract it actually uses.
3. Build Place Resonance Search on top of batch profile evidence, scoring,
   curation, and bucket assignment.
4. Build later descendants from that contract, not from visual templates first.
5. Let each product keep its own depth, section map, and future methods without
   flattening them into one generic location report.

## Phase 1: Stabilize Place Profile As The Reference Unit

The current Place Resonance code path should be treated as the proof that
Location Services can run. Its long-term architectural role is the reusable
Place Profile unit used inside Search, Between Places, and later products.

Required work:

- Keep the focused Place Resonance / Place Profile test suite green.
- Document the real input payload shape accepted by the relocated chart
  pipeline.
- Document the current `LocationEvidenceRecord` fields and which template
  sections consume them.
- Mark every selector leaf by evidence dependency: relocated angles, relocated
  house movement, synthesis ranking, technical appendix, and map/SVG evidence.
- Add one known-good local sample generation command and expected output file
  path.

Exit criteria:

- A developer can run the focused tests and generate one sample profile report
  without reading old roadmap docs.
- The reference evidence contract is written in repo-local docs and matches
  tests.

## Phase 2: Build The Place Resonance Search Contract

Place Resonance Search should become a real curated discovery product before it
is treated as production output.

Current implementation status:

- Fixture-backed candidate catalog exists.
- Batch Place Profile evidence generation exists.
- First-pass deterministic scoring exists.
- Bucket assignment and curated selection exist.
- Search result context assembly exists.
- Search-level prose scaffold exists with intentional TODO leaves.
- True multi-location HTML rendering exists.
- Fixture-backed Search HTML generation exists through
  `products/location_services/tooling/generate_place_resonance_search_ready.py`.

Required work:

- Create a curated U.S. candidate location catalog with location IDs, display
  names, coordinates, timezone identifiers, region, population tier, source,
  active flag, and notes.
- Run the Place Profile evidence builder for each candidate without mutating
  the natal payload.
- Define score fields for overall resonance, theme fit, complexity or pressure,
  consensus, grounding, and baseline divergence.
- Define the first theme vector: visibility/calling, belonging/bonds,
  hearth/restoration, study/signal, creative culture, long-term build,
  change/aliveness, and shadow pressure.
- Add curated selection rules so the report is not just a top-score list.
- Assign selected places to buckets: Highest Resonance, Goal-Specific Allies,
  Transformational / Demanding Places, Quiet or Grounding Alternatives, and
  Pattern Outliers.
- Add search-level prose routing for summary, bucket explanations, location
  recommendations, and pattern synthesis.

Exit criteria:

- Place Resonance Search can evaluate a small local candidate fixture and return
  selected locations with scores, bucket labels, evidence references, and
  compact profile context.
- Tests prove batch generation does not mutate the natal payload or candidate
  records.
- The product still tells the truth when the candidate pool is a fixture rather
  than a complete U.S. catalog.

## Phase 3: Normalize The Four New Product Shells

The four draft products should remain expansive, but their contexts need to
stay aligned with the working profile evidence contract.

Required work:

- Rename or map placeholder fields to production evidence names where the
  reference contract already exists.
- Use `relocated_angle_contacts` for angle contact evidence.
- Use `planet_house_changes` for relocated planetary house movement evidence.
- Keep future-only methods explicit with `is_future_method`, but do not treat
  them as computed outputs.
- Add product-level contract notes for each assembler explaining which fields
  are live, placeholder, or future.

Exit criteria:

- Every new product shell can explain exactly which parts are currently backed
  by Place Profile evidence and which parts are presentation-only.
- Registry smoke tests confirm all shells still build context and render HTML.

## Phase 4: Make Between Places The First Comparison Descendant

Between Places is the best next comparison product because it can reuse Place
Profile twice before inventing new engine math.

Required work:

- Run the Place Profile evidence builder independently for Destination A and
  Destination B.
- Build a comparison record from two immutable `LocationEvidenceRecord` outputs.
- Separate comparison evidence into shared signatures, divergent signatures,
  angular emphasis differences, house movement differences, and technical
  appendix per destination.
- Add selector leaves for comparison-specific language instead of forcing
  single-place prose into a two-place report.
- Add tests for equal destinations, missing destination metadata, and asymmetric
  evidence.

Exit criteria:

- Between Places can generate a report from two real relocated evidence records.
- The comparison layer is tested without mutating either single-place record.

## Phase 5: Keep World Lines Companion Contract-First

World Lines Companion should not be wired as a pretty astrocartography shell
until the map/line evidence contract exists.

Required work:

- Define the minimum line evidence schema: planet, angle line type, distance
  from destination, orb/band, interpretation weight, and map trace metadata.
- Reuse existing astrocartography SVG work only where it can provide auditable
  map evidence.
- Separate calculated line proximity from interpretive line meaning.
- Add technical appendix language for map projection, line tolerance, and
  missing geometry.

Exit criteria:

- World Lines has a tested line-evidence contract before it enters production
  routing.

## Phase 6: Keep Local Compass Directional

Local Compass depends on Local Space style directional/azimuth evidence, so it
should not be built from relocated house movement alone.

Required work:

- Define directional evidence: planet, azimuth, bearing, distance context if
  used, directional house/sign framing if used, and confidence limits.
- Decide whether local directions are computed from birthplace, current
  location, destination, or all three.
- Add explicit tests for cardinal/intercardinal bucketing and azimuth wraparound.
- Keep Place Profile evidence available as supporting context, not as the
  primary Local Compass method.

Exit criteria:

- Local Compass has a directional evidence contract that can be calculated and
  audited independently.

## Phase 7: Keep Living Map As Dynamic Timing Overlay

Living Map is likely the most complex product because it combines location with
time. It should stay contract-first until static products are stable.

Required work:

- Define whether the first live version uses transits, progressions, solar arcs,
  annual profections, or a smaller timing subset.
- Define a time-window schema: start, end, active body, trigger type, target
  location evidence, intensity, and interpretation rationale.
- Decide whether Living Map overlays timing onto Place Profile, Between Places,
  or World Lines evidence.
- Add tests for overlapping timing windows and missing ephemeris data.

Exit criteria:

- Living Map has a timing overlay contract and does not claim dynamic outputs
  before a timing method is selected.

## Phase 8: Production Routing

Production routing should happen after at least Place Profile plus Place
Resonance Search have real contracts. Between Places should follow when its
comparison record is tested.

Required work:

- Decide whether the registry becomes the production routing layer or remains a
  product-family entry point used by dedicated scripts.
- Add CLI/API arguments for candidate search, destination count, and
  product-specific options.
- Add sample generation scripts for each product as they become evidence-backed.
- Add output naming rules that distinguish search, one-place profile,
  two-place comparison, map, compass, and timing products.

Exit criteria:

- A product is only added to production routing when it has real evidence
  inputs, tests, and a sample generation path.

## Do Not Do Yet

- Do not wire draft shells into `generate.py` as if they are production products.
- Do not treat future-method sections as computed evidence.
- Do not let visual template polish replace evidence-contract work.
- Do not flatten the products into one generic Location Services report.
- Do not ask Gemini to build engine wiring until the target contract for that
  product is written.

## Immediate Verification Commands

Run the focused Location Services suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_location_services_relocated_payload.py tests\test_location_services_selector.py tests\test_place_resonance_assembler.py tests\test_place_resonance_renderer.py tests\test_astrocartography_svg.py tests\test_location_services_product_registry.py tests\test_place_resonance_search_package_layout.py -q
```

Compile the touched renderers and tests:

```powershell
.\.venv\Scripts\python.exe -m py_compile products\location_services\between_places\renderer.py products\location_services\world_lines_companion\renderer.py products\location_services\local_compass\renderer.py products\location_services\living_map\renderer.py tests\test_location_services_selector.py tests\test_location_services_product_registry.py tests\test_place_resonance_search_package_layout.py
```
