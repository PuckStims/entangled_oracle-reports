# Block Family Expansion Plan — Location Services

**Status:** GEMINI FIRST-PASS DRAFT. All block families proposed here are
TODO-only scaffolding proposals. None of these files exist yet (except
where noted as already built in Round 4). Nothing here should be wired as
final until Claude Code validates schema alignment and ChatGPT/Codex
validates content architecture.

**Reading rule:** If a proposed family is marked "DEPENDS ON UNRESOLVED
TAXONOMY," it must not be scaffolded in JSON until the taxonomy it depends
on is authored and approved by the content lane.

Before creating any block family that depends on resolver, theme clusterer,
goal compatibility, report planner, line geometry, direction geometry, or
timing overlay work, read
`products/location_services/BUILD_OUTLINE_DRIFT_GUARD.md`. Blocks should follow
computed evidence contracts, not create them by implication.

---

## Already Built (Round 4, Blocks Under `blocks/plainspeak/`)

These block families already exist as TODO-only scaffolds. Do not rebuild them.

| File | Leaves | Key Path |
|---|---|---|
| `technical_appendix_blocks.json` | 19 | calculation_note, unsupported_method, confidence_note, coordinate_precision_note, warning_summary |
| `relocated_angle_contact_blocks.json` | 177 | angle → body → contact_strength |
| `planet_relocated_house_blocks.json` | 539 | body → relocated_house(1-12) → movement_type |
| `location_synthesis_blocks.json` | 10 | 9 named synthesis categories + fallback |

Total: 745 leaves. All bodies are literal `"body": "TODO"` with `_note`,
`claim_level`, and `requires_evidence` fields.

---

## Proposed Block Families — Place Resonance (Product 1)

These block families are defined in `BLOCK_SCHEMA.md` but not yet scaffolded:

### BF-PR-01: `house_shift_blocks.json`

**Purpose:** Interpret the domain shift from natal house to relocated house,
independent of body. Owns the editorial house-to-domain taxonomy at content
or selector layer.

**Proposed location:**

```
products/location_services/blocks/plainspeak/house_shift_blocks.json
```

**Key path:** `natal_house → relocated_house`

**Leaf shape (TODO-only):**

```json
{
  "body": "TODO",
  "_note": "Describe the domain shift from natal house N to relocated house M. Must not imply improvement or loss. Must name the kind of life arena that changes.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["planet_house_changes[*].natal_house", "planet_house_changes[*].relocated_house"]
}
```

**Grid size estimate:** 12 × 12 = 144 leaves maximum; realistically fewer
because same-house entries will be minimal and many natal→relocated
combinations are astronomically constrained.

**DEPENDS ON UNRESOLVED TAXONOMY:** The house-to-domain mapping (public /
private / relational / operational) is not yet authored. This block family
can be scaffolded as `natal_house → relocated_house` key pairs without
domain labels, but the domain layer should not be invented.

**Scaffold priority:** DEFERRED — after selector taxonomy exists, per
`PROSE_PURPOSE_REVIEW.md` and `BLOCK_SCHEMA.md` Initial Content Priority.

---

### BF-PR-02: `purpose_lens_blocks.json`

**Purpose:** Translate evidence into the user's stated use case without
promising outcomes.

**Proposed location:**

```
products/location_services/blocks/plainspeak/purpose_lens_blocks.json
```

**Key path:** `purpose_lens → evidence_domain → fit_type`

**Purpose lens values:**

```
career
belonging
rest
partnership
creative_visibility
study
retreat
structure
experimentation
fallback
```

**Fit types:**

```
strong_fit
conditional_fit
tradeoff
low_signal
conflicted
fallback
```

**Leaf shape (TODO-only):**

```json
{
  "body": "TODO",
  "_note": "Translate evidence into use-case language for this purpose + evidence domain + fit type. Must not promise outcomes. Strong fit language should name what participation style the evidence supports, not whether the goal is guaranteed.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["purpose_lens", "evidence_ranking.primary_evidence"]
}
```

**DEPENDS ON UNRESOLVED TAXONOMY:** `evidence_domain` key path requires
selector-side judgment about what evidence items map to what domain. This
taxonomy must be authored before the three-level key path is wired.

