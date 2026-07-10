# Forecast Computation Ledger & Canonical Event Adapter

Status: internal Tier 0 / Tier 1 evidence work. This document describes
runtime computation and normalization; it does not claim that an internal
method is client-visible or production-ready.

## 1. Active Forecast Call Path

`generate.py` orchestrates the `year_ahead` and `personal_forecast` report
paths. Both context builders call
`engine.transit_engine.compute_year_ahead_events`, with distinct options and
report windows:

- **Year Ahead (`year_ahead`)**
  - **Pipeline Call:** `compute_year_ahead_events(payload, start_date, end_date, include_year_texture=True)`
  - **Characteristics:** Spans 12 months. Consumes the full baseline timeline (transits, ingresses, stations, eclipses, lunations) plus slow-moving "texture" events (Solar Arc directions and structural secondary progressions) to contextualize the era.

- **Personal Forecast (`personal_forecast`)**
  - **Pipeline Call:** `compute_year_ahead_events(payload, start_date, end_date, include_moon_progressions=True)`
  - **Characteristics:** Spans 90 days. Excludes slow texture (since they remain static over a 90-day window) but opts into fast-moving Progressed Moon contacts to act as rapid modifiers and triggers.

*Note: The `weekly_horoscope` and `daily_horoscope` bypass this engine, instead routing through `compute_daily_timeline` for localized, short-window activation.*

---

## 2. Raw Event Families & Consuming Surfaces

The engine currently emits several raw event families, enriched synchronously via `formulas/standard/forecast_activation.py` (`link_related_forecast_events`):

| Method Family | Engine Method | Included by Default | Specific Consumers |
|---|---|---|---|
| **Transits** | `scan_transit_windows` | Yes | `year_ahead`, `personal_forecast` |
| **Ingresses** | `scan_house_ingresses` | Yes | `year_ahead`, `personal_forecast` |
| **Stations** | `scan_stations` | Yes | `year_ahead`, `personal_forecast` |
| **Eclipses** | `scan_eclipses` | Yes | `year_ahead`, `personal_forecast` |
| **Lunations** | `scan_lunations` | Yes | `year_ahead`, `personal_forecast` |
| **Profection Periods** | `annual_profection_periods` | Yes (Internal) | Alters transit weights internally; no template consumes standalone profection periods. |
| **Moon Progressions** | `scan_progression_events` | No | `personal_forecast` (when `include_moon_progressions=True`) |
| **Texture Progressions** | `scan_progression_events` | No | `year_ahead` (when `include_year_texture=True`) |
| **Solar Arcs** | `scan_solar_arc_events` | No | `year_ahead` (when `include_year_texture=True`) |
| **Returns** | `scan_return_events` | No | Internal/engineering evidence only; not called by the two active report-context paths above. |
| **Zodiacal Releasing events** | `zodiacal_releasing_events` | No | Internal/engineering evidence only; not called by the two active report-context paths above. |

### State distinctions

- Transits, ingresses, stations, eclipses, and lunations are computed and
  consumed by both forecast context builders.
- Annual profections are computed as internal weighting/linkage. Their periods
  are not standalone client prose.
- Progressed Moon events are computed for Personal Forecast context. Broader
  progression and Solar Arc events are computed for Year Ahead texture context.
  Context presence is not, by itself, proof of template consumption.
- Returns and Zodiacal Releasing are implemented scanners with internal or
  engineering visibility. This pass does not promote them into an active report.
- The canonical adapter is additive and preserves legacy keys so existing
  selectors/templates continue to receive their current shapes.

---

## 3. Discrepancies in Event Fields Across Methods

Before events reach the standard schema adapter, the raw pipeline output contains legacy discrepancies. `formulas.standard.forecast_activation.enrich_forecast_event` appends a suite of uniform scoring fields (`natal_relevance`, `structural_importance`, `combined_intensity_score`, etc.), but the core timeline data fields exhibit drift:

- **House Targets:**
  - *Ingresses* use `house_number` or `whole_sign_house`.
  - *Transits/Other* use `natal_house`.
