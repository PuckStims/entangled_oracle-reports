# Location Services Capability Inventory

**Status:** Source-grounded capability inventory for the Location Services stack.  
**Scope:** What EO already uses, what the current engine can likely support with new wiring, and what is not currently computable in this repo.  
**Source baseline:** `ARCHITECTURE.md`, `METHODS.md`, `engine/natal_engine.py`, `engine/transit_engine.py`, `engine/offline_place_resolver.py`, `formulas/report_surface.py`, `formulas/standard/*`, `formulas/governance_registry.py`, and the current product stack in `products/location_services/PRODUCT_STACK.md`.
**Standard-clock audit:** See `products/location_services/STANDARD_CLOCK_INTEGRATION_AUDIT.md` for the local-file pass on returns, profections, ZR, Lots, Moon progressions, progressions, and Solar Arc.

This document is intentionally about computation and report-facing data truth. It does not decide final product copy.

## Executive Classification

### Already Used In Production Reports

EO already computes and surfaces a strong natal/forecast foundation:

- Local birthplace resolution to display name, latitude, longitude, and timezone.
- Local birth time conversion to UTC and Julian Day.
- Tropical zodiac + Whole Sign houses as the only active production methodology.
- Ascendant, Midheaven, Descendant, Imum Coeli, and Vertex.
- Whole Sign house cusps and body house placement.
- Standard planets, true nodes, derived South Node, mean Black Moon Lilith, Chiron, and configured custom asteroids.
- Natal aspect matrix for planets, nodes, BML, asteroids, Ascendant, Midheaven, and Vertex.
- Standard formula layers: chart orientation, planetary conditions, prominence, chart ruler, house emphasis, luminary structure, aspect architecture, rulership/dispositors, named configurations, natal convergence, and forecast natal priority.
- EO proprietary indexes layered on top of the standard chart.
- Forecast event families: natal transits, Whole Sign house ingresses, planetary stations, eclipses, lunations, retrograde clusters, void-of-course Moon windows, daily activation transits, weekly contact timelines, Year Ahead events, and Personal Forecast event grouping.
- Progressions and Solar Arc directions as client-facing Year Ahead texture.
- Exact returns, annual profections, Lots, and Zodiacal Releasing as real computational modules; several are already surfaced in Year Ahead or Personal Forecast research layers, but none are finished location products.

### Computable Or Close, But Not Wired For Location Services

EO already has enough pieces to build the first relocation-aware product layer, but there is no dedicated Location Services engine yet:

- A destination can be resolved with the same offline resolver used for birth locations.
- Swiss Ephemeris `swe.houses(...)` is already used to calculate angles from a Julian Day and coordinates.
- Whole Sign houses can already be regenerated from any recalculated Ascendant.
- Planetary longitudes can be preserved from the natal instant while angles/houses are recalculated for destination coordinates.
- Standard formula modules can likely be rerun on a relocated payload once a safe relocated-payload constructor exists.
- Existing angularity logic can detect planets conjunct relocated angles if fed a relocated payload.
- Existing rulership and house-emphasis modules can support natal-vs-relocated comparison, with care to preserve natal condition separately from relocated expression.
- Existing forecast scanners can likely target relocated angles after a relocated payload exists, but this is not yet a product-safe dynamic location feature.

### Standard Predictive Logic That Should Not Stay Sandbox-Only

The predictive sandbox has historically been the proving ground for standard predictive computation. That does not mean validated standard clocks should remain quarantined forever. When a computation is standard, deterministic, tested, and governed, it should be promoted into the existing report family before Location Services depends on it.

The production rule is:

```text
standard predictive computation -> existing reports -> Location Services dynamic products
sandbox-only semantic experiments -> sandbox/R&D until separately validated
```

Current implications:

- Progressions and Solar Arc already belong in the production report conversation; they are not merely speculative sandbox vocabulary.
- Returns, profections, Lots, and Zodiacal Releasing are real computational modules. Returns, profections, and ZR already surface as Year Ahead timing/research context and can feed Personal Forecast's predictive research surface; Lots remain substrate for ZR rather than standalone report content.
- Predictive sandbox semantics such as lifecycle state, residual windows, experimental candidate phrasing, and semantic topology should not be copied into client products until each field has a production claim policy.
- Current report integration should be treated as the first promotion lane: standard clocks should graduate through Year Ahead / Personal Forecast before Living Map depends on them.
- Living Map should eventually reuse the same standard-clock infrastructure as Year Ahead and Personal Forecast, rather than invent a parallel predictive engine.

### Not Currently Computable As A Location Product

These require genuinely new computation, not just product wiring:

