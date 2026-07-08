# Engine Capability Surface Audit

Read-only architectural diagnostic for `C:\entangled_oracle`, performed from code inspection on 2026-07-07. Source files were not modified.

## 1. Executive Findings

The engine already contains meaningful analytical complexity, but only part of it is fully surfaced. The strongest fully surfaced surfaces are the Year Ahead / Personal Forecast event timeline, ordinary timing ledger, monthly intensity shaping, and the dedicated `predictive_sandbox` diagnostic page. The predictive sandbox itself calculates richer structures than the consumer reports currently use: signal normalization, baseline/residual daily series, peak prominence, structural-vs-trigger signal separation, semantic operation profiles, coherence, polarity/counterforce/complexity, epistemic confidence, and episode memory/FSM state.

The three largest information-loss points are:

1. `predictive_results` is computed for `year_ahead`, `personal_forecast`, and `predictive_sandbox`, but only `_build_predictive_sandbox_context()` transforms it into visible fields. Year Ahead and Personal Forecast carry it in context without rendering or manifesting it as predictive evidence.
2. Daily predictive evidence is preserved as daily scalar rows, but per-day contributing signal IDs are not preserved. After `_build_daily_series()`, the system can show raw/smooth/baseline/residual/structural/trigger values, but not exact per-day provenance without reconstructing overlap from signal dates.
3. The manifest records methodology, versions, active modules, and report-surface trace, but not `predictive_results`, the raw Year Ahead timeline, or the full predictive evidence needed for independent retrospective validation.

The current primary limitation is a combination of detector, pipeline, schema, interpretation, presentation, and validation limitations, not a simple engine limitation. The predictive engine can already produce localized windows and rich diagnostic attributes. Consumer-facing outputs mostly do not interpret or expose those attributes, and exports do not preserve enough evidence for later validation.

The codebase does contain latent predictive-analysis capability not yet exposed. High-confidence examples include local spike detection, trigger-vs-background separation, rank-based window prioritization through prominence/distance filtering, signal-convergence semantics, confidence scaffolding, and feature provenance at signal/window level. Returns, Solar Arc, progressions, directions, profections, time lords, and zodiacal releasing should not be claimed as implemented predictive clocks; current evidence shows taxonomy/config/planning hooks, not normal scanners.

## 2. System Architecture Map

| Layer | Files / Entry Points | Inputs | Outputs | Downstream Consumers |
| --- | --- | --- | --- | --- |
| Birth data and chart acquisition | `generate.py:181-221`, `engine/natal_engine.py:336`, `engine/natal_engine.py:154-223` | CLI/user birth data; location; timezone; Swiss Ephemeris | Natal payload with bodies, angles, houses, retrograde flags, aspects | Formula engines, transit scanners, report contexts |
| Standard / EO formula indexes | `formulas/proprietary_indexes.py:1077`, `formulas/report_surface.py:461-537`, `selectors/variable_resolver.py:142` | Natal payload, report type, standard bundle | `index_results`, `standard_report_bundle`, flattened variables, routing trace | Report builders; predictive leading-index fallback; manifest |
| Forecast event scanning | `engine/transit_engine.py:2267-2343` | Natal payload, report window | `transits`, `ingresses`, `stations`, `eclipses`, `lunations`, `all_events` | Year Ahead, Personal Forecast, Predictive Sandbox signal collection |
| Transit cycle detection | `engine/transit_engine.py:1452-1578`, `_finalize_transit_event()` at `1396-1438` | Natal targets, transit planet states, orb tables, activation profile | Refined cycle events with entry/peak/leave, contacts, score, duration, motion | Year Ahead event cards, ledger, Personal Forecast themes, predictive signals |
| Daily timeline detection | `engine/transit_engine.py:1297-1390` | Natal payload, day/window range | Top exact daily activation moments with UTC peak, orb, score | Weekly horoscope; potentially R&D, but not predictive sandbox detector |
| Predictive signal extraction | `engine/predictive_engine.py:264-331`, `336-459` | Year Ahead event timeline, birth-time status | Normalized signals with strength, method family, operation profile, confidence | Daily series, window detection, sandbox signal table |
| Daily predictive series | `engine/predictive_engine.py:464-521` | Predictive signals | Daily `raw_score`, `smooth_score`, `baseline_score`, `residual_score`, `structural_raw`, `trigger_raw` | Window detector; sandbox daily table |
| Predictive window segmentation | `engine/predictive_engine.py:555-689` | Daily series, signals, index results | Windows with start/peak/end, local peak, structural field, prominence, gradient, active signals, semantics, memory | Sandbox context and block routing |
| Predictive narrative preview | `generate.py:7736-7773`, `7776-7824`, `7827-7973` | Predictive windows/signals/daily series, JSON block registry | `predictions`, diagnostic `windows`, `signals`, `daily_series`, debug | `products/predictive_sandbox/templates/predictive_sandbox.html` only |
| Personal Forecast assembly | `generate.py:737-1048` | 90-day `compute_year_ahead_events()`, blocks, optional VOC/retrograde detectors | Theme cards, timing windows, JSON timeline string, raw `predictive_results` passthrough | `products/personal_forecast/templates/personal_forecast.html` |
| Year Ahead assembly | `generate.py:7236-7722` | 12-month event timeline, convergence detector, monthly scoring, blocks | Months, landmarks, forecast shape, climate, raw cycle ledger, calculation record, raw `predictive_results` passthrough | `products/year_ahead/templates/active/year_ahead.html` |
| Export / manifest | `generate.py:3444-3525` | Payload, context, versions, surface trace | HTML report plus `.manifest.json` | Operator/package review; does not include predictive evidence |
| Debug / validation tooling | `products/predictive_sandbox/templates/predictive_sandbox.html:346-423`, `tools/extract_sandbox_ledger.py:6-110`, tests | Rendered sandbox HTML or unit fixtures | Debug rows, CSV extraction, regression assertions | Developer QA only |

