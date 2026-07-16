# World Lines Companion Build / Edit Plan

Status date: 2026-07-16

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
- The Phase 1 normalized evidence grammar exists for current relocated-chart
  evidence. World Lines should extend that grammar with real line evidence
  only after map geometry is computed.

## Build Goal

Move from an attractive placeholder shell to an auditable
astrocartography companion with a real line-evidence contract.

Full line-engine build outline:
`products/location_services/BUILD_OUTLINE_DRIFT_GUARD.md` Build Area G.

## Build Sequence

1. Define the minimum line evidence schema:
   planet, angle, line type, distance/proximity, confidence, and map
   trace metadata.
2. Audit what `engine/astrocartography_svg.py` can already supply versus
   what still needs calculation work.
3. Wire map evidence into context assembly without inventing distance
   bands or crossings.
4. Emit line evidence through the normalized grammar shape once geometry is
   real.
5. Promote only the sections backed by real geometry.
6. Keep unbuilt sections explicitly marked as future methods.

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
- Write the line evidence schema before any prose or renderer changes:
  planet, angle, line type, nearest point, distance, distance band, continuous
  strength, birth-time sensitivity, map trace metadata, and claim boundary.
- Keep the current SVG contract as visual support only until nearest-point and
  distance calculations are tested.

## Verification

- Keep registry smoke coverage green.
- Keep `tests/test_astrocartography_svg.py` green.
- Add product-specific tests before production routing.
