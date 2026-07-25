# Location Services Operational Audit

Date: July 25, 2026

## Scope

This audit reflects the actual codebase state in `C:\entangled_oracle` after the
Location Services studio/routing work completed on July 25, 2026.

It is intentionally narrower than the long-range product vision docs. The goal
here is to record what is operational now, what is still bounded or partial,
and what the next finish phases should target.

## Operational Now

- Shared location-product routing is live in `generate.py` through
  `products/location_services/routing.py`.
- The private-beta Report Studio exposes:
  - `place_resonance`
  - `place_resonance_search`
  - `world_lines`
  - `local_compass`
  - `living_map`
- Studio input contracts now support:
  - `purpose_lens`
  - `relationship_to_place` where applicable
  - Local Compass `anchor_location`
  - Local Compass optional route corridor inputs
  - Living Map `report_end_date`
- Local Compass and Living Map both generate HTML and manifest outputs through
  the same manifest-writing path as the other reports.

## Findings

### 1. Some older planning docs are now stale

Several Location Services planning documents still describe Local Compass and
Living Map as future-only shells. That is no longer accurate.

Current code reality:

- Local Compass has a real directional engine path in `engine/local_space.py`.
- Living Map has a real date-bounded relocated-angle timing scan in
  `engine/living_map.py`.

What remains true from those docs is narrower:

- neither product has a completed purpose-fit selector taxonomy;
- neither product has a mature block-selector prose system like Place Resonance;
- Living Map still excludes relocated returns, parans, and dynamic
  astrocartography.

### 2. Studio exposure is still incomplete across the family

`between_places` is registry-wired and routable at the generator layer, but it
is not yet exposed in the studio report picker.

That means the studio currently covers the single-place, search, line, local
space, and timing shells, but not the comparison product.

### 3. Local Compass and Living Map still rely on assembler-authored prose

Place Resonance has the strongest selector/block foundation in the family.
Local Compass and Living Map do not yet have equivalent report-safe prose
selection.

Current state:

- Local Compass block scaffold files are still fallback-only.
- Living Map block scaffold files are still fallback-only.
- Their rendered reports depend mostly on assembler-authored explanatory prose,
  not selector-routed block composition.

That is operational, but it is not the same finish level as Place Resonance.

### 4. Purpose awareness is now present, but intentionally bounded

As of July 25, 2026:

- Local Compass includes a purpose-aware reading frame.
- Living Map includes a purpose-aware timing frame.

What this does:

- helps the reader interpret the existing evidence in relation to the stated
  question;
- keeps the route/anchor/date window explicit.

What this does not do:

- rank signals by purpose-fit taxonomy;
- compute strong-fit / tradeoff / low-signal categories;
- claim that a purpose lens has already been promoted into selector truth.

### 5. Review/edit ergonomics were a real operational gap

Before the July 25, 2026 fix, the review page had an `Edit details` action that
returned the user to a blank form.

That is now fixed with a posted edit route that preserves entered values. This
brings the studio flow closer to a usable operator shell instead of a thin demo.

### 6. Living Map still needs governance and product-boundary cleanup

The code now computes a bounded timing overlay:

- daily noon UTC scan;
- transits to relocated angles only;
- explicit date window;
- explicit boundary that timing weather does not replace baseline place
  meaning.

Remaining boundary work:

- clarify which older governance notes are obsolete versus still binding;
- keep existing standard timing clocks out of the location layer unless a
  separate policy says otherwise;
- preserve the exclusion of relocated returns and dynamic astrocartography.

## Recommended Finish Order

### Phase A: Bring comparison into the studio

- Expose `between_places` in `app/services/report_registry.py`.
- Add the paired destination contract to the form/review flow.
- Verify manifest parity and smoke generation.

### Phase B: Build Local Compass and Living Map selector-backed prose seams

- Author or scaffold product-specific selector surfaces.
- Route report sections through structured block families where the data
  contract is already real.
- Keep purpose-fit taxonomy deferred unless the selector logic is actually
  implemented.

### Phase C: Reconcile outdated Location Services planning docs

- Mark the docs that still say Local Compass and Living Map are entirely
  future-only.
- Replace those status claims with narrower, current statements:
  operational method, bounded claim surface, missing selector/prose depth.

### Phase D: End-to-end family QA

- Studio form -> review -> edit -> generate for every exposed location report.
- Manifest checks for report type and date window.
- Real smoke outputs for:
  - Place Resonance
  - Place Resonance Search
  - World Lines
  - Local Compass
  - Living Map
  - Between Places once exposed

## Bottom Line

The astrocartography/location-services family is no longer just a planning
artifact. It has a live generator path, a studio shell, and bounded operational
Local Compass and Living Map reports.

The remaining work is not "make it exist." It is:

- finish studio coverage across the family,
- raise the prose/selector depth of the newer products,
- and clean up the stale planning language so the repo tells the truth about
  what is actually running.
