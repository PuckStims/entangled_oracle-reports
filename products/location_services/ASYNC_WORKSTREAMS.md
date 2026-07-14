# Location Services Async Workstreams

**Status:** Division-lead work plan for parallel Location Services development.  
**Purpose:** Split asynchronous work between ChatGPT and Claude Code without flattening either agent's strengths.  
**Operating principle:** ChatGPT leads content, method analysis, evidence language, and precision. Claude Code leads repo adaptation, wiring, scaffolding, tests, and implementation repair.

## Current Direction Overlay

This document predates the Place Resonance Search pivot. Treat the current
product hierarchy as:

1. **Place Resonance Search** - flagship curated discovery/search report.
2. **Place Profile** - reusable one-location evidence unit, currently
   implemented by the existing Place Resonance code path.
3. **Between Places**, **World Lines Companion**, **Local Compass**, and
   **Living Map** - descendants or adjacent products that should reuse the
   relevant profile/search contracts once they are real.

Older references below that call Place Resonance the permanent anchor should be
read as references to the working single-place profile engine, not as a reason
to collapse the new search product back into a one-city report.

## Shared Destination

Location Services is not a side feature. It is a product family that turns place into an auditable interpretive layer:

```text
birth UTC instant + destination coordinates
-> relocated chart baseline
-> location evidence records
-> product-specific prose, comparison, maps, timing, and appendices
```

The first fully stable implementation path is the existing one-location Place
Resonance code, now treated architecturally as the reusable **Place Profile**
engine. The flagship product direction is **Place Resonance Search**, which
will reuse profile evidence across a curated candidate pool instead of asking
the user to begin with one chosen city.

## Non-Negotiable Boundaries

- A place does not rewrite the natal chart. It changes which parts of the chart become louder, more visible, more private, more pressured, more available, or more consequential.
- Relocation must preserve the original birth UTC instant. Destination location never reinterprets the birth time as local destination time.
- Tropical zodiac and Whole Sign houses remain the production baseline unless explicitly reopened.
- Natal planetary condition modifies relocated expression; relocation does not rewrite natal condition.
- Location claims must be evidence-routed, not keyword-based.
- No report should say a city guarantees love, wealth, success, danger, illness, or destiny.
- Static location evidence comes before dynamic timing overlays.
- Standard timing clocks should graduate through existing reports before Living Map depends on them.
- TODO prose is acceptable only where the scaffold is intentionally non-client-facing or the test contract permits it. Current Year Ahead Tier 5 timing blocks should not receive literal TODO placeholders.

## Shared Evidence Contract To Design Around

Both leads should align to a future `LocationEvidenceRecord`:

```text
LocationEvidenceRecord
  birth_context
    birth_date
    birth_time
    birth_location
    birth_timezone
    birth_time_confidence
    utc_instant
    calculation_profile

  destination_context
    display_name
    latitude
    longitude
    timezone
    coordinate_precision
    user_relationship
    purpose_lens

  relocated_chart
    ascendant
    midheaven
    descendant
    imum_coeli
    house_system
    house_cusps
    planet_house_changes
    relocated_angle_contacts
    relocated_chart_ruler_notes

  natal_modifiers
    natal_condition_of_emphasized_planets
    natal_house_rulership_links
    natal_aspect_modifiers
    natal_angularity_modifiers

  astrocartography
    nearest_lines
    line_distances
    nearest_points
    distance_bands
    line_strength_estimates
    excluded_line_claims

  dynamic_location_timing
    date_range
    timing_method
    active_windows
    static_signature_relationship
    temporary_strength_notes

  evidence_ranking
    primary_evidence
    supporting_evidence
    contradictory_evidence
    speculative_or_excluded_evidence
    confidence_notes

  prose_inputs
    dominant_place_theme
    secondary_place_themes
    practical_modes
    resonance_scope
    technical_terms_to_name
    safety_notes

  appendix_trace
    calculation_sources
    tolerances
    unsupported_methods
    warnings
```

## ChatGPT Lead: Content, Method, And Precision

ChatGPT should operate as **Content Analysis and Interpretive Systems Lead**.

### Work Packet C1: Product End-State Spec

Deliverable:

- A polished end-state product spec for:
  - Place Resonance
  - Between Places
  - World Lines Companion
  - Local Compass
  - Living Map

Required focus:

- Define the user question each product answers.
- Define included and excluded evidence.
- Define report sections and section jobs.
- Define what the product must never claim.
- Define what data each product needs from the backend.

Output file:

```text
products/location_services/PRODUCT_STACK.md
```

### Work Packet C2: EO Locational Prose Guide

Deliverable:

- A prose guide for locational reports that extends the existing EO voice into place analysis.

Required focus:

- Strong, bounded interpretation.
- No travel-horoscope tone.
- No universal "best place" framing.
- Language for support, pressure, resonance, relocation, duration, purpose lens, and uncertainty.
- Examples of acceptable and unacceptable phrasing.

Output file:

```text
products/location_services/PROSE_GUIDE.md
```

### Work Packet C3: Evidence-To-Meaning Matrix

Deliverable:

- A structured interpretive matrix for the first Place Resonance content system.

Required focus:

- Relocated angle contacts by angle: Ascendant, Midheaven, Descendant, IC.
- Planetary emphasis by planet.
- House-change meaning by natal house -> relocated house.
- Natal modifier rules: dignity, sect, angularity, rulership, aspect pressure/support.
- Purpose lens modifiers: career, belonging, rest, partnership, creative visibility, study, retreat.

Output file:

```text
products/location_services/EVIDENCE_TO_MEANING_MATRIX.md
```

### Work Packet C4: Content Block Schema

Deliverable:

- JSON schema proposal for the future Place Resonance block libraries.

Required focus:

- In-depth leaves like other EO JSON blocks.
- Placeholder prose allowed only where explicitly non-client-facing or test-safe.
- Each string should carry notes about intended meaning when prose is not final.
- Keys should match likely engine evidence fields, not vibes.

Suggested block families:

```text
relocated_angle_contact_blocks.json
planet_relocated_house_blocks.json
house_shift_blocks.json
natal_modifier_blocks.json
purpose_lens_blocks.json
location_synthesis_blocks.json
technical_appendix_blocks.json
```

Output file:

```text
products/location_services/BLOCK_SCHEMA.md
```

### Work Packet C5: Competitive And Method Research Brief

Deliverable:

- A concise, citation-ready research brief for competitor products and method requirements.

Required focus:

- Astrocartography expectations.
- Relocated chart expectations.
- Local Space and parans as future methods.
- What competitors overclaim or under-explain.
- How EO differentiates with evidence routing and transparent appendices.

Output file:

```text
products/location_services/RESEARCH_BRIEF.md
```

## Claude Code Lead: Wiring, Scaffolding, And Engine Expansion

Claude Code should operate as **Implementation and Integration Lead**.

### Work Packet D1: Capability Inventory From Local Files

Deliverable:

- A repo-grounded inventory of what is already computed, computable with wiring, and not currently possible.

Required focus:

- Birth/destination resolver reuse.
- UTC/JD preservation.
- Angle and house recalculation.
- Standard formula modules that can be rerun on relocated payloads.
- Existing transits/progressions/returns/profections/ZR status.
- Missing astrocartography, Local Space, parans, relocated returns.

Output file:

```text
products/location_services/CAPABILITY_INVENTORY.md
```

### Work Packet D2: Relocated Payload Prototype

Deliverable:

- A minimal non-reporting engine helper that builds a relocated chart baseline from an existing natal payload and destination coordinates.

Implementation target:

```text
engine/location_services.py
```

Expected functions:

```python
build_relocated_payload(natal_payload: dict, destination: dict) -> dict
compare_natal_to_relocated(natal_payload: dict, relocated_payload: dict) -> dict
```

Hard requirements:

- Preserve birth UTC instant / Julian Day.
- Recalculate angles for destination latitude/longitude.
- Regenerate Whole Sign houses from relocated Ascendant.
- Reassign existing natal body longitudes into relocated houses.
- Preserve natal condition separately from relocated expression.
- Do not mutate the original natal payload.

Test target:

```text
tests/test_location_services_relocated_payload.py
```

### Work Packet D3: Location Evidence Record Scaffold

Deliverable:

- A structured evidence builder that turns relocated comparison output into a stable record shape.

Implementation target:

```text
engine/location_services.py
```

Expected functions:

```python
build_location_evidence_record(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> dict
```

Hard requirements:

- Emit stable keys even when evidence is missing.
- Include appendix trace and warnings.
- Include `unsupported_methods` for astrocartography, Local Space, parans, and relocated returns until implemented.
- Include evidence ranking placeholders with real structured reasons, not prose fluff.

Test target:

```text
tests/test_location_services_evidence_record.py
```

### Work Packet D4: Report Context Scaffold

Deliverable:

- A Place Resonance context builder that can feed a future template without final prose.

Implementation target options:

```text
products/location_services/
generate.py
```

Expected output:

- `place_summary`
- `strongest_structural_shift`
- `angle_contacts`
- `house_changes`
- `natal_modifiers`
- `evidence_summary`
- `technical_appendix`

Hard requirements:

- Do not create final client prose if ChatGPT's block schema is not ready.
- Use `TODO` only if tests are written to expect scaffold-only fields.
- Prefer structured placeholders such as:

