# Entangled Oracle Location Services Product Stack

**Status:** Product goal specification.  
**Scope:** End-state product stack for EO locational astrology services. This document defines the reports and service experiences the backend must ultimately support; it is not a tentative implementation phase plan.

## Product Thesis

Entangled Oracle Location Services turns locational astrology into evidence-routed place intelligence: not a map of generic planetary keywords, not a ranked list of "best places," and not a substitute for practical relocation judgment. The product stack explains how a specific place reorganizes the expression of a natal chart, how multiple places differ, and how geographic symbolism can be read with calculation transparency, interpretive discipline, and EO's adult report voice.

The central promise is simple:

> A place does not rewrite the chart. It changes which parts of the chart become louder, more visible, more private, more pressured, more available, or more consequential.

The stack is built around five end-goal products:

1. **Place Resonance** - one-location depth report.
2. **Between Places** - multi-location comparison report.
3. **World Lines Companion** - astrocartography map evidence companion.
4. **Local Compass** - Local Space directional report.
5. **Living Map** - time-sensitive geographic forecast layer.

All five products share a canonical evidence backbone so prose, maps, comparison tables, and technical appendices are generated from the same auditable location record.

## Product Principles

### Evidence Before Interpretation

Every reader-facing claim must trace back to explicit location evidence: relocated angles, relocated houses, angular contacts, nearby planetary lines, distance bands, Local Space direction, dynamic timing evidence, or a clearly labeled synthesis of multiple signals.

### Location-Specific, Not Keyword-Based

The product stack must not reduce locational astrology to `Venus = love`, `Jupiter = luck`, or `Pluto = danger`. Planetary function, angle, natal condition, house context, distance, purpose lens, and uncertainty all modify the final claim.

### No Universal Best Place

EO does not declare one city "best." It identifies fit, emphasis, contrast, pressure, support, and purpose-specific suitability. A city can be better for visibility and worse for restoration. A place can be compelling for a short stay and demanding as a permanent home.

### Confident Interpretation, Bounded Claims

The prose should make clear interpretive moves without pretending to predict objective life outcomes. EO is not hesitant about symbolic meaning, but it does not claim that a location guarantees love, success, illness, wealth, danger, or spiritual destiny.

### Technical Transparency Is Part Of The Product

The technical appendix is not afterthought documentation. It is part of the premium trust layer: coordinates, time handling, relocated angles, house shifts, line distances, angular contacts, supported objects, excluded methods, confidence notes, and evidence rankings should be inspectable.

### Product Voice

Location Services inherits the EO prose standard:

- Translate machinery into lived-life language by default.
- Name the mechanism when it helps the reader understand why they received a claim.
- Avoid generic caution loops and decorative vagueness.
- Give each section a distinct job.
- Keep deterministic future-fact claims out of production surfaces.
- Use professional symbolic timing language rather than horoscope-app gimmickry.

## Shared Location Evidence Record

Every product writes from a shared canonical object rather than directly from raw calculations.

```text
LocationEvidenceRecord
  identity
    subject_id
    report_id
    product_id
    generated_at

  birth_context
    birth_date
    birth_time
    birth_location
    birth_timezone
    birth_time_confidence
    utc_instant
    calculation_profile

  destination_context
    location_id
    display_name
    latitude
    longitude
    elevation_m
    timezone
    coordinate_precision
    user_relationship
    purpose_lens

  relocated_chart
    ascendant
    midheaven
    descendant
    imum_coeli
    house_system
    house_cusps
    planet_house_changes
    relocated_angle_contacts
    relocated_chart_ruler_notes

  astrocartography
    nearest_lines
    line_distances
    nearest_points
    distance_bands
    line_strength_estimates
    line_clusters
    excluded_line_claims

  natal_modifiers
    natal_condition_of_emphasized_planets
    natal_house_rulership_links
    natal_aspect_modifiers
    natal_angularity_modifiers

  local_space
    origin_location
    planetary_azimuths
    direction_labels
    destination_cross_track_distances

  dynamic_location_timing
    date_range
    timing_method
    active_windows
    static_signature_relationship
    temporary_strength_notes

  evidence_ranking
    primary_evidence
    supporting_evidence
    contradictory_evidence
    speculative_or_excluded_evidence
    confidence_notes

  prose_inputs
    dominant_place_theme
    secondary_place_themes
    practical_modes
    resonance_scope
    technical_terms_to_name
    safety_notes

  appendix_trace
    calculation_sources
    tolerances
    unsupported_methods
    warnings
```

