# Location Services — Gemini Expansion Pass 01

**Status:** FIRST-PASS DRAFT. Not authoritative. Must be reviewed before any
material here is treated as final specification.

**Pass author:** Gemini (Google DeepMind) — high-throughput first-pass breadth
scaffolding role, per `CONTENT_LEAD_HANDOFF.md` multi-agent flow definition.

**Created:** 2026-07-14

---

## What This Pass Is

This folder contains broad, non-client-facing scaffolding and planning
infrastructure for the full Location Services product suite beyond Place
Resonance v0.1. It does **not** replace, modify, or supersede any existing
file in `products/location_services/`.

Everything here is draft-quality expansion material intended to open pathways
for later review and implementation. It is not architectural truth.

---

## Required Review Before Any Item Becomes Authoritative

### ChatGPT / Codex Review Required

- Product/content truth for all five product definitions
- Section purpose language and claim-boundary language
- Draft taxonomy options (all marked DRAFT — must not be wired as final)
- Purpose-lens, duration-lens, and house-domain language
- Any prose direction in _note fields

### Claude Code (Sonnet 5) Review Required

- JSON schema alignment against `BLOCK_SCHEMA.md` and
  `LOCATION_EVIDENCE_RECORD_CONTRACT.md`
- Repo path accuracy for all proposed files and folders
- Data contract gaps — verify status labels against actual engine capability
- Block family proposals — confirm they don't conflict with existing blocks/
  selectors
- Implementation roadmap sequencing — confirm against active repo state
- Test scope boundaries — confirm no proposed tests require engine changes
- Any invented keys must be reconciled or quarantined

---

## What Must Not Be Treated As Final

- Any taxonomy listed as DRAFT in any file here
- Any data contract item labeled "not currently computable" or "future method"
- Any block family proposals that depend on unresolved domain taxonomy
- Any report section definitions for products 3–5 (World Lines Companion,
  Local Compass, Living Map) — these products have no implemented backend yet
- The REPORT_ASSEMBLY_ROADMAP staged path — stage sequencing needs Claude
  validation against actual repo routing before it becomes a build plan
- The handoff note at the end of this README — it describes next steps, not
  approved implementation decisions

---

## Files In This Pass

```
README.md                          -- this file
PRODUCT_SUITE_SECTION_MAP.md       -- report section outlines for all 5 products
PRODUCT_DATA_CONTRACT_GAPS.md      -- evidence inventory with capability status
BLOCK_FAMILY_EXPANSION_PLAN.md     -- future block family proposals (TODO-only)
REPORT_ASSEMBLY_ROADMAP.md         -- staged implementation path draft
GEMINI_DRAFT_RISKS.md              -- review risks, taxonomy flags, over-scaffolding
```

Optional subfolders (if created in this pass):

```
product_scaffolds/
  place_resonance/
  between_places/
  world_lines_companion/
  local_compass/
  living_map/
```

---

## What Was Not Touched

The following were not read in a way that would permit modification, and were
not modified:

- `products/location_services/blocks/` — existing block files are untouched
- `engine/` — no engine files
- Any Year Ahead, Personal Forecast, Daily, Weekly, Soul Ecosystem, or
  Identity Profile product files
- `BLOCK_SCHEMA.md`, `LOCATION_EVIDENCE_RECORD_CONTRACT.md`,
  `EVIDENCE_TO_MEANING_MATRIX.md`, `PROSE_GUIDE.md`, `PROSE_PURPOSE_REVIEW.md`,
  `PRODUCT_STACK.md`, `CONTENT_LEAD_HANDOFF.md` — all read-only for this pass

---

## Handoff Note For Claude Code (Sonnet 5) and ChatGPT/Codex

See the end of `REPORT_ASSEMBLY_ROADMAP.md` for the full handoff note.

Short version:

**What was created:** Six planning/scaffold documents inside this folder,
covering all five Location Services products. No engine files, no block prose,
no final taxonomy. All taxonomy options are DRAFT and labeled as such.

**What must be reviewed:** Every capability status label in
`PRODUCT_DATA_CONTRACT_GAPS.md`. Every block family proposal in
`BLOCK_FAMILY_EXPANSION_PLAN.md`. All draft taxonomy. All roadmap stage
sequencing.

**What must not be treated as final:** Anything in this folder until Claude
Code has validated schema alignment and ChatGPT/Codex has validated product
and content truth.

**Next safest implementation step:** Claude Code should read this folder,
audit it for blockers and path errors, and report back a bounded list of
quarantine candidates before any scaffold file here is promoted into active
repo routing.
