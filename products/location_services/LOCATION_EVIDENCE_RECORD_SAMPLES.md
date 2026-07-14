# Location Evidence Record — Samples

**Author:** Claude Code, Implementation and Integration Lead
**Status:** Round 2.5 (Evidence Contract Handoff Samples), with a Round 3
correction notice below — two issues this doc originally reported as open
bugs are now fixed. The samples below are left as originally generated
(historical record of what Round 2.5 actually found), with inline notes
added at each affected spot rather than silently rewritten.
**Purpose:** Give the content lead real, generated output to revise
`BLOCK_SCHEMA.md` against — every value below came out of
`build_location_evidence_record()`, none were hand-typed.
**Companion doc:** `products/location_services/BLOCK_SCHEMA_RECONCILIATION.md`
answers the "so what do I change in BLOCK_SCHEMA.md" question this doc's
raw data feeds into.

## Round 3 correction notice

Two things this doc flagged as open problems in Round 2.5 are now fixed
(`engine/location_services.py` and `formulas/standard/planetary_condition.py`,
verified by `tests/test_planetary_condition_confidence.py` and new tests in
`tests/test_location_services_evidence_record.py`):

1. **The `natal_modifiers[body].confidence` bug (see Sample C below) is
   fixed.** It now correctly reports `unknown_birth_time` /
   `approximate_birth_time` instead of always `exact_birth_time`.
2. **Warning-noise (see "What production scale actually looks like" below)
   now has a fix: `warning_summary`.** Raw `warnings` is unchanged (still
   38 items for the Chicago→Denver example below), but a new
   `warning_summary` field (top level and `appendix_trace.warning_summary`)
   collapses the 37 near-identical "no natal condition record" lines into
   one entry: `count: 37`, plus the affected body names in `examples`. See
   `LOCATION_EVIDENCE_RECORD_CONTRACT.md`'s `warning_summary` section for
   the full shape.

All names, dates, and locations here are synthetic test data — none of
this is client information.

## How these were generated

```python
from engine.location_services import build_location_evidence_record
from engine.natal_engine import generate_payload

natal = generate_payload({
    "name": "Sample B", "date": "1990-06-15", "time": "14:22",
    "location": "Chicago, Illinois",
})
record = build_location_evidence_record(natal, {"location": "Denver, Colorado"})
```

Exact scripts used for these three samples are in this repo's test
fixtures / this doc's source session — see
`tests/test_location_services_evidence_record.py` for the equivalent
`_build_natal_payload()` fixture used in Sample A. Note: destination
place names in these examples always use full state/country names
(`"Chicago, Illinois"`, not `"Chicago, IL"`) — see
`CAPABILITY_INVENTORY.md` §5 for the pre-existing US-state/ISO-country-code
collision bug in the offline resolver, unrelated to this pass but worth
knowing when picking your own sample destinations.

## Top-level shape (identical across all samples)

```text
formula_version, birth_context, destination_context, relocated_chart,
planet_house_changes, relocated_angle_contacts, natal_modifiers,
evidence_ranking, purpose_lens, relationship_to_place, appendix_trace,
unsupported_methods, warnings
```

`appendix_trace.unsupported_methods` and top-level `unsupported_methods`
are identical in every sample:

```json
["astrocartography", "local_space", "parans", "relocated_returns"]
```

---

## Sample A — High change, with a relocated angle contact

**Input:** synthetic 10-planet chart (no asteroids), Ascendant fabricated
in early Aries for a clean demo · relocated Chicago → Sydney, Australia ·
`purpose_lens="career"`, `relationship_to_place="possible_move"`.

### `planet_house_changes` (selected)

```json
[
  {
    "id": "house_change:Sun", "body": "Sun",
    "natal_house": 3, "relocated_house": 4, "house_changed": true,
    "natal_house_type": "cadent", "relocated_house_type": "angular",
    "movement_type": "newly_angular"
  },
  {
    "id": "house_change:Moon", "body": "Moon",
    "natal_house": 5, "relocated_house": 6, "house_changed": true,
    "natal_house_type": "succedent", "relocated_house_type": "cadent",
    "movement_type": "house_changed"
  }
]
```

(10 total, all 10 changed — this fixture was deliberately built with a
distant destination to exercise every movement_type.)

### `relocated_angle_contacts` (all 2)

```json
[
  {
    "id": "angle_contact:Venus:Imum_Coeli", "body": "Venus",
    "angle": "Imum_Coeli", "orb": 2.2425, "contact_strength": "moderate",
    "relocated_house_type": "angular"
  },
  {
    "id": "angle_contact:Jupiter:Midheaven", "body": "Jupiter",
    "angle": "Midheaven", "orb": 0.7575, "contact_strength": "tight",
    "relocated_house_type": "angular"
  }
]
```

