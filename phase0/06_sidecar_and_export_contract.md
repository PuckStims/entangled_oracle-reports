# Phase 0 — Sidecar and Export Contract

Program: [EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md](../EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md)
Depends on: [01_predictive_object_schemas.md](./01_predictive_object_schemas.md) (now `phase0.1.1`), [04_convergence_and_candidate_protocol.md](./04_convergence_and_candidate_protocol.md), [05_validation_protocol.md](./05_validation_protocol.md).
Status: charter (Phase 0, operator-approved). Contract. No implementation.
Version: `phase0.1.1`
Date: 2026-07-07 (patched same day, before Phase 2 implementation began, per Phase 2 Claude contract-conformance review: added `natal_snapshot.lots` — see `phase0.1.0` → `phase0.1.1` diff in `agents/REVISIONS.md`)

## Purpose

Specify the machine-readable evidence artifacts EO writes alongside each predictive report. These artifacts are the recordkeeping layer that makes every downstream method inspectable, reproducible, and validation-eligible.

## 1. Files

Per predictive report run:

| File | Purpose | Written by | Read by |
|---|---|---|---|
| `<report_id>.html` | Rendered report. Unchanged by Phase 0. | Existing generator. | End user / reviewer. |
| `<report_id>.manifest.json` | Delivery-oriented manifest. Unchanged by Phase 0. Retains existing operator/traceability role. | Existing `_write_report_manifest()`. | Operator / delivery review. |
| `<report_id>.eo_predictive.json` | **New. Full predictive evidence sidecar.** | Phase 1 deliverable. | R&D, validation, sandbox. |
| `<report_id>.eo_outcomes.json` | **New. Outcome ledger, written after outcome review.** | Reviewer tooling (Phase 9). | Validation aggregation. |

Note: the existing `manifest.json` is intentionally not extended with `predictive_results`. Two separate files means the delivery manifest stays partner-safe (no diagnostic density) while the predictive sidecar becomes the R&D artifact.

## 2. `<report_id>.eo_predictive.json` — top-level structure

```json
{
  "sidecar_version": "phase0.1.1",
  "sidecar_schema_version": "phase0.1.1",
  "report_run": { ... },
  "natal_snapshot": { ... },
  "environment": { ... },
  "policy_versions": { ... },
  "natal_promise_anchors": [ ... ],
  "raw_events": [ ... ],
  "predictive_signals": [ ... ],
  "daily_series": [ ... ],
  "time_lord_periods": [ ... ],
  "chapters": [ ... ],
  "candidates": [ ... ],
  "rejected_candidates": [ ... ],
  "convergence_composition": [ ... ],
  "detector_thresholds": { ... },
  "asteroid_diagnostics": { ... },
  "debug": { ... },
  "provenance": { ... }
}
```

### 2.1 `report_run`

```json
{
  "report_run_id": "run_<8-hex>",
  "report_type": "predictive_sandbox",
  "report_start": "2026-07-07T00:00:00Z",
  "report_end": "2027-07-07T00:00:00Z",
  "generated_at": "2026-07-07T12:34:56Z",
  "engine_version": "eo_generator_x.y.z",
  "git_commit": "<hash>",
  "engine_command": "generate.py --report-type predictive_sandbox --name ... --date ... --time ... --location ..."
}
```

`git_commit` is best-effort; if the sandbox environment cannot resolve HEAD it is `null` with a note in `debug.git_commit_note`.

### 2.2 `natal_snapshot`

Immutable. This is *the* natal snapshot the predictive run used. If a chart is re-run with corrected birth data, a new snapshot ID is produced.

```json
{
  "natal_snapshot_id": "natal_<16-hex>",
  "birth_data": {
    "name": "...",
    "date": "1980-01-01",
    "time": "12:34:56",
    "time_state": "exact",
    "location_input": "...",
    "resolved_location": "...",
    "latitude": 0.0,
    "longitude": 0.0,
    "timezone": "...",
    "julian_day": 0.0,
    "local_datetime": "...",
    "utc_datetime": "..."
  },
  "methodology": {
    "zodiac": "tropical",
    "house_system": "whole_sign",
    "ephemeris": "swiss_ephemeris",
    "ephemeris_version": "...",
    "ephemeris_files_hash": "..."
  },
  "angles": { "Ascendant": {...}, "Midheaven": {...}, "Descendant": {...}, "Imum_Coeli": {...}, "Vertex": {...} },
  "houses": { "House_1": {...}, ..., "House_12": {...} },
  "standard_planets": { "Sun": {...}, ..., "Lilith_BML": {...} },
  "custom_asteroids": { "Kassandra": {...}, ..., "DNA": {...} },
  "lots": { "Fortune": {...}, "Spirit": {...}, "Necessity": {...} },
  "aspects": [ {...}, ... ],
  "user_profile": {...}
}
```

