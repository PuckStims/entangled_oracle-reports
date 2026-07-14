# Entangled Oracle Location Services Product Stack

**Status:** Content-lead end-state specification.  
**Scope:** Product goals, evidence expectations, report sections, and claim boundaries for the Location Services family.  
**Primary anchor:** Place Resonance Search.
**Reusable evidence unit:** Place Profile, currently implemented by the
`place_resonance` package and legacy root-level Place Resonance modules.

## Product Thesis

Location Services turns place into an auditable symbolic layer. The work is not to rank the world from best to worst, and it is not to reduce a destination to a planetary keyword. The stack explains how a specific place changes the expression of an existing natal chart by bringing certain angles, houses, planets, and life arenas forward.

Core promise:

```text
A place does not rewrite the chart.
It changes which parts of the chart become louder, more visible, more private,
more pressured, more available, or more consequential.
```

## Shared Product Rules

- Every claim must be traceable to a structured evidence record.
- Relocation preserves the original birth UTC instant and recalculates angles/houses for the destination.
- Tropical zodiac and Whole Sign houses remain the production baseline.
- Natal condition modifies relocated expression; relocation does not overwrite natal condition.
- Static place evidence comes before map lines, Local Space, parans, or dynamic timing.
- No product declares a single universal best place.
- No product claims guaranteed love, wealth, safety, illness, destiny, success, or failure.
- Technical transparency is part of the premium product, not a backend footnote.

## Product Ladder

1. **Place Resonance Search** - curated discovery report that evaluates a
   candidate pool and surfaces the places whose symbolic field is worth the
   reader's attention.
2. **Place Profile** - reusable one-location depth unit, currently implemented
   by the `place_resonance` report path.
3. **Between Places** - comparison report across selected locations.
4. **World Lines Companion** - astrocartography map evidence companion.
5. **Local Compass** - Local Space directional report.
6. **Living Map** - time-sensitive geographic forecast layer.

## Product 1: Place Resonance Search

### User Question

Which places are most worth considering for the kind of life I am trying to
build, and what would each place emphasize, support, or demand from me?

### Product Role

Place Resonance Search is the flagship discovery product for the Location
Services suite. It does not ask the user to begin with one city and it does not
publish a bulk "best places" list. It evaluates a curated candidate pool,
selects a smaller set of meaningful locations, groups them into interpretive
buckets, and explains what each place is asking from the natal chart.

The current `place_resonance_search` package is a transitional product identity:
it is registry-wired but still wraps the single-location Place Resonance output
until candidate catalog, scoring, curation, and bucket logic are built.

### Required Inputs

- Birth date.
- Exact birth time.
- Birth location.
- Preferred search country or region, initially United States.
- Optional current residence or anchor location.
- Optional places already under consideration.
- Optional places to exclude.
- Optional goal weighting: visibility, restoration, love, friendship,
  study, creativity, stability, reinvention, or related life priorities.

### Included Evidence

- One `LocationEvidenceRecord` per evaluated candidate location.
- Theme-vector scores by life dimension.
- Overall resonance score.
- Complexity or pressure index.
- Consensus score across evidence types.
- Grounding score for quieter or stabilizing places.
- Baseline divergence or novelty score.
- Bucket assignment with evidence references.
- Technical appendix preserving candidate, coordinate, and scoring trace.

### Excluded Until Later Versions

- Practical city filters unless they have reliable mundane data sources.
- AI-generated web summaries of cities.
- Parans as a primary scoring layer.
- Local Space directionality.
- Current-year timing overlays.
- Claims of one objective best or worst location.

### Selection Buckets

- **Highest Resonance** - strongest multi-indicator support.
- **Goal-Specific Allies** - excellent for a defined theme, not universally easy.
- **Transformational / Demanding Places** - powerful, complex, high-pressure
  locations.
- **Quiet or Grounding Alternatives** - gentler support, lower drama, or
  stabilizing emphasis.
- **Pattern Outliers** - unusual chart shifts or surprising symbolic contrast.

### Report Sections

1. **Search Summary** - the central pattern across the selected locations.
2. **What This Search Is Pointing Toward** - the strongest repeated theme.
3. **Top Locations By Theme** - major life-dimension leaders.
4. **Curated Location Table** - selected cities, buckets, labels, and scores.
5. **Location Profiles** - compact one-place interpretations powered by the
   reusable Place Profile unit.
6. **Pattern Synthesis** - what the selected places reveal together.
7. **Practical Use Guidance** - how to use symbolic perspective without turning
   it into a command.
8. **Uncertainty And Safety Notes** - method boundaries, birth-time sensitivity,
   and unsupported methods.
9. **Technical Appendix** - candidate pool, coordinates, scoring trace, and
   exclusions.

### End-State Backend Needs

