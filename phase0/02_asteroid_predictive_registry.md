# Phase 0 — Asteroid Predictive Registry (Narrative)

Program: [EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md](../EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md)
Machine-readable companion: [02_asteroid_predictive_registry.json](./02_asteroid_predictive_registry.json)
Status: charter (Phase 0, operator-approved). Policy. No implementation.
Version: `phase0.1.1`
Date: 2026-07-07 (patched same day, before Phase 3 implementation began, per Phase 3 Claude registry review: structured the Sirene/Themis source-eligibility overrides and fixed a field-path reference — see `phase0.1.0` → `phase0.1.1` diff in `agents/REVISIONS.md`)

## Purpose

Give every one of the 34 EO asteroids an explicit, versioned predictive policy. From the program's locked rule set: **"No asteroid may disappear merely because a scanner, serializer, target list, or template forgot that `custom_asteroids` exists."** This document is that guarantee.

## Governing rules

1. **First-class ≠ identical.** Each asteroid may carry its own eligibility, orb, weight, aspect policy, source vs. target behavior, clock coverage, and topic mapping. Differences are policy, never accidental exclusion.
2. **Explicit exclusion is fine.** An asteroid may be excluded from a given clock — but the exclusion must be declared here, dated, and reasoned. Silent exclusion is prohibited.
3. **Every asteroid gets at least one active clock family.** Even the most contextual asteroids are natal-target-eligible under `transit_family`.
4. **The eight already-scaffolded asteroids are the initial anchor tier.** Their behavior in the existing `scan_proprietary_forecast_windows` scanner is preserved as the migration baseline. New behavior extends, never contradicts, that baseline.
5. **Governance visibility is inherited.** The governance registry restricts asteroid material to `soul_ecosystem` and `predictive_sandbox`. This registry does not override that policy — it operates *within* it. Phase 10 alone may reconsider consumer-report visibility, per the program.

## Tier structure

Three tiers, chosen by declared archetypal role, current index participation, and existing scaffolding. Every tier has a defensible default policy that per-asteroid entries may override in either direction.

### Anchor tier (8 asteroids)

Asteroids with existing scaffolded predictive roles, driver-level participation in ≥1 proprietary index, and a distinct, well-defined archetypal function.

Members: **Kassandra, Aletheia, Destinn, Karma, Kaali, Medea, Hermes, Chaos.**

Default policy:

