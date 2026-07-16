# Product Data Contract Gaps — Location Services

**Status:** GEMINI FIRST-PASS DRAFT. Capability status labels must be
verified by Claude Code against the actual engine before any item is
treated as authoritative.

**Source documents:** `LOCATION_EVIDENCE_RECORD_CONTRACT.md`,
`BLOCK_SCHEMA.md`, `PRODUCT_STACK.md`, `CAPABILITY_INVENTORY.md`
(reviewed for context).

**Important:** This document does not change what the backend produces.
It inventories what each product needs and where the gaps are.

---

## Current Direction Overlay

This draft predates the Place Resonance Search pivot. The Place Resonance
section below remains useful as the data-gap inventory for the reusable
one-location **Place Profile** engine. It is not the complete flagship product
contract. The flagship Search product additionally needs candidate catalog,
batch profile generation, scoring, curation, bucket assignment, and search-level
prose contracts.

Use `products/location_services/BUILD_OUTLINE_DRIFT_GUARD.md` for the full
build outlines behind those referenced areas. This file inventories data gaps;
it does not define the implementation sequence by itself.

## Capability Status Labels

| Label | Meaning |
|---|---|
| `AVAILABLE_NOW` | Field exists and is tested in v0.1 `LocationEvidenceRecord` |
| `AVAILABLE_WITH_WIRING` | Data is computable from existing engine functions; needs new selector, loader, or helper function |
| `NOT_COMPUTABLE` | Data does not exist anywhere in the current codebase; needs new computation |
| `FUTURE_METHOD` | Requires an entirely new astrological method not yet started |

---

## Product 1 Profile Unit: Place Resonance / Place Profile

### Evidence Already Available (AVAILABLE_NOW)

The following fields are confirmed present and tested in
`build_location_evidence_record()` v0.1:

| Field | Description |
|---|---|
| `birth_context.birth_date` | Parsed from user profile |
| `birth_context.birth_time` | Parsed; `None` in simple_mode |
| `birth_context.birth_location` | From natal payload |
| `birth_context.birth_timezone` | Birth-location timezone |
| `birth_context.birth_time_confidence` | Controlled state string |
| `birth_context.utc_instant` | ISO string, preserved exactly |
| `birth_context.julian_day` | Preserved exactly |
| `birth_context.calculation_profile` | Always `tropical_whole` in production |
| `destination_context.display_name` | Resolved or user-provided |
| `destination_context.latitude` / `.longitude` | Rounded to 4 decimals |
| `destination_context.timezone` | Resolved or user-provided |
| `destination_context.coordinate_precision` | Provenance tag, not precision measurement |
| `relocated_chart.angles` | All 5 canonical angles, full zodiac_position shape |
| `relocated_chart.house_cusps` | All 12 houses |
| `relocated_chart.house_system` | Fixed: Whole Sign |
| `relocated_chart.zodiac` | Fixed: Tropical |
| `planet_house_changes[*].id` | Stable ID per body |
| `planet_house_changes[*].body` | Canonical body name |
| `planet_house_changes[*].natal_house` | Integer 1–12 |
| `planet_house_changes[*].relocated_house` | Integer 1–12 |
| `planet_house_changes[*].house_changed` | Boolean |
| `planet_house_changes[*].natal_house_type` | angular / succedent / cadent |
| `planet_house_changes[*].relocated_house_type` | angular / succedent / cadent |
| `planet_house_changes[*].movement_type` | same_house / newly_angular / leaves_angular / house_changed / unknown |
| `relocated_angle_contacts[*].id` | Stable ID |
| `relocated_angle_contacts[*].body` | Canonical body name |
| `relocated_angle_contacts[*].angle` | Long canonical name |
| `relocated_angle_contacts[*].orb` | Degrees, float |
| `relocated_angle_contacts[*].contact_strength` | tight / moderate / wide |
| `relocated_angle_contacts[*].relocated_house_type` | angular |
| `natal_modifiers[body].condition_classification` | For core planets (Sun–Pluto) only |
| `natal_modifiers[body].overall_condition_score` | Numeric |
| `natal_modifiers[body].essential_dignity` | Full dignity profile |
| `natal_modifiers[body].accidental_dignity` | Natal angularity |
| `natal_modifiers[body].sect_condition` | in_sect / out_of_sect |
| `natal_modifiers[body].motion_condition` | Direct / retrograde |
| `natal_modifiers[body].natal_house_type` | angular / succedent / cadent |
| `natal_modifiers[body].was_natal_angular` | Boolean |
| `natal_modifiers[body].routing_tags` | List |
| `natal_modifiers[body].confidence` | Reflects actual birth-time state (fixed Round 3) |
| `natal_modifiers[body].source_standard_formula` | Audit field |
| `evidence_ranking.primary_evidence` | List of evidence IDs |
| `evidence_ranking.supporting_evidence` | List of evidence IDs |
| `evidence_ranking.contradictory_evidence` | Always empty in v0.1 |
| `evidence_ranking.speculative_or_excluded_evidence` | Four unsupported methods |
| `evidence_ranking.confidence_notes` | Non-empty when birth time is non-exact |
| `purpose_lens` | Passed through unchanged; string or None |
| `relationship_to_place` | Passed through unchanged; string or None |
| `appendix_trace.formula_version` | |
| `appendix_trace.relocated_payload_formula_version` | |
| `appendix_trace.calculation_sources` | List of function paths |
| `appendix_trace.tolerances` | Orb/band table |
| `appendix_trace.unsupported_methods` | Same as top-level |
| `appendix_trace.warnings` | Raw warning list |
| `appendix_trace.warning_summary` | Aggregated (Round 3) |
| `appendix_trace.birth_time_confidence` | Same as birth_context |
| `appendix_trace.coordinate_precision` | Same as destination_context |
| `appendix_trace.methodology` | |
| `unsupported_methods` | Flat tuple: astrocartography, local_space, parans, relocated_returns |
| `warnings` | Raw list |
| `warning_summary` | Aggregated (Round 3) |

