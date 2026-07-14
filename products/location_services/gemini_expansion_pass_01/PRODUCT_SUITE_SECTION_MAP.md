# Product Suite Section Map — Location Services

**Status:** GEMINI FIRST-PASS DRAFT. Not authoritative. Requires
ChatGPT/Codex product/content review and Claude Code implementation review
before any section becomes a build target.

**Source documents:** `PRODUCT_STACK.md`, `PROSE_GUIDE.md`,
`EVIDENCE_TO_MEANING_MATRIX.md`, `BLOCK_SCHEMA.md`,
`LOCATION_EVIDENCE_RECORD_CONTRACT.md`

---

## Reading Guide

Each product section below defines:

- **Section purpose** — what the section is for in the report
- **Evidence needed** — the `LocationEvidenceRecord` fields required
- **Current capability status** — what v0.1 backend can actually provide
- **Excluded / unsupported claims** — what must not appear in this section
- **Prose deferred?** — whether final prose authorship should wait

Capability status labels used throughout:

- `AVAILABLE_NOW` — field exists in v0.1 `LocationEvidenceRecord`, tested
- `AVAILABLE_WITH_WIRING` — data computable from existing engine, needs
  selector/loader/new function to expose it
- `NOT_COMPUTABLE` — data does not exist in engine; would require new
  computation or new method
- `FUTURE_METHOD` — requires an entirely new astrological method not yet
  started (astrocartography geometry, Local Space engine, paran engine, etc.)

---

## Product 1: Place Resonance

**v0.1 foundation exists. This is the primary build target.**

The Place Resonance section map is grounded in the existing block scaffold
in `blocks/plainspeak/` (745 TODO leaves, delivered in Round 4). This
section map describes the full report shell; some sections are already
scaffolded, others are pending selector taxonomy.

### Section 1.1 — Place Signature

**Purpose:** Name the dominant symbolic emphasis of the destination.
Single-statement opening that tells the reader what this place foregrounds
above all else.

**Evidence needed:**
- `evidence_ranking.primary_evidence`
- `evidence_ranking.supporting_evidence`
- `relocated_angle_contacts` (primary items)
- `planet_house_changes` (newly_angular items)
- `birth_context.birth_time_confidence`

**Current capability status:** `AVAILABLE_NOW` for evidence fields. Selector
logic that produces a single dominant theme label from ranked evidence is
`AVAILABLE_WITH_WIRING` — the synthesis categories are defined in
`location_synthesis_blocks.json` (scaffolded in Round 4) but selector code
that reads evidence_ranking and selects a synthesis key does not yet exist.

**Excluded claims:** No "best place" language. No guaranteed outcomes. No
map-line evidence.

**Prose deferred?** YES — TODO leaf body. `_note` guidance exists in
`location_synthesis_blocks.json`.

---

### Section 1.2 — What Changes Here

**Purpose:** Describe the main shift from natal baseline to relocated
expression. Compare where planets were natally to where they are relocated.
Not personality change — functional foregrounding.

**Evidence needed:**
- `planet_house_changes[*]` where `house_changed == true`
- `planet_house_changes[*].movement_type`
- `relocated_angle_contacts[*]`
- `natal_modifiers[body].was_natal_angular`

**Current capability status:** `AVAILABLE_NOW`. All required fields tested
and present in v0.1.

**Excluded claims:** No "rewriting the chart" language. No domain-bucket
labels (moves_public / moves_private etc.) until taxonomy exists.

**Prose deferred?** YES — TODO leaf body. Block family is
`planet_relocated_house_blocks.json`, scaffolded in Round 4.

---

### Section 1.3 — Strongest Structural Evidence

**Purpose:** Surface the highest-ranked evidence items and explain why they
lead. Transparent evidence hierarchy, not a ranked "score."

**Evidence needed:**
- `evidence_ranking.primary_evidence`
- `evidence_ranking.supporting_evidence`
- `evidence_ranking.confidence_notes`
- `birth_context.birth_time_confidence`

**Current capability status:** `AVAILABLE_NOW`. Evidence ranking is computed
and tested.

**Excluded claims:** No single-number confidence score visible to reader. No
claim that primary evidence guarantees anything.

**Prose deferred?** YES — synthesis section of report, requires selector.

---

### Section 1.4 — Relocated Angles

**Purpose:** Explain how ASC, MC, DSC, and IC change the field of
expression at this location.

**Evidence needed:**
- `relocated_chart.angles` (all 5 canonical angles)
- `relocated_chart.house_cusps`
- `relocated_angle_contacts[*]`
- `birth_context.birth_time_confidence`

