# Local Compass Implementation Notes

This product provides local space horizon-based direction.

## Key Principles
- **Directional Focus**: Focuses on anchor-place directions and relocation vectors.
- **Future Method Boundaries**:
  - `azimuth_computation`: Direction-ray computation is not computed yet.
  - `direction_strength`: Direction strength policy is not implemented yet.
- **Honest Placeholders**: We DO NOT fake azimuth or direction-ray computation. Ensure the templates and schemas explicitly mark this.

## DRAFT Taxonomy Notes
- `direction_sector`: (DRAFT) Used to categorize directional vectors (e.g. `north`, `south`, `east`, `west`, and intermediate points).