`natal_snapshot_id` is deterministic: hash of the canonicalized `birth_data + methodology + ephemeris_files_hash + policy_versions.natal_engine`. The same chart re-run under the same natal engine produces the same ID.

`custom_asteroids` includes all 34 entries (or their error strings). Missing asteroids are listed in `asteroid_diagnostics.ephemeris_missing`.

`lots` is empty (`{}`) until Phase 6 implements Lot calculation per `03_method_charters.md` §C5. Each populated entry follows the same shape as an `angles` entry (`longitude`, `sign`, `degree`, `house`) plus a `sect` field (`day` / `night`) recording which sect condition produced that lot's formula variant for this chart. This is the canonical natal home for Lot positions — `NatalPromiseAnchor.natal_lots` (`01_predictive_object_schemas.md` §1) and any `ForecastEvent` with `source_kind` or `target_kind = "lot"` resolve against these entries, the same way body-based events resolve against `standard_planets`/`custom_asteroids`.

### 2.3 `environment`

```json
{
  "python_version": "...",
  "swisseph_version": "...",
  "jinja2_version": "...",
  "asteroid_registry_version": "phase0.1.0",
  "method_policy_versions": {
    "returns": "phase0.1.0",
    "solar_arc": "phase0.1.0",
    "progressions": "phase0.1.0",
    "profections": "phase0.1.0",
    "lots": "phase0.1.0",
    "zodiacal_releasing": "phase0.1.0"
  },
  "predictive_engine_formula_version": "predictive_v0.3.1",
  "transit_engine_version": "..."
}
```

### 2.4 `policy_versions`

Every policy artifact used during the run, versioned.

```json
{
  "predictive_object_schemas": "phase0.1.1",
  "asteroid_registry": "phase0.1.0",
  "method_charters": "phase0.1.0",
  "convergence_protocol": "phase0.1.0",
  "candidate_protocol": "phase0.1.0",
  "component_score_weights": "phase0.1.0",
  "detector_thresholds": "phase0.1.0"
}
```

### 2.5 `natal_promise_anchors`

Array of `NatalPromiseAnchor` records per [01_predictive_object_schemas.md](./01_predictive_object_schemas.md) §1.

### 2.6 `raw_events`

Array of `ForecastEvent` records per [01_predictive_object_schemas.md](./01_predictive_object_schemas.md) §2. Every event produced by every scanner is included, regardless of whether it entered a signal or a candidate.

### 2.7 `predictive_signals`

Array of `PredictiveSignal` records per §3. Every signal, even those that did not contribute to a candidate.

### 2.8 `daily_series`

Array of daily rows. **This is the primary Phase 1 delivery beyond what `engine/predictive_engine._build_daily_series()` currently produces.**

```json
[
  {
    "date": "2026-07-07",
    "raw_score": 0.0,
    "smooth_score": 0.0,
    "baseline_score": 0.0,
    "residual_score": 0.0,
    "structural_raw": 0.0,
    "trigger_raw": 0.0,
    "contributing_signal_ids": ["sig_...", "sig_..."],
    "contributing_event_ids": ["fe_...", "fe_..."],
    "structural_contributors": [{"signal_id": "sig_...", "strength": 0.0, "source_body": "Saturn"}],
    "trigger_contributors": [{"signal_id": "sig_...", "strength": 0.0, "source_body": "Mars"}]
  }
]
```

Rules:

- `contributing_signal_ids` is the union of all signal IDs whose `[start_date, end_date]` covers this day.
- `structural_contributors` and `trigger_contributors` are ordered by descending strength.
- `per_contributor_strength` fields are floats in `[0, 1]`.
- Days with zero contributors have empty arrays, not omitted fields.

### 2.9 `time_lord_periods`

Array of `TimeLordPeriod` per §6.

### 2.10 `chapters`

Array of `ChapterState` per §4.

### 2.11 `candidates`

Array of `MicroCandidate` per §5. Includes `pre_registered`, `active`, and `expired` states. `withheld` and `voided` states also included so the file is self-consistent for the outcome ledger.

### 2.12 `rejected_candidates`

**Critical Phase 1 deliverable.** Every peak or prospective candidate that did not become a `MicroCandidate` is recorded here with a machine-readable rejection reason.

