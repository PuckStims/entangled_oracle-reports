# Living Map Implementation Notes

This product adds dynamic timing/weather overlays to a location.

## Key Principles
- **Timing Overlay**: Combines the static locational baseline with dynamic weather (transits).
- **Future Method Boundaries**:
  - `relocated_timing`: Relocated timing computation (transits over the relocated chart) is not implemented yet.
- **Honest Placeholders**: We DO NOT fake relocated timing computation. We explicitly mark the dynamic overlay section as a FUTURE_METHOD placeholder.
- **Grammar Attachment Later**: Timing windows should attach to normalized
  static evidence items from `products/location_services/evidence_grammar/`
  once computation exists. They must not rewrite the permanent location
  baseline.

## DRAFT Taxonomy Notes
- `timing_weather`: (DRAFT) Used to categorize the current transit conditions (e.g. `stormy`, `clear`, `foggy`).
- `baseline_vs_weather`: (DRAFT) Distinguishes what is permanently true about the location (baseline) versus what is temporarily happening there now (weather).
