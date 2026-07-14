# Between Places Build / Edit Plan

Status date: 2026-07-14

## Purpose

`Between Places` is the first real multi-destination Location Services
product. It should compare two places without collapsing into a "best
place" ranking engine.

## Current Repo State

- Product shell exists: `assembler.py`, `renderer.py`, `plugin.py`.
- Registry wiring exists through `products/location_services/registry.py`.
- HTML rendering exists and is covered by registry smoke tests.
- The current context is still scaffold-level: most sections are draft
  prompts or future-method placeholders.
- No true comparison engine exists yet. Current wrapper logic only passes
  destination metadata into placeholder records.

## Build Goal

Turn this from a two-place visual shell into the first production
descendant of Place Resonance.

## Build Sequence

1. Reuse the Place Resonance single-place evidence builder for
   Destination A and Destination B independently.
2. Preserve both evidence records as immutable inputs.
3. Add a comparison layer that computes:
   - shared themes
   - strongest differences
   - angular emphasis deltas
   - house movement deltas
   - purpose-lens tradeoffs
4. Replace draft prompts with evidence-backed section payloads.
5. Add a technical appendix that shows how each destination was derived.

## Edit Rules

- Do not turn this into prescriptive ranking copy.
- Do not mutate the single-place evidence record shape just to make
  comparison easier.
- Do not hardcode "A is better than B" language in templates.
- Keep `purpose_lens` optional, and keep the neutral baseline readable
  even when no lens is supplied.

## Immediate Next Edits

- Add or reuse a dedicated comparison record/schema.
- Decide which Place Resonance sections map cleanly into shared-vs-
  divergent comparison summaries.
- Add tests for same-destination comparisons and asymmetric evidence.

## Verification

- Registry smoke test must stay green:
  `tests/test_location_services_product_registry.py`
- Add focused tests once comparison logic lands.
- Sample output should still render HTML before deeper logic is added.