## 3. Capability Inventory

| Capability / Signal | Where Calculated | Inputs | Stored After Calculation? | Used by Detector? | Used by Interpretation? | Exported? | Client-Facing? | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Transit cycle events | `engine/transit_engine.py:1452-1578`, `1396-1438` | Natal targets, transit planets, aspects, orb, duration | Yes, as event dicts in `compute_year_ahead_events()` | Indirectly, converted to predictive signals | Yes in Year Ahead / Personal Forecast | Partly in manifest only by rendered output/version; not raw event JSON | Yes | Fully surfaced | `compute_year_ahead_events()` returns `transits` and `all_events` at `2267-2343`; Year Ahead ledger at `5563-5714` |
| Ingress events | `engine/transit_engine.py:1584+`, `2267-2343` | Ascendant, whole-sign house boundaries, planet states | Yes | Converted to signals as TRANSIT/INGRESS | Yes | No raw export | Yes | Fully surfaced | `compute_year_ahead_events()` includes `ingresses`; ledger includes house ingresses at `5590-5592` |
| Station events | `engine/transit_engine.py:1681+`, `2267-2343` | Planet speed changes, activation profile | Yes | Converted to signals as TRANSIT/STATION when peak datetime present | Yes | No raw export | Yes | Fully surfaced | Year Ahead/Personal Forecast count and template use; ledger station branch `5654-5671` |
| Eclipse events | `engine/transit_engine.py:2015+`, `2267-2343` | Swiss Ephemeris eclipse events, natal contacts/houses | Yes | Converted to LUNATION/ECLIPSE signals | Yes | No raw export | Yes | Fully surfaced | Eclipse scanner returned in `compute_year_ahead_events()`; ledger branch `5672-5695` |
| Lunation events | `engine/transit_engine.py:2181+`, `2267-2343` | New/full moon scan; eclipse-date suppression | Yes | Converted to LUNATION signals | Yes in ledger and related logic | No raw export | Yes in Year Ahead ledger | Fully surfaced | `scan_lunations()` called with `eclipse_events` at `2310-2316`; tests cover duplicate suppression |
| Daily horoscope / weekly exact moments | `engine/transit_engine.py:1297-1390` | Fast Moon scan plus rare slow-planet interior peaks | Yes, returned as list | No, separate from predictive sandbox detector | Yes in weekly context | No independent JSON export found | Yes in weekly outputs | Fully surfaced | Function returns top scored exact moments; `generate.py:1128-1179` assembles weekly timeline |
| Personal Forecast themes | `generate.py:454-493`, `737-1048` | `all_events`, theme map, event scores, block library | Yes, as `theme_cards` | No | Yes | Timeline JSON embedded in context, not separate export | Yes | Fully surfaced | Themes/timing windows returned at `1023-1048` and rendered in template |
| Year Ahead monthly arc score | `generate.py:3026-3070`, `7426-7514` | Active events, `combined_intensity_score`, local timing weight | Yes, as month `arc_score` and display fields | No predictive window detector use | Yes | In rendered HTML, not manifest raw data | Yes | Fully surfaced | Month records store `arc_score`, `arc_label`, `events` at `7487-7514` |
| Forecast shape | `generate.py:3168+`, `7612-7617`, template `1725-1752` | Month arc scores and birth-time status | Yes | No | Yes | Rendered only | Yes | Fully surfaced | `forecast_shape_details` added to context and rendered |
| Raw Cycle Ledger | `generate.py:5563-5714`, template `2187-2310` | Raw Year Ahead source events | Yes, report-safe subset | No | Yes as technical registry | Rendered only | Yes | Fully surfaced | Contract preserves merged cycles/contacts but excludes internals |
| Predictive raw signal strength | `engine/predictive_engine.py:366-459` | Event exactness, planet weight, target relevance, structural/theme modifiers | Yes, in `signals` | Yes, summed into daily series | Sandbox only | Sandbox HTML only; no manifest | Dev-facing only | Engine-only | `signals` returned at `323-330`; context forwards at `7845-7869` |
| Method family / event kind / independence group | `engine/predictive_engine.py:412-422`, `876-965` | Event type, target | Yes, on signals | Indirect via memory method weight; not segmentation threshold | Sandbox block routing via derived window method family | Sandbox HTML only | Dev-facing only | Partially wired | Window method is derived in `generate.py:7872-7890`; method clocks for returns/progressions are hooks only |
| Operation profile / dominant operation | `engine/predictive_engine.py:998-1022` | Source body, target substrate, aspect family, method family, magnitude | Yes, on signal and aggregated to window | Not used to segment windows | Yes in sandbox narrative routing/tags | Sandbox HTML only | Dev-facing only | Partially wired | Signal fields forwarded `7863-7865`; window fields at `7912-7915` |
| Epistemic confidence | `engine/predictive_engine.py:1025-1114` | Birth-time status, angle eligibility, exactness, allowed orb, uncertainty heuristic | Yes, on signal | No | Shown in sandbox signal table; not narrative logic found | Sandbox HTML only | Dev-facing only | Partially wired | Signal context includes confidence fields `7859-7862` |
| Daily predictive raw/smooth/baseline/residual | `engine/predictive_engine.py:464-521` | Active signals per day | Yes, in `daily_series` | Yes, residual drives peak detection | Sandbox table only | Sandbox HTML only | Dev-facing only | Partially wired | `daily_series` returned `327-329` and forwarded `7932-7942` |
| Structural vs trigger split | `engine/predictive_engine.py:486-504`, `629-635` | Source body class | Yes, daily `structural_raw`/`trigger_raw` and window signal ID lists | Indirect through baseline/residual; not as independent detector lanes | Sandbox only | Sandbox HTML only | Dev-facing only | Partially wired | Window lists at `672-674`; template displays counts/IDs at `486-514` |
| Local peak intensity | `engine/predictive_engine.py:625-627`, `657-667` | Residual at peak index | Yes, on window | It is the detector peak value | Sandbox only | Sandbox HTML only | Dev-facing only | Partially wired | Template displays at `441-467` |
| Structural field intensity | `engine/predictive_engine.py:625-627`, `657-667` | Baseline at peak index | Yes, on window | Used as total context, not peak qualification | Sandbox only | Sandbox HTML only | Dev-facing only | Partially wired | Stored as `structural_field_intensity`; template displays it |
| Total intensity | `engine/predictive_engine.py:625-667` | Smooth score at peak | Yes | Indirect as descriptive value, not primary residual detector | Sandbox and legacy intensity compatibility | Sandbox HTML only | Dev-facing only | Partially wired | `intensity` backward compat at `666` |
| Peak prominence | `engine/predictive_engine.py:585-601`, `710-760` | Residual peaks | Yes, on window and debug counts | Yes, filters qualified peaks | Sandbox only | Sandbox HTML only | Dev-facing only | Partially wired | `_MIN_PROMINENCE` filter and template column |
| Gradient | `engine/predictive_engine.py:637-647` | Peak position inside detected window | Yes | No; computed after segmentation | Sandbox block routing/narrative and memory route | Sandbox HTML only | Dev-facing only | Partially wired | `_predictive_window_narrative()` matches conditions at `7791-7801` |
| Leading index | `engine/predictive_engine.py:840-873` | Active signals plus EAS index fallback | Yes | No | Sandbox narrative dimension fallback | Sandbox HTML only | Dev-facing only | Partially wired | `leading_index` stored at `670` and displayed |
| Window semantic coherence/profile/state | `engine/predictive_engine.py:1132-1228` | Active signal operation profiles and confidence | Yes | No | Sandbox table/tags/block conditions | Sandbox HTML only | Dev-facing only | Partially wired | Window fields `676-680`; template semantic columns `447-475` |
| Polarity / coalition / counterforce / complexity | `engine/predictive_engine.py:1181-1227` | Aggregated operation masses | Yes, inside `semantic_diagnostics` | No | Sandbox table; block routing can use exposed window keys only if present | Sandbox HTML only | Dev-facing only | Partially wired | Diagnostics stored at `1217-1227`, displayed at `472-475` |
| Episode memory / pass state / lifecycle route | `engine/predictive_engine.py:1231-1398` | Activation key, related signal history, decay, FSM, gradient | Yes | No | Sandbox table/tags/block routing | Sandbox HTML only | Dev-facing only | Partially wired | Window fields `681-685`; context forwards `7916-7921` |
| Predictive JSON block library | `generate.py:7736-7773`, `7776-7824` | Flat JSON entries with conditions | Yes, registry cached | No | Yes for sandbox narrative preview | Rendered only | Dev-facing only | Partially wired | Active folders listed at `7743`; selection uses condition count |
| Predictive debug counters | `engine/predictive_engine.py:579-609`, `320-321`; template `346-423` | Signal collection and detector internals | Yes, debug dict | No | Debug display only | Sandbox HTML only | Dev-facing only | Debug-only | Debug rows render raw count, peak filters, parameters |
| Report manifest | `generate.py:3444-3525` | Context, payload, versions, trace | Yes, `.manifest.json` | No | Operator trace only | Yes | Operator-facing | Partially wired | Manifest lacks `predictive_results`/raw timeline evidence |
| Returns / Solar Arc / progressions | `engine/predictive_engine.py:121-128`, `175-181`, `876-965` | None from normal scanners found | Only config/taxonomy hooks | No normal detector path found | No | No | No | Configuration-only | Search found method family hooks but no scanners; repo notes say not implemented |
| Profections / time lords / zodiacal releasing | Repo search | No executable implementation found | No | No | No | No | No | Configuration-only | Search found no normal implementation |
| Legacy convergence detector | `generate.py:6842-6966` | Events and convergence blocks | Function name includes `legacy_dead` | No evidence of normal call | No normal use found | No | No | Dead / unreachable | Active detector is `_detect_and_frame_convergences()` at `6966+`; legacy function appears superseded |

