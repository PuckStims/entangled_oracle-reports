# Report Assembly Roadmap — Location Services

**Status:** GEMINI FIRST-PASS DRAFT. Staged path proposed for review.
Stage sequencing, path names, and implementation decisions must be
validated by Claude Code before any stage becomes a build target.
ChatGPT/Codex should validate product and content-section ordering.

**This document does not authorize any implementation step.**

---

## Roadmap Principles

1. Each stage builds a stable foundation before the next stage begins.
2. No stage begins if its prerequisite evidence is not stable.
3. Products 3–5 (World Lines Companion, Local Compass, Living Map) must
   not be started before the static evidence record and Place Resonance
   render skeleton are stable.
4. Dynamic timing (Living Map) is last — it depends on the static baseline
   being proven in production before any time-layer is added.
5. Unsupported methods must not appear in rendered reports as evidence
   until they are implemented and validated.

---

## Stage 1: Place Resonance Render Skeleton

**Goal:** A working end-to-end report render for a single destination,
using the existing v0.1 `LocationEvidenceRecord` and the Round 4 block
scaffold.

**Prerequisites:**
- `build_location_evidence_record()` stable (confirmed v0.1)
- Round 4 block scaffold in `blocks/plainspeak/` (745 TODO leaves confirmed)
- `BLOCK_SCHEMA.md` v0.1 final

### Stage 1 Tasks

**1.1 — Block Loader / Selector Scaffold**

```
TODO: Build a block loader that reads JSON files from
products/location_services/blocks/plainspeak/ and returns block leaves
by key path.

TODO: Build a block selector that accepts a LocationEvidenceRecord and
a block family name, and returns the correct leaf (or fallback).

Proposed location: engine/location_services_selector.py (or equivalent)
NOTE: Claude Code must confirm path against active repo routing. Do not
assume this path is correct.
```

**1.2 — Technical Appendix Section Render**

```
TODO: Wire technical_appendix_blocks.json into a report section.
Uses: appendix_trace, warning_summary, unsupported_methods,
      birth_context.birth_time_confidence, destination_context.coordinate_precision.
All leaves are TODO-body with _note guidance. Section can render
structurally before final prose is authored.
```

**1.3 — Evidence Summary Table Render**

```
TODO: Wire evidence_ranking into a rendered evidence table.
Columns: evidence ID, type (angle_contact / house_change / orientation_shift /
         natal_modifier / unsupported), confidence, rank tier.
Table structure can be finalized before prose rows are authored.
```

**1.4 — Relocated Angle Contacts Section Render**

```
TODO: Wire relocated_angle_contact_blocks.json into the angle contacts
section. Selector key path: angle → body → contact_strength.
All bodies are TODO. Section renders structurally.
```

**1.5 — Planet Relocated House Section Render**

```
TODO: Wire planet_relocated_house_blocks.json into the house shifts section.
Selector key path: body → relocated_house → movement_type.
All bodies are TODO. Section renders structurally.
```

**1.6 — Location Synthesis Section Render**

```
TODO: Build synthesis selector logic that reads evidence_ranking and
selects one of the 9 synthesis categories from location_synthesis_blocks.json.
This requires the selector to understand which category applies:
  convergent_place_signature: multiple evidence types repeat same body/angle
  angle_led_signature: primary evidence is angle contact(s) only
  house_shift_led_signature: primary evidence is house changes only
  repeated_body_signature: same body appears in both angle and house evidence
  quiet_continuity_signature: no house changes, no strong angle contacts
  mixed_public_private_signature: (uses narrower proxy — MC/ASC vs IC/DSC contacts)
  purpose_aligned_signature: purpose_lens matches primary evidence domain
  purpose_tradeoff_signature: purpose_lens conflicts with primary evidence
  low_signal_signature: no primary evidence at all
NOTE: mixed_public_private_signature in existing scaffold uses a narrower
proxy (MC/ASC vs IC/DSC) not the full house-domain taxonomy. See
CONTENT_LEAD_HANDOFF.md Round 4 note. Do not expand this beyond the proxy
without content lane approval.
```

**Claude Code must validate before Stage 1 is called complete:**

- [ ] All proposed selector key paths match actual JSON structure in
      `blocks/plainspeak/` files
- [ ] Loader does not touch any non-location block files
- [ ] Selector does not require engine changes
- [ ] Synthesis category selection logic does not invent new taxonomy
- [ ] Technical appendix section uses `warning_summary`, not raw `warnings`
- [ ] Tests added for selector behavior (fallback paths, missing key handling)

---

## Stage 2: Selector Integration and Taxonomy-Gated Blocks

