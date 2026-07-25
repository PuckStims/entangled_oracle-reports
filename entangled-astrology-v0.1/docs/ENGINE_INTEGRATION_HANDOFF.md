# Engine Integration Handoff

## Objective

Expose the existing Entangled Oracle engine through the v1 contract without reimplementing or simplifying its astrology.

## Required first pass

1. Locate the actual CLI and programmatic entry points.
2. Trace birth data through timezone/location resolution, ephemeris calculation, event production, normalization, canonical identity, deduplication, selection, content-pack lookup, fallback handling, report context, and rendering.
3. Record every module and file-path assumption.
4. Identify mutable global state and concurrency hazards.
5. Identify what already produces structured data and what exists only as rendered prose.
6. Compare known-good outputs before and after wrapping.

## Adapter rule

The adapter may translate inputs and outputs. It must not replace calculation semantics, silently drop events, construct interpretations from aspect names, or create a parallel simplified engine.

## Initial target

A thin FastAPI service is the preferred first bridge. It should import the existing modules and call the same functions used by the working CLI wherever possible.

## Acceptance test

For the same birth profile, moment, configuration, and ephemeris files:

- CLI raw events and API raw events reconcile,
- report selections reconcile,
- normalized IDs reconcile,
- rendered report content is not degraded,
- provenance identifies the invoked modules and fallback tier.