**Current capability status:** `AVAILABLE_NOW`.

**Excluded claims:** No Vertex treated as primary chart axis. No claim that
angular emphasis guarantees outcomes. No astrocartography line distances.

**Prose deferred?** YES — angle contact blocks are TODO in
`relocated_angle_contact_blocks.json` (Round 4 scaffold).

---

### Section 1.5 — House Shifts

**Purpose:** Show which planets move into more visible, private, relational,
or operational terrain. Describe the change-of-rooms, not personality change.

**Evidence needed:**
- `planet_house_changes[*].natal_house`
- `planet_house_changes[*].relocated_house`
- `planet_house_changes[*].movement_type`
- `natal_modifiers[body]` for emphasized bodies

**Current capability status:** `AVAILABLE_NOW` for structural facts.
Domain-bucket interpretation (public/private/relational/operational) is
`NOT_COMPUTABLE` until content lane authors an explicit house→domain table.

**Excluded claims:** No invented domain labels until taxonomy is authored
and approved. No "improvement/loss" framing.

**Prose deferred?** YES — `house_shift_blocks.json` is not yet scaffolded
(pending selector taxonomy per `BLOCK_SCHEMA.md`).

---

### Section 1.6 — Planets Brought Forward

**Purpose:** Name emphasized planets, explain what natal material they carry,
and explain what this place makes louder.

**Evidence needed:**
- `evidence_ranking.primary_evidence` (angle_contact and newly_angular items)
- `natal_modifiers[body]` for all emphasized bodies
- `relocated_angle_contacts[*]`
- `planet_house_changes[*]` where `movement_type == "newly_angular"`

**Current capability status:** `AVAILABLE_NOW`. Natal modifiers are computed
for emphasized bodies only (core planets, Sun through Pluto). Nodes, Lilith,
and asteroids that are relocation-emphasized will lack natal modifier entries
— warnings emitted.

**Excluded claims:** No natal condition treated as relocated condition. No
condition guarantee (strong condition does not guarantee benefit).

**Prose deferred?** YES — natal modifier prose pending (post-selector-taxonomy
tier per `PROSE_PURPOSE_REVIEW.md`).

---

### Section 1.7 — What This Place Rewards

**Purpose:** Describe the participation style supported by the evidence.
What does showing up here make easier, more available, or more natural?

**Evidence needed:**
- `evidence_ranking.primary_evidence`
- `relocated_angle_contacts[*]`
- `planet_house_changes[*]`
- `natal_modifiers[body]`
- `purpose_lens`

**Current capability status:** Evidence fields `AVAILABLE_NOW`. Reward-pattern
synthesis key is `AVAILABLE_WITH_WIRING` — requires synthesis selector logic.

**Excluded claims:** No "this place will bring X." No outcome guarantees.
Use reward language from `PROSE_GUIDE.md` verb list.

**Prose deferred?** YES.

---

### Section 1.8 — What May Require Adjustment

**Purpose:** Surface pressure, friction, overuse, or mismatch grounded in
evidence. Not fear language — constructive-use framing.

**Evidence needed:**
- `evidence_ranking.primary_evidence`
- `natal_modifiers[body].condition_classification`
- `natal_modifiers[body].sect_condition`
- `birth_context.birth_time_confidence`

**Current capability status:** `AVAILABLE_NOW` for evidence fields.
Adjustment synthesis selector is `AVAILABLE_WITH_WIRING`.

**Excluded claims:** No "bad for you" language. No fate language. No danger
or illness claims.

**Prose deferred?** YES.

---

### Section 1.9 — Duration Lens

**Purpose:** Adjust the stakes of the evidence based on the user's
relationship to this place (short visit, extended stay, residence, past
place, remote connection).

**Evidence needed:**
- `relationship_to_place`
- `evidence_ranking.primary_evidence`

**Current capability status:** `relationship_to_place` field `AVAILABLE_NOW`
(passed through unchanged). Duration block key paths defined in `BLOCK_SCHEMA.md`
Family 7. Block scaffold (`duration_lens_blocks.json`) not yet written —
pending selector taxonomy tier.

**Excluded claims:** No relocation advice. No "you should move here." Same
evidence must not read identically for a tourist, a resident, and someone
considering a move.

**Prose deferred?** YES — duration lens blocks are post-taxonomy-tier.

---

### Section 1.10 — Purpose Lens

**Purpose:** Interpret how the evidence reads for the user's stated purpose
(career, belonging, rest, partnership, etc.).

