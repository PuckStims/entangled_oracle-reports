# Entangled Oracle — Multi-Clock, Asteroid-Rich Predictive Readiness Audit

Date: 2026-07-07
Method: read-only code inspection. No production files, formulas, templates, JSON block libraries, or configuration were modified. Existing audit artifacts (`ENGINE_CAPABILITY_SURFACE_AUDIT.md`, `ENGINE_CAPABILITY_SURFACE_AUDIT.json`, `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md`, `agents/PLANNED_UPDATES.md`, `agents/REVISIONS.md`, `ARCHITECTURE.md`, `METHODS.md`) were treated as prior evidence and re-verified where their claims touched this audit's scope.

Scope: assess how prepared the current codebase is to support a comprehensive, asteroid-rich, multi-clock predictive system spanning natal promise → long-clock activation → short trigger → convergence → narrow candidate window → stored evidence for retrospective validation.

---

## 1. Executive Summary

**Overall verdict.** Entangled Oracle is, today, a **transit-weather-plus-sandbox-diagnostic system with strong asteroid *natal* substrate but almost no asteroid *predictive* participation**, and no active long-clock scanners. It is *not* a multi-clock predictive platform; it is *not* a discrete-event prediction engine; but it is *architecturally closer to multi-clock readiness than a casual read of the reports suggests*, because normalization, method-family taxonomy, memory, semantic diagnostics, and epistemic confidence scaffolding are already present at the signal and window level in `engine/predictive_engine.py` — they simply have no non-transit signal source feeding them.

**Which predictive layers are present in the existing code:**

- Natal chart with all 34 declared asteroids (fully calculated, houses, aspects, retrograde flags).
- Transit event scanning: transit cycles (Mars → Pluto), whole-sign house ingresses (Jupiter → Pluto), stations (Mercury → Pluto), eclipses, plain lunations with 2° natal contact qualification, retrograde clusters, void-of-course Moon.
- Daily / weekly intra-day exact contact detection (Moon primary; slow-planet interior peaks with boundary-artifact filtering).
- A predictive engine that normalizes those transit events into `PredictiveSignal` objects with `method_family`, `event_kind`, `independence_group`, `activation_route`, `operation_profile`, `epistemic_confidence`, `angle_eligibility`.
- Daily resonance series (raw / smooth / baseline / residual, structural vs trigger split), prominence-filtered residual peaks, minimum-distance filtered windows with FSM lifecycle (`PRELUDE` → `RESIDUAL_FIELD`), episode memory, window-level semantic diagnostics (`coherence`, `polarity`, `coalition`, `counterforce`, `complexity`, `dominant_operation`, `semantic_state`).
- A stranded but complete `scan_proprietary_forecast_windows()` scanner for **asteroid → planet/angle transit contacts** (Chaos → Kassandra, Hermes → Kassandra, Aletheia → Sun, BML → each angle, Medea/Kaali → Mars, Destinn/Karma/Chiron → DSC, TrueNode → Destinn) that is defined and callable but *never called* by the active pipeline.
- A convergence detector for existing transit events (`_detect_and_frame_convergences()` in `generate.py`), but it currently ships synthesized convergence objects with `combined_intensity_score = 0.0` — structural overlay, not intensity-ranked evidence.
- Governance registry that classifies every asteroid's `eligible_report_types` as `("soul_ecosystem", "predictive_sandbox")` only — asteroid material is deliberately gated *out* of `year_ahead`, `personal_forecast`, `daily_horoscope`, and `weekly_horoscope`.

**Which clocks are missing or only scaffolded:**

- **Secondary progressions:** absent (taxonomy hook only).
- **Solar Arc directions:** absent (taxonomy hook only).
- **Primary directions:** absent.
- **Solar / lunar / planetary returns:** absent (event_type "return" is normalized in taxonomy; no scanner).
- **Annual profections:** absent.
- **Zodiacal Releasing:** absent.
- **Firdaria / other time-lord systems:** absent.
- **Arabic Parts / Hellenistic lots (Fortune, Spirit, etc.):** absent.

**Are the 34 asteroids first-class in the pipeline?**

- **Yes**, at the natal-substrate layer (all 34 stored, houses assigned, joined into the aspect matrix, indexed by proprietary formulas KVQ/DFIS/CATALYST/MKI/RWI/AHL/NGE).
- **No**, at the forecasting layer. Of the 34 declared asteroids, exactly **8** (`Kassandra`, `Aletheia`, `Destinn`, `Karma`, `Kaali`, `Medea`, `Hermes`, `Chaos`) are surfaced as natal *transit targets* in `PROPRIETARY_ASTEROID_TARGETS`, and only through the stranded `scan_proprietary_forecast_windows()` scanner that never runs in production or sandbox. The predictive engine reserves `_TARGET_RELEVANCE` slots for those same 8 (relevance 0.70 – 0.85) so signals *would* be first-class if produced. The other 26 asteroids have no predictive-layer participation at all beyond natal indexing.

**Top three latent capabilities already available:**

1. **`scan_proprietary_forecast_windows()` is complete, tested-shaped, and produces events that match the standard event contract** (`event_type: "proprietary_transit"`, aspect, natal_target, orb, entry/peak/leave datetimes, score, intensity_label). The predictive engine's `_normalize_method_family` already maps `"proprietary_transit"` → `TRANSIT` family, and its `_TARGET_RELEVANCE` already scores those 8 asteroids. Wiring one call site into `compute_year_ahead_events()` would put asteroid transits into the active predictive signal stream without any new astronomy code.
2. **A production-grade signal / window normalization layer**, including `operation_profile` (six-axis: stabilize / amplify / activate / disrupt / dissolve / reveal), aspect-bias operator, target-substrate shaping, and FSM-based lifecycle continuity. This is designed to *absorb* new clocks without redesign — only a new scanner producing dated events per method family is required.
3. **Whole-window diagnostics preserving separation of `intensity`, `coherence`, `memory`, `gradient`, `polarity`, `coalition`, `counterforce`, `complexity`, `dominant_operation`, and `semantic_state`**, plus per-signal `epistemic_confidence`, `confidence_components`, `angle_eligibility`. This is precisely the shape a convergence-with-provenance layer needs, and it already exists — just not yet used for cross-method convergence because there is only one method.

**Top three architectural gaps blocking discrete-event candidate work:**

1. **No long-clock scanners.** Progressions, Solar Arc, returns, profections, and ZR are taxonomy-only. Without at least one non-transit event source, "multi-clock convergence" cannot mean more than "multiple transit sub-types," and the anti-double-counting rules (station and ingress do not create a second transit-clock vote) are already enforced *inside* the transit family. Convergence with method-source provenance is architecturally supported but has nothing to converge across.
2. **Daily provenance and rejected-peak evidence are dropped.** `_build_daily_series` collapses per-day signal contributions into scalar totals, and `_detect_windows` records rejected peak *counts* in `debug` but not rejected indices, prominences, or which signals drove them. This is the specific loss point that blocks retrospective validation "which signals actually caused this spike on this date, and which candidate spikes were rejected and why."
3. **No first-class validation export.** `_write_report_manifest()` records methodology, versions, active modules, warnings, and report-surface trace, but omits `predictive_results` entirely (signals, daily series, windows, debug). `tools/extract_sandbox_ledger.py` scrapes rendered HTML from `predictive_sandbox`; consumer reports have no predictive appendix at all. Without a durable machine-readable record of what the engine calculated *before* an event, retrospective validation of narrow event windows is not possible.

**Overhaul or incremental?**

- **Incremental.** The engine mechanics required for multi-clock convergence and asteroid-rich predictive work are, in most cases, already present in `engine/predictive_engine.py`. The delta is (a) wiring the existing `scan_proprietary_forecast_windows()` scanner and normalizing its output, (b) building one or two additional astronomical event scanners (returns first, then Solar Arc, then progressions per the existing plan of record), (c) preserving daily signal provenance and rejected-peak diagnostics, and (d) writing a validation-grade sidecar. None of these requires redesigning the natal engine, the transit engine, the report-surface bundle, or the report generation flow.

Language calibrated for the source-of-truth agent notes: this audit does **not** claim confidence has become interval-sampled; it does **not** claim any long clock is implemented; it does **not** claim asteroid transit scanning is currently on for any report type; and it does **not** claim discrete-event windows exist as first-class outputs.

---

## 2. Predictive Architecture Map

Pipeline as actually implemented (files, functions, inputs, outputs, downstream consumers, debug/testing surfaces, and identified loss points).

### Stage: Birth data → natal payload

- **Files:** `generate.py` (CLI, arg parsing, dispatch), `engine/natal_engine.py` (`generate_payload()`), `engine/offline_place_resolver.py`.
- **Inputs:** name, date, time, location, optional `--simple`, optional `--report-date`.
- **Outputs:** natal payload dict with `user_profile` (incl. `birth_time_state`, `methodology`, JD), `angles` (Ascendant, Midheaven, Descendant, Imum_Coeli, Vertex — Vertex gets its own house), `houses` (12 whole-sign cusps), `standard_planets` (Sun … Pluto, Chiron, North_Node, South_Node, Lilith_BML), `custom_asteroids` (34 named asteroids or a graceful `"Calculation failed: …"` string per asteroid on ephemeris miss), and `aspects` (planet+asteroid+ASC/MC/Vertex joint aspect matrix at scan orb 10.0°). See `engine/natal_engine.py:459-634`.
- **Downstream consumers:** every formula layer (standard, established niche, proprietary), variable resolver, transit engine, predictive engine, all report contexts, and manifest.
- **Debug/testing:** `test_offline_location.py`, `tests/test_d1_context_preparation.py`, `tests/test_confidence.py`, `tests/test_methodology_profiles.py`.
- **Loss points:** none at natal construction. All 34 asteroids get position and house data. `custom_asteroids` failure per body is per-body isolated, not global.

