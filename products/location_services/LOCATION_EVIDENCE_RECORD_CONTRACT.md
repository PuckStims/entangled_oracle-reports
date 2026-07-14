# Location Evidence Record Contract — v0.1

**Author:** Claude Code, Implementation and Integration Lead
**Status:** Round 2 (Contract Formation) deliverable, updated in Round 3
(two bounded fixes — see "Round 3 updates" below).
**Consumer:** ChatGPT content lane, validating against `BLOCK_SCHEMA.md` and
`CONTENT_LEAD_HANDOFF.md`.
**Source:** `engine/location_services.py`, function `build_location_evidence_record()`.
**Verified against:** `tests/test_location_services_evidence_record.py`,
`tests/test_location_services_relocated_payload.py`, and
`tests/test_planetary_condition_confidence.py` (66 tests total across the
three, passing) — every field named below is backed by a real, running
test, not a sketch.

## Round 3 updates

Two bounded fixes landed after Round 2.5's sampling pass surfaced them:

1. **The `natal_modifiers[body].confidence` bug is fixed.** It previously
   always reported `"exact_birth_time"` regardless of the chart's actual
   birth-time state (root cause: `formulas/standard/planetary_condition.py`'s
   `_resolve_confidence()` never checked `simple_mode`/`birth_time_state`).
   It now correctly reflects the chart's real state. **You can now trust
   `natal_modifiers[body].confidence` for approximate/unknown-birth-time
   charts** — this reverses the earlier caveat below and in
   `BLOCK_SCHEMA.md`. `birth_context.birth_time_confidence` /
   `appendix_trace.birth_time_confidence` remain the chart-level source of
   truth either way.
2. **`warning_summary` is new** — a stable, aggregated view of `warnings`
   at both top level and `appendix_trace.warning_summary`. See §2 below.
   The raw `warnings` list is completely unchanged (same strings, same
   order, same count) — this is a pure addition.

