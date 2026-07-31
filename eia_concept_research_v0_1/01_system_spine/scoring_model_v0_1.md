# Scoring Model v0.1

## Model status

This scoring model is deliberately provisional. It is intended to provide a buildable engine spine, not a finished interpretive doctrine.

## Score units

Each register mode receives a normalized score from 0.00 to 1.00.

```text
final_mode_score = weighted_sum(source_scores) * confidence_modifier
```

## Source score categories

### Natal Signature Score

Direct astrological support for the mode.

Examples:

- Mars/ASC/fire/cardinal -> Direct Spark.
- Moon/water/mutable/Neptune -> Open Field or Tidal Knowing.
- Saturn/earth/2nd/6th/10th -> Structured Commitment, Precision Battery, Material Simplification.

### Aspect/Tension Score

Aspects that modify the mode.

Examples:

- Moon-Neptune opposition may raise Reception: Deep Sponge and Decision: Tidal Knowing, but also distortion risk around fog/idealization.
- Mars-Saturn may raise Structured Commitment or Control Lock depending on context.
- Mercury-Uranus may raise Pattern Recognition or Translator.

### Element/Modality Current Score

Broad elemental and movement signature.

```text
Fire    = ignition, action, heat, courage, pulse.
Earth   = structure, materiality, endurance, repair through practical form.
Air     = contract, language, relational agreements, translation.
Water   = feeling, atmosphere, memory, permeability, restoration through emotional truth.
Aether  = whole-chart integration, liminal/field/symbolic overlays.

Cardinal = initiates.
Fixed    = sustains.
Mutable  = adapts.
```

### EAS Resonance Score

Existing EO/EAS indexes can feed the architecture.

Examples:

- DFIS / Sovereign Queen / Boundary Architect -> Boundary Register: Gate, Blade, Clean Agreement.
- Catalyst Index -> Contact Register: Catalyst/Challenger.
- Kassandra Validation Score -> Reception: Pattern Receiver or Contact: Witness/Translator.
- Narrative Genre Engine -> Expression layer, not permanent EIA mode by itself.

### Polarity Current Modifier

Symbolic current flow modifier.

```text
Positive current  -> output, initiation, radiance, projection.
Negative current  -> reception, absorption, magnetism, inward pull.
Neutral current   -> regulation, integration, witnessing, pause.
```

Use polarity as a metaphorical current model only, not a health claim.

### Optional Divination State Modifier

Only applies to State Overlay reports.

Examples:

- Tarot Tower / Uranus-coded lot -> Threshold Break or Catalyst active now.
- Tarot Temperance / neutral-current lot -> Restoration: Ritual and Repetition or Neutral Integration.
- Rune Isa -> Stillness First / Low-Noise Receiver / pause.

### Optional Client Calibration Modifier

A lightweight intake or check-in can tune outputs.

Example check-in fields:

- Current energy: low / medium / high / volatile.
- Decision pressure: none / mild / intense.
- Input load: quiet / normal / overloaded.
- Relationship pressure: low / moderate / high.
- Body signal clarity: clear / mixed / numb / loud.

## Confidence modifier

Confidence depends on data quality.

```text
Exact birth time:        1.00
Approximate birth time:  0.85
Unknown birth time:      0.65, suppress angle/house-dependent claims
No birth location:       invalid for full report; offer reduced symbolic mode
```

## Mode selection

For each register:

1. Calculate all mode scores.
2. Select highest score as dominant mode.
3. Select secondary if:
   - secondary score >= 0.50; and
   - secondary is within 0.18 of dominant; or
   - secondary explains a clear contradiction pattern.
4. Suppress all others unless practitioner appendix is requested.

## Contradiction rendering

If high-scoring modes conflict, do not smooth them into mush. Name the operating sequence.

Examples:

```text
Direct Spark + Tidal Knowing
Action may begin before meaning settles. The correction is not to stop moving; it is to return after the heat passes.
```

```text
Open Field + Selective Gate
You receive broadly, but your clarity improves when access is chosen. Permeability is a gift only when paired with consent.
```

```text
Anchor + Borrowed Charge
You stabilize others, but prolonged contact can make other people's urgency feel like your own fuel.
```

## Validation plan

Run 10-20 known charts through EIA v0.1 and review:

- Does each register feel distinct?
- Are outputs too close to HD vocabulary?
- Does the report give practical decision relief?
- Does it preserve EO poetic identity while becoming more operational?
- Do contradiction outputs feel accurate rather than confused?
- Are restoration keys actionable?