## 4. Latent Capability Findings

### High-confidence latent capabilities

- Localized spike detection exists. `_detect_windows()` uses residual local maxima, peak prominence, minimum distance, zero-crossings, and valleys (`engine/predictive_engine.py:555-689`). This is more precise than broad annual weather, but only the sandbox exposes it.
- Trigger-versus-background separation exists. `_build_daily_series()` separates `structural_raw` from `trigger_raw`, and windows preserve slow/fast active signal ID lists (`engine/predictive_engine.py:486-504`, `629-674`).
- Signal convergence semantics exist. Operation profiles, dominant operations, coherence, polarity, coalition, counterforce, and complexity are computed (`engine/predictive_engine.py:998-1228`) and survive into sandbox windows.
- Confidence/provenance scaffolding exists. Signals carry confidence components and angle-eligibility state (`engine/predictive_engine.py:1025-1114`) and sandbox context forwards them (`generate.py:7859-7865`).
- Episode continuity exists. Memory charge and FSM pass state are computed (`engine/predictive_engine.py:1231-1398`) and forwarded (`generate.py:7916-7921`).
- Year Ahead already has independent report-safe event provenance through the Cycle Ledger (`generate.py:5563-5714`), but it is separate from predictive sandbox evidence.

### Plausible partial capabilities requiring verification

