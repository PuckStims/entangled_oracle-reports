# Horoscope Prose Coverage Audit

Status: inventory only. This document lists current horoscope prose coverage,
block-routing depth, and missing authored alternatives before any prose
refinement work begins.

Date: 2026-07-12

## Scope

Included surfaces:

- `products/daily_horoscope`
- `products/weekly_horoscope`
- `products/sun_sign_horoscope`

Excluded from this pass:

- Year Ahead, Personal Forecast, Soul Ecosystem, and Identity Profile prose.
- New prose writing.
- Template changes.
- Recommendation of final block architecture.

The goal is to know what the horoscope family can currently express, what data
the runtime has available, and where JSON coverage is too thin to support a
serious prose overhaul.

## Routing Inventory

`config.py` registers `daily_horoscope` and `weekly_horoscope` as block-backed
report types in `REPORT_BLOCK_DIRS`. `sun_sign_horoscope` is not registered as
its own block type; its tooling reuses `daily_horoscope` blocks.

Daily Horoscope:

- Runtime context is built in `generate._build_horoscope_context`.
- It selects:
  - `daily_horoscope/todays_sky`
  - `daily_horoscope/your_activation`
  - `daily_horoscope/day_ruler`
  - `daily_horoscope/proprietary_reference`
  - `daily_horoscope/closing_line`
- The client template renders the activation header as machinery-forward text:
  `{{ activation_planet }} moves through your {{ natal_house_name ... }}`.

Weekly Horoscope:

- Runtime context is built in `generate._build_weekly_horoscope_context`.
- It uses `engine.transit_engine.compute_daily_timeline()` over a seven-day
  window, then caps displayed contacts at two per day.
- The runtime carries richer timing data than the prose layer currently uses:
  `transit_planet`, `aspect`, `aspect_character`, `natal_target`,
  `natal_target_display`, `natal_house`, `score`, and `peak_datetime`.
- The template currently renders the technical formula as the primary card
  line before the translated prose:
  `{{ moment.transit_planet }} {{ moment.aspect }} {{ moment.natal_target_display ... }}`.

Sun-Sign Horoscope:

- `products/sun_sign_horoscope/tooling/sun_sign_engine.py` computes a shared sky
  and maps the featured planet into solar houses by sign.
- It reuses Daily blocks:
  - `daily_horoscope/todays_sky`
  - `daily_horoscope/your_activation`
  - `daily_horoscope/day_ruler`
- It has no separate JSON prose library in this checkout.
- The card template and caption both use the machinery-forward activation
  phrase: `{activation_planet} moves through your {activation_house_name}`.

## Daily Horoscope Coverage

### `your_activation.json`

Purpose: personalized activation prose.

Declared key path: `transit_planet -> natal_house`.

Coverage:

| Dimension | Coverage |
|---|---:|
| Planets/bodies | 10/10 |
| Houses per body | 12/12 |
| Total leaves | 131 |
| Top-level fallback | yes |
| Per-body fallback | yes |

Bodies present:

- Sun
- Moon
- Mercury
- Venus
- Mars
- Jupiter
- Saturn
- Uranus
- Neptune
- Pluto

House coverage:

- Every listed body has authored entries for houses `1` through `12`.

Important limitation:

- This is a strong `planet x house` matrix, but it is not a contact matrix.
- It does not vary by aspect/contact type.
- It does not vary by natal target.
- It does not include multiple authored variants for the same `planet x house`
  key.

### `todays_sky.json`

Purpose: shared lunar atmosphere.

Declared key path: `moon_phase -> element`.

Coverage:

| Dimension | Coverage |
|---|---:|
| Moon phases | 8/8 |
| Elements per phase | 4/4 |
| Total leaves | 41 |
| Top-level fallback | yes |
| Per-phase fallback | yes |

Phases present:

- `new_moon`
- `waxing_crescent`
- `first_quarter`
- `waxing_gibbous`
- `full_moon`
- `waning_gibbous`
- `last_quarter`
- `balsamic`

Elements present for every phase:

- fire
- earth
- air
- water

### `day_ruler.json`

Purpose: one short day-ruler note.

Coverage:

| Dimension | Coverage |
|---|---:|
| Chaldean day rulers | 7/7 |
| Total leaves | 7 |

Bodies present:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn

### `proprietary_reference.json`

Purpose: optional proprietary-current reference in full Daily mode.

