# Client Forecast Claim Cleanup Queue

Date: 2026-07-07
Source: Phase 1 claim/presentation audit per `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md`
Scope: outward-facing copy only. No source code, formulas, or templates inspected here beyond the two marketing site files below.
Status: closed — one item, resolved 2026-07-07

## Item 1: "personal progressions" claimed for Year Ahead on the live marketing site — RESOLVED

**File:** `entangled_oracle_SITE.html`
**Lines:** 521, 522

```html
<p class="product-desc">A long-range view of the coming twelve months. Analyzes major planetary movements, retrogrades, and personal progressions to help you notice the timing shaping your year.</p>
<button class="btn" onclick="openOrderDemo('The Year Ahead', '$45', 'A long-range twelve-month timing report for major transits, retrogrades, and progressions.')">Select Report</button>
```

**Problem:** secondary progressions are not implemented anywhere in the codebase. Per `EO_MULTICLOCK_ASTEROID_PREDICTIVE_READINESS_AUDIT.md` §4 (Clock System Inventory), `PROGRESSION` exists only as a taxonomy string recognized by `engine/predictive_engine._normalize_method_family()` — no scanner, no progressed-chart constructor, no progressed-to-natal contact detection exists. Year Ahead's actual event sources are `scan_transit_windows`, `scan_house_ingresses`, `scan_stations`, `scan_eclipses`, and `scan_lunations` (`engine/transit_engine.compute_year_ahead_events()`). None of these compute a progression.

This is a live claim, on the $45 product's own order card, for a method the report does not compute.

**Fix:** remove "personal progressions" / "progressions" from both strings. Suggested replacement copy, keeping the existing voice:

```html
<p class="product-desc">A long-range view of the coming twelve months. Analyzes major planetary movements, retrogrades, and eclipse activity to help you notice the timing shaping your year.</p>
<button class="btn" onclick="openOrderDemo('The Year Ahead', '$45', 'A long-range twelve-month timing report for major transits, retrogrades, and eclipses.')">Select Report</button>
```

(Exact wording is Codex's/operator's call — the requirement is only that "progressions" not appear as an active method until Phase 5 lands and is validated.)

**Cross-check:** `marketing-site/index.html` — the *other* marketing site file — already describes Year Ahead correctly ("month by month, transit by transit, nothing smoothed over"), with no progressions claim. The two site files currently disagree with each other about what Year Ahead does. Worth confirming with the operator which site file is the live/canonical one, since only `entangled_oracle_SITE.html` needs the text fix, but it's also worth checking whether the two files are meant to stay in sync at all or whether one is stale.

**Owner:** Codex, per `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md` Phase 1 file ownership (marketing/site copy falls outside its explicitly listed ownership paths — confirm assignment with the operator before editing, since Phase 1's Codex ownership list names `generate.py`, `selectors/variable_resolver.py`, `engine/transit_engine.py`, and the daily/weekly/personal-forecast product paths, not the root-level site HTML files).

**Resolution (2026-07-07):** the operator explicitly assigned this fix outside the normal Phase 1 ownership split and asked Claude to apply it directly, since it's a two-line text change with zero pipeline risk. Applied exactly as suggested above — both `product-desc` copy and the `openOrderDemo()` button string now read "eclipse activity" / "eclipses" instead of "personal progressions" / "progressions." `marketing-site/index.html` required no change (already correct). No further action needed on this item.

## Swept and clean (no action needed)

- `README.md`, `METHODS.md`, `ARCHITECTURE.md`
- `products/shared/CLIENT_METHOD_AND_LIMITS.md`
- `products/shared/B2B_DEMO_AND_EARLY_RECIPIENT_PACKAGE.md`
- `products/shared/LOCAL_GENERATION_PROCEDURE.md`
- `products/shared/VERSIONING_POLICY.md`
- `products/shared/PRE_DELIVERY_QC_CHECKLIST.md`
- `products/shared/REPORT_PDF_WORKFLOW.md`
- `products/shared/CONTROLLED_FEEDBACK_INTAKE_TEMPLATE.md`
- `marketing-site/index.html`
- `marketing/facebook_page_assets_preview.md` and `.json`

No mentions found anywhere in this sweep of: Solar Arc, returns, profections, time lords, Zodiacal Releasing, or concrete "this will happen" event-prediction language. `CLIENT_METHOD_AND_LIMITS.md` in particular is carefully hedged throughout ("does not guarantee a fixed event or outcome").

Not in scope for this queue: `orders@entangledoracle.com — replies within 48 hours, guaranteed.` (`marketing-site/index.html`) is a customer-service SLA claim, not an astrological method claim, so it falls outside this audit's remit.