```json
[
  {
    "rejection_id": "rej_<8-hex>",
    "candidate_date": "2026-08-15",
    "peak_date": "2026-08-15T00:00:00Z",
    "residual": 0.12,
    "prominence": 0.03,
    "candidate_width_days": null,
    "candidate_width_note": "Null because the peak was rejected before a trigger-derived window could be constructed. When a rejection occurs after window construction, this field carries the natural (non-fixed) width that was computed.",
    "filter_reason": "insufficient_method_family_diversity",
    "requirement_that_failed": "|independent_method_families| >= 2",
    "merged_into": null,
    "suppressed_by": null,
    "signal_ids_considered": ["sig_...", "sig_..."],
    "method_families_present": ["transit_family"],
    "anchor_ids_considered": ["npa_..."],
    "notes": ""
  }
]
```

`filter_reason` values (locked enum):

- `residual_below_min` — peak's `residual_score` below the detector threshold.
- `prominence_below_min` — peak's prominence below `_MIN_PROMINENCE`.
- `distance_too_close` — peak too close to a higher-prominence peak.
- `no_natal_anchor_match` — no `NatalPromiseAnchor` matched.
- `no_chapter_support` — no long-clock or sustained transit support.
- `no_trigger_support` — no signal with `signal_role = trigger_evidence`.
- `insufficient_method_family_diversity` — `|independent_method_families| < 2`.
- `coherence_graph_disconnected` — topic-coherence graph not a single connected component.
- `anti_double_counting_violation` — dedup collapsed families below the threshold.
- `confidence_withheld` — birth-time dependency + `hard` angle involvement.
- `voided_calculation_error` — a calculation error was found post-emission.
- `superseded_by_later_candidate` — merged into a later, higher-scoring candidate.
- `other` — with a documented `notes` field.

### 2.13 `convergence_composition`

Per-candidate breakdown of the convergence-graph structure.

```json
[
  {
    "candidate_id": "cand_...",
    "coherence_graph": {
      "nodes": ["sig_...", "sig_..."],
      "edges": [{"from": "sig_...", "to": "sig_...", "rule": "shared_anchor"}]
    },
    "independence_group_composition": {"transit_family": 3, "return_family_solar": 1, "profection_family": 1},
    "method_family_dedup_trace": [
      {"collapsed_pair": ["transit_family:Uranus:Sun", "proprietary_transit_family:Uranus:Sun"], "reason": "composite_key_match"}
    ]
  }
]
```

### 2.14 `detector_thresholds`

Snapshot of every threshold that governed detection during this run. Enables reproducibility even if defaults change later.

```json
{
  "predictive_engine": {
    "_MIN_PROMINENCE": 0.05,
    "_MIN_PEAK_DISTANCE": 14,
    "_BASELINE_WINDOW_DAYS": 35,
    "_SMOOTH_WINDOW_DAYS": 7,
    "_MEMORY_DECAY_YEARS": 1.5,
    "_FSM_EXACTNESS_THRESHOLD": 0.5,
    "_TRANSIT_ORB": { ... full table ... },
    "_PLANET_WEIGHT": { ... },
    "_TARGET_RELEVANCE": { ... }
  },
  "transit_engine": {
    "_REFINE_TOLERANCE": 0.01,
    "_BISECT_MAX_ITER": 53,
    "_CYCLE_MERGE_GAP": 120,
    "TRANSIT_ORB": { ... },
    "PLANET_SIGNIFICANCE": { ... },
    "DAILY_ACTIVATION_ORB": { ... }
  },
  "candidate_protocol": {
    "window_rule": "trigger_derived_no_fixed_maximum",
    "sandbox_research_cap_days": 6.0,
    "sandbox_research_cap_applies_to_this_run": false,
    "component_score_weights": { ... },
    "window_width_reference_scale_days": 3.0,
    "minimum_method_family_diversity": 2
  }
}
```

### 2.15 `asteroid_diagnostics`

Per-run asteroid summary.

```json
{
  "asteroid_registry_version": "phase0.1.0",
  "asteroids_present": ["Kassandra", "..."],
  "asteroids_absent": [],
  "ephemeris_missing": [],
  "asteroids_active_as_target": ["Kassandra"],
  "asteroids_active_as_source": ["Chaos", "Hermes"],
  "asteroid_events_count": 0,
  "asteroid_signals_count": 0,
  "per_asteroid_contact_counts": {"Kassandra": 0, "Aletheia": 0}
}
```