Coverage:

| Dimension | Coverage |
|---|---:|
| Index keys | 6 plus fallback |
| Total leaves | 13 |

Keys present:

- KVQ
- MKI
- RWI
- DFIS
- NGE
- CATALYST
- fallback

Observed shape:

- Most index keys have `dominant` and `fallback` branches.
- This is not a deep activation-state matrix.

### `closing_line.json`

Purpose: short closing line by lunar phase.

Coverage:

| Dimension | Coverage |
|---|---:|
| Moon phases | 8/8 |
| Total leaves | 9 |
| Fallback | yes |

## Weekly Horoscope Coverage

### Runtime Timing Data

Weekly uses `compute_daily_timeline()`, which has more detail available than the
current weekly prose JSON resolves.

Available runtime dimensions include:

- Transit body: Moon plus Sun through Pluto, when selected by the timeline scan.
- Aspect/contact: major aspects plus hard minor aspects in the daily timeline.
- Aspect character: flowing, challenging, or neutral.
- Natal target: target display is carried through the selected moment.
- Natal house: house number is carried through the selected moment.
- Score band: converted to reader-facing signal labels.
- Exact time: UTC peak timestamp.

Timeline aspects currently scanned:

- Conjunction
- Opposition
- Square
- Trine
- Sextile
- Semisquare
- Sesquiquadrate
- Quincunx

Aspect-character collapse:

- `Conjunction`, `Trine`, and `Sextile` become `flowing`.
- `Square`, `Opposition`, `Semisquare`, `Sesquiquadrate`, and `Quincunx`
  become `challenging`.
- Weekly prose selection usually sees only the collapsed character, not the
  exact aspect.

### `house_domains.json`

Purpose: short reader-facing domain labels by house.

Coverage:

| Dimension | Coverage |
|---|---:|
| Houses | 12/12 |
| Total leaves | 13 |
| Fallback | yes |

Important limitation:

- These are labels, not authored interpretations.
- They do not vary by planet, aspect, natal target, or emotional register.

### `planet_motifs.json`

Purpose: short planet motif clauses for weekly overview blocks.

Coverage:

| Dimension | Coverage |
|---|---:|
| Bodies | 10/10 |
| Total leaves | 11 |
| Fallback | yes |

Bodies present:

- Sun
- Moon
- Mercury
- Venus
- Mars
- Jupiter
- Saturn
- Uranus
- Neptune
- Pluto

Important limitation:

- These are motif clauses, not complete interpretations.
- They do not vary by aspect, natal target, house, or contact type.

### `aspect_movements.json`

Purpose: short weekly overview prompt by aspect character.

Coverage:

| Dimension | Coverage |
|---|---:|
| Aspect characters | 3/3 |
| Total leaves | 4 |
| Fallback | yes |

Keys present:

- flowing
- challenging
- neutral

Missing depth:

- No exact-aspect alternatives.
- No distinction between sextile and trine.
- No distinction between square, opposition, semisquare, sesquiquadrate, and
  quincunx.

### `theme_headline.json`

Purpose: weekly theme headline.

Coverage:

| Dimension | Coverage |
|---|---:|
| Aspect characters | 3/3 plus fallback |
| Total leaves | 12 |

Observed shape:

- Keyed by aspect character, with some planet-specific sub-branches.
- Not a complete `aspect_character x planet` matrix.

### `theme_overview.json`

Purpose: weekly overview paragraph.

Coverage:

| Dimension | Coverage |
|---|---:|
| Aspect characters | 3/3 plus fallback |
| Total leaves | 9 |

Observed shape:

- Keyed by `aspect_character -> guidance_mode`.
- Uses placeholders such as `{first_contact_phrase}`, `{contact_phrase}`,
  `{strongest_house}`, `{planet_prompt}`, and `{aspect_prompt}`.

Important limitation:

- Current placeholders can insert technical contact strings into prose.
- Coverage is not deep enough to resolve specific body/aspect/target/house
  meanings without generic composition.

### `watch_for.json`

Purpose: weekly watch-list items.

Coverage:

| Dimension | Coverage |
|---|---:|
| Aspect characters | 3/3 plus fallback |
| Item roles | domain, timing pattern, next move |
| Total leaves | 12 |

Important limitation:

- These are generic watch-list roles.
- They do not vary by body, exact aspect, natal target, or house.

