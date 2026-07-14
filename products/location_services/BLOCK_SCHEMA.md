# Place Resonance Block Schema

**Status:** v0.1 content schema aligned to `LocationEvidenceRecord`.  
**Scope:** JSON block families and selector-safe key paths for Place Resonance.  
**Important:** This schema is grounded in `engine/location_services.py::build_location_evidence_record()` as documented by `LOCATION_EVIDENCE_RECORD_CONTRACT.md` and `BLOCK_SCHEMA_RECONCILIATION.md`.

## Schema Principles

- Block keys must match deterministic evidence fields.
- Each block family should have `fallback` leaves.
- In-depth leaves should be written in EO's bounded, evidence-routed voice.
- Literal `TODO` is allowed only in new scaffold-only files with tests that expect placeholder status.
- If prose is not final, use `_note` beside the placeholder to preserve intent.
- Do not require a content key for evidence the backend cannot produce.
- Treat relocation as foregrounding, not rewriting: natal planetary longitudes and natal condition remain natal facts.
- Prefer selector-side taxonomy for interpretive buckets when the engine only emits structural facts.

## Confirmed Record Shape

`LocationEvidenceRecord` v0.1 emits these top-level field families:

```text
birth_context
destination_context
relocated_chart
planet_house_changes
relocated_angle_contacts
natal_modifiers
evidence_ranking
purpose_lens
relationship_to_place
appendix_trace
unsupported_methods
warnings
```

Selector authors should remember that `planet_house_changes` and `relocated_angle_contacts` are flat lists of self-describing records with stable IDs, not nested dictionaries. The key paths below describe how a selector should index those lists for block lookup.

## Canonical Names

Angles use long canonical names only:

```text
Ascendant
Midheaven
Descendant
Imum_Coeli
Vertex
```

Short authoring aliases such as `ASC`, `MC`, `DSC`, and `IC` may be accepted by the block selector if it normalizes them through the existing standard angle alias map, but block files should use the long names.

Bodies use existing EO body names, including:

```text
Sun
Moon
Mercury
Venus
Mars
Jupiter
Saturn
Uranus
Neptune
Pluto
North_Node
South_Node
Lilith_BML
```

Custom asteroid names can also appear when present in the natal payload.

## Proposed Folder

```text
products/location_services/blocks/plainspeak/
```

Possible later pack:

```text
products/location_services/blocks/entangled_oracle/
```

## Shared Leaf Shape

Preferred in scaffoldable block files:

```json
{
  "body": "TODO",
  "_note": "Explain the evidence in reader-facing language without guaranteeing outcomes.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["relocated_angle_contact"]
}
```

For mature block files, direct string leaves are acceptable if they match existing EO block conventions:

```json
{
  "fallback": "This place brings a specific chart function forward, but the available evidence is broader than one narrow pathway."
}
```

## Block Family 1: Relocated Angle Contacts

File:

```text
relocated_angle_contact_blocks.json
```

Purpose:

- Interpret a planet, point, or asteroid conjunct a relocated angle.
- Treat angle contacts as standalone relocated-chart facts, not necessarily as differences from natal angularity.
- A same-place or otherwise "quiet" relocation may still have angle contacts.

Selector key path:

```text
relocated_angle_contacts[*].angle -> relocated_angle_contacts[*].body -> relocated_angle_contacts[*].contact_strength
```

Contact strength bands:

```text
tight      0.00-2.00 degrees
moderate   2.01-5.00 degrees
wide       5.01-8.00 degrees
fallback
```

Use `wide` as the softest angle-contact tier. It is still computed evidence, but prose should read as edge-of-contact rather than central emphasis.

Example:

```json
{
  "_note": "Key path: relocated angle -> body -> contact strength. Angles use long canonical names.",
  "fallback": {
    "body": "TODO",
    "_note": "Broad relocated-angle contact when the angle/body pair is unsupported."
  },
  "Midheaven": {
    "Venus": {
      "tight": {
        "body": "TODO",
        "_note": "Public visibility, social value, aesthetics, collaboration. No promise of fame, love, or money."
      },
      "moderate": {
        "body": "TODO",
        "_note": "Same Venus/Midheaven theme, lower strength and less central."
      },
      "wide": {
        "body": "TODO",
        "_note": "Venus is near the public angle but not strongly exact. Use softer language and avoid making this the whole place signature unless other evidence repeats it."
      }
    }
  }
}
```

