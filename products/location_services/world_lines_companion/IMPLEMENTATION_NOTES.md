# World Lines Companion Implementation Notes

This product is the astrocartography map companion.

## Key Principles
- **Astrocartography Focus**: Focuses on line geometry, distance bands, and line clusters.
- **Future Method Boundaries**:
  - `line_geometry`: ASC, DSC, MC, IC line geometry is not computed yet.
  - `nearest_point`: Nearest line point to the destination is not computed yet.
  - `distance_to_line`: Distance-to-line bands are not computed yet.
  - `line_clusters`: Groupings of overlapping lines are not computed yet.
- **Honest Placeholders**: The assembler and template must wire up the current `engine/astrocartography_svg.py` contract, which explicitly states the line geometry is missing. We DO NOT fake line geometry.

## DRAFT Taxonomy Notes
- `distance_band`: (DRAFT) Used to categorize proximity to a line (e.g. `tight`, `moderate`, `wide`, `background`).