### `work_with.json`

Purpose: practical weekly guidance.

Coverage:

| Dimension | Coverage |
|---|---:|
| Aspect characters | 3/3 plus fallback |
| Total leaves | 10 |

Observed shape:

- Keyed by `aspect_character -> guidance_mode`.
- Guidance modes include receiving, action, conversation, structure,
  discernment, visibility, and fallback paths.

Important limitation:

- This has guidance-mode variety, but not chart-specific prose depth.

### `day_movement.json`

Purpose: short day label in the weekly timing section.

Coverage:

| Dimension | Coverage |
|---|---:|
| Day characters | quiet, flowing, challenging, neutral plus fallback |
| Variants | six per branch |
| Total leaves | 30 |

### `day_guidance.json`

Purpose: day-level guidance before selected contacts.

Coverage:

| Dimension | Coverage |
|---|---:|
| Day characters | quiet, flowing, challenging, neutral plus fallback |
| Variants | six per branch |
| Total leaves | 30 |

Important limitation:

- Day guidance is keyed by day character, not by the actual contacts in the day
  except through placeholders.

### `moment_focus.json`

Purpose: contact-level localization sentence.

Coverage:

| Dimension | Coverage |
|---|---:|
| Bodies present | 9/10 |
| Missing body branch | Sun |
| Aspect characters per present body | fallback, flowing, challenging |
| Total leaves | 28 |

Bodies present:

- Moon
- Mercury
- Venus
- Mars
- Jupiter
- Saturn
- Uranus
- Neptune
- Pluto

Missing:

- Sun branch.
- Neutral branches per planet.
- Exact-aspect branches.
- Natal-target branches.
- House-specific authored branches.
- Variants per body/aspect-character key.

Important limitation:

- This is the thinnest layer relative to the amount of timing data available.
- It is currently a `planet x aspect_character` localization layer, not an
  interpretation matrix.

### `moment_guidance.json`

Purpose: contact-level practical guidance.

Coverage:

| Aspect character | Modes present | Variant depth |
|---|---|---:|
| fallback | fallback | 6 |
| flowing | fallback, action, receiving, pacing | 6 each |
| challenging | fallback, conversation, structure, discernment, adjustment, visibility | 6 each |
| neutral | fallback, visibility, pacing | 6 each |

Total leaves: 84.

Important limitation:

- Strong variant depth, but generic routing.
- It does not vary by planet.
- It does not vary by exact aspect.
- It does not vary by natal target.
- It does not vary by house except through surrounding context.

### `empty_week.json`

Purpose: fallback weekly reading when no selected exact contacts are retained.

Coverage:

| Dimension | Coverage |
|---|---:|
| Top-level sections | headline, overview, work_with, watch_for |
| Total leaves | 6 |

## Sun-Sign Horoscope Coverage

Sun-Sign has no independent JSON prose library in this checkout.

Current authored prose comes from Daily:

- `todays_sky.json`
- `your_activation.json`
- `day_ruler.json`

Sun-sign runtime computes:

- sign
- frame (`sun` or `moon`)
- moon phase
- moon sign
- day ruler
- featured planet
- featured aspect and partner for the Sun-sign frame
- solar house for the featured planet

Important limitation:

- The featured aspect and partner are computed, but the selected prose block is
  only `feature_planet x solar_house`.
- There is no sign-specific prose matrix.
- There is no `sign x planet x house` matrix.
- There is no aspect-aware sun-sign prose matrix.
- The card and caption both expose the activation as machinery-forward text
  before the authored block.

## Cross-Surface Coverage Gaps

### 1. Weekly Has Runtime Detail Without Matching Authored Depth

Weekly can know:

- body
- exact aspect
- natal target
- house
- exact time
- score band

But its JSON alternatives mostly resolve to:

- body motif
- house label
- aspect character
- guidance mode

The available data is deeper than the available prose structure.

### 2. Exact Aspects Are Not Authored as Distinct Meanings

No horoscope surface currently has a complete authored matrix for exact contact
types.

Weekly scans:

- Conjunction
- Opposition
- Square
- Trine
- Sextile
- Semisquare
- Sesquiquadrate
- Quincunx

But weekly prose mostly receives:

- flowing
- challenging
- neutral

This means a sextile and trine can collapse into the same prose family, and a
square, opposition, semisquare, sesquiquadrate, and quincunx can collapse into
the same prose family.