Required evidence fields:

```text
relocated_angle_contacts[*].id
relocated_angle_contacts[*].angle
relocated_angle_contacts[*].body
relocated_angle_contacts[*].orb
relocated_angle_contacts[*].contact_strength
relocated_angle_contacts[*].relocated_house_type
birth_context.birth_time_confidence
natal_modifiers[body]
```

## Block Family 2: Planet Relocated House

File:

```text
planet_relocated_house_blocks.json
```

Purpose:

- Interpret a planet's relocated house placement, especially when it changes from natal house to relocated house.
- Keep structural movement separate from editorial domain buckets.

Selector key path:

```text
planet_house_changes[*].body -> planet_house_changes[*].relocated_house -> planet_house_changes[*].movement_type
```

Real movement types:

```text
same_house
newly_angular
leaves_angular
house_changed
unknown
fallback
```

Deferred domain buckets:

```text
moves_public
moves_private
moves_relational
moves_operational
```

The deferred buckets are content taxonomy, not engine output. If we want them, the selector should derive them from `natal_house` and `relocated_house`, or the content lane should author an explicit house-to-domain table before asking the engine to emit `domain_movement_type`.

Example:

```json
{
  "_note": "Key path: body -> relocated house number -> structural movement type.",
  "Moon": {
    "4": {
      "house_changed": {
        "body": "TODO",
        "_note": "Moon moves into home/root/private life emphasis. Avoid claiming the place is automatically home."
      },
      "same_house": {
        "body": "TODO",
        "_note": "The Moon remains in the same house domain here; describe continuity rather than relocation-driven change."
      }
    }
  }
}
```

Required evidence fields:

```text
planet_house_changes[*].id
planet_house_changes[*].body
planet_house_changes[*].natal_house
planet_house_changes[*].relocated_house
planet_house_changes[*].house_changed
planet_house_changes[*].natal_house_type
planet_house_changes[*].relocated_house_type
planet_house_changes[*].movement_type
natal_modifiers[body]
birth_context.birth_time_confidence
```

## Block Family 3: House Shift

File:

```text
house_shift_blocks.json
```

Purpose:

- Interpret the life-domain shift from natal house to relocated house independent of planet.
- Own the editorial house-domain taxonomy at the content or selector layer.

Selector key path:

```text
planet_house_changes[*].natal_house -> planet_house_changes[*].relocated_house
```

Example:

```json
{
  "_note": "Key path: natal house -> relocated house. Use when the report needs the life-domain shift itself.",
  "12": {
    "10": {
      "body": "TODO",
      "_note": "A private or hidden natal function becomes more public. Must not imply exposure is automatically good."
    }
  }
}
```

Required evidence fields:

```text
planet_house_changes[*].natal_house
planet_house_changes[*].relocated_house
planet_house_changes[*].body
planet_house_changes[*].house_changed
planet_house_changes[*].movement_type
```

Do not require `domain_from` or `domain_to` in v0.1. Those are selector/content derivations until an explicit taxonomy is authored.

## Block Family 4: Natal Modifiers

File:

```text
natal_modifier_blocks.json
```

Purpose:

- Modify relocated claims using natal condition, sect, angularity, rulership, and natal aspects.
- Preserve the boundary that condition-bearing formulas run against the natal payload only.

Selector key paths:

```text
natal_modifiers[body].condition_classification
natal_modifiers[body].sect_condition
natal_modifiers[body].was_natal_angular
natal_modifiers[body].natal_house_type
natal_modifiers[body].routing_tags
```

Example:

