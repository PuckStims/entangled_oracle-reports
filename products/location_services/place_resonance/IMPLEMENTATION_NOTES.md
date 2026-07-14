# Place Resonance Implementation Notes

This product is the reference single-location report for the entire
Location Services family.

## Key Principles

- **Reference Contract First**: Place Resonance defines the real
  `LocationEvidenceRecord` contract that later location products should
  reuse rather than reinvent.
- **Static Locational Baseline**: This product explains what a place
  consistently emphasizes through relocation evidence. It is not a timing
  or map-first product.
- **Evidence Before Prose**: Selector leaves, evidence ranking, and
  technical appendix traceability come before cosmetic template expansion.
- **No Outcome Guarantees**: It can speak confidently about pattern and
  emphasis, but it must not promise life results.
- **Package Normalization In Progress**: The dedicated product folder now
  exists, but the canonical assembler and renderer still live at the
  root of `products/location_services/` while tests and tooling migrate.

## DRAFT Taxonomy Notes

- `place_signature`: The top-level synthesis category describing the
  dominant pattern of the relocation evidence.
- `evidence_summary`: Ranked evidence rows used to show why the synthesis
  was selected.
- `technical_appendix`: Traceability and warning-family output for the
  current supported method boundary.