### `natal_modifiers` (selected — 10 bodies present)

```json
{
  "Jupiter": {
    "condition_classification": "excellent", "overall_condition_score": 8.0,
    "was_natal_angular": false, "confidence": "exact_birth_time"
  },
  "Mars": {
    "condition_classification": "excellent", "overall_condition_score": 13.0,
    "was_natal_angular": true, "confidence": "exact_birth_time"
  }
}
```

(Full field list per body — `essential_dignity`, `accidental_dignity`,
`sect_condition`, `motion_condition`, `routing_tags`, `missing_inputs`,
`note` — is in `LOCATION_EVIDENCE_RECORD_CONTRACT.md` §2, not repeated
here.)

### `evidence_ranking` (full)

```json
{
  "primary_evidence": [
    "angle_contact:Venus:Imum_Coeli", "angle_contact:Jupiter:Midheaven",
    "house_change:Sun", "house_change:Mercury", "house_change:Venus",
    "house_change:Jupiter", "orientation_shift:Ascendant",
    "orientation_shift:Midheaven", "orientation_shift:Descendant",
    "orientation_shift:Imum_Coeli"
  ],
  "supporting_evidence": [
    "house_change:Moon", "house_change:Mars", "house_change:Saturn",
    "house_change:Uranus", "house_change:Neptune", "house_change:Pluto",
    "natal_modifier:Jupiter", "natal_modifier:Mars", "natal_modifier:Mercury",
    "natal_modifier:Moon", "natal_modifier:Neptune", "natal_modifier:Pluto",
    "natal_modifier:Saturn", "natal_modifier:Sun", "natal_modifier:Uranus",
    "natal_modifier:Venus"
  ],
  "contradictory_evidence": [],
  "speculative_or_excluded_evidence": ["astrocartography", "local_space", "parans", "relocated_returns"],
  "confidence_notes": []
}
```

### `warnings` (all 1)

```text
2 natal aspect(s) involving an angle (Ascendant/Descendant/Midheaven/
Imum_Coeli/Vertex) were excluded from the relocated payload's aspect list
because those angles move under relocation. See relocated_angle_contacts
from compare_natal_to_relocated() for the relocated equivalents.
```

---

## Sample B — Quiet / no-change case

**Input:** a *real* chart (`generate_payload()`, real Swiss Ephemeris
angles — see note below on why this matters), standard planets only,
relocated to its **own birth coordinates** (same lat/lon it was born at).

**Why a real chart, not a hand-built one:** a hand-built fixture's angles
are fabricated for test speed, not computed by `swe.houses()`. Relocating
a fabricated chart "to the same coordinates" would still show spurious
house changes, because `build_relocated_payload()` always computes real
angles regardless of what the natal payload's angles claim to be. This
invariant only means something against a real chart. (This is exactly the
bug I caught in my own Round 2 test suite before it shipped — see
`tests/test_location_services_evidence_record.py`'s
`test_no_house_changes_when_destination_matches_birth_coordinates`
docstring.)

### `planet_house_changes`: **0 of 14 changed** — every item reads `movement_type: "same_house"`.

### `relocated_angle_contacts` (all 5) — **not empty**

```json
[
  {"id": "angle_contact:Mars:Descendant", "body": "Mars", "angle": "Descendant", "orb": 1.8077, "contact_strength": "tight", "relocated_house_type": "angular"},
  {"id": "angle_contact:Jupiter:Midheaven", "body": "Jupiter", "angle": "Midheaven", "orb": 0.5997, "contact_strength": "tight", "relocated_house_type": "angular"},
  {"id": "angle_contact:Uranus:Imum_Coeli", "body": "Uranus", "angle": "Imum_Coeli", "orb": 7.203, "contact_strength": "wide", "relocated_house_type": "angular"},
  {"id": "angle_contact:Neptune:Imum_Coeli", "body": "Neptune", "angle": "Imum_Coeli", "orb": 1.6469, "contact_strength": "tight", "relocated_house_type": "angular"},
  {"id": "angle_contact:Chiron:Midheaven", "body": "Chiron", "angle": "Midheaven", "orb": 0.7353, "contact_strength": "tight", "relocated_house_type": "angular"}
]
```