- Micro-window extraction: daily residual peaks and exact daily timeline moments exist, but the predictive detector enforces `_MIN_PEAK_DISTANCE = 14` and creates windows from residual crossings/valleys. Narrower micro-windows are implied by upstream daily data, not currently assembled as first-class outputs.
- Broad weather/chapter detection: the baseline and structural field are calculated, but the detector intentionally looks for residual spikes. Baseline chapters are visible as diagnostics, not their own window type.
- Independent validation exports: sandbox tables and `tools/extract_sandbox_ledger.py` can extract rendered windows to CSV, but no first-class raw JSON/CSV validation export preserves full signals, daily provenance, and windows together.
- Event-type specificity: event kind and method family exist for transit/station/ingress/eclipse/lunation; returns/progressions/Solar Arc are only taxonomy-ready.

### Apparent dead or abandoned structures

- `_detect_and_frame_convergences_legacy_dead()` appears superseded by `_detect_and_frame_convergences()` and is named accordingly (`generate.py:6842-6966` vs active detector at `6966+`).
- `RETURN`, `PROGRESSION`, and `SOLAR_ARC` predictive method handling exists only as downstream taxonomy/config in the inspected path, not as scanners that feed `compute_year_ahead_events()`.
- Some predictive block conditions may route on fields that are only derived in sandbox context, not native window fields. `method_family` is derived per window from active signal IDs in `generate.py:7872-7890`.

