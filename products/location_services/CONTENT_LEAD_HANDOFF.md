# Content Lead Handoff For Location Services

**Status:** Round 3 reconciled content handoff; Round 4 block scaffold delivered (see "Round 4 Update" below).  
**Owner:** ChatGPT content-analysis lane.  
**Consumer:** Claude / implementation-review lane.

## Current Direction Overlay

This handoff includes historical rounds that were written when Place Resonance
was treated as the long-term flagship. The current product direction is:

- **Place Resonance Search** is the flagship discovery/search product.
- The existing Place Resonance implementation is the reusable single-place
  **Place Profile** engine.
- Content work already authored for Place Resonance remains valuable, but its
  long-term role is profile prose and reusable evidence interpretation inside
  Search, Between Places, and later products.

When older notes say "build Place Resonance first," read that as "keep the
single-place profile engine stable before building search, comparison, map,
directional, or timing products."

## Files Created

```text
products/location_services/PRODUCT_STACK.md
products/location_services/PROSE_GUIDE.md
products/location_services/EVIDENCE_TO_MEANING_MATRIX.md
products/location_services/BLOCK_SCHEMA.md
products/location_services/CONTENT_REFERENCES.md
products/location_services/PROSE_PURPOSE_REVIEW.md
products/location_services/CONTENT_AUDIT_PERSONAS.md
```

## Reconciliation Update

Claude Code has now delivered and sampled the v0.1 evidence record. `BLOCK_SCHEMA.md` has been revised against:

```text
products/location_services/LOCATION_EVIDENCE_RECORD_CONTRACT.md
products/location_services/LOCATION_EVIDENCE_RECORD_SAMPLES.md
products/location_services/BLOCK_SCHEMA_RECONCILIATION.md
```

The original validation questions are considered answered for v0.1. Future implementation work should treat `BLOCK_SCHEMA.md` as the current content-facing contract, not the first-pass sketch.

## Round 3 Update

Claude Code completed two bounded fixes after schema reconciliation:

- `natal_modifiers[body].confidence` now reflects the chart's actual birth-time confidence, including approximate and unknown birth-time charts.
- `warning_summary` now exists at both top level and `appendix_trace.warning_summary`, while raw `warnings` remains unchanged for audit/debug use.

`BLOCK_SCHEMA.md` has been updated to treat both as current v0.1 evidence fields.

## Round 4 Update

Claude Code built the first Place Resonance block scaffold against
`BLOCK_SCHEMA.md` and `PROSE_PURPOSE_REVIEW.md`, under:

```text
products/location_services/blocks/plainspeak/
```

Files created:

```text
technical_appendix_blocks.json          19 leaves  -- calculation_note, unsupported_method,
                                                       confidence_note, coordinate_precision_note, warning_summary
relocated_angle_contact_blocks.json    177 leaves  -- angle -> body -> contact_strength (Sun-Pluto explicit,
                                                       Chiron/node/Lilith coverage via a fallback body block per angle;
                                                       EO custom asteroids are excluded from Location Services)
planet_relocated_house_blocks.json     539 leaves  -- body -> relocated_house(1-12) -> movement_type (Sun-Pluto
                                                       explicit, same fallback-body pattern; movement_type keys per
                                                       house are restricted to what is astronomically reachable --
                                                       angular houses never show leaves_angular, non-angular houses
                                                       never show newly_angular)
location_synthesis_blocks.json          10 leaves  -- the 9 named categories from PROSE_PURPOSE_REVIEW.md
                                                       (convergent_place_signature, angle_led_signature,
                                                       house_shift_led_signature, repeated_body_signature,
                                                       quiet_continuity_signature, mixed_public_private_signature,
                                                       purpose_aligned_signature, purpose_tradeoff_signature,
                                                       low_signal_signature) plus fallback
```

All 745 leaves are literal `"body": "TODO"` with a rich `_note`,
`claim_level` (`bounded_interpretation` for the three interpretive files,
`technical_disclosure` for the technical appendix), and `requires_evidence`
pointing at real evidence-record field paths -- no final reader-facing
prose was written. Structural contract verified by 52 new tests in
`tests/test_location_services_block_scaffold.py` (canonical angle names
only, real contact-strength bands, real movement types with the deferred
`moves_public`/`moves_private`/`moves_relational`/`moves_operational`
domain taxonomy absent everywhere, `warning_summary`/`unsupported_method`
keys cross-checked against the actual engine constants, every TODO leaf
carries its required scaffold fields).