- **Natal Target Names:**
  - Usually mapped to `natal_target`.
  - Occasionally found under `natal_contact`.
- **Date Boundaries and exact moments:**
  - *Transits* carry `cycle_start_date` and `cycle_end_date` alongside `entry_date`, `peak_date`, and `leave_date`.
  - *Stations* and *Eclipses* typically carry a `peak_datetime` with fixed or missing entry/leave margins.
  - Advanced scanners commonly use `exact_datetimes`; some transit-cycle
    records instead use a `contacts` list. The adapter accepts both without
    deleting either legacy representation.
- **Scoring Aliases:**
  - Events may carry varying score identifiers prior to normalization: `concentration_score`, `raw_score`, `combined_intensity_score`, `score`, and `reader_facing_activity_score`. The `enrich_forecast_event` method forcibly mirrors these to `combined_intensity_score`, `score`, and `reader_facing_activity_score`.

---

## 4. Canonical Event Schema Adapter Map

`engine.forecast_event_adapter.normalize_to_forecast_event()` now adds the
Phase 0 `ForecastEvent` contract (`phase0.1.0`) to legacy dictionaries. It
does not remove or rename existing keys.

| `ForecastEvent` Field (Phase 0) | Source Data / Transformation Rule |
|---|---|
| `schema_version` | Hardcoded: `"phase0.1.0"` |
| `event_id` | Deterministic hash of method family/variant, peak, source, target, and aspect; preserves a scanner-supplied ID. |
| `method_family` | Normalization of `event_type` (`TRANSIT`, `LUNATION`, `PROGRESSION`, `SOLAR_ARC`). |
| `method_variant` | `event_type` subclass (e.g., `ingress`, `station`, `eclipse`). |
| `clock_role` | Assigned via charter lookup based on method variant. |
| `source_body` | `raw["transit_planet"]` (or directed/progressed body). |
| `source_kind` | Mapped via taxonomy (planet, luminary, angle, node, asteroid). |
| `target_body` | `raw["natal_target"]` or `raw["natal_contact"]`. |
| `target_kind` | Mapped via taxonomy. |
| `start_at` | `raw["entry_datetime"]` or `raw["cycle_start_date"]`. |
| `peak_at` | `raw["peak_datetime"]`. |
| `end_at` | `raw["leave_datetime"]` or `raw["cycle_end_date"]`. |
| `exact_at` | List derived from `exact_datetimes` and/or the `contacts` array. |
| `orb` | `raw["peak_orb"]` or fallback. |
| `phase` | `raw["station_type"]` (for stations) or `raw["eclipse_type"]`. |
| `event_strength` | `raw["combined_intensity_score"]` or `raw["reader_facing_activity_score"]`. |
| `strength_components` | `{ exactness: raw["exactness"], duration: raw["duration_factor"], structural: raw["structural_importance"] ... }` |
| `temporal_precision` | Computed based on event duration limits. |
| `independence_group` | Preserves scanner value; otherwise uses a conservative family-level anti-double-counting group. |
| `activation_route` | Preserves scanner value; otherwise derives only routes declared by the canonical contract. |
| `topic_keys` / `domain_keys` | Derived directly from `raw["shared_life_domains"]`. |
| `calculation_trace` | Preserves scanner trace, formula version, and a concrete `missing_fields` list. Missing calculation evidence remains visible. |
| `report_surface_visibility` | Preserves scanner value; missing visibility defaults to internal/engineering diagnostics only. |

### Remaining gaps before broader normalization

- Legacy core event families do not all provide the complete confidence
  component set defined by the Phase 0 schema. The adapter records absent
  inputs and uses conservative numeric values; scanner-level calculation is a
  later Tier 1 task.
- An event with no `orb`, `distance`, or `phase` remains visibly malformed in
  `calculation_trace`. The adapter does not invent `orb = 0.0`; scanner or
  serializer policy must resolve or reject it.
- This pass does not add convergence scoring, formula thresholds, synthesis,
  templates, prose blocks, or client-surface promotion.
