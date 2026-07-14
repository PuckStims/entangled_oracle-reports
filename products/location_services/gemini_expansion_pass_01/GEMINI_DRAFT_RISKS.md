# Gemini Draft Risks — Location Services Expansion Pass 01

**Status:** SELF-AUDIT. This document lists all places where this
Gemini pass may have over-scaffolded, guessed, or introduced review risk.
It is written for Claude Code (Sonnet 5) and ChatGPT/Codex to use as
a triage checklist.

**Reading rule:** Every flagged item is a potential problem. Do not dismiss
any flag without review. If a flag turns out to be harmless, mark it
reviewed and note why.

---

## Risk Category 1: Capability Status Labels

**Risk:** Gemini assigned capability status labels (`AVAILABLE_NOW`,
`AVAILABLE_WITH_WIRING`, `NOT_COMPUTABLE`, `FUTURE_METHOD`) based on reading
`LOCATION_EVIDENCE_RECORD_CONTRACT.md` and `BLOCK_SCHEMA.md`. These labels
are only as accurate as that reading.

### Flagged Items

**1.1 — Natal ruler of relocated Ascendant labeled `AVAILABLE_WITH_WIRING`**

Source: `PRODUCT_DATA_CONTRACT_GAPS.md`, "Evidence Available With Wiring"
section.

`LOCATION_EVIDENCE_RECORD_CONTRACT.md` §3 says: "A genuinely safe 'which
planet rules the relocated Ascendant sign' fact is computable (a pure
sign→ruler dictionary lookup, no condition involved), but that's a new,
narrower helper this pass didn't build since nothing downstream currently
asks for it."

Gemini labeled this `AVAILABLE_WITH_WIRING` based on that language.

**Review question for Claude Code:** Is `sign → ruler dictionary lookup`
truly a no-cost helper, or does it pull in any condition-bearing function?
Confirm safety boundary before approving this label.

---

**1.2 — Batch evidence record generation labeled `AVAILABLE_WITH_WIRING`**

Source: `PRODUCT_DATA_CONTRACT_GAPS.md`, Product 2 gap summary.

Gemini assumed that looping `build_location_evidence_record()` over 2–5
destinations is straightforward wiring. No batch function exists; Gemini
inferred it from the single-record function.

**Review question for Claude Code:** Is there any state mutation, caching,
or payload-sharing constraint in `build_location_evidence_record()` that
would make batch generation unsafe without additional work? Natal payload
sharing assumption (one natal payload, multiple destination records) needs
explicit confirmation.

---

**1.3 — `purpose_lens` and `relationship_to_place` labeled `AVAILABLE_NOW`**

Source: Both are confirmed pass-through fields in the contract. However,
Gemini labeled "Duration-lens selector" as `AVAILABLE_WITH_WIRING`
specifically because the selector logic (reading `relationship_to_place`
and mapping it to block keys) doesn't exist yet.

**Risk:** The distinction between the field being available and the selector
logic being available may not be clear enough in the gap table. Claude Code
should flag any downstream code that assumes the selector exists.

---

**1.4 — `coordinate_precision` described as usable in prose**

Source: `PRODUCT_DATA_CONTRACT_GAPS.md`, "Evidence Available With Wiring."

The contract explicitly says `coordinate_precision` is a "provenance tag,
not a precision measurement" and that true precision bands do not exist.
Gemini described this as `AVAILABLE_WITH_WIRING` if content lane defines
what the provenance tags mean in prose terms.

**Review question for ChatGPT/Codex:** Does the content lane want to define
prose for "user_provided" vs "offline_geonamescache" in the appendix?
If not, this item should be downgraded to `NOT_COMPUTABLE` (cannot produce
real precision language without real precision data).

---

## Risk Category 2: Taxonomy Assumptions

**Risk:** Gemini proposed multiple DRAFT taxonomy sets. All are clearly
labeled DRAFT, but they may still anchor thinking in unhelpful directions.
Each set should be reviewed for whether the categories themselves are sound,
not just whether they are labeled correctly.

### Flagged Items

**2.1 — Between Places comparison pattern taxonomy (DRAFT)**

Source: `BLOCK_FAMILY_EXPANSION_PLAN.md`, BF-BP-01.

