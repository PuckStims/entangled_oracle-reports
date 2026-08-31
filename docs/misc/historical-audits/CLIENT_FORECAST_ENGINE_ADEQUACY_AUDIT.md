# Client Forecast Engine Adequacy Audit

Date: 2026-07-07  
Scope: read-only architectural diagnostic of the client-facing forecast surfaces in this repository.  
Explicit exclusion: `predictive_sandbox` is an engineering/validation surface and is not evaluated here as a client product.

## 1. Executive Answer

The client-facing forecast stack is real, but uneven across products.

`year_ahead` and `personal_forecast` have the strongest implemented forecasting substrate. They use Swiss Ephemeris-backed natal charts, transit/event scans, scoring, monthly or thematic selection, timing-window extraction, and rendered provenance. These products can honestly be described as reflective astrological forecast/planning reports. They should not be described as concrete external-event prediction engines, and they do not currently justify claims that methods such as progressions, solar arc, returns, profections, or time-lord systems are active client-facing forecast inputs.

`daily_horoscope` is individualized in a lighter way: it routes authored daily prose from live Moon phase/sign, day ruler, and a same-day activation or fallback house signal. However, the daily resolver uses the system date at generation time rather than the requested `--report-date`, so reproducible historical/future daily generation is not adequate yet.

`weekly_horoscope` computes chart-specific exact timing moments for the week, but the client output is still mostly a technical timeline rather than an authored interpretive forecast. It is implemented, but under-explained and not yet a mature client narrative product.

`soul_ecosystem` should be treated as natal/context infrastructure for this audit, not as a forecast product.

Year Ahead is evaluated here as an exact-birth-time product only. Non-exact Year Ahead generation is out of commercial/client scope and should be disregarded rather than treated as a required product adequacy target.

## 2. Client Forecast Product Map

| Surface | Active client route | Forecast role | Audit disposition |
| --- | --- | --- | --- |
| Year Ahead | `generate.py --report-type year_ahead` | 12-month transit/event forecast with monthly chapters, climate, timing windows, and cycle ledger | Primary client forecast product |
| Personal Forecast | `generate.py --report-type personal_forecast` | 90-day transit/event forecast grouped into themes and timing windows | Primary client forecast product |
| Daily Horoscope | `generate.py --report-type horoscope` | Daily natalized sky/activation guidance | Active but lighter and date-control-limited |
| Weekly Horoscope | `generate.py --report-type weekly_horoscope` | Weekly chart-specific exact-contact timeline | Active but partial/under-authored |
| Soul Ecosystem | `generate.py --report-type soul_ecosystem` | Natal/context report, shared chart infrastructure | Not a forecast product except as context |
| Predictive Sandbox | `generate.py --report-type predictive_sandbox` | Engineering validation/research | Excluded by scope |

The active CLI exposes all of these report types, but active CLI availability is not the same thing as client-facing forecast adequacy.

## 3. Calculation and Method Inventory