---

### Evidence Available With Wiring (AVAILABLE_WITH_WIRING)

These items are computable from existing engine functions but require
new selector code, new helper functions, or new integration work:

| Item | What Is Needed |
|---|---|
| Relocated Ascendant ruler (sign→ruler lookup) | Narrow helper: `sign → ruler dictionary` lookup, not a full condition evaluation. Safe to compute against relocated chart. Not built in this pass. |
| House-to-domain mapping (public / private / relational / operational) | Requires content lane to author an explicit house→domain table. Once authored, engine can expose `domain_movement_type` OR selector can derive it at block-selection time from raw `natal_house` / `relocated_house` integers. The latter is recommended — see `LOCATION_EVIDENCE_RECORD_CONTRACT.md` §3. |
| Purpose-fit type (strong_fit / conditional_fit / tradeoff / low_signal / conflicted) | Requires selector logic that reads `evidence_ranking` and `purpose_lens` together. Fit-type taxonomy is `BLOCK_SCHEMA.md` Family 5 selector output. |
| Synthesis category selector (convergent_place_signature, etc.) | Requires selector that reads `evidence_ranking` and applies synthesis logic from `BLOCK_SCHEMA.md` Family 6 keys. |
| Duration-lens selector | Requires selector that reads `relationship_to_place` and maps to block keys per `BLOCK_SCHEMA.md` Family 7. |
| Batch evidence record generation (for Between Places) | Loop over destination list, call `build_location_evidence_record()` per destination, collect results. Straightforward wiring; no new computation. |
| `coordinate_precision` as provenance language | Possible if content lane defines what "user_provided" and "offline_geonamescache" mean in prose terms. This must not become an accuracy band or ±km claim. No new computation required. |

---

### Not Currently Computable (NOT_COMPUTABLE)

| Item | Why Not Computable |
|---|---|
| `contradictory_evidence` populated entries | Requires domain taxonomy to identify visibility/privacy tension, expansion/structure tension, etc. Domain taxonomy not yet authored. See `LOCATION_EVIDENCE_RECORD_CONTRACT.md` §3. |
| `domain_movement_type` engine field | Same dependency: house→domain taxonomy not authored. |
| Cross-destination evidence comparison/diff | No comparison function exists. Needed for Between Places sections 2.4 and 2.5. |
| Cross-destination purpose-fit ranking | No comparison function. Required for Between Places section 2.3. |
| Date-bounded transits to relocated angles | No relocated timing function exists. Required for Living Map. |
| Baseline-vs-weather field model | Depends on dynamic timing layer not yet built. |
| True coordinate precision measurement (±km) | `geonamescache` gives city centroids only. Neither `natal_engine.py` nor `offline_place_resolver.py` computes positional accuracy. Not a Location Services-specific gap. |
| Natal rulership links carried into relocated expression (rulership chain) | `evaluate_chart_ruler()` calls condition-bearing functions and is forbidden against relocated payload. Safe narrow version (sign→ruler lookup only) is not yet built. |
| Aspects to relocated angles | `evaluate_angularity()` is used for conjunction contacts only. Aspect contacts to relocated angles (non-conjunction aspects from natal planets to relocated angles) are not computed. |

---

### Future Method (FUTURE_METHOD)

These require entirely new astrological methods not yet started:

| Item | Method Required | Known Dependencies |
|---|---|---|
| Astrocartography planetary line generation | Planetary line geometry: compute the great-circle on Earth's surface where each planet transits a given angle (ASC, DSC, MC, IC) | None in codebase |
| Distance from destination to nearest point on each line | Distance-to-line geometry, antimeridian handling, polar handling | Requires line generation first |
| Distance band policy | Content lane must define defensible orb-equivalent distance thresholds (e.g. ≤100km tight, ≤500km moderate) | Distance calculation first; content policy decision second |
| Line cluster detection | Finding and grouping nearby lines for a region | Requires line generation and distance calculation |
| Planetary azimuths from anchor (Local Space) | Altitude/azimuth engine: compute horizon-based direction for each planet from a given location | None in codebase |
| Direction ray / great-circle path generation | From azimuth to a full directional line across Earth's surface | Requires azimuth engine |
| Cross-track distance to direction lines | Destination's lateral distance from a directional path | Requires direction ray generation |
| Parans | Simultaneous rising/setting/culminating relationships across different meridians | None in codebase; method requires dedicated implementation |
| Relocated return charts | Solar, lunar, or planetary return calculated for the relocated place | Return chart engine exists for natal; relocated variant not yet built |
| Dynamic relocated timing overlay | Date-bounded transits/progressions to relocated angles | Requires static Place Resonance baseline to be stable first |

---

## Product 2: Between Places — Gap Summary

| Need | Status |
|---|---|
| Single `LocationEvidenceRecord` per destination | `AVAILABLE_NOW` |
| Batch generation (loop over 2–5 destinations) | `AVAILABLE_WITH_WIRING` |
| Evidence comparison function | `NOT_COMPUTABLE` |
| Evidence intersection/shared-themes function | `NOT_COMPUTABLE` |
| Purpose-fit comparison across records | `NOT_COMPUTABLE` |
| Cross-destination tradeoff synthesis | `NOT_COMPUTABLE` |
| Per-destination technical appendix | `AVAILABLE_WITH_WIRING` |

---

## Product 3: World Lines Companion — Gap Summary

| Need | Status |
|---|---|
| Natal modifiers for line planets (reuse) | `AVAILABLE_WITH_WIRING` |
| Astrocartography line generation | `FUTURE_METHOD` |
| Distance-to-line calculation | `FUTURE_METHOD` |
| Distance band policy | `NOT_COMPUTABLE` (needs content decision first) |
| Line cluster detection | `FUTURE_METHOD` |
| Antimeridian / polar handling | `FUTURE_METHOD` |
| Birth-time sensitivity for line movement | `AVAILABLE_WITH_WIRING` (uses existing birth_time_confidence) |
| Map-ready geometry payload | `FUTURE_METHOD` |

---

## Product 4: Local Compass — Gap Summary

| Need | Status |
|---|---|
| Natal modifiers for directional planets (reuse) | `AVAILABLE_WITH_WIRING` |
| Planetary azimuths from anchor | `FUTURE_METHOD` |
| Direction ray generation | `FUTURE_METHOD` |
| Cross-track distance | `FUTURE_METHOD` |
| Direction group/strength policy | `NOT_COMPUTABLE` (needs content decision) |
| Altitude/azimuth convention documentation | `NOT_COMPUTABLE` (policy not defined) |

---

## Product 5: Living Map — Gap Summary

| Need | Status |
|---|---|
| Static `LocationEvidenceRecord` baseline | `AVAILABLE_NOW` |
| Date-bounded transits to relocated angles | `NOT_COMPUTABLE` |
| Transit-to-house computation for relocated houses | `NOT_COMPUTABLE` |
| Standard timing clocks (existing) | Governance-blocked as a Location Services overlay until timing policy defines what may be reused; not a Living Map implementation path by itself |
| Baseline-vs-weather field model | `NOT_COMPUTABLE` |
| Relocated return charts | `FUTURE_METHOD` |
| Dynamic astrocartography | `FUTURE_METHOD` (depends on static geometry first) |

---

## Shared Evidence Reusability

The following Place Resonance evidence fields can be reused across multiple
products without regeneration:

| Field | Reusable By |
|---|---|
| `natal_modifiers[body]` | Between Places, World Lines Companion, Local Compass, Living Map |
| `birth_context` | All products |
| `appendix_trace.birth_time_confidence` | All products |
| `appendix_trace.unsupported_methods` | All products |
| `warning_summary` | All products |

**Note:** Reuse assumes the natal payload does not change between products
for the same user chart. Claude Code should verify that batch generation
(Between Places) reuses the natal payload correctly rather than
regenerating it per destination.