Proposed DRAFT values:
```
divergent_emphasis
convergent_emphasis
purpose_differentiating
mixed_signal
low_signal_all
fallback
```

**Risk:** These categories were derived from the product description in
`PRODUCT_STACK.md` and general comparison-report logic. They have no
grounding in existing EO taxonomy. A comparison function that returns one
of these labels does not exist. These labels could constrain the eventual
comparison function design if they are taken as requirements rather than
suggestions.

**Review question for ChatGPT/Codex:** Are these the right categories for
a comparison summary? Should some be merged, renamed, or removed?

**Review question for Claude Code:** When a comparison function is eventually
built, should it produce one of these category strings, or should the
selector derive the pattern from raw evidence without an explicit category
label?

---

**2.2 — World Lines distance band taxonomy (DRAFT)**

Source: `BLOCK_FAMILY_EXPANSION_PLAN.md`, BF-WL-01.

Proposed DRAFT values: `on_line`, `near`, `approaching`, `fallback`.

**Risk:** These band names are invented. The contract states that distance
band thresholds do not exist. Gemini created three named bands as a structural
placeholder.

**Review question for ChatGPT/Codex:** Should the distance band set be
binary (on/off) or graduated? What distance thresholds are defensible for
astrocartography (common practice uses ~100–400km orb but this varies)?
These values must not be adopted without content lane decision.

---

**2.3 — Local Compass use mode taxonomy (DRAFT)**

Source: `BLOCK_FAMILY_EXPANSION_PLAN.md`, BF-LC-02.

Proposed DRAFT values:
```
movement_and_travel
workspace_and_daily_base
ritual_and_orientation
exploration_and_discovery
rest_and_recovery
fallback
```

**Risk:** These categories are structurally similar to `relationship_to_place`
and `purpose_lens` values but are distinct (they describe directional use
modes, not relational stance or goals). Overlap with existing taxonomy
is possible and should be checked.

**Review question for ChatGPT/Codex:** Do these use modes belong in the
block family, or should they be derived from the existing `purpose_lens`
values? Does Local Compass need its own use-mode set, or can it borrow
purpose lens?

---

**2.4 — Living Map time band taxonomy (DRAFT)**

Source: `BLOCK_FAMILY_EXPANSION_PLAN.md`, BF-LM-01.

Proposed DRAFT values: `current_window`, `approaching`, `just_passed`,
`fallback`.

**Risk:** Time band definitions (what counts as "approaching"? days? weeks?
months?) are entirely unspecified. These are placeholder names with no
duration policy behind them.

**Review question for ChatGPT/Codex:** What time band definitions would be
appropriate for a location-timing report? This is likely adjacent to the
existing timing report governance and should be aligned with it.

**Review question for Claude Code:** When date-bounded transit computation
is eventually built, what shape would its output take? The proposed key path
`transit_planet → relocated_angle → time_band` assumes the engine would emit
a time_band field. Confirm this is a plausible output shape.

---

**2.5 — Tradeoff map taxonomy (DRAFT)**

Source: `BLOCK_FAMILY_EXPANSION_PLAN.md`, BF-BP-03.

Proposed DRAFT values:
```
visibility_with_exposure_cost
belonging_with_public_friction
depth_with_isolation_risk
expansion_with_grounding_cost
rest_with_opportunity_gap
structure_with_rigidity_risk
freedom_with_instability_risk
fallback
```

**Risk:** These are constructed from the conflict types in
`EVIDENCE_TO_MEANING_MATRIX.md` (visibility vs. privacy, expansion vs.
structure, etc.), but they are not the same as those conflict types. They
combine a domain and a cost into single labels. This is interpretive
pre-work that belongs to the content lane.

**Review question for ChatGPT/Codex:** Should tradeoff labels combine
domain and cost (as proposed), or should they be two separate keys
(domain → cost_type)? The proposed labels may over-commit to a specific
tradeoff direction.

---

## Risk Category 3: Over-Scaffolding Risk

**Risk:** Gemini may have scaffolded sections or products at a level of
detail that creates unnecessary constraints before the evidence foundation
is proven.

### Flagged Items

**3.1 — Products 3–5 section maps are fully detailed**

Source: `PRODUCT_SUITE_SECTION_MAP.md`, Products 3, 4, and 5.

