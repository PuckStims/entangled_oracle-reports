# Location Services — Capability Inventory

**Author:** Claude Code, Implementation and Integration Lead
**Status:** Repo-grounded audit as of this pass. Every claim below is traced to a
specific file. Where planning docs (`ASYNC_WORKSTREAMS.md`) describe something
that does not match runtime truth, that is called out explicitly rather than
smoothed over.

This document answers one question for the content lead: **what can Place
Resonance actually stand on today, and what still needs to be built?**

---

## 1. Already computed (no new code needed)

### Natal payload

[engine/natal_engine.py](../../engine/natal_engine.py) `generate_payload()` produces the shared payload
every report type consumes. Relevant to Location Services:

- `user_profile.julian_day` — the Julian Day computed from the birth UTC
  instant (natal_engine.py:415-420). This is the value relocation must
  preserve unchanged.
- `user_profile.utc_datetime` / `local_datetime` — ISO strings for the birth
  instant and the birth-location local clock (natal_engine.py:469-470).
- `angles.{Ascendant,Midheaven,Descendant,Imum_Coeli,Vertex}` — computed via
  `swe.houses(julian_day, latitude, longitude, b"P")`, with a Porphyry
  (`b"O"`) fallback for polar latitudes where Placidus is degenerate
  (natal_engine.py:435-453). **This exact angle-calculation call is what
  relocation reuses** — same function, new latitude/longitude, same
  Julian Day.
- `houses.House_1..House_12` — Whole Sign houses generated from the
  Ascendant sign via `generate_whole_sign_houses()` (natal_engine.py:223-242).
- `standard_planets`, `custom_asteroids` — geocentric ecliptic longitudes
  from `swe.calc_ut(julian_day, body_id, CALC_FLAGS)`. **These do not change
  with location.** A planet's ecliptic longitude at a given instant is the
  same everywhere on Earth; only its house placement (which depends on the
  local Ascendant) changes. This is the physical fact that makes relocation
  computationally cheap and correct: recompute angles/houses, reuse
  longitudes as-is.
- `aspects` — a flat body-to-body (and body-to-angle) matrix computed once
  at generation time from those longitudes (natal_engine.py:583-625).

### Destination / place resolution

[engine/offline_place_resolver.py](../../engine/offline_place_resolver.py) resolves free-text place strings
("Chicago, IL") to `{display_name, latitude, longitude, timezone, source}`
using packaged `geonamescache` city data and `timezonefinder`, entirely
offline. `natal_engine._resolve_location()` (natal_engine.py:306-316) calls
this first and only falls back to online Nominatim
(`natal_engine._resolve_location_online`, natal_engine.py:270-303) if the
offline lookup can't find a unique match.

**This resolver is directly reusable for destinations with zero
modification** — a destination is just another place string. The new
`engine/location_services.py` calls `resolve_place()` directly (offline
only, deliberately skipping the Nominatim network fallback — see §4).

### Standard formula layer (reusable on any correctly-shaped payload)

Every module in `formulas/standard/` that exposes an `evaluate_*(payload)`
function takes a single payload dict and reads only `angles`,
`standard_planets`, `custom_asteroids`, and `houses` from it — it does not
care whether that payload came from `generate_payload()` or from a
relocated reconstruction, as long as the shape matches:

| Module | Entry point | Reads |
|---|---|---|
| `formulas/standard/angularity.py:38` | `evaluate_angularity(payload, body_name)` | `angles`, body's `house` |
| `formulas/standard/dignity.py:124` | `evaluate_dignity(payload, body_name)` | `standard_planets` |
| `formulas/standard/sect.py:47,55,135` | `evaluate_chart_sect(payload)` etc. | `angles.Ascendant`, `standard_planets.Sun` |
| `formulas/standard/planetary_condition.py:117` | `evaluate_all_planetary_conditions(payload)` | angularity + dignity + sect + motion |
| `formulas/standard/chart_ruler.py:48` | `evaluate_chart_ruler(payload)` | `angles.Ascendant`, rulership |
| `formulas/standard/house_emphasis.py:90` | `evaluate_house_emphasis(payload)` | houses, occupancy |
| `formulas/standard/planetary_prominence.py:54` | `evaluate_prominence(payload)` | angularity, aspects |
| `formulas/standard/chart_structure.py:104` | `evaluate_chart_structure(payload)` | elements/modalities/polarities |
| `formulas/standard/aspect_architecture.py:155` | `evaluate_aspect_architecture(payload)` | `aspects` |
| `formulas/standard/rulership_network.py:179` | `evaluate_rulership_network(payload)` | dispositors |
| `formulas/standard/named_configurations.py:68` | `evaluate_named_configurations(payload)` | aspect patterns |
| `formulas/standard/natal_convergence.py:183` | `evaluate_standard_natal_convergence(payload)` | multiple |