One addition beyond `BLOCK_SCHEMA.md`'s literal text: `technical_appendix_blocks.json`
adds a `coordinate_precision_note` family, since `appendix_trace.coordinate_precision`
is named in that block family's required-evidence list but no selector key
path was proposed to render it. Flag if a different key name is preferred
-- nothing downstream depends on this name yet.

`mixed_public_private_signature` in `location_synthesis_blocks.json` is
scaffolded on a narrower, already-computable signal (Midheaven/Ascendant
angle contacts vs. Imum_Coeli/Descendant ones) rather than the deferred
house-domain taxonomy -- its `_note` says so explicitly (`TAXONOMY NOT
IMPLEMENTED (full version)`), per the standing instruction to defer
contradiction/conflict categories unless they can be scaffolded with that
kind of explicit boundary note.

No engine files were touched this round -- no loader/selector exists yet
to wire these files into, and none was required to validate them (the
test file reads the JSON directly).

## Round 5 Content Start

Codex began the first bounded prose-fill pass while preserving the large
grid scaffolds for later authorship:

```text
products/location_services/blocks/plainspeak/technical_appendix_blocks.json
products/location_services/blocks/plainspeak/location_synthesis_blocks.json
```

Historical authoring status at the end of Round 5:

- `technical_appendix_blocks.json` now has authored first-pass `body` text for all 19 leaves.
- `location_synthesis_blocks.json` now has authored first-pass `body` text for all 10 leaves.
- `relocated_angle_contact_blocks.json` was still TODO-only.
- `planet_relocated_house_blocks.json` was still TODO-only.

That distinction is no longer current; see Round 6 below for the active
status.

## Round 6 Content Audit Status

The large grid prose pass has now occurred. Current authoring status:

- `technical_appendix_blocks.json` has authored `body` text for all 19 leaves.
- `location_synthesis_blocks.json` has authored `body` text for all 10 leaves.
- `relocated_angle_contact_blocks.json` has authored `body` text for all 241 leaves.
- `planet_relocated_house_blocks.json` has authored `body` text for all 731 leaves.

`tests/test_location_services_block_scaffold.py` now enforces the current
state: every Place Resonance block leaf must have a non-empty body, must
not be literal `TODO`, and must carry `_note`, `claim_level`, and
`requires_evidence`.

## Prose Purpose Review

Before block scaffolding, the content lane reviewed representative active JSON block libraries across Daily, Weekly, Year Ahead, Personal Forecast, Soul Ecosystem, and Identity Profile:

```text
products/location_services/PROSE_PURPOSE_REVIEW.md
```

The working conclusion is that Location Services blocks should be evidence-shaped interpretive modules, not generic prose inserts. The first block pack should prioritize technical appendix, relocated angle contacts, relocated houses, and location synthesis; later purpose, duration, natal-modifier, and house-shift families should wait for selector taxonomy or final prose ownership.

## Multi-Agent Optimization Flow

The preferred Location Services build flow now uses two named partner lanes plus Codex as the local repo integrator:

```text
ChatGPT / Codex -> product direction, content architecture, prose purpose, evidence boundaries, local repo verification
Claude          -> implementation review, architecture critique, stabilization guidance, flaw-finding
Gemini          -> high-throughput first-pass breadth, product-suite scaffolding, basic infrastructure proposals
```

Gemini is useful for opening pathways and laying down broad scaffolds quickly. Gemini output should be treated as an expansion draft, not as architectural truth. Claude and ChatGPT/Codex should expect flaws and focus on auditing, fixing, upgrading, and reconciling rather than asking Gemini to be final.

Because Claude may operate outside this local Codex workspace, Claude review can be advisory rather than directly committed. Codex remains responsible for applying any accepted local edits, running local verification, preserving repo boundaries, and keeping the committed workspace coherent.

### Gemini Is Allowed To Do

- Create first-pass Location Services folder structures.
- Draft non-client-facing product-suite outlines and implementation checklists.
- Scaffold TODO-only JSON block grids when a schema already exists.
- Add `_note`, `_version`, fallback, and test-oriented metadata to scaffold files.
- Propose basic loader or selector integration plans for later Claude/Codex review.
- Create repo-local planning docs that clearly label themselves as drafts.

### Gemini Must Not Do