**Evidence needed:**
- `purpose_lens`
- `evidence_ranking.primary_evidence`
- `evidence_ranking.supporting_evidence`

**Current capability status:** `purpose_lens` field `AVAILABLE_NOW`. Fit-type
taxonomy (strong_fit, conditional_fit, tradeoff, low_signal, conflicted) is
`AVAILABLE_WITH_WIRING` — requires selector judgment. Block scaffold
(`purpose_lens_blocks.json`) not yet written.

**Excluded claims:** No "career place" or "love place" labels without evidence
strength and tradeoff language. No universal best-use claims.

**Prose deferred?** YES.

---

### Section 1.11 — Evidence Summary

**Purpose:** Ranked evidence table in plain language. Transparency layer.

**Evidence needed:**
- `evidence_ranking` (all sub-fields)
- `unsupported_methods`
- `warning_summary`

**Current capability status:** `AVAILABLE_NOW`. Rendering format (table vs.
list) is a selector/template decision, not an engine decision.

**Excluded claims:** No evidence presented as proof. Speculative/excluded
methods must appear in this table as excluded.

**Prose deferred?** PARTIAL — table structure can be wired now; interpretive
prose for each evidence row is deferred.

---

### Section 1.12 — Technical Appendix

**Purpose:** Calculation transparency. What was computed, what was not
computed, confidence notes, coordinate precision, methodology.

**Evidence needed:**
- `appendix_trace` (all fields)
- `unsupported_methods`
- `warning_summary`
- `birth_context.birth_time_confidence`
- `destination_context.coordinate_precision`

**Current capability status:** `AVAILABLE_NOW`. Block scaffold exists in
`technical_appendix_blocks.json` (Round 4, 19 leaves).

**Excluded claims:** No marketing promises for unsupported methods. No
precision claims beyond actual coordinate provenance.

**Prose deferred?** PARTIAL — some technical appendix blocks have near-final
_note language. Final body prose is still TODO.

---
---

## Product 2: Between Places

**Status: NOT YET BUILT. Backend evidence record exists for single
destination. Multi-destination batch generation and comparison logic
are not implemented.**

### Section 2.1 — Comparison Summary

**Purpose:** State the central contrast between the selected places in
plain language, without ranking them universally.

**Evidence needed:**
- One `LocationEvidenceRecord` per destination (2–5 records)
- `evidence_ranking.primary_evidence` per record
- `birth_context.birth_time_confidence` (shared)

**Current capability status:** `AVAILABLE_WITH_WIRING` — single-record
generation works; batch generation loop and comparison function do not exist.

**Excluded claims:** No universal best/worst ranking. No "place A is better
than place B." Contrast must be purpose-specific or domain-specific.

**Prose deferred?** YES — no block scaffold exists for this product.

---

### Section 2.2 — Place Profiles

**Purpose:** Compact Place Resonance signature for each destination.
Mini-versions of the Place Signature section, not full Place Resonance
reports.

**Evidence needed:**
- `evidence_ranking.primary_evidence` per destination
- `relocated_angle_contacts[*]` per destination (primary items only)

**Current capability status:** `AVAILABLE_WITH_WIRING`.

**Excluded claims:** No ranking. Each profile must stand alone.

**Prose deferred?** YES.

---

### Section 2.3 — Best Fit By Purpose

**Purpose:** For the user's stated purpose, which place has the strongest
evidence fit — and what are the tradeoffs?

**Evidence needed:**
- `purpose_lens` (shared across destinations)
- `evidence_ranking` per destination
- Comparison/purpose-fit function (not yet built)

**Current capability status:** `NOT_COMPUTABLE` — requires cross-record
purpose-fit comparison function.

**Excluded claims:** No "best for love/career/money" labels. Purpose fit
must name evidence and tradeoffs.

**Prose deferred?** YES.

---

### Section 2.4 — Strongest Difference

**Purpose:** The evidence that most separates the places. What does place A
foreground that place B does not, and vice versa?

**Evidence needed:**
- Evidence diff/contrast function across `LocationEvidenceRecord` objects
  (not yet built)

**Current capability status:** `NOT_COMPUTABLE` — requires new comparison
function.

**Excluded claims:** No claim that difference implies superiority.

**Prose deferred?** YES.

---

### Section 2.5 — Shared Themes

**Purpose:** Where multiple places activate similar chart material. Useful for
understanding what the chart produces regardless of geography.

**Evidence needed:**
- Evidence intersection function across records (not yet built)

**Current capability status:** `NOT_COMPUTABLE`.

**Prose deferred?** YES.

---