### Stage: Standard + proprietary formula indexes

- **Files:** `formulas/standard_indexes.py`, `formulas/standard/` (aspect_architecture, angularity, chart_ruler, chart_structure, confidence, dignity, forecast_activation, house_emphasis, method_registry, methodology_profiles, named_configurations, natal_convergence, normalization, planetary_condition, planetary_prominence, rulership_network, sect), `formulas/proprietary_indexes.py`, `formulas/report_surface.py`, `formulas/governance_registry.py`, `formulas/established_niche.py`.
- **Inputs:** natal payload, report type.
- **Outputs:** `index_results` (KVQ, MKI, RWI, DFIS, Catalyst, AHL, NGE — each a scored dimension with driver/facet metadata), `standard_report_bundle` (layered chart structure, dignity, sect, angularity, chart ruler, etc.), aspect trace, layer-status metadata.
- **Downstream consumers:** variable resolver, report context builders, manifest.
- **Debug/testing:** `tests/test_standard_natal_architecture_phase2.py`, `test_established_niche_governance_phase3.py`, `test_forecast_engine_phase4.py`, `test_standard_report_wiring_phase5.py`, `test_content_phase6.py`, `test_phase7_rendering_system.py`, `test_phase8_quality_assurance.py`, `test_phase9_operational_readiness.py`.
- **Loss points:** `_leading_index()` in the predictive engine falls back to natal EAS dimension scores when no registry target matches, which is fine, but `NGE` and `AHL` are commented out of `PREDICTIVE_COMPONENT_REGISTRY` (`engine/predictive_engine.py:242-244`) — their predictive routing is deferred despite being active as natal indexes.

### Stage: Report window resolution

- **Files:** `generate.py` (`_report_window()`, `_align_to_week_start()`).
- **Inputs:** `report_type`, `report_start` (default `datetime.now(UTC)` if `--report-date` not passed).
- **Outputs:** `(report_start, report_end)` — 1 year for `year_ahead`, 90 days for `personal_forecast`, 1 day for `horoscope`, Monday-Friday for `weekly_horoscope`, 1 year for `predictive_sandbox`.
- **Loss point (known):** the daily horoscope path uses `datetime.now()` inside the variable resolver rather than the requested report window; documented in `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md` §7.

### Stage: Forecast event scanning (transit family)

- **File:** `engine/transit_engine.py`.
- **Active scanners:**
  - `scan_transit_windows()` — Mars/Jupiter/Saturn/Uranus/Neptune/Pluto → 10 standard planets, ASC, MC, Vertex (Mars restricted to Sun/Moon/ASC/MC/Vertex). Three-phase: coarse 12h grid, bisection refinement to 0.01°, 120-day cycle merge. Emits `event_type: "transit"` events with entry / peak / leave datetimes, contacts, activation route, priority, score, cycle_id. Uses `_natal_targets()` (planets + angles only, **no asteroids**).
  - `scan_house_ingresses()` — Jupiter → Pluto whole-sign ingresses, keyed by house destination.
  - `scan_stations()` — Mercury → Pluto retrograde and direct stations near natal targets.
  - `scan_eclipses()` — Swiss Ephemeris eclipse hits with 2° natal-contact match against `ECLIPSE_TARGET_KEYS` (planets + ASC/MC/Vertex only).
  - `scan_lunations()` — new/full moons with 2° natal contact against `ECLIPSE_TARGET_KEYS`, deduplicated against eclipse dates.
  - `scan_proprietary_forecast_windows()` (**defined at line 951, never called elsewhere**) — asteroid-aware transit scanner with 3 formula groups (DISRUPTION, SOVEREIGNTY, CATALYST). Uses `_proprietary_targets()` (planets + angles + 8 asteroids). Produces `event_type: "proprietary_transit"`. Isolated from the active pipeline.
  - `detect_retrograde_clusters()` — 8-planet daily sweep, 2+ simultaneous retrograde tiers.
  - `detect_void_of_course_windows()` — single-pass Moon void with 6h/day-crossing tiers.
  - `compute_daily_activation_transits()` — same-day scan, graduated orbs (0.15° Pluto → 1.0° Sun/Mercury/Venus/Mars).
  - `compute_daily_timeline()` — Moon-primary intra-day peaks over an arbitrary date range, boundary-artifact filtered, optionally including slow-planet interior peaks. Used by daily and weekly reports.
  - `compute_current_transits()` — snapshot form, used by the legacy report.
- **Aggregation:** `compute_year_ahead_events()` (`engine/transit_engine.py:2267-2343`) calls exactly `scan_transit_windows`, `scan_house_ingresses`, `scan_stations`, `scan_eclipses`, `scan_lunations` (in that order), links related events, and returns `{transits, ingresses, stations, eclipses, lunations, all_events}`. **`scan_proprietary_forecast_windows` is not part of this aggregation.**
- **Downstream consumers:** `generate.py` context builders for `year_ahead` and `personal_forecast`; `engine/predictive_engine._collect_transit_signals()`; `engine/temporal_river.py` (a separate visualization surface — see below).
- **Debug/testing:** `tests/test_transit_cycles.py`, `test_forecast_engine_phase4.py`, `test_daily_horoscope_activation.py`, `test_year_ahead_month_continuity.py`, `test_year_ahead_raw_cycle_ledger.py`, `test_year_ahead_turning_point_timeline.py`, `test_prominence.py`.
- **Loss points:**
  1. Proprietary asteroid scanner is stranded — real evidence loss for every asteroid transit.
  2. Lunation and eclipse targets are hard-coded to `ECLIPSE_TARGET_KEYS` (planets + ASC/MC/Vertex only), so a Moon-conjoins-natal-Kassandra lunation is never emitted.
  3. Ingress scanner covers only Jupiter → Pluto; Mars/Venus/Mercury/Sun ingresses are not part of the timeline.

### Stage: Predictive signal normalization

- **File:** `engine/predictive_engine.py`.
- **Function:** `_collect_transit_signals()` (line 336) → `_event_to_signal()` (line 366).
- **Inputs:** `compute_year_ahead_events(all_events)`, `birth_time_status`.
- **Per-signal fields produced:**
  - Identification / lineage: `signal_id`, `method_family` (TRANSIT / LUNATION / RETURN / PROGRESSION / SOLAR_ARC / UNKNOWN), `event_kind`, `independence_group`, `activation_route`, `source_event_type`, `source_body`, `target_body`, `aspect`, `orb`, `allowed_orb`.
  - Strength: `exactness`, `event_weight`, `target_relevance`, `trigger_strength`, `signal_strength` (with structural/theme modifiers), `structural_importance`, `theme_convergence`.
  - Sequence: `routing_state`, `pass_sequence`, `cycle_id`, `contact_count`, `multiple_exact_passes`, `start_date`, `peak_date`, `end_date`.
  - Semantic: `operation_profile` (6-axis), `operation_basis` (source × substrate × aspect × method breakdown), `dominant_operation`.
  - Epistemic: `epistemic_confidence`, `confidence_components` (`exactness_support`, `angle_support`, `calculation_integrity`, `target_uncertainty`), `confidence_state`, `angle_eligibility`.
- **Downstream consumers:** `_build_daily_series` (aggregation), `_detect_windows` (window construction), sandbox context builder in `generate.py`.
- **Loss points:** signals are held in memory during `compute_predictive_windows()` and returned in the result dict. They are then dropped by every consumer template except `products/predictive_sandbox/templates/predictive_sandbox.html`.

### Stage: Daily resonance series

- **Function:** `_build_daily_series()` (line 464).
- **Outputs per date:** `raw_score`, `smooth_score` (7d MA), `baseline_score` (35d MA), `residual_score` (smooth − baseline), `structural_raw` (slow bodies only), `trigger_raw` (fast bodies only).
- **Loss point (critical for validation):** per-day contributing signal IDs are *not* stored. To reconstruct which signals drove a given day, one must re-scan the signal list for overlap dates — this is a schema hole in an otherwise clean design.

### Stage: Window detection and semantic aggregation

- **Function:** `_detect_windows()` (line 555), `_window_memory()`, `_window_semantic_metrics()`.
- **Algorithm:** residual local maxima → prominence filter (`_MIN_PROMINENCE = 0.05`) → minimum-distance filter (`_MIN_PEAK_DISTANCE = 14`) → residual zero-crossing / valley split for boundaries → FSM lifecycle assignment → semantic aggregation.
- **Window fields:** `window_id`, `start_date`, `peak_date`, `end_date`, `local_peak_intensity`, `structural_field_intensity`, `total_intensity`, `intensity` (backward-compat alias), `prominence`, `gradient` (`rising` / `plateau` / `releasing`), `leading_index`, `active_signals`, `active_slow_chapter_signals`, `active_fast_trigger_signals`, `coherence`, `semantic_profile`, `dominant_operation`, `semantic_state`, `semantic_diagnostics` (`polarity`, `coalition`, `counterforce`, `complexity`), `memory`, `memory_state` (`activation_key`, `pass_state`, `lifecycle_route`, episode counts), `interpretive_tags`.
- **Downstream consumers:** `_build_predictive_sandbox_context()` in `generate.py` (only). Templates for `year_ahead` and `personal_forecast` receive `predictive_results` in context but *do not render it*.
- **Loss points:**
  - Rejected peak indices / prominences not preserved (only counts in `debug`).
  - Structural baseline never becomes its own window type; only residual peaks become windows.
  - `_MIN_PEAK_DISTANCE = 14` structurally excludes sub-2-week windows.

### Stage: Method convergence