- U.S. candidate location catalog.
- Batch `LocationEvidenceRecord` generation.
- Theme-vector scoring.
- Complexity, consensus, grounding, and baseline-divergence indexes.
- Curated selection rules that avoid monotony and near-duplicates.
- Bucket assignment.
- Search-level prose routing.
- Technical appendix export for evaluated and selected candidates.

## Reusable Unit: Place Profile

### User Question

What changes when I live in, work in, visit, return to, or spend meaningful time in this specific place?

### Product Role

Place Profile is the one-location depth unit that interprets a single
destination. It is currently implemented by the existing Place Resonance
assembler, renderer, template, generator, and tests. It should remain stable
because it proves the relocated evidence pipeline and supplies reusable profile
language for Place Resonance Search, Between Places, and later products.

The legacy public name may remain `Place Resonance` during transition, but
planning docs should treat it as a reusable profile engine rather than the
long-term flagship product.

### Required Inputs

- Birth date.
- Birth time and birth-time confidence.
- Birth location.
- Destination location.
- Optional relationship to the place: current home, possible move, past home, travel, retreat, family place, work base, creative base.
- Optional purpose lens: career, belonging, rest, relationship, creative visibility, study, retreat, structure, experimentation.

### Included Evidence

- Relocated Ascendant, Midheaven, Descendant, and IC.
- Relocated Whole Sign houses.
- Planet natal-house to relocated-house changes.
- Planets near relocated angles.
- Major aspects or contacts to relocated angles, once supported by the backend.
- Natal condition of emphasized planets.
- Natal rulership links carried into relocated expression.
- Birth-time sensitivity and location precision notes.
- Explicit unsupported-method warnings.

### Excluded Until Later Products

- Astrocartography line distance claims.
- Parans.
- Local Space directions.
- Geodetic claims.
- Relocated returns.
- Dynamic timing overlays.
- Remote activation claims.

### Report Sections

1. **Place Signature** - the dominant symbolic emphasis of the destination.
2. **What Changes Here** - the main shift from natal baseline to relocated expression.
3. **Strongest Structural Evidence** - the highest-ranked evidence and why it leads.
4. **Relocated Angles** - how ASC, MC, DSC, and IC change the field of expression.
5. **House Shifts** - planets that move into more visible, private, relational, or operational terrain.
6. **Planets Brought Forward** - emphasized planets and the natal material they carry.
7. **What This Place Rewards** - participation style supported by the evidence.
8. **What May Require Adjustment** - pressure, friction, overuse, or mismatch grounded in evidence.
9. **Duration Lens** - short visit, extended stay, residence, return, or remote relationship to place.
10. **Purpose Lens** - how the location reads for the user's stated purpose.
11. **Evidence Summary** - ranked evidence table.
12. **Technical Appendix** - coordinates, time handling, calculations, exclusions, confidence notes.

### End-State Backend Needs

- `build_relocated_payload()`.
- `compare_natal_to_relocated()`.
- `build_location_evidence_record()`.
- Stable relocated angle and house fields.
- House-change list for planets and selected points.
- Relocated angle contact list.
- Natal modifier extraction for emphasized planets.
- Evidence ranking and confidence notes.
- Appendix trace.

## Product 2: Between Places

### User Question

How do these locations differ, and which one better supports a specific purpose without pretending there is one universally best place?

### Product Role

Between Places compares two to five destinations using the same Place Profile
evidence record. It is not a ranking gimmick. It is a contrast report for
choices: moving, travel, work bases, family locations, retreat options,
creative homes, or life-stage decisions.

### Required Inputs

- All Place Profile inputs.
- Two to five destinations.
- Optional decision context: relocation, travel, split life, work, relationship, restoration, visibility.
- Optional priority weights: stability, opportunity, intimacy, creative work, public role, recovery, study.

### Included Evidence

- One `LocationEvidenceRecord` per destination.
- Side-by-side dominant place themes.
- Shared evidence and contrast evidence.
- Purpose-lens fit.
- Tradeoffs: what each place foregrounds and what it may ask in return.
- Confidence notes where evidence is close, contradictory, or birth-time sensitive.

### Report Sections

1. **Comparison Summary** - the central contrast.
2. **Place Profiles** - compact one-location signatures.
3. **Best Fit By Purpose** - purpose-specific suitability, not universal ranking.
4. **Strongest Difference** - the evidence that most separates the places.
5. **Shared Themes** - where multiple places activate similar material.
6. **Tradeoff Map** - what each place supports and pressures.
7. **Decision Notes** - how to use the symbolism alongside practical reality.
8. **Technical Appendix** - location-by-location evidence trace.

### End-State Backend Needs

- Batch evidence-record generation.
- Comparison/ranking function.
- Purpose-lens weighting.
- Conflict and similarity detection across locations.

## Product 3: World Lines Companion

### User Question

Which planetary angularity lines are relevant to this place or region, and how should I understand them without overreading a map?

### Product Role

World Lines Companion is the astrocartography product. It explains map evidence with distance, angle type, line clustering, uncertainty, and natal context. It should make the map more trustworthy, not more sensational.