**Important, non-obvious finding:** `evaluate_chart_sect()`
(sect.py:38-44) determines day/night by testing whether the Sun sits above
or below the **Ascendant/Descendant horizon axis** — `(sun_lon - asc_lon)
% 360 < 180`. Because the Ascendant genuinely rotates with geographic
location at a fixed UTC instant, running this function against a
*relocated* payload can, for real (if unusual) relocation distances,
return a different day/night sect than the natal chart — and sect feeds
directly into `evaluate_dignity()` and `evaluate_all_planetary_conditions()`.
This is exactly why the project boundary "natal planetary condition
modifies relocated expression; relocation does not rewrite natal condition"
matters at the code level, not just the prose level: **condition-bearing
formulas (`evaluate_dignity`, `evaluate_chart_sect*`,
`evaluate_all_planetary_conditions`) must only ever be called on
`natal_payload`, never on a relocated payload.** `engine/location_services.py`
enforces this by calling `evaluate_angularity()` (house placement / angle
contact — genuinely relocation-sensitive) against the relocated payload,
and documenting condition as a natal-only lookup rather than recomputing it.

### Methodology / confidence scaffolding

- [formulas/standard/methodology_profiles.py](../../formulas/standard/methodology_profiles.py) — single active profile is
  `tropical_whole` (Tropical + Whole Sign). `validate_profile_id()` raises
  for anything else. Location Services introduces no new profile; relocated
  payloads carry the same `methodology` block, untouched.
- [formulas/standard/confidence.py](../../formulas/standard/confidence.py) — controlled birth-time confidence
  states (`EXACT_BIRTH_TIME`, `APPROXIMATE_BIRTH_TIME`, `UNKNOWN_BIRTH_TIME`,
  etc.). Relocation does not change birth-time confidence — the birth
  instant/location is unchanged — so the natal `user_profile` block
  (including its confidence state) is copied through unmodified.
- [formulas/standard/normalization.py](../../formulas/standard/normalization.py) — canonical angle names
  (`Ascendant`, `Midheaven`, `Descendant`, `Imum_Coeli`, `Vertex`) and the
  `ANGLE_ALIAS_MAP` for shorthand (`ASC`, `MC`, ...). The relocated payload
  uses canonical names throughout, matching every downstream formula module.

---

## 2. Computable with wiring (not done yet, but the pieces exist)

- **Relocated angle contacts as structured evidence.** `evaluate_angularity()`
  already returns `is_conjunct_angle` / `conjunct_angle_name` / `orb` for a
  single body against a payload's angles. `compare_natal_to_relocated()`
  (this pass) loops it across every standard planet and asteroid to build
  `relocated_angle_contacts`. This is evidence-shaped output, not prose —
  ready for the content lead's block-key mapping.
- **Whole-sign house-change table.** Same idea: for every body, compare
  `natal_payload[...]['house']` to the relocated payload's recomputed
  house. Implemented this pass as `compare_natal_to_relocated()`'s
  `house_changes`.
- **Relocated chart-ruler / prominence / house-emphasis reads.** Because
  those formula modules only need a well-shaped payload, a relocated
  Place Resonance report could call `evaluate_chart_ruler(relocated_payload)`
  or `evaluate_house_emphasis(relocated_payload)` today, once the content
  lead decides which of those belong in the report surface. Not wired in
  this pass (out of scope: "no report rendering yet").
- **Destination resolution from a bare place string.** `build_relocated_payload()`
  accepts either pre-resolved `{latitude, longitude}` or a `{"location":
  "Chicago, IL"}` string and resolves it through the same offline resolver
  natal charts use. Ambiguous or unresolvable destinations raise the same
  kind of clear, catchable error `generate_payload()` raises for birth
  locations.