- **Function:** `_detect_and_frame_convergences()` in `generate.py` (active at ~line 6966+; legacy dead form at 6842-6966).
- **Inputs:** the transit event list + convergence blocks.
- **Outputs:** synthesized convergence event objects with `combined_intensity_score = 0.0`, framed as structural overlays.
- **Consumers:** Year Ahead context, convergence block routing.
- **Assessment:** the convergence detector operates on *transit sub-types* (transit / ingress / station / eclipse / lunation) within a single method family. It is not a multi-method convergence layer. Method-source provenance is preserved at the signal level; it is not aggregated into convergence scoring.

### Stage: Report context, template render, manifest

- **Files:** `generate.py` (context builders, template map, manifest writer), `products/<report>/templates/`, `products/<report>/blocks/`.
- **Outputs per generated report:** HTML file + `.manifest.json` sidecar with `report_type`, `report_version`, active modules, methodology, warnings, report-surface trace, and querent PII (this is the local-tenancy manifest, not partner-safe).
- **Loss points:**
  - Manifest omits `predictive_results` (signals, daily series, windows, debug).
  - Manifest omits the raw event timeline (`all_events`) that `compute_year_ahead_events()` returned.
  - `predictive_results` is placed into context for `year_ahead` and `personal_forecast` but no template block renders it.

### Stage: Debug and validation tooling

- **Files:** `products/predictive_sandbox/templates/predictive_sandbox.html:346-423` (debug rows), `tools/extract_sandbox_ledger.py` (scrapes rendered HTML → CSV), `tests/test_predictive_engine.py`, `tests/test_prominence.py`, `tests/test_transit_cycles.py`.
- **Loss point:** the only validation "export" for predictive windows is CSV-scraped from rendered HTML; no first-class raw JSON export exists.

### Stage: Visualization surfaces (adjacent, not on the predictive-report path)

- `engine/temporal_river.py` and `engine/constellation_mesh.py` provide alternate diagnostic renderings. `scripts/test_temporal_river_from_birth.py` is a standalone driver. These are engineering-facing.
- `products/cosmic_weather/` and `products/sun_sign_horoscope/` are newer tooling-first products (uncommitted; visible in `git status`). They do not currently participate in the multi-clock predictive pipeline.

---

## 3. Asteroid Integration Overview

All 34 asteroids are declared in `engine/natal_engine.py:76-120` (`ASTEROID_DICTIONARY`). Each is astronomically computed via Swiss Ephemeris body ID `10000 + catalog_number` (except where the catalog number ≥ 10000, in which case the direct catalog number is used — e.g. Sirene 11009, Chaos 29521, Hermes 79230, DNA 65555). Each is joined into the natal aspect matrix (`master_payload["aspects"]`) with a 10° scan orb. Each is registered in `formulas/governance_registry.py:187-238` with `eligible_report_types=("soul_ecosystem", "predictive_sandbox")` and `default_visibility="technical_reference"`.

**Legend for status column:**

- **Natal-only, indexed** — natal position stored, joined into aspect matrix, referenced by ≥1 proprietary formula index; no predictive-layer participation.
- **Natal + proprietary transit target** — natal-only *plus* named as a natal target in `_proprietary_targets()` and receives predictive `_TARGET_RELEVANCE` weighting; usable by a stranded proprietary transit scanner.
- **Natal + proprietary transit source** — natal-only *plus* named as a *transiting* body in `PROPRIETARY_FORMULA_CONFIG` (Chaos, Hermes, Aletheia, Medea, Kaali, Karma, Destinn) or as a computed natal + BML-body (Lilith_BML lives in `standard_planets`, not `custom_asteroids`, and is not one of the 34 asteroids counted below).

"Aspects Calculated" refers to the natal aspect matrix. "Eligible in Predictive/Transit" refers to whether the predictive engine has a scoring path that includes this body if a signal were produced.

| # | Asteroid | Ephemeris ID | Natal Stored | House | Natal Aspects | Predictive Target Relevance | Proprietary Transit Target | Proprietary Transit Source | Used in Proprietary Indexes | Consumer Report Surface | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Sirene | 11009 | Yes | Yes | Yes | No | No | No | NGE, MCQ (dead), SIREN (dead), MAGNETIC (dead) | soul_ecosystem, predictive_sandbox (governance) | Natal-only, indexed | `natal_engine.py:77`, `governance_registry.py:188` |
| 2 | Aphrodite | 11388 | Yes | Yes | Yes | No | No | No | NGE, SIREN (dead), MAGNETIC (dead) | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:78`, `governance_registry.py:189` |
| 3 | Apollo | 11862 | Yes | Yes | Yes | No | No | No | RWI, NGE, MCQ (dead) | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:79`, `governance_registry.py:190` |
| 4 | Kassandra | 10114 | Yes | Yes | Yes | **0.85** | **Yes** (Chaos-conj, Hermes-conj) | No | KVQ (primary driver) | soul_ecosystem, predictive_sandbox | Natal + proprietary target (unwired) | `natal_engine.py:81`, `predictive_engine.py:97`, `transit_engine.py:860,903-904`, `governance_registry.py:191` |
| 5 | Karma | 13811 | Yes | Yes | Yes | **0.80** | No | **Yes** (Karma-conj DSC) | CATALYST | soul_ecosystem, predictive_sandbox | Natal + proprietary source (unwired) | `natal_engine.py:82`, `predictive_engine.py:100`, `transit_engine.py:926`, `governance_registry.py:192` |
| 6 | Destinn | 16583 | Yes | Yes | Yes | **0.80** | **Yes** (TrueNode-conj) | **Yes** (Destinn-conj DSC) | CATALYST, NGE | soul_ecosystem, predictive_sandbox | Natal + proprietary source+target (unwired) | `natal_engine.py:83`, `predictive_engine.py:99`, `transit_engine.py:925,928`, `governance_registry.py:193` |
| 7 | Mnemosyne | 10057 | Yes | Yes | Yes | No | No | No | MKI | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:85`, `governance_registry.py:194` |
| 8 | Atlantis | 11198 | Yes | Yes | Yes | No | No | No | MKI | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:86`, `governance_registry.py:195` |
| 9 | Sophia | 10251 | Yes | Yes | Yes | No | No | No | MKI | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:87`, `governance_registry.py:196` |
| 10 | Arachne | 10407 | Yes | Yes | Yes | No | No | No | RWI | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:89`, `governance_registry.py:197` |
| 11 | Chaos | 29521 | Yes | Yes | Yes | **0.70** | No | **Yes** (Chaos-conj Kassandra) | RWI | soul_ecosystem, predictive_sandbox | Natal + proprietary source (unwired) | `natal_engine.py:90`, `predictive_engine.py:104`, `transit_engine.py:903`, `governance_registry.py:198` |
| 12 | Hermes | 79230 | Yes | Yes | Yes | **0.70** | No | **Yes** (Hermes-conj Kassandra) | MKI, RWI, CATALYST | soul_ecosystem, predictive_sandbox | Natal + proprietary source (unwired) | `natal_engine.py:91`, `predictive_engine.py:103`, `transit_engine.py:904`, `governance_registry.py:199` |
| 13 | Themis | 10024 | Yes | Yes | Yes | No | No | No | RWI, NGE, MCQ (dead) | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:93`, `governance_registry.py:200`, `proprietary_indexes.py:919` (Themis→Destinn aspect used inside CATALYST) |
| 14 | Euterpe | 10027 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:94`, `governance_registry.py:201` |
| 15 | Urania | 10030 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:95`, `governance_registry.py:202` |
| 16 | Polyhymnia | 10033 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:96`, `governance_registry.py:203` |
| 17 | Circe | 10034 | Yes | Yes | Yes | No | No | No | DFIS | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:97`, `governance_registry.py:204` |
| 18 | Isis | 10042 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:98`, `governance_registry.py:205` |
| 19 | Melete | 10056 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:99`, `governance_registry.py:206` |
| 20 | Sappho | 10080 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:101`, `governance_registry.py:207` |
| 21 | Terpsichore | 10081 | Yes | Yes | Yes | No | No | No | NGE | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:102`, `governance_registry.py:208` |
| 22 | Minerva | 10093 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:103`, `governance_registry.py:209` |
| 23 | Hekate | 10100 | Yes | Yes | Yes | No | No | No | DFIS | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:104`, `governance_registry.py:210` |
| 24 | Medea | 10212 | Yes | Yes | Yes | **0.75** | No | **Yes** (Medea → Mars) | DFIS | soul_ecosystem, predictive_sandbox | Natal + proprietary source (unwired) | `natal_engine.py:106`, `predictive_engine.py:102`, `transit_engine.py:917`, `governance_registry.py:211` |
| 25 | Aletheia | 10259 | Yes | Yes | Yes | **0.80** | No | **Yes** (Aletheia → Sun) | none | soul_ecosystem, predictive_sandbox | Natal + proprietary source (unwired) | `natal_engine.py:107`, `predictive_engine.py:98`, `transit_engine.py:905`, `governance_registry.py:212` |
| 26 | Industria | 10389 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:109`, `governance_registry.py:213` |
| 27 | Alma | 10390 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:110`, `governance_registry.py:214` |
| 28 | Moirai | 10638 | Yes | Yes | Yes | No | No | No | MCQ (dead), NGE | soul_ecosystem, predictive_sandbox | Natal-only, indexed (partially dead) | `natal_engine.py:111`, `governance_registry.py:215` |
| 29 | Lilith_Asteroid | 11181 | Yes | Yes | Yes | No | No | No | none (deliberately distinct from BML) | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:113`, `governance_registry.py:131` |
| 30 | Anubis | 11912 | Yes | Yes | Yes | No | No | No | AHL | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:114`, `governance_registry.py:216` |
| 31 | Kaali | 14227 | Yes | Yes | Yes | **0.75** | No | **Yes** (Kaali → Mars) | DFIS | soul_ecosystem, predictive_sandbox | Natal + proprietary source (unwired) | `natal_engine.py:116`, `predictive_engine.py:101`, `transit_engine.py:918`, `governance_registry.py:217` |
| 32 | Child | 14580 | Yes | Yes | Yes | No | No | No | AHL | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:117`, `governance_registry.py:218` |
| 33 | Angel | 21911 | Yes | Yes | Yes | No | No | No | none | soul_ecosystem, predictive_sandbox | Natal-only, no downstream use | `natal_engine.py:118`, `governance_registry.py:219` |
| 34 | DNA | 65555 | Yes | Yes | Yes | No | No | No | AHL | soul_ecosystem, predictive_sandbox | Natal-only, indexed | `natal_engine.py:119`, `governance_registry.py:220` |