**Naming this clearly rather than smoothing it over:** "quiet" and
"empty" are not the same thing. A same-place relocation is genuinely
quiet at the *house* level (nothing moves), but `relocated_angle_contacts`
reflects the chart's real, natal, always-true angularity — those 5
contacts exist whether or not anyone relocates anywhere, because they're
simply "is this body within 8° of an angle." **If the content lane wants
a way to distinguish "this angle contact is a relocation effect" from
"this angle contact is just a fact about the birth chart that relocation
didn't create," that distinction does not currently exist in the record.**
Right now `relocated_angle_contacts` always describes the relocated
chart's angularity, full stop — it doesn't diff against natal angularity
the way `planet_house_changes` diffs against natal houses. Worth deciding
before writing angle-contact prose blocks: should "no relocation effect"
angle contacts be excluded, flagged, or left as-is (arguably still
legitimate evidence — the person *does* live somewhere their Mars sits on
the Descendant, even if that was already sort of true).

### `natal_modifiers` (all 4 emphasized bodies)

```json
{
  "Jupiter": {"condition_classification": "excellent", "overall_condition_score": 11.0, "was_natal_angular": true, "confidence": "exact_birth_time"},
  "Mars": {"condition_classification": "excellent", "overall_condition_score": 14.0, "was_natal_angular": true, "confidence": "exact_birth_time"},
  "Neptune": {"condition_classification": "strong", "overall_condition_score": 7.0, "was_natal_angular": true, "confidence": "exact_birth_time"},
  "Uranus": {"condition_classification": "strong", "overall_condition_score": 7.0, "was_natal_angular": true, "confidence": "exact_birth_time"}
}
```

### `evidence_ranking` (full)

```json
{
  "primary_evidence": ["angle_contact:Mars:Descendant", "angle_contact:Jupiter:Midheaven", "angle_contact:Uranus:Imum_Coeli", "angle_contact:Neptune:Imum_Coeli", "angle_contact:Chiron:Midheaven"],
  "supporting_evidence": ["natal_modifier:Jupiter", "natal_modifier:Mars", "natal_modifier:Neptune", "natal_modifier:Uranus"],
  "contradictory_evidence": [],
  "speculative_or_excluded_evidence": ["astrocartography", "local_space", "parans", "relocated_returns"],
  "confidence_notes": []
}
```

Notice: **zero house-change evidence, but 5 primary items anyway.** A
"quiet" Place Resonance report is not necessarily a short one under this
ranking — the content lane should decide whether same-place-flavored
requests (`relationship_to_place="current_home"`, near-zero
`changed_house_count`) should suppress angle-contact evidence too, or
whether angle contacts stand on their own regardless of relocation
distance.

### `warnings` (all 2)

```text
68 natal aspect(s) involving an angle [...] were excluded from the
relocated payload's aspect list [...]
Chiron is relocation-emphasized but has no natal condition record
(evaluate_all_planetary_conditions covers Sun through Pluto only).
```

### `destination_context` — a real gap found while sampling

```json
{
  "display_name": "",
  "latitude": 41.85, "longitude": -87.65,
  "timezone": "America/Chicago",
  "coordinate_precision": "user_provided"
}
```

