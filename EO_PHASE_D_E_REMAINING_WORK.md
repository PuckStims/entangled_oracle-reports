# Entangled Oracle — Phase D & E Remaining Work

Standalone continuation of the standard-forecasting phased upgrade map. Phases A (ZR Loosing of the Bond), B (scaffolding verification), C (Annual Profections weighting), and the Personal-Forecast half of D (progressed Moon) are done, verified, and committed (`8cef1f3`). This document covers what's left: the open half of Phase D, and the fully-deferred Phase E items.

---

## Phase D remainder — Year Ahead progressions/solar arc as "texture"

**Decided already:** progressions and solar arc belong in Year Ahead's 12-month scope (not Personal Forecast — confirmed too slow for a 90-day window, except progressed Moon which is already wired in). Framed as ambient developmental *texture* — describing the terrain/mood of the period — not point-forecast claims ("on date X, Y happens"). Uses the prog-to-prog/transit-to-prog axes verified in Phase B, plus the existing `clock_role: "chapter"` designation already present in `engine/progressions.py`/`engine/solar_arc.py` for non-Moon contacts.

**Still open — the one real fork:**
- **Backend-only this pass:** wire progression/solar-arc events into `compute_year_ahead_events` (mirroring how `include_moon_progressions` was added for Personal Forecast — an opt-in flag, e.g. `include_year_texture: bool = False`, defaulting False so nothing changes until explicitly turned on), verify the data flows correctly against real charts, but don't touch templates or write new prose yet.
- **All the way to visible content:** also design and write the actual "texture" section — the language/framing is as much a voice decision as a data one, and hasn't been drafted at all yet.

Recommendation stands from earlier: backend first, get real data to react to before writing client-facing language. But that's the actual decision to make when picking this up.

**Implementation notes for whoever builds this:**
- `engine/progressions.py::scan_progression_events()` already tags Moon-sourced contacts `clock_role: "modifier"` and everything else `clock_role: "chapter"` — filtering to `clock_role == "chapter"` (the inverse of the existing `_filter_moon_progression_events()` helper in `engine/transit_engine.py`) gets you the non-Moon, texture-appropriate set directly.
- `engine/solar_arc.py::scan_solar_arc_events()` needs no filtering — every event it produces is already `clock_role: "chapter"`.
- Don't fold these into `all_events`' existing sort without checking — `entry_datetime`/`peak_datetime`/`leave_datetime` windows here are much wider (season-scale) than transits, so "chronological order" may read strangely mixed into the same list. Worth its own section/list in the returned dict rather than assuming it slots into `all_events` cleanly the way Moon progressions did.
- The `link_related_forecast_events(..., progression_events=..., solar_arc_events=...)` parameters already exist and already run events through `enrich_forecast_event` — this scaffolding is ready, just unused for the non-Moon case.

---

## Phase E — deferred, no urgency

- **E1. Return chart generation/interpretation.** Solar/lunar/planetary return *timing* is solid (`engine/returns.py`); the actual return chart (read as its own chart, the way a solar return normally works) doesn't exist. Real gap, large net-new scope, not a fix to something broken. No research done yet.
- **E2. Lord-of-the-decade / profection sub-periods.** Still just a research item — is there a standard sub-lord tier beneath the annual profection lord, and is it worth the (likely small) implementation lift. Not started.
- **E3. Firdaria, primary directions.** Your own charter (`phase0/03_method_charters.md` C6) already defers these correctly until the primary six techniques (returns, profections, solar arc, progressions, lots, ZR) complete a full validation cycle. No action needed — this is already the right call.
- **E4. Personal Forecast coverage expansion.** Flagged 2026-07-08: deeper/richer coverage of Lunation, Mars+Venus transits, house ingresses, and stationary points specifically within Personal Forecast. Explicitly a placeholder — additional depth on top of whatever Phase D ships, not a replacement for anything in it. Not scoped, not started.

---

## Standing rule, carried over

Anything that declares a flat ceiling or fixed number as EO-specific logic gets ignored in favor of actual astrological research/data. Nothing in any internal document (charter, spec, or otherwise) overrides real research for prediction functions — verify uncertainty, don't default to a presumed EO principle. This applied directly during Phase B/C (the orb-scaling fix) and should apply again here if any new thresholds come up while building the texture section.
