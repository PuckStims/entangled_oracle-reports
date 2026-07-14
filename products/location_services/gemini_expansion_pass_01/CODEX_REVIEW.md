# Codex Review — Gemini Expansion Pass 01

**Reviewer:** ChatGPT/Codex, local repo integration and content-boundary lead.  
**Status:** Reviewed draft. This file does not make Gemini's pass authoritative; it classifies what can be reused, corrected, or deferred.  
**Scope:** `products/location_services/gemini_expansion_pass_01/` reviewed against the current Location Services code, tests, scaffold, and content contracts.

## Current Direction Overlay

This review predates the Place Resonance Search pivot. Its caution about
building from the working Place Resonance code path still applies, but the
product role has changed:

- The existing Place Resonance implementation is now the reusable single-place
  Place Profile engine.
- Place Resonance Search is the intended flagship discovery product.
- The next production contract after profile stability is candidate catalog,
  batch profile generation, scoring, curation, and bucket assignment for Search.

## Review Summary

Gemini Pass 01 succeeded at its intended job: it created broad draft structure without modifying engine files, block scaffold files, templates, or active non-location products. The pass is useful as a planning map, but not as an implementation source of truth.

The near-term path is narrower than Gemini's full roadmap:

1. Keep the existing Place Resonance code path stable as the reusable Place
   Profile engine.
2. Build Place Resonance Search from candidate catalog, batch profile
   generation, scoring, curation, and bucket assignment.
3. Keep the Location Services block-loader/selector adapter and profile render
   path green as the evidence layer evolves.
4. Only then promote comparison, map, direction, or timing products into real
   production routing.

Between Places can follow after Place Resonance selection/rendering is stable. World Lines Companion, Local Compass, and Living Map remain planning-only until their missing methods and governance policies exist.

## Findings By Severity

### High — Timing Clocks Are Not Location-Ready

Gemini labels "standard timing clocks" for Living Map as `AVAILABLE_WITH_WIRING`. That is too optimistic for a Location Services product.

Current repo truth:

- Existing timing clocks can compute ordinary forecast/timing material.
- No date-bounded relocated-angle timing layer exists.
- No baseline-vs-weather field model exists.
- No governance rule currently says a standard timing clock can be reused as a location-timing claim.

Decision:

- Downgrade Living Map timing from `AVAILABLE_WITH_WIRING` to **governance-blocked / not computable as a location overlay**.
- Existing timing clocks may be treated as source material only, not a Living Map implementation path.
- Living Map should not become a build target until Place Resonance is stable and a separate timing-governance pass defines what "location weather" may claim.

### High — Draft Taxonomies Must Remain Unwired

Gemini proposed useful draft category sets for:

- Between Places comparison patterns;
- World Lines distance bands;
- Local Compass use modes;
- Living Map time bands;
- tradeoff mapping.

Decision:

- Keep all of these as DRAFT brainstorming.
- Do not wire any of them into engine output, selector output, tests, or required block schemas yet.
- The comparison-pattern and tradeoff sets are especially sticky; they should be reviewed by the content lane before being copied into scaffold files.

Preferred direction for tradeoffs:

```text
domain -> cost_type
```

rather than single combined labels like:

```text
visibility_with_exposure_cost
```

The two-axis version will be easier to personalize and less likely to overcommit the evidence.

### High — "Best Fit By Purpose" Sounds Too Ranking-Like

`PRODUCT_SUITE_SECTION_MAP.md` section 2.3 uses "Best Fit By Purpose" and asks "which place has the strongest evidence fit." That is close to a ranking frame.

Decision:

- Rename before implementation to **Purpose Fit By Place** or **Purpose Fit Comparison**.
- The prose job should be:

```text
How each place relates to the stated purpose, what evidence supports that relationship, and what tradeoffs appear per destination.
```

not:

```text
Which place is best.
```

### Medium — Batch Generation Is Probably Safe, But Needs A Dedicated Regression

Gemini assumes Between Places can share one natal payload across multiple destination records.

Source-grounded review:

- `build_relocated_payload()` deep-copies profile, body records, and kept aspects before returning a relocated payload.
- `compare_natal_to_relocated()` starts with a copied warnings list and does not mutate natal or relocated payloads.
- `build_location_evidence_record()` builds a relocated payload internally and has a direct no-mutation test.
- Existing tests verify:
  - `build_relocated_payload()` does not mutate natal payload.
  - `compare_natal_to_relocated()` does not mutate either payload.
  - `build_location_evidence_record()` does not mutate natal payload.

Decision:

- Keep batch record generation as `AVAILABLE_WITH_WIRING`.
- Before implementing Between Places, add a dedicated multi-destination regression:

```text
same natal_payload -> build records for 2-5 destinations -> natal_payload remains unchanged -> records do not share mutable destination-specific structures
```

### Medium — Relocated Ascendant Ruler Is Safe Only As A Pure Lookup

Gemini labels relocated Ascendant ruler as `AVAILABLE_WITH_WIRING`.

Source-grounded review:

- `formulas.standard.chart_ruler.evaluate_chart_ruler()` is not safe for relocated payload condition work because it calls condition-bearing formulas including dignity, angularity, and sect.
- A safe relocated Ascendant ruler helper is possible if it only reads the relocated Ascendant sign and looks up `TRADITIONAL_DOMICILE` / `MODERN_DOMICILE` from `formulas.standard.dignity`.