**`display_name` is an empty string, not `null` and not a computed
label.** This happens whenever a caller passes bare coordinates with no
`"location"` or `"display_name"` key (exactly what a "relocate to my own
birth coordinates" caller would naturally do). If a block or template
does `f"in {display_name}"`, this renders as `"in "`. Not fixed in this
pass — flagging so the content lane doesn't design a block that assumes
`display_name` is always populated.

---

## Sample C — Unknown birth time, showing confidence notes

**Input:** `simple_mode=True` chart (date only, no time), standard
planets only, relocated Portland, Oregon → Tokyo, Japan.

### `birth_context`

```json
{
  "birth_date": "1985-11-02",
  "birth_time": null,
  "birth_location": "Portland, Oregon, United States",
  "birth_timezone": "America/Los_Angeles",
  "birth_time_confidence": "unknown_birth_time",
  "utc_instant": "1985-11-02T20:00:00+00:00"
}
```

`birth_time` is correctly withheld (`null`), not silently filled with the
noon placeholder `generate_payload()` uses internally for chart math.

### `evidence_ranking.confidence_notes` (the mechanism working as designed)

```json
["Birth time confidence is 'unknown_birth_time'; angle-contact and house-placement evidence should be treated with reduced certainty."]
```

### `natal_modifiers` — **a real bug found while sampling, not this pass's code**

> **Fixed in Round 3.** Re-running this exact sample after the fix, every
> body now correctly reports `confidence: "unknown_birth_time"`. The
> original (buggy) output is preserved below as the historical finding
> that motivated the fix — see `LOCATION_EVIDENCE_RECORD_CONTRACT.md`'s
> "Round 3 updates" section for the current, correct behavior.

```json
{
  "Jupiter": {"condition_classification": "neutral", "overall_condition_score": 0.0, "confidence": "exact_birth_time"},
  "Venus":   {"condition_classification": "excellent", "overall_condition_score": 10.0, "confidence": "exact_birth_time"}
}
```

**Every `natal_modifiers[body].confidence` reads `"exact_birth_time"` even
though this whole chart is `unknown_birth_time`.** Verified directly, not
inferred:

```text
>>> unknown_chart["user_profile"]["birth_time_state"]
'unknown_birth_time'
>>> evaluate_all_planetary_conditions(unknown_chart)["Jupiter"].confidence
'exact_birth_time'
```

Root cause (pre-existing, in `formulas/standard/planetary_condition.py`'s
`_resolve_confidence()`): it only checks whether an Ascendant longitude is
present and whether angularity's `house_type` resolved to `"unknown"` —
neither of which is ever true for a `simple_mode` chart, because
`generate_payload()` always computes *some* Ascendant (the noon
placeholder) and that placeholder always produces a resolvable house
type. The function never actually looks at `payload.simple_mode` or
`birth_time_state`. This meant `natal_modifiers[body].confidence` was
not a trustworthy per-body signal — `birth_context.birth_time_confidence` /
`appendix_trace.birth_time_confidence` were the correctly-populated
alternatives at the time this sample was generated.

**Round 3 status:** fixed. `_resolve_confidence()` now checks
`payload.user_profile.birth_time_state` (falling back to `simple_mode`,
then to the original Ascendant/house_type check only when neither is
present) before deciding. `natal_modifiers[body].confidence` is trustworthy
again as of this fix. The resolver bug from Round 1 (US state/country code
collisions) remains open and out of scope for both Round 2.5 and Round 3.

### `warnings` (all 6, one truncated for length here — full list is short enough to show)

```text
64 natal aspect(s) involving an angle [...] were excluded [...]
Chiron is relocation-emphasized but has no natal condition record [...]
Lilith_BML is relocation-emphasized but has no natal condition record [...]
North_Node is relocation-emphasized but has no natal condition record [...]
South_Node is relocation-emphasized but has no natal condition record [...]
birth_context.birth_time is withheld: natal_payload was generated in
simple_mode. A placeholder noon time is used internally for chart math
only and is not a real reported birth time.
```

---

## What production scale actually looks like

All three samples above used **standard-planets-only** charts for
readability. A real `generate_payload()` chart also carries ~24 custom
asteroids (`ASTEROID_DICTIONARY` in `engine/natal_engine.py`) plus nodes
and Lilith — 34+ bodies total. I generated one full sample at production
scale (Chicago → Denver, a moderate relocation) to see what that actually
looks like, and it surfaced a usability problem:

- `planet_house_changes`: **47** items (not 10-14).
- `warnings`: **38** items, of which **37** are the near-identical
  templated line ("X is relocation-emphasized but has no natal condition
  record...") repeated once per un-covered asteroid, differing only by
  body name.
- `evidence_ranking.primary_evidence` / `supporting_evidence` similarly
  balloon into 20-30+ entry lists (unchanged by the Round 3 fix — see
  below, `warning_summary` addresses `warnings` specifically, not
  `evidence_ranking`'s lists).

**Round 3 status: fixed via `warning_summary`.** Raw `warnings` is
unchanged — still 38 items, same strings, same order — but
`warning_summary` (top level and `appendix_trace.warning_summary`) now
collapses the 37 repeated lines into one entry:

```json
{
  "id": "warning_summary:no_natal_condition_record",
  "key": "no_natal_condition_record",
  "message": "37 relocation-emphasized bodies have no natal condition record (evaluate_all_planetary_conditions covers Sun through Pluto only).",
  "count": 37,
  "examples": ["Aletheia", "Alma", "Angel", "Aphrodite", "Apollo", "..."]
}
```

plus one more entry for the single "68 natal aspect(s) involving an
angle..." warning (`count: 1`, unrecognized-template messages still get
their own entry rather than being dropped). Two entries total instead of
38 raw lines. A technical appendix block should render `warning_summary`,
not the raw `warnings` list, whenever it wants reader-facing or
even-just-legible appendix text; `warnings` remains available verbatim
for debugging/audit purposes.

`evidence_ranking.primary_evidence` / `supporting_evidence` list-length
growth at production scale is a separate, still-open consideration —
`warning_summary` only aggregates `warnings`. Worth a similar look if the
content lane finds those lists unwieldy too, but not addressed in this
pass since it wasn't part of the Round 3 brief.