- Astrocartography MC/IC line generation.
- Astrocartography ASC/DSC global curve generation.
- Nearest-point and distance-to-line calculations for curved line geometry.
- Birth-time uncertainty as geographic line-shift estimates.
- Map geometry storage, antimeridian splitting, polar behavior, and map rendering.
- Parans.
- Local Space altitude/azimuth and directional path generation.
- Geodetic astrology.
- Relocated return charts.
- Return-chart interpretation.
- Multi-location comparison engine and fit-profile synthesis.
- Location-specific technical appendix schema.
- Location Evidence Record schema and report assembly layer.

## Already Used: Source-Of-Truth Details

### Birth And Location Normalization

`engine/natal_engine.py` requires birth date and birth location, with optional birth time and simple mode. It resolves the location, stores latitude/longitude/timezone, converts local datetime to UTC, and stores Julian Day in `user_profile`.

Current live fields:

```text
payload.location
payload.birth_location
payload.user_profile.queried_location
payload.user_profile.resolved_location
payload.user_profile.resolved_coordinates.latitude
payload.user_profile.resolved_coordinates.longitude
payload.user_profile.timezone
payload.user_profile.local_datetime
payload.user_profile.utc_datetime
payload.user_profile.julian_day
payload.user_profile.birth_time_state
payload.user_profile.birth_time_confidence
```

`engine/offline_place_resolver.py` uses packaged city data and timezone lookup to resolve ordinary strings such as `Peoria, IL` without network access.

Location Services implication:

- Destination location lookup can reuse this resolver.
- The current resolver is birthplace-oriented in naming and error text, but the computation is generic enough for destination lookup.
- Historical timezone quality still needs an explicit research/QA policy; current conversion depends on resolved IANA timezone and `zoneinfo`, not a dedicated historical atlas workflow.

### Active Methodology

`METHODS.md` and `formulas/standard/methodology_profiles.py` agree that production reports use:

```text
Tropical zodiac
Whole Sign houses
Swiss Ephemeris calculation
```

`methodology_profiles.py` declares other profile names, but `VALID_PROFILE_IDS` only includes `tropical_whole`, and `validate_profile_id()` rejects non-production profiles.

Location Services implication:

- Location Services should inherit Tropical + Whole Sign as the production baseline unless a separate future decision explicitly opens additional methodologies.
- Relocation work should not quietly introduce Placidus, sidereal, or synthesis profiles as production options.

### Natal Payload

`engine/natal_engine.py` already builds:

```text
angles
  Ascendant
  Midheaven
  Descendant
  Imum_Coeli
  Vertex

houses
  House_1 ... House_12

standard_planets
  Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn,
  Uranus, Neptune, Pluto, Chiron,
  North_Node, South_Node, Lilith_BML

custom_asteroids
  configured asteroid dictionary entries

aspects
  major natal aspects
```

Important detail:

- Descendant and Imum Coeli are calculated and stored.
- The natal aspect matrix intentionally includes Ascendant, Midheaven, and Vertex, but not Descendant or Imum Coeli, to avoid double-counting derived axes.
- The transit engine's target map does include ASC, MC, DSC, IC, and Vertex.

Location Services implication:

- Place Resonance can use all four relocated axes in its own evidence object without forcing DSC/IC into the natal aspect matrix.
- Relocated angle contacts should be a Location Services evidence type, not a mutation of the shared natal aspect matrix.

### Standard Formula Intelligence Already Available

`formulas/report_surface.py` bundles these standard categories:

```text
chart_orientation
planetary_conditions
planetary_prominence
chart_ruler
house_emphasis
luminary_structure
aspect_architecture
rulership_and_dispositors
named_configurations
natal_convergence
forecast_natal_priority
```

Useful modules for Location Services:

- `formulas/standard/angularity.py` identifies house type and angle conjunctions.
- `formulas/standard/planetary_condition.py` combines dignity, angularity, sect, and motion.
- `formulas/standard/rulership_network.py` maps house rulers, dispositors, receptions, and central routing planets.
- `formulas/standard/house_emphasis.py` and `formulas/standard/planetary_prominence.py` support emphasis ranking.
- `formulas/standard/forecast_activation.py` builds target and house weights used by forecast event routing.

Location Services implication:

- The engine already has the interpretive modifier spine needed for natal condition and rulership context.
- A future relocated payload must preserve the distinction between:
  - natal condition of a planet, and
  - relocated environmental expression of that planet.

### Forecast Timing Already Used

`engine/transit_engine.py` documents and implements:

- natal transit windows
- Whole Sign house ingresses
- planetary stations
- eclipses contacting natal targets
- lunations
- retrograde clusters
- void-of-course Moon windows
- daily activation transits
- weekly timeline contacts
- Year Ahead event timelines

`compute_year_ahead_events()` returns separate event families plus a combined chronology:

```text
transits
ingresses
stations
eclipses
lunations
progressions
return_events
zodiacal_releasing_events
time_lord_periods
zodiacal_releasing_periods
year_texture_progressions
year_texture_solar_arc
all_events
```