### 3. Natal Target Meaning Is Not Authored in Weekly Moment Prose

Weekly carries `natal_target` and `natal_target_display`, but current moment
prose does not select against natal target.

Missing target-aware alternatives include at least:

- Sun
- Moon
- Mercury
- Venus
- Mars
- Jupiter
- Saturn
- Uranus
- Neptune
- Pluto
- ASC
- MC
- DSC
- IC
- Vertex, when included by the timeline target pool

### 4. House Meaning Is Mostly Label-Level Outside Daily

Daily has real `planet x house` paragraphs.

Weekly has:

- `house_domains.json` labels
- placeholder insertion of `{house_theme}`

Weekly does not have authored house-specific interpretation at the contact
level.

### 5. Variant Depth Is Uneven

High variant depth:

- Weekly `moment_guidance.json`
- Weekly `day_guidance.json`
- Weekly `day_movement.json`

Low or no variant depth:

- Daily `your_activation.json`: one authored block per `planet x house`.
- Weekly `moment_focus.json`: one branch per `planet x aspect_character`.
- Weekly `planet_motifs.json`: one motif per planet.
- Weekly `house_domains.json`: one label per house.
- Sun-sign: no independent variants beyond reused Daily blocks.

### 6. Technical Display Hierarchy Is Not Covered by JSON Depth

The current coverage problem is not only a template problem. Even if technical
labels are moved below the meaning, weekly contact-level prose still lacks a
deep enough authored matrix to make every timing card feel crafted.

## Inventory Questions Before Refinement

These are listing questions only. They are not proposed fixes yet.

1. Which horoscope surfaces should receive new authored alternatives first:
   Daily, Weekly, Sun-sign, or all three as one family?

2. Should Weekly gain a new contact-level JSON matrix, and if so what is the
   minimum viable key path?

   Candidate dimensions to inventory before choosing:
   - transit body
   - exact aspect
   - aspect character
   - natal target
   - natal house
   - guidance mode
   - emotional register
   - variant number

3. Should Daily remain `planet x house`, or does it need variants by tone,
   dignity/strength, or activation source?

4. Should Sun-sign continue to reuse Daily blocks, or does it need a separate
   social-card prose library with shorter, feed-native variants?

5. Which exact contact types are allowed to appear in client-facing weekly
   timing cards, and which require extra translation because they are too
   technical to stand alone?

6. How many variants per key are needed before prose writing begins?

7. Should technical labels be generated from runtime fields only, while prose
   blocks stay fully translated and never include aspect names unless explicitly
   intended?

## Current Audit Conclusion

Daily Horoscope has the strongest authored coverage in the horoscope family,
with complete `planet x house` prose.

Weekly Horoscope has the richest timing data but the thinnest contact-level
authored coverage. It currently relies on labels, motifs, aspect-character
branches, and generic guidance variants rather than a true contact
interpretation matrix.

Sun-Sign Horoscope is structurally dependent on Daily blocks and has no
independent prose library.

Before any prose refinement, the next step is to decide the intended coverage
matrix for each horoscope surface, especially Weekly's contact-level prose.

## Follow-Up Wiring Audit

Status after the contact-selector wiring upgrade:

- Weekly now has a contact-level receiving architecture keyed by
  `transit_planet -> exact_aspect -> natal_target_group`.
- Exact aspects are preserved as selector inputs rather than only collapsing to
  `flowing` or `challenging`.
- Natal targets are grouped by function keys such as `identity`, `presence`,
  `public_role`, and `threshold`.
- House context is available as an independent secondary layer instead of a
  fourth key-path leg.
- Weekly moment rendering now has separate fields for primary meaning,
  secondary technical label, tertiary metadata, guidance, and selector trace.
- The new contact-matrix block leaves are still `TODO`; current rendered prose
  safely falls back to the older `moment_focus` and `moment_guidance` blocks.
- Selector trace is now structured and ledger-visible, so future audits can tell
  the difference between authored matrix coverage and legacy fallback output.

Remaining pre-prose truth:

- The wiring can now receive real prose.
- The contact matrix is not yet authored.
- A rendered weekly card that reads well today may still be reading well because
  legacy prose filled the `TODO` gap.
- Prose planning should use `selector_trace` and `weekly_prose_ledger` to avoid
  mistaking fallback safety for content completion.