### Important unknowns

- No live generation was run for this audit, so this file does not claim current output samples or counts for any specific chart.
- The exact breadth of content-block routing coverage was not exhaustively audited; the audit verifies loader shape and route mechanism, not every block condition combination.
- The manifest/export story may have adjacent scripts outside normal generation, but no first-class predictive JSON export was found in the inspected normal path.

## 5. Information-Loss Map

| Upstream richness | Loss point | Downstream consequence | Likely nature | Confidence |
| --- | --- | --- | --- | --- |
| Full `predictive_results`: signals, daily series, windows, debug | Year Ahead and Personal Forecast contexts include raw `predictive_results` but templates do not render it | Consumer reports cannot show predictive-window evidence despite the engine calculating it | Intentional / staging | High |
| Per-signal active overlap per day | `_build_daily_series()` stores daily scalar sums but not contributing signal IDs per day | Later validation cannot directly explain why a daily value spiked without reconstructing overlaps | Schema limitation | High |
| Residual local maxima before filters | `_detect_windows()` stores debug counts, but not rejected peak indices/prominences | R&D cannot inspect false positives/near misses from normal output | Validation limitation | High |
| Structural baseline field across year | Window object stores baseline only at peak date | Broad chapters are not first-class segments | Detector/schema limitation | Medium |
| Signal operation profile and confidence | Aggregated to window semantic profile and limited table display | Prose cannot explain which signal carried which operation/confidence without signal-table inspection | Interpretation limitation | Medium |
| Active raw Year Ahead event records | `_build_raw_cycle_ledger()` intentionally produces report-safe subset | Client sees technical provenance but not full raw scoring/selection state | Intentional presentation limitation | High |
| Context-level `predictive_results` | `_write_report_manifest()` omits it | Manifest cannot support retrospective predictive validation | Validation/schema limitation | High |
| Convergence synthetic objects | Convergence windows get `combined_intensity_score: 0.0` | They can be visible as structural overlays but not intensity-ranked like ordinary events | Intentional / unclear | Medium |
| Predictive sandbox rendered HTML tables | `tools/extract_sandbox_ledger.py` scrapes rendered HTML, not raw engine output | CSV extraction is brittle and loses non-rendered fields | Tooling limitation | Medium |

## 6. Predictive Sandbox Diagnostic

What inputs create a predictive window?