**Scaffold priority:** DEFERRED — post-selector-taxonomy tier.

---

### BF-PR-03: `duration_lens_blocks.json`

**Purpose:** Adjust evidence stakes based on the user's relationship to
the place (visit, stay, residence, past, remote).

**Proposed location:**

```
products/location_services/blocks/plainspeak/duration_lens_blocks.json
```

**Key path:** `relationship_to_place → dominant_theme`

**Relationship values:**

```
current_home
possible_move
past_home
short_visit
extended_stay
work_base
family_place
retreat
remote_connection
fallback
```

**Leaf shape (TODO-only):**

```json
{
  "body": "TODO",
  "_note": "Adjust the stakes language for this relationship type. Short visit → activation/testing. Residence → operating environment/sustainability. Past home → retrospective, not advice. Remote → symbolic/relational, not embodied.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["relationship_to_place", "evidence_ranking.primary_evidence"]
}
```

**DEPENDS ON UNRESOLVED TAXONOMY:** `dominant_theme` key is a selector output
derived from `evidence_ranking`. Theme taxonomy must be stable (from
`location_synthesis_blocks.json`) before this second key is populated.

**Scaffold priority:** DEFERRED — post-selector-taxonomy tier.

---

### BF-PR-04: `natal_modifier_blocks.json`

**Purpose:** Qualify relocated evidence using the body's natal condition.
Add texture, ease, friction, or caution without overriding angle/house
interpretation.

**Proposed location:**

```
products/location_services/blocks/plainspeak/natal_modifier_blocks.json
```

**Key path:**

```
sect_condition → condition_classification
motion_condition → natal_house_type
```

(Two separate axes; selector should combine them as qualifiers, not as a
single deep key path.)

**Condition classification values (from existing formula layer):**

```
excellent
strong
average
challenged
severely_challenged
unknown
```

**Sect condition values:**

```
in_sect
out_of_sect
unknown
```

**Leaf shape (TODO-only):**

```json
{
  "body": "TODO",
  "_note": "This block qualifies the relocated expression; it does not replace it. In-sect + excellent: easier integration. Out-of-sect + challenged: may require more conscious handling. Unknown confidence: state uncertainty explicitly.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["natal_modifiers[body].sect_condition", "natal_modifiers[body].condition_classification", "natal_modifiers[body].confidence"]
}
```

**Note:** `natal_modifiers` covers only core planets (Sun–Pluto). Nodes,
Lilith, and asteroids that are relocation-emphasized will lack entries.
Any block that selects natal modifier keys must have a fallback for
bodies without modifier records.

**Scaffold priority:** DEFERRED — post-selector-taxonomy tier (same reason
as purpose and duration lenses).

---

## Proposed Block Families — Between Places (Product 2)

**All of these are proposals only. Product 2 has a draft shell, but no
production comparison backend yet.**

### BF-BP-01: `place_comparison_summary_blocks.json`

**Purpose:** Contrast-statement opener for a Between Places report.
Names the central difference without ranking.

**Proposed location:**

```
products/location_services/blocks/plainspeak/between_places/place_comparison_summary_blocks.json
```

**Key path:** `comparison_pattern → destination_count`

**Proposed comparison patterns (DRAFT — not taxonomy truth):**

```
DRAFT: divergent_emphasis      (places foreground clearly different material)
DRAFT: convergent_emphasis     (places foreground similar material through different paths)
DRAFT: purpose_differentiating (one place clearly fits the stated purpose; others less so)
DRAFT: mixed_signal            (evidence is close or conflicted; contrast is not clean)
DRAFT: low_signal_all          (all places show quiet relocation charts)
DRAFT: fallback
```

**Leaf shape (TODO-only):**

```json
{
  "body": "TODO",
  "_note": "Open the comparison without ranking. State what is different and why it matters for the user's question. Do not call any place best or worst.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["evidence_ranking.primary_evidence (per destination)", "purpose_lens"]
}
```

**DEPENDS ON UNRESOLVED TAXONOMY:** Comparison pattern detection requires
a cross-record comparison function that does not yet exist. The DRAFT
pattern names above should not be wired as taxonomy until Claude Code
reviews what comparison function output shape would actually look like.

