# Lightweight Forecast Surface Audit

Date: 2026-07-11
Scope: Daily Horoscope, Weekly Horoscope, Sun Sign Horoscope batch, and Cosmic Weather.

Editorial standards:

- `docs/prose_guides/Entangled_Oracle_Master_Plainspeak_Guide_v5.md`
- `docs/prose_guides/Entangled_Oracle_Anti-Monotony_Redundancy_Protocol_v2.md`
- `docs/prose_guides/README.md`

## Executive Summary

The lightweight forecast stack is not a static horoscope stack. It has real
calculation capacity, but most outputs intentionally compress that capacity into
short consumer surfaces.

The main product question is no longer "is there any astrology underneath?"
There is. The bar for the subscriber-email lane is whether a consumer feels a
productive mismatch between low price and high perceived depth: premium-feeling
prose, practical elucidation, and enough method truth to feel more substantial
than generic horoscope feeds.

## Product Map

| Product | Calculation capacity | Simplified output | Current status |
| --- | --- | --- | --- |
| Daily Horoscope | Natal payload, report-date Moon phase/sign, day ruler, station priority, same-day natal transit scan, Moon-house fallback, EO proprietary index reference | Short daily reading with sky, one activation lane, localized activation basis, day ruler, optional EO index card | Active localized surface; needs sample-output QA |
| Weekly Horoscope | Chart-specific exact contact scanner over seven full calendar days from the report date; includes Moon timing and rare slow-planet interior peaks; angle gating respects simple mode | Subscriber-style weekly theme, overview, practical guidance, watch-list, localized timing notes, and compact evidence | Active first interpretive layer; needs broader sample-output QA |
| Sun Sign Horoscope | Swiss Ephemeris daily sky, Moon phase/sign, day ruler, featured fast-planet sky aspect, solar houses by sign; optional Sun-sign or Moon-sign frame | One square card per sign/day plus captions | Operational social product; intentionally non-natal |
| Cosmic Weather | Swiss Ephemeris daily sky, Moon phase/sign, day ruler; reuses daily sky and day-ruler blocks | One collective card/day plus captions | Operational lightweight product; intentionally no signs, no natal layer |

## Complexity Versus Output

### Daily Horoscope

Computed complexity:

- exact report-date sky state
- Moon phase and Moon sign
- day ruler
- station-today priority
- same-day transit-to-natal activation with tight speed-adjusted orbs
- Whole Sign activation house
- Moon-house fallback
- dominant EO index reference when full natal data is available

Simplified output:

- `Today's Sky`
- `Your Activation` when not in simple mode
- `The Day's Ruler`
- optional proprietary reference
- activation-basis note explaining whether the day localized through a station,
  same-day natal contact, or Moon-house fallback
- closing line

Gap classification:

- Engine: adequate for a short daily product.
- Output: now carries both a calculation-basis note and localized activation
  source.
- Commercial readiness: needs generated sample review across exact-time and simple-mode cases.

### Weekly Horoscope

Computed complexity:

- exact contact scan across the selected seven-day report window
- chronological display after selection
- simple-mode gating for angle-dependent targets
- score and aspect character per moment

Simplified output:

- weekly theme headline
- weekly overview synthesized from selected exact contacts
- practical "Work With It" guidance
- watch-list
- supporting timing notes with per-moment localized focus, signal band, and
  reader guidance
- calculation-basis note

Gap classification:

- Engine: adequate for a subscriber weekly forecast starter.
- Output: no longer only a timing list; it now has a first interpretive layer.
- Content: needs broader sample QA across empty, Moon-heavy, slow-planet-heavy,
  simple-mode, and exact-time weeks before it can be called premium-ready.

### Sun Sign Horoscope

Computed complexity:

- one shared Swiss Ephemeris sky per date
- solar-house activation by sign
- Sun-sign and Moon-sign frames
- captions and manifest per batch

Simplified output:

- card-format social horoscope
- no natal specificity

Gap classification:

- Engine: appropriate for commercial social content.
- Output: intentionally simple.
- Workflow: needs periodic render QA and caption review.

### Cosmic Weather

Computed complexity:

- one shared Swiss Ephemeris sky per date
- Moon phase/sign
- day ruler
- day-use theme

Simplified output:

- one collective daily card
- no sign-specific or natalized activation

Gap classification:

- Engine: appropriate for local/business content and general social posting.
- Output: intentionally simple.
- Workflow: needs render/caption QA before scheduling runs.

## Implementation Notes

This pass added explicit complexity/simplification contracts:

- Daily Horoscope context: `horoscope_complexity_capacity`,
  `horoscope_simplified_output_contract`, `activation_source`,
  `activation_basis_line`
- Weekly Horoscope context: `weekly_complexity_capacity`,
  `weekly_simplified_output_contract`, `weekly_theme_headline`,
  `weekly_theme_overview`, `weekly_work_with`, `weekly_watch_for`,
  `weekly_narrative_basis`, plus per-moment `signal_band`,
  `localized_focus`, and `reader_guidance`
- Sun Sign manifest: `complexity_capacity`,
  `simplified_output_contract`
- Cosmic Weather manifest: `complexity_capacity`,
  `simplified_output_contract`

## Remaining Audit Stack

1. Generate exact-time Daily Horoscope and confirm the activation lane matches
   the manifest/context evidence.
2. Generate simple-mode Daily Horoscope and confirm activation/proprietary
   sections suppress cleanly while sky/day-ruler content remains useful.
3. QA Weekly Horoscope across varied weeks and decide whether the synthesized
   narrative layer is enough for launch, or whether it needs a curated block
   library comparable to the Year Ahead prose packs.
4. Generate Sun Sign and Cosmic Weather sample batches, render cards, and check
   card fit plus captions.
5. Decide whether the commercial package needs a single operator runbook for
   lightweight forecast content.

## Predictive Upgrade Localization Boundary

The expanded predictive upgrades are appropriate source architecture for richer
horoscope language, but not all of them should be exposed directly inside daily
or weekly emails.

- Daily and Weekly may borrow the Tier 3 pattern of transparent ranking/local
  relevance: why this signal led, what life area it localizes through, and how
  to use it.
- Weekly may borrow the Tier 4/Tier 5 synthesis posture: theme first, evidence
  second, contradictions and density handled without pretending every event has
  equal weight.
- Personal Forecast and Year Ahead remain the correct surfaces for full
  long-range predictive terrain, progressions, solar arc, profections, returns,
  and zodiacal releasing.
- A future premium Weekly tier could call a bounded forecast-synthesis adapter,
  but that should be a deliberate product tier rather than accidental scope
  creep in the base email.
