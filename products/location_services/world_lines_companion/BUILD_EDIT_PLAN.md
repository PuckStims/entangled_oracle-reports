# World Lines Companion Build / Edit Plan

Status date: 2026-07-14

## Purpose

`World Lines Companion` is the astrocartography-specific location product.
Its job is to explain line geometry and planetary-line proximity without
pretending the geometry layer already exists.

## Current Repo State

- Product shell exists: `assembler.py`, `renderer.py`, `plugin.py`.
- Registry wiring exists and HTML rendering works.
- Most sections are future-method placeholders, which is currently honest.
- `engine/astrocartography_svg.py` exists, but full line geometry,
  nearest-point calculation, and distance attenuation are not yet
  production contracts.

## Build Goal

Move from an attractive placeholder shell to an auditable
astrocartography companion with a real line-evidence contract.

## Build Sequence

1. Define the minimum line evidence schema:
   planet, angle, line type, distance/proximity, confidence, and map
   trace metadata.
2. Audit what `engine/astrocartography_svg.py` can already supply versus
   what still needs calculation work.
3. Wire map evidence into context assembly without inventing distance
   bands or crossings.
4. Promote only the sections backed by real geometry.
5. Keep unbuilt sections explicitly marked as future methods.

## Edit Rules

- Do not fake line proximity, crossings, or nearest points.
- Do not let the template imply that map geometry is already complete.
- Keep natal-context interpretation downstream of identified planetary
  lines, not upstream guessed prose.

## Immediate Next Edits

- Reconcile this folder against
  `products/location_services/ASTROCARTOGRAPHY_SVG_CONTRACT.md`.
- Decide whether the first live version is line-summary only or includes
  limited proximity interpretation.
- Add tests around whatever line evidence contract is chosen.

## Verification

- Keep registry smoke coverage green.
- Keep `tests/test_astrocartography_svg.py` green.
- Add product-specific tests before production routing.