- **Predictive/timing clocks re-pointed at a destination.** `engine/returns.py`,
  `engine/profections.py`, `engine/progressions.py`, `engine/solar_arc.py`,
  and `engine/zodiacal_releasing.py` all currently compute **time-only**
  event moments (when a return/profection/progression becomes exact) from
  `natal_payload` — none of them build a chart with location-dependent
  angles. In principle a "relocated return chart" (a real technique — the
  return moment's chart cast for the destination instead of the birth
  place) could be built by taking the exact moment `scan_return_events()`
  already finds and feeding it, plus the destination coordinates, through
  the same `swe.houses()` call `location_services.py` uses. That is
  deliberately **not implemented in this pass** (see §3 and
  `ASYNC_WORKSTREAMS.md`'s explicit boundary against relocated returns
  before the static baseline is stable).

## 3. Not currently possible (real gaps, not just unwired)

- **Astrocartography.** No planetary-line geometry (where a planet is
  exactly angular anywhere on Earth) exists anywhere in the codebase. This
  requires a genuinely different calculation (great-circle projection of
  each planet's angularity condition across all longitudes/latitudes, not
  a single-point relocation). Zero scaffolding present.
- **Local Space.** No azimuth/horizon-line calculation exists. Also a
  different geometric method from Whole Sign relocation.
- **Parans.** No paran (simultaneous horizon/meridian crossing pair)
  detection exists. Would need new geometry, likely built on top of an
  astrocartography line engine once one exists.
- **Relocated returns as full charts.** `engine/returns.py` finds *when* a
  return is exact (a time-only scan against natal longitude — see
  returns.py:69-92); it does not cast a chart for that moment anywhere,
  relocated or not. Building one is straightforward given
  `location_services.py`'s angle-recalculation helper plus a
  `scan_return_events()` moment, but it is explicit new work, not
  something to retrofit into this pass.
- **Dynamic location-timing overlays** (`dynamic_location_timing` in the
  shared evidence contract) — depends on the static baseline being stable
  first, and on a decision for *which* clock (transits to relocated
  angles? profections read through a destination lens?) actually applies
  to a place rather than a date. Not started.

## 4. Deliberate scope decisions in this pass (documented, not silent)

- **No online geocoding fallback for destinations.** `natal_engine.py`
  falls back to Nominatim over the network when the offline resolver can't
  find a unique match (natal_engine.py:270-303). `location_services.py`
  intentionally does **not** wire that fallback in — it would make
  relocated-payload construction non-deterministic and network-dependent,
  which is wrong for a computational seam that should be equally testable
  offline. If a destination can't be resolved offline, `build_relocated_payload()`
  raises the same `UnresolvedLocationError`/`AmbiguousLocationError` the
  offline resolver raises, unmodified — the caller can decide whether to
  retry with a fuller place string or add online resolution later.
- **Aspects are not recomputed wholesale for the relocated payload.**
  Body-to-body aspects (e.g. Sun trine Moon) are location-invariant and are
  copied through unchanged. Aspects involving `Ascendant`, `Descendant`,
  `Midheaven`, `Imum_Coeli`, or `Vertex` are **excluded** from the copied
  list, because those angles move under relocation and a stale
  natal-angle aspect would misrepresent the relocated chart. Their
  relocated replacements are the `relocated_angle_contacts` produced by
  `compare_natal_to_relocated()` (§2), which are correctly computed against
  the new angles.
- **`location_services.py` is not registered with
  `formulas.standard.method_registry.MethodRegistry`.** That registry
  exists to route standard/niche/EO results through
  `formulas/report_surface.py`'s layered report bundle — i.e. it is a
  report-routing concern. This pass is explicitly non-reporting
  ("do not add report rendering yet"), so registration is deferred until
  a content/report surface actually consumes relocated evidence. Flagging
  this now so it isn't forgotten when Work Packet D3/D4 begins.

## 5. Pre-existing repo-truth mismatches found during this audit (unrelated to Location Services, noted per instructions rather than fixed)

While tracing the standard formula layer, five existing test files fail at
**collection** (not just at assertion) because they import from module
paths that no longer exist — they predate a refactor into
`formulas/standard/*`:

- `tests/test_angularity.py` → `from planetary_angularity_algorithm import ...`
- `tests/test_dignity.py` → `from expanded_dignity_matrix import ...`
- `tests/test_sect.py` → `from sect_calculation_algorithm import ...`
- `tests/test_planetary_condition.py` → `from planetary_condition import ...`
- `tests/test_phase7_rendering_system.py` → `import oracle_to_pdf`

