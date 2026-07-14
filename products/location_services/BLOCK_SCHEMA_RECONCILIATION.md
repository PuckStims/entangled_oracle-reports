# Block Schema Reconciliation — For The Content Lead

**Author:** Claude Code, Implementation and Integration Lead
**Status:** Round 2.5 (Evidence Contract Handoff Samples). **Round 3
update:** two items in §6 below (`natal_modifiers[body].confidence` and
`warnings` length) are now fixed — see the inline notes at each.
**Read alongside:** `LOCATION_EVIDENCE_RECORD_SAMPLES.md` (the raw data
this note interprets) and `LOCATION_EVIDENCE_RECORD_CONTRACT.md` (the full
field-by-field engine reference, more technical than this doc).

This is written for you, not as engine documentation — it's meant to be
the punch list you work from when revising `BLOCK_SCHEMA.md` into a v0.1
that matches what actually exists. I'll flag anything that makes a
content assumption awkward rather than smooth it over.

---

## 1. Confirmed — build blocks against these as-is

- **`relocated_angle_contact_blocks.json`'s core evidence fields** are
  real: `body`, `angle`, `orb`, `contact_strength` all exist exactly as
  proposed. (`body_natal_condition` and `birth_time_confidence` also
  exist, just sourced from `natal_modifiers` / `birth_context` rather than
  attached to the contact item itself — see §4.)
- **`planet_relocated_house_blocks.json`'s core evidence fields** are
  real: `body`, `natal_house`, `relocated_house`, `house_changed` all
  exist exactly as proposed.
- **`house_shift_blocks.json`'s key path** (`natal_house -> relocated_house`)
  is directly usable — both integers are present on every
  `planet_house_changes` item, independent of body.
- **`technical_appendix_blocks.json`'s required fields** are all present:
  `calculation_sources`, `tolerances`, `unsupported_methods`, `warnings`,
  `birth_time_confidence`, `coordinate_precision` — all live in
  `appendix_trace`.