Gemini wrote detailed section definitions for World Lines Companion, Local
Compass, and Living Map despite all three being entirely pre-engine. The
section definitions are grounded in `PRODUCT_STACK.md`, but detailed
section-level evidence requirements and capability labels for future-method
products may create false specificity.

**Review question for Claude Code:** Are the evidence field names proposed
for products 3–5 (e.g., `planetary_lines[*].distance_to_destination`) plausible
output field names, or would a real implementation use different shapes?

**Review question for ChatGPT/Codex:** Should products 3–5 have detailed
section maps at this stage, or should they remain at the high-level
`PRODUCT_STACK.md` description until engine work begins?

---

**3.2 — Stage 4 and 5 roadmap tasks are written as if they will happen soon**

Source: `REPORT_ASSEMBLY_ROADMAP.md`, Stages 4 and 5.

The roadmap is written with concrete TODO task descriptions for World Lines,
Local Compass, and Living Map. These stages have large Future Method
dependencies. The task descriptions may create premature expectations.

**Risk:** These are planning placeholders, not approved work items. They
should not be treated as a sprint plan.

---

**3.3 — Between Places section 2.3 ("Best Fit By Purpose") implies ranking**

Source: `PRODUCT_SUITE_SECTION_MAP.md`, Section 2.3.

The section purpose says: "for the user's stated purpose, which place has
the strongest evidence fit — and what are the tradeoffs?"

**Risk:** "Which place" phrasing could be read as ranking even though the
section description explicitly forbids universal ranking. The product intent
is purpose-specific fit, not rank order.

**Review question for ChatGPT/Codex:** Should section 2.3's purpose language
be revised to more clearly avoid any ranking implication? Suggested
alternative: "How does each place relate to the stated purpose, and what
does the evidence show about fit and tradeoffs per destination?"

---

**3.4 — "Shared natal payload" assumption for Between Places**

Source: `PRODUCT_DATA_CONTRACT_GAPS.md` and `REPORT_ASSEMBLY_ROADMAP.md`
Stage 3.1.

Gemini assumed that Between Places would share one natal payload across all
destinations. This is logical (the birth chart doesn't change), but it needs
explicit engine-level confirmation.

**Risk:** If `build_location_evidence_record()` has any internal mutation
of the natal payload during processing, sharing it across a batch loop would
introduce a subtle bug.

**Review question for Claude Code:** Confirm that `build_location_evidence_record()`
does not mutate its natal_payload argument. If any mutation occurs, the batch
loop must clone the payload per destination.

---

## Risk Category 4: Scope Boundary Risks

**Risk:** Gemini may have inadvertently proposed items that touch non-location
product files, engine calculation logic, or shared libraries.

### Flagged Items

**4.1 — Selector path proposals reference `engine/location_services_selector.py`**

Source: `REPORT_ASSEMBLY_ROADMAP.md`, Stage 1.1.

Gemini proposed `engine/location_services_selector.py` as a possible path.
This is a speculative path. The actual repo structure and routing conventions
are Claude Code's domain.

**Risk:** If there is an existing selector pattern in the codebase that should
be followed, Gemini's proposed path may be incompatible.

**Review question for Claude Code:** What is the correct path and module pattern
for a Location Services block selector, given the existing repo routing?

---

**4.2 — References to "standard timing clocks" in Stage 5**

Source: `REPORT_ASSEMBLY_ROADMAP.md`, Stage 5 task 5.1.

Gemini included a note: "Existing standard timing clocks already promoted
into report-safe use." This language comes from `PRODUCT_STACK.md` (Living Map
section). Gemini did not verify whether any standard timing clocks are
currently in report-safe governance or what "report-safe" means operationally.

**Risk:** This could be read as implying that existing timing clocks can be
used in Living Map without further governance review. That implication is
incorrect.

**Review question for Claude Code and ChatGPT/Codex:** What does "report-safe
governance" mean for existing timing clocks? Is there a governance review
process that Living Map must go through before reusing them in a relocated
timing context?

---

**4.3 — Astrocartography engine path proposed as `astrocartography_line_engine.py`**

Source: `REPORT_ASSEMBLY_ROADMAP.md`, Stage 4.1.

Gemini proposed a filename. This is speculative.