```json
{
  "body": "TODO",
  "_note": "Explain how relocated Venus on the MC changes public/social visibility without promising success."
}
```

### Work Packet D5: CLI/Generation Seam

Deliverable:

- A narrow generation path for a Place Resonance sample, gated so it does not affect current products.

Possible CLI shape:

```text
python generate.py --report-type place_resonance --destination "Chicago, IL"
```

Hard requirements:

- Existing report types remain unchanged.
- Missing destination fails clearly.
- Birth exactness warnings are visible in context.
- The first sample can render a scaffold HTML or context JSON; final PDF polish is later.

## Interface Between Leads

### ChatGPT Hands To Claude

ChatGPT should deliver:

- Product stack.
- Prose guide.
- Evidence-to-meaning matrix.
- Block schema.
- First-pass JSON block key plan.

Claude should consume these by:

- Matching evidence field names to proposed block keys.
- Rejecting block keys that cannot be produced deterministically.
- Adding comments where content asks for evidence that does not exist yet.

### Claude Hands To ChatGPT

Claude should deliver:

- Capability inventory.
- Relocated payload/evidence record schema.
- Sample evidence records.
- Any unsupported or ambiguous fields.
- Test fixtures showing actual output shapes.

ChatGPT should consume these by:

- Revising content schema to match actual output.
- Writing or refining block leaves.
- Tightening prose claims around real available evidence.

## Suggested Parallel Sequence

### Round 1: Split Discovery

ChatGPT:

- Write `PRODUCT_STACK.md`, `PROSE_GUIDE.md`, and `EVIDENCE_TO_MEANING_MATRIX.md`.

Claude:

- Write `CAPABILITY_INVENTORY.md`.
- Prototype `build_relocated_payload()`.

Merge point:

- Compare ChatGPT's desired evidence fields against Claude's actual relocated payload output.

### Round 2: Contract Formation

ChatGPT:

- Write `BLOCK_SCHEMA.md`.
- Draft first no-prose or TODO-note block scaffolds.

Claude:

- Build `LocationEvidenceRecord`.
- Add tests for UTC preservation, house changes, angle contacts, stable missing-method warnings.

Merge point:

- Freeze v0.1 evidence keys before any real prose expansion.

### Round 3: First Product Surface

ChatGPT:

- Fill the highest-value Place Resonance prose leaves.
- Write technical appendix language.

Claude:

- Build context builder and first scaffold render.
- Add CLI seam if safe.

Merge point:

- Generate one sample Place Resonance report and review it for evidence/prose alignment.

### Round 4: Expansion Gate

Only after Place Resonance has a stable evidence record:

- Between Places can compare multiple `LocationEvidenceRecord` objects.
- World Lines Companion can add astrocartography geometry.
- Local Compass can add Local Space.
- Living Map can add date-bounded timing overlays.

## Prompt For ChatGPT Lead

```text
You are the Content Analysis and Interpretive Systems Lead for Entangled Oracle Location Services.

Work in products/location_services only unless explicitly asked otherwise.

Your job is to define the end-state product and prose system for Place Resonance and the broader Location Services stack. You are especially responsible for precision: do not ask the backend to support claims it cannot compute, and do not flatten locational astrology into generic planet keywords.

Create or update:
- PRODUCT_STACK.md
- PROSE_GUIDE.md
- EVIDENCE_TO_MEANING_MATRIX.md
- BLOCK_SCHEMA.md
- RESEARCH_BRIEF.md if external/method comparison is requested

Use strong, bounded EO language. Avoid universal best-place claims, deterministic life guarantees, and generic travel-horoscope phrasing.
```

## Prompt For Claude Code Lead

```text
You are the Implementation and Integration Lead for Entangled Oracle Location Services.

Work from local files first. Do not assume planned methods exist. Trace the real call paths and preserve existing report behavior.

Your job is to create the backend seam for Place Resonance:
- repo-grounded CAPABILITY_INVENTORY.md
- engine/location_services.py
- tests for relocated payloads and LocationEvidenceRecord scaffolding
- optional report context scaffold only after the evidence object is stable

Hard boundaries:
- Preserve the natal UTC instant when relocating.
- Do not mutate the natal payload.
- Do not introduce final prose before the content schema is ready.
- Represent unsupported methods explicitly.
- Keep existing Year Ahead and Personal Forecast behavior unchanged.
```

## Stop Conditions

Pause and reconcile before continuing if:

- ChatGPT proposes a required evidence field Claude cannot compute.
- Claude changes evidence keys after ChatGPT has begun block-writing.
- Any locational code changes existing natal payload semantics.
- Any implementation introduces a new methodology profile.
- Any sample report claims a location guarantees an outcome.
- Dynamic timing work begins before the static location baseline is stable.
