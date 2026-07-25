# Synastry Block Schema

Status: v0.1 round 1 authored prose. Terminal leaves now contain live draft copy
for testing rather than scaffold placeholders.

Engine contract: `docs/SYNASTRY_ENGINE_CONTRACT.md`

Implemented evidence source: `engine/synastry.py`

## Round 1 Rule

Every terminal leaf in this product family now uses the same structural shape:

```json
{
  "body": "Reader-facing prose for a specific emitted route.",
  "_note": "Authoring and selector guidance for future revisions.",
  "claim_level": "bounded_interpretation",
  "requires_evidence": ["computations.mutual_aspects"]
}
```

Round 1 prose is intentionally broad enough to exercise selector and rendering
logic while still respecting current method limits.

## Product Boundary

Synastry is still not exposed as a client report. These blocks now support
round-1 testing of prose selection, confidence handling, and evidence
localization, but they do not authorize relationship verdicts.

Avoid labels such as:

- compatible
- incompatible
- doomed
- soulmate
- twin flame
- destined
- karmic debt

## Block Directory

```text
products/synastry/blocks/plainspeak/
```

## Authoring Standard

Round 1 prose should:

- stay trace-linked to emitted evidence
- preserve direction when the engine localizes one chart through the other
- keep composite language distinct from synastry-contact language
- treat approximate birth times as softer localization, not fake exactness
- withhold house or angle claims when the confidence layer says they are not live
- avoid verdict framing, diagnosis, destiny claims, and decorative vagueness

The writing pass is informed by the current PlainSpeak and Anti-Monotony guides
and should remain aligned with future selector refinement.

## Block Families

### 1. Technical Appendix

File:

```text
technical_appendix_blocks.json
```

Purpose:

- Explain method boundaries and sidecar status.
- Render confidence and withholding notes.
- Name non-live layers without implying they are secretly available.

Selector key paths:

```text
calculation_note -> pair_payload
confidence_note -> confidence_state
withheld_reason -> reason_key
unsupported_layer -> layer_key
claim_safety -> flag_key
```

Required evidence:

```text
schema_version
sidecar.computation_status
sidecar.withheld_summary
sidecar.claim_safety
confidence.withheld_records
```

Claim level:

```text
technical_disclosure
```

### 2. Directional Aspect Blocks

File:

```text
directional_aspect_blocks.json
```

Purpose:

- Interpret live directional and mutual cross-chart contacts.
- Preserve direction as routing and localization, not blame or one-way causality.

Selector key paths:

```text
aspect -> dependency -> polarity
body_pair_family -> aspect
```

Primary evidence:

```text
computations.directional_aspects
computations.mutual_aspects
```

Claim level:

```text
bounded_interpretation
```

### 3. House Overlay Blocks

File:

```text
house_overlay_blocks.json
```

Purpose:

- Interpret a body from one chart falling in the other person's Whole Sign
  house.
- Keep the house owner's confidence state visible.

Selector key paths:

```text
source_body -> target_house -> confidence_band
house_domain -> source_body
```

Required evidence:

```text
computations.house_overlays
person_a.birth_time_state
person_b.birth_time_state
confidence.withheld_records
```

Claim level:

```text
bounded_interpretation
```

### 4. Composite Blocks

File:

```text
composite_blocks.json
```

Purpose:

- Interpret midpoint-composite body positions and composite aspects.
- Surface midpoint ambiguity without treating it as a hidden answer.
- Keep composite houses and Davison out of prose until implemented.

Selector key paths:

```text
body_midpoint -> body
composite_aspect -> aspect
ambiguity_note -> opposite_midpoint
unsupported_layer -> composite_houses | davison
```

Required evidence:

```text
computations.composite.bodies
computations.composite.aspects
computations.composite.status
```

Claim level:

```text
bounded_interpretation
```

### 5. Repeated Theme Blocks

File:

```text
repeated_theme_blocks.json
```

Purpose:

- Interpret repeated natal structures between the two charts.
- Keep repeated themes separate from cross-chart contacts.

Selector key paths:

```text
theme_type -> confidence_state
theme_key -> fallback
```

Required evidence:

```text
computations.repeated_natal_themes
```

Claim level:

```text
bounded_interpretation
```

### 6. Topic And Convergence Blocks

File:

```text
topic_convergence_blocks.json
```

Purpose:

- Interpret relationship topic signatures and convergence records.
- Provide ranked section language without converting convergence into a verdict.

Selector key paths:

```text
topic_signature -> signature_key -> polarity
convergence -> polarity -> localization
confidence_note -> confidence_state
```

Required evidence:

```text
computations.relationship_topic_signatures
computations.relationship_convergence
```

Claim level:

```text
bounded_interpretation
```

## Current Authored Families

Round 1 currently covers:

- five major aspect families with body-to-body and angle-localized branches
- body-family summaries for luminaries, personal planets, social planets, outers,
  angles, and node or Chiron material
- twelve house domains plus source-body and confidence overlays
- midpoint composite bodies, composite aspects, and midpoint ambiguity notes
- repeated natal theme families and their confidence handling
- eight relationship topic signatures
- convergence localization notes
- sidecar claim-safety, withholding, and unsupported-layer notes

## Not Included Yet

Round 1 still does not include:

- a selector implementation
- a report template
- product registry exposure
- client-facing report availability
- timing prose
- Davison prose beyond technical disclosure
- composite-house prose beyond technical disclosure

Those remain separate implementation waves.