---

### BF-BP-02: `place_profile_compact_blocks.json`

**Purpose:** Mini Place Signature per destination, for use inside a
comparison report. Not a full Place Resonance report.

**Proposed location:**

```
products/location_services/blocks/plainspeak/between_places/place_profile_compact_blocks.json
```

**Key path:** Reuse `location_synthesis_blocks.json` synthesis category keys
as the compact profile selector.

**Note:** This block family may not need to be a separate file if the
synthesis categories from the existing `location_synthesis_blocks.json`
scaffold can be selected per-destination. Claude Code should determine
whether a new compact file is needed or whether the existing synthesis
scaffold is sufficient.

---

### BF-BP-03: `tradeoff_map_blocks.json`

**Purpose:** For each destination, what does the location support and what
may it ask in return?

**Proposed location:**

```
products/location_services/blocks/plainspeak/between_places/tradeoff_map_blocks.json
```

**Key path:** `dominant_theme → tradeoff_type`

**Proposed tradeoff types (DRAFT — not taxonomy truth):**

```
DRAFT: visibility_with_exposure_cost
DRAFT: belonging_with_public_friction
DRAFT: depth_with_isolation_risk
DRAFT: expansion_with_grounding_cost
DRAFT: rest_with_opportunity_gap
DRAFT: structure_with_rigidity_risk
DRAFT: freedom_with_instability_risk
DRAFT: fallback
```

**DEPENDS ON UNRESOLVED TAXONOMY:** Tradeoff type detection depends on
domain taxonomy and contradiction taxonomy, neither of which is authored.
These DRAFT names must not be wired as final.

---

## Proposed Block Families — World Lines Companion (Product 3)

**All proposals. No backend exists. FUTURE_METHOD dependency.**

### BF-WL-01: `map_line_contact_blocks.json`

**Purpose:** Interpret planet on an astrocartography line, with distance
band context. Structural analog to `relocated_angle_contact_blocks.json`.

**Proposed location:**

```
products/location_services/blocks/plainspeak/world_lines/map_line_contact_blocks.json
```

**Key path:** `line_angle → body → distance_band`

**Proposed distance bands (DRAFT — content lane must define final thresholds):**

```
DRAFT: on_line       (very close — distance TBD by content lane)
DRAFT: near          (moderate distance — thresholds TBD)
DRAFT: approaching   (further — thresholds TBD)
DRAFT: fallback
```

**DEPENDS ON FUTURE METHOD:** Entire block family is inert until
astrocartography line generation and distance calculation exist.

**DEPENDS ON UNRESOLVED TAXONOMY:** Distance band thresholds must be
authored by content lane before this selector key has meaning.

---

### BF-WL-02: `line_cluster_blocks.json`

**Purpose:** Interpret clusters of nearby lines — coherent or conflicting.

**Proposed location:**

```
products/location_services/blocks/plainspeak/world_lines/line_cluster_blocks.json
```

**Key path:** `cluster_type → dominant_angle`

**Proposed cluster types (DRAFT):**

```
DRAFT: single_dominant
DRAFT: convergent_cluster    (multiple lines, similar angle type)
DRAFT: mixed_cluster         (multiple lines, different angle types)
DRAFT: no_cluster            (lines well-separated)
DRAFT: fallback
```

**DEPENDS ON FUTURE METHOD and UNRESOLVED TAXONOMY.**

---

## Proposed Block Families — Local Compass (Product 4)

**All proposals. No backend exists. FUTURE_METHOD dependency.**

### BF-LC-01: `directional_signature_blocks.json`

**Purpose:** Name the main directional pattern from the anchor location.

**Proposed location:**

```
products/location_services/blocks/plainspeak/local_compass/directional_signature_blocks.json
```

**Key path:** `dominant_direction → body`

**DEPENDS ON FUTURE METHOD:** Requires azimuth engine.

---

### BF-LC-02: `direction_use_mode_blocks.json`

**Purpose:** How to use directional signatures for movement, workspace,
ritual, exploration, rest.

**Proposed location:**