### Required Inputs

- Birth data.
- Destination or region.
- Optional line focus: career, partnership, belonging, creativity, retreat, study.

### Included Evidence

- Planetary ASC, DSC, MC, and IC lines.
- Nearest point on each relevant line.
- Distance to selected destination.
- Distance bands and strength policy.
- Birth-time sensitivity for line movement.
- Natal condition and house rulership of line planets.
- Clusters of nearby lines.

### Excluded Until Validated

- Parans, unless implemented as a deliberate method.
- Remote activation claims.
- Wide line claims with no defensible distance policy.
- Guaranteed event claims.

### Report Sections

1. **Map Summary** - the main line story.
2. **Closest Lines** - distance-ranked evidence.
3. **Angle Meaning** - how MC, IC, ASC, or DSC changes the planet's expression.
4. **Natal Context** - what the line planet carries from the birth chart.
5. **Distance And Uncertainty** - strength bands and birth-time sensitivity.
6. **Line Clusters** - coherent or conflicting nearby signals.
7. **Technical Appendix** - geometry, coordinates, tolerances, exclusions.

### End-State Backend Needs

- Astrocartography line generation.
- Distance-to-line and nearest-point geometry.
- Antimeridian and polar handling.
- Distance band policy.
- Map-ready geometry payload.

## Product 4: Local Compass

### User Question

From a chosen anchor place, which directions carry different symbolic emphasis, and how should I use that directional information?

### Product Role

Local Compass is the Local Space product. It is directional rather than relocation-first: it asks what planetary directions radiate from an anchor location and how a destination or movement path relates to those directions.

### Required Inputs

- Birth data.
- Anchor location.
- Optional destination or route.
- Optional use case: home layout, travel direction, city exploration, retreat selection, symbolic orientation.

### Included Evidence

- Planetary azimuths from the anchor location.
- Direction labels.
- Destination or route cross-track distance to each directional path.
- Natal condition of directional planets.
- Practical mode guidance.

### Excluded Until Validated

- Claims that a direction guarantees outcomes.
- Remote activation claims.
- Local Space claims without altitude/azimuth convention and distance policy.

### Report Sections

1. **Directional Signature** - the main directional pattern.
2. **Planetary Directions** - the strongest directions and what they emphasize.
3. **Destination Relationship** - how a chosen place relates to those paths.
4. **Use Modes** - movement, workspace, ritual, exploration, rest.
5. **Technical Appendix** - anchor, azimuths, distance policy, exclusions.

### End-State Backend Needs

- Local Space altitude/azimuth engine.
- Direction ray or great-circle path generation.
- Cross-track distance to direction lines.
- Direction grouping and confidence policy.

## Product 5: Living Map

### User Question

How does timing interact with place right now, without confusing temporary weather with the deeper location signature?

### Product Role

Living Map is the dynamic layer. It combines static location evidence with date-bounded timing, but only after Place Resonance and the standard timing clocks are stable. It should never make temporary transits sound like permanent location fate.

### Required Inputs

- Birth data.
- Destination or multiple destinations.
- Date range.
- Optional purpose lens.

### Included Evidence

- Static Place Resonance baseline.
- Date-bounded transits to relocated angles, if supported.
- Transits through relocated houses, if supported.
- Standard timing clocks already promoted into report-safe use.
- Temporary strength notes.
- Distinction between baseline resonance and current weather.

### Excluded Until Later

- Relocated returns until return charts exist.
- Dynamic astrocartography unless line geometry and timing policy are stable.
- Any timing claim that bypasses existing report governance.

### Report Sections

1. **Static Place Baseline** - what the place means before timing.
2. **Current Place Weather** - date-bounded shifts.
3. **Windows Of Emphasis** - active periods and what they temporarily amplify.
4. **What Is Baseline vs Temporary** - explicit distinction.
5. **Purpose Timing** - how the date range interacts with the stated purpose.
6. **Technical Appendix** - methods, dates, exclusions, confidence notes.

### End-State Backend Needs

- Stable `LocationEvidenceRecord`.
- Date-bounded relocated timing policy.
- Existing standard clocks integrated before reuse.
- Clear baseline-vs-weather field model.

## Product Priority

### Build First

Place Profile stability and Place Resonance Search contract.

Reason:

- The existing profile engine defines the relocated chart baseline.
- Search is the actual flagship product direction.
- Together, they force the core evidence record, batch candidate handling, and
  curated selection logic to become stable.
- They create content keys and profile language that later products can reuse.
- It avoids map geometry and dynamic timing before the foundation exists.

### Build Second

Between Places.

Reason:

- It reuses Place Profile records.
- It creates immediate commercial value.
- It tests evidence ranking and purpose lenses without needing astrocartography.

### Build Later

World Lines Companion, Local Compass, and Living Map.

Reason:

- Each requires new computation beyond simple relocation.
- Each can create overclaiming risk if launched before the evidence contract is mature.
