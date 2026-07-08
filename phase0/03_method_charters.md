# Phase 0 — Method Charters

Program: [EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md](../EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md)
Status: charter (Phase 0, operator-approved). No implementation permitted until sign-off.
Version: `phase0.1.1`
Date: 2026-07-07 (patched same day, before Phase 4 implementation began, per Phase 4 Claude method-charter review: fixed a load-bearing gap in C1 Returns, C4 Annual Profections, and C5b Zodiacal Releasing where none specified a value for `phase0/01_predictive_object_schemas.md` §2's hard `orb`/`distance`/`phase` requirement — every emitted event from these three charters would otherwise have been rejected as malformed by the sidecar writer. Also clarified the C1 Return-chapter vs. `ChapterState` layering, the C1 secondary-body independence-group fallback, and the C4 time-lord ruler lookup table's zodiacal-order framing. See `phase0.1.0` → `phase0.1.1` diff in `agents/REVISIONS.md`.

One charter per active clock family or planned clock family. Each charter specifies the exact answer to twelve required questions:

1. Astronomical calculation convention.
2. House system and zodiac assumptions.
3. Sect or birth-time dependency.
4. Allowed bodies, angles, and asteroids.
5. Exactness and orb policy.
6. Output `ForecastEvent` shape: `method_family`, `method_variant`, `clock_role`, `activation_route`.
7. Chapter vs. trigger role.
8. Anti-double-counting behavior (`independence_group` policy).
9. Topic / natal-anchor linkage rule.
10. Confidence limits.
11. Report-surface policy.
12. Validation rule (what specifically counts as evidence of correct behavior in Phase 9).

Charters are ordered by build sequence per the program (Phase 4 → Phase 6).

---

## C1. Returns

**Program phase:** 4.

### 1. Astronomy

- Solar return: exact moment `transiting_Sun.longitude == natal_Sun.longitude`, computed by bisection to 0.01° tolerance around the natal-Sun anniversary window (±48 hours of the anniversary date, expandable if leap-year drift requires).
- Lunar return: exact moment `transiting_Moon.longitude == natal_Moon.longitude`, computed monthly across the report window. ~27.3-day recurrence.
- Jupiter / Saturn / other planetary returns: exact moment `transiting_body.longitude == natal_body.longitude`, computed within the report window. Long-cycle returns may not occur within a given report window; if none does, the scanner returns an empty list.
- All computations use Swiss Ephemeris `swe.calc_ut` in the report location's UTC frame. Return moment is location-agnostic for the *event* (the moment is the same worldwide); return-chart interpretation (Phase 4b+) uses birth location by default. Relocated returns are deferred to a later phase.

### 2. House system and zodiac

- Tropical zodiac (matches EO active methodology).
- Whole Sign houses.
- Deferred: sidereal, Placidus, other quadrant systems.

### 3. Sect / birth-time dependency

- Solar return: `birth_time_dependency = none` for the return moment itself. Return-chart interpretation degrades gracefully under approximate/unknown birth time (angles suppressed).
- Lunar return: `birth_time_dependency = none` for the return moment. Return-chart interpretation same as above.
- Planetary returns: `none` for moment; `soft` for chart interpretation.

### 4. Allowed bodies

- Primary: `Sun`, `Moon`, `Jupiter`, `Saturn`.
- Secondary (through declared policy, off by default in Phase 4): `Mercury`, `Venus`, `Mars`, `Uranus`, `Neptune`, `Pluto`, `Chiron`.
- Asteroids: not returned to as first-class in Phase 4. Asteroid returns (Kassandra, Destinn etc.) are deferred to a later phase; the registry marks eligibility but Phase 4 does not scan them.

### 5. Orb / exactness

- The return moment itself is exact (bisection to ≤0.01°). Not an orb-based event, so `orb` is left null. Per `phase0/01_predictive_object_schemas.md` §2's hard rule ("every `ForecastEvent` carries at least one of `orb`, `distance`, or `phase`, or the sidecar writer must reject it as malformed"), the return moment's `ForecastEvent.distance` carries the bisection residual, which is `0.0` by construction (the root-finder terminates once the residual is within the 0.01° tolerance, and the stored value is the rounded residual — effectively zero, not a placeholder). `phase` stays null for the moment event.
- For candidate-support purposes, a "return window" may be declared as `[peak_at − 12h, peak_at + 12h]` for the Sun and Moon; `[peak_at − 24h, peak_at + 24h]` for Jupiter and Saturn. This is the window in which return-driven convergence is granted proximity to co-occurring triggers.

### 6. Output shape

- `method_family = "RETURN"`.
- `method_variant ∈ {"solar_return", "lunar_return", "jupiter_return", "saturn_return", ...}`.
- `clock_role = "return"`.
- `activation_route = "return_moment"`.
- `temporal_precision = "instant"` for solar/lunar; `"day"` for Jupiter/Saturn given typical usage.
- `independence_group ∈ {"return_family_solar", "return_family_lunar", "return_family_jupiter", "return_family_saturn", "return_family_generic"}` — the fifth value is `phase0/01_predictive_object_schemas.md` §9's reserved catch-all. If the "secondary" body list (Mercury, Venus, Mars, Uranus, Neptune, Pluto, Chiron — declared policy, off by default in Phase 4) is ever enabled, every secondary-body return uses `return_family_generic` collectively rather than a per-body group; splitting secondary bodies into individual `return_family_<body>` groups is deferred until a real validation need arises, so the taxonomy doesn't fragment ahead of demand.

### 7. Chapter vs. trigger role

- Solar return: `chapter` for the "solar return year" (start_at = current SR moment; end_at = next SR moment). Additionally, the SR moment itself may be emitted as a `trigger` event when convergence assembly needs the exact moment. **The scanner emits both, but they carry distinct `event_id`s and both link to the same `independence_group` — the candidate builder dedupes.** Both are `ForecastEvent` records, not a `ChapterState` directly — the scanner does not construct `ChapterState` itself. The chapter builder (`phase0/04_convergence_and_candidate_protocol.md` §8.1) later aggregates the chapter-role `ForecastEvent` into a proper `ChapterState` with `chapter_kind = "return_year"` (already reserved for this in `phase0/01_predictive_object_schemas.md` §4). The Return scanner's job stops at emitting the two `ForecastEvent`s; promotion to `ChapterState` is downstream, shared machinery.
- Lunar return: `chapter` for the "lunar return month"; `trigger` for the return moment.
- Jupiter / Saturn returns: `chapter` for the return year (± 6 months of the exact date); `trigger` for the exact moment.

### 8. Anti-double-counting

- A return chapter and its trigger share `independence_group = "return_family_<body>"`. The candidate builder counts the pair as one method-family vote.
- A return moment that coincides with a transit contact of the same natal body (e.g. solar return day happens to fall during a transiting-Saturn-conjunct-natal-Sun contact) does **not** count as two independent families for `MicroCandidate` purposes if the transit is `transit_Sun` — Sun ≠ Saturn is fine; but a return of body X coinciding with a transit of body X to X *is* the same underlying phenomenon and dedupes.

### 9. Topic / anchor linkage

- Every return links to natal anchors that contain the returned body: e.g. solar return links to any anchor containing `Sun`, any anchor whose `rulers` contains `Sun`, and any anchor whose `proprietary_index_links` includes an index driven by `Sun`.
- `topic_keys` union: return `chapter` inherits topics of every linked anchor. Return `trigger` inherits topics of anchors whose primary body matches the returned body.

### 10. Confidence

- `confidence = 1.0 * calculation_integrity(0.98) * method_maturity(0.85 at Phase 4 launch)`. Bounded to `[0, 1]`.
- Return-chart-interpretation confidence (Phase 4b) is a separate score not covered by this charter.

### 11. Report-surface policy

- Phase 4: `[internal_rd, predictive_sandbox]` only.
- Phase 10 may promote solar-return chapter to `year_ahead_appendix` under explicit governance approval.

### 12. Validation rule

- Fixture: for the `known_retrograde_loop` and `dense_transit_year` regression charts, the scanner must produce exactly one solar return and 11–13 lunar returns per 12-month window.
- Fixture: solar-return `peak_at` must fall within ±48h of the natal-Sun anniversary date for every chart.
- Fixture: lunar-return sequence must have every `end_at ≤ next.start_at`, monotonic in time.
- Adversarial: report windows spanning DST transitions must not shift the returned longitude by more than the tolerance.

---

## C2. Solar Arc directions

**Program phase:** 5.

### 1. Astronomy

- Convention: **Naibod-adjusted secondary progression of the Sun**. Specifically: the arc for age `t` years is `arc(t) = progressed_Sun.longitude(t) − natal_Sun.longitude`, where `progressed_Sun` uses the "one ephemeris day per year of life" mapping (see C3 for the shared time-scale). This is standard Solar Arc, expressed via the secondary Sun's daily motion.
- Every natal body's directed longitude is `natal_body.longitude + arc(t)`, applied uniformly across the chart.
- Contacts detected as: `directed_body.longitude` forms an in-orb major aspect with any natal target.
- **Single declared arc convention.** Do not mix conventions in the same formula version.

### 2. House system and zodiac

- Tropical. Whole Sign for house-based interpretation.

### 3. Sect / birth-time dependency

- `birth_time_dependency = soft` for body-to-body contacts.
- `birth_time_dependency = hard` for any contact involving a directed body → natal angle, or a directed angle → natal body. Under approximate/unknown birth time, angle-involving contacts are `confidence_state = "withheld"`.

### 4. Allowed bodies

- Directed: `Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, `Jupiter`, `Saturn`, `Uranus`, `Neptune`, `Pluto`, `Chiron`, `Ascendant`, `Midheaven`, `Vertex`.
- Directed asteroids: **anchor tier only** (Kassandra, Aletheia, Destinn, Karma, Kaali, Medea, Hermes, Chaos) at Phase 5 launch. Registry may promote elevated tier later.
- Natal targets: full set (planets + angles + all 34 asteroids where the registry marks target-eligibility). Asteroid targets participate under the registry's per-asteroid Solar Arc policy.

### 5. Orb / exactness

- Solar Arc orb: **1.0° maximum**, tighter than transit orbs because Solar Arc is a symbolic uniform-motion technique with high precision expectations.
- Applicable aspects: `Conjunction`, `Sextile`, `Square`, `Trine`, `Opposition`. Minor aspects deferred.
- Event window: entry when `orb ≤ 1.0`; exact when `orb ≤ 0.05`; exit when `orb > 1.0` on the outgoing side.

### 6. Output shape

- `method_family = "SOLAR_ARC"`.
- `method_variant ∈ {"solar_arc_body_aspect", "solar_arc_angle_aspect", "solar_arc_asteroid_aspect"}`.
- `clock_role = "chapter"` for slow-arc contacts (arc-day motion ~0.985°/year means most contacts span multiple months); `clock_role = "trigger"` reserved for the exact date.
- `activation_route ∈ {"solar_arc_to_body", "solar_arc_to_angle", "solar_arc_to_asteroid"}`.
- `temporal_precision = "week"` for the exact contact date; `"season"` for the surrounding chapter.
- `independence_group = "solar_arc_family"`.

### 7. Chapter vs. trigger role

- Both. Emit a `chapter` event covering `[exact_at − 90d, exact_at + 90d]` (approximately the 6-month zone in which the arc is within 1° of exactness by convention).
- Emit a `trigger` event at `exact_at` for candidate assembly.
- Both share `independence_group`, candidate builder dedupes.

### 8. Anti-double-counting

- All Solar Arc contacts share `solar_arc_family` regardless of body pair.
- A Solar Arc contact and a Secondary Progression contact of the same directed body to the same natal target are counted as **separate** families (`solar_arc_family` vs. `progression_family`) *only if* the calculation methods are genuinely distinct — which they are (Solar Arc applies a uniform arc; secondary progression uses each body's individual progressed motion). This is one of the few places where two long clocks may both contribute independent votes.

### 9. Topic / anchor linkage

- Every contact links to natal anchors containing the natal target body.
- Asteroid participation: when `source_body` or `target_body` is an asteroid, the event's `asteroid_participants` includes it, and `topic_keys` inherits from that asteroid's registry entry.

### 10. Confidence

- `confidence = calculation_integrity(0.95) * (angle_support: 1.0 or 0.4 depending on angle involvement + birth_time_state) * method_maturity(0.80 at Phase 5 launch)`.
- Cap at `0.90` for the first two operator-approved runs; unlock to `1.0` cap after validation ledger has ≥3 test runs recorded.

### 11. Report-surface policy

- Phase 5: `[internal_rd, predictive_sandbox]` only.

### 12. Validation rule

- Fixture: for the `dense_transit_year` chart, the Solar Arc scanner over a 5-year report window must produce a monotonic-in-time sequence with no gap larger than the maximum plausible year-to-year arc drift (< 1.5°).
- Fixture: the Solar Arc convention must reproduce the natal Sun's exact secondary-progressed longitude for age 0.5 years to within `1e-5` degrees.
- Adversarial: charts with birth time at midnight vs 23:59 on the same date should produce Solar Arc contacts within the same day.

---

## C3. Secondary progressions

**Program phase:** 5.

### 1. Astronomy

- Convention: **one ephemeris day per year of life** (the classical convention). For age `t` in years, the progressed chart uses ephemeris state at `natal_jd + t` days.
- Progressed bodies: `Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, plus `Ascendant` and `Midheaven` when birth time is exact.
- Progressed asteroids: **anchor tier only** at Phase 5 launch (Kassandra, Aletheia, Destinn, Karma, Kaali, Medea, Hermes, Chaos), and only for `Conjunction` aspects to natal targets.
- Contacts: progressed_body → natal_target, major aspects.
- Progressed ingresses: sign changes of progressed bodies (event_variant = `progression_ingress`).
- Progressed lunation phases: progressed_Sun-Moon phase changes (new/full/quarters).

### 2. House system and zodiac

- Tropical, Whole Sign.
- Progressed angles use the same house-computation convention as the natal engine.

### 3. Sect / birth-time dependency

- `soft` for body-to-body contacts.
- `hard` for anything involving progressed or natal angles.
- Progressed Moon is `soft` in general but `hard` when its progressed house placement is claimed (which requires natal angle continuity).

### 4. Allowed bodies

- Progressed sources: `Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, `Ascendant`, `Midheaven`. Deferred: `Jupiter`, `Saturn`, outers (barely move in secondary progression; deferred to protect noise budget).
- Natal targets: full set (planets + angles + all 34 asteroids under registry policy).
- Asteroid sources: anchor tier only at launch; conjunctions only.

### 5. Orb / exactness

- **1.0° maximum** for progressed body → natal body contacts.
- **0.5° maximum** for contacts involving progressed or natal angles.
- Applicable aspects: `Conjunction`, `Square`, `Trine`, `Opposition`, `Sextile`.

### 6. Output shape

- `method_family = "PROGRESSION"`.
- `method_variant ∈ {"progression_body_aspect", "progression_ingress", "progression_lunation_phase"}`.
- `clock_role = "chapter"` for slow progressed contacts (Sun, angles); `clock_role = "trigger"` for exact contact date; `clock_role = "modifier"` for progressed Moon which is fast (~13° per year) and functions as a monthly modifier.
- `activation_route ∈ {"progression_to_body", "progression_to_angle", "progression_to_asteroid"}`.
- `temporal_precision`: `"week"` for exact contact; `"season"` for chapter.
- `independence_group = "progression_family"`.

### 7. Chapter vs. trigger role

- Progressed Sun contact: chapter (many months to years within 1° orb).
- Progressed Moon contact: modifier (fast enough that a "chapter" designation would inflate; use monthly modifier + trigger for exact contact).
- Progressed inner-planet contact: chapter + trigger.
- Progressed angle contact: chapter + trigger.
- Progressed ingress: standalone `trigger` (the ingress date).
- Progressed lunation phase change: standalone `trigger` + `chapter` for the following ~3-year phase.

### 8. Anti-double-counting

- All progression contacts share `progression_family`.
- Progression + Solar Arc: independent (per C2).
- Progression + transit of the same natal target by a different body: independent.
- Progression + return of the same body: **not independent when the returned body is the progressed body's natal counterpart** (e.g. progressed Sun conjunct natal Sun + solar return in the same window — same underlying anchor, dedup at candidate assembly).

### 9. Topic / anchor linkage

- Every contact links to natal anchors containing the natal target body.
- Progressed lunation phase change links to anchors containing `Sun` or `Moon` and to phase-associated topic keys (`chapter_opening` for new, `chapter_climax` for full).

### 10. Confidence

- `confidence = calculation_integrity(0.95) * angle_support * method_maturity(0.80 at Phase 5 launch)`.
- Progressed Moon fast enough that day-precision matters; withhold intraday timing claims and use day granularity only.

### 11. Report-surface policy

- Phase 5: `[internal_rd, predictive_sandbox]` only.

### 12. Validation rule

- Fixture: for `known_retrograde_loop`, progressed Mercury retrograde stations must appear as events at their genuine progressed-motion-zero moments.
- Fixture: progressed Sun ingress dates must agree with published ephemeris to within one day.
- Fixture: progressed Moon crosses the entire zodiac in ~27.3 years — regression window must confirm 27–28 progressed sign ingresses over that span.

---

## C4. Annual profections

**Program phase:** 4.

### 1. Astronomy

- Whole-sign annual profection: from age 0 (birth year), House 1 profects. Age 1 → House 2. Age 12 → back to House 1. So profected house for age `t` = `((t % 12) + 1)`.
- Profected sign = the sign of that house in the natal chart.
- Time lord = the traditional domicile ruler of that sign. Lookup table in zodiacal sign order, Aries through Pisces, using classical/traditional rulerships (not modern outer-planet rulerships — matches the codebase's established dignity convention): Aries=Mars, Taurus=Venus, Gemini=Mercury, Cancer=Moon, Leo=Sun, Virgo=Mercury, Libra=Venus, Scorpio=Mars, Sagittarius=Jupiter, Capricorn=Saturn, Aquarius=Saturn, Pisces=Jupiter. Look up by the profected *sign*, not by house number — house number determines the sign only via the natal chart's own whole-sign house-to-sign mapping.
- Optional: monthly profection (12 signs per year, 1 per month starting from the annual profected sign).

### 2. House system and zodiac

- Tropical.
- Whole Sign strictly required. Profections are a whole-sign technique; using another house system voids the method.

### 3. Sect / birth-time dependency

- `birth_time_dependency = none`. Annual profection depends only on natal Ascendant sign, which is knowable to whole-sign granularity even when birth-time confidence is `approximate`. **Refuse to compute** when Ascendant sign is unknown (`simple_mode` with no time supplied but sign resolved from noon fallback is a `soft` confidence state).

### 4. Allowed bodies

- Not a body-based technique. Emits `TimeLordPeriod` records, not `ForecastEvent` records with a body source.
- The time lord is a natal body; its condition (dignity, aspects, house placement) contributes to the period's `lord_natal_state`.

### 5. Orb / exactness

- Not applicable; whole-sign transitions occur on the birthday (year handoff) or on the monthly profection date. Per `phase0/01_predictive_object_schemas.md` §2's hard rule ("every `ForecastEvent` carries at least one of `orb`, `distance`, or `phase`"), the yearly handoff `ForecastEvent` (§6 below) sets `distance = 0.0` — the handoff is an exact whole-sign transition with zero residual by construction, not an approximated or orb-based contact, so `0.0` is a genuine value, not a placeholder. `orb` and `phase` stay null for this event.

### 6. Output shape

- Emits `TimeLordPeriod` with `system = "annual_profection"` or `"monthly_profection"`. `TimeLordPeriod` has no orb/distance/phase requirement (that rule is `ForecastEvent`-only), so the period record itself needs no such field.
- Additionally emits a single `ForecastEvent` per year at the profection year handoff (birthday) with `method_family = "PROFECTION"`, `method_variant = "annual_profection"`, `clock_role = "time_lord"`, `activation_route = "profection_year_lord"`, `temporal_precision = "year_or_longer"`, `independence_group = "profection_family"`, `distance = 0.0` (see §5).

### 7. Chapter vs. trigger role

- Annual profection is a **weight modifier** for its year. It elevates signals whose anchors involve the time lord, its ruled houses, or its natal aspects.
- The birthday handoff itself is a `time_lord` role event, not a `trigger`. It does not by itself justify a `MicroCandidate`.

### 8. Anti-double-counting

- Profection contributes ≤1 method-family vote per year for candidates.
- Profection + time lord's transit is independent because the transit is a distinct calculation.

### 9. Topic / anchor linkage

- Profected house → `domain_keys` from that house's whole-sign house theme.
- Time lord → all anchors containing that body, weighted by the natal condition of the lord.

### 10. Confidence

- `confidence = 1.0 * calculation_integrity(0.99) * method_maturity(0.85)`.
- Method_maturity may be revised after ≥2 fixture runs.

### 11. Report-surface policy

- Phase 4: `[internal_rd, predictive_sandbox]`.
- Phase 10 may promote annual profection to Year Ahead as a "yearly focus" module.

### 12. Validation rule

- Fixture: for every regression chart, the profected house sequence over 12 years must reproduce `1, 2, ..., 12` cyclically.
- Fixture: time lord for a Cancer-Ascendant chart at age 12 must be the Moon; for age 13, Sun; etc.
- Adversarial: charts with birth time on the boundary of a sign change in the Ascendant should raise a `low` confidence flag rather than silently choosing one sign.

---

## C5. Lots

**Program phase:** 6 (prerequisite for ZR).

### 1. Astronomy

- Lot of Fortune (day chart): `ASC + Moon − Sun`.
- Lot of Fortune (night chart): `ASC + Sun − Moon`.
- Lot of Spirit (day chart): `ASC + Sun − Moon`.
- Lot of Spirit (night chart): `ASC + Moon − Sun`.
- Lot of Necessity (day chart): `ASC + Fortune − Mercury`.
- Lot of Necessity (night chart): `ASC + Mercury − Fortune`.
- All arithmetic modulo 360°.
- Sect determination: **day chart** if Sun is above the horizon (whole-sign houses 7–12), **night chart** otherwise. Use `formulas/standard/sect.py` for authoritative sect state.

### 2. House system and zodiac

- Tropical.
- Whole Sign for house placement of each lot.

### 3. Sect / birth-time dependency

- `birth_time_dependency = hard` for degree-precise lot positions.
- `birth_time_dependency = soft` for whole-sign house placement of each lot when birth time is approximate but Ascendant sign is knowable.

### 4. Allowed bodies

- Lots are calculated points, not bodies. They appear as `source_kind = "lot"` on any `ForecastEvent` involving them (e.g. transit contacts to lots).
- Lots are natal targets under the same policy as calculated points: contacts to lots from any allowed transit source are eligible under registry policy.

### 5. Orb / exactness

- Lots are single degrees; transit contacts use `1.0°` maximum orb (tighter than natal-planet transit orbs because a lot is a symbolic degree, not a diffuse body).

### 6. Output shape

- Lots themselves do not emit events. Transit contacts to lots emit `ForecastEvent` with `method_family = "TRANSIT"` (they remain transit events), `activation_route = "transit_to_body"` with `target_kind = "lot"`, and `asteroid_participants` empty unless a proprietary asteroid is the source.
- Zodiacal Releasing uses lot positions as inputs; see C5b.

### 7. Chapter vs. trigger role

- Contacts to lots are `trigger` events by default; `chapter` when made by structural transits (Saturn/Uranus/Neptune/Pluto).

### 8. Anti-double-counting

- Lot contacts join `transit_family` for anti-stacking purposes.

### 9. Topic / anchor linkage

- Lot of Fortune → domain `resources`, `home`, `identity`, `vocation`; topic `fate`, `allotment`.
- Lot of Spirit → domain `vocation`, `meaning`, `identity`; topic `soul`, `essence`, `wisdom`.
- Lot of Necessity → domain `transformation`, `resources`; topic `oath`, `obligation`, `right_order`.

### 10. Confidence

- `confidence = calculation_integrity(0.98) * angle_support * method_maturity(0.85)`.
- Withhold degree-precise claims under approximate birth time; house-only claims permitted at reduced confidence.

### 11. Report-surface policy

- Phase 6: `[internal_rd, predictive_sandbox]` only.

### 12. Validation rule

- Fixture: for a day chart with `ASC = 100°`, `Sun = 200°`, `Moon = 50°`, Lot of Fortune must equal `(100 + 50 − 200) mod 360 = 310°`. Bit-exact.
- Fixture: for a night chart with the same longitudes, Lot of Fortune must equal `(100 + 200 − 50) mod 360 = 250°`.
- Adversarial: exactly-on-horizon Sun (sect boundary) must raise a `low` confidence flag rather than silently choose a sect.

---

## C5b. Zodiacal Releasing

**Program phase:** 6.

### 1. Astronomy

- Input: Lot of Fortune (for topics of embodiment, health, livelihood) or Lot of Spirit (for topics of action, career, life direction).
- L1 (major) periods: begin at the lot's sign; each sign rules for a fixed number of years per Vettius Valens (Aries 15, Taurus 8, Gemini 20, Cancer 25, Leo 19, Virgo 20, Libra 8, Scorpio 15, Sagittarius 12, Capricorn 27, Aquarius 30, Pisces 12). L1 periods cycle through the zodiac.
- L2 (sub-) periods: within each L1, sub-divide into 12 sub-periods proportional to the L1 sign's total years, cycling through signs starting from the L1 sign.
- L3 and L4: recursively subdivide L2 and L3 by the same rule.
- **Peaks**: an L1 period is a peak when its sign is the sign of the lot itself or the sign(s) in whole-sign aspect (angular houses from the lot: 4, 7, 10). Additional peak marker: whether the L2 period sign is angular from the L1 period sign.
- **Loosing of the Bond (LOB)**: when a sub-period completes its allotted duration but the parent period has not, the next sub-period "jumps" to the sign opposite the sub-period that just ended. Marked as `is_loosing_of_the_bond = True`.

### 2. House system and zodiac

- Tropical, Whole Sign.

### 3. Sect / birth-time dependency

- Inherits from Lots (C5).
- ZR from a lot with `hard` birth-time dependency inherits `hard`.

### 4. Allowed bodies

- Not a body technique. Emits `TimeLordPeriod` records.
- Period lord = domicile ruler of the period's sign.
- Optionally emits `ForecastEvent` records with `method_family = "ZODIACAL_RELEASING"` for `L1_transition`, `L2_transition`, `peak_activation`, `loosing_of_the_bond`.

### 5. Orb / exactness

- Not applicable; period boundaries are exact-to-the-day. Per `phase0/01_predictive_object_schemas.md` §2's hard rule, the period-transition `ForecastEvent`s (§6 below) set `distance = 0.0` — a period boundary is exact by construction, not orb-approximated, so `0.0` is genuine, not a placeholder. Same convention as C1 (Returns) and C4 (Profections).

### 6. Output shape

- Primary: `TimeLordPeriod` records for every L1, L2, L3, L4 period intersecting the report window. Each has `system ∈ {"zodiacal_releasing_fortune", "zodiacal_releasing_spirit"}`, `level ∈ {"L1", "L2", "L3", "L4"}`, `parent_period_id` filled where applicable. No orb/distance/phase requirement (`ForecastEvent`-only rule).
- Secondary: `ForecastEvent` records at period-transition moments with `method_family = "ZODIACAL_RELEASING"`, `method_variant ∈ {"zr_l1_transition", "zr_l2_transition", "zr_peak", "zr_lob"}`, `clock_role ∈ {"time_lord", "trigger", "overlay"}`, `activation_route = "zr_period_transition"`, `temporal_precision` inherits from level, `distance = 0.0` (see §5).
- `independence_group ∈ {"zr_family_fortune", "zr_family_spirit"}` — Fortune ZR and Spirit ZR are independent families.

### 7. Chapter vs. trigger role

- L1 and L2 are `chapter` weight modifiers.
- L1 transitions, L2 transitions, peaks, and LOB moments are `trigger` events (short, dated).
- L3 and L4 are `modifier` scale — used to weight signals but not to justify candidates on their own.

### 8. Anti-double-counting

- L1 and L2 sharing the same lot count as one vote (both `zr_family_<lot>`).
- Fortune ZR and Spirit ZR are independent → contribute two votes to `independent_method_families` when both are active in the candidate window.
- ZR + profection: independent (different techniques).

### 9. Topic / anchor linkage

- Every ZR period links to natal anchors containing the period lord.
- Peaks additionally link to anchors containing the lot itself and the lot's ruler.
- LOB moments link to anchors of the incoming and outgoing signs' rulers.

### 10. Confidence

- `confidence = calculation_integrity(0.95) * angle_support * method_maturity(0.80)`.
- Cap at `0.90` until validation ledger has ≥3 test runs.

### 11. Report-surface policy

- Phase 6: `[internal_rd, predictive_sandbox]` only.

### 12. Validation rule

- Fixture: for a chart with Lot of Fortune in Cancer, the first L1 period is Cancer (25 years).
- Fixture: total years across all L1 periods in a 246-year cycle must equal 12 × mean(15, 8, 20, 25, 19, 20, 8, 15, 12, 27, 30, 12) = the correct sum per Valens.
- Fixture: LOB events must occur at documented moments in a hand-computed sample chart.

---

## C6. Additional time-lord infrastructure (Firdaria, primary directions, others)

**Program phase:** deferred beyond Phase 6.

### 1–12. Placeholder

This charter reserves the `TimeLordPeriod` shape and the `TIME_LORD` method family for future systems. When any of Firdaria, primary directions, monomoiria, decennials, or others is charted:

- It must use `TimeLordPeriod` for period records.
- It must use `ForecastEvent` for dated transitions.
- It must declare its own `independence_group = "time_lord_family_<system>"`.
- It must publish its charter answering all 12 required questions before implementation.

**Do not implement any of these in Phase 4–6.** They wait for the first successful validation cycle over the primary six (returns, profections, Solar Arc, progressions, Lots, ZR) before any expansion.

---

## Common rules across all charters

- **No charter enters report prose before it enters the sidecar and validation harness.** Sidecar first, then validation, then optional client surface.
- **Every charter's scanner outputs `ForecastEvent`** per the schema (or `TimeLordPeriod` where applicable). No scanner is permitted to emit a bespoke shape.
- **Every charter respects the asteroid registry.** When a scanner extends target eligibility to asteroids, it must read `phase0/02_asteroid_predictive_registry.json` at load time and honor per-asteroid orb / aspect / clock policy.
- **Every charter publishes fixtures.** No new clock passes Phase 0 sign-off without at least 3 named fixtures listed in `07_versioning_and_regression_fixtures.md`.
- **Every charter is versioned.** A charter change increments its version and appears in the sidecar's `policy_version` field so historical runs can be reproduced against their original charter.