## Shared Evidence Hierarchy

The final stack uses a transparent hierarchy so stronger evidence shapes the report before weaker or more school-dependent techniques.

### Primary Structural Evidence

- A planet tightly conjunct a relocated angle.
- A major natal planet changing into an angular relocated house.
- The relocated Ascendant, Midheaven, IC, or Descendant changing the chart's expression in a major way.
- A selected destination falling very close to a natal planetary angularity line.
- A tight paran once paran support is researched and validated.

### Major Contextual Evidence

- Relocated house changes for planets with strong natal relevance.
- Major aspects to relocated angles.
- Multiple nearby planetary lines that tell a coherent story.
- Natal rulership links carried into relocated houses.
- Strong Local Space alignment from a selected anchor.

### Supporting Evidence

- Moderate line proximity.
- Non-angular relocated house emphasis.
- Repeated but weaker evidence across techniques.
- Purpose-lens fit, such as career, restoration, belonging, experimentation, or creative visibility.

### Research-Only Or Restricted Evidence

- Remote activation claims.
- Wide map crossings with no actual astronomical relationship.
- Geodetic symbolism.
- Dynamic timing claims before the static location baseline is established.
- Any technique that cannot be explained deterministically in the technical appendix.

## Product 1: Place Resonance

### Product Promise

Place Resonance is EO's flagship one-location report. It answers:

> What changes when I live in, work in, visit, return to, or spend meaningful time in this specific place?

The report describes how one selected destination reorganizes natal expression through relocated angles and houses, nearby planetary angularity lines, natal modifiers, distance, and explicit uncertainty.

### Commercial Role

Place Resonance is the anchor product for Location Services. It serves people considering a move, understanding a current home, reflecting on a formative past place, planning extended travel, choosing a retreat or work base, or seeking language for why a place feels different.

### Required Inputs

- Birth date.
- Birth time, with confidence level.
- Birth location.
- Selected destination location.
- Optional current residence.
- Optional relationship to the place: current home, future option, past home, work location, retreat, travel, family location, creative base.
- Optional purpose lens: visibility, belonging, rest, relationship, career, creative work, structure, experimentation, healing, study, retreat.

### Included Evidence

- Relocated chart generation.
- Recalculated Ascendant, Midheaven, Descendant, and IC.
- Relocated houses and house cusps.
- Natal-versus-relocated planet house changes.
- Planets becoming angular in the relocated chart.
- Major contacts to relocated angles.
- Nearest ASC, DSC, MC, and IC planetary lines.
- Distance from destination to nearby lines.
- Natal condition of emphasized planets.
- Natal rulership carried into relocated context.
- Birth-time sensitivity and location precision notes.

### Excluded From Production Claiming

- Parans until definition, timing convention, orb policy, and validation are complete.
- Local Space until the Local Compass product is ready.
- Dynamic timing overlays until Living Map is ready.
- Geodetic methods.
- Remote activation claims.
- "This is your best place" conclusions.

### Report Structure

1. **Location Summary** - the destination's dominant symbolic emphasis in plain language.
2. **What Changes Here** - the most important shift from natal baseline to relocated expression.
3. **The Strongest Structural Shift** - the highest-ranked evidence and why it leads the report.
4. **Relocated Angles And Houses** - what the recalculated chart foregrounds.
5. **Planets Brought Forward** - planets made louder through angularity, house change, or rulership.
6. **Nearby Planetary Lines** - closest relevant lines, distance, and what each line adds.
7. **What This Place Rewards** - the participation style the place appears to support.
8. **What May Require Adjustment** - friction, pressure, overuse, or mismatch grounded in evidence.
9. **Short Stay, Long Residence, Or Returning Place** - how duration changes the report's use.
10. **Current Home / Past Place / Future Option Lens** - contextual reading based on the user's relationship to the place.
11. **Evidence Summary** - ranked evidence table in reader-friendly language.
12. **Technical Appendix** - coordinates, calculations, orbs, distances, uncertainty, and exclusions.

### Prose Standard

Place Resonance should sound like environmental emphasis analysis written by someone with astrological judgment, not travel-horoscope copy. It should be warm, grounded, specific, and unafraid to name the pattern.