`generate_report()` calls `compute_predictive_windows()` for `year_ahead`, `personal_forecast`, and `predictive_sandbox` (`generate.py:224-245`). The predictive engine calls `compute_year_ahead_events()` (`engine/predictive_engine.py:336-353`), converts returned events to normalized signals (`366-459`), builds a daily series (`464-521`), and detects windows from residual peaks (`555-689`).

Are daily values retained after window construction?

Yes. `compute_predictive_windows()` returns `daily_series` alongside `windows` and `signals` (`engine/predictive_engine.py:323-330`). `_build_predictive_sandbox_context()` forwards daily rows with raw, smooth, baseline, residual, structural, and trigger values (`generate.py:7932-7942`). Daily rows are not rendered in consumer reports.

Are local spikes distinguishable from structural field activity?

Yes in the sandbox data model. `local_peak_intensity` comes from residual at the peak, `structural_field_intensity` comes from baseline at the peak, and `total_intensity` comes from smooth score (`engine/predictive_engine.py:625-667`). Daily rows also keep `structural_raw` and `trigger_raw`.

Is prominence actually used to localize periods, or merely exported?

It is used by the detector. Peaks below `_MIN_PROMINENCE` are discarded (`engine/predictive_engine.py:585-598`), and minimum inter-peak distance is enforced after prominence ranking (`600-609`). Prominence is also exported to the sandbox window table.

Are there calculations capable of producing narrow micro-windows that current segmentation suppresses?

Partially. The residual series and local maxima can identify daily peaks, and `compute_daily_timeline()` can find exact intra-day activation moments (`engine/transit_engine.py:1297-1390`). But predictive segmentation enforces a 14-day minimum peak distance and derives window boundaries from residual crossings/valleys (`engine/predictive_engine.py:600-635`, `786-835`). That means micro-window ingredients exist, but no first-class predictive micro-window output is assembled.

Are multiple signal types collapsed before they can be independently inspected?

Partially. Signal records survive in `signals`, and windows retain active signal IDs plus slow/fast splits. But the daily series collapses per-day contributors into scalar totals, so daily provenance is not preserved directly. Also `method_family` is signal-level only and is derived as a representative window field later in sandbox context (`generate.py:7872-7890`).

Does the report/export layer preserve enough evidence to validate a claimed window later?

Only in the sandbox HTML, and only partially. The normal manifest records methodology, versions, trace summaries, and routing metadata (`generate.py:3444-3525`), but it does not include predictive signals, daily rows, rejected peaks, or full raw event records. `tools/extract_sandbox_ledger.py` can scrape rendered sandbox windows, but that is not a durable raw validation export.

What existing data could support stricter R&D tests without altering the astronomical calculation layer?

- `signals` with source body, target, aspect, exactness, strength, method family, operation profile, confidence, and active dates.
- `daily_series` with raw/smooth/baseline/residual/structural/trigger daily values.
- `windows` with start/peak/end, prominence, local peak, structural field, total intensity, active signal IDs, semantics, memory, and tags.
- `debug` peak counts and algorithm parameters.
- Year Ahead `all_events` and `raw_cycle_ledger` event provenance.

## 7. Output-Surface Opportunities

| Existing capability | Existing source | Missing connection | Likely output location | Task type | Confidence |
| --- | --- | --- | --- | --- | --- |
| Predictive evidence appendix | `variables["predictive_results"]` in `generate.py:245`, Year Ahead context key at `7706` | Template section and/or manifest field | Year Ahead appendix or operator manifest | Schema + presentation | High |
| Predictive validation JSON | `compute_predictive_windows()` return contract | Dedicated JSON writer preserving signals/daily/windows/debug | Sidecar file next to HTML/manifest | Schema + validation | High |
| Rejected peak diagnostics | `_detect_windows()` intermediate peaks/prominences | Store rejected peaks in debug or validation export | Sandbox debug / JSON export | Detector + validation | High |
| Per-day signal provenance | `_build_daily_series()` overlap loop | Preserve contributing signal IDs and split strengths per day | JSON export; optional sandbox detail table | Schema + validation | Medium |
| Micro-window candidates | Residual local maxima; `compute_daily_timeline()` exact moments | First-class candidate output distinct from main windows | Sandbox R&D panel | Detector + schema | Medium |
| Window semantic explanation | `semantic_profile`, `semantic_diagnostics`, signal operation profiles | Narrative/template mapper outside sandbox | Sandbox prose first; later report appendix | Interpretation | Medium |
| Confidence-aware filtering/display | `epistemic_confidence`, `angle_eligibility` | Consumer-safe labels and manifest summary | Method appendix / validation export | Interpretation + presentation | Medium |
| Broad structural chapter view | `baseline_score`, `structural_field_intensity`, slow signal IDs | Segment baseline field independently from residual windows | Sandbox R&D view | Detector + schema | Medium |