### 2.16 `debug`

Free-form dictionary. Not schema-validated. Signal-count, warnings, timing-per-scanner, per-scanner exceptions caught, whatever the engine wants to record for R&D.

Existing predictive engine `debug` dict (from `_collect_transit_signals`, `_build_daily_series`, `_detect_windows`) is embedded here under `debug.predictive_engine`.

### 2.17 `provenance`

```json
{
  "scanner_versions": {
    "scan_transit_windows": "...",
    "scan_house_ingresses": "...",
    "scan_stations": "...",
    "scan_eclipses": "...",
    "scan_lunations": "...",
    "scan_proprietary_forecast_windows": "..."
  },
  "sidecar_writer_version": "phase1.x.y",
  "sidecar_written_at": "2026-07-07T12:34:56Z"
}
```

## 3. `<report_id>.eo_outcomes.json` — outcome ledger

Written *after* review, not by the engine.

```json
{
  "outcome_ledger_version": "phase0.1.0",
  "sidecar_reference": "<report_id>.eo_predictive.json",
  "sidecar_natal_snapshot_id": "natal_...",
  "sidecar_report_run_id": "run_...",
  "outcomes": [
    {
      "outcome_id": "out_<8-hex>",
      "candidate_id": "cand_...",
      "report_run_id": "run_...",
      "chart_id": "natal_...",
      "research_subject": "notable partnership shift in 2026",
      "candidate_window": ["2026-08-15T00:00:00Z", "2026-08-21T00:00:00Z"],
      "candidate_domain": ["partnership"],
      "pre_registered_evidence": { ... copy of candidate at emission ... },
      "chronology_source": "querent_journal_shared_2026-09-01",
      "chronology_source_timestamp": "2026-08-30T00:00:00Z",
      "outcome_category": "supported_hit",
      "event_date": "2026-08-18",
      "match_precision": "within_window",
      "research_completeness": "full",
      "domain_mismatch": false,
      "non_hit_rationale": "",
      "unresolved_rationale": "",
      "reviewer_id": "rev_ab",
      "reviewed_at": "2026-09-05T18:00:00Z",
      "blind_review_status": "partially_blind"
    }
  ],
  "matched_random_baseline": {
    "baseline_id": "base_...",
    "generation_procedure": "...",
    "baseline_outcomes": [ ... same shape ... ]
  },
  "aggregation_notes": ""
}
```

Rules:

- `pre_registered_evidence` is copied from the sidecar so the outcome file is self-contained for external review.
- `matched_random_baseline` is required per [05_validation_protocol.md](./05_validation_protocol.md) §5.10.

## 4. Write policy

- **Atomic writes.** Sidecar is written via temp-file + rename to prevent partial writes on interruption.
- **Sidecar is write-once per run.** Re-running the same report produces a *new* sidecar; the previous sidecar is not modified. Old sidecars are retained under their `report_run_id`.
- **Outcome ledger is append-only per candidate.** Re-coding an outcome creates a new outcome entry with a new `outcome_id`; the previous entry is retained. This preserves review history for validation audits.
- **No sensitive fields in sidecar beyond what's already in `manifest.json`.** Since the manifest already carries querent PII for local operator use, the sidecar follows the same policy. For any future partner-facing surface, PII redaction is a separate concern.

## 5. Size and performance considerations

- Sidecars for a 1-year report window are estimated at 100 KB – 5 MB depending on chart activity and asteroid participation.
- No streaming write required; sidecar is emitted after the report generation completes.
- Sidecar validation should be lazy: schema violations are logged but do not block report delivery. The manifest remains authoritative for delivery.

## 6. Backward compatibility

- The existing `manifest.json` schema is unchanged.
- The existing HTML report is unchanged.
- Consumers of `predictive_results` in-memory (e.g. `predictive_sandbox` template) can continue to read from context; the sidecar is an additional serialization, not a replacement.

## 7. Locked at Phase 0

- Two-file model: sidecar + outcome ledger, separate.
- Sidecar top-level shape (§2 fields).
- Rejected-candidate `filter_reason` enum (§2.12).
- Daily provenance requirement (§2.8).
- Detector-threshold snapshot requirement (§2.14).
- Deterministic `natal_snapshot_id` and `candidate_id` (§2.2, [04](./04_convergence_and_candidate_protocol.md) §4.4).
- `natal_snapshot.lots` as the canonical home for computed Lot of Fortune / Spirit / Necessity positions (§2.2, added in `phase0.1.1`).

Any change requires a new sidecar version.