- **Target eligibility:** yes across all clock families (transit, return, progression, solar_arc, lunation, eclipse, profection-anchor, ZR-anchor).
- **Source eligibility:** yes for `transit` and `solar_arc` (as directed source). No for `progression` in Phase 5 launch (asteroid progressions are noisy at inner-scale). Return-source is meaningless for asteroids (they don't have "returns" in the ordinary sense — they conjoin their natal position slowly, but with orb sizing that makes it less useful than for the Sun/Moon/Jupiter/Saturn).
- **Allowed aspects:** all major (`Conjunction`, `Sextile`, `Square`, `Trine`, `Opposition`) for transit. `Conjunction` only for progression/solar_arc/lunation/eclipse contacts at Phase 4/5/6 launch; may widen with fixture support.
- **Orb by clock:** transit `2.0°`, solar_arc `1.0°`, progression `0.5°`, lunation/eclipse `1.5°`, return `n/a`.
- **Relevance weight:** matches `_TARGET_RELEVANCE` in `engine/predictive_engine.py` — Kassandra 0.85, Aletheia 0.80, Destinn 0.80, Karma 0.80, Kaali 0.75, Medea 0.75, Hermes 0.70, Chaos 0.70.
- **Report surface:** `[internal_rd, predictive_sandbox, soul_ecosystem]` by default.
- **Validation category:** `primary_asteroid`.

### Elevated tier (13 asteroids)

Asteroids with active index participation (indexes named alongside their record in `governance_registry.py`), well-defined archetypal function, and asteroids whose absence from the predictive layer would materially degrade an already-shipped natal reading.

Members: **Sirene, Aphrodite, Apollo, Themis, Mnemosyne, Sophia, Hekate, Circe, Arachne, Anubis, Lilith_Asteroid, Moirai, Terpsichore.**

Default policy:

- **Target eligibility:** yes for `transit`, `return`, `lunation`, `eclipse`, `profection-anchor`, `ZR-anchor`. Deferred for `progression` and `solar_arc` at Phase 5 launch — may be promoted per-asteroid after validation cycles.
- **Source eligibility:** conjunction-only transit source *when* the asteroid is explicitly named in an index-driver role (Apollo → RWI, Themis → RWI, Sirene → NGE, etc.). Otherwise no source eligibility. This means most elevated asteroids appear as targets, not as transit sources, matching the mainstream astrological convention that asteroids-as-transit-sources are used sparingly. Where an asteroid's source eligibility is narrower than "any target" (currently Sirene and Themis), the machine-readable registry's `source_eligibility_override.transit` carries a structured `{allowed_aspects, restricted_targets}` shape rather than a free-text condition — the policy API should treat `restricted_targets` as the authoritative eligibility list, not attempt to parse a description.
- **Allowed aspects:** `Conjunction`, `Square`, `Opposition` (hard aspects) for transit at Phase 2 launch. `Conjunction` only for lunation/eclipse. Flowing aspects (`Trine`, `Sextile`) deferred to a later revision.
- **Orb by clock:** transit `1.5°`, lunation/eclipse `1.5°`, return `n/a`.
- **Relevance weight:** `0.65` for all elevated by default; may be tuned per asteroid based on index-driver participation.
- **Report surface:** `[internal_rd, predictive_sandbox, soul_ecosystem]`.
- **Validation category:** `elevated_asteroid`.

### Contextual tier (13 asteroids)

Asteroids whose archetypal function is contextual — they nuance a natal reading but do not drive independent forecast conclusions today. This is deliberately conservative for Phase 2. Any of these may be promoted to elevated tier when a fixture demonstrates it earns the promotion.

Members: **Atlantis, Minerva, Sappho, Isis, Melete, Euterpe, Urania, Polyhymnia, Industria, Alma, Child, Angel, DNA.**

Default policy:

- **Target eligibility:** yes for `transit` and `return`. `lunation` and `eclipse` are conditional — only when the asteroid falls within `1.0°` of the exact lunation/eclipse point AND participates in a proprietary index for the querent's chart. Not eligible for `progression`, `solar_arc`, `profection-anchor`, or `ZR-anchor` in Phase 2/4/5/6.
- **Source eligibility:** no.
- **Allowed aspects:** `Conjunction` only.
- **Orb by clock:** transit `1.0°`, lunation/eclipse `1.0°`, return `n/a`.
- **Relevance weight:** `0.55` by default.
- **Report surface:** `[internal_rd, predictive_sandbox, soul_ecosystem]`.
- **Validation category:** `contextual_asteroid`.

## Cross-tier rules

- **House-relevance policy.** All asteroids inherit whole-sign house placement from the natal payload. House placement contributes to `signal.target_relevance` when a transit forms an aspect to the asteroid *while the asteroid occupies an angular (1/4/7/10) or succedent (2/5/8/11) house* — cadent-house asteroids receive a `0.85×` relevance multiplier. This is uniform across tiers.
- **Angle-relevance policy.** An asteroid within `2°` of any natal angle (ASC, MC, DSC, IC, Vertex) receives a `1.15×` relevance bonus. This is uniform across tiers.
- **Rulership / dispositor policy.** Asteroids do not participate in classical or modern rulership chains. They do not disposit planets. Dispositor chain analysis skips them. This is explicit and uniform.
- **Transit-speed / source constraints.** When an asteroid is source-eligible, transit-source events use the asteroid's actual daily motion at the transit moment. Retrograde asteroid contacts are permitted; multi-pass cycles are handled by the shared cycle-merging logic in the transit engine. **No orb widening is granted for asteroid retrogrades** because their daily motion is small and the cycle merger already collapses same-contact windows within 120 days.
- **Confidence modifiers.** Every asteroid contact carries a `method_maturity` component of `0.75` at Phase 2 launch (asteroids as forecast participants are a newer capability than transits to planets). This may be revised upward per asteroid after fixture-supported validation.
- **Report-surface visibility.** All 34 asteroids share the same default `[internal_rd, predictive_sandbox, soul_ecosystem]` visibility. Governance registry policy is authoritative for consumer-facing report surfaces.
- **Ephemeris resilience.** When an asteroid's ephemeris file is unavailable and its natal position is stored as a string error (`"Calculation failed: ..."` in `custom_asteroids`), the registry classifies it as `ephemeris_missing` and no forecast events are emitted for it. This must appear in the sidecar's `asteroid_diagnostics.ephemeris_missing` list (`phase0/06_sidecar_and_export_contract.md` §2.15 — corrected here from an earlier draft that referenced a nonexistent `debug.asteroids_ephemeris_missing` path; Codex's live Phase 2 sidecar writer already implements the correct path and was used to confirm it, including a real observed case where `Anubis`'s ephemeris file was unavailable in the local environment). A per-chart ephemeris failure is not a "silent disappearance" violation of this registry's own rule — the asteroid is declared and its absence for that specific chart is explicit and traceable, not scanner oversight.

## Per-asteroid rationale (34 records)

Below, each asteroid gets one paragraph justifying its tier, its topic keys, and any per-asteroid override. The machine-readable JSON companion carries the exact field values; this narrative explains the *why*.

### Anchor tier

**Kassandra (10114).** Already the primary driver of KVQ. Its archetype — unheeded truth, warning under doubt — is a specific enough natal focus that transit contacts to it produce a distinct predictive signal from generic transit-to-luminary contacts. Source eligibility retained per the existing `scan_proprietary_forecast_windows` triggers (Chaos-Kassandra, Hermes-Kassandra) and extended to `solar_arc` because a directed Kassandra to a natal angle is a recognized predictive marker in the KVQ literature. Topic keys: `truth_under_doubt`, `warning`, `insight_validation`, `disclosure`. Domain keys: `communication`, `meaning`.

**Aletheia (10259).** Truth as unconcealment (Heideggerian sense, but the asteroid was named for the Greek personification centuries earlier). Aletheia's transit-to-Sun trigger already appears in the DISRUPTION formula group. Anchor tier because truth-revelation is a specific event class that Aletheia distinctly represents; other asteroids nuance it, none replace it. Source-eligible for transit and solar_arc. Topic keys: `truth`, `unconcealment`, `disclosure`. Domain keys: `meaning`, `identity`.

**Destinn (16583).** Destined encounter, catalytic other. Already drives CATALYST index alongside Karma. Anchor tier because the Destinn-Vertex-DSC-Sun natal axis is a distinct EO predictive substrate. Source eligibility retained per existing Destinn→DSC trigger; extended to `solar_arc` for directed Destinn-to-natal-anchor contacts. Topic keys: `destined_encounter`, `catalyst`, `threshold_person`. Domain keys: `partnership`, `transformation`, `vocation`.

**Karma (13811).** Karmic thread, cause-effect debt. Drives CATALYST. Source eligibility retained per existing Karma→DSC trigger. Topic keys: `karmic_thread`, `cause_effect`, `obligation`. Domain keys: `partnership`, `transformation`.

**Kaali (14227).** Fierce protection, destruction of illusion. Drives DFIS. Source-eligible per existing Kaali→Mars trigger; extended to `solar_arc` because directed Kaali to natal Mars, Sun, or an angle is a recognized fierce-clarification marker. Topic keys: `fierce_protection`, `destruction_of_illusion`, `war_against_falsehood`. Domain keys: `identity`, `transformation`, `work`.

**Medea (10212).** Sacrifice, ruthless devotion, cost of love. Drives DFIS. Source-eligible per existing Medea→Mars trigger. Topic keys: `sacrifice`, `ruthless_devotion`, `cost_of_love`. Domain keys: `transformation`, `partnership`.

**Hermes (79230).** Messenger, translator, boundary-crosser. Drives MKI, RWI, CATALYST (three indexes — the most cross-index participation of any asteroid). Source-eligible per existing Hermes→Kassandra trigger, extended to include Hermes as a transit-source to any anchor asteroid or angle. Topic keys: `message`, `translation`, `boundary_crossing`. Domain keys: `communication`, `transformation`.

**Chaos (29521).** Primordial rupture, generative void. Drives RWI. Source-eligible per existing Chaos→Kassandra trigger. Topic keys: `rupture`, `generative_void`, `primal_reorganization`. Domain keys: `transformation`, `identity`.

### Elevated tier

**Sirene (11009).** Attraction, voice, allure. Drives NGE. Elevated because voice/attraction/allure is a distinct EO narrative substrate but transit contacts to Sirene are more contextual than event-generating on their own. Source-eligible for transit conjunction-only (Sirene aspecting a natal angle or Venus is a genuine timing marker). Topic keys: `voice`, `attraction`, `allure`. Domain keys: `creativity`, `partnership`.

**Aphrodite (11388).** Desire, aesthetic love, harmony. Drives NGE. Elevated with default policy. Topic keys: `desire`, `aesthetic`, `harmony`. Domain keys: `partnership`, `creativity`.

**Apollo (11862).** Clarity, oracle, radiance, prophecy. Drives RWI, NGE. Elevated because Apollonian clarity is distinct from Kassandran warning — they can co-occur but represent different topic axes. Topic keys: `clarity`, `oracle`, `radiance`, `prophecy`. Domain keys: `meaning`, `creativity`, `vocation`.

**Themis (10024).** Natural law, right order, oath. Drives RWI, NGE. Elevated. Themis participates in `proprietary_indexes.py` at line 919 in a Themis→Destinn aspect calculation for CATALYST, meaning it is *already* source-active for that specific pathway; registry preserves that. Topic keys: `natural_law`, `right_order`, `oath`. Domain keys: `partnership`, `work`, `meaning`.

**Mnemosyne (10057).** Memory, remembrance, ancestral thread. Drives MKI. Elevated because memory-as-topic is central to MKI's ancestral-thread readings. Topic keys: `memory`, `remembrance`, `ancestral_thread`. Domain keys: `home`, `meaning`, `spirit`.

**Sophia (10251).** Wisdom, gnosis, deep knowing. Drives MKI. Elevated. Topic keys: `wisdom`, `gnosis`, `deep_knowing`. Domain keys: `meaning`, `spirit`.

**Hekate (10100).** Crossroads, threshold, keys, night wisdom. Drives DFIS. Elevated because threshold-marking is a specific and distinct timing role. Topic keys: `crossroads`, `threshold`, `keys`, `night_wisdom`. Domain keys: `transformation`, `spirit`.

**Circe (10034).** Transformation, enchantment, potion. Drives DFIS. Elevated. Topic keys: `transformation`, `enchantment`, `potion`. Domain keys: `transformation`, `creativity`.

**Arachne (10407).** Pattern-weaving, hubris, structural construction. Drives RWI. Elevated. Topic keys: `pattern_weaving`, `hubris`, `structural_construction`. Domain keys: `work`, `creativity`.

**Anubis (11912).** Psychopomp, weighing, transition. Drives AHL. Elevated because Anubis's role at transitions (deaths, endings, integrations) is a specific event class. Topic keys: `psychopomp`, `weighing`, `transition`. Domain keys: `transformation`, `spirit`.

**Lilith_Asteroid (11181).** Refusal, exile-return, unbound self. No proprietary index link (deliberately distinct from Black Moon Lilith which is in `standard_planets`). Elevated because the refusal-topic is specific enough that transits to natal Asteroid Lilith deserve a first-class predictive path. **Explicit reminder:** never conflate with `Lilith_BML`. Topic keys: `refusal`, `exile_return`, `unbound_self`. Domain keys: `identity`, `transformation`, `partnership`.

**Moirai (10638).** Fate, thread, allotment. Drives NGE (also legacy MCQ, dead). Elevated. Topic keys: `fate`, `thread`, `allotment`. Domain keys: `transformation`, `meaning`.

**Terpsichore (10081).** Dance, rhythm, movement. Drives NGE. Elevated because rhythm-as-topic serves NGE's narrative-gravity readings. Topic keys: `dance`, `rhythm`, `movement`. Domain keys: `creativity`, `community`.

### Contextual tier

**Atlantis (11198).** Submerged knowledge, lost pattern, hidden lineage. Drives MKI. Contextual because Atlantis nuances MKI readings but does not by itself generate distinct predictive claims that other MKI drivers wouldn't. Topic keys: `submerged_knowledge`, `lost_pattern`, `hidden_lineage`. Domain keys: `meaning`, `spirit`, `transformation`.

**Minerva (10093).** Strategy, craft, tactical wisdom. No active index link. Contextual. Topic keys: `strategy`, `craft`, `tactical_wisdom`. Domain keys: `vocation`, `work`.

**Sappho (10080).** Intimate lyric, eros, tender expression. No active index link. Contextual. Topic keys: `intimate_lyric`, `eros`, `tender_expression`. Domain keys: `partnership`, `creativity`.

**Isis (10042).** Restoration, magical sovereignty, gathering. No active index link. Contextual. Topic keys: `restoration`, `magical_sovereignty`, `gathering`. Domain keys: `home`, `transformation`, `spirit`.

**Melete (10056).** Practice, rehearsal, meditation. No active index link. Contextual. Topic keys: `practice`, `rehearsal`, `meditation`. Domain keys: `work`.

**Euterpe (10027).** Lyric, melody, delight. No active index link. Contextual. Topic keys: `lyric`, `melody`, `delight`. Domain keys: `creativity`.

**Urania (10030).** Celestial mapping, cosmology, big picture. No active index link. Contextual. Topic keys: `celestial_mapping`, `cosmology`, `big_picture`. Domain keys: `meaning`, `spirit`.

**Polyhymnia (10033).** Sacred song, silent prayer. No active index link. Contextual. Topic keys: `sacred_song`, `silent_prayer`. Domain keys: `spirit`, `creativity`.

**Industria (10389).** Labor, sustained effort, industry. No active index link. Contextual. Topic keys: `labor`, `sustained_effort`, `industry`. Domain keys: `work`, `resources`.

**Alma (10390).** Soul, essence, animating spark. No active index link. Contextual — despite the evocative name, contextual because "soul" as a predictive topic is too broad without accompanying evidence; Alma's role is to nuance other soul-related evidence, not to drive it. Topic keys: `soul`, `essence`, `animating_spark`. Domain keys: `identity`, `spirit`.

**Child (14580).** Innocence, inner child, becoming. Drives AHL. Contextual. Topic keys: `innocence`, `inner_child`, `becoming`. Domain keys: `home`, `creativity`.

**Angel (21911).** Grace, luminous aid, guardianship. No active index link. Contextual. Topic keys: `grace`, `luminous_aid`, `guardianship`. Domain keys: `spirit`, `home`.

**DNA (65555).** Inheritance, essential code, lineage. Drives AHL. Contextual. Topic keys: `inheritance`, `essential_code`, `lineage`. Domain keys: `home`, `identity`.

## Migration path from current engine state

- **B1 (per program):** wire `scan_proprietary_forecast_windows()` into the predictive stream under an R&D feature flag. That scanner's existing 8-asteroid target set matches the anchor tier exactly. No behavior change at wire-up time.
- **B2:** move the `PROPRIETARY_ASTEROID_TARGETS` list and `PROPRIETARY_FORMULA_CONFIG` in `engine/transit_engine.py:859-932` into a load-from-registry function that reads `02_asteroid_predictive_registry.json`. Preserve exact current behavior during the migration.
- **B3:** expand `_natal_targets()` (or introduce a new resolver) to include all 34 asteroids as targets, honoring per-asteroid clock eligibility.
- **B4:** extend `ECLIPSE_TARGET_KEYS` and the lunation target-eligibility filter to accept asteroids whose registry entry permits it.

## Promotion path

An asteroid may move between tiers only with:

1. A dated operator note in `agents/REVISIONS.md`.
2. At least one regression fixture demonstrating the new tier's behavior.
3. A revised version string in the machine-readable registry (`policy_version` bump).
4. Historical sidecar records preserving the prior policy version so old candidates remain reproducible against their original policy.

## What Phase 0 does not decide

- Whether any asteroid appears in Year Ahead, Personal Forecast, or Daily Horoscope prose. That is Phase 10.
- Exact narrative prose per asteroid activation. That is downstream of the block library.
- Weight tuning beyond the tier defaults. That is a validation-driven decision after Phase 9.