Decision:

- Keep as `AVAILABLE_WITH_WIRING` only for a pure structural helper.
- Do not call `evaluate_chart_ruler()` on a relocated payload.
- Do not compute relocated ruler condition.

### Medium — Coordinate Precision Is Provenance, Not Accuracy

Gemini treats coordinate precision as usable if content defines prose around it.

Decision:

- `coordinate_precision` is available as a provenance tag:

```text
user_provided
offline_geonamescache
```

- It is not an accuracy band and must not be rendered as "precise within N km."
- Appendix copy may say how coordinates were sourced, not how exact they are.

### Medium — Stage 1 Selector Path Needs Repo-Native Routing

Gemini proposes `engine/location_services_selector.py` as a possible selector path.

Source-grounded review:

- Existing block loading lives in `selectors/block_selector.py`.
- Block roots are registered through `config.py::REPORT_BLOCK_DIRS`.
- `location_services` is not currently registered in `REPORT_BLOCK_DIRS`.
- Existing `select_block()` returns string leaves, while Round 4 Location Services scaffold leaves are dicts with `body`, `_note`, `claim_level`, and `requires_evidence`.

Decision:

- Stage 1 should not start by putting selector logic in `engine/`.
- The smallest repo-native path is likely:

```text
config.py: add REPORT_BLOCK_DIRS["location_services"] = products/location_services/blocks/plainspeak
selectors/location_services_selector.py: load and return structured scaffold leaves
tests/test_location_services_selector.py: prove traversal and fallback behavior
```

- Engine evidence construction should stay separate from content block selection.

### Medium — Products 3-5 Are Over-Scaffolded But Useful As Vision

World Lines Companion, Local Compass, and Living Map have detailed section maps despite missing major backend methods.

Decision:

- Keep these docs as product-suite vision.
- Do not treat them as implementation backlog.
- Any file paths, evidence field names, or block families for products 3-5 are speculative until method engines exist.

## Confirmed Safe Items

- Gemini stayed inside `products/location_services/gemini_expansion_pass_01/`.
- No engine, formula, template, or active non-location product files were modified by Gemini.
- The pass clearly labels itself as draft material.
- Future methods are generally marked `FUTURE_METHOD` or `NOT_COMPUTABLE`.
- `contradictory_evidence` is correctly treated as empty in v0.1.
- The Round 4 scaffold remains TODO-only and untouched.
- The risk register is useful and should remain attached to the pass.

## Required Corrections Before Use

These do not all require immediate edits to Gemini's draft files, but they must be applied before any implementation uses those docs as instructions:

1. Rename "Best Fit By Purpose" to "Purpose Fit By Place" or equivalent.
2. Downgrade Living Map timing claims from "available with wiring" to governance-blocked/not computable for location overlay.
3. Treat `coordinate_precision` as coordinate provenance only.
4. Do not wire any DRAFT taxonomy.
5. Use repo-native selector routing, not an engine-only selector path.
6. Require a dedicated batch no-mutation test before Between Places.

## Accepted Draft Items

The following Gemini ideas are accepted as planning direction:

- Product suite should remain ordered:
  1. Place Resonance
  2. Between Places
  3. World Lines Companion
  4. Local Compass
  5. Living Map
- Place Resonance render skeleton is the next build target.
- Between Places should reuse `LocationEvidenceRecord` per destination rather than inventing a separate evidence record at first.
- Products 3-5 should remain blocked behind new method engines and policy decisions.
- Technical appendix should use `warning_summary`, not raw `warnings`, for reader-facing disclosure.

## Deferred Or Quarantined Items

Quarantine until content/method review:

- comparison pattern taxonomy;
- distance band taxonomy;
- local direction use modes;
- living map time bands;
- tradeoff taxonomy;
- house-to-domain taxonomy;
- purpose-fit taxonomy;
- contradiction taxonomy.

Quarantine until new computation exists:

- astrocartography line geometry;
- Local Space azimuth/ray geometry;
- parans;
- relocated return charts;
- dynamic timing overlays;
- date-bounded transits to relocated angles/houses.

## Next Safest Implementation Step

Build only the Stage 1 selector foundation:

```text
Goal: prove the four Round 4 Place Resonance scaffold files can be selected safely.

Work:
1. Add a Location Services block root to config.py.
2. Create a Location Services selector/adapter that returns structured leaf dicts, not only strings.
3. Support:
   - technical_appendix_blocks.json
   - relocated_angle_contact_blocks.json
   - planet_relocated_house_blocks.json
   - location_synthesis_blocks.json
4. Add focused tests for:
   - canonical angle key lookup;
   - tight/moderate/wide lookup;
   - body fallback for nodes/Lilith/asteroids;
   - house/movement lookup;
   - impossible movement fallback;
   - warning_summary lookup;
   - no non-location block roots touched;
   - no engine changes required.
```

Do not build a rendered report until this selector foundation is tested.

## Stop Conditions

Stop and regroup if any Stage 1 implementation would require:

- modifying astronomical calculations;
- running condition-bearing formulas on relocated payloads;
- writing final consumer-facing prose;
- wiring a DRAFT taxonomy;
- changing existing non-location report behavior;
- implementing unsupported methods.