Preferred language:

- "This place foregrounds..."
- "The public/private balance changes here..."
- "The location rewards..."
- "The chart becomes more oriented toward..."
- "This is strong evidence for..."
- "The line is close enough to treat as regional emphasis..."

Avoid:

- "Move here to find love."
- "This is your luckiest city."
- "Never live near this line."
- "This city guarantees success."
- "You are destined to..."

### Technical Appendix

The appendix must include:

- Destination name, coordinates, timezone, and coordinate precision.
- Birth-time confidence and UTC conversion note.
- House system.
- Relocated angles and house cusps.
- Planetary house changes.
- Relocated angle contacts with orbs.
- Nearest planetary lines with angle, distance, nearest point, and distance band.
- Evidence ranking.
- Birth-time sensitivity note.
- Supported objects.
- Excluded techniques.
- Calculation profile and tolerances.

## Product 2: Between Places

### Product Promise

Between Places compares multiple locations without flattening them into a universal ranking. It answers:

> How do these places differ for me, and what is each one best suited to hold?

The product runs Place Resonance logic across two to five candidate locations, then synthesizes the differences through purpose-specific fit profiles.

### Commercial Role

Between Places is a premium decision-support product for relocation, job offers, retreat selection, long-term travel, creative bases, family moves, school choices, or retrospective comparison of places that shaped the client.

### Required Inputs

- Birth date.
- Birth time, with confidence level.
- Birth location.
- Two to five candidate locations.
- Optional current residence.
- Optional priority lens: visibility, restoration, relationship, stability, experimentation, creative work, study, home, family, spiritual practice, professional recognition.

### Included Evidence

- Full Place Resonance evidence per location.
- Cross-location comparison of relocated angularity.
- Cross-location comparison of house emphasis.
- Nearest-line comparison.
- Natal baseline contrast.
- Current-home contrast when supplied.
- Purpose-lens fit profiles.
- Near-tie and contradiction handling.

### Reader-Facing Comparison Categories

- **Visibility And Public Contribution**
- **Home, Belonging, And Restoration**
- **Relationship Contact And Collaboration**
- **Creative Permission And Pleasure**
- **Structure, Pressure, And Accountability**
- **Experimentation And Reinvention**
- **Study, Meaning, And Perspective**
- **Long-Term Integration**

### Report Structure

1. **Comparison Overview** - the central difference among the locations.
2. **How To Read The Comparison** - purpose-specific fit, not universal ranking.
3. **Place Profiles** - concise Place Resonance summary for each location.
4. **Category Comparison** - where each place is strongest, most demanding, or most ambiguous.
5. **Current Home Baseline** - if supplied, how the current place differs from the candidates.
6. **Best For Specific Uses** - visibility, restoration, experimentation, stability, belonging, creative work, etc.
7. **Contradictions And Tradeoffs** - where one place supports one domain while complicating another.
8. **Close Calls** - locations whose evidence is too similar for a strong distinction.
9. **Decision Language** - grounded reflection frames, not commands.
10. **Technical Appendix By City** - evidence table and calculation trace per location.

### Prose Standard

Between Places should sound comparative, clean, and non-combative. It should describe different environments inviting different versions of the person.

Preferred language:

- "Chicago carries stronger public-accountability evidence."
- "Santa Fe reads as more restorative, but less forceful for vocational traction."
- "These two locations are close enough that practical considerations should lead."
- "This is not a better/worse split; it is a difference in what each place foregrounds."

Avoid:

- Universal city scores as the main result.
- "Winner" framing.
- "Worst city" framing.
- Collapsing the whole report into one number.

Internal numeric scores may exist for sorting and evidence ranking, but reader-facing output should use fit profiles, strength bands, and conditional language.

## Product 3: World Lines Companion

### Product Promise

World Lines Companion gives the reader a disciplined map-based view of their planetary angularity lines. It answers:

> Which planetary angularity lines are nearest to this place, and how much should that map evidence matter?

The companion is a map and evidence product, not a full relocation reading.

### Commercial Role

World Lines Companion can function as an add-on to Place Resonance, a lower-cost exploratory product, or a visual appendix for clients who want to inspect the line evidence behind a report.

### Required Inputs

- Birth date.
- Birth time, with confidence level.
- Birth location.
- Optional selected city.
- Optional object and angle filters.

### Included Evidence

