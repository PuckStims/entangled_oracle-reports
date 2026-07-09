# Next Upgrade Outline

This outline tracks wiring up the new **Year Ahead Texture** events (Progressions & Solar Arcs) and addressing the quarantined "mad-libs" style prose files.

> **Framing note:** "plainspeak" phrasing and anti-monotony/variant-tracking are core product features, not add-on polish — see section 4 for why this matters and what's next.

## 1. Content Block Creation (Progressions & Solar Arcs) — DONE (scaffolded)
Four new JSON files exist and are wired into `config.py`/`generate.py`/the template. Every file has the full key structure (source planet -> aspect -> natal_target, with a `fallback` at every level) but **every leaf value is still the literal string `"TODO"`** — no real prose has been written yet. That's the only remaining step here.

- `blocks/entangled_oracle/EO_Standard_Progression_Blocks.json` (378 leaf placeholders)
- `blocks/plainspeak/progression_blocks.json` (378 leaf placeholders)
- `blocks/entangled_oracle/EO_Standard_Solar_Arc_Blocks.json` (439 leaf placeholders)
- `blocks/plainspeak/solar_arc_blocks.json` (439 leaf placeholders)

Sources: progressions use Sun/Mercury/Venus/Mars/Ascendant/Midheaven (progressed Moon is modifier-scope and stays with Personal Forecast); solar arc adds Moon since it has no modifier tier. Targets: the 10 classical bodies + ASC/MC (asteroids and IC/DSC/Vertex fall through to `fallback`). Plainspeak and entangled_oracle copies are currently identical, matching the existing precedent (house_ingress/station files are also pack-identical today).