Location Services implication:

- Living Map should not start from scratch, but it cannot simply reuse Year Ahead unchanged.
- Date-bounded location timing needs a static location baseline first, then a clear policy for which timing methods can target relocated angles or location-specific charts.
- Any standard predictive clock proven in the sandbox should be evaluated for Year Ahead / Personal Forecast integration before it becomes a Location Services timing layer.

## Capable But Not Wired For Location Services

### Relocated Chart Baseline

Current code can calculate angles and Whole Sign houses for a latitude, longitude, and Julian Day, but `generate_payload()` currently ties the input location to the input local birth time.

Location Services needs a new helper that preserves the original birth instant:

```text
birth UTC instant + destination coordinates -> relocated angles + relocated houses
```

It should not reinterpret the birth time as local time in the destination city.

Likely reusable pieces:

- `swe.houses(julian_day, latitude, longitude, b"P")` fallback logic for angles.
- `build_angle_data()`
- `generate_whole_sign_houses()`
- `build_body_data()`
- `whole_sign_house()`
- standard formula modules once the relocated payload is assembled.

Missing wiring:

- `engine/location_services.py` or equivalent.
- `build_relocated_payload(natal_payload, destination_location)`.
- `compare_natal_to_relocated(natal_payload, relocated_payload)`.
- A stable `LocationEvidenceRecord`.
- Tests proving UTC instant is preserved.

### Relocated House Changes

The current payload stores every planet's Whole Sign house from the birth-location Ascendant. If a relocated Ascendant is calculated, the same longitudes can be reassigned to relocated Whole Sign houses.

What is close:

- Body longitude and sign already exist.
- Whole Sign house assignment helper already exists.
- House theme labels already exist.

Missing:

- a comparison object such as:

```text
body
natal_house
relocated_house
natal_house_label
relocated_house_label
changed
priority
```

### Relocated Angle Contacts

`formulas/standard/angularity.py` can evaluate whether a body is conjunct Ascendant, Descendant, Midheaven, or Imum Coeli within a given orb if the payload has those angles.

What is close:

- All four axis angles exist in the payload.
- Angularity evaluator checks all four axis angles.
- Existing orb policy can seed first tests, though Location Services needs its own deliberate orb policy.

Missing:

- relocated-angle contact evidence separated from natal condition.
- Place Resonance-specific orbs and confidence labels.
- rules for conjunction-only versus other aspects to relocated angles.

### Natal Modifiers For Location Reports

Planetary condition, sect, dignity, rulership, dispositorship, and house-emphasis modules are already available.

What is close:

- A location report can use natal condition of an emphasized planet as a modifier.
- Rulership networks can explain which natal houses a relocated angular planet carries into the destination context.

Missing:

- explicit Location Services rule: natal condition modifies relocated expression, but relocation does not rewrite natal condition.
- evidence ranking that decides when a natal modifier is strong enough to affect prose.

### Dynamic Timing Against Relocated Context

The transit engine can scan transits against payload targets, including all four angles internally. A relocated payload could theoretically make relocated angles the targets.

What is close:

- `engine/transit_engine.py` target map includes ASC, MC, DSC, IC, and Vertex.
- existing scanners can calculate transit contacts, ingresses, stations, eclipses, and lunations against a payload.

Missing:

- product policy for whether Living Map uses transits to relocated angles, transits through relocated houses, relocated returns, or another method.
- a baseline-vs-temporary distinction.
- assurance that relocated payloads do not corrupt natal baseline claims.
- output structures for date-bounded location evidence.

### Returns, Profections, Lots, Zodiacal Releasing

The modules exist and compute real structures:

- `engine/returns.py` finds exact Solar, Lunar, Jupiter, and Saturn return moments.
- `engine/profections.py` computes annual profection periods.
- `engine/lots.py` computes Fortune, Spirit, and Necessity.
- `engine/zodiacal_releasing.py` computes Zodiacal Releasing periods/events from Fortune and Spirit.

Location Services relevance:

- These can later inform Living Map or advanced timing products.
- They should also be evaluated for existing report integration where their computation is standard, tested, and bounded.
- They do not currently compute return charts or relocated return charts.
- They should not be treated as finished locational techniques simply because the base clock exists.
- Local audit result: Year Ahead already renders grouped returns/profections/ZR timing notes; Personal Forecast can consume returns/profections/ZR through forecast synthesis and predictive candidate prose; Lots remain a support calculation only.

## Not Currently Computable

### Astrocartography Lines

Missing computation:

- MC line longitude generation.
- IC line longitude generation.
- ASC curve generation.
- DSC curve generation.
- curve segmentation and storage.
- high-latitude discontinuity handling.
- antimeridian splitting.
- projection-aware rendering.
- nearest-point calculation.
- distance from selected city to a line.
- distance bands and strength estimates.
- birth-time uncertainty as line-shift distance.