- Do not write final consumer-facing prose.
- Do not replace `TODO` placeholders with reader-facing report text.
- Do not modify final prose guides, reference prose, or active non-location block libraries.
- Do not modify engine calculations, astronomical formulas, standard condition logic, confidence logic, sect logic, or natal/relocated condition boundaries.
- Do not treat unsupported methods as implemented: astrocartography, Local Space, parans, dynamic timing overlays, relocated returns.
- Do not invent house-domain taxonomy, contradiction taxonomy, or purpose-fit taxonomy as final truth.
- Do not change existing Year Ahead, Personal Forecast, Daily, Weekly, Soul Ecosystem, or Identity Profile behavior.
- Do not rank locations as best/worst or imply guaranteed love, wealth, success, danger, healing, destiny, or relocation advice.

### Claude Review Posture For Gemini Output

Claude should review Gemini work as a broad first pass. The expected job is not perfection review; it is blocker and integrity repair:

- validate JSON and schemas;
- confirm paths match active repo routing;
- remove or quarantine any consumer-facing prose Gemini generated by mistake;
- preserve TODO-only scaffolding where appropriate;
- add focused tests;
- reconcile any invented keys against `BLOCK_SCHEMA.md` and `LOCATION_EVIDENCE_RECORD_CONTRACT.md`;
- keep sensitive computation boundaries intact.

If Claude is not operating directly in the local repo, Claude should return a review report or patch plan. Codex should then perform any local edits and verification.

### Gemini Pass 01 Review Status

Gemini Expansion Pass 01 now has a local Codex review:

```text
products/location_services/gemini_expansion_pass_01/CODEX_REVIEW.md
```

Use `CODEX_REVIEW.md` as the active triage layer over the raw Gemini draft. The review accepts Gemini's broad planning value, but narrows the next implementation target to the Place Resonance selector foundation. It also downgrades Living Map timing claims, keeps all draft taxonomies unwired, and requires a dedicated batch no-mutation regression before Between Places.

### Gemini Prompt Guardrail Template

Use this guardrail block in any Gemini prompt for Location Services:

```text
You are creating first-pass Location Services scaffolding only.

You may create broad draft structure, TODO-only JSON scaffolds, planning docs, checklists, and non-client-facing notes.

You must not write final consumer-facing prose. Any future report text must remain literal TODO with explanatory _note fields.

You must not modify engine calculations, formulas, confidence logic, sect logic, natal condition logic, relocated condition logic, or any existing non-location product behavior.

You must not treat astrocartography, Local Space, parans, dynamic timing overlays, or relocated returns as implemented.

You must not invent final taxonomy for house domains, purpose fit, or contradictory evidence. You may propose draft options only if clearly marked DRAFT and not wired as truth.

You must not modify active Year Ahead, Personal Forecast, Daily, Weekly, Soul Ecosystem, Identity Profile, or shared prose libraries.

Stay inside products/location_services unless explicitly instructed otherwise.
```

## Content Position

Place Resonance is the first product to build because it stabilizes the shared evidence contract. The later products should reuse that contract rather than invent separate evidence shapes.

The content lane assumes this product order:

1. Place Resonance.
2. Between Places.
3. World Lines Companion.
4. Local Compass.
5. Living Map.

The prose stance is:

```text
A place does not rewrite the chart.
It changes what the chart foregrounds.
```

All locational language should stay evidence-routed, bounded, and technically inspectable.

## Proposed Backend Fields The Content Wants

The block schema currently expects these field families:

```text
birth_context
destination_context
relocated_chart
planet_house_changes
relocated_angle_contacts
natal_modifiers
evidence_ranking
purpose_lens
relationship_to_place
appendix_trace
unsupported_methods
warnings
```

## Most Important Validation Questions

Answered in `LOCATION_EVIDENCE_RECORD_CONTRACT.md` and reconciled into `BLOCK_SCHEMA.md`:

- What canonical body names will the evidence record emit?
- What canonical angle names will it emit: `ASC`/`MC`/`DSC`/`IC`, long names, or both?
- Can v0.1 emit relocated angle contacts, or only relocated houses and house changes?
- What orb and strength bands can v0.1 support for relocated angle contacts?
- Can v0.1 include natal condition summaries for emphasized planets without rerunning the whole report bundle?
- What exact fields describe birth-time confidence and angle sensitivity?
- How will unsupported methods be represented?
- What fields are definitely not computable yet and should be removed from v0.1 block requirements?

## Fields That Should Stay Optional Until Proven

```text
astrocartography.nearest_lines
astrocartography.line_distances
local_space.planetary_azimuths
dynamic_location_timing.active_windows
relocated_return_chart
parans
```

## No-Prose Scaffolding Preference

If the backend needs placeholder content before final prose, prefer structured leaves:

```json
{
  "body": "TODO",
  "_note": "Explain the exact evidence and claim boundary here.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["relocated_angle_contact"]
}
```

