# Codex Implementation Prompt

You are working inside the Entangled Oracle codebase. Build a v0.1 **Entangled Internal Architecture (EIA)** engine that can generate structured JSON output for a future report renderer.

## Goal

Create a new module that transforms natal chart data + optional existing EAS indexes + optional state overlay into an EIA register map.

EIA is not Human Design. Do not use HD terminology such as BodyGraph, Type, Strategy, Authority, Profile, Centers, Gates, Channels, Incarnation Cross, Rave, or not-self. Use EIA vocabulary: Registers, Modes, Mechanisms, Distortions, Restorations, Experiments.

## Required module structure

Create:

```text
eia_engine/
  __init__.py
  models.py
  feature_extraction.py
  register_scoring.py
  mode_selection.py
  content_pack.py
  state_overlay.py
  report_builder.py
  schema.py
content/eia/
  modes_seed_catalog.json
  register_copy_v0_1.json
  distortion_patterns_v0_1.json
tests/eia/
  test_models.py
  test_mode_selection.py
  test_register_scoring.py
  test_report_builder.py
```

## Data model

Implement a Pydantic/dataclass model for:

- EIAReport
- EIARegisterBlock
- EIAStateSnapshot
- EIAPressurePattern
- EIASourceEvidence

Each register block must include:

- register name
- dominant mode
- optional secondary mode
- score
- mechanism
- distortion
- restoration
- experiment
- source evidence list

## Seven registers

- ignition
- reception
- decision
- current
- boundary
- contact
- restoration

## Modes

Load from `content/eia/modes_seed_catalog.json`.

## Scoring

Implement a rules-first v0.1 scorer with placeholder feature hooks:

```python
score_natal_signature(register, mode, features)
score_eas_resonance(register, mode, eas_indexes)
score_polarity(register, mode, features)
score_state_overlay(register, mode, state_overlay)
```

The first implementation can use simple weighted lookups and must be easy to expand.

Baseline weights:

```python
{
  "natal_signature": 0.55,
  "eas_resonance": 0.20,
  "polarity_current": 0.15,
  "biophysical_metaphor": 0.10,
  "state_overlay": 0.00,
  "client_calibration": 0.00,
}
```

## Mode selection rules

- Highest scoring mode becomes dominant.
- Secondary mode appears when score >= 0.50 and within 0.18 of dominant OR tagged as contradiction-relevant.
- Suppress tertiary modes from consumer output.

## Deliverables

1. Working code.
2. Tests.
3. One sample generated JSON report from fixture natal data.
4. README section explaining that EIA is a symbolic operating-map engine and not a Human Design implementation.

## Quality bar

- No Human Design terminology in public model names or report fields.
- Deterministic output for same input.
- Clear schema validation.
- Easy to add more scoring rules.
- Content pack separated from scoring logic.