**Goal:** Wire the four deferred block families (house_shift, purpose_lens,
duration_lens, natal_modifier) after selector taxonomy is established.

**Prerequisites:**
- Stage 1 complete and tested
- Content lane has authored house-to-domain mapping table
- Content lane has authored purpose-fit taxonomy
- Synthesis selector is stable

### Stage 2 Tasks

**2.1 — House-to-Domain Taxonomy Handoff**

```
TODO: Receive from content lane: explicit house → domain table
(mapping houses 1–12 to a controlled domain set).
NOTE: Do not invent this mapping. The EVIDENCE_TO_MEANING_MATRIX.md
table gives rich per-house themes, not a 4-bucket enum. The mapping
is a content decision, not an engine decision.
```

**2.2 — House Shift Blocks Scaffold**

```
TODO: Once house-to-domain mapping exists, scaffold house_shift_blocks.json
with natal_house → relocated_house key path.
Grid: 12 × 12 max. Same-house entries will likely be fallback-only.
All bodies: TODO with _note guidance.
```

**2.3 — Purpose Lens Blocks Scaffold**

```
TODO: Once purpose-fit taxonomy and evidence-domain classification exist,
scaffold purpose_lens_blocks.json with purpose_lens → evidence_domain → fit_type.
```

**2.4 — Duration Lens Blocks Scaffold**

```
TODO: Once synthesis selector is stable (Stage 1.6), scaffold
duration_lens_blocks.json with relationship_to_place → dominant_theme.
```

**2.5 — Natal Modifier Blocks Scaffold**

```
TODO: Scaffold natal_modifier_blocks.json.
Cover: sect_condition and condition_classification key axes.
Fallback required for every body (nodes, Lilith, asteroids have no modifier records).
```

**2.6 — Contradictory Evidence Handling**

```
TODO: Once domain taxonomy exists (from 2.1), implement contradictory_evidence
population in build_location_evidence_record().
This is not a Stage 1 item — it requires the same domain taxonomy as
house_shift and domain_movement_type.
```

**Claude Code must validate before Stage 2 is called complete:**

- [ ] House-to-domain mapping received and authored by content lane (not invented)
- [ ] No domain labels invented in engine output without content lane approval
- [ ] Natal modifier blocks have explicit fallback for non-core-planet bodies
- [ ] Purpose and duration block key paths match actual selector output shapes

---

## Stage 3: Between Places — Comparison Product

**Goal:** A working two-to-five destination comparison report reusing the
Place Resonance evidence record.

**Prerequisites:**
- Stage 1 and Stage 2 complete
- Single-destination record generation stable
- No new computation required (comparison uses existing records)

### Stage 3 Tasks

**3.1 — Batch Evidence Record Generation**

```
TODO: Build a batch loop that accepts a list of 2–5 destination inputs
and calls build_location_evidence_record() per destination.
Returns a list of LocationEvidenceRecord objects.
Share natal_payload across destinations — do not regenerate per destination.
NOTE: Claude Code should confirm that natal_payload sharing is safe and
that no destination-specific mutation occurs.
```

**3.2 — Comparison Function**

```
TODO: Build compare_location_records(records: list[LocationEvidenceRecord])
that returns:
  - shared_evidence: evidence appearing in multiple records
  - divergent_evidence: evidence unique to specific destinations
  - purpose_fit_per_destination: purpose-lens fit per record
  - comparison_pattern: one of the DRAFT taxonomy values from
    BLOCK_FAMILY_EXPANSION_PLAN.md BF-BP-01
NOTE: comparison_pattern taxonomy is DRAFT and must be reviewed by
ChatGPT/Codex before being wired.
```

**3.3 — Between Places Block Scaffolds**

```
TODO: Scaffold block files under blocks/plainspeak/between_places/ for:
  - place_comparison_summary_blocks.json (BF-BP-01)
  - place_profile_compact_blocks.json (BF-BP-02)
  - tradeoff_map_blocks.json (BF-BP-03)
All leaves: TODO with _note guidance. No final prose.
```

**3.4 — Between Places Report Template**

```
TODO: Build report template that assembles:
  Section 2.1: Comparison Summary
  Section 2.2: Place Profiles (compact, per destination)
  Section 2.3: Best Fit By Purpose
  Section 2.4: Strongest Difference
  Section 2.5: Shared Themes
  Section 2.6: Tradeoff Map
  Section 2.7: Decision Notes
  Section 2.8: Technical Appendix (per-destination)
```

**Claude Code must validate before Stage 3 is called complete:**