```json
{
  "_note": "Modifiers should qualify the relocated expression rather than replace it.",
  "sect_condition": {
    "in_sect": {
      "body": "TODO",
      "_note": "Planet may be easier to integrate when brought forward."
    },
    "out_of_sect": {
      "body": "TODO",
      "_note": "Planet may require more conscious handling when brought forward."
    }
  }
}
```

Required evidence fields:

```text
natal_modifiers[body].source_standard_formula
natal_modifiers[body].condition_classification
natal_modifiers[body].overall_condition_score
natal_modifiers[body].essential_dignity
natal_modifiers[body].accidental_dignity
natal_modifiers[body].sect_condition
natal_modifiers[body].motion_condition
natal_modifiers[body].natal_house_type
natal_modifiers[body].was_natal_angular
natal_modifiers[body].routing_tags
natal_modifiers[body].confidence
birth_context.birth_time_confidence
```

Round 3 confidence status:

- `natal_modifiers[body].confidence` is now trustworthy for exact, approximate, and unknown birth-time charts.
- Use `birth_context.birth_time_confidence` or `appendix_trace.birth_time_confidence` when the report needs one chart-level confidence statement.
- Use `natal_modifiers[body].confidence` when a modifier leaf needs the confidence state attached to that specific emphasized body.
- `natal_modifiers` covers emphasized core planets only (`Sun` through `Pluto`). Nodes, Lilith, and asteroids may appear in house changes or angle contacts without a natal modifier entry.

## Block Family 5: Purpose Lens

File:

```text
purpose_lens_blocks.json
```

Purpose:

- Interpret evidence through the user's stated purpose without converting the purpose into a guarantee.
- Keep purpose taxonomy in the content layer; the engine passes the string through unchanged and validates only that it is a string or `None`.

Selector key path:

```text
purpose_lens -> evidence_domain -> fit_type
```

Purpose lenses:

```text
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

Fit types:

```text
strong_fit
conditional_fit
tradeoff
low_signal
conflicted
fallback
```

Example:

```json
{
  "_note": "Purpose lens blocks translate evidence into use-case language without promising outcomes.",
  "career": {
    "public_visibility": {
      "strong_fit": {
        "body": "TODO",
        "_note": "Use when Midheaven/10th evidence supports public role. Avoid success guarantees."
      }
    }
  }
}
```

Required evidence fields:

```text
purpose_lens
evidence_ranking.primary_evidence
evidence_ranking.supporting_evidence
birth_context.birth_time_confidence
```

Deferred selector fields:

```text
evidence_domain
fit_type
supporting_evidence_ids
contradictory_evidence_ids
```

These are content/selector outputs, not raw engine fields in v0.1.

## Block Family 6: Location Synthesis

File:

```text
location_synthesis_blocks.json
```

Purpose:

- Assemble the overall Place Signature, strongest shift, rewards, and adjustment notes.
- Select synthesis only after evidence ranking identifies which computed facts are primary.

Selector key paths:

```text
dominant_theme -> tone
reward_pattern -> participation_style
adjustment_pattern -> pressure_type
conflict_pattern -> conflict_type
```

Dominant themes:

```text
public_visibility
private_rooting
relational_mirror
self_reinvention
creative_expression
work_and_craft
study_and_horizon
shared_depth
community_future
retreat_and_repair
material_stability
fallback
```

Example:

```json
{
  "_note": "Synthesis blocks should only be selected after evidence ranking identifies a dominant theme.",
  "public_visibility": {
    "supportive": {
      "body": "TODO",
      "_note": "Public life is emphasized in a workable way. Name participation and limits."
    },
    "pressurized": {
      "body": "TODO",
      "_note": "Public life is emphasized with pressure. Avoid fear language."
    }
  }
}
```

Required evidence fields:

```text
evidence_ranking.primary_evidence
evidence_ranking.supporting_evidence
evidence_ranking.confidence_notes
planet_house_changes
relocated_angle_contacts
natal_modifiers
birth_context.birth_time_confidence
```

Known v0.1 caveat:

- `evidence_ranking.contradictory_evidence` is always an empty list.
- Do not select contradiction/conflict blocks until the content lane authors a domain taxonomy that can identify visibility/privacy, expansion/structure, and similar tensions.

## Block Family 6B: Place Resonance Search Blocks

File:

```text
place_resonance_search_blocks.json
```

Purpose:

- Provide search-level prose for Place Resonance Search.
- Explain the selected location set, curated buckets, recommendation labels,
  and cross-location pattern synthesis.
- Keep these leaves separate from the reusable one-location Place Profile
  blocks, because Search is interpreting a candidate pool and selected set, not
  one destination in isolation.

Selector key paths:

```text
search_summary -> dominant_search_theme
bucket_intro -> bucket
recommendation_label -> recommendation_key
pattern_synthesis -> synthesis_pattern
```

Search summary keys:

```text
visibility_calling
belonging_bonds
hearth_restoration
study_signal
creative_culture
long_term_build
change_aliveness
shadow_pressure
mixed_signature
fallback
```

Bucket intro keys:

```text
highest_resonance
goal_specific_allies
transformational_demanding
quiet_grounding_alternatives
pattern_outliers
fallback
```

Recommendation label keys:

```text
strongly_consider
goal_specific_ally
powerful_but_demanding
gentle_alternative
useful_contrast
stable_baseline
low_signal_not_priority
fallback
```

Pattern synthesis keys:

```text
convergent_theme
split_need
pressure_pattern
quiet_counterweight
outlier_reveal
fallback
```

Required evidence/context fields:

```text
selected_locations
evaluated_locations
candidate_pool
scores
dominant_themes
bucket_distribution
evidence_refs
purpose_lens
relationship_to_place
```

Known v0.1 caveat:

- These leaves are authored search-level prose and should be kept distinct from
  one-location Place Profile interpretation blocks.
- They are selected by `select_place_resonance_search_leaf()`.
- Search-level blocks should never command relocation, declare a universal best
  place, or flatten a demanding location into a vague positive.

## Block Family 6A: Place Context Modifiers

File:

```text
place_context_modifier_blocks.json
```

Purpose:

- Add practical perspective after the primary Place Resonance evidence has
  already been selected.
- Keep internal caution inside evidence thresholds and selector rules, not
  in consumer-facing ambiguity.
- Support clear context statements such as social connection, isolation,
  visibility, restoration, pressure, movement, stability, and intimacy
  without turning those statements into guarantees or commands.

Selector key path:

```text
context_axis -> context_expression
```

Context axes:

```text
social_connection
visibility
restoration
isolation
pressure
movement
stability
intimacy
fallback
```

Context expressions:

```text
supportive
demanding
thin
mixed
fallback
```

Example:

```json
{
  "isolation": {
    "demanding": {
      "body": "The place may lean toward isolation or social thinning in a way the report should name directly.",
      "_note": "Select from repeated private/12th/Saturn/Pluto evidence when social support is thin."
    }
  }
}
```

Required evidence fields:

```text
evidence_ranking.primary_evidence
evidence_ranking.supporting_evidence
relocated_angle_contacts
planet_house_changes
natal_modifiers
purpose_lens
relationship_to_place
birth_context.birth_time_confidence
```

Known v0.1 caveat:

- These leaves are authored but not yet wired into Place Resonance
  assembly.
- Selectors should not choose a context modifier from a single isolated
  factor unless the leaf itself is explicitly written as low-signal or
  thin.
- A difficult context may be named directly. The forbidden move is not
  negativity; it is turning symbolic emphasis into a guaranteed life
  outcome.

## Block Family 7: Duration Lens

File:

```text
duration_lens_blocks.json
```

Purpose:

- Adjust meaning for short visit, extended stay, residence, past place, or remote relationship.
- Keep relationship taxonomy in the content layer; the engine passes the string through unchanged and validates only that it is a string or `None`.

Selector key path:

```text
relationship_to_place -> dominant_theme
```

Relationship values:

```text
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

Example:

```json
{
  "short_visit": {
    "public_visibility": {
      "body": "TODO",
      "_note": "Activation may be temporary and useful to test. Do not imply permanent relocation advice."
    }
  }
}
```

