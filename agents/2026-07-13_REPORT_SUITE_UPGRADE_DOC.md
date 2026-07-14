# 2026-07-13 Report Suite Upgrade Doc

This note is the July 13 handoff for the Entangled Oracle report-suite
polish pass and the next Soul Ecosystem expansion pass. It is meant to
save the next agent from reconstructing the day from scattered diffs,
chat history, and QA artifacts.

## Blanket Agent Rule: Update Stale References

If you notice referenced information in files is outdated, update it
instead of acknowledging it and then ignoring it. If the update is unsafe
or outside your assigned scope, record the exact stale reference and the
needed correction in `agents/PLANNED_UPDATES.md` before moving on.

## Scope of today's work

The active work today was a product-readiness polish pass across the
current client-facing report suite:

- `Year Ahead` as the flagship premium almanac
- `Soul Ecosystem` as the natal / proprietary baseline product
- `Personal Forecast` as the 90-day seasonal bridge
- `Weekly Horoscope` as the subscription timing layer
- `Daily Horoscope` as the lightweight daily touchpoint

The operator's guardrails for this pass were:

- do not flatten EO into generic wellness language
- do not remove technical transparency
- do not remove proprietary EO concepts
- do not add excessive disclaimers
- do not rewrite the astrology engine or change calculation logic except
  for specific bug fixes
- do not reduce report depth just because a report is long
- do not make every report visually identical
- do not overcorrect into sterile professionalism

For future content-writing decisions, the governing prose references are:

- `docs/prose_guides/Entangled_Oracle_Master_Plainspeak_Guide_v5.md`
- `docs/prose_guides/Entangled_Oracle_Anti-Monotony_Redundancy_Protocol_v2.md`

If a future prompt conflicts with those guides, the guides win.

## Primary files touched in the live suite

- `generate.py`
- `selectors/variable_resolver.py`
- `products/shared/report_visual_system.css`
- `products/year_ahead/templates/active/year_ahead.html`
- `products/soul_ecosystem/templates/soul_ecosystem.html`
- `products/personal_forecast/templates/personal_forecast.html`
- `products/weekly_horoscope/templates/weekly_horoscope.html`
- `products/daily_horoscope/templates/daily_horoscope.html`
- `products/daily_horoscope/blocks/your_activation.json`
- `tests/test_phase1_client_forecast_adequacy.py`

Supporting documentation and audit surfaces added or referenced in the
same window:

- `docs/prose_guides/README.md`
- `HOROSCOPE_PROSE_COVERAGE_AUDIT.md`
- `LIGHTWEIGHT_FORECAST_SURFACE_AUDIT.md`

## What landed

### 1. Cross-suite presentation and trust pass

The suite was moved closer to a coherent family surface without making
every report visually identical.

Shared improvements now in play across the active templates:

- stronger report identity metadata blocks
- more consistent footer / brand / generated-date treatment
- recurring trust language:
  - calculation basis
  - method note
  - birth-time confidence
  - Tropical zodiac / Whole Sign houses / Swiss Ephemeris references
  - proprietary EO layer note where relevant
- closer alignment around container / card styling and section hierarchy

### 2. Year Ahead: premium almanac framing

The Year Ahead surface was upgraded toward a flagship almanac / manual /
annual companion identity.

Key additions and polish targets:

- `How to Use This Almanac`
- annual-companion orientation language
- stronger internal navigation and section distinction
- preserved trust architecture and technical note visibility
- readability / premium-use framing rather than scope reduction

### 3. Soul Ecosystem: baseline product framing

Soul Ecosystem was made more obviously foundational inside the suite.

Key additions and polish targets:

- `How to Use This Report`
- explicit suite-role framing
- clearer hierarchy for:
  - Core Pattern
  - Growth Pattern
  - World Pattern
  - World Interface
  - EO Pattern Depth
  - Narrative Current / Power Current / Foresight Pattern
- stronger bridge sentences before dense proprietary sections
- clearer explanation that EO layers deepen the natal baseline rather
  than replace it

### 4. Personal Forecast: 90-day bridge framing

Personal Forecast was clarified as a focused seasonal bridge rather than
an abbreviated Year Ahead or an inflated weekly.

Key additions and polish targets:

- `How to Use This Forecast`
- stronger `Season at a Glance` treatment
- stronger `Three Headline Themes` treatment
- cleaner metadata block and trust-note consistency
- better separation between themes, event lists, and practical guidance

### 5. Weekly Horoscope: renderer cleanup and scanability

The weekly surface was refined as a short-form subscription timing
product.

Key work:

- duplicated natal-house phrasing removed from the weekly timing-event
  renderer path
- stronger scan hierarchy:
  - Week Theme
  - Work With It
  - Watch For
  - Timing Notes
  - Daily entries
