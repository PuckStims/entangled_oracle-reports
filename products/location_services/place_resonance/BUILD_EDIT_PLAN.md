# Place Resonance Build / Edit Plan

Status date: 2026-07-14

## Purpose

`Place Resonance` is the anchor product for the Location Services suite.
It is the one-location depth report that proves the relocated evidence
pipeline works before comparison, map, directional, or timing products
are promoted.

## Current Repo State

- Canonical implementation exists today in:
  - `products/location_services/place_resonance_assembler.py`
  - `products/location_services/place_resonance_renderer.py`
  - `products/location_services/templates/place_resonance.html`
  - `products/location_services/tooling/generate_place_resonance_ready.py`
- Product-folder registration now exists through
  `products/location_services/place_resonance/plugin.py`.
- Focused tests and the ready-generator script now import the normalized
  `products/location_services/place_resonance/` package path.
- Focused tests already exist and are green for assembler, renderer,
  selector behavior, relocated payload shape, and astrocartography SVG
  contract usage.
- This dedicated folder now exists as the product home, but it currently
  uses wrapper modules so the old imports do not break during migration.

## Build Goal

Keep Place Resonance as the known-good reference product while gradually
moving it into the same folder structure as the newer location products.

## Build Sequence

1. Keep the current root-level assembler and renderer as canonical until
   migration work is deliberate and tested.
2. Use this folder as the local planning and normalization seam.
3. Keep the product-folder wrapper imports and registry plugin live now
   that tests and tooling reference the product folder safely.
4. When ready, migrate tests/tooling/imports from root-level modules to
   package-local modules in a dedicated pass.
5. Only after import migration is stable should the root-level modules be
   reduced to shims or removed.

## Edit Rules

- Do not break the current Place Resonance generator or focused test path
  in pursuit of folder symmetry.
- Do not widen Place Resonance into dynamic timing, comparison, or map
  logic that belongs to later products.
- Keep Place Resonance as the evidence-contract authority for the other
  Location Services products.

## Immediate Next Edits

- Decide whether the next migration pass should move tests first or
  tooling first.
- Add package-local imports only where they do not create duplicate logic.
- Keep the folder docs here current as Place Resonance evolves.

## Verification

- `tests/test_place_resonance_assembler.py`
- `tests/test_place_resonance_renderer.py`
- `tests/test_location_services_selector.py`
- `tests/test_location_services_relocated_payload.py`
- `tests/test_astrocartography_svg.py`
- `products/location_services/tooling/generate_place_resonance_ready.py`