### Section 2.6 — Tradeoff Map

**Purpose:** What each place supports and what it may ask in return. Not
good/bad — support and pressure language side-by-side.

**Evidence needed:**
- `evidence_ranking` per destination
- Synthesis/tradeoff function (not yet built)

**Current capability status:** `NOT_COMPUTABLE`.

**Prose deferred?** YES.

---

### Section 2.7 — Decision Notes

**Purpose:** How to use the symbolic comparison alongside practical reality.
Explicitly acknowledge that astrology does not make practical decisions.

**Evidence needed:**
- `purpose_lens`, `relationship_to_place` (per destination)

**Current capability status:** `AVAILABLE_WITH_WIRING` — template content
can be written without new computation.

**Excluded claims:** No advice to move, stay, or choose a specific place.

**Prose deferred?** YES.

---

### Section 2.8 — Technical Appendix

**Purpose:** Per-destination evidence traces, coordinate precision, and
shared methodology note.

**Evidence needed:**
- `appendix_trace` per destination

**Current capability status:** `AVAILABLE_WITH_WIRING`.

**Prose deferred?** YES.

---
---

## Product 3: World Lines Companion

**Status: NOT YET BUILT. Astrocartography line generation, distance-to-line
geometry, and nearest-point calculation are NOT IMPLEMENTED. This section map
is planning-only.**

### Section 3.1 — Map Summary

**Purpose:** Name the main line story for this place or region.

**Evidence needed:**
- Astrocartography planetary line set (ASC/DSC/MC/IC lines per planet)
- Distance from destination to nearest point on each line
- Distance band classification

**Current capability status:** `FUTURE_METHOD` — requires astrocartography
engine (planetary line geometry, distance-to-line calculation, antimeridian
and polar handling).

**Excluded claims:** No distance claims without validated geometry and a
defined distance policy. No remote activation claims.

**Prose deferred?** YES — entire product deferred until geometry engine exists.

---

### Section 3.2 — Closest Lines

**Purpose:** Distance-ranked evidence. Which lines are nearest, and how near?

**Evidence needed:**
- Planetary line catalog for this birth data
- Distance-to-destination per line
- Distance band (defined policy needed)

**Current capability status:** `FUTURE_METHOD`.

**Prose deferred?** YES.

---

### Section 3.3 — Angle Meaning

**Purpose:** How MC, IC, ASC, or DSC changes the planet's expression when
on a line (compared to relocated chart placement).

**Evidence needed:**
- Line-angle type per planet
- `natal_modifiers[body]` (reusable from Place Resonance)

**Current capability status:** `AVAILABLE_WITH_WIRING` for natal modifier
reuse once line geometry exists. Line geometry itself is `FUTURE_METHOD`.

**Prose deferred?** YES.

---

### Section 3.4 — Natal Context

**Purpose:** What the line planet carries from the birth chart.

**Evidence needed:**
- `natal_modifiers[body]` (reusable from Place Resonance)

**Current capability status:** `AVAILABLE_WITH_WIRING`.

**Prose deferred?** YES.

---

### Section 3.5 — Distance And Uncertainty

**Purpose:** Explain strength bands and birth-time sensitivity for line
movement.

**Evidence needed:**
- Distance-to-line value
- Distance band policy (DRAFT — not yet authored)
- `birth_context.birth_time_confidence`

**Current capability status:** Birth time confidence `AVAILABLE_NOW`.
Distance band policy is `NOT_COMPUTABLE` — needs content lane to define
acceptable distance thresholds before geometry can apply them.

**Excluded claims:** No wide-orb line claims without a defensible distance
policy.

**Prose deferred?** YES.

---

### Section 3.6 — Line Clusters

**Purpose:** Coherent or conflicting signals from multiple nearby lines.

**Evidence needed:**
- Planetary line catalog (multiple lines)
- Cluster detection function (not built)

**Current capability status:** `FUTURE_METHOD`.

**Prose deferred?** YES.

---

### Section 3.7 — Technical Appendix

**Purpose:** Geometry, coordinates, tolerances, exclusions.

**Evidence needed:**
- Astrocartography calculation metadata (not yet built)

**Current capability status:** `FUTURE_METHOD` for geometry-specific fields.
Standard appendix fields (`AVAILABLE_NOW`) can appear.

**Prose deferred?** YES.

---
---

## Product 4: Local Compass

**Status: NOT YET BUILT. Local Space altitude/azimuth engine, direction ray
generation, and cross-track distance calculation are NOT IMPLEMENTED.**

### Section 4.1 — Directional Signature