- **Unsupported-method language** (your two templates in
  `EVIDENCE_TO_MEANING_MATRIX.md`'s "Unsupported Method Language" section)
  can key directly off `unsupported_methods` — it's always exactly
  `["astrocartography", "local_space", "parans", "relocated_returns"]`,
  no per-method status to worry about yet.

## 2. Must revise — long canonical angle names, not `ASC`/`MC`/`DSC`/`IC`

Every angle field in the record uses the long form:
`Ascendant`, `Midheaven`, `Descendant`, `Imum_Coeli`, `Vertex`.
`BLOCK_SCHEMA.md` Family 1's proposed key path (`MC -> Venus ->
contact_strength`) and its worked example both use short forms.

**Fix on your side, not the engine's:** rekey your block files to use
`Midheaven`, `Ascendant`, etc. as the top-level keys. Don't ask the
engine to emit short forms — every other standard formula module in this
codebase (`formulas/standard/*.py`) already standardized on long
canonical names, and `formulas/standard/normalization.py`'s
`ANGLE_ALIAS_MAP` exists specifically so *your* block selector can accept
either spelling from an author's shorthand and normalize before lookup,
if that's more convenient for whoever is writing block JSON by hand.

## 3. `wide` relocated angle contacts — how to handle them

The record uses three bands, not your proposed two:

| Band | Orb |
| --- | --- |
| `tight` | 0.00°–2.00° |
| `moderate` | 2.01°–5.00° |
| `wide` | 5.01°–8.00° |

Your Family 1 example only writes `tight` and `moderate` leaves. From an
implementation standpoint, you have three real options, and I'd lean
toward the first:

1. **Add a third `wide` leaf per angle/body pair**, written as the
   softest-confidence version of the same theme (barely-there contact,
   language should be tentative — "at the edge of," not "on"). This
   matches the band ceiling being tied to `evaluate_angularity`'s own
   8° cutoff: anything wider than that isn't flagged as a contact at all,
   so `wide` really is "the weakest thing that still counts."
2. **Fold `wide` into `moderate`** and treat the two-band system as
   correct, discarding the distinction in block selection (engine still
   computes it, block selector just doesn't branch on it).
3. **Drop `wide` contacts from angle-contact blocks entirely**, letting
   them surface only via `planet_house_changes` if the same body also had
   a house change. This under-uses real evidence but keeps prose
   confident.

I'd avoid (3) — a `wide` contact is still a real, computed fact (see
Sample B: `Uranus` at 7.2° from the IC), just a weaker one. (1) matches
your own "Minimum Evidence For A Strong Claim" section in
`EVIDENCE_TO_MEANING_MATRIX.md`, which already distinguishes "use softer
language when evidence is house-only" — `wide` is the angle-contact
equivalent of that softness tier.

## 4. What `movement_type` actually emits — narrower than proposed

Real values: `same_house`, `newly_angular`, `leaves_angular`,
`house_changed` (catch-all for any other real transition), `unknown`
(missing house data, shouldn't occur in practice). **The four
domain-flavored values your Family 2 example proposed —
`moves_public`, `moves_private`, `moves_relational`, `moves_operational`
— are not implemented.**

This isn't an oversight, it's a genuine open question that's yours to
close, not mine to guess at: which houses count as "public" vs.
"relational" vs. "operational" is an editorial call. Your own
`EVIDENCE_TO_MEANING_MATRIX.md` "House Shift Meaning" table already gives
each house a rich theme (Aries=1: "Embodiment, identity..."; 10:
"Career, reputation, authority..."), but that's 12 individual themes, not
a clean 4-bucket taxonomy — house 5 ("Creativity, pleasure, romance...")
doesn't obviously sort into any of your four proposed buckets, and
neither does house 8 or house 9.

**Two ways forward, your call:**

- **(a)** You author an explicit `{house_number: bucket}` mapping for all
  12 houses and hand it back — I'll wire it into
  `_evidence_planet_house_changes()` as a `domain_movement_type` field
  alongside the existing `movement_type`, computed the same deterministic
  way.
- **(b)** `house_shift_blocks.json` (already proposed with the
  `natal_house -> relocated_house` key path) does this bucketing itself
  at block-selection time, using the raw integers `planet_house_changes`
  already provides. No engine change needed.

I'd lean toward (b) — it keeps the domain taxonomy fully owned by you,
versionable independently of the engine, and it's exactly what Family 3's
key path already expects. But either is fine; I just won't invent the
bucket boundaries myself.

## 5. Fields that should stay optional or deferred

- **`relocated_chart_ruler_notes`** — not implemented, and not because
  it's hard exactly, but because the "which planet rules the relocated
  Ascendant sign" question is entangled with condition (dignity/sect) in
  the existing `evaluate_chart_ruler()` function, and condition must
  never be recomputed against a relocated chart (see
  `CAPABILITY_INVENTORY.md` §1). A safe structural-only version (pure
  sign→ruler lookup, no condition) is possible as future work if you
  actually want it — flag if so.
- **Everything already in your own "Fields That Should Stay Optional
  Until Proven" list** (`astrocartography.*`, `local_space.*`,
  `dynamic_location_timing.*`, `relocated_return_chart`, `parans`) —
  confirmed still true, nothing changed here.
- **`purpose_lens_blocks.json` fields** (`supporting_evidence_ids`,
  `contradictory_evidence_ids`) — the engine emits `evidence_ranking`
  with real IDs, but nothing purpose-lens-aware filters or tags them yet.
  You already deprioritized this family to "write later" in
  `BLOCK_SCHEMA.md`'s own priority order, so this should be a non-surprise,
  just confirming the engine matches that sequencing.
- **`contradictory_evidence`** — always an empty list right now (see §7).

## 6. What not to ask the engine for yet

- ~~Don't ask for `natal_modifiers[body].confidence` to mean anything
  per-body-precise for approximate/unknown-birth-time charts.~~
  **Fixed in Round 3.** `formulas/standard/planetary_condition.py`'s
  `_resolve_confidence()` now checks the chart's actual
  `birth_time_state`/`simple_mode` before deciding. This field is
  trustworthy now — safe to build `natal_modifier_blocks.json`'s
  confidence-aware leaves against it directly, not just against
  `birth_context.birth_time_confidence`. (That chart-level field remains
  correct too and is still the right choice when you want one confidence
  value for the whole report rather than per body.)
- **Don't design a block that assumes `destination_context.display_name`
  is always a non-empty string.** It's `""` when a caller supplies bare
  coordinates with no name (see Sample B) — a template doing
  `f"in {display_name}"` will silently render `"in "`. (Not addressed in
  Round 3 — still open.)
- ~~Don't design `technical_appendix_blocks.json`'s `warning` key-path
  family assuming `warnings` is always short.~~ **Fixed in Round 3** via a
  new `warning_summary` field (top level and
  `appendix_trace.warning_summary`) — render `warning_summary`, not raw
  `warnings`, for appendix prose. A later method-boundary correction now
  excludes EO custom asteroids from Location Services evidence entirely, so
  the old 37-line asteroid warning case should no longer occur in this
  product stack. Raw `warnings` is untouched for anyone who wants the
  literal list. `technical_appendix_blocks.json`'s
  `warning_summary -> warning_key` key path already anticipated this shape
  — you were right that it should be selector-facing; it just turned out
  cheap enough to compute in the engine too, so both are available.
  `evidence_ranking.primary_evidence` /
  `supporting_evidence` can still balloon at production scale — that's a
  separate, still-open list-length question `warning_summary` doesn't
  touch.
- **Don't ask for a relocation/natal distinction inside
  `relocated_angle_contacts`.** It always describes the relocated chart's
  angularity as a standalone fact — it does not currently flag "this
  contact would exist even without relocating" vs. "this contact is new."
  Sample B shows this concretely: 0 house changes, but 5 angle contacts
  still present.

## 7. `contradictory_evidence` — still empty, and why that's not a bug

`EVIDENCE_TO_MEANING_MATRIX.md`'s "Evidence Conflict Handling" section
(visibility vs. privacy, expansion vs. structure, etc.) is real and
useful, but detecting those conflicts requires the same kind of
house/angle-domain taxonomy call as `movement_type`'s missing four
buckets (§4) — "does this evidence represent visibility or privacy"
needs the same house→domain mapping. I'd bet these two gaps
(`movement_type`'s domain buckets and `contradictory_evidence`'s conflict
detection) share one underlying taxonomy and one fix, whenever you're
ready to author it.

## 8. Suggested selector-safe key paths, based on the actual record shape

These are paths I can already see working cleanly against the real
record, offered as a starting point for however you want to structure
block file key paths — not a demand that you use these exact shapes:

```text
relocated_angle_contacts[*].angle -> relocated_angle_contacts[*].body -> relocated_angle_contacts[*].contact_strength
planet_house_changes[*].body -> planet_house_changes[*].movement_type
planet_house_changes[*].natal_house -> planet_house_changes[*].relocated_house   (Family 3, as proposed)
natal_modifiers[body].was_natal_angular  (drives your "Natal Angularity" rule directly, both branches)
purpose_lens -> (your own evidence_domain / fit_type taxonomy, unvalidated by the engine)
relationship_to_place -> (same — plain pass-through string, no engine-side enum)
```

One structural note: `relocated_angle_contacts` and `planet_house_changes`
are **flat lists of self-describing items with stable `id`s**, not nested
dicts (`angle -> body -> ...`). This was a deliberate v0.1 choice — see
`LOCATION_EVIDENCE_RECORD_CONTRACT.md` §3 for the reasoning (mainly: your
own Family 1 and Family 2 examples nest in *different* axis orders from
each other, so I didn't want to guess which nesting the engine should
bake in). Building your nested key-path index is a one-line
reshape (`{item["angle"]: {item["body"]: item["contact_strength"]} for
item in relocated_angle_contacts}`) — say the word if you'd rather the
engine hand you that shape directly instead of the flat list, and I'll
add it alongside (not instead of) the flat list.
