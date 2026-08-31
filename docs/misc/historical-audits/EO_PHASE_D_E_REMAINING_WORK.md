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

- **E1. Return chart generation/interpretation.** Solar/lunar/planetary return *timing* is solid (`engine/returns.py`); the actual return chart (read as its own chart) doesn't exist yet. Research done 2026-07-08 — see "E1 research findings" below. Still not started as code.
- **E2. Monthly profections (the real sub-lord tier beneath annual profections).** Research done 2026-07-08 — this is confirmed as a real, standard, well-documented technique (not the same thing as Decennials — see below). Small implementation lift expected, mirroring existing `engine/profections.py::annual_profection_periods()` logic at a monthly cadence instead of annual. Confirmed as the next real E2 candidate whenever picked up. Not started as code yet.
- **E2b. Decennials (10-year time-lord periods, each split into 7 sub-periods).** Operator-confirmed 2026-07-08: this *is* the actual longer-term goal implied by "lord of the decade" — but it's a separate, independent Hellenistic time-lord system, not a sub-tier of annual profections, and a meaningfully bigger build (a whole new time-lord family, own `independence_group`, own charter per `phase0/03_method_charters.md` C6's rules for new time-lord systems). Explicitly parked — "way later, not an issue now by any means." Do not conflate with E2's monthly profections when scoping either one.
- **E3. Firdaria, primary directions.** Your own charter (`phase0/03_method_charters.md` C6) already defers these correctly until the primary six techniques (returns, profections, solar arc, progressions, lots, ZR) complete a full validation cycle. No action needed — this is already the right call.
- **E4. Personal Forecast coverage expansion.** Flagged 2026-07-08: deeper/richer coverage of Lunation, Mars+Venus transits, house ingresses, and stationary points specifically within Personal Forecast. Explicitly a placeholder — additional depth on top of whatever Phase D ships, not a replacement for anything in it. Not scoped, not started.

### E1 research findings (2026-07-08)

**Reading methodology** (converges across sources, cross-checked against multiple independent astrology references — see session history for source links): read the return chart the same way as a natal chart, same house system, same aspect logic, just anchored to the return moment. Priority order: return Ascendant first (colors the whole period's orientation), then its ruler by house/sign/aspect, then the Sun's house placement (what area of life is emphasized), then any planet within a few degrees of an angle (1st/4th/7th/10th cusp) gets outsized weight, then the Moon's house/sign for emotional tone. Read the return chart standalone first, then optionally overlay/compare to natal.

**Duration per type:** solar return ~1 year (birthday to birthday); lunar return ~27-28 days (~13/year); Jupiter return ~12 years (with a real effect window ~6mo-1.5yr around the exact hit, not just the instant); Saturn return ~29.5 years, universally treated as the single biggest-deal one.

**Location decision — resolved for now:** the field itself has a genuine, unresolved split between natal-location and relocated/current-location casting for return charts, with credible teachers on both sides. **Operator decision 2026-07-08: build to natal location for now**, for internal consistency with every other directed/timed technique already in EO (progressions, solar arc, profections all anchor to natal-location math). **Explicitly flagged as temporary**: the operator wants to move toward "modern influences" including current-location inclusion later — this is a real planned direction change, not a closed debate, so whoever implements E1 should build it in a way that doesn't hard-bake natal-only assumptions any deeper than necessary (keep the location input as a clean parameter, not implicit).

**Internal architecture check:** `engine/returns.py`'s own module docstring already says *"Return-chart interpretation is intentionally deferred"* — confirms E1 is exactly its documented gap. `engine/chart_wheel.py::build_chart_wheel_data()` (the function behind every existing chart wheel) is payload-shape-agnostic — it only needs `angles.Ascendant.longitude` and `standard_planets` on whatever dict it's given, so it's already reusable for a return chart, not natal-only. **Unresolved, not yet checked:** whether EO's natal-chart-construction pipeline (wherever `get_payload()` builds a full chart from birth data) can be pointed at an arbitrary datetime+location pair to produce that same payload shape for the *return* moment, or whether that construction path currently assumes "this is always the person's actual birth." That's the concrete next question before E1 can be scoped as "small, mostly wiring" vs. "needs new chart-construction code" — check this first when picking E1 back up.

---

## Standing rule, carried over

Anything that declares a flat ceiling or fixed number as EO-specific logic gets ignored in favor of actual astrological research/data. Nothing in any internal document (charter, spec, or otherwise) overrides real research for prediction functions — verify uncertainty, don't default to a presumed EO principle. This applied directly during Phase B/C (the orb-scaling fix) and should apply again here if any new thresholds come up while building the texture section.
