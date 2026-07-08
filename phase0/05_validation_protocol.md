# Phase 0 — Validation Protocol

Program: [EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md](../EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md)
Depends on: [04_convergence_and_candidate_protocol.md](./04_convergence_and_candidate_protocol.md), [06_sidecar_and_export_contract.md](./06_sidecar_and_export_contract.md).
Status: charter (Phase 0). Policy. No implementation.
Version: `phase0.1.0`
Date: 2026-07-07

## Purpose

Specify how EO codes outcomes for `MicroCandidate` objects and how the system distinguishes calibration effects from raw method effects. Validation exists *alongside* method development; it is not deferred.

## 1. Design principles

1. **Outcomes live outside the generation artifact.** The sidecar (`<report_id>.eo_predictive.json`) records what the engine said. The outcome ledger (`<report_id>.eo_outcomes.json` per the sidecar contract) records what the reviewer coded. Two files, two roles, two write cycles.
2. **Pre-registration precedes outcome review.** A candidate's `pre_registered_at` timestamp must fall before any outcome coding for that candidate. Reviewers cannot back-date candidates.
3. **Unresolved is not a failure.** Missing evidence is a distinct category. Do not force binary classification.
4. **Matched-random baselines are mandatory** for any comparative metric. Raw hit rates without baseline are not evidence.
5. **Ablation is the primary attribution tool.** To claim asteroid participation improves candidate precision, run the same charts without asteroids and compare.

## 2. Research status categories (locked)

Only these five values are allowed for `OutcomeLedgerEntry.outcome_category`.

- `supported_hit` — an outcome date within the candidate window, matching the candidate's declared domain and topic keys, was independently documented before outcome review began. "Independently documented" means: dated in a source not authored by the reviewer specifically for this validation, or authored by the reviewer with a timestamp preceding the outcome review start.
- `supported_non_hit` — the candidate window elapsed with no outcome matching the candidate's declared domain and topic keys, and the reviewer documented sufficient search effort (e.g. searched the querent's calendar, journal, external event log, or news archive for the target domain).
- `unresolved` — outcome coding attempted but insufficient evidence in either direction. This is distinct from research incomplete: the reviewer looked and couldn't decide.
- `research_incomplete` — outcome coding not yet attempted or evidence source not yet available. Should be revisited.
- `excluded_by_protocol` — the candidate is disqualified from the validation set for a documented reason (e.g. calculation-error void, birth-time revision that changed the natal snapshot, reviewer conflict of interest).

**Never** coerce `unresolved` or `research_incomplete` into `supported_hit` or `supported_non_hit` in aggregate statistics. Reports must show all five categories.

## 3. Outcome ledger schema

Defined in [06_sidecar_and_export_contract.md](./06_sidecar_and_export_contract.md) §4. Summary here for convenience.

Fields:

- `outcome_id`
- `candidate_id` (reference to sidecar)
- `report_run_id` (reference to sidecar)
- `chart_id` (the natal snapshot)
- `research_subject` — description of what event class was being sought
- `candidate_window` — `[start_at, end_at]` copied from sidecar
- `candidate_domain` — copied from sidecar
- `pre_registered_evidence` — copied from sidecar; retained here so outcome file is self-contained for external review
- `chronology_source` — where the outcome evidence came from (calendar, journal, news, third-party report, etc.)
- `chronology_source_timestamp` — when the source was written / dated
- `outcome_category` — one of the five §2 values
- `event_date` — if `supported_hit`, the actual event date. Empty otherwise.
- `match_precision` — one of `exact_day`, `within_window`, `edge_of_window`, `outside_window_close_call`. Empty for non-hits.
- `research_completeness` — one of `full`, `partial`, `minimal`. Reviewer's own assessment of search effort.
- `non_hit_rationale` — text for non-hits; describes what search was done.
- `unresolved_rationale` — text for unresolved; describes what evidence was found on each side.
- `reviewer_id` — anonymous reviewer identifier (initials or hash).
- `reviewed_at` — timestamp of outcome coding.
- `blind_review_status` — one of `blind`, `partially_blind`, `open`. See §5.

## 4. Blind review policy

Ideal: reviewer codes outcomes without seeing the candidate's `topic_keys`, `candidate_domain`, or `component_scores`. Practical: for early validation, a partially-blind protocol is acceptable.

### 4.1 Blind

Reviewer sees only: the candidate window `[start_at, end_at]` and a generic prompt "did any notable event happen for [querent] in this window? If so, categorize by domain." Reviewer does not see the candidate's declared domain or topic keys.

### 4.2 Partially blind

Reviewer sees the candidate window and its declared domain (e.g. `partnership`) but not its topic keys, component scores, or contributing signal specifics.

### 4.3 Open

Reviewer sees everything. Should only be used for method development testing, not for headline validation metrics.

Every `OutcomeLedgerEntry` carries `blind_review_status` for downstream stratification.

## 5. Metrics

Distinct metrics, tracked separately.

### 5.1 Candidate precision

Definition: `supported_hit / (supported_hit + supported_non_hit)`.

Excluded from denominator: `unresolved`, `research_incomplete`, `excluded_by_protocol`.

Report shape: precision by candidate-score band, by asteroid-participation, by convergence-score decile, by chart type (from regression fixtures).

### 5.2 Event coverage

Definition: proportion of known-outcome events (from an independently-maintained event log) that fell within a candidate window somewhere in the report period.

This is the "recall" side. Requires an independently-maintained event log per chart, ideally journaled before validation begins.

### 5.3 Rank sensitivity

