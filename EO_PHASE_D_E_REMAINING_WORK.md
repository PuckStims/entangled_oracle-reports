# Entangled Oracle — Phase D & E Remaining Work

Standalone continuation of the standard-forecasting phased upgrade map. Phases A (ZR Loosing of the Bond), B (scaffolding verification), C (Annual Profections weighting), and both halves of Phase D (progressed Moon in Personal Forecast, and Year Ahead progressions/solar-arc "texture") are done, verified, and committed. This document now covers what's left: Phase D's real follow-on (volume/content), and the fully-deferred Phase E items.

---

## Phase D — closed

Both halves landed:
- Progressed Moon → Personal Forecast (`8cef1f3`)
- Year Ahead progressions/solar-arc "texture," backend-only: `include_year_texture` flag on `compute_year_ahead_events()`, filtered to `clock_role == "chapter"`, surfaced as its own `year_texture_progressions`/`year_texture_solar_arc` keys, not merged into `all_events` (`cea2fec`)
- Follow-on scoring fix, found during live review: progression/solar-arc events were scoring a flat `0.0` (missing `raw_score` field plus no scoring-formula case for these event types); fixed and re-verified against a real chart — also fixed the already-shipped Moon-progression events for free, since they share the same code path (`3807661`)

**Real follow-on, not part of Phase D itself:** a live 12-month chart produced 208 `year_texture_progressions` and 14 `year_texture_solar_arc` events — reported raw, no cap applied, per the standing rule below. Now that real scores exist (post-`3807661`), there's an actual axis to sort/trim by if volume-limiting is ever taken up. Not decided, not scheduled.

**Also still not done, deliberately deferred by the backend-only scoping decision:** the client-facing "texture" section itself — no templates touched, no prose written. That's a voice/design pass for whenever visible content is picked up, same recommendation as before: get real data reacted to first (done now), write language second.

---

## Phase E — deferred, no urgency

- **E1. Return chart generation/interpretation.** Solar/lunar/planetary return *timing* is solid (`engine/returns.py`); the actual return chart (read as its own chart, the way a solar return normally works) doesn't exist. Real gap, large net-new scope, not a fix to something broken. No research done yet.
- **E2. Lord-of-the-decade / profection sub-periods.** Still just a research item — is there a standard sub-lord tier beneath the annual profection lord, and is it worth the (likely small) implementation lift. Not started.
- **E3. Firdaria, primary directions.** Your own charter (`phase0/03_method_charters.md` C6) already defers these correctly until the primary six techniques (returns, profections, solar arc, progressions, lots, ZR) complete a full validation cycle. No action needed — this is already the right call.
- **E4. Personal Forecast coverage expansion.** Flagged 2026-07-08: deeper/richer coverage of Lunation, Mars+Venus transits, house ingresses, and stationary points specifically within Personal Forecast. Explicitly a placeholder — additional depth on top of whatever Phase D ships, not a replacement for anything in it. Not scoped, not started.

---

## Standing rule, carried over

Anything that declares a flat ceiling or fixed number as EO-specific logic gets ignored in favor of actual astrological research/data. Nothing in any internal document (charter, spec, or otherwise) overrides real research for prediction functions — verify uncertainty, don't default to a presumed EO principle. This applied directly during Phase B/C (the orb-scaling fix) and should apply again here if any new thresholds come up while building the texture section.