```
products/location_services/blocks/plainspeak/local_compass/direction_use_mode_blocks.json
```

**Key path:** `use_mode → body → direction_band`

**Proposed use modes (DRAFT):**

```
DRAFT: movement_and_travel
DRAFT: workspace_and_daily_base
DRAFT: ritual_and_orientation
DRAFT: exploration_and_discovery
DRAFT: rest_and_recovery
DRAFT: fallback
```

**DEPENDS ON FUTURE METHOD and UNRESOLVED TAXONOMY.**

---

## Proposed Block Families — Living Map (Product 5)

**All proposals. No backend exists. NOT_COMPUTABLE / FUTURE_METHOD dependency.**

### BF-LM-01: `place_weather_blocks.json`

**Purpose:** Interpret date-bounded transit emphasis over relocated angles
and houses.

**Proposed location:**

```
products/location_services/blocks/plainspeak/living_map/place_weather_blocks.json
```

**Key path:** `transit_planet → relocated_angle → time_band`

**Proposed time bands (DRAFT):**

```
DRAFT: current_window     (within date range)
DRAFT: approaching        (within N days/weeks)
DRAFT: just_passed        (recently ended)
DRAFT: fallback
```

**DEPENDS ON NOT_COMPUTABLE:** Requires date-bounded transit-to-relocated-
angle computation, which does not exist.

**DEPENDS ON FUTURE METHOD** if dynamic astrocartography is included.

---

### BF-LM-02: `baseline_vs_weather_blocks.json`

**Purpose:** Explicitly distinguish the static Place Resonance baseline
from the current date-specific activation.

**Proposed location:**

```
products/location_services/blocks/plainspeak/living_map/baseline_vs_weather_blocks.json
```

**Key path:** `signal_layer → activation_type`

**DEPENDS ON NOT_COMPUTABLE:** The baseline-vs-weather field model does not
exist until dynamic timing is built.

---

## Block Packs — Future Consideration

The following are longer-horizon ideas that should not be scaffolded until
products 3–5 have backend foundations:

| Proposed Pack | Depends On |
|---|---|
| `blocks/entangled_oracle/` voice variant | Final prose ownership decision; `blocks/plainspeak/` must stabilize first |
| Comparison packs for 3-way and 5-way destinations | Between Places comparison function + more than 2 destinations tested |
| Seasonal/annual living map packs | Dynamic timing layer stable and in report-safe governance |
| Natal rulership chain blocks | Safe relocated Ascendant ruler helper built and approved |

---

## Summary: Taxonomy Dependencies

All proposed block families that depend on unresolved taxonomy are listed
here for Claude Code and ChatGPT/Codex review:

| Block Family | Taxonomy Needed | Status |
|---|---|---|
| `house_shift_blocks.json` | House → domain mapping (public/private/relational/operational) | NOT AUTHORED |
| `purpose_lens_blocks.json` | Evidence domain classification at selector layer | NOT AUTHORED |
| `duration_lens_blocks.json` | Dominant theme from synthesis (selector output) | DEPENDS ON SYNTHESIS SELECTOR |
| `natal_modifier_blocks.json` | Body coverage (nodes/Lilith/asteroids excluded) must be explicit | UNDERSTOOD |
| `place_comparison_summary_blocks.json` | Comparison pattern detection function | NOT_COMPUTABLE |
| `tradeoff_map_blocks.json` | Tradeoff type taxonomy | NOT AUTHORED |
| `map_line_contact_blocks.json` | Distance band policy | NOT AUTHORED, FUTURE_METHOD dependency |
| `line_cluster_blocks.json` | Cluster type taxonomy + distance policy | NOT AUTHORED, FUTURE_METHOD dependency |
| `directional_signature_blocks.json` | Azimuth engine + direction policy | FUTURE_METHOD |
| `direction_use_mode_blocks.json` | Use mode taxonomy + direction policy | NOT AUTHORED, FUTURE_METHOD |
| `place_weather_blocks.json` | Transit-to-relocated-angle computation + time band policy | NOT_COMPUTABLE |
| `baseline_vs_weather_blocks.json` | Dynamic timing field model | NOT_COMPUTABLE |