Confirmed via `python -m pytest tests/ -q`: these 5 files error at import
time regardless of Location Services changes. Excluding them, baseline is
**283 passed, 1 pre-existing failure**
(`test_year_ahead_forecast_climate_render.py::test_client_report_omits_forecast_climate_section_in_three_report_outputs`,
unrelated to this work — a missing-birth-time copy string assertion in the
Year Ahead renderer). This is the true baseline this pass was measured
against; none of it was introduced by Location Services work, and none of
it is touched by this pass.

There is also an untracked `tmp/yearahead_baseline_workspace/tests/` copy
of the test suite in the repo working tree, which causes `pytest`
(un-scoped) to fail collection entirely on basename collisions. Running
`pytest tests/` (scoped) avoids it. Left untouched — not part of this
work packet.

### A real bug found while exercising the resolver for destination reuse

While confirming `engine/offline_place_resolver.py` is safe to call
directly for destinations (§4), a genuine, verified bug surfaced:
**26 of the 51 US state/territory postal codes in `US_STATES`
(offline_place_resolver.py:38-52) collide with real ISO country codes**
that `geonamescache` also uses. Verified programmatically against the
actual installed `geonamescache` country table (not guessed):

```
AL, AR, AZ, CA, CO, DE, GA, ID, IL, IN, KY, LA, MA, MD, ME, MN, MO, MS,
MT, NC, NE, PA, SC, SD, TN, VA
```

(5 Canadian province codes — `NL, NU, PE, SK, YT` — and 1 Australian
state code — `SA` — collide the same way.)

`_split_location()` (offline_place_resolver.py:114-138) resolves a
two-part `"City, XX"` string by checking `_lookup_country_code(XX)`
*before* treating `XX` as a region. Because e.g. `IL` is also Israel's
ISO code, `CA` is also Canada's, and `DE` is also Germany's,
`resolve_place("Chicago, IL")` and `resolve_place("Peoria, IL")` are
**misparsed as city="Chicago"/"Peoria", country=Israel** — confirmed
directly:

```
>>> _split_location("Chicago, IL")
('Chicago', None, 'IL')          # region=None, country='IL' (Israel)
>>> resolve_place("Chicago, IL")
UnresolvedLocationError: Could not resolve location "Chicago, IL" offline.
```

This resolves offline for `"Peoria, IL"` in the codebase's other passing
tests only because `engine.natal_engine._resolve_location()`
(natal_engine.py:306-316) silently falls back to a live Nominatim network
call when the offline lookup fails — masking the bug whenever network
access happens to be available, and failing outright when it isn't.

**This is a pre-existing bug in shared resolver infrastructure, not
something introduced by or in scope for this pass.** It is out of scope to
fix here (`offline_place_resolver.py` is used by the production birth-location
path too, and a fix deserves its own dedicated review and regression
tests), but it directly bears on Location Services: `build_relocated_payload()`
deliberately calls `resolve_place()` **without** the online fallback (§4),
so any destination given as `"City, XX"` where `XX` is in the collision
list above will fail to resolve offline, or — in states/regions that
coincidentally share a city name with a place in the colliding country —
could silently resolve to the wrong country's city. Callers should pass
a full state or country name (`"Chicago, Illinois"`) or pre-resolved
`latitude`/`longitude` for any of the 26 affected US states until the
resolver itself is fixed. Flagged separately as a follow-up task.

---

## 6. What this pass delivers

`engine/location_services.py`:

- `build_relocated_payload(natal_payload, destination) -> dict` — recomputes
  angles + Whole Sign houses for a destination at the **same Julian Day**,
  reassigns existing natal longitudes into their new houses, never mutates
  `natal_payload`.
- `compare_natal_to_relocated(natal_payload, relocated_payload) -> dict` —
  structural (non-prose) comparison: angle sign/longitude changes, per-body
  house changes, relocated angle contacts (via `evaluate_angularity` reuse),
  a `birth_instant_preserved` check, and an explicit `unsupported_methods`
  list for astrocartography / Local Space / parans / relocated returns.

`tests/test_location_services_relocated_payload.py` covers: UTC/Julian Day
preservation, no natal-payload mutation, relocated house changes, stable
angle output shape, offline-resolver reuse from a bare destination string,
and unsupported-method warnings.

Existing report types (`horoscope`, `personal_forecast`,
`predictive_sandbox`, `soul_ecosystem`, `weekly_horoscope`, `year_ahead`)
are untouched — `generate.py` has no new call path into
`location_services.py` in this pass.
