# Entangled Engine Expectations

The integration is expected to preserve the existing Entangled Oracle architecture, including distinctions among:

- calculated events,
- normalized/canonical event identity,
- selection and grouping,
- content-pack lookup,
- fallback tiers,
- report context,
- presentation and export.

## Current Field synthesis

A `FieldPattern` is not an arbitrary mood score. It is an engine-owned synthesis with:

- role: dominant, supporting, or background,
- timing stage,
- supporting event IDs,
- interpretive summary,
- optional orientation prompts.

If the current engine does not yet create this object, Codex should construct it through a documented adapter over the real selector and report-context outputs—not through invented weighting.