**Are asteroids handled differently than planets or points?**

Yes, in three concrete ways:

1. **Payload placement.** Asteroids live in `custom_asteroids`, planets in `standard_planets`, angles in `angles`. Downstream code has to know to check `custom_asteroids` explicitly. `selectors/utils.py:33-46` provides a `body_data()` helper that transparently searches both dicts.
2. **Governance visibility.** Every asteroid's `eligible_report_types` in the registry is `("soul_ecosystem", "predictive_sandbox")` only. `report_surface.py`'s layer rules gate them out of `year_ahead`, `personal_forecast`, `daily_horoscope`, `weekly_horoscope`. This is a deliberate policy, not a bug.
3. **Forecast eligibility.** `_natal_targets()` in the transit engine returns only planets + angles. `_proprietary_targets()` extends it with the 8 named proprietary asteroids. No scanner uses `_proprietary_targets()` in the aggregation flow.

**Are their parameters explicit?**

Partially. Per-asteroid orb, per-asteroid weight, per-asteroid role are declared **only** for those in `PROPRIETARY_FORMULA_CONFIG` (each formula group has one shared `orb`, and each trigger has a per-line `weight`). The remaining 26 asteroids have no forecasting parameters at all. `_TARGET_RELEVANCE` in the predictive engine assigns 0.85 / 0.80 / 0.75 / 0.70 to 8 asteroids and nothing to the other 26.

**Are their signals preserved after aggregation?**

Not at the daily-series level. Once signals feed `_build_daily_series()`, the per-day scalar totals do not carry per-asteroid provenance. Windows retain `active_signals` as a list of signal IDs, so at the window layer you *can* re-look-up any asteroid contribution — but only if the signal was actually produced, which today it wouldn't be.

**Can individual asteroids be linked as causal factors in forecasts?**

Structurally yes, but only for the 8 asteroids listed above, and only if `scan_proprietary_forecast_windows()` were wired in. All 34 asteroid *natal* positions can be traced through the aspect matrix and proprietary indexes.

---

## 4. Clock System Inventory

Clocks are evaluated independently. "Asteroid-Compatible" means: does the code path treat asteroid natal targets or asteroid sources as valid participants?

| Clock / Method | Calculation Active? | Inputs | Temporal Scale | Output Type | Asteroid-Compatible? | Used in Ranking? | Used in Convergence? | Used in Reports? | Validation-Ready? | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Transit cycles (natal transits) | Yes | natal targets (planets + ASC/MC/Vertex), transit planets (Mars → Pluto), orb tables, activation profile | months to years | refined cycle events with entry/peak/leave, contacts, score, duration | **No** (no asteroid targets, no asteroid sources) | Yes (transit score, monthly arc, personal forecast themes) | Yes (structural overlay) | Yes (year_ahead, personal_forecast, weekly_horoscope, daily_horoscope) | Partial (raw cycle ledger rendered; not manifested as validation JSON) | Fully operational | `transit_engine.py:1452-1578` |
| Whole-sign house ingresses | Yes | Jupiter → Pluto ingress moments, natal ASC-derived house map | months | ingress event | No | Yes | Yes (participates as an event kind) | Yes (year_ahead ledger, personal_forecast) | Partial | Fully operational | `transit_engine.py:1584+` |
| Planetary stations | Yes | Mercury → Pluto speed sign changes | day-precision | station event | No | Yes | Yes | Yes | Partial | Fully operational | `transit_engine.py:1681+` |
| Eclipses | Yes | Swiss Ephemeris eclipse events, natal contacts (2° via ECLIPSE_TARGET_KEYS) | discrete events | eclipse event | No (target list is planets + ASC/MC/Vertex only) | Yes (with same-date deduplication vs plain lunation) | Yes | Yes | Partial | Fully operational | `transit_engine.py:2015+` |
| Plain lunations (with natal contact qualification) | Yes | new/full moons, 2° natal contact via ECLIPSE_TARGET_KEYS, eclipse-date suppression | discrete events | lunation event | No (same target list as eclipses) | Yes | Yes | Yes | Partial | Fully operational | `transit_engine.py:2176-2263` |
| Retrograde clusters | Yes | 8-planet daily sweep | multi-day tiers | cluster event | No | Yes (climate) | No | Yes (personal_forecast, year_ahead climate) | No | Fully operational | `transit_engine.py:1803+` |
| Void-of-course Moon | Yes | Moon aspect scan | hours to a day | VOC window | No | Yes (climate) | No | Yes (personal_forecast, daily_horoscope planning) | No | Fully operational | `transit_engine.py:1907+` |
| Same-day activation | Yes | 9 planets (excl. Moon), graduated orbs 0.15–1.0° | intra-day | scored contact | No | Yes (daily horoscope selection) | No | Yes (daily_horoscope activation) | No | Fully operational | `transit_engine.py:1177-1250` |
| Daily / weekly exact-contact timeline | Yes | Moon-primary + slow-planet interior peaks; boundary-artifact filter | intra-day | exact contact moments | No | Yes | No | Yes (daily_horoscope, weekly_horoscope) | Partial | Fully operational | `transit_engine.py:1297-1390` |
| Proprietary forecast windows (asteroid-aware transit) | **Function present, not called** | 8 asteroid natal targets + planets + angles; asteroid + BML + Chiron + North_Node sources | months | proprietary_transit event matching standard contract | **Yes** (only clock where asteroids participate as first-class transit targets and transiting sources) | No (not aggregated) | No (not aggregated) | No | No | **Implemented but hidden / inactive** | `transit_engine.py:951-1049` |
| Convergence detector (transit sub-type overlay) | Yes | transit events (all sub-types), convergence blocks | overlay | synthesized event (score 0.0) | No (inherits transit target scope) | No (not intensity-ranked) | Yes (structural overlay only) | Yes (year_ahead) | Partial | Fully operational as overlay; not a multi-method convergence layer | `generate.py:6966+`; legacy dead form at 6842-6966 |
| Predictive residual-window detector | Yes | transit-derived predictive signals; residual peaks with prominence + distance filter | ~2–8 weeks | window with FSM lifecycle, semantic profile, memory | Yes in principle (respects `_TARGET_RELEVANCE`) — but sees no asteroid signals today | No (sandbox-only) | No | Only in predictive_sandbox | Partial (sandbox HTML only) | Fully operational for the transit-clock only | `predictive_engine.py:555-689` |
| Secondary progressions | No | — | — | — | — | — | — | — | — | Not implemented (taxonomy hook only) | `predictive_engine.py:125,179,883-884`; no scanner |
| Solar Arc directions | No | — | — | — | — | — | — | — | — | Not implemented (taxonomy hook only) | `predictive_engine.py:126,180,885-886`; no scanner |
| Primary directions | No | — | — | — | — | — | — | — | — | Not implemented | grep returned no matches |
| Solar returns | No | — | — | — | — | — | — | — | — | Not implemented (`RETURN` taxonomy hook only) | `predictive_engine.py:124,178,881-882` |
| Lunar returns | No | — | — | — | — | — | — | — | — | Not implemented | as above |
| Planetary returns (Jupiter, Saturn) | No | — | — | — | — | — | — | — | — | Not implemented | as above |
| Annual profections | No | — | — | — | — | — | — | — | — | Not present at all | grep returned no matches in engine/formulas/selectors |
| Zodiacal Releasing | No | — | — | — | — | — | — | — | — | Not present at all | grep returned no matches |
| Firdaria / other time-lord systems | No | — | — | — | — | — | — | — | — | Not present at all | grep returned no matches |
| Arabic Parts / Hellenistic lots | No | — | — | — | — | — | — | — | — | Not present at all | no `Lot_of` / `Part_of` / `Spirit_lot` / `Fortune_lot` in engine or formulas |
| Ingress points (beyond Jupiter → Pluto) | No | — | — | — | — | — | — | — | — | Not present (ingress scanner covers only outer planets) | `transit_engine.py:86-92` |
| Retrograde cycles (as first-class multi-station events) | Partial | station events with `pass_sequence` metadata; retrograde cluster detector | months | station + cluster events | No | Yes | No | Yes | Partial | Partially scaffolded — station events carry cycle metadata but there is no first-class "retrograde cycle" object | `transit_engine.py:1681+`, activation profile `pass_sequence` |
| Proprietary / custom clocks (Disruption / Sovereignty / Catalyst formula groups) | **Function present, not called** | as `scan_proprietary_forecast_windows` | months | proprietary_transit event | Yes | No | No | No | No | **Implemented but hidden / inactive** | `transit_engine.py:896-1049` |

**Categorization summary.**

- **Fully operational and active:** transit cycles, ingresses, stations, eclipses, lunations, retrograde clusters, void-of-course, same-day activation, daily/weekly timeline, convergence overlay, predictive residual windows.
- **Implemented but hidden / inactive:** `scan_proprietary_forecast_windows()` (asteroid-aware); `_detect_and_frame_convergences_legacy_dead()` (superseded).
- **Partially scaffolded:** retrograde cycles as first-class multi-station events; predictive method families beyond TRANSIT (LUNATION is active as a *subtype* under TRANSIT convergence).
- **Only described in configuration or taxonomy:** RETURN, PROGRESSION, SOLAR_ARC, UNKNOWN clocks — recognized by `_normalize_method_family()`, receive `_METHOD_OPERATION_MULTIPLIER` values, receive `_METHOD_WEIGHT_BY_GROUP` values — but no event source produces events of these types.
- **Planned but not implemented:** Solar Arc sandbox macro; limited secondary progressions (Sun/Moon/ASC/MC); exact returns per `agents/PLANNED_UPDATES.md`.
- **Not present at all:** primary directions, profections, zodiacal releasing, firdaria, other time-lord methods, Arabic Parts / lots.

