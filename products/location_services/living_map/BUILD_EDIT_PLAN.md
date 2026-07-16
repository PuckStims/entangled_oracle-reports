# Living Map Build / Edit Plan

Status date: 2026-07-16

## Purpose

`Living Map` is the dynamic timing-overlay product. It should distinguish
the permanent baseline of a place from temporary activation weather.

## Current Repo State

- Product shell exists: `assembler.py`, `renderer.py`, `plugin.py`.
- Registry wiring exists and HTML rendering works.
- Static baseline sections are scaffolded from Place Resonance ideas.
- Dynamic timing sections remain future-method placeholders.
- No relocated timing engine or timing-window contract is implemented yet.
- The Phase 1 normalized evidence grammar exists for the static baseline.
  Living Map timing should attach to those evidence items later, not overwrite
  the permanent place baseline.

## Build Goal

Build a timing-overlay product that can explain what is structurally true
about a place versus what is temporarily active there.

Full timing-overlay build outline:
`products/location_services/BUILD_OUTLINE_DRIFT_GUARD.md` Build Area I.

## Build Sequence

1. Decide the first live timing stack:
   relocated transits only, or a broader mix such as profections and
   returns later.
2. Define a timing-window schema:
   start, end, trigger, target location evidence, intensity, and rationale.
3. Reuse Place Resonance as the baseline layer.
4. Normalize the static baseline through
   `products/location_services/evidence_grammar/`.
5. Overlay timing evidence without blurring baseline and temporary effects.
6. Replace placeholder timing sections with actual window summaries.

## Edit Rules

- Do not fake relocated timing activation.
- Do not confuse permanent place signature with short-lived transit
  weather.
- Keep timing-language intensity tied to real evidence and time windows.

## Immediate Next Edits

- Choose the first live timing method for v1.
- Define how timing attaches to relocated angles and relocated planetary
  emphasis.
- Add tests for overlapping windows and missing timing evidence.
- Define timing-window output before prose: start, end, trigger, linked static
  evidence IDs, intensity, confidence, and baseline-vs-weather classification.
- Require static baseline evidence to remain byte-for-byte unchanged when a
  timing overlay is added.

## Verification

- Keep registry smoke coverage green.
- Reuse focused Place Resonance tests as the baseline contract guardrail.
- Add Living Map timing tests before production routing.