- clarified method note about selected exact contacts, cap-per-day, and
  chronological ordering
- label cleanup around contradictory-feeling support vs challenging
  language

### 6. Daily Horoscope: safer and cleaner lightweight touchpoint

The daily surface stayed compact while gaining better trust and safer
action phrasing.

Key work:

- preserved the compact daily structure
- tightened action language around money / health / legal /
  relationship-adjacent topics toward concrete, proportionate, reversible
  steps
- standardized footer and calculation-basis treatment
- clarified EO cross-reference wording:
  `Fuller context appears in the Soul Ecosystem report when included in your package.`

## Rendered artifact trail

HTML outputs generated in this window:

- `tmp/finalized_suite_html/year_ahead_test_name_2026-07-13.html`
- `tmp/finalized_suite_html/soul_ecosystem_test_name_2026-07-13.html`
- `tmp/finalized_suite_html/personal_forecast_test_name_2026-07-13.html`
- `tmp/finalized_suite_html/weekly_horoscope_test_name_2026-07-13.html`
- `tmp/finalized_suite_html/daily_horoscope_test_name_2026-07-13.html`

PDF / visual QA artifacts generated in this window:

- `tmp/pdfs/year_ahead_test_name_2026-07-13.pdf`
- `tmp/pdfs/soul_ecosystem_test_name_2026-07-13.pdf`
- `tmp/pdfs/personal_forecast_test_name_2026-07-13.pdf`
- `tmp/pdfs/weekly_horoscope_test_name_2026-07-13.pdf`
- `tmp/pdfs/daily_horoscope_test_name_2026-07-13.pdf`
- `tmp/pdfs/weekly_horoscope_polish_qa.pdf`
- `tmp/pdfs/daily_horoscope_full_qa.pdf`
- `tmp/pdfs/daily_horoscope_simple_qa.pdf`

Preview PNGs were also generated under `tmp/pdfs/preview_pngs/`.

## Known follow-up items from the current pass

- run the final end-of-pass guardrail audit across the full suite rather
  than trusting prompt compliance alone
- confirm any remaining date-span wording differences in Year Ahead are
  intentional and not metadata mismatch
- confirm final PDF route with `browser_print` when production PDFs are
  needed; prior audit output suggested browser chrome from the audit path,
  not necessarily a report-template bug
- decide whether Daily remaining two-page behavior in full-mode QA is
  acceptable product behavior or whether it should be forced into a
  tighter single-page contract

## Soul Ecosystem expansion runway

Planning work in the same session established a clear direction for the
next Soul Ecosystem pass.

### Core conclusion

Do not de-proprietize Soul Ecosystem. Instead, make the non-proprietary
baseline more visibly alive and let the EO layer read as a deeper
synthesis rather than the only thing carrying interpretive weight.

### Recommended expansion structure

Use a three-layer model:

1. `Standard natal foundation`
   - signs, houses, rulers, aspects, angularity, modality / element
     balance, sect, dignities where useful
2. `Established astro-psych / interpretive support`
   - only where it clarifies function, development, tension, and lived
     pattern
3. `EO proprietary synthesis`
   - Narrative Current, Power Current, Foresight Pattern, archetypal
     drivers, expression architecture, cross-report continuity

### Best expansion candidates by existing section

- `Core Pattern`
  - chart ruler
  - Sun / Moon / Ascendant relationship
  - elemental / modal weighting
  - angular emphasis
- `Growth Pattern`
  - Saturn and Mars development logic
  - hard-aspect learning patterns
  - houses requiring sustained labor, repair, or maturation
- `World Pattern`
  - MC and relevant house-ruler logic
  - 9th / 10th / 11th house participation / vocation / meaning vectors
- `World Interface`
  - how the inner chart becomes visible through public, relational, and
    consequential life surfaces

### Preferred expansion techniques

- add short `why this is true in the chart` bridges
- use open / established astrological language where it adds mechanism
- keep EO layers as the naming and deep-pattern synthesis layer
- add specificity, not just more category language

### Avoid

- imported material that competes with EO cosmology
- extra abstractions that do not map to chart mechanics
- generic wellness language
- clinical over-explanation that drains intimacy

### Recommended next planning artifact

Build a `Soul Ecosystem expansion matrix` with four columns:

- current section
- add standard natal support
- add established astro-psych support
- keep proprietary only

That matrix should drive the actual expansion implementation pass.

## Recommended next sequence

1. Final audit of the current suite changes against the guardrails and
   prose guides.
2. Build the Soul Ecosystem expansion matrix from the live template plus
   current report structure.
3. Implement the expansion in bounded, section-specific seams.
4. Re-render HTML and production-route PDFs.
5. Do final prose-modification review plus PDF QA before push.
