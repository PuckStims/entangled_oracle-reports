# Local Compass Implementation Notes

This product provides local space horizon-based direction.

## Key Principles
- **Directional Focus**: Focuses on anchor-place directions and relocation vectors.
- **Future Method Boundaries**:
  - route-aware travel optimization is not implemented.
- **Live Computation**: Azimuth computation and v1 direction-strength weighting
  are now live, and optional route-corridor geometry is now live.
- **Honest Boundaries**: We DO NOT fake travel-optimization claims beyond
  geometric alignment evidence.
- **Grammar Extension Later**: Directional evidence can now enter the normalized
  evidence grammar; any travel-advice or route-ranking layer should wait for
  its own contract.

## DRAFT Taxonomy Notes
- `direction_sector`: (DRAFT) Used to categorize directional vectors (e.g. `north`, `south`, `east`, `west`, and intermediate points).