## 8. Recommended Investigation Order

1. Inspect actual rendered `predictive_sandbox` output for one known test chart and compare `signals`, `daily_series`, `windows`, and debug counts against the code contract.
2. Trace `predictive_results` through Year Ahead and Personal Forecast templates to confirm all current non-use points and decide whether it belongs in a report appendix, manifest, or R&D-only sidecar.
3. Audit whether `daily_series` should preserve per-day contributing signal IDs and rejected peak candidates for validation without altering astronomical calculations.
4. Inspect all active `products/predictive_sandbox/blocks/*/*.json` conditions against `_build_predictive_sandbox_context()` window fields to find unreachable or over-broad narrative routes.
5. Review manifest requirements for R&D: determine whether predictive evidence belongs in `.manifest.json`, a separate `.predictive.json`, or both.

## 9. Evidence Appendix

Commands run:

```powershell
rg --files
rg -n "predictive|window|daily|score|intensity|prominence|gradient|baseline|threshold|segment|transit|lunation|return|progression|direction|profection|time lord|zodiacal|export|debug|validation|schema|serializer|TODO" -S .
rg -n "compute_daily_timeline|scan_transit_windows|detect_void|scan_stations|eclipse|year_ahead|_build_year_ahead|forecast_shape|raw_cycle|ledger|transit_trace|EO_TRANSIT_TRACE|write_report_output|generate_report_data" generate.py engine\transit_engine.py tests\test_transit_cycles.py products\year_ahead\templates\active\year_ahead.html
rg -n "def .*return|event_type.*return|progression|solar_arc|direction|profection|time_lord|zodiacal|return_clock|progression_clock|solar_arc_clock|primary direction|secondary progression|zodiacal releasing" -S engine generate.py formulas selectors tests products\predictive_sandbox agents\PLANNED_UPDATES.md agents\REVISIONS.md
rg -n "predictive_results|timeline_data_json|raw_cycle_ledger|forecast_shape|calculation_record|retrograde_cluster|voc_next|timing_windows" products\personal_forecast\templates\personal_forecast.html products\year_ahead\templates\active\year_ahead.html products\predictive_sandbox\templates\predictive_sandbox.html
git status --short
```

Important evidence references:

- Predictive engine return contract: `engine/predictive_engine.py:264-331`
- Signal conversion: `engine/predictive_engine.py:366-459`
- Daily series: `engine/predictive_engine.py:464-521`
- Window detection: `engine/predictive_engine.py:555-689`
- Prominence helpers: `engine/predictive_engine.py:710-760`
- Semantic metrics: `engine/predictive_engine.py:998-1228`
- Memory/FSM: `engine/predictive_engine.py:1231-1398`
- Predictive integration in generator: `generate.py:224-245`
- Predictive sandbox context: `generate.py:7827-7973`
- Predictive sandbox template: `products/predictive_sandbox/templates/predictive_sandbox.html:286-520`
- Forecast event timeline: `engine/transit_engine.py:2267-2343`
- Daily exact timeline: `engine/transit_engine.py:1297-1390`
- Year Ahead monthly scoring: `generate.py:2978-3070`, `7426-7514`
- Raw Cycle Ledger: `generate.py:5563-5714`
- Manifest writer: `generate.py:3444-3525`
- Report surface bundle: `formulas/report_surface.py:433-537`

Unresolved traces:

- Exact rendered behavior was not sampled because this audit stayed code-inspection-first and avoided creating report outputs.
- The full active predictive block library was not exhaustively route-tested.
- Existing dirty worktree state was observed before audit artifact creation; unrelated modified/untracked files were not touched.