Existing code can compute natal angles for one coordinate, but it does not generate global locations where a body is angular.

### Distance And Geometry

Missing computation:

- haversine or geodesic distance helpers for Location Services.
- nearest point on a polyline.
- cross-track distance to a great-circle segment.
- Earth model policy.
- unit conversion and rounding policy.
- geometry caching.

Without this, World Lines Companion cannot make defensible distance claims.

### Local Space

Missing computation:

- altitude/azimuth calculation from an anchor location.
- planetary direction rays or great-circle paths.
- destination cross-track distance to a direction path.
- anchor-location policy.
- direction labels and corridor grouping.

Swiss Ephemeris may provide lower-level functions that can help, but this repo does not currently expose a Local Space engine.

### Parans

Missing computation:

- exact paran definition.
- rise/set/culmination/anti-culmination timing convention.
- latitude-band generation.
- pairwise angular phase combinations.
- orb policy.
- distance from destination to paran band.

No active module implements parans.

### Relocated Return Charts

Missing computation:

- return-chart payload constructor at exact return moment.
- location parameter for return chart.
- return chart angles/houses/aspects.
- natal-to-return overlay.
- relocated/current-location return policy.

Current returns module computes exact return timestamps only.

### Multi-Location Comparison

Missing computation:

- running multiple Location Evidence Records in one report.
- normalized evidence strength across locations.
- near-tie detection.
- contradiction synthesis.
- purpose-lens fit profiles.
- comparison appendix by city.

Existing report code ranks events and targets, but there is no city-comparison engine.

### Location Evidence Record

Missing computation/schema:

- canonical LocationEvidenceRecord.
- product-specific subsets for Place Resonance, Between Places, World Lines Companion, Local Compass, and Living Map.
- traceable source fields for technical appendix.
- explicit excluded-method tracking.
- validation tests independent from prose.

## Product Implications

### Place Resonance

Closest to current capability.

What is ready:

- natal payload.
- destination resolution primitives.
- angle/houses calculation primitives.
- Whole Sign reassignment logic.
- natal condition and rulership modifiers.

What must be built:

- relocated payload constructor.
- natal-vs-relocated comparison.
- relocated angle contact evidence.
- LocationEvidenceRecord.
- technical appendix.
- report context and template.

What is not required for first truthful version:

- full astrocartography line engine.
- Local Space.
- parans.
- dynamic timing.

### Between Places

Depends on Place Resonance.

What is ready:

- nothing location-specific beyond the future Place Resonance record.

What must be built:

- multi-location orchestration.
- comparison categories.
- normalized evidence strength.
- close-call handling.
- purpose-specific fit profiles.

### World Lines Companion

Not close yet.

What is ready:

- natal planetary positions.
- birth instant and coordinates.
- Swiss Ephemeris dependency.

What must be built:

- astrocartography line engine.
- line geometry storage.
- nearest-line distance engine.
- map or map-derived output.
- birth-time sensitivity model.

### Local Compass

Not close yet.

What is ready:

- planetary positions and location resolution.

What must be built:

- horizontal coordinate calculation.
- azimuth/direction engine.
- path/destination relationship.
- Local Space-specific prose and appendix rules.

### Living Map

Conceptually related to current forecast engine, but not ready as a location product.

What is ready:

- robust forecast event infrastructure.
- transits, stations, ingresses, eclipses, lunations.
- progressions and Solar Arc for Year Ahead.
- return/profection/ZR scaffolds.

What must be built:

- existing-report promotion policy for any standard predictive clock that still lives only in sandbox/internal evidence.
- static location baseline first.
- method policy for location timing.
- dynamic LocationEvidenceRecord extensions.
- date-bounded location evidence ranking.
- clear distinction between temporary emphasis and permanent fit.

## Recommended Build Order From Capability Reality

1. Create destination location normalization that reuses `offline_place_resolver`.
2. Add a relocated chart helper that preserves the natal UTC instant.
3. Build a relocated payload shape with recalculated angles/houses and preserved planetary positions.
4. Build natal-vs-relocated house comparison.
5. Build relocated angle contact evidence.
6. Run existing standard formula modules against relocated payload only where conceptually valid.
7. Build `LocationEvidenceRecord`.
8. Build Place Resonance technical appendix.
9. Build Place Resonance report context and template.
10. Only then begin astrocartography line geometry for World Lines Companion.

## Guardrails

- Do not call a destination chart "relocated" unless the birth instant is preserved.
- Do not use destination local birth time as though the client were born there.
- Do not introduce Placidus or sidereal methodology through Location Services without an explicit product decision.
- Do not treat map line proximity as a full interpretation.
- Do not treat internal timing modules as finished locational methods.
- Do not merge dynamic timing into Place Resonance until static location evidence is stable.
- Keep natal condition separate from relocated expression.
