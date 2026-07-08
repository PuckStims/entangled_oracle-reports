# Phase 3 Asteroid Policy Review

Date: 2026-07-07
Source: Phase 3 Claude registry-policy review per `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md` ("audit the all-34 asteroid registry for completeness, contradictions, and missing predictive policy")
Scope: `phase0/02_asteroid_predictive_registry.json` and `.md`, cross-checked against source-of-truth code
Status: complete — two structural issues already found and fixed in a prior pass (see `agents/REVISIONS.md`); this document is the full systematic sweep the Phase 3 Claude prompt calls for, confirming nothing further

## Method

Checked every one of the 34 asteroids against every field the Phase 3 prompt names: natal roles, topic keys, source eligibility, target eligibility, clock eligibility, allowed aspects, orb policy, weighting, confidence modifiers, report-surface permissions, and validation category. The registry is deliberately tier-inherited (`phase0/02_asteroid_predictive_registry.md`'s own stated design: "Every tier has a defensible default policy that per-asteroid entries may override") — so for the eight tier-inherited fields (source/target/clock eligibility, allowed aspects, orb policy, weighting default, confidence, report-surface permissions, validation category), the correct check is not "does every asteroid restate this field" but "does every asteroid have a valid tier assignment, and do all three tiers have complete defaults." Per-asteroid fields (name, ephemeris ID, tier, natal roles, topic keys, domain keys, proprietary index links, and any override) were checked individually against every entry.

## Findings already fixed (prior pass, referenced for completeness)

1. **Sirene and Themis source-eligibility overrides restructured** from free-text condition strings to `{allowed_aspects, restricted_targets}`. See `agents/REVISIONS.md` 2026-07-07 "Phase 3 asteroid registry review, before Codex implementation."
2. **`forecast_event_normalization_guidance` added** to `registry_metadata` — `method_variant` for `PROPRIETARY_TRANSIT` events was previously undocumented.
3. **Stale field-path reference corrected** — narrative doc pointed to a nonexistent `debug.asteroids_ephemeris_missing`; fixed to the real `asteroid_diagnostics.ephemeris_missing`.

Both files are now `phase0.1.1`.

## New checks performed this pass

### 1. `ephemeris_id` cross-check against `engine/natal_engine.py`'s `ASTEROID_DICTIONARY`

All 34 values checked individually against the source-of-truth Swiss Ephemeris ID table. **Zero transcription errors.** A wrong ID here would be the single most dangerous class of registry bug — it would silently make the registry describe the wrong physical body while the natal engine calculates the correct one, with no error thrown anywhere. Confirmed exact match for all 34:

Kassandra 10114, Aletheia 10259, Destinn 16583, Karma 13811, Kaali 14227, Medea 10212, Hermes 79230, Chaos 29521, Sirene 11009, Aphrodite 11388, Apollo 11862, Themis 10024, Mnemosyne 10057, Sophia 10251, Hekate 10100, Circe 10034, Arachne 10407, Anubis 11912, Lilith_Asteroid 11181, Moirai 10638, Terpsichore 10081, Atlantis 11198, Minerva 10093, Sappho 10080, Isis 10042, Melete 10056, Euterpe 10027, Urania 10030, Polyhymnia 10033, Industria 10389, Alma 10390, Child 14580, Angel 21911, DNA 65555.

### 2. Completeness and uniqueness of the 34-asteroid set

Every name in `ASTEROID_DICTIONARY` appears in the registry exactly once, across exactly one tier (8 anchor + 13 elevated + 13 contextual = 34). No duplicates, no omissions, no name mismatches (e.g. `Lilith_Asteroid` correctly distinguished from `Lilith_BML`, which correctly does not appear in this registry at all since it lives in `standard_planets`, not `custom_asteroids`).

### 3. `proprietary_index_links` cross-check against `formulas/governance_registry.py`'s `eo_uses` tuples

All 34 checked individually. **Exact match for all 34, with the dead legacy indexes (`MCQ`, `SIREN`, `MAGNETIC` — removed 2026-07-02 per `agents/REVISIONS.md`'s "Asteroid Portrait removed" entry) correctly excluded everywhere they'd otherwise appear:** Sirene, Aphrodite, Apollo, Themis, and Moirai all had one or more dead-index references in the original governance tuples, and the registry correctly omits every one of them. Moirai's `natal_roles` even explicitly documents this with a `"legacy_mcq_dead"` tag rather than silently dropping the reference — good practice, worth noting as a model for any future similar exclusion.

### 4. Per-asteroid required-field presence

All 34 entries have non-empty `asteroid_name`, `ephemeris_id`, `tier`, `natal_roles`, `topic_keys`, `domain_keys`, and a `proprietary_index_links` array (empty array is valid where no index links exist — 15 of 34 asteroids legitimately have none). No missing required fields anywhere.

### 5. Override-field consistency check (are there other asteroids that should have an override but don't?)

Searched every asteroid's `notes` field for language implying an existing, narrower code pathway that isn't yet reflected in a `source_eligibility_override`. Only Sirene and Themis have `notes` referencing a specific existing pathway (both already fixed in the prior pass). No other elevated- or contextual-tier asteroid's notes imply an unaddressed narrow eligibility case. The 8 anchor-tier asteroids' `existing_scaffolding` blocks are complete 1:1 mappings to `engine/transit_engine.py`'s `PROPRIETARY_FORMULA_CONFIG` triggers (cross-checked against the `migration_map` section, which independently documents the same 12 triggers) — no anchor-tier asteroid has scaffolding information missing from its entry.

### 6. Tier default completeness

All three tiers (`anchor`, `elevated`, `contextual`) have complete values for every field an asteroid entry might need to inherit: `target_eligibility` (8 clock types each), `source_eligibility` (6 clock types each), `allowed_aspects_by_clock`, `orb_policy_by_clock`, `weight_policy_default`, `house_relevance_multiplier_cadent`, `angle_relevance_bonus`, `rulership_participation`, `transit_speed_source_constraints`, `confidence_method_maturity_default`, `report_surface_permissions`, `validation_category`. No tier has a gap that would leave an inheriting asteroid without a value for any of these.

## Contradictions checked for and not found

- No asteroid appears in two tiers.
- No asteroid's per-entry override contradicts its tier default in a way that would be ambiguous to a policy API (both existing overrides *narrow* the tier default, they don't loosen or contradict it).
- No asteroid's `proprietary_index_links` references an index that doesn't exist in the currently active proprietary index set (`KVQ`, `MKI`, `RWI`, `DFIS`, `CATALYST`, `AHL`, `NGE` — cross-checked against `config.py`'s `INDEX_DIMENSION_NAMES`).
- `migration_map`'s 12 documented triggers and the anchor tier's 8 asteroids' `existing_scaffolding` blocks are mutually consistent — every trigger referencing an asteroid is reflected in that asteroid's own entry, and vice versa.

## Verdict

No further registry changes needed before Codex begins Phase 3 implementation. The two structural fixes from the prior pass were the real gaps; this exhaustive sweep found nothing additional. The registry is internally consistent, matches its source-of-truth code (natal engine ephemeris IDs, governance registry index links) exactly, and every asteroid has complete, unambiguous policy coverage either through tier inheritance or an explicit, now-structured override.