**Risk:** The actual implementation structure (single module, subpackage,
integration with existing angularity formula) is Claude Code's call.

---

**4.4 — Local Space engine path proposed as `local_space_engine.py`**

Same risk as 4.3.

---

## Risk Category 5: Content Voice Risks

**Risk:** Gemini may have used language in _note-equivalent descriptions that
edges toward reader-facing prose direction without being final prose.

### Flagged Items

**5.1 — Section purpose language in `PRODUCT_SUITE_SECTION_MAP.md`**

All section purpose descriptions use language like "Name the dominant symbolic
emphasis" or "Describe the change-of-rooms." These are paraphrases of
`PRODUCT_STACK.md` and `PROSE_GUIDE.md` language.

**Risk:** If a section purpose description is treated as final editorial
direction without ChatGPT/Codex review, it may conflict with the content
lane's actual intent.

**Review question for ChatGPT/Codex:** Are the section purpose descriptions
in `PRODUCT_SUITE_SECTION_MAP.md` consistent with product intent, or should
any be revised?

---

**5.2 — `_note` language in block family leaf examples**

Source: `BLOCK_FAMILY_EXPANSION_PLAN.md`, leaf shape examples.

The `_note` fields in the proposed leaf shapes contain prose-direction
guidance (e.g. "Must not imply improvement or loss. Must name the kind of
life arena that changes."). This is not final reader prose, but it is
directional guidance.

**Risk:** If these notes are taken as final editorial constraints without
content lane review, they may be too restrictive or misaligned.

**Review question for ChatGPT/Codex:** Review the _note content in the
leaf shape examples. Are the constraints they describe correct?

---

## Summary Triage Table

| Risk ID | File | Risk Level | Who Reviews |
|---|---|---|---|
| 1.1 | PRODUCT_DATA_CONTRACT_GAPS.md | Medium | Claude Code |
| 1.2 | PRODUCT_DATA_CONTRACT_GAPS.md | High | Claude Code |
| 1.3 | PRODUCT_DATA_CONTRACT_GAPS.md | Low | Claude Code |
| 1.4 | PRODUCT_DATA_CONTRACT_GAPS.md | Medium | ChatGPT/Codex |
| 2.1 | BLOCK_FAMILY_EXPANSION_PLAN.md | High | Both |
| 2.2 | BLOCK_FAMILY_EXPANSION_PLAN.md | High | ChatGPT/Codex |
| 2.3 | BLOCK_FAMILY_EXPANSION_PLAN.md | Medium | ChatGPT/Codex |
| 2.4 | BLOCK_FAMILY_EXPANSION_PLAN.md | Medium | Both |
| 2.5 | BLOCK_FAMILY_EXPANSION_PLAN.md | High | ChatGPT/Codex |
| 3.1 | PRODUCT_SUITE_SECTION_MAP.md | Medium | Both |
| 3.2 | REPORT_ASSEMBLY_ROADMAP.md | Medium | Both |
| 3.3 | PRODUCT_SUITE_SECTION_MAP.md | Medium | ChatGPT/Codex |
| 3.4 | PRODUCT_DATA_CONTRACT_GAPS.md / REPORT_ASSEMBLY_ROADMAP.md | High | Claude Code |
| 4.1 | REPORT_ASSEMBLY_ROADMAP.md | Medium | Claude Code |
| 4.2 | REPORT_ASSEMBLY_ROADMAP.md | High | Both |
| 4.3 | REPORT_ASSEMBLY_ROADMAP.md | Low | Claude Code |
| 4.4 | REPORT_ASSEMBLY_ROADMAP.md | Low | Claude Code |
| 5.1 | PRODUCT_SUITE_SECTION_MAP.md | Medium | ChatGPT/Codex |
| 5.2 | BLOCK_FAMILY_EXPANSION_PLAN.md | Medium | ChatGPT/Codex |

**High-priority review items (must not proceed without resolution):**

- 1.2: Natal payload sharing assumption for Between Places batch generation
- 2.1: Between Places comparison pattern taxonomy (DRAFT — must not be wired)
- 2.2: World Lines distance band taxonomy (no thresholds defined)
- 2.5: Tradeoff map taxonomy (content-lane authorship required)
- 3.4: Natal payload mutation safety check
- 4.2: Timing clock governance for Living Map
