# Codex brief — Phase D remainder: Year Ahead progressions/solar-arc "texture" (backend only)

## Context

Standard-forecasting phased upgrade map, Phase D. Phases A–C and the
Personal-Forecast half of D (progressed Moon) are done, verified, and
committed (`8cef1f3`). This is the other half of D: Year Ahead's 12-month
scope gets progression and solar-arc events too, but framed as ambient
developmental *texture* (terrain/mood of the period), not point-forecast
claims. This pass is **backend only** — wire the data, verify it against
real charts, do not touch templates or write any new client-facing prose.
That's a deliberate, already-made decision: get real data to react to
before anyone (human or AI) writes language for it.

Mirror the pattern already proven for Personal Forecast's progressed
Moon (see `agents/REVISIONS.md`, 2026-07-08 entry, "Progressed Moon wired
into Personal Forecast, gated to Moon only"). Same shape, different
filter, different destination.

## What to build

1. **`engine/transit_engine.py::compute_year_ahead_events()`** — add an
   `include_year_texture: bool = False` parameter (default `False`;
   every existing caller's behavior is unchanged unless explicitly
   opted in).

   When `True`:
   - Call `engine.progressions.scan_progression_events()` and filter
     the result to `clock_role == "chapter"` only (this is the
     opposite filter direction of the existing
     `_filter_moon_progression_events()` helper — that one *keeps*
     Moon/`modifier` events; this one *excludes* them, keeping
     everything tagged `"chapter"`). You can implement this as a new
     small helper (e.g. `_filter_texture_progression_events()`) or an
     inline filter — your call, whichever reads cleaner next to the
     existing Moon helper.
   - Call `engine.solar_arc.scan_solar_arc_events()` directly — no
     filtering needed, every event it produces is already
     `clock_role: "chapter"`.
   - Pass both filtered lists through the existing
     `link_related_forecast_events(..., progression_events=...,
     solar_arc_events=...)` scaffolding (already implemented, already
     runs events through `enrich_forecast_event` for the Moon case —
     just currently called with empty/absent lists for this path).
   - **Do not merge these into `all_events`.** `entry_datetime` /
     `peak_datetime` / `leave_datetime` windows here are season-scale
     (months, sometimes ~9mo–2yr of "current"), much wider than
     transit windows. Mixing them into the same chronological list
     `all_events` already sorts by will likely read as broken
     ordering, not enriched content. Add them as their own key(s) in
     the returned dict instead — e.g. `"year_texture_progressions"`
     and `"year_texture_solar_arc"` (or one combined
     `"year_texture"` list if that reads cleaner to you structurally —
     your call, just keep it separate from `all_events`).

2. **`generate.py::_build_year_ahead_context()`** (around line 7301,
   where it currently calls `compute_year_ahead_events(payload,
   start_date=report_start, end_date=report_end)` with no extra
   flags) — pass `include_year_texture=True` and pull the new key(s)
   out of `timeline` into the context dict under a clearly-scoped name
   (e.g. `year_texture_events` or similar), same way `all_events` and
   `transit_events` are currently pulled out just above. **Do not**
   wire it into any template variable, HTML section, or content-pack
   block selection — this data should exist in the context/manifest
   for inspection only, not render anywhere yet.

3. Leave Personal Forecast's `_build_personal_forecast_context()`
   untouched — it already correctly uses `include_moon_progressions=True`
   and should stay that way; this task doesn't touch it.

## Verification (required before calling this done)

- Confirm `include_year_texture=False` (the default) produces byte-identical
  event output to current behavior — i.e. every existing caller of
  `compute_year_ahead_events()` that doesn't pass the new flag sees zero
  change.
- Run against at least one real natal chart already used elsewhere in the
  test suite/fixtures, generate a live Year Ahead report with the flag on,
  and report back:
  - actual event counts for `year_texture_progressions` /
    `year_texture_solar_arc` (or your combined key) over a real 12-month
    window
  - the actual date-span shape of a few sample events (confirm they really
    do span months, not days, matching the "season-scale" assumption this
    design is built on)
  - whether `link_related_forecast_events` enrichment is populating
    correctly on these (same fields Moon-progression events get)
- Full test suite green, same as the Moon-progression pass (226 passed
  baseline before this — confirm no regressions).

## One thing to flag back to us, not solve yourself

If the real event count from that live-chart verification turns out to be
large enough that it looks like it'll need some kind of volume limit before
this is usable later (e.g. dozens of overlapping season-scale windows), **stop
and report the actual numbers — don't invent a cap.** Standing rule on this
codebase: no flat ceiling or fixed number gets introduced as EO-specific
logic without real astrological research backing it first (this bit us
before on orb-scaling during Phase B/C). If volume turns out to be a real
problem, that's a "let's research what standard practice actually looks like
here" conversation with the operator, not a "just pick a number" fix.

## Explicitly out of scope this pass

- No template changes.
- No new content-pack JSON, no prose, no "texture section" copy.
- No changes to Personal Forecast's existing Moon-only wiring.
- No changes to `all_events` sort behavior or shape.
