# Tarot / Lots / Entropy State Overlay

## Role in EIA

Tarot, runes, and lots should function like current-state observation tools. They do not create the baseline architecture.

## Core idea

```text
Natal architecture = stable operating map.
Entropy state overlay = what is active right now.
```

## Entropy-derived workflow

1. App collects environmental/user-device entropy sources where available.
2. System normalizes entropy into a cryptographic seed.
3. User locks the moment before reveal.
4. Seed deterministically produces tarot/rune/lots state snapshot.
5. Result is interpreted through EIA registers.
6. Snapshot can be reproduced from seed and timestamp.

## Overlay questions

The State Overlay should answer:

- Which register is loud right now?
- Which distortion pattern is activated?
- What is the restoration key for this moment/week?
- What experiment should the user try?
- What should not be over-interpreted?

## Tarot as symbolic grammar

Tarot can map to registers without becoming permanent identity.

Examples:

| Tarot family | EIA register influence |
|---|---|
| Wands | Ignition / Current |
| Cups | Reception / Restoration / Contact |
| Swords | Decision / Boundary / Pattern Recognition |
| Pentacles | Current / Restoration / Material Simplification |
| Major Arcana | Cross-register activation / major state theme |

## Rune/lots as spatial grammar

Runes and lots can modify state by placement, clustering, crossing, distance, orientation, and region of the casting field.

Examples:

- Cluster near center -> core signal activated.
- Crossed lot -> friction/distortion.
- Far outer region -> environmental/world pressure.
- Boundary-line placement -> threshold or agreement issue.

## State output structure

```json
{
  "state_snapshot": {
    "seed_id": "...",
    "method": "tarot_entropy",
    "active_register": "Decision Register",
    "state_symbol": "Two of Swords",
    "activation": "Stillness First",
    "distortion_risk": "Over-translation",
    "restoration_key": "Naming and Writing",
    "experiment": "Write the decision in one sentence, then wait until the body softens or tightens."
  }
}
```

## Guardrails

- Do not use state overlays for emergency or high-stakes decisions.
- State snapshots are reflective aids, not commands.
- The user retains authority.
- Do not override real-world information.
- Do not imply the entropy source is supernatural proof.
