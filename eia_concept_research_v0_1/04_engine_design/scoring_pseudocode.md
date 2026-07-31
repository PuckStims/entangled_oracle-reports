# Scoring Pseudocode

```python
REGISTERS = [
    "ignition",
    "reception",
    "decision",
    "current",
    "boundary",
    "contact",
    "restoration",
]

BASELINE_WEIGHTS = {
    "natal_signature": 0.55,
    "eas_resonance": 0.20,
    "polarity_current": 0.15,
    "biophysical_metaphor": 0.10,
    "state_overlay": 0.00,
    "client_calibration": 0.00,
}

STATE_WEIGHTS = {
    "natal_architecture": 0.40,
    "current_transits": 0.20,
    "entropy_divination": 0.25,
    "client_checkin": 0.15,
}


def build_eia_report(natal_chart, eas_indexes=None, state_overlay=None, client_checkin=None):
    features = extract_astrology_features(natal_chart)
    confidence = birth_time_confidence_modifier(natal_chart.birth_time_confidence)

    register_results = {}

    for register in REGISTERS:
        mode_scores = {}
        for mode in MODES[register]:
            score = 0.0
            score += BASELINE_WEIGHTS["natal_signature"] * score_natal_signature(register, mode, features)
            score += BASELINE_WEIGHTS["eas_resonance"] * score_eas_resonance(register, mode, eas_indexes)
            score += BASELINE_WEIGHTS["polarity_current"] * score_polarity(register, mode, features)
            score += BASELINE_WEIGHTS["biophysical_metaphor"] * score_system_language(register, mode, features)

            if state_overlay:
                score += STATE_WEIGHTS["entropy_divination"] * score_state_overlay(register, mode, state_overlay)
            if client_checkin:
                score += STATE_WEIGHTS["client_checkin"] * score_client_checkin(register, mode, client_checkin)

            mode_scores[mode] = clamp(score * confidence, 0.0, 1.0)

        dominant = max(mode_scores, key=mode_scores.get)
        secondary = select_secondary_mode(mode_scores, dominant)

        register_results[register] = render_register_block(
            register=register,
            dominant_mode=dominant,
            secondary_mode=secondary,
            scores=mode_scores,
            content_pack=CONTENT_PACK,
        )

    pressure_patterns = derive_pressure_patterns(register_results, features, eas_indexes)
    restoration_plan = derive_restoration_plan(register_results, client_checkin)

    return assemble_report(
        natal_chart=natal_chart,
        registers=register_results,
        pressure_patterns=pressure_patterns,
        restoration_plan=restoration_plan,
        state_overlay=state_overlay,
    )
```

## Required implementation modules

```text
eia_engine/
  __init__.py
  feature_extraction.py
  register_scoring.py
  mode_selection.py
  pressure_patterns.py
  content_pack.py
  report_model.py
  renderer_adapter.py
  state_overlay.py
```

## Testing plan

```text
tests/
  test_feature_extraction.py
  test_register_scoring.py
  test_mode_selection.py
  test_suppression_logic.py
  test_schema_validation.py
  test_snapshot_reproducibility.py
```