| Method/component | Where it appears | Status | Notes |
| --- | --- | --- | --- |
| Natal chart calculation | Shared generation path and natal engine | Adequately implemented and represented | Tropical zodiac, Whole Sign houses, Swiss Ephemeris, location resolution, and calculation record are surfaced in the stronger reports. |
| Major natal transit cycles | Year Ahead, Personal Forecast | Adequately implemented and represented | `scan_transit_windows()` finds entry, exact, and exit windows, merges cycles, assigns duration and score, and reports timing. |
| Monthly relevance scoring | Year Ahead | Adequately implemented and represented | Monthly peak scoring weights peak, entry, leave, and continuing influence differently. This supports climate-style month ranking. |
| Event prioritization and filtering | Year Ahead, Personal Forecast | Adequately implemented and represented | Events are filtered by score and selected into monthly chapters or personal themes. |
| Forecast climate | Year Ahead | Implemented but under-explained | The output represents the result, but the weighting model is not fully transparent to a client reader. This is acceptable if framed as internal synthesis. |
| Convergence windows | Year Ahead | Implemented but under-explained | The detector looks for overlapping/proximate independently selected events. In samples, convergence events can display score `0.0`, so they should be framed as structural overlays rather than ranked intensity events. |
| House ingresses | Year Ahead, Personal Forecast | Adequately implemented and represented for exact-birth-time reports | Jupiter through Pluto house ingresses are scanned and scored. They depend on house/angle reliability, so this audit treats Year Ahead as exact-time-only. |
| Stations and retrogrades | Year Ahead, Personal Forecast | Adequately implemented and represented | Stations are detected by speed-zero refinement and proximity to natal targets; broader retrograde clusters are available for personal forecast climate. |
| Eclipses and lunations | Year Ahead, Personal Forecast | Adequately implemented and represented | Eclipses are included even without tight natal match at lower score; lunations require tighter natal contact. |
| Void-of-course Moon | Personal Forecast | Implemented but under-explained | Available as ambient climate context, not as a high-confidence personal prediction method. |
| Daily Moon phase/sign/day ruler | Daily Horoscope | Partially implemented | The calculations are active, but tied to actual current date rather than requested report date. |
| Daily activation transit | Daily Horoscope | Partially implemented | Same-day transit scan exists with fallback to Moon house. Date-control bug limits batch/replay adequacy. |
| Weekly exact-contact timeline | Weekly Horoscope | Implemented but under-explained | Contact detection works, but the output is sparse and ranking-first rather than clearly chronological. |
| Progressions | Client forecast output | Configuration-only / inactive | No evidence found that progressions drive current client-facing report output. |
| Solar arc directions | Client forecast output | Configuration-only / inactive | No evidence found that solar arc is active in current client-facing forecast output. |
| Returns | Client forecast output | Configuration-only / inactive | No evidence found that solar/lunar/planetary returns drive active client report output. |
| Profections/time lords | Client forecast output | Configuration-only / inactive | No evidence found that time-lord methods drive active client report output. |

## 4. Timing and Prediction-Resolution Audit

The implemented timing resolution is strongest for transit-style astrology, not for real-world event prediction.

Year Ahead scans long-range events across a one-year report window. Transit cycles are refined to entry, exact, and exit times, then translated into monthly relevance and visible timing windows. This is adequate for "months with stronger astrological emphasis", "active windows", and "themes peaking around date X." It is not adequate for "specific external event X will happen."

Personal Forecast uses a 90-day window from the report start. It reuses the event engine, then groups events into themes and selects a small set of visible timing windows. This is adequate for a concise 90-day symbolic planning report.

Daily Horoscope currently has a timing-control problem. A sample generated with `--report-date 2026-01-01` produced a displayed date of July 07, 2026 because the daily resolver uses `datetime.now()`. That means the daily product can be adequate for "today, generated now", but not for reproducible date-targeted daily reports.

Weekly Horoscope builds a Monday-Friday week window from the report date and computes exact contacts. The sample for `2026-01-01` produced a Dec 29, 2025-Jan 02, 2026 week, which matches the code's Monday-Friday windowing. However, the visible list is ranked by significance rather than displayed as a strict chronology, so the word "timeline" should be used carefully unless the presentation is adjusted.

## 5. Ranking, Selection, and Duplication Audit

Year Ahead event ranking is coherent. Raw events are sorted by peak date and score, monthly chapter events are filtered to keep non-transits and scored transits, and monthly peak scores use local relevance rather than only global event score. This supports month-by-month climate synthesis.

Personal Forecast ranking is coherent at the engine level. Themes are built from events above score threshold, anchors are chosen from highest-scoring theme events, and timing windows are selected with type bonuses and deduplication before chronological display.

Weekly Horoscope selection is coherent but potentially confusing. The engine selects top moments by score, and the template labels them as a timeline. In the sample, Jan 01 appeared before Dec 30 and Dec 29 because ranking outranked chronology. That is not necessarily wrong, but it is under-explained.

Daily Horoscope selection is simple and inspectable: station today, then highest same-day transit activation, then Moon-house fallback. The main issue is date source, not selection logic.

