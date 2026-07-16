# Place Resonance / Place Profile Build Edit Plan

Status date: 2026-07-16

## Purpose

`Place Resonance` is currently the working one-location Location Services
implementation. Its long-term architectural role is the reusable Place Profile
engine: a single-destination evidence and interpretation unit that Place
Resonance Search, Between Places, and later products can reuse.

The legacy public name may stay `Place Resonance` while the repo transitions,
but agents should not treat this package as the permanent flagship discovery
product. That role now belongs to `Place Resonance Search`.

## Current Repo State

- Canonical implementation exists today in:
  - `products/location_services/place_resonance_assembler.py`
  - `products/location_services/place_resonance_renderer.py`
  - `products/location_services/templates/place_resonance.html`
  - `products/location_services/tooling/generate_place_resonance_ready.py`
- Phase 1 normalized evidence grammar now exists in
  `products/location_services/evidence_grammar/` as an opt-in adapter over the
  current `LocationEvidenceRecord`.
- Product-folder registration exists through
  `products/location_services/place_resonance/plugin.py`.
- Focused tests and the ready-generator script import through the normalized
  `products/location_services/place_resonance/` package path.
- Focused tests exist for assembler, renderer, selector behavior, relocated
  payload shape, and astrocartography SVG contract usage.
- This folder currently uses wrapper modules so old imports do not break during
  migration.

## Build Goal

Keep the existing one-location implementation stable while deliberately
reframing it as a reusable Place Profile engine. It should remain the evidence
contract authority for single-place interpretation, but it should not absorb
search, comparison, map, directional, or timing responsibilities.

Full shared-grammar build outline:
`products/location_services/BUILD_OUTLINE_DRIFT_GUARD.md` Build Areas A through
D for resolver, theme clusterer, goal compatibility, and report planner work.

## Build Sequence

1. Keep the current root-level assembler and renderer canonical until migration
   work is deliberate and tested.
2. Use this folder as the product-local planning and normalization home for the
   single-place profile engine.
3. Keep product-folder wrapper imports and registry plugin live.
4. When ready, migrate tests/tooling/imports from root-level modules to
   package-local modules in a dedicated pass.
5. Only after import migration is stable should root-level modules become shims
   or be removed.
6. Expose compact profile context cleanly enough for Place Resonance Search and
   Between Places to reuse it without copying single-place prose logic.
7. Route broad interpretation/prose upgrades through the normalized evidence
   grammar and later resolver/report-planner phases.

## Edit Rules

- Do not break the current generator or focused test path in pursuit of folder
  symmetry.
- Do not widen this package into candidate search, dynamic timing, comparison,
  or map logic.
- Keep this package responsible for single-place evidence, profile context, and
  one-location prose selection.
- Update stale references when they still describe this package as the future
  flagship instead of the reusable profile engine.

## Immediate Next Edits

- Add a short compatibility note wherever external tooling still says "Place
  Resonance" but is functionally using the Place Profile engine.
- Keep documenting which context fields are reusable profile fields and which
  are report-rendering fields.
- Wire `place_context_modifier_blocks.json` only after a context-axis classifier
  exists.
- Preserve the focused test suite before any migration out of root-level modules.
- Do not broaden Place Profile prose until a report plan can name source
  clusters, source evidence IDs, claim boundaries, and required disclosures.

## Verification

- `tests/test_place_resonance_assembler.py`
- `tests/test_place_resonance_renderer.py`
- `tests/test_location_services_selector.py`
- `tests/test_location_services_relocated_payload.py`
- `tests/test_astrocartography_svg.py`
- `products/location_services/tooling/generate_place_resonance_ready.py`
