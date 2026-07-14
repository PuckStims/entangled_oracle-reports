# Location Services Prose Purpose Review

**Status:** Content-lead review against existing EO JSON block libraries.  
**Scope:** What current product block files teach us about building Place Resonance prose for depth and personalized variability.  
**Primary source files reviewed:** active block routes from `config.py`, representative JSON under `products/daily_horoscope/blocks`, `products/weekly_horoscope/blocks`, `products/year_ahead/blocks/plainspeak`, `products/personal_forecast/blocks/shared`, `products/soul_ecosystem/blocks`, and `products/identity_profile/blocks`.

## Executive Read

The stronger EO block files are not simple text insert banks. They use JSON structure to define a prose job:

- what evidence is being interpreted;
- what kind of claim the block may make;
- how the block changes tone under strength, domain, duration, method, or activation state;
- what fallback preserves when exact evidence is unavailable;
- how repetition is avoided without hiding the evidence.

Location Services should follow that pattern. The first Place Resonance block pack should not ask for finished generic paragraphs like "Venus on the Midheaven means...". It should create evidence-shaped prose modules where the same base contact can deepen, soften, redirect, or become an aside depending on relocated angle, contact strength, natal condition, house movement, purpose lens, relationship to place, and repeated evidence.

## Active Product Patterns To Reuse

### Daily Horoscope: Concrete Localized Expression

Representative file:

```text
products/daily_horoscope/blocks/your_activation.json
```

Pattern observed:

- Small key path: `transit_planet -> natal_house`.
- Fully authored, direct, lived-language leaves.
- Each leaf translates a planet/house fact into a concrete daily arena.
- Fallbacks preserve usefulness without pretending specificity.

Location Services use:

- Good model for `planet_relocated_house_blocks.json`.
- A relocated house block should make the placement feel lived: rooms, roles, conversations, visibility, privacy, rhythm, belonging.
- It should not stay at keyword level.

Risk if copied too directly:

- Daily blocks are short-cycle and immediate. Place Resonance needs more durable place-climate language.

### Weekly Horoscope: Guidance Mode Separation

Representative files:

```text
products/weekly_horoscope/blocks/contact_meanings.json
products/weekly_horoscope/blocks/work_with.json
```

Pattern observed:

- `contact_meanings.json` is a large evidence grid with TODO-safe leaves and unusually strong `_note` guidance.
- It deliberately avoids a fourth key-path dimension by pushing house context into separate interpolation.
- `work_with.json` separates practical guidance from contact meaning by routing through aspect character and guidance mode.

Location Services use:

- Good model for scaffolding large grids without flattening them.
- `relocated_angle_contact_blocks.json` should define meaning; a separate synthesis or guidance family should define "how to work with this place."
- House/domain context should be injectable, not necessarily another axis on every angle-contact leaf.

Risk if copied too directly:

- Weekly guidance is action-oriented. Location Services should be decision-supportive, not prescriptive.

### Year Ahead: Synthesis, Agreement, Contradiction, and Climate

Representative files:

```text
products/year_ahead/blocks/plainspeak/forecast_synthesis_blocks.json
products/year_ahead/blocks/plainspeak/predictive_chapters.json
products/year_ahead/blocks/plainspeak/annual_profection_blocks.json
products/year_ahead/blocks/plainspeak/return_blocks.json
products/year_ahead/blocks/plainspeak/zodiacal_releasing_blocks.json
```

Pattern observed:

- `forecast_synthesis_blocks.json` does not interpret one astrological fact. It names relationship between facts: convergent, supportive, isolated, ambiguous, contradictory, background.
- `predictive_chapters.json` varies by timing method and life domain, with a stable research-signal voice.
- Newer scaffold files use literal `TODO` plus notes, preserving future writing intent without faking finished prose.

Location Services use:

- Best model for `location_synthesis_blocks.json`.
- Place Resonance needs agreement labels: repeated planet, repeated angle/domain, angle plus house change, house-only, quiet/no-house-change, mixed public/private signals.
- The synthesis family should decide whether an evidence item becomes a main section, supporting paragraph, tag, or appendix note.

Risk if copied too directly:

- Year Ahead predictive scaffolds deliberately hedge as research signals. Place Resonance can be more confident because relocated chart evidence is the product's actual supported method, but it must still avoid outcome guarantees.

### Personal Forecast: Domain By Method Family

Representative file:

```text
products/personal_forecast/blocks/shared/predictive_candidates.json
```

Pattern observed:

- Key path: `candidate_domain -> leading independent_method_family`.
- The same domain changes depending on how the evidence arises.
- The prose avoids settled prediction and asks the reader to gather lived evidence.

Location Services use:

- Good model for purpose and relationship-to-place lenses.
- "Career" should not always mean the same thing. Career through Midheaven angle contact, a 10th-house shift, natal Saturn condition, or same-place quiet evidence should all sound different.
- The selector should know whether a purpose fit comes from angle evidence, house shift evidence, repeated evidence, or weak/quiet evidence.