No major duplicate-output failure was observed in the generated samples. Related forecast events and convergence events can sit alongside ordinary transit events, so client copy should distinguish "overlay/synthesis" from "another independent event."

## 6. Prose-to-Evidence Trace Results

Sample reports were generated into `audit_output/client_forecast_samples` using artificial audit data and a fixed requested date of `2026-01-01`.

Year Ahead exact-time sample:

- Rendered 101 timeline events.
- January 2026 showed `arc_score 0.773`, labeled "Significant".
- Visible events included Jupiter square natal Vertex, Jupiter trine natal Pluto, and Pluto sextile natal Sun.
- Major timing windows corresponded to concrete event records with dates, event type, score, and cycle metadata.
- The calculation record surfaced exact birth time, resolved location, report window, methodology, Swiss Ephemeris, and report version.

Personal Forecast sample:

- Rendered 29 events across transits, ingresses, stations, eclipses, and one other event.
- Top themes had traceable anchors and supporting events.
- Timing windows mapped to actual event dates and event titles.
- The prose was theme-oriented and reflective, not a discrete-event claim.

Daily Horoscope sample:

- Requested report date was `2026-01-01`.
- Displayed date and sky state reflected July 07, 2026.
- This confirms the report-date control issue for the daily path.

Weekly Horoscope sample:

- Rendered 10 exact timing moments for the Dec 29, 2025-Jan 02, 2026 week.
- Items included date/time, transit, aspect, natal target, house, and aspect character.
- The output remained technical and sparse rather than fully interpreted.

## 7. Product-by-Product Adequacy Findings

### Year Ahead

Status: Adequately implemented and represented for exact-birth-time reflective forecasting.

The Year Ahead report is the most complete client forecast surface. It has a real event engine, monthly synthesis, visible timing windows, a raw cycle ledger, forecast shape language, and calculation record. The generated exact-time sample supports the visible prose and timing claims.

This finding assumes exact birth time is required for Year Ahead delivery. Non-exact Year Ahead reports are not part of the intended client-facing offer and do not need to be repaired unless that product policy changes.

### Personal Forecast

Status: Adequately implemented and represented, with minor presentation limitations.

The Personal Forecast product has a coherent 90-day forecast structure. It identifies events, groups them into themes, picks anchors/supporting events, and renders timing windows. Its strongest claim is "near-term symbolic timing and theme synthesis."

The visual timeline dots are positioned evenly by loop index rather than actual date spacing. The table dates are real, so this is a presentation limitation, not an engine failure.

### Daily Horoscope

Status: Partially implemented.

The daily product has actual individualized selection logic, but it is currently bound to the system date. It can support a "today generated now" experience. It does not yet support reliable `--report-date` batch generation, replay, QA, or future-date scheduling.

The prose appears to be routed authored content rather than fully generated from event details. That is acceptable if described as daily guidance selected from calculated conditions.

### Weekly Horoscope

Status: Implemented but under-explained.

The weekly product computes real chart-specific timing moments. It is not merely static weekly prose. However, the current client output is closer to a technical timing table than a finished interpretive forecast. It should be framed as a weekly transit timeline until authored interpretive layers are wired.

The ranking-vs-chronology behavior should also be clarified. If the product promises "timeline," chronological display would better match client expectations.

### Soul Ecosystem

Status: Adequately implemented and represented as natal/context infrastructure; not audited as a forecast product.

Soul Ecosystem can contribute chart context and shared interpretive infrastructure. No evidence from this audit supports treating it as a timing or prediction engine.

## 8. Claims That Are Earned Now

The repository can currently support these client-safe claims:

- Year Ahead provides a 12-month astrological forecast/planning report based on natal chart calculation and a ranked set of transit, station, ingress, eclipse, lunation, and convergence signals.
- Personal Forecast provides a 90-day personal transit outlook organized into themes and timing windows.
- Exact-birth reports can include house/angle-aware timing, subject to the normal symbolic limits of astrology.
- Daily Horoscope provides current-day symbolic guidance selected from live sky/natal activation variables.
- Weekly Horoscope provides a chart-specific list of notable exact contacts for the selected week.
- Calculation records and manifests provide meaningful delivery provenance.

