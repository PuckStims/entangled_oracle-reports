# Place Resonance Content Audit

Status date: 2026-07-14

Audit path: `Horizon -> Weaver -> Scribe -> Sentinel`

## Current State

All four active Place Resonance block files now have authored `body` text:

- `technical_appendix_blocks.json`: 19 authored leaves
- `location_synthesis_blocks.json`: 10 authored leaves
- `relocated_angle_contact_blocks.json`: 241 authored leaves
- `planet_relocated_house_blocks.json`: 731 authored leaves

The old TODO-only state is historical. Future content work should treat the
current task as audit, strengthening, expansion, and routing refinement.

## Horizon Audit

The angle and house grids already do meaningful locational work: they name
what the place foregrounds, how strongly it appears, and what kind of life
arena receives the emphasis.

The synthesis file is the highest-value improvement target because it sets
the report's main conclusion. It should do more than summarize the evidence
shape. It should help the report state what the place is actually better
for, thinner for, louder around, or more demanding about when the evidence
supports that conclusion.

## Weaver Audit

The content libraries are no longer scaffold-only. Tests and handoff notes
must enforce the current authored state instead of the old TODO split.

The current large grids are structurally complete enough for audit passes.
The next content-system need is not more raw coverage; it is better
classification, routing, and synthesis selection where multiple leaf types
could apply.

## Scribe Audit

The prose is generally direct and useful, especially in the angle and house
files. The main risk is that the synthesis leaves can still sound like
careful categorization rather than a reader-facing conclusion.

Synthesis leaves should end with a landing point: what the place asks for,
what it supports, what it is less suited to, or what the reader should not
misread.

## Sentinel Audit

The existing content is careful about guarantees, commands, and unsupported
methods. That caution should remain.

The needed correction is not more disclaimers. It is sharper separation
between:

- a strong symbolic conclusion;
- an unsupported outcome promise;
- a practical perspective that helps the reader use the report.

## Action Taken

- Updated stale test and handoff language that still described the large
  grid files as TODO-only.
- Strengthened `location_synthesis_blocks.json` so synthesis leaves offer
  clearer reader-facing perspective, especially around convergence,
  angularity, house shifts, purpose alignment, purpose tradeoff, mixed
  public/private emphasis, and low-signal cases.
- Added `place_context_modifier_blocks.json` as an authored context bridge
  for smaller practical leaves such as social connection, isolation,
  visibility, restoration, pressure, movement, stability, and intimacy.
  This keeps internal caution in selection logic while allowing report
  prose to name difficult context directly when evidence supports it.
- Added a regression check that rejects empty vague escape phrases such as
  "could mean many different things" and "only you can know."
- Added this audit record so future agents can see the current content
  baseline before proposing more scaffolding.

## Recommended Next Content Work

1. Strengthen `location_synthesis_blocks.json` first.
2. Wire `place_context_modifier_blocks.json` into selector/assembly only
   after a context-axis classifier exists.
3. Add rendered-sample review once synthesis copy is strengthened.
4. Only then consider expanding new purpose, duration, natal-modifier, or
   house-domain families.
