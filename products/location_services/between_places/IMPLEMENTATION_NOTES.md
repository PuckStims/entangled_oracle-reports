# Between Places Implementation Notes

This product compares two locations side-by-side.

## Key Principles
- **Multi-Destination Comparison**: This is not just "Place Resonance twice." The assembly layer must actively compare the evidence profiles of Place A and Place B.
- **No Ranking**: It must not become a "best place" ranking. We provide tradeoff mapping, not prescriptive choice.
- **Shared vs Divergent Evidence**: The context assembler needs to distinguish what remains consistent across both places vs where the evidence diverges significantly.
- **Purpose Fit**: Focuses on tradeoff framing for the specific `purpose_lens` (if provided).
- **No Relocation Advice Guarantee**: Explicitly state that this is an evidence comparison, not guaranteed life advice.

## DRAFT Taxonomy Notes
- `tradeoff_framing`: (DRAFT) Used to categorize the dynamic tension between the two places (e.g. `career_vs_community`, `action_vs_reflection`).