---

## 5. Natal Promise and Topic-Relevance

**Does the system determine relevant natal houses for forecasts?**

Partially. Forecast events carry `natal_house` (the target's house), `natal_target_display` ("your Sun in the 5th house"), and — for ingresses — the destination house. Personal Forecast groups events into themes with anchors chosen from highest-scoring theme events; Year Ahead surfaces month-level `arc_score` per month and a monthly climate section. Neither passes the surviving natal-house evidence through as an independent, first-class "which life domain is being activated" trace. Instead the house is embedded in each event, and the reader synthesizes house pattern implicitly through the event list.

**Does the system determine which natal planets, points, or bodies carry specific topics?**

Yes for planets and angles: `_natal_targets()` builds a topic-relevance-ready target map, `_TARGET_RELEVANCE` in the predictive engine encodes body salience (angles 1.00, luminaries 0.90, Mars 0.70, Chiron 0.65, Pluto 0.70, and the 8 proprietary asteroids 0.70–0.85). Proprietary indexes (KVQ, MKI, RWI, DFIS, CATALYST, NGE, AHL) explicitly declare which natal bodies drive each index. This is the strongest natal-promise substrate in the codebase.

**Are forecast signals related to meaningful natal configurations?**

Yes at the signal level: each predictive signal carries `source_body`, `target_body`, `aspect`, `target_relevance`, and `activation_route` (`transit_to_angle` / `transit_to_body`). No, at the window-narrative level: windows aggregate signals but do not surface "this window activates *your* Kassandra-conjunct-MC configuration" — only "Uranus square Sun is active." The natal *configuration* (multi-body pattern) is not a first-class output.

**Convergence on life domains from multiple signals.**

Not yet. Convergence today means "multiple transit events with proximate peak dates," not "multiple methods activating the same natal configuration." Domain (house) is a per-event attribute; the convergence detector does not aggregate on domain.

**Distinguishing target relevance from sign symbolism.**

Well-separated. `_TARGET_RELEVANCE` is body-based, not sign-based. Signs are used only for eclipse/lunation zodiac display and ingress destination. Reports do not currently confuse "Mars in Aries season" with "transit hits your Mars."

**Does the report differentiate "transit generally active" from "transit activates a specific natal configuration relevant to [domain]"?**

Not consistently for consumer reports. Year Ahead ledger and Personal Forecast timing windows attach the natal target and house; Year Ahead's Cycle Ledger is the closest to "activates a specific natal configuration." Daily and weekly outputs still frame more of the activity as sky-state.

**Asteroid-based relevance access.**

The engine has structural access to every asteroid's house placement, natal aspects, and rulerships-of-participation *at the natal layer*. Contacts with transits or predictive windows exist only through `scan_proprietary_forecast_windows()` (unwired) or through `_TARGET_RELEVANCE` weighting (unreached).

---

## 6. Long-Clock System Readiness

### Existing prerequisites (already implemented)

- **Date and Julian day arithmetic:** `_julian_day()`, `_datetime_from_julian_day()`, `_add_year_window()`, `_ensure_utc()`.
- **Ephemeris access:** Swiss Ephemeris via `swe.set_ephe_path()`; asteroid catalog access verified.
- **Chart construction:** `generate_payload()` produces a fully normalized payload usable as the base chart for progressions, arcs, or return-chart computation.
- **House and ruler logic:** `whole_sign_house()`, `generate_whole_sign_houses()`, `formulas/standard/rulership_network.py`, `chart_ruler.py`.
- **Aspect infrastructure:** `_detect_aspect()`, `ASPECT_ANGLES`, `ASPECT_CHARACTERS`, orb tables both natal-side and transit-side.
- **Event schema and scoring:** all event families use a shared contract (`event_type`, `transit_planet`, `natal_target`, `aspect`, `peak_datetime`, `entry_datetime`, `leave_datetime`, `combined_intensity_score`, `intensity_label`, `intensity_bar`, `duration_days`). Proprietary events already conform.
- **Predictive method taxonomy:** `TRANSIT`, `LUNATION`, `RETURN`, `PROGRESSION`, `SOLAR_ARC`, `UNKNOWN` are all recognized by `_normalize_method_family()`, `_METHOD_OPERATION_MULTIPLIER`, `_METHOD_WEIGHT_BY_GROUP`, `_activation_route_for_signal()`. Adding a new clock only requires producing events with a matching `event_type` string.
- **Time zone and date-range utilities:** `zoneinfo`, offline place resolver, TZ-aware naïve conversion, DST spring-forward gap detection.
- **Report context / routing infrastructure:** `build_report_context()` dispatches per report type; adding a new context is additive.
- **Predictive residual segmentation and window construction:** entirely event-type-agnostic. Any dated event that fits the signal contract can flow through.

### Missing components (per clock family)

**Solar returns / lunar returns / planetary returns.**
- Missing: a scanner that finds each moment `transit_body.longitude == natal_body.longitude` for a given natal body within the report window (Sun for solar return, Moon for lunar, Jupiter for Jupiter return, etc.).
- Missing: a return-chart constructor (a natal-payload-shaped chart at the return moment, in the birth or relocated location).
- Missing: an event-level return "hit" contract vs a chart-level "return chart interpretation" contract. `agents/PLANNED_UPDATES.md` explicitly directs "start with event-level return hits, not full return-chart interpretation."
- Present: `RETURN` method family taxonomy hook; `RETURN` operation multipliers; `return_clock` weight in `_METHOD_WEIGHT_BY_GROUP` (0.88); target-relevance table can score returns to any body/angle already.

**Secondary progressions.**
- Missing: progression time-scale mapping (one day of ephemeris = one year of life) applied to a chosen inner-body set (Sun, Moon, Mercury, Venus, Mars, ASC, MC).
- Missing: a scanner that produces progressed-body-to-natal-target aspect events within the report window, or that surfaces progressed sign/house ingresses.
- Missing: birth-time gating for progressed angle events (exact-time-required).
- Present: `PROGRESSION` method family taxonomy hook; `progression_clock` weight 0.94; `PROGRESSION` operation multipliers; angle vs body activation routes handle progressed-to-angle vs progressed-to-body.

**Solar Arc directions.**
- Missing: arc computation (progressed Sun's daily arc from natal Sun applied uniformly to every natal body), and a scanner producing arc-body-to-natal-target contacts.
- Missing: a single declared arc convention (`agents/PLANNED_UPDATES.md` explicitly requires "one declared convention only; do not mix arc conventions in the same formula version").
- Present: `SOLAR_ARC` method family taxonomy hook; `solar_arc_clock` weight 0.96; `SOLAR_ARC` operation multipliers.

**Profections.**
- Missing: everything. Profection is a whole-sign transfer (age → house → sign → time-lord planet), which can be computed cheaply per report year, then used to weight the natal target relevance for the year. No `_normalize_method_family` hook exists for it (would fall to `UNKNOWN`).
- Present: whole-sign house math; ruler logic; year math.

**Zodiacal Releasing.**
- Missing: Lot of Spirit (and optionally Fortune) computation; the L1/L2/L3/L4 period stack per lot; peak / loosing-of-the-bond markers; period-to-period transitions.
- Missing: any lot computation infrastructure at all.

**Firdaria and other time-lord methods.** Missing entirely, as with ZR.

**Primary directions.**
- Missing: primary-motion arc computation, key-based conversions (Ptolemy / Naibod / Placidus), promissors and significators.

**Report-interpretation bridges.**
- Missing across all long clocks: a way to link a long-clock event back to the natal chart's *promise* (e.g., "your progressed Moon conjuncts your natal Venus, which rules your 7th house of partnership"). This is the interpretation gap, not an astronomy gap.

**Scoring, convergence, report routing, validation.**
- Present in scaffolding: predictive engine already accepts events of any recognized method family; convergence detector operates on the pre-normalized event list; validation would require the same predictive JSON sidecar noted in §10.
- Missing: convergence *across method families* — the current convergence detector treats transit sub-types, not multiple clocks.

### Integration modes possible

- **As additional event sources into `compute_year_ahead_events()`**: yes, for returns, Solar Arc, and progressions. Each new scanner returns a list matching the event contract, `compute_year_ahead_events()` concatenates into `all_events`, and downstream flows work unchanged. This is the cheapest path per the plan of record.
- **As separate long-cycle layers**: yes, for profections and zodiacal releasing. These are period-based rather than event-based, so they should attach to the report context as time-lord metadata (currently-active lord for each moment) and weight the target relevance for events falling inside their period.
- **As report-only interpretive features**: possible for any long clock as a first pass — surface the current progressed Sun sign, current profected sign/lord, current ZR period as narrative context without feeding them into scoring.
- **As independent subsystems**: primary directions would likely qualify, given the calculation complexity. All others integrate incrementally.

Diagnosis, per user's request, without prescribing specific code changes.

---

## 7. Convergence and Candidate Event Readiness

### Storability / scorability / explainability by component

- **Natal promise:** stored as per-body target relevance, per-body natal aspects, and per-index driver bodies. Not yet linked back per-window as "which specific natal configuration this window is activating." Storable now via existing signal fields; explainability layer would need to compose.
- **Long-clock activation:** unavailable (no long clocks).
- **Short trigger events:** stored with method family, event kind, independence group, activation route, aspect, orb, target, source, dates, cycle metadata, pass sequence.
- **Method convergence and thematic agreement:** the *current* convergence detector treats transit sub-types (transit / ingress / station / eclipse / lunation) with anti-double-counting rules (see `agents/PLANNED_UPDATES.md`: "`station` does not create a second transit-clock chorus vote"). It does not treat multiple *method families* because there is only one. Structurally, `independence_group` on each signal is precisely the field a multi-method convergence layer would key on.
- **Asteroid-specific participation:** absent from consumer flows; latent via unwired proprietary scanner.
- **Multiple methods and method diversity:** absent (only TRANSIT family produces signals).
- **Temporal proximity and topic coherence:** temporal proximity is captured (residual windows). Topic coherence at the window level is captured as `coherence` computed from operation-profile compatibility, with `polarity`, `coalition`, `counterforce`, `complexity` diagnostics — but the "topic" today is operation axes (stabilize/amplify/activate/disrupt/dissolve/reveal), not natal-target coherence.
- **Conflict or counteracting signals:** `counterforce` and `polarity` diagnostics are computed and stored on each window (`semantic_diagnostics`).
- **Confidence levels and age alignment:** per-signal `epistemic_confidence`, `confidence_components`, `confidence_state`, `angle_eligibility`. Age alignment (relevance to the querent's specific life-cycle context) is not modeled.
- **Candidate event window width:** windows enforce `_MIN_PEAK_DISTANCE = 14` days between peaks. Boundaries derive from residual zero-crossings or valleys. Micro-window candidates (see §8) require additional segmentation.

### Where signals collapse into a single score without method provenance

- **`combined_intensity_score`** on transit events combines exactness, planet significance, target-relevance-weighted structural importance, activation multipliers — internal fields are readable inside the event but not re-derivable from the final score alone.
- **`residual_score`** in the daily series is a scalar sum of contributing signal strengths for the day, with structural and trigger split available separately. **Which** signals contributed is not stored per-day; only inferable by re-scanning the signal list for overlap. This is the specific loss point that would prevent post-hoc method-provenance attribution at daily granularity.
- **`combined_intensity_score = 0.0`** on convergence overlay events erases method provenance for the convergence itself.

### Could future convergence scoring integrate without architecture overhaul?

Yes. The predictive engine already carries method_family, event_kind, independence_group, and activation_route on every signal. Adding a cross-method convergence layer needs:

- At least one non-TRANSIT method producing signals (returns, Solar Arc, progressions, lunation-as-independent-family, or profection-as-weighting).
- Per-window aggregation over `independence_group` (rather than only over signal count) to produce a "method diversity" score.
- Optional per-window natal-configuration key so the convergence can be scored not just "N methods active" but "N methods activating the same natal configuration or house."

None of the above requires changing the transit engine, the natal engine, or the predictive engine's window shape. It is additive.

---

## 8. Discrete-Event Prediction Capability

| Requirement | Current Support | Existing Substrate | Missing Components | Confidence Level |
|---|---|---|---|---|
| Isolate a narrow date range without post-hoc adjustments | Partial | Predictive residual peak detection, prominence filter, valley-based boundaries; exact-contact intra-day timing via `compute_daily_timeline` | Micro-window assembly as a first-class output distinct from the 14-day-minimum predictive windows; multi-method peak alignment | Segmentation/detection |
| Preserve exact contact dates for triggers | Yes | `peak_datetime` at 0.01° tolerance; refined transit windows | none | No work needed |
| Differentiate broad background weather from specific triggers | Yes at engine level, No at consumer level | Structural/trigger split in daily series; slow vs fast active-signal lists on each window | Consumer-report expression of the split; separate broad-chapter output type | Pipeline wiring |
| Link timing windows to natal or topic hypotheses | Partial | `natal_target` on every event; `active_signals` list on every window | Natal-configuration keying at the window level; house-domain aggregation across signals | Provenance/schema |
| Retain all evidence and probabilities for auditing | Partial | Signals, daily series, windows, semantic diagnostics, confidence components in memory | Not written to durable export; not attached to manifest | Provenance/schema + validation infrastructure |
| Record misses, quiet periods, or rejected windows | Partial | Rejected peak *counts* recorded in `debug` | Rejected peak indices, prominences, and per-peak reason not preserved; no first-class "quiet period" output | Provenance/schema |
| Generate candidate windows ≤ 6 days | No | `_MIN_PEAK_DISTANCE = 14` blocks this. `compute_daily_timeline` finds exact intra-day moments but does not assemble them into predictive candidate windows. | A distinct micro-window detector operating on `residual_score` daily peaks *and/or* `compute_daily_timeline` moments; a threshold that admits shorter windows for specific method combinations | Segmentation/detection + new astronomical or interpretive methods |
| Distinguish "candidate" from "confirmed" | No | No candidate/confirmed lifecycle exists | Requires convergence-scored candidates plus retrospective validation records | Ranking/convergence + validation infrastructure |
| Handle high-confidence angle events differently from unknown-birth events | Yes at signal level | `epistemic_confidence`, `angle_eligibility`, birth-time gating | Consumer-facing filter/labeling | Pipeline wiring |
| Persist the "why" of each window in a machine-readable form | Partial | Window's `semantic_diagnostics`, `active_signals`, `memory_state` all exist | Windows are not sidecar-exported; per-day contributor IDs not stored | Provenance/schema + validation infrastructure |

**Six-day candidate windows specifically.** The residual detector cannot produce these under current constants. However, `compute_daily_timeline` returns intra-day exact contact moments over any date range, and the `predictive_sandbox` architecture explicitly reserves space for "micro-window candidates" per `ENGINE_CAPABILITY_SURFACE_AUDIT.md`. Assembling those moments into a candidate object (distinct from a window) is scoped as segmentation + schema work; the astronomy is already there.

---

## 9. Report and User Interface Compatibility

Advanced multi-clock outputs would need appropriate surface layers per product. The complexity should be gated by product, not universally exposed.

- **Year Ahead** — client-facing forecast/planning report.
  - Best surface for multi-clock results: **client-facing timing signals** in the existing timing-windows module; **practitioner-level evidence layer** in a technical appendix; **hidden calculation** for method-family provenance and epistemic confidence internals.
  - What already exists as substrate: raw cycle ledger, forecast climate, monthly arc scores, calculation record.
  - What would need to be added: a "candidate events" module for narrow windows, a "clock activity" panel for currently-active long clocks (profections, ZR, returns), and a manifest-side predictive evidence bundle.

- **Personal Forecast** — 90-day themes and windows.
  - Best surface for multi-clock: **client-facing timing signals** at theme anchors; **discrete candidate reports** where multi-method convergence exceeds a threshold in the next 90 days.
  - Substrate present: theme grouping, anchor/support event selection, timing windows.

- **Daily Horoscope** — same-day guidance.
  - Best surface: current-day *natalized* activation, which already exists. Multi-clock content is over-scale for daily — surface only if a candidate window overlaps today.
  - Constraint: the `--report-date` control issue documented in `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md` §4 must be resolved before daily can be used for reproducible batch validation of predictive claims.

- **Weekly Horoscope** — chart-specific timeline for the week.
  - Best surface: **client-facing timing signals**; can carry candidate windows overlapping the week.
  - Constraint: currently under-authored per `agents/PLANNED_UPDATES.md`; interpretive content packs still forthcoming.

- **Internal R&D outputs** — `predictive_sandbox`.
  - Already the correct home for full multi-clock evidence: signals table, daily series table, windows table, semantic diagnostics, debug counters, block routing preview.
  - Recommended surface for: raw predictive JSON export, rejected peak diagnostics, per-day signal provenance, method-family provenance, epistemic confidence detail.

- **White-label or client reports** — not currently implemented (`CONTENT_PACKS` is wired only to `year_ahead`).
  - Would need per-tenant content pack routing and per-tenant surface-layer policy (which multi-clock content is visible).

The design principle already in the codebase (`agents/PLANNED_UPDATES.md`: "Renderers remain downstream of computed evidence; they do not invent meaning") supports this layering: engine evidence is one thing, consumer expression is another.

---

## 10. Validation and Auditability

### Currently persisted

- **Input chart:** natal payload is in memory, and its identifying fields (birth data, resolved location, user profile) are recorded in the report manifest sidecar.
- **Ephemeris and versions:** Swiss Ephemeris version is available via `swe`; the manifest records report_version, active modules, methodology.
- **Clock calculations** (transit/ingress/station/eclipse/lunation): produced by `compute_year_ahead_events()`, held in memory, rendered into HTML. Raw event JSON is **not** written to any sidecar.
- **Asteroid positions:** natal only; forecast-side asteroid positions from `scan_proprietary_forecast_windows()` do not run.
- **Signal records and weights:** produced by predictive engine, held in memory, forwarded to sandbox context, **not** manifested.
- **Candidate windows and trigger points:** produced, held in memory, rendered in sandbox HTML only.
- **Convergence analysis:** synthesized into Year Ahead context and rendered; not exported as machine-readable data.
- **Rejected or suppressed candidates:** rejected peak *counts* recorded in `debug`; per-index / per-prominence details **not** preserved.
- **Confidence flags and reasoning:** per-signal `epistemic_confidence`, `confidence_components`, `confidence_state`, `angle_eligibility` — all in memory, forwarded to sandbox context, not manifested.
- **Report versions and research status:** `product_versions.py` provides per-report-type version numbers; the predictive engine carries `predictive_v0.3.1` as `formula_version` and returns it in `compute_predictive_windows()` result.
- **Past outcomes / feedback:** no infrastructure for tracking outcomes exists.

### Required for validation

A durable machine-readable "audit trail" per generated report would need:

1. **A predictive evidence sidecar** (`.predictive.json`) containing: `signals`, `daily_series` (with contributor IDs, see next item), `windows`, `debug`, `rejected_peaks`.
2. **Per-day signal provenance** inside `daily_series`: `contributing_signal_ids` list, and structural vs trigger breakdown per contributor.
3. **Rejected-peak diagnostics** inside `debug`: `rejected_peaks: [{index, date, residual, prominence, filter_reason}, …]`.
4. **Raw event timeline** (either in the predictive sidecar or in the manifest): the pre-signal `all_events` list from `compute_year_ahead_events()`.
5. **Ephemeris fingerprint** in the manifest: Swiss Ephemeris file inventory hash and version number.
6. **Immutable snapshot of thresholds and constants** at generation time: `_MIN_PROMINENCE`, `_MIN_PEAK_DISTANCE`, `_BASELINE_WINDOW_DAYS`, `_SMOOTH_WINDOW_DAYS`, orb tables, planet weights, target relevance table. These are literals today; a snapshot in the manifest makes the run reproducible even if constants later change.
7. **Convergence provenance:** per convergence overlay, the list of contributing events and the specific rule that produced the overlay.
8. **Rejected-window log:** windows the detector considered but dropped (below-prominence, too-close, or explicitly filtered) with reason codes.
9. **Formula version bindings:** every scoring component (`_PREDICTIVE_FORMULA_VERSION`, transit_engine formula version, natal_engine formula version) carried in the manifest.
10. **A retrospective-outcome log** persisted per chart per window (outside the report file) — this does not exist today and would be new infrastructure.

An external reviewer today can see rendered evidence (Year Ahead cycle ledger, sandbox HTML tables) and can hand-transcribe fields. Machine-readable retrospective validation is not yet supported.

---

## 11. Capability Inventory

| Capability | Location | Inputs | Consumers | Surface Level | Asteroid-Awareness | Clock Layer | Status | Loss Points | Confidence | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| 34-asteroid natal calculation | `engine/natal_engine.py:76-120, 559-581` | JD, ephemeris | proprietary indexes, aspect matrix, governance registry | Hidden calculation (surfaced only via soul_ecosystem) | Full | Natal | Fully surfaced | ephemeris miss per body → string message | High | verified |
| Natal aspect matrix (planets + angles + asteroids) | `natal_engine.py:583-626` | payload bodies | formula layer, transit `_natal_targets`, `_proprietary_targets` | Hidden calculation | Full | Natal | Fully surfaced | none | High | verified |
| Whole-sign house assignment | `natal_engine.py:204-242` | ASC longitude | every downstream layer | Hidden calculation | Full | Natal | Fully surfaced | none | High | verified |
| Proprietary indexes (KVQ, MKI, RWI, DFIS, CATALYST, AHL, NGE) | `formulas/proprietary_indexes.py` | natal payload | report contexts, `_leading_index()` | Client-facing (soul_ecosystem, identity), practitioner (technical appendix) | Full | Natal | Fully surfaced | NGE and AHL commented out of predictive registry | High | verified |
| Governance registry | `formulas/governance_registry.py` | body/method key | report layer rules, report_surface bundle | Hidden calculation | Full | Cross-cutting | Fully surfaced | none | High | verified |
| Transit cycle scanner (planets + angles, no asteroids) | `transit_engine.py:1452-1578` | natal, window, orb tables | `compute_year_ahead_events` | Client-facing (year_ahead, personal_forecast) | None | Transit | Fully surfaced | asteroids excluded from target set | High | verified |
| House-ingress scanner (Jupiter → Pluto only) | `transit_engine.py:1584+` | natal, window | `compute_year_ahead_events` | Client-facing | None | Transit sub-type | Fully surfaced | Mars/Venus/Mercury/Sun ingresses absent | High | verified |
| Station scanner | `transit_engine.py:1681+` | natal, window | `compute_year_ahead_events` | Client-facing | None | Transit sub-type | Fully surfaced | none | High | verified |
| Eclipse scanner | `transit_engine.py:2015+` | Swiss Ephemeris eclipses, natal | `compute_year_ahead_events` | Client-facing | None | Transit sub-type / LUNATION taxonomy | Fully surfaced | asteroids excluded from `ECLIPSE_TARGET_KEYS` | High | verified |
| Plain lunation scanner (with 2° natal contact filter, eclipse-date suppression) | `transit_engine.py:2176-2263` | natal, eclipses | `compute_year_ahead_events` | Client-facing | None | LUNATION | Fully surfaced | asteroids excluded from targets | High | verified |
| Retrograde cluster detector | `transit_engine.py:1803+` | 8-planet daily sweep | year_ahead / personal_forecast climate | Client-facing | None | Climate | Fully surfaced | none | High | verified |
| Void-of-course Moon detector | `transit_engine.py:1907+` | Moon aspects | personal_forecast, potential daily | Client-facing | None | Climate | Fully surfaced | none | High | verified |
| Daily activation transit selection | `transit_engine.py:1177-1250` | natal, day | daily_horoscope | Client-facing | None | Transit (day-scale) | Fully surfaced | daily date-source bug | High | verified |
| Daily / weekly exact-contact timeline | `transit_engine.py:1297-1390` | natal, window | daily_horoscope, weekly_horoscope | Client-facing (partial) | None | Transit (intra-day) | Fully surfaced | weekly interpretation copy pending | High | verified |
| Proprietary forecast scanner (Disruption, Sovereignty, Catalyst — asteroid-aware) | `transit_engine.py:951-1049` | natal payload with asteroids | (none — stranded) | None | **Full** (only forecast surface with asteroid participation) | Transit family | **Implemented but unreachable in active pipeline** | scanner exists but is never called | High | grep confirms sole reference is the `def` line |
| Predictive engine end-to-end | `predictive_engine.py:264-331` | year_ahead events, index results | year_ahead / personal_forecast contexts (dropped by templates), sandbox context | Partial (sandbox HTML) | Latent (relevance table has 8 asteroids) | Multi-family (only TRANSIT is fed) | Partially wired | consumer templates do not render `predictive_results` | High | verified |
| Predictive signal normalization | `predictive_engine.py:366-459` | year_ahead events | daily series, windows, sandbox context | Sandbox HTML | Latent | Multi-family taxonomy | Partially wired | asteroid signals never produced | High | verified |
| Daily resonance series (raw/smooth/baseline/residual, structural vs trigger) | `predictive_engine.py:464-521` | predictive signals | window detector, sandbox context | Sandbox HTML | Latent | Cross-family | Partially wired | per-day contributor IDs dropped | High | verified |
| Prominence-filtered residual window detector | `predictive_engine.py:555-689` | daily series, signals | sandbox context, block routing | Sandbox HTML | Latent | Cross-family | Partially wired | rejected peaks not preserved; 14-day floor | High | verified |
| Window semantic metrics (`coherence`, `polarity`, `coalition`, `counterforce`, `complexity`, `dominant_operation`, `semantic_state`) | `predictive_engine.py:1132-1228` | active signals, operation profiles | window objects, sandbox context, block routing | Sandbox HTML | Latent | Cross-family | Partially wired | consumer reports do not surface | High | verified |
| Episode memory + FSM lifecycle | `predictive_engine.py:1231-1398` | activation key + prior signals + gradient | window fields, sandbox context, block routing | Sandbox HTML | Latent | Cross-family | Partially wired | none as debug; consumer reports do not surface | High | verified |
| Epistemic confidence scaffolding | `predictive_engine.py:1025-1114` | birth-time state, angle-eligibility, exactness, target uncertainty | per-signal fields | Sandbox HTML | Latent | Cross-family | Partially wired | relation_robustness still exactness-derived (per REVISIONS.md) | High | verified |
| Method-family taxonomy hooks (TRANSIT/LUNATION/RETURN/PROGRESSION/SOLAR_ARC/UNKNOWN) | `predictive_engine.py:121-128,175-181,876-965` | signal event_type | operation multipliers, method weight, activation route | Sandbox HTML | Any (only TRANSIT is fed) | All families | Partially wired | RETURN/PROGRESSION/SOLAR_ARC hooks unused because no scanner emits them | High | verified |
| Convergence detector (transit sub-type overlay) | `generate.py:6966+` (active); `6842-6966` (legacy dead) | all_events, convergence blocks | Year Ahead | Client-facing | None | Single-family | Fully surfaced as overlay | score 0.0; not multi-family | High | verified |
| Report manifest sidecar | `generate.py:3444-3525` | context, versions, trace | operator review | Practitioner | none | Cross-cutting | Partially wired | omits `predictive_results` and raw event timeline | High | verified |
| Predictive block routing (sandbox JSON library) | `products/predictive_sandbox/blocks/` + registry loader | window fields | sandbox narrative preview | Sandbox HTML | via window semantic fields | Cross-family | Partially wired | content coverage uneven; legacy fallback still reachable | Medium | verified via directory structure |
| Progressions | not present | — | — | — | — | Long | Absent | — | High | grep negative |
| Solar Arc | not present | — | — | — | — | Long | Absent | — | High | grep negative |
| Returns (scanner) | not present | — | — | — | — | Long | Absent | — | High | grep negative |
| Profections | not present | — | — | — | — | Long | Absent | — | High | grep negative |
| Zodiacal Releasing | not present | — | — | — | — | Long | Absent | — | High | grep negative |
| Firdaria and other time-lord | not present | — | — | — | — | Long | Absent | — | High | grep negative |
| Primary directions | not present | — | — | — | — | Long | Absent | — | High | grep negative |
| Arabic parts / lots | not present | — | — | — | — | Long substrate | Absent | — | High | grep negative |
| Legacy convergence detector | `generate.py:6842-6966` | events | (superseded) | none | none | Transit | Dead / unreachable | function name says `_legacy_dead` | Medium | per prior audit |
| Legacy MCQ / SIREN / MAGNETIC indexes | removed in 2026-07-02 asteroid_portrait removal | — | — | — | referenced by soul_ecosystem archetypes | Natal | Removed / superseded | — | Medium | `agents/REVISIONS.md` 2026-07-02 |

---

## 12. Existing Capabilities Summary

**Present today, no promotional overstatement.**

- **Current transit-based forecasting skills:** natal chart with 34 asteroids and Whole Sign houses; multi-planet transit-cycle scanner with entry/peak/leave refinement to sub-arc-minute precision; whole-sign house ingress scanner for Jupiter through Pluto; station scanner for Mercury through Pluto; eclipse and lunation scanners with 2° natal-contact qualification and eclipse-vs-lunation dedup; retrograde-cluster and void-of-course-Moon climate detectors; daily activation-transit selection with graduated same-day orbs; Moon-primary intra-day exact-contact timeline extendable across arbitrary date ranges; monthly arc scoring for Year Ahead; theme grouping and anchor selection for Personal Forecast; convergence detection as structural overlay within transit family; predictive signal normalization, residual peak detection with prominence filter, minimum-distance filtering, valley-based boundary assembly, FSM lifecycle continuity, episode memory, and window-level semantic diagnostics — all engine-only unless the report is `predictive_sandbox`.

- **Asteroid inclusion in current models:** all 34 asteroids computed astronomically and stored per natal payload; joined into the natal aspect matrix; classified in the governance registry with catalog number, lineage, and layer eligibility; consumed by 7 proprietary indexes (KVQ, MKI, RWI, DFIS, CATALYST, AHL, NGE) plus dead legacy indexes; not surfaced in forecast events for any active report; visible to the client only through `soul_ecosystem` narrative and `predictive_sandbox` diagnostics.

- **Timing systems present:** transit cycles, house ingresses, stations, eclipses, lunations, retrograde clusters, void-of-course Moon, same-day activation, intra-day exact-contact timeline. All are transit-family. No progressions, no Solar Arc, no returns, no profections, no zodiacal releasing, no time-lord methods, no primary directions.

- **Report architecture in use:** shared natal payload → standard + proprietary formula indexes → variable resolver + block selector → per-product context builder → per-product Jinja template → HTML + manifest sidecar. Products: `year_ahead`, `personal_forecast`, `daily_horoscope`, `weekly_horoscope`, `soul_ecosystem`, `predictive_sandbox` (dev-only). Additional in-tree but not on the CLI dispatch: `identity_profile` (orphaned per `agents/REVISIONS.md`), `cosmic_weather` (new, uncommitted), `sun_sign_horoscope` (uncommitted).

**Ambitions and plans (not present in code today), per `agents/PLANNED_UPDATES.md` and `agents/REVISIONS.md`:**

- Interval-aware epistemic robustness (replace exactness-derived proxy).
- Bounded semantic-metric calibration against real output distributions.
- Exact returns (event-level, not full return-chart interpretation), starting with Solar/Lunar/Jupiter/Saturn.
- Solar Arc sandbox macro (one declared convention).
- Limited secondary progressions sandbox (Sun/Moon/ASC/MC with exact-time gating).
- Sandbox JSON library content coverage in `predictive_sandbox/blocks/` folders (`00_scaffold`, `10_copy_entirely`, `20_modify_from_existing`, `30_new_writes`, `90_archive`).
- Deliberately deferred: Relay Gate, Structural Shear, pathway topology, full return-chart interpretation, harmonics, time lords, asteroid seasons, electional timing, synastry prediction, primary directions.

**Discrete-event research posture (not a shipping capability):**

- The `predictive_sandbox` template surfaces windows with their evidence rows and is the R&D lane. Any discrete-event candidate work is targeted there.

Kept language deliberately factual and separated from the aspirations section, per the audit spec.

---

## 13. Next Investigation Priorities

Ranked to maximize future architecture support, with the current constraints of a single-operator local workflow and the plan-of-record from `agents/PLANNED_UPDATES.md`.

1. **Verify what `scan_proprietary_forecast_windows()` produces for a real chart, and identify why it is not wired into `compute_year_ahead_events()`.** This is the single highest-leverage question in the codebase for asteroid-rich predictive work. Determine whether the non-wiring is (a) intentional (governance policy: proprietary asteroid transits are only for `predictive_sandbox` / `soul_ecosystem`), (b) legacy pending decision, or (c) an oversight. Answering this defines the shortest path to asteroid-first-class forecasting.
2. **Design and validate a predictive evidence sidecar schema.** `predictive_results` is calculated, forwarded to context, dropped by templates. A `.predictive.json` sidecar that preserves `signals`, `daily_series` (with per-day contributor IDs), `windows`, `debug`, `rejected_peaks`, and formula-version bindings is the smallest change that unlocks retrospective validation.
3. **Assess whether daily-series contributor IDs and rejected-peak diagnostics can be preserved without altering astronomical calculation.** The two known loss points at the daily level. Both are schema fixes, not detector redesigns.
4. **Determine the minimum viable exact-return event contract.** Per `agents/PLANNED_UPDATES.md`, "start with event-level return hits, not full return-chart interpretation." Confirm the event contract to match, decide the return-body set (Sun, Moon, Jupiter, Saturn), and identify how to gate lunar returns against birth-time confidence.
5. **Confirm the plan-of-record boundary between `scan_proprietary_forecast_windows()` participation and the future non-TRANSIT method families.** If proprietary transits are meant to normalize as `method_family = "TRANSIT"` (they already do via `_normalize_method_family`), decide whether they should also carry a distinct `activation_route` for asteroid-source-vs-planet-source anti-double-counting.
6. **Decide the convergence-detection scope explicitly.** The active `_detect_and_frame_convergences()` operates in a single family. Choose whether convergence should aggregate across `independence_group`, across `activation_route`, or across natal-house / natal-configuration keys.
7. **Assess micro-window candidate assembly.** `compute_daily_timeline` returns exact intra-day moments. Determining whether a distinct "micro-window candidate" object should ride alongside the 14-day-minimum residual window in `predictive_sandbox` output is a scoping question, not a research question.
8. **Confirm the manifest / sidecar boundary for asteroid natal positions.** Currently the manifest omits the natal aspect matrix and asteroid positions. Deciding whether validation needs a signed natal snapshot beyond the birth data record affects whether a natal sidecar is warranted.
9. **Audit governance layer rules for cross-report asteroid visibility.** Governance today gates asteroids to `soul_ecosystem` and `predictive_sandbox` only. This is a deliberate policy. Determining whether Year Ahead / Personal Forecast can carry practitioner-appendix asteroid content requires a policy call, not a code call.
10. **Identify quick wins that expose latent capability without expanding scope.** Concrete candidates:
    - Add `predictive_results` to `_write_report_manifest()` under a feature flag so that R&D runs preserve it.
    - Add a "predictive evidence appendix" section to `predictive_sandbox` HTML that includes signal IDs, per-window active_signals, and per-window semantic_diagnostics as a copyable JSON blob.
    - Add per-day `contributing_signal_ids` field to `_build_daily_series()` output.
    - Add `rejected_peaks: [{index, date, residual, prominence, filter_reason}, …]` to `_detect_windows()` debug output.
    - Wire a single-call site for `scan_proprietary_forecast_windows()` in `predictive_sandbox` only (governance-consistent), so asteroid-aware signals start reaching the predictive engine without changing consumer-report claims.

---

## Appendix: Deliberate omissions

- No production files, formulas, JSON block libraries, templates, or configuration were modified for this audit.
- No new test outputs were generated; existing `audit_output/` was treated as reference material.
- Confidence and semantic aggregation code was inspected as-is; the interval-sampled epistemic robustness expansion described in `agents/PLANNED_UPDATES.md` is not treated as present.
- Adjacent surfaces (`engine/temporal_river.py`, `engine/constellation_mesh.py`, `products/cosmic_weather/`, `products/sun_sign_horoscope/`, `products/identity_profile/`) were catalogued but not evaluated as multi-clock predictive infrastructure.
- The client-forecast product policy calls in `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md` §9-10 were treated as source of truth and not re-litigated.

---

## Final Note

Entangled Oracle is closer to a multi-clock predictive platform than the shipping consumer reports suggest, because the signal-normalization, semantic-diagnostic, epistemic-confidence, memory, and lifecycle-continuity scaffolding needed to receive multi-clock events already exists in `engine/predictive_engine.py`. The distance from where the codebase is now to a comprehensive, asteroid-rich, multi-clock predictive system is dominated by:

- one wiring decision (`scan_proprietary_forecast_windows()` → predictive signal stream, governance-appropriate),
- one schema decision (predictive evidence sidecar with daily contributor IDs and rejected peaks),
- one or two additional astronomical event scanners (returns first, then Solar Arc, then progressions, in the order the plan of record specifies),
- one convergence-scope decision (cross-family aggregation),
- one micro-window assembly decision (retain 14-day residual windows *and* emit narrower candidates for specific method combinations).

None of these requires an overhaul of the natal engine, transit engine, formula layer, or report generation flow. The complexity that exists is well-structured, mechanically connected via the shared event contract, transparent (via the sandbox surface and forwarded diagnostics), and testable in principle once the validation sidecar exists. It is *not* currently testable in a retrospective-outcome sense because the durable audit trail is not written.

The current system supports natal-promise assessment strongly; long-term-segment identification not at all except through single-family transit chapters; trigger-period identification well within the transit family; and narrow event window generation only at intra-day exact-contact granularity, not at the 3–6 day predictive-candidate granularity. Moving to the target capability is incremental, layered work, matching the sequencing described in `agents/PLANNED_UPDATES.md` — semantic-metric calibration and interval-aware confidence before more clocks; asteroid participation as a governance-consistent early win; and validation infrastructure alongside method expansion rather than after.