This document answers `CONTENT_LEAD_HANDOFF.md`'s and `BLOCK_SCHEMA.md`'s
validation questions directly, then documents where v0.1 diverges from the
originally sketched shape (`ASYNC_WORKSTREAMS.md`'s `LocationEvidenceRecord`)
and why.

---

## 1. Validation questions, answered

### What canonical body names will the evidence record emit?

Whatever `engine/natal_engine.py`'s `STANDARD_PLANETS` already use — no
new naming layer was introduced. The EO custom asteroid load is deliberately
excluded from Location Services evidence; it belongs to natal/report-specific
EO products, not the astrocartography/relocation stack.
Confirmed by `test_house_change_items_cover_every_standard_planet`:

```text
Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto,
Chiron, North_Node, South_Node, Lilith_BML
```

`planet_house_changes` and `relocated_angle_contacts` will use these exact
names in their `body` field.

**Important asymmetry:** `natal_modifiers` covers only the 10 core bodies
(`Sun` through `Pluto` — `formulas.standard.planetary_condition.STANDARD_BODIES`).
If `Chiron`, `North_Node`, `South_Node`, or `Lilith_BML` is relocation-emphasized
(a house change or angle contact), it will appear in `planet_house_changes` /
`relocated_angle_contacts` but **not** in `natal_modifiers` — a warning is
appended instead (`"{body} is relocation-emphasized but has no natal
condition record..."`). Dignity/sect condition for Chiron, nodes, and Lilith
is simply not computed anywhere in the standard formula layer
today; this isn't a gap this pass introduced.

### What canonical angle names will it emit: `ASC`/`MC`/`DSC`/`IC` or long names?

**Long canonical names only**: `Ascendant`, `Midheaven`, `Descendant`,
`Imum_Coeli`, `Vertex` — matching
`formulas/standard/normalization.py`'s `CANONICAL_ANGLE_NAMES`. `BLOCK_SCHEMA.md`'s
Family 1 example uses short forms (`MC`, `ASC`) in its proposed key paths;
**the engine does not emit those**. If the content lane wants short-form
key paths for block-file authoring convenience, translate at the block
selector layer using `formulas.standard.normalization.ANGLE_ALIAS_MAP`
(already exists, already bidirectional) — don't ask the engine to change
its canonical vocabulary, since every other standard formula module in the
codebase depends on the long form.

### Can v0.1 emit relocated angle contacts, or only relocated houses and house changes?

**Both.** `relocated_angle_contacts` is a real, computed list in v0.1 (see
§2 below), built by reusing `formulas.standard.angularity.evaluate_angularity()`
against the relocated payload — the same function the rest of the codebase
already uses for natal angularity, just pointed at relocated angles/houses
instead. Verified non-empty for the reference fixture in
`test_angle_contact_items_have_required_fields`.

### What orb and strength bands can v0.1 support for relocated angle contacts?

Three bands, ceiling matched exactly to `evaluate_angularity`'s own default
`angle_orb=8.0` (so no contact this module reports is ever "unbanded"):

| Band | Orb range |
| --- | --- |
| `tight` | 0.00° – 2.00° |
| `moderate` | 2.01° – 5.00° |
| `wide` | 5.01° – 8.00° |

Verified in `test_contact_strength_bands`. These are structural bands
(distance only) — they carry no claim about interpretive strength; that
translation belongs to the content lane. `BLOCK_SCHEMA.md`'s Family 1
example uses `tight`/`moderate` as its two top-level keys; a third `wide`
band exists here and needs a decision from the content lane (fold into
`moderate`, add a third prose tier, or drop `wide` contacts from
angle-contact blocks entirely and let them surface only through
`planet_house_changes`).

### Can v0.1 include natal condition summaries for emphasized planets without rerunning the whole report bundle?

**Yes**, and this is the most important engineering answer in this
document. `natal_modifiers` calls
`formulas.standard.planetary_condition.evaluate_all_planetary_conditions(natal_payload)`
directly — the narrow standard-formula function, **not**
`formulas.report_surface.build_layered_report_bundle()` (the heavier
report-routing wrapper, which stays entirely out of scope for Location
Services in this pass). This is safe specifically because the payload
argument is always `natal_payload`, never the relocated payload —
verified by `test_evaluate_all_planetary_conditions_is_only_ever_called_with_natal_payload`,
which patches the function and asserts every call it receives `is natal`
and `is not relocated`.

Concretely, `natal_modifiers[body]` carries: `condition_classification`,
`overall_condition_score`, `essential_dignity` (full dignity profile),
`accidental_dignity` (natal angularity — house type, natal angle
conjunction), `sect_condition`, `motion_condition`, `natal_house_type`,
`was_natal_angular` (bool), `routing_tags`, `confidence`, `missing_inputs`.
This directly operationalizes `EVIDENCE_TO_MEANING_MATRIX.md`'s "Natal
Angularity" rule ("if a planet is already natal-angular and becomes
relocated-angular, treat as repeated emphasis...") — `was_natal_angular`
plus `planet_house_changes[...].relocated_house_type == "angular"` gives
the block selector everything needed to implement that rule directly.

**Scope of "emphasized":** `natal_modifiers` only covers bodies that
appear in `relocated_angle_contacts` or have `house_changed: true` in
`planet_house_changes` — not every body in the chart. This keeps the
record proportionate to what's actually locationally significant rather
than dumping the full natal condition bundle every time. See
`test_natal_modifiers_only_cover_emphasized_bodies`.

### What exact fields describe birth-time confidence and angle sensitivity?

- `birth_context.birth_time_confidence` — the controlled state string from
  `formulas/standard/confidence.py` (`exact_birth_time` /
  `approximate_birth_time` / `unknown_birth_time`), read straight from
  `natal_payload.user_profile.birth_time_state`.
- `appendix_trace.birth_time_confidence` — same value, duplicated at the
  appendix level for technical-appendix block convenience.
- `evidence_ranking.confidence_notes` — a plain-language note is appended
  **only** when birth time is not exact
  (`test_evidence_ranking_adds_confidence_note_for_non_exact_birth_time`),
  empty list otherwise. This is a real signal, not a placeholder.
- **`birth_context.birth_time` is `None` whenever `natal_payload.simple_mode`
  is true**, even though `natal_engine.generate_payload()` internally uses a
  noon placeholder to make chart math possible. That placeholder is
  deliberately never surfaced as if it were a real reported birth time — see
  `test_top_level_keys_match_content_lead_handoff`'s sibling
  `birth_context` tests and the inline warning
  `"birth_context.birth_time is withheld: ... A placeholder noon time is
  used internally for chart math only..."`.

### How will unsupported methods be represented?

A single frozen tuple, `UNSUPPORTED_METHODS = ("astrocartography",
"local_space", "parans", "relocated_returns")`, surfaced in **three**
places for convenience, always identical (same constant, no drift risk):
top-level `unsupported_methods`, `appendix_trace.unsupported_methods`, and
`evidence_ranking.speculative_or_excluded_evidence`. No per-method status
object (e.g. "planned" vs. "not started") exists yet — all four are
flatly unsupported in v0.1. If the content lane wants per-method
messaging (`EVIDENCE_TO_MEANING_MATRIX.md`'s "Unsupported Method Language"
section gives two different templates — "not included" vs. "can later
add"), that's a block-selection-time decision keyed on the method name
string, not something the engine needs to differentiate.

### What fields are definitely not computable yet and should be removed from v0.1 block requirements?

See §3 below — this is substantial enough to warrant its own section.

---

## 2. Full field reference

### `birth_context`

| Field | Source | Notes |
| --- | --- | --- |
| `birth_date` | parsed from `user_profile.local_datetime` | `None` if unparseable (warned) |
| `birth_time` | parsed from `user_profile.local_datetime` | `None` in simple_mode (see above) |
| `birth_location` | `natal_payload.birth_location` | |
| `birth_timezone` | `user_profile.timezone` | birth-location timezone, never destination |
| `birth_time_confidence` | `user_profile.birth_time_state` | controlled state string |
| `utc_instant` | `user_profile.utc_datetime` | ISO string, preserved exactly |
| `julian_day` | `user_profile.julian_day` | preserved exactly, see `birth_utc_preserved` invariant tests |
| `calculation_profile` | `user_profile.methodology` | always `tropical_whole` in production |

### `destination_context`

| Field | Source | Notes |
| --- | --- | --- |
| `display_name` | resolved or user-provided | |
| `latitude` / `longitude` | resolved or user-provided | rounded to 4 decimals |
| `timezone` | resolved or user-provided | `None` if never supplied (warned) |
| `coordinate_precision` | `"user_provided"` or `"offline_geonamescache"` | see §3, "coordinate_precision is a provenance tag, not a precision measurement" |

### `relocated_chart`

`house_system`, `zodiac` (both fixed at `Whole Sign` / `Tropical` in this
methodology), `angles` (all 5 canonical angles, full `zodiac_position()`
shape), `house_cusps` (all 12 `House_1..House_12` records).

### `planet_house_changes` — list, one item per Location Services standard body

```json
{
  "id": "house_change:Sun",
  "body": "Sun",
  "natal_house": 3,
  "relocated_house": 10,
  "house_changed": true,
  "natal_house_type": "cadent",
  "relocated_house_type": "angular",
  "movement_type": "newly_angular"
}
```

`movement_type` is one of `same_house`, `newly_angular`, `leaves_angular`,
`house_changed`, `unknown` (missing house data). **This is a smaller set
than `BLOCK_SCHEMA.md` Family 2/3 proposed** — see §3.

### `relocated_angle_contacts` — list, one item per (body, angle) conjunction found

```json
{
  "id": "angle_contact:Venus:Midheaven",
  "body": "Venus",
  "angle": "Midheaven",
  "orb": 1.42,
  "contact_strength": "tight",
  "relocated_house_type": "angular"
}
```

Only bodies actually within 8° of an angle appear here — this is not a
padded/complete list.

### `natal_modifiers` — dict keyed by body name, emphasized bodies only

See §1 above for the full field list. `source_standard_formula` and a
`note` field are included on every entry specifically so a content author
or QA reviewer can see at a glance that this came from the natal chart,
not the relocated one, without reading engine code.

### `evidence_ranking`

```json
{
  "primary_evidence": ["angle_contact:Venus:Midheaven", "house_change:Jupiter", "orientation_shift:Ascendant"],
  "supporting_evidence": ["house_change:Moon", "natal_modifier:Venus"],
  "contradictory_evidence": [],
  "speculative_or_excluded_evidence": ["astrocartography", "local_space", "parans", "relocated_returns"],
  "confidence_notes": []
}
```

Ranking rules implement `EVIDENCE_TO_MEANING_MATRIX.md`'s "Evidence
Priority" section **exactly as written**, with no new interpretive
judgment introduced:

- **Primary:** any angle contact; any house change with
  `movement_type == "newly_angular"`; any angle with a natal→relocated
  sign change (`orientation_shift:{angle}`, Vertex excluded — Vertex sign
  changes aren't treated as chart-orientation shifts here since Vertex
  isn't one of the four primary chart axes); any body repeated across both
  an angle contact and a house change (promoted even if that house change
  isn't itself `newly_angular` — see
  `test_evidence_ranking_promotes_repeated_body_to_primary`).
- **Supporting:** all other real house changes; every `natal_modifiers`
  entry (`natal_modifier:{body}`).
- **Contradictory:** always empty in v0.1 — see §3.
- **Speculative/excluded:** the four unsupported methods.
- **Confidence notes:** one note when birth time isn't exact; otherwise
  empty.

### `purpose_lens`, `relationship_to_place`

Plain strings (or `None`), passed through **unchanged and unvalidated**.
The engine does not check these against `BLOCK_SCHEMA.md`'s enumerated
lens/relationship values — that taxonomy belongs to the content lane's
schema, not the engine layer. Passing a non-string, non-`None` value
raises `ValueError` (type safety only, not taxonomy validation).

### `appendix_trace`

`formula_version`, `relocated_payload_formula_version`,
`calculation_sources` (a plain list of the actual function paths used —
useful for debugging, not reader-facing), `tolerances` (the orb/band
table from §1), `unsupported_methods`, `warnings`, `warning_summary`,
`birth_time_confidence`, `coordinate_precision`, `methodology`.

### `warning_summary` (Round 3)

An aggregated, countable view of `warnings`, computed by
`_summarize_warnings()` and placed both at top level and
`appendix_trace.warning_summary` (identical contents, same
convenience-duplicate pattern as `unsupported_methods`). **`warnings`
itself is completely unchanged** — same strings, same order, same
count — `warning_summary` is purely additive.

```json
[
  {
    "id": "warning_summary:no_natal_condition_record",
    "key": "no_natal_condition_record",
    "message": "37 relocation-emphasized bodies have no natal condition record (evaluate_all_planetary_conditions covers Sun through Pluto only).",
    "count": 37,
    "examples": ["Aletheia", "Alma", "Angel", "..."]
  }
]
```

Two known per-body-repeated warning templates (both from within this
module) are recognized by pattern and collapsed with `count` +
`examples`: the "no natal condition record" one shown above, and "{body}
is missing from the relocated payload; house comparison skipped."
**Every other warning message is grouped only with other messages that
are byte-identical to it** — a literal duplicate collapses to `count: 2`
with the same `message`, but two genuinely different one-off warnings
each get their own entry with `count: 1`. `key` for those is a short
stable hash of the message text (`other_xxxxxxxx`), not a human-readable
name — `message` carries the actual reader-facing text either way.

This is a fixed, closed set of two templates, not a generic
"detect any parameterized string" mechanism — if a future warning message
in `engine/location_services.py` gets a per-body variable inserted the
same way, it needs its own entry in `_WARNING_TEMPLATES` to be recognized
as a template rather than falling back to literal-string grouping (which
still works, it just won't collapse across different body names).

### `unsupported_methods`, `warnings`, `warning_summary` (top-level)

Convenience duplicates of `appendix_trace`'s versions of the same fields —
same constant / same list object contents, not independently derived, so
there is no drift risk between the top-level and nested copies.

---

## 3. Where this diverges from `BLOCK_SCHEMA.md` / `ASYNC_WORKSTREAMS.md`, and why

Documented per the standing instruction to flag mismatches rather than
paper over them.

### `movement_type` only has 4 real values, not the 7 `BLOCK_SCHEMA.md` Family 2 proposed

`BLOCK_SCHEMA.md` proposes: `newly_angular`, `leaves_angular`,
`moves_public`, `moves_private`, `moves_relational`, `moves_operational`,
`same_house`, `fallback`. The engine implements the first two plus
`same_house` and a catch-all `house_changed` — all four are pure
angularity-transition facts, derivable from `formulas.standard.angularity.HOUSE_TYPES`
with zero interpretive judgment.

The four domain-flavored types (`moves_public` / `moves_private` /
`moves_relational` / `moves_operational`) require a **house → domain
category** mapping the content lane hasn't authored yet.
`EVIDENCE_TO_MEANING_MATRIX.md`'s "House Shift Meaning" table (its "Meaning"
column) gives rich per-house *themes* — prose-adjacent, not a clean
4-bucket enum — so I did not invent a mapping from those themes to
`moves_public`/etc. myself; that's an editorial call (is house 5 "public"
or something else? is house 8 "relational" or "operational"?) that
belongs to the content lane, not the engine.

**Recommendation:** either (a) the content lane authors an explicit
`house -> {public, private, relational, operational}` table and hands it
back, and I'll add a `domain_movement_type` field computed from it, or (b)
`house_shift_blocks.json` (Block Family 3, already proposed as
`natal_house -> relocated_house` key-path) does this categorization
itself at block-selection time using the raw `natal_house` /
`relocated_house` integers `planet_house_changes` already provides — no
engine change needed for that path. I'd lean toward (b): it keeps the
domain taxonomy fully owned by content, versionable independently of the
engine, and it's exactly what Block Family 3's key path already expects.

### `relocated_angle_contacts` and `planet_house_changes` are flat lists, not nested key-path dicts

`BLOCK_SCHEMA.md`'s examples show nested dicts (`angle -> body ->
contact_strength`, `body -> relocated_house -> movement_type`) matching
other EO block file conventions. v0.1 emits flat lists of self-describing
items with stable `id`s instead. Reasoning: a flat list is simpler to
test for determinism, matches how `natal_payload.aspects` is already
shaped elsewhere in this codebase, and doesn't force a single nesting
order on the content lane (block selection can build whichever nested
index it wants from the flat list — `{item["angle"]: {item["body"]:
item["contact_strength"]}}` is a one-line comprehension). If the content
lane's block selector genuinely needs the nested shape as the wire
format rather than an internal reshaping step, say so and I'll add a
second nested view alongside the flat one rather than replace it — happy
to carry both if useful, but won't guess which nesting order without a
concrete key-path spec, since Family 1 nests `angle -> body` while Family
2 nests `body -> house`, i.e. the two proposed families don't even agree
on axis order with each other.

### `relocated_chart_ruler_notes` (from `ASYNC_WORKSTREAMS.md`'s original sketch) is not implemented

Not in `BLOCK_SCHEMA.md`'s actual context-field list either, so this may
already be a non-issue — flagging for completeness. `formulas.standard.chart_ruler.evaluate_chart_ruler()`
internally calls `evaluate_dignity`, `evaluate_chart_sect`, and
`evaluate_planetary_sect` (chart_ruler.py:89-92) — all condition-bearing,
all forbidden against a relocated payload per the sect/horizon boundary
(see `CAPABILITY_INVENTORY.md` §1's "important, non-obvious finding"). A
genuinely safe "which planet rules the relocated Ascendant sign" fact
*is* computable (a pure sign→ruler dictionary lookup, no condition
involved), but that's a new, narrower helper this pass didn't build since
nothing downstream currently asks for it. Flagging as available future
work, not implemented now.

### `purpose_lens` / `relationship_to_place` are top-level, not nested under `destination_context`

`ASYNC_WORKSTREAMS.md`'s original `LocationEvidenceRecord` sketch nests
`user_relationship` and `purpose_lens` inside `destination_context`. The
Round 2 task brief that produced this pass listed them as their own
top-level sections instead, matching `CONTENT_LEAD_HANDOFF.md`'s flat
field-family list. Implemented as top-level per the more recent,
explicit instruction — flagging the divergence from the original sketch
so it isn't mistaken for an oversight.

### `contradictory_evidence` is always empty

`EVIDENCE_TO_MEANING_MATRIX.md`'s "Evidence Conflict Handling" section
(visibility vs. privacy, expansion vs. structure, etc.) describes real
conflict types, but detecting them requires comparing evidence *across*
domains with judgment calls this pass didn't attempt to encode
(e.g. "MC signature" vs. "IC/Moon signature" requires deciding which
angle contacts and house changes count as representing which domain —
the same kind of taxonomy gap as `movement_type` above). Left honestly
empty rather than faked. Worth a dedicated pass once the content lane's
domain taxonomy (needed for `movement_type` too) exists — the two gaps
likely share a solution.

### `coordinate_precision` is a provenance tag, not a precision measurement

Neither `natal_engine.py` nor `offline_place_resolver.py` computes actual
positional accuracy (e.g. "±2km") — `geonamescache` gives city centroids,
nothing more granular. `coordinate_precision` is populated with
`"user_provided"` (caller passed exact lat/lon directly) or
`"offline_geonamescache"` (resolved from a place name, so precision is
"somewhere at this city's centroid," not exact). If the content lane
needs true precision bands, that data doesn't exist anywhere in this
codebase yet and isn't a Location Services–specific gap.

---

## 4. Reused, not reinvented

Everything in this record was assembled by calling existing functions
with existing arguments — no new astronomical calculation was written for
this pass beyond what Round 1's `build_relocated_payload()` /
`compare_natal_to_relocated()` already did:

- `formulas.standard.angularity.evaluate_angularity()` — relocated angle
  contacts (called against the relocated payload — this is the
  relocation-sensitive one).
- `formulas.standard.planetary_condition.evaluate_all_planetary_conditions()` —
  natal modifiers (called against `natal_payload` only — this is the
  boundary the whole task hinges on).
- `formulas.standard.angularity.HOUSE_TYPES` — the angular/succedent/
  cadent lookup backing both `movement_type` and `natal_house_type` /
  `relocated_house_type`.
- `engine.offline_place_resolver.resolve_place()` — destination resolution
  from a bare place name, reused unchanged from Round 1 (including its
  known collision bug — see `CAPABILITY_INVENTORY.md` §5 — which remains
  out of scope for this pass and is tracked separately).

Not registered with `formulas.standard.method_registry.MethodRegistry` —
same reasoning as Round 1: that registry routes standard/niche/EO results
through `formulas/report_surface.py`'s layered report bundle, a
report-routing concern this pass still deliberately stays out of.

## 5. Still not implemented (unchanged from Round 1, restated for this doc's completeness)

Astrocartography, Local Space, parans, relocated returns, and any dynamic
location-timing overlay. `unsupported_methods` names the first four
explicitly on every record; dynamic timing isn't named because the static
baseline this pass builds is the prerequisite `ASYNC_WORKSTREAMS.md`
requires before dynamic timing work can even start.