- [ ] Natal payload is not mutated between destination calls
- [ ] Comparison function does not introduce new evidence methods
- [ ] Comparison pattern taxonomy reviewed by ChatGPT/Codex before wiring
- [ ] Technical appendix correctly traces per-destination, not shared
- [ ] Decision Notes section explicitly states the product does not provide relocation advice

---

## Stage 4: Map-Adjacent Products — World Lines and Local Compass

**Goal:** Lay the engine groundwork for astrocartography and Local Space
evidence. These are Future Method products and cannot be built until
new computation exists.

**Prerequisites:**
- Stage 1–3 complete
- New astrological method engines built and tested separately
- Content lane has authored distance band policy (World Lines)
- Content lane has authored altitude/azimuth convention and direction policy
  (Local Compass)

### Stage 4 Tasks

**4.1 — Astrocartography Line Engine (Prerequisite)**

```
TODO: Build astrocartography_line_engine.py (or equivalent).
Must implement:
  - Planetary ASC, DSC, MC, IC line generation (great-circle geometry)
  - Distance-to-line and nearest-point calculation
  - Antimeridian handling
  - Polar handling
  - Distance band classification (using content-lane-authored policy)
NOTE: This is a significant new computation. It is out of scope for
any existing engine file. Must be built and tested independently before
any World Lines report section is wired.
```

**4.2 — World Lines Evidence Record**

```
TODO: Build build_world_lines_evidence_record() that extends or wraps
LocationEvidenceRecord with:
  - planetary_lines: catalog of ASC/DSC/MC/IC lines per planet
  - line_distances: distance-to-destination per line
  - distance_bands: classified per content-lane policy
  - line_clusters: detection of nearby line groups
  - natal_modifiers: reuse from existing build_location_evidence_record()
NOTE: Do not conflate this with the Place Resonance evidence record.
They may share natal_modifier computation but are separate evidence objects.
```

**4.3 — Local Space Engine (Prerequisite)**

```
TODO: Build local_space_engine.py (or equivalent).
Must implement:
  - Altitude/azimuth calculation for each planet from anchor location
  - Direction ray or great-circle path from anchor
  - Cross-track distance from destination to direction ray
  - Direction strength policy (using content-lane-authored policy)
NOTE: Altitude/azimuth convention must be documented and approved before
this engine is built. Do not assume a convention.
```

**4.4 — World Lines and Local Compass Block Scaffolds**

```
TODO: Scaffold block files under blocks/plainspeak/world_lines/ and
blocks/plainspeak/local_compass/ per BLOCK_FAMILY_EXPANSION_PLAN.md.
All leaves: TODO with _note guidance. No final prose.
```

**Claude Code must validate before Stage 4 is called complete:**

- [ ] Astrocartography line engine does not modify existing angle calculation
      functions in formulas/standard/
- [ ] World Lines evidence record does not run condition-bearing functions
      against relocated payload (same boundary as Place Resonance)
- [ ] Distance band policy authored by content lane, not invented by engine
- [ ] Altitude/azimuth convention documented and approved before implementation
- [ ] All new engines have independent test suites before wiring to reports
- [ ] `unsupported_methods` field updated to remove newly-implemented methods
      only after implementation is confirmed complete

---

## Stage 5: Future Method Overlays — Living Map

**Goal:** Add date-bounded timing to static place evidence.

**Prerequisites:**
- Stages 1–4 complete
- Static Place Resonance baseline proven in production
- Existing standard timing clocks in report-safe governance
- Date-bounded relocated angle transit computation built and tested
- Content lane approval for timing claim governance

### Stage 5 Tasks

**5.1 — Date-Bounded Relocated Timing**

```
TODO: Build relocated_timing_engine.py (or equivalent).
Must implement:
  - Transit-to-relocated-angle computation for a date range
  - Transit-through-relocated-house computation for a date range
  - Clear separation from static Place Resonance evidence
  - Baseline-vs-weather field model
NOTE: This engine must not start before the static evidence record
is proven stable. Do not begin this work in parallel with Stage 1.
```

**5.2 — Living Map Evidence Record**

```
TODO: Build build_living_map_evidence_record() that wraps:
  - Static LocationEvidenceRecord (baseline)
  - Date-bounded transit windows (weather layer)
  - Explicit baseline_vs_weather field model
```

**5.3 — Living Map Block Scaffolds**

```
TODO: Scaffold block files under blocks/plainspeak/living_map/ per
BLOCK_FAMILY_EXPANSION_PLAN.md (BF-LM-01, BF-LM-02).
All leaves: TODO with _note guidance. No final prose.
```

**5.4 — Relocated Return Chart Integration (If Built)**