Definition: precision as a function of `convergence_score` percentile. If ranking is meaningful, top-decile candidates should hit more often than bottom-decile.

### 5.4 Topic-domain accuracy

Definition: among `supported_hit` candidates, the fraction where the coded event's actual domain matches the candidate's declared `candidate_domain`.

A wrong-domain hit is coded as `supported_hit` with a `domain_mismatch = true` flag, and is separately tracked.

### 5.5 Window-width calibration

Definition: for `supported_hit` candidates, the distribution of `match_precision` across `exact_day / within_window / edge_of_window`. Because candidate windows are trigger-derived rather than fixed-width (see [04_convergence_and_candidate_protocol.md](./04_convergence_and_candidate_protocol.md) §4.2), calibration is checked per natural window size, not against one universal width: a well-calibrated window of any size shouldn't over-concentrate hits at the exact center or at the edges — a roughly uniform distribution within the window is expected under random-timing null. `predictive_sandbox` candidates additionally get a same-width comparison since its research cap is fixed.

### 5.6 Method-family contribution

Ablation-based. For each method family, run candidates without that family and measure precision drop.

- Baseline: transit-only.
- +Asteroid transits (proprietary + 34-asteroid registry).
- +Returns.
- +Profections.
- +Solar Arc.
- +Progressions.
- +Lots + ZR.

Each configuration is a separate run with its own sidecar and outcome ledger.

### 5.7 Asteroid contribution

Two sub-analyses:

- Overall: precision with vs. without asteroid participation across all candidates.
- Per-asteroid: precision of candidates involving each specific asteroid vs. matched candidates without that asteroid.

Per-asteroid analysis requires ≥10 candidates involving that asteroid before publication.

### 5.8 False-positive rate

Definition: `supported_non_hit / total_candidates_with_documented_search`. Excluded: `unresolved`, `research_incomplete`.

Interpretation: how often the system says "here comes something" and nothing comparable happens under reasonable search.

### 5.9 Quiet-period behavior

Definition: proportion of report windows with zero candidates emitted. Break down by chart type. A system that emits candidates on every chart every month is not discriminating; a system that emits zero candidates on charts with genuinely notable events is under-sensitive.

Reported alongside `event coverage` (§5.2) for calibration reads.

### 5.10 Matched-random baseline

**Mandatory for every metric that compares "with EO candidates" against "chance."**

Procedure:

1. Preserve the report year, chart, and candidate count.
2. Preserve the window width (6 days).
3. For each real candidate, generate a matched-random candidate: same window width, randomly placed within the same report period, respecting the same "excluded dates" if any (e.g. exclude birthdays as noise).
4. Code outcomes for the matched-random candidates using the same blind protocol.
5. Compute the same metrics on the matched-random set.
6. Report EO metrics *minus* matched-random baseline.

Raw hit rates without matched-random baseline are not published.

## 6. Regression against fixture charts

The regression fixtures ([07_versioning_and_regression_fixtures.md](./07_versioning_and_regression_fixtures.md)) are the persistent test harness. Every new clock, every registry change, every candidate-protocol change re-runs against the fixture charts.

Validation runs against fixtures do not need outcome ledgers (they're not real charts); they need reproducibility ledgers:

- Same policy version + same fixture chart + same report window ⇒ identical sidecar (bit-exact) OR documented and approved delta.

Delta approval requires an operator note explaining what changed and why.

## 7. Historical / retrospective validation

For validating against real historical charts with real known events, the protocol adds:

### 7.1 Pre-registration lock

The event log for the querent must be timestamped or archived before the retrospective test begins. Ideally the event log lives in a version-controlled place (Git repo, dated journal, external document with modification timestamps) and its state at the moment validation begins is snapshotted.

### 7.2 Report generation date

Retrospective validation uses the actual historical date as the report date (not "generate a 2015 Year Ahead for someone born in 1980" — that's a projection). The report is generated *as if* it were being run at the moment.

### 7.3 Blind-to-outcome reviewer

Ideally the reviewer coding outcomes is not the same person who generated the report, or is blind to the candidate details at review time (§4).

### 7.4 Statistical thresholds

For any headline claim (e.g. "EO's asteroid layer improves precision"), the threshold is:

- Effect size that survives matched-random baseline subtraction.
- N ≥ 30 candidates in the affected set for precision claims.
- N ≥ 10 outcomes in the affected set for per-asteroid claims.

No headline claims from smaller samples.

## 8. Validation cadence

Suggested — subject to project scheduling.

- **Per phase** (4, 5, 6, 7, 8): a regression run against fixtures + a small (≤3 chart) live retrospective run.
- **Post-Phase 8**: the first full retrospective validation program (Phase 9 per the program document).
- **Ongoing**: matched-random baseline maintained alongside the live candidate stream.

## 9. What validation does not do

- Does not decide whether EO's astrology is "true." That is not a question this framework answers.
- Does not promote a candidate class to a client surface. That is Phase 10.
- Does not adjust weights automatically. Weight tuning is a manual, versioned decision informed by validation reports.
- Does not replace method charters. If validation surfaces a bug, the fix is in the charter and the scanner, not in the outcome-coding process.

## 10. Locked at Phase 0

- Five research status categories (§2).
- Outcomes live outside generation artifact (§1).
- Pre-registration precedes outcome review (§1.2, §7.1).
- Matched-random baseline mandatory (§5.10).
- Blind or partially-blind reviewer protocol per candidate (§4).
- Ablation for method-family attribution (§5.6).

Any change requires a new policy version and an operator note.