- Planetary ASC, DSC, MC, and IC lines.
- Nearest lines to selected city.
- Distance from selected city to nearest lines.
- Line clusters.
- Same-planet axis relationships where meaningful.
- Birth-time sensitivity estimate.
- Supported object list.

### Excluded From Production Claiming

- Deep relocated-chart interpretation.
- Parans unless paran support is explicitly added.
- Local Space.
- Dynamic transits.
- Claims based on visual crossings alone.
- "Line proximity equals destiny" language.

### Report Structure

1. **Map Overview** - what the map shows and what it does not show.
2. **Nearest Lines** - closest three to six relevant lines for the selected city.
3. **Line Meanings** - planet plus angle interpretation grounded in EO language.
4. **Distance And Strength** - transparent distance bands rather than hard magic thresholds.
5. **Line Clusters** - multiple nearby lines, if they create a coherent emphasis.
6. **Birth-Time Sensitivity** - how much uncertainty affects the map.
7. **How This Connects To Place Resonance** - why a map is only one evidence layer.
8. **Technical Appendix** - geometry, nearest points, supported objects, and exclusions.

### Prose Standard

World Lines Companion can be lighter and more exploratory than Place Resonance, but it must stay disciplined. The visual layer should feel evocative without pretending to be the whole truth.

Preferred language:

- "This line is close enough to be considered in the regional field."
- "The map evidence supports the relocation-chart emphasis."
- "This line is visually noticeable but not close enough to lead the interpretation."

Avoid:

- "You are on the line" without distance support.
- Treating every visual crossing as meaningful.
- Strong relocation claims from map evidence alone.

## Product 4: Local Compass

### Product Promise

Local Compass interprets symbolic directionality from a chosen anchor point. It answers:

> What directions or directional corridors carry meaningful symbolic emphasis from this anchor?

This product uses Local Space logic to describe planetary directions from a birthplace, current home, selected city, retreat site, studio, business headquarters, or other meaningful anchor.

### Commercial Role

Local Compass is a later premium or niche product for reflective users, artists, ritual planners, travelers, place-based creators, and clients who want to understand local or regional directionality rather than only relocation.

### Required Inputs

- Birth date.
- Birth time, with confidence level.
- Birth location.
- Selected anchor location.
- Optional destination or exploration radius.
- Optional purpose lens: creativity, connection, restoration, outreach, study, retreat, business development, pilgrimage.

### Included Evidence

- Planetary azimuths from the anchor.
- Altitude values where useful.
- Direction labels.
- Directional clustering.
- Destination cross-track distance to planetary direction paths.
- Anchor-dependent interpretation.

### Excluded From Production Claiming

- Strong destiny claims from direction alone.
- "Travel east for Venus love" simplifications.
- Parans.
- Dynamic timing overlays.
- Geodetic methods.

### Report Structure

1. **Anchor Overview** - what place the compass is reading from.
2. **How Local Compass Differs From World Lines** - direction from an anchor, not global angularity.
3. **Dominant Directional Signatures** - strongest planetary directions.
4. **Directional Corridors** - how nearby places, routes, or regions relate to the compass.
5. **Planetary Directions In Practice** - symbolic directionality translated into use.
6. **Purpose Lens** - creative, relational, restorative, professional, spiritual, or exploratory use.
7. **Working With Direction Without Overclaiming** - reflective guidance.
8. **Technical Appendix** - anchor coordinates, azimuths, altitude, direction labels, and calculations.

### Prose Standard

Local Compass can be more contemplative and poetic than the decision-support products, but the method/metaphor boundary must stay visible. It should invite exploration, not issue commands.

Preferred language:

- "This direction carries Venus symbolism from the chosen anchor."
- "The western corridor may be useful for exploring..."
- "Treat this as directional symbolism, not an instruction."

## Product 5: Living Map

### Product Promise

Living Map adds time to the static location layer. It answers:

> Which places are temporarily emphasized for me during this period, and how does that differ from my long-term location baseline?

The product interprets date-bounded geographic activation through selected forecast methods layered onto an already-established location record.

### Commercial Role

Living Map is an advanced premium layer or subscription add-on for users who already understand their static location signatures and want current-year or seasonal geographic timing.

### Required Inputs

- Birth date.
- Birth time, with confidence level.
- Birth location.
- Current residence.
- Target date range or year.
- Selected cities, regions, or known location list.
- Optional purpose lens.