Do not put literal TODO placeholders into existing Year Ahead or Personal Forecast timing files. The TODO allowance here is for new Location Services scaffold files only, with tests that knowingly permit it.

## Claim Boundaries To Preserve In Implementation

- Do not rank locations as universally best or worst.
- Do not imply a place guarantees outcomes.
- Do not treat map-line evidence as available until astrocartography geometry exists.
- Do not let dynamic timing begin before the static Place Resonance evidence record is stable.
- Do not mutate natal payload semantics.
- Do not let relocation overwrite natal condition.

## Immediate Merge Point

Completed. Claude has provided relocated payload/evidence record samples, and the content lane has revised:

```text
products/location_services/BLOCK_SCHEMA.md
```

Current v0.1 decisions:

- Use long canonical angle names: `Ascendant`, `Midheaven`, `Descendant`, `Imum_Coeli`, `Vertex`.
- Include `wide` relocated angle contacts as a soft evidence tier.
- Use actual structural movement types: `same_house`, `newly_angular`, `leaves_angular`, `house_changed`, `unknown`.
- Keep `moves_public`, `moves_private`, `moves_relational`, and `moves_operational` as deferred selector/content taxonomy, not engine output.
- Read chart-level birth-time confidence from `birth_context.birth_time_confidence` or `appendix_trace.birth_time_confidence`.
- Read emphasized-body modifier confidence from `natal_modifiers[body].confidence`.
- Treat `contradictory_evidence` as intentionally empty in v0.1 until the same domain taxonomy exists.
- Render `warning_summary` for technical appendix prose; keep raw `warnings` for audit/debug displays.

## Round 6 Selector Foundation Status

Completed locally by Codex on 2026-07-14.

Implemented:

```text
config.py
selectors/location_services_selector.py
tests/test_location_services_selector.py
```

Selector surface:

```python
select_technical_appendix_leaf(family: str, sub_key: str) -> dict
select_angle_contact_leaf(angle: str, body: str, contact_strength: str) -> dict
select_planet_house_leaf(body: str, relocated_house: int | None, movement_type: str) -> dict
select_synthesis_leaf(synthesis_category: str) -> dict
```

Confirmed behavior:

- Location Services now has a dedicated `REPORT_BLOCK_DIRS["location_services"]` root at `products/location_services/blocks/plainspeak`.
- The selector returns whole structured leaf dictionaries, preserving `body`, `_note`, `claim_level`, and `requires_evidence`.
- Short angle aliases (`ASC`, `MC`, `DSC`, `IC`) normalize through the shared standard normalization helper before traversal.
- `Vertex` is rejected for relocated angle contacts because the current engine does not emit it in `relocated_angle_contacts`.
- Non-core bodies route to the scaffold `fallback` body before traversal.
- `movement_type == "unknown"` and missing relocated houses route to the body-level `unknown` leaf, not a house-level leaf.
- Impossible movement/house combinations return the relevant house-level fallback leaf rather than raising.
- Selector cache is separate from `selectors.block_selector._block_cache`.
- The selector does not import or invoke `engine.location_services`; it reads block files only.

Verification:

```text
python -m pytest tests/test_location_services_selector.py tests/test_location_services_block_scaffold.py tests/test_location_services_evidence_record.py tests/test_location_services_relocated_payload.py tests/test_planetary_condition_confidence.py
156 passed
```

Open next seam:

- Report assembly can now consume structured leaves without engine changes.
- The large angle and house grids are now authored; prose depth remains an
  audit and expansion lane, not a TODO-fill lane.
- Do not wire draft house-domain taxonomy, purpose-fit taxonomy, contradictory evidence, astrocartography, Local Space, parans, relocated returns, or dynamic timing from this selector foundation.

## Round 7 Place Resonance Assembly Status

Completed locally by Codex on 2026-07-14.

Implemented:

```text
products/location_services/place_resonance_assembler.py
tests/test_place_resonance_assembler.py
```

Assembler surface:

```python
assemble_place_resonance_context(evidence_record: dict) -> dict
build_place_resonance_context(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> dict
select_synthesis_category(record: dict) -> str
```

Confirmed behavior:

- The assembler consumes a `LocationEvidenceRecord` and returns a structured Place Resonance draft context.
- It does not render HTML/PDF and does not author new prose.
- It does not mutate the evidence record.
- It builds sections for `place_signature`, `evidence_summary`, `relocated_angle_contacts`, `planet_house_changes`, and `technical_appendix`.
- It selects existing structured leaves through `selectors/location_services_selector.py`.
- It uses `warning_summary` for the technical appendix surface and only reports raw warning count.
- Synthesis classification is selector-side and intentionally narrow:
  - no primary evidence -> `low_signal_signature`
  - no changed houses -> `quiet_continuity_signature`
  - repeated angle-contact + changed-house body -> `convergent_place_signature`
  - public/private angle split proxy -> `mixed_public_private_signature`
  - angle-primary patterns -> `angle_led_signature`
  - house-primary patterns -> `house_shift_led_signature`
- Purpose-fit and purpose-tradeoff categories remain deferred; the assembler records `purpose_lens` but does not implement the missing taxonomy.

Verification:

```text
python -m pytest tests/test_place_resonance_assembler.py tests/test_location_services_selector.py tests/test_location_services_block_scaffold.py tests/test_location_services_evidence_record.py tests/test_location_services_relocated_payload.py tests/test_planetary_condition_confidence.py
166 passed
```

Open next seam:

- Add a scaffold HTML/template renderer that consumes the Place Resonance context.
- Or begin a targeted prose-depth pass for the highest-value TODO leaves in `relocated_angle_contact_blocks.json` and `planet_relocated_house_blocks.json`.
- Do not treat the context assembler as a final client report; it is the inspectable report draft contract.

## Round 8 Place Resonance HTML Status

Completed locally by Codex on 2026-07-14.

Implemented:

```text
products/location_services/place_resonance_renderer.py
products/location_services/templates/place_resonance.html
products/location_services/tooling/generate_place_resonance_ready.py
tests/test_place_resonance_renderer.py
```

Renderer surface:

```python
render_place_resonance_html(place_context: dict) -> str
build_place_resonance_html(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> str
write_place_resonance_html(html_content: str, output_filename: str | None = None) -> str
```

Confirmed behavior:

- The renderer consumes the assembled Place Resonance context and produces HTML.
- Authored leaves render as report prose.
- Unauthored scaffold leaves do not render raw `TODO`; they render as explicit browser-editable draft slots with the leaf `_note` preserved as the editing prompt and source note.
- The HTML includes a synthesis lead, evidence summary table, angle-contact cards, house-change cards, and technical appendix cards.
- The technical appendix surfaces `warning_summary` groups and warning counts, not the raw warning-string dump.
- The renderer reuses `products/shared/report_visual_system.css` and preserves the standard EO report footer contract.
- A lightweight generation script now exists for end-to-end local draft generation from natal birth data plus one destination.

Verification:

```text
python -m pytest tests/test_place_resonance_renderer.py tests/test_place_resonance_assembler.py tests/test_location_services_selector.py tests/test_location_services_block_scaffold.py tests/test_location_services_evidence_record.py tests/test_location_services_relocated_payload.py tests/test_planetary_condition_confidence.py
171 passed
```

Smoke test:

```text
python products/location_services/tooling/generate_place_resonance_ready.py --name "Place Resonance Sample" --date 1990-06-15 --time 14:22 --location "Chicago, Illinois" --destination "Sydney, Australia" --purpose-lens career --relationship-to-place possible_move --output-filename sample_place_resonance.html
```

Generated:

```text
output/location_services/sample_place_resonance.html
```

Open next seam:

- Fill high-value angle-contact and relocated-house prose leaves and re-render the HTML.
- Add a more polished export path only after the content lane is comfortable with the current HTML review surface.
- Keep purpose-fit taxonomy, contradictory evidence, astrocartography, Local Space, parans, relocated returns, and dynamic timing out of the renderer until their data contracts are real.

### Round 8.1 Visual Addendum

Place Resonance HTML now includes:

- a repo-native natal SVG wheel rendered through `engine/chart_wheel.py`
- a reserved astrocartography visual slot with explicit unavailable status

Boundaries preserved:

- The natal wheel is only added on the wrapper path that has the full natal payload.
- It uses the existing shared wheel renderer; no new chart engine was introduced.
- The wheel is treated as a stable natal reference, not relocated evidence.
- No astrocartography geometry, lines, map projections, or local-space visuals were implemented.
- The astrocartography area is only a named placeholder so the future map seam already has a visual home in the HTML.

Additional verification:

```text
python -m pytest tests/test_place_resonance_renderer.py tests/test_place_resonance_assembler.py tests/test_location_services_selector.py tests/test_location_services_block_scaffold.py tests/test_location_services_evidence_record.py tests/test_location_services_relocated_payload.py tests/test_planetary_condition_confidence.py
172 passed
```
