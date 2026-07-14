# Local Compass Build / Edit Plan

Status date: 2026-07-14

## Purpose

`Local Compass` is the directional / Local Space product. It should answer
how planetary vectors express through directions and orientation, not just
repeat relocated-chart findings with compass-themed prose.

## Current Repo State

- Product shell exists: `assembler.py`, `renderer.py`, `plugin.py`.
- Registry wiring exists and HTML rendering works.
- Directional sections are still future-method placeholders.
- No azimuth or direction-strength computation is implemented yet.

## Build Goal

Create a real directional evidence contract before attempting rich Local
Space interpretation.

## Build Sequence

1. Define directional evidence inputs:
   anchor location, target destination, planet/body, azimuth, sector, and
   confidence/strength.
2. Decide the computation frame:
   current location to destination, natal anchor to destination, or both.
3. Build the azimuth computation seam.
4. Add readable sector/grouping logic for user-facing interpretation.
5. Replace placeholder sections with evidence-backed directional output.

## Edit Rules

- Do not fake azimuths or directional rays.
- Do not use Place Resonance evidence as a substitute for true Local Space
  computation.
- Keep practical-use sections downstream of actual directional evidence.

## Immediate Next Edits

- Write the first directional evidence contract note.
- Choose the minimum viable directional vocabulary for sectors.
- Add tests for azimuth wraparound and sector bucketing once the seam is
  real.

## Verification

- Keep registry smoke coverage green.
- Add product tests before any routing into the main generator.
- Ensure the technical appendix stays honest about missing directional
  computation until it exists.