Required evidence fields:

```text
relationship_to_place
evidence_ranking.primary_evidence
evidence_ranking.supporting_evidence
birth_context.birth_time_confidence
```

Deferred selector fields:

```text
dominant_theme
duration_assumption
```

## Block Family 8: Technical Appendix

File:

```text
technical_appendix_blocks.json
```

Purpose:

- Provide clear standard language for calculation methods, limitations, unsupported techniques, and confidence notes.

Selector key paths:

```text
calculation_note -> relocated_chart
unsupported_method -> method_key
confidence_note -> confidence_state
warning_summary -> warning_key
```

`warning_summary` is a real Round 3 evidence field at both top level and `appendix_trace.warning_summary`. Use it for reader-facing appendix prose. Raw `warnings` remains available for audit/debug views.

Example:

```json
{
  "_note": "Appendix blocks may be closer to documentation than interpretation.",
  "calculation_note": {
    "relocated_chart": "Relocation was calculated from the original birth UTC instant. Destination coordinates were used to recalculate angles and Whole Sign houses; natal planetary longitudes were preserved."
  },
  "unsupported_method": {
    "astrocartography": "Astrocartography line-distance claims are not included in this version. This report uses relocated chart evidence only."
  }
}
```

Required evidence fields:

```text
appendix_trace.calculation_sources
appendix_trace.tolerances
appendix_trace.unsupported_methods
appendix_trace.warnings
appendix_trace.warning_summary
appendix_trace.birth_time_confidence
appendix_trace.coordinate_precision
appendix_trace.methodology
unsupported_methods
warnings
warning_summary
```

Round 3 warning status:

- Production-scale asteroid charts may emit many repeated warning strings for bodies with no natal condition record.
- The evidence record now provides aggregated `warning_summary` items with stable IDs, counts, and examples.
- Appendix rendering should use `warning_summary` for prose and reserve raw `warnings` for diagnostic or audit displays.

## Proposed Context Fields For Report Assembly

The future Place Resonance context should be able to feed these template fields:

```text
place_signature
dominant_place_theme
strongest_structural_shift
relocated_angles
angle_contacts
house_changes
planets_brought_forward
natal_modifiers
purpose_lens_fit
duration_lens
rewards
adjustments
evidence_summary
technical_appendix
unsupported_methods
warnings
```

## Initial Content Priority

Write first:

1. `technical_appendix_blocks.json`
2. `relocated_angle_contact_blocks.json`
3. `planet_relocated_house_blocks.json`
4. `location_synthesis_blocks.json`

Write after selector taxonomy exists:

1. `house_shift_blocks.json`
2. `purpose_lens_blocks.json`
3. `duration_lens_blocks.json`
4. `natal_modifier_blocks.json`

Reason:

- Technical appendix and angle/house evidence are closest to the first backend seam.
- Purpose, duration, contradiction, and domain-movement claims need selector-owned taxonomy before prose expansion.
- Natal modifiers are computable now, with confidence fixed in Round 3.

## Answered Validation Questions

- Canonical body names come from the existing natal payload and standard body dictionaries.
- Canonical angle names are long names only: `Ascendant`, `Midheaven`, `Descendant`, `Imum_Coeli`, `Vertex`.
- v0.1 emits both relocated house changes and relocated angle contacts.
- Contact strength bands are `tight`, `moderate`, and `wide`.
- Natal modifiers are available for emphasized core planets without rerunning the full report bundle, and are computed from the natal payload only.
- Birth-time confidence is available at chart level through `birth_context.birth_time_confidence` / `appendix_trace.birth_time_confidence`, and at emphasized-body modifier level through `natal_modifiers[body].confidence`.
- Warning aggregation is available through top-level `warning_summary` and `appendix_trace.warning_summary`; raw `warnings` remains unchanged.
- Unsupported methods are flat strings: `astrocartography`, `local_space`, `parans`, `relocated_returns`.
- Astrocartography line distances, local-space azimuths, parans, dynamic timing windows, and relocated return charts remain out of v0.1 scope.
