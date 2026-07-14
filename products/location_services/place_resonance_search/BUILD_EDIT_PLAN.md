# Place Resonance Search Build / Edit Plan

Status date: 2026-07-14

## Purpose

`Place Resonance Search` is the emerging flagship discovery product for
Location Services. Its long-term job is to surface the places whose
symbolic field is most worth attention, then interpret why.

## Current Repo State

- This product folder now exists and is registry-wired.
- It currently reuses the existing single-location Place Resonance context
  and render path through wrapper modules.
- The current implementation is intentionally transitional: it creates a
  duplicate product identity before the original Place Resonance files are
  repurposed.

## Build Goal

Create a stable renamed product home now, then let the original
`place_resonance` files become available for reassignment inside the
evolving location family.

## Build Sequence

1. Keep this package as a stable parallel product identity.
2. Preserve output compatibility while the original product is still in
   use.
3. Reassign the original `Place Resonance` role deliberately after the new
   search/discovery architecture is clearer.
4. Add candidate-pool, scoring, curation, and bucket logic here when the
   product theory is settled.

## Edit Rules

- Do not pretend this package already performs multi-location search.
- Do not remove the current single-location interpretation path until its
   role in the family has been reassigned.
- Keep naming clear so future agents do not confuse the search product with
   the single-location report logic it currently wraps.

## Immediate Next Edits

- Decide what the original `place_resonance` package will become after this
  duplicate exists.
- Add future docs for candidate-pool evaluation, selection buckets, and
  place-profile reuse.
- When the time comes, split "search product" and "single-place profile"
  content/routing explicitly.

## Verification

- `tests/test_location_services_product_registry.py`
- `tests/test_place_resonance_search_package_layout.py`
- `tests/test_place_resonance_assembler.py`
- `tests/test_place_resonance_renderer.py`