## 9. Findings Requiring No Engine Change

These are claim/presentation issues, not necessarily engine defects:

- Avoid calling any current client product a concrete predictive engine.
- Describe convergence windows as overlays or synthesis signals, not as separate high-intensity events unless their score semantics are changed.
- Describe weekly output as a ranked weekly transit/timing list unless it is rendered chronologically and interpreted narratively.
- Describe Personal Forecast as symbolic timing and theme synthesis, not as deterministic outcome prediction.
- Keep Soul Ecosystem positioned as natal/contextual, not predictive.
- Keep `predictive_sandbox` out of client product claims.

## 10. Findings That Would Require Engine or Method Work

1. Make Daily Horoscope respect the requested report date.

   The resolver should accept the report date/window from generation context instead of using `datetime.now()` directly. Without that, QA, scheduling, backfills, and reproducible report generation remain unreliable.

2. Decide whether weekly output is ranked or chronological.

   If ranked, label it as "top moments." If chronological, sort the rendered list by date/time after selection. A more client-ready version would also attach interpretive copy to each moment.

3. Add or remove claims for inactive methods.

   If progressions, solar arc, returns, profections, or time-lord methods are intended client features, they need active calculation paths, traceable evidence, and surfaced provenance. If not, they should stay out of client claims.

4. Expand manifest trace depth if third-party validation is important.

   Current manifests are useful for provenance, but the full event-selection trace is not packaged in a client/auditor-friendly way. This is not required for normal delivery, but it would help external review.

## 11. Recommended Investigation Order

1. Daily report-date control.

   This is likely a narrow plumbing fix with high QA value.

2. Weekly product positioning.

   Decide whether the weekly surface is a technical timeline, a ranked "top moments" list, or a fully authored weekly forecast.

3. Claim inventory cleanup.

   Audit outward-facing copy/docs for any unsupported method claims.

4. Manifest/event-trace packaging.

   Only pursue this if review packs, client validation, or commercial diligence require stronger evidence bundles.

## 12. Evidence Appendix

Primary files inspected:

- `generate.py`
- `engine/natal_engine.py`
- `engine/transit_engine.py`
- `selectors/variable_resolver.py`
- `products/year_ahead/templates/active/year_ahead.html`
- `products/personal_forecast/templates/personal_forecast.html`
- `products/daily_horoscope/templates/daily_horoscope.html`
- `products/weekly_horoscope/templates/weekly_horoscope.html`

Generated audit samples:

- `audit_output/client_forecast_samples/audit_exact_year_ahead.html`
- `audit_output/client_forecast_samples/audit_exact_year_ahead.manifest.json`
- `audit_output/client_forecast_samples/audit_personal_forecast.html`
- `audit_output/client_forecast_samples/audit_personal_forecast.manifest.json`
- `audit_output/client_forecast_samples/audit_daily_horoscope.html`
- `audit_output/client_forecast_samples/audit_daily_horoscope.manifest.json`
- `audit_output/client_forecast_samples/audit_weekly_horoscope.html`
- `audit_output/client_forecast_samples/audit_weekly_horoscope.manifest.json`
- `audit_output/client_forecast_samples/context_trace_summary.json`

Representative source anchors:

- CLI report choices and report window routing: `generate.py`
- Master report generation and context dispatch: `generate.py`
- Year Ahead context construction, monthly relevance, forecast climate, convergence, and raw cycle ledger: `generate.py`
- Personal Forecast theme grouping and timing selection: `generate.py`
- Daily horoscope context construction: `generate.py` and `selectors/variable_resolver.py`
- Daily activation transit calculation: `engine/transit_engine.py`
- Weekly timeline calculation: `engine/transit_engine.py`
- Transit cycles, ingresses, stations, retrograde clusters, void-of-course windows, eclipses, and lunations: `engine/transit_engine.py`
Boundary note:

This audit intentionally does not evaluate `predictive_sandbox` as a product and does not recommend surfacing it. It is mentioned only to document exclusion from the client-facing forecast adequacy review.