Risk if copied too directly:

- Personal Forecast is timing-centered. Place Resonance is place-centered: the question is not "when will this happen?" but "what does this location make easier to encounter, repeat, or sustain?"

### Soul Ecosystem: Deep Identity And Contribution Language

Representative files:

```text
products/soul_ecosystem/blocks/midheaven.json
products/soul_ecosystem/blocks/reality_field.json
products/soul_ecosystem/blocks/narrative_current.json
```

Pattern observed:

- Single-axis and two-axis files can still be deep when the prose purpose is clear.
- The best leaves name a function, an expression, a constructive use, and a boundary.
- Public-role language is mature, non-hype, and avoids status promises.

Location Services use:

- Good voice model for Midheaven/10th-house place signatures.
- Use this depth when a place foregrounds contribution, visibility, authority, public role, or vocation.
- A locational public signature should say what kind of contribution becomes legible, not whether the person becomes famous or successful there.

Risk if copied too directly:

- Soul Ecosystem is natal identity/contribution. Location Services must say "this place foregrounds" rather than "you are."

### Identity Profile: Multi-Axis Personalization

Representative files:

```text
products/identity_profile/blocks/identity_synthesis.json
products/identity_profile/blocks/archetypal_tensions.json
```

Pattern observed:

- The strongest personalization comes from axis crossing: genre, index/current, activation state.
- Blocks are not interchangeable because each leaf adjusts the developmental posture: awakening, embodied, sovereign.
- Tension files treat mixed evidence as an interpretive asset, not an error.

Location Services use:

- Best model for later high-depth locational synthesis.
- Place Resonance should eventually distinguish "awakening to this place's signal," "living inside the place signal," and "integrating a past or remote place signal."
- Tension handling should treat public/private, freedom/belonging, ease/pressure, and expansion/structure as meaningful cross-currents once domain taxonomy exists.

Risk if copied too directly:

- Identity Profile can speak ontologically. Location Services should remain conditional and place-specific.

## Locational Prose Purposes By Block Family

### `technical_appendix_blocks.json`

Primary job:

- Explain what was calculated, what was not calculated, how confident the angle-sensitive evidence is, and why warnings exist.

Existing-product pattern to imitate:

- Year Ahead scaffolds and synthesis blocks: clear, bounded, method-aware.

Purpose standard:

- This file should increase trust without sounding apologetic.
- It should distinguish "unsupported in this version" from "computed and weak" from "computed and strong."
- It should render `warning_summary`, not raw `warnings`, for reader-facing text.

Avoid:

- Turning unsupported methods into marketing promises.
- Overexplaining implementation details in the main report voice.

### `relocated_angle_contact_blocks.json`

Primary job:

- Translate `angle -> body -> contact_strength` into how a place foregrounds a chart function.

Existing-product pattern to imitate:

- Weekly `contact_meanings.json` for grid discipline and `_note` guidance.
- Soul Ecosystem `midheaven.json` for mature public-role language.

Purpose standard:

- Each leaf should name:
  - what the angle means in location;
  - what the body brings forward;
  - what `tight`, `moderate`, or `wide` changes;
  - what the claim does not guarantee.

Personalization variables that should modulate prose:

- `contact_strength`: tight gets central language; wide gets edge-of-contact language.
- `natal_modifiers[body].condition_classification`: excellent/strong can support smoother expression; strained or missing should add handling language.
- `natal_modifiers[body].was_natal_angular`: repeated natal and relocated angularity should read as reinforcement, not novelty.
- `purpose_lens`: same evidence can be useful, exposing, distracting, or low-signal depending on user purpose.
- `relationship_to_place`: short visit, residence, past place, or remote connection should alter stakes.

Avoid:

- "Venus on the Midheaven means fame/love/money."
- Single-paragraph leaves that ignore strength, natal condition, and purpose.

### `planet_relocated_house_blocks.json`

Primary job:

- Explain how a natal function changes rooms in the relocated chart.

Existing-product pattern to imitate:

- Daily `your_activation.json` for concrete house-based lived examples.
- Personal Forecast `predictive_candidates.json` for domain-specific variations.

Purpose standard:

- This file should feel highly personal because it answers "where does this planet go in this place?"
- It should handle `same_house`, `house_changed`, `newly_angular`, `leaves_angular`, and `unknown` differently.
- `same_house` should not be treated as empty. It can preserve continuity, especially when angle contacts still exist.

Personalization variables that should modulate prose:

- natal house vs relocated house;
- angularity change;
- planet/body;
- natal condition;
- contact overlap with relocated angles;
- whether body lacks natal modifiers.

Avoid:

- House keyword inserts that could be used in any report.
- Treating all house changes as improvement or loss.

### `house_shift_blocks.json`

Primary job:

- Interpret the domain shift itself, independent of body.

Existing-product pattern to imitate:

- Forecast synthesis for relationship between facts.
- Identity tension files for mixed-domain interpretation once available.

Purpose standard:

- This file should eventually hold the house-to-domain taxonomy and become the bridge from raw houses to public/private/relational/operational language.
- In v0.1, it should remain scaffolded or selector-internal until the taxonomy is authored.

Avoid:

- Asking the engine to invent `moves_public` or similar editorial categories.

### `natal_modifier_blocks.json`

Primary job:

- Qualify relocated evidence by the body's natal condition.

Existing-product pattern to imitate:

- Personal Forecast method-family modulation: same domain, different pathway.
- Identity Profile activation states: same signature, different developmental posture.

Purpose standard:

- This file should answer "what version of this planet arrives when the place foregrounds it?"
- It should not override the angle or house interpretation; it should add texture, ease, friction, capacity, or caution.

Personalization variables that should modulate prose:

- condition classification;
- sect condition;
- motion condition;
- natal angularity;
- natal house type;
- confidence.

Avoid:

- Recomputing condition for relocated payloads.
- Treating good condition as guaranteed benefit or hard condition as guaranteed harm.

### `purpose_lens_blocks.json`

Primary job:

- Translate evidence into the user's stated use case without promising outcomes.

Existing-product pattern to imitate:

- Personal Forecast candidate grid: domain plus evidence pathway.
- Weekly guidance files: meaning separated from "how to work with it."

Purpose standard:

- This file should eventually distinguish strong fit, conditional fit, tradeoff, low signal, and conflicted evidence.
- It should tell the user how the place relates to their question, not whether the place is objectively best.

Avoid:

- "Career place," "love place," or "healing place" labels without evidence strength and tradeoff language.

### `location_synthesis_blocks.json`

Primary job:

- Decide the report's reading order and overall place signature.

Existing-product pattern to imitate:

- `forecast_synthesis_blocks.json` almost directly, but with place-centered language instead of month/year timing.

Purpose standard:

- This is where repeated evidence becomes a coherent Place Signature.
- It should identify primary evidence, supporting evidence, quiet evidence, mixed evidence, and excluded evidence.
- It should decide what becomes a main paragraph vs a short aside.

Needed synthesis categories:

```text
convergent_place_signature
angle_led_signature
house_shift_led_signature
repeated_body_signature
quiet_continuity_signature
mixed_public_private_signature
purpose_aligned_signature
purpose_tradeoff_signature
low_signal_signature
fallback
```

Avoid:

- Forcing every destination into a dramatic story.
- Treating contradiction as failure once the taxonomy exists.

### `duration_lens_blocks.json`

Primary job:

- Change the stakes of the same evidence based on relationship to the place.

Existing-product pattern to imitate:

- Identity Profile activation posture.
- Daily vs Year Ahead contrast: short activation vs sustained climate.

Purpose standard:

- A short visit should read as activation/testing.
- Residence should read as operating environment and sustainability.
- Past place should read as retrospective meaning, not advice.
- Remote connection should read as symbolic/relational activation, not embodied relocation.

Avoid:

- Using the same paragraph for a trip, a move, a childhood home, and a remote city someone is considering.

## What The First Block Pack Should Prioritize

Write first:

1. `technical_appendix_blocks.json`
2. `relocated_angle_contact_blocks.json`
3. `planet_relocated_house_blocks.json`
4. `location_synthesis_blocks.json`

Why:

- They match the evidence record that exists now.
- They can create depth without the unresolved house-domain taxonomy.
- They prevent the product from sounding like a generic relocation report.

Write after selector taxonomy:

1. `house_shift_blocks.json`
2. `purpose_lens_blocks.json`
3. `duration_lens_blocks.json`
4. `natal_modifier_blocks.json`

Why:

- These need more selector judgment or careful cross-evidence routing to reach EO-level personalization.
- They are valuable, but writing them too early risks generic labels.

## Main Content Risk

The main risk is not missing prose. The main risk is writing prose too early at the wrong granularity.

Bad direction:

```text
Venus + Midheaven = public charm paragraph.
Moon + fourth house = home paragraph.
Career lens = career paragraph.
```

Correct direction:

```text
Venus near relocated Midheaven, tight, repeated by 10th-house shift, natal Venus strong, purpose lens career, residence context = central public-social contribution signature.

Venus near relocated Midheaven, wide, no house repetition, natal Venus strained, purpose lens rest, short visit context = light visibility/contact note, possibly pleasant but not the main reason to choose the place.
```

## Recommended Claude Boundary

Claude should not author final prose yet. Claude can safely build:

- JSON scaffold files with `TODO` bodies;
- rich `_note` fields carrying the prose purpose and modulation rules;
- schema tests for required keys, fallbacks, and placeholder allowance;
- selector utilities that assemble evidence bundles for content selection.

Content lead should own:

- final body prose;
- house-to-domain taxonomy;
- purpose fit taxonomy;
- contradiction taxonomy;
- anti-monotony rules for repeated locational sections.