**Still open:** write the actual prose to replace the `"TODO"` placeholders, at whatever pace/priority makes sense (doesn't have to be all 378/439 blocks before shipping — `select_block_from_path` gracefully falls back at each level, so partial coverage degrades to `fallback` text rather than breaking).

## 2. Prose Rewrite (Quarantined Files) — DONE
These files were quarantined into `blocks/TODO/` due to highly repetitive, mad-libs style prose: `predictive_chapters.json`, `transit_blocks.json`/`EO_standard_transit_blocks_working.json`, `year_overview.json`/`EO_Standard_Year_Overview_Blocks.json`, `year_integration.json`/`EO_Standard_Year_Integration_Blocks.json`, `eclipse_blocks.json`/`EO_Standard_Eclipse_Blocks.json`.

The rewrite was done locally (not on a branch — local files are the source of truth here, not git state) and now lives entirely under `blocks/plainspeak/`:
- `EO_standard_transit_blocks.json` — **single file, shared by both packs.** There is no separate entangled_oracle transit file anymore; both packs route through this one (see `config.py` below).
- `eclipse_blocks.json` / `EO_Standard_Eclipse_Blocks.json` — genuinely different content per pack (diffed, not a duplicate), both now filed under `plainspeak/`.
- `year_overview.json` / `EO_Standard_Year_Overview_Blocks.json` — same: different content, same folder now.
- `year_integration.json` / `EO_Standard_Year_Integration_Blocks.json` — same.
- `predictive_chapters.json` — rewritten and copied in, but **not wired into `CONTENT_PACKS` at all** (wasn't before either — no consumer currently calls it).

`blocks/entangled_oracle/` no longer holds any of these five categories at all — what's left there is `EO_Standard_Forecast_Climate_Blocks.json`, `EO_Standard_House_Ingress.json`, `EO_Standard_Monthly_Snapshot_Blocks.json`, `EO_Standard_Station_Blocks_Revised.json`, plus the three `EO_Year_Ahead_*` files (archetypal opening, convergence, refraction bridges).

`blocks/TODO/` still has the old pre-rewrite originals (`transit_blocks.json`, `EO_standard_transit_blocks_working.json`) plus leftover analysis tooling (`analyze.py`, `phase1_split.py`, `baseline_schema.json`, `chunks/`) — nothing currently reads these, they're just not deleted yet. See section 4.

## 3. Core Wiring Updates — DONE

### `config.py`
- `CONTENT_PACKS` now has `year_texture_progressions` and `year_texture_solar_arc` keys in both `plainspeak` and `entangled_oracle` packs, pointing at the files from section 1.
- Fixed a real, pre-existing bug found while wiring in the section 2 rewrite: the quarantine move never updated `config.py`, so both packs' `transits`/`eclipses`/`year_overview`/`year_integration` paths pointed at files that no longer existed (they'd been moved to `blocks/TODO/`) — meaning those categories were silently falling back to generic fallback text. All four now point at the rewritten files under `blocks/plainspeak/` (see section 2), and `transits` is the same path for both packs (single shared file, no entangled_oracle-specific transit content anymore).
- Confirmed via `tests/test_eclipse_house_fix.py`: 2 tests that were failing before this fix (`test_eo_eclipse_file_has_10th_house_block`, `test_eo_eclipse_10th_differs_from_6th`) now pass — that test file was silently exercising the broken path.

### `generate.py`
- `_select_year_block` gained `progression`/`solar_arc` branches that call `select_block_from_path(pack_paths["year_texture_progressions"|"year_texture_solar_arc"], transit_planet, aspect, natal_target)`.
- `_format_timeline_event` gained title/subtitle/event_label branches for both event types ("Progressed {planet} {aspect} natal {target}" / "{planet} solar arc {aspect} natal {target}").
- `_build_year_ahead_context` now runs `year_texture_progressions`/`year_texture_solar_arc` through `_format_timeline_event` before they land in the template context (they're never folded into `all_events`/`months` — progressions and solar arc run on their own ~60-90 day "chapter" clock, separate from the monthly cadence).
- **Engine-side fix required to make this work:** `engine/progressions.py` and `engine/solar_arc.py` event builders didn't set `peak_date`/`entry_date`/`leave_date`/`natal_target_display` (every other event family — transits, ingresses, stations, eclipses — already does). Without those, `date_label` and the "why this matters" plumbing came up blank. Both builders now set these fields the same way `engine/transit_engine.py` does.

### HTML Template (`products/year_ahead/templates/active/year_ahead.html`)
Note: the outline originally said `templates/year_ahead.html`; the real path is `templates/active/year_ahead.html` (there's also a `templates/legacy/` copy that isn't live). Added a "Progressions & Solar Arc Texture" subsection inside section VII (Year Arcs) rather than a new top-level numbered section, so the existing table-of-contents roman-numeral anchors didn't need renumbering. Reuses the existing `.arc-story` card styling; loops separately over `year_texture_progressions` and `year_texture_solar_arc`, rendering title, date, subtitle, and block prose (currently the `"TODO"` placeholder text).

Verified via a direct `_build_year_ahead_context` + `render_template` smoke test with a full synthetic natal payload: progression/solar arc cards render with correct titles, dates, and placeholder prose, no Jinja errors, both content packs, no `MISSING BLOCK FILE`/`BLOCK NOT FOUND` anywhere in output. Full test suite passes except pre-existing, unrelated failures (missing `seas_18.se1` ephemeris asset in this environment).

## 4. Next Technical Overhaul: Content Pack Consolidation — not started

Important context for whoever picks this up: **there is no real "content pack" system today.** The `EO_`/`Standard_` naming in these files exists because the early prose rewrites were unstructured, not because `plainspeak` and `entangled_oracle` were ever designed as genuinely distinct product tiers. Section 2 above is a live example of the current mess: transit content is now a single shared file, while eclipse/year_overview/year_integration are still two separate files with different prose per pack, and progression/solar-arc (section 1) are pack-identical placeholders — three different patterns for the same conceptual thing, sitting next to each other in the same `CONTENT_PACKS` dict.

The planned next overhaul, in order:
1. **Abolish the varied content-block pathways.** Pick one consistent pattern (shared file vs. per-pack file vs. per-pack directory) and migrate everything to it — no more mix of `blocks/plainspeak/`, `blocks/entangled_oracle/`, and `blocks/shared/` holding arbitrary, inconsistent subsets of content.
2. **Delete every unused content block.** Concrete candidates already sitting around: everything left in `blocks/TODO/` (old pre-rewrite originals + `analyze.py`/`phase1_split.py`/`baseline_schema.json`/`chunks/` tooling — see section 2), and likely other dead files elsewhere in `products/*/blocks/` accumulated the same way across other report types (personal_forecast, soul_ecosystem, identity_profile).
3. **Only then** build actual intentional content packs — e.g. neo-pagan-focused, business-specific white-label collabs, mythic/archetypal prose, etc. — as real differentiated products, not just naming residue.

**Framing this correctly matters:** the "plainspeak" phrasing and the anti-monotony/variant-tracking guidelines already in the engine (`_VariantTracker`, refraction bridges, convergence dedup) aren't polish layered on top — they're the core long-term differentiator that's supposed to let Entangled Oracle produce meaningfully better prose than B2B astrology-software competitors without those competitors' premium markup. Don't treat prose-quality/anti-repetition work as an add-on to deprioritize; it's the actual roadmap, and the pack-consolidation work above exists to clear space for it.