### Included Evidence

- Static Place Resonance baseline per selected location.
- Date-bounded timing activations.
- Temporary strengthening of existing static signatures.
- Transit-to-relocated-angle or other validated dynamic evidence.
- Time windows with intensity and confidence.
- Difference between temporary activation and permanent place fit.

### Excluded From Production Claiming

- "Move now" commands.
- Global rankings without user-selected context.
- Excessively layered timing stacks that cannot be explained.
- Permanent suitability claims from temporary timing evidence.
- Objective-fact predictions.

### Report Structure

1. **Period Overview** - the geographic theme of the date range.
2. **Static Baseline Reminder** - what is permanent or structural in the location record.
3. **Temporary Geographic Emphasis** - places that become louder during the period.
4. **Activation Windows** - date-bounded windows with clear method labels.
5. **Where Static And Temporary Evidence Agree** - strong reinforcement.
6. **Where Timing Complicates The Baseline** - a temporary emphasis that is not the same as long-term fit.
7. **How To Use The Window** - symbolic timing guidance without relocation commands.
8. **Technical Appendix** - methods, date range, windows, orbs, intensity, exclusions.

### Prose Standard

Living Map must be time-sensitive, explicit, and carefully bounded. It should sound like temporary amplification, not permanent relocation truth.

Preferred language:

- "This location is temporarily louder during this window."
- "The timing reinforces an existing static signature."
- "This is a useful period to test the place, not proof that it is the right permanent base."

Avoid:

- "Move here now."
- "This city is activated, therefore it is your destiny."
- "This date guarantees the outcome."

## Stack-Level Product Relationships

### Place Resonance As The Interpretive Core

Place Resonance is the foundation because every other product either compares it, visualizes part of it, localizes it directionally, or time-activates it.

### Between Places As Multi-Location Synthesis

Between Places is not a separate calculation universe. It is a comparison and synthesis layer over multiple Location Evidence Records.

### World Lines As Visual Evidence

World Lines Companion explains map evidence. It should never outrank relocated-chart evidence by visual drama alone.

### Local Compass As Directional Symbolism

Local Compass uses a different geometry and a different interpretive register. It belongs in the stack, but its claims should not be mixed casually into Place Resonance unless the report explicitly opts into Local Space evidence.

### Living Map As Time Activation

Living Map depends on the static location baseline and the existing report family's validated predictive clocks. Standard predictive computations should graduate into Year Ahead, Personal Forecast, or other appropriate existing reports before they become Location Services timing layers. Sandbox-only semantic experiments remain R&D until they have a production claim policy.

Living Map must always distinguish temporary emphasis from long-term place fit.

## Backend Engine End-State Contract

The end-state backend must support the following capabilities.

### Location Normalization

- City and coordinate lookup.
- Timezone identification.
- Historical timezone support.
- Coordinate precision labels.
- Elevation storage where available.
- User relationship to place.
- Current residence and selected destination separation.

### Birth-Time Handling

- Exact time.
- Approximate time.
- Unknown time suppression or severe qualification.
- Rectified time label.
- Birth-time sensitivity estimates for angles and lines.
- Confidence notes surfaced in the report and appendix.

### Relocated Chart Engine

- Preserve the birth instant.
- Recalculate angles and houses for destination.
- Preserve planetary positions except where explicitly configured otherwise.
- Recalculate location-dependent points where supported.
- Compare natal and relocated house placements.
- Identify relocated angular planets.
- Identify major contacts to relocated angles.
- Produce JSON-safe evidence output.

### Astrocartography Line Engine

- Generate MC and IC lines.
- Generate ASC and DSC curves.
- Support antimeridian splitting.
- Handle high-latitude discontinuities.
- Store line geometry.
- Calculate nearest point from a selected city to each line.
- Calculate geographic distance in miles and kilometers.
- Assign transparent distance bands.
- Estimate line movement from birth-time uncertainty.

### Comparison Engine

- Normalize evidence strength across locations.
- Preserve qualitative distinctions rather than collapsing everything to a rank.
- Detect close calls.
- Detect contradictory evidence.
- Group evidence by reader-facing category.
- Generate purpose-lens summaries.

### Local Space Engine

- Calculate planetary altitude and azimuth from an anchor.
- Generate directional paths.
- Label directions in reader-friendly compass language.
- Calculate destination relationship to a directional path.
- Preserve anchor identity and method notes.