```
TODO (OPTIONAL, FUTURE): If relocated return chart engine is built,
integrate it as an optional evidence layer for Living Map.
Must not appear in any report before the return chart engine is
validated. Must not be inferred from static Place Resonance evidence.
```

**Claude Code must validate before Stage 5 is called complete:**

- [ ] Timing governance review: any use of existing standard timing clocks
      in relocated context must be reviewed by the timing-report lead
- [ ] Dynamic timing does not retroactively change static Place Resonance
      evidence records
- [ ] Baseline/weather distinction is explicit in every report rendering
- [ ] Relocated returns blocked from report output until engine is confirmed complete

---

## Stage Dependencies Map

```
Stage 1: Place Resonance Render Skeleton
    ↓
Stage 2: Selector Integration + Taxonomy-Gated Blocks
    ↓
Stage 3: Between Places (Comparison Product)
    ↓
Stage 4: World Lines + Local Compass (New Method Engines)
    ↓
Stage 5: Living Map (Dynamic Timing Overlay)
```

No stage should begin without completing the prior stage. Stages 4 and 5
have significant new method dependencies that may take multiple separate
implementation passes.

---

## Handoff Note: For Claude Code (Sonnet 5) and ChatGPT/Codex

### What Was Created

Six planning and scaffold documents in:

```
products/location_services/gemini_expansion_pass_01/
```

Files:

| File | Purpose |
|---|---|
| `README.md` | Pass identity, review requirements, handoff summary |
| `PRODUCT_SUITE_SECTION_MAP.md` | Report section outlines for all 5 products |
| `PRODUCT_DATA_CONTRACT_GAPS.md` | Evidence inventory with capability status labels |
| `BLOCK_FAMILY_EXPANSION_PLAN.md` | Future block family proposals (TODO-only) |
| `REPORT_ASSEMBLY_ROADMAP.md` | Staged implementation path (this file) |
| `GEMINI_DRAFT_RISKS.md` | Review risks, taxonomy flags, over-scaffolding alerts |

### What Must Be Reviewed

**Claude Code (Sonnet 5) — implementation and integrity review:**

1. Verify all `AVAILABLE_NOW` labels in `PRODUCT_DATA_CONTRACT_GAPS.md`
   against the actual v0.1 `LocationEvidenceRecord` contract.
2. Verify all proposed file paths against active repo routing.
3. Verify that no proposed selector or helper function requires engine changes.
4. Identify any invented keys or invented taxonomy in this pass and quarantine them.
5. Confirm Stage 1 task sequencing is achievable without touching engine files.
6. Confirm the synthesis selector logic sketch in Stage 1.6 matches the
   existing `location_synthesis_blocks.json` category structure.
7. Read `GEMINI_DRAFT_RISKS.md` — respond to each flagged risk.

**ChatGPT / Codex — product and content review:**

1. Validate section purpose language for all five products in
   `PRODUCT_SUITE_SECTION_MAP.md`.
2. Review all DRAFT taxonomy options in `BLOCK_FAMILY_EXPANSION_PLAN.md`
   and either approve, revise, or reject each set.
3. Author or delegate authorship of the house-to-domain mapping table
   required for Stage 2.
4. Author or delegate authorship of the distance band policy required for
   Stage 4 (World Lines).
5. Author or delegate authorship of the altitude/azimuth convention
   required for Stage 4 (Local Compass).
6. Review the excluded/unsupported claims list for every section and
   confirm they align with product intent.
7. Read `GEMINI_DRAFT_RISKS.md` — respond to any content-direction risks.

### What Must Not Be Treated As Final

- Any DRAFT taxonomy in any file in this folder
- Any capability status label for `AVAILABLE_WITH_WIRING` items — these
  require wiring work that may surface new constraints
- Stage sequencing — stages may need to be split or reordered based on
  actual repo state
- Any proposed file path — paths must be confirmed against active routing
- The synthesis selector logic sketch — must be validated against actual
  JSON structure in `location_synthesis_blocks.json`
- Any product definition for World Lines Companion, Local Compass, or
  Living Map — these products have no backend and full section definitions
  are based on `PRODUCT_STACK.md` intent only

### Next Safest Implementation Step

Claude Code should:

1. Read this folder.
2. Produce a bounded list of: (a) items that are safe to proceed with as
   written, (b) items that need revision before proceeding, (c) items that
   should be quarantined.
3. Begin Stage 1 only after that triage is complete and reviewed.
4. Do not begin Stage 2 or later stages before Stage 1 is tested and
   confirmed stable.

The single highest-value unblocked action is: **build the block loader and
selector for the four Round 4 block families** and confirm that the existing
JSON structure can be walked with the proposed key paths without any engine
modification. Everything else in this pass depends on that foundation.