**Purpose:** Name the main directional pattern from the anchor location.

**Evidence needed:**
- Planetary azimuths from anchor (not built)
- Direction strength policy (not defined)

**Current capability status:** `FUTURE_METHOD`.

**Excluded claims:** No outcome guarantees for directions. No claims without
altitude/azimuth convention and distance policy.

**Prose deferred?** YES — entire product deferred until directional engine exists.

---

### Section 4.2 — Planetary Directions

**Purpose:** The strongest directions and what they emphasize.

**Evidence needed:**
- Planetary azimuths (not built)
- `natal_modifiers[body]` (reusable from Place Resonance)

**Current capability status:** `FUTURE_METHOD` for directions. `AVAILABLE_WITH_WIRING`
for natal modifier reuse.

**Prose deferred?** YES.

---

### Section 4.3 — Destination Relationship

**Purpose:** How a chosen destination or route relates to the directional paths.

**Evidence needed:**
- Cross-track distance to direction lines (not built)
- Destination coordinates

**Current capability status:** `FUTURE_METHOD`.

**Prose deferred?** YES.

---

### Section 4.4 — Use Modes

**Purpose:** Movement, workspace, ritual, exploration, rest. How to use the
directional signature practically.

**Evidence needed:**
- Directional signature (not built)
- Optional use case from user input

**Current capability status:** `FUTURE_METHOD` for directions. Template text
is `AVAILABLE_WITH_WIRING` once directions exist.

**Prose deferred?** YES.

---

### Section 4.5 — Technical Appendix

**Purpose:** Anchor coordinates, azimuth convention, distance policy, exclusions.

**Evidence needed:**
- Directional engine metadata (not built)

**Current capability status:** `FUTURE_METHOD` for directional fields.

**Prose deferred?** YES.

---
---

## Product 5: Living Map

**Status: NOT YET BUILT. Requires stable Place Resonance static baseline
AND date-bounded transit-to-relocated-angle computation, which is not
implemented. This product must not be started before Place Resonance is
stable.**

### Section 5.1 — Static Place Baseline

**Purpose:** What the place means before timing. Reuse of Place Resonance
section output.

**Evidence needed:**
- Full `LocationEvidenceRecord` (stable Place Resonance output)

**Current capability status:** `AVAILABLE_NOW` for static record.
Assembly into Living Map context is `AVAILABLE_WITH_WIRING`.

**Excluded claims:** Static baseline must not be confused with date-specific
claims.

**Prose deferred?** YES.

---

### Section 5.2 — Current Place Weather

**Purpose:** Date-bounded shifts from transits to relocated angles.

**Evidence needed:**
- Date range from user
- Transits to relocated angles for date range (not built)
- Existing standard timing clocks (if promoted into report-safe use)

**Current capability status:** `NOT_COMPUTABLE` — requires date-bounded
relocated timing function.

**Excluded claims:** No relocated return charts until return chart engine
exists. No timing claim that bypasses existing report governance.

**Prose deferred?** YES.

---

### Section 5.3 — Windows Of Emphasis

**Purpose:** Active periods and what they temporarily amplify.

**Evidence needed:**
- Date-bounded transit windows to relocated angles (not built)

**Current capability status:** `NOT_COMPUTABLE`.

**Prose deferred?** YES.

---

### Section 5.4 — What Is Baseline vs Temporary

**Purpose:** Explicit distinction between the static Place Resonance
signature and the current date-bounded weather.

**Evidence needed:**
- Both static `LocationEvidenceRecord` and dynamic timing fields (dynamic
  not yet built)

**Current capability status:** Static `AVAILABLE_NOW`. Dynamic
`NOT_COMPUTABLE`. Baseline/weather field model is `NOT_COMPUTABLE` —
this section requires the dynamic layer to exist before it can function.

**Excluded claims:** No temporary transit treated as permanent place fate.

**Prose deferred?** YES.

---

### Section 5.5 — Purpose Timing

**Purpose:** How the date range interacts with the user's stated purpose.

**Evidence needed:**
- `purpose_lens`
- Date-bounded transit windows (not built)

**Current capability status:** `NOT_COMPUTABLE`.

**Prose deferred?** YES.

---

### Section 5.6 — Technical Appendix

**Purpose:** Methods, dates, exclusions, confidence notes.

**Evidence needed:**
- Dynamic timing metadata (not built)
- Standard appendix fields

**Current capability status:** Standard appendix `AVAILABLE_NOW`. Dynamic
timing metadata `NOT_COMPUTABLE`.

**Prose deferred?** YES.