### Dynamic Location Engine

- Accept static location baselines.
- Add date-bounded timing evidence.
- Support selected forecast methods only when validated.
- Reuse standard predictive computations already accepted into existing reports instead of creating a parallel location-only prediction stack.
- Keep sandbox-only semantic fields out of production Location Services until each field has explicit governance, content, and safety policy.
- Relate temporary activation to permanent location signatures.
- Generate time windows, intensity, confidence, and exclusions.

### Evidence Ranking Layer

- Separate primary, supporting, contradictory, speculative, and excluded evidence.
- Preserve method labels.
- Preserve confidence.
- Preserve calculation trace.
- Provide prose assembly inputs.
- Provide appendix tables.

### Report Assembly Layer

- Select sections based on product.
- Translate evidence into EO prose.
- Name technical mechanisms where useful.
- Generate technical appendix from the same evidence object.
- Avoid repeated phrase families and generic caution loops.
- Prevent deterministic objective-fact claims.

## Product-Level Safety Contract

All Location Services products must state or imply the following boundary:

> A location can emphasize, foreground, complicate, or support symbolic themes. It does not guarantee outcomes, replace practical decision-making, or override housing, legal, immigration, financial, healthcare, accessibility, climate, family, or safety realities.

This boundary should not make the report timid. It should make the product more trustworthy. The report can land clear symbolic claims while remaining clear about what kind of claim is being made.

## Competitive Differentiation

The market already has:

- Clickable astrocartography maps.
- Free relocation calculators.
- Professional software map modules.
- Low-cost city-comparison PDFs.
- AI-style line explanations and theme filters.

EO's differentiated lane is:

- Report-first rather than map-first.
- Evidence-routed rather than keyword-routed.
- Relocated-chart depth plus line proximity, not one or the other.
- Adult prose rather than viral astrology language.
- Purpose-specific fit rather than universal ranking.
- Technical appendix and uncertainty as premium trust features.
- Static baseline before dynamic timing.

## Stack Inventory

```text
products/location_services/
  PRODUCT_STACK.md
  future:
    research/
      historical_lineage.md
      calculation_spec.md
      competitor_audit.md
      validation_suite.md
    schemas/
      location_evidence_record.schema.json
      place_resonance.schema.json
      between_places.schema.json
    blocks/
      place_resonance/
      between_places/
      world_lines_companion/
      local_compass/
      living_map/
    templates/
      place_resonance.html
      between_places.html
      world_lines_companion.html
      local_compass.html
      living_map.html
    runtime/
      location_context.py
      evidence_ranking.py
      comparison_context.py
```

The inventory above describes the natural product home. It does not mean every file exists yet or that all products should be built at once.

## Research Agenda Anchored To End Products

Research should begin from the end-state product contract, not from curiosity about every locational method. The required research sequence is:

1. Define the calculation standard for relocated charts.
2. Define house system and angle policy.
3. Define relocated angle contacts and orbs.
4. Define natal-versus-relocated house comparison.
5. Define how natal rulership modifies relocated evidence.
6. Define MC and IC line calculation.
7. Define ASC and DSC curve calculation.
8. Define distance-to-line geometry.
9. Define defensible distance bands.
10. Define birth-time uncertainty behavior.
11. Define the Location Evidence Record schema.
12. Define technical appendix requirements.
13. Define comparison logic for Between Places.
14. Define map-output requirements for World Lines Companion.
15. Promote validated standard predictive clocks from sandbox/internal evidence into the existing report family where appropriate.
16. Define Local Space only after the static report core is stable.
17. Define dynamic location timing only after static evidence, comparison, appendix truth, and existing-report predictive integration are stable.

## Finished Stack Standard

The Location Services stack is complete when EO can generate:

- A one-location report that explains how a destination reorganizes the natal chart.
- A multi-location report that compares places by purpose-specific fit without universal ranking.
- A map companion that shows line evidence without overclaiming.
- A Local Space report that treats directionality as symbolic exploration with method clarity.
- A dynamic location report that distinguishes temporary timing from permanent place fit.
- A shared technical appendix across all products.
- A canonical evidence object that can be tested independently from prose.
- Prose that is confident, specific, non-repetitive, and clear about the boundary between symbolic pattern and objective outcome.
