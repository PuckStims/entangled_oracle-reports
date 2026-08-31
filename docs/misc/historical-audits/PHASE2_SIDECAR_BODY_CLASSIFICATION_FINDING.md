# Phase 2 Sidecar Body Classification Finding

Date: 2026-07-07
Source: Phase 2 contract-conformance review per `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md` (Claude Code lane)
Scope: `engine/predictive_sidecar.py` — the Phase 2 `.eo_predictive.json` sidecar writer
Status: open — one item, verified live, not just theoretical

## Item 1: `_body_kind()` silently misclassifies unrecognized bodies as `"asteroid"`, currently corrupting eclipse asteroid diagnostics and dormant-but-guaranteed to misfire on `Lilith_BML`

**File:** `engine/predictive_sidecar.py`
**Function:** `_body_kind(body: str) -> str` (and its callers `_is_asteroid_participant`, `_asteroid_participants`, `_target_kind`)

```python
def _body_kind(body: str) -> str:
    if not body:
        return "planet"
    if body in _LUMINARIES:
        return "luminary"
    if body in _PLANETS:
        return "planet"
    if body in _NODES:
        return "node"
    if body in _ANGLE_TARGETS:
        return "angle"
    return "asteroid"   # <- fallback for anything unrecognized
```

`_LUMINARIES`, `_PLANETS`, `_NODES`, `_ANGLE_TARGETS` are hardcoded frozensets. Anything not in one of those four sets — including bodies that are neither planets nor asteroids at all — falls through to `"asteroid"`.

### Manifestation 1 (confirmed live, currently active): eclipse events

`engine/transit_engine.py:2101` (pre-existing code, unrelated to Phase 1/2 work, part of the long-standing production eclipse scanner) sets:

```python
"transit_planet": eclipse_type,   # eclipse_type is the string "Solar" or "Lunar"
```

This is correct and intentional for `scan_eclipses()`'s own purposes — `eclipse_type` is a label ("Solar Eclipse" vs "Lunar Eclipse") used by existing content-pack block routing, not a claim that the transiting body's name is literally "Solar" or "Lunar". Nothing downstream had ever tried to classify `transit_planet` as an actual celestial body before — `predictive_sidecar.py` is the first code to do that, and it exposed the mismatch.

**Verified live** by generating an actual Year Ahead report and inspecting the resulting sidecar:

```json
{"event_id": "fe_luna_a5ab8c88", "method_family": "LUNATION", "method_variant": "ECLIPSE",
 "source_body": "Solar", "source_kind": "asteroid", "asteroid_participants": ["Solar"], ...}
{"event_id": "fe_luna_fa043c24", "method_family": "LUNATION", "method_variant": "ECLIPSE",
 "source_body": "Lunar", "source_kind": "asteroid", "asteroid_participants": ["Lunar"], ...}
```

Each such event also carries `strength_components.asteroid_specificity: 1.0` (the maximum score, since `_is_asteroid_participant()` returned `True`).

**Measured impact on that one report:** `asteroid_diagnostics.asteroid_events_count` reported `8`. Of those 8, **4 were eclipse events, not asteroid events** — exactly half the reported "asteroid participation" in that run's diagnostics was eclipses being counted as if `"Solar"` and `"Lunar"` were asteroid names. `asteroids_active_as_source` and `asteroids_active_as_target` are unaffected (they cross-reference the real `custom_asteroids` key list, not `_body_kind()`), so those two fields are trustworthy — but `asteroid_events_count`, `asteroid_signals_count`, and every event/signal's own `asteroid_participants` and `asteroid_specificity` are corrupted whenever an eclipse is present in the report window, which is common (most report windows a year or more long contain at least one eclipse).

### Manifestation 2 (confirmed dormant, not yet live): `Lilith_BML`

`Lilith_BML` (Black Moon Lilith, the mean lunar apogee) lives in `payload["standard_planets"]` (`engine/natal_engine.py:551`) and is explicitly, deliberately distinct from `Lilith_Asteroid` (physical asteroid 11181, in `custom_asteroids`) — this distinction is called out directly in the codebase itself (`formulas/proprietary_indexes.py:639`: *"Black Moon Lilith is intentionally distinct from asteroid Lilith"*; `formulas/governance_registry.py`: *"not interchangeable with asteroid Lilith"*).

`Lilith_BML` is absent from all four of `predictive_sidecar.py`'s classification sets (`_LUMINARIES`, `_PLANETS`, `_NODES`, `_ANGLE_TARGETS`), so `_body_kind("Lilith_BML")` would return `"asteroid"` — misclassifying a proprietary-formula-relevant point (BML drives the SOVEREIGNTY forecast formula group per `engine/transit_engine.py`'s `PROPRIETARY_FORMULA_CONFIG`) as if it were the unrelated physical asteroid.

**Confirmed not yet live:** current transit scanners (`TRANSIT_PLANETS`, `STANDARD_TARGETS` in `engine/transit_engine.py`) never emit `Lilith_BML` as a source or target, and `scan_proprietary_forecast_windows()` — the scanner that does use `Lilith_BML` as a source (`SOVEREIGNTY` formula group, BML → ASC/MC/DSC/IC) — is not wired into Phase 2's signal stream (confirmed in the live sidecar's own `provenance.scanner_versions.scan_proprietary_forecast_windows: "not_wired_phase2"`). This bug is real but currently inert. It will start firing the moment that scanner is wired (Phase 2/3's own B1 milestone per `phase0/02_asteroid_predictive_registry.md`), so it's worth fixing now rather than rediscovering it under time pressure later.

## Recommended fix

Rather than patching two special cases (`"Solar"`/`"Lunar"` eclipse labels, `Lilith_BML`), make `_body_kind()` authoritative instead of exclusion-based. `_asteroid_diagnostics()` already computes `present = sorted(payload["custom_asteroids"].keys())` two functions over in the same file — the real, ground-truth list of this chart's actual asteroid names is already available. Passing that set (or the full `payload`) into `_body_kind()` and checking membership there directly — rather than "anything not planet/luminary/node/angle must be an asteroid" — would:

1. Fix the eclipse `"Solar"`/`"Lunar"` corruption (neither string is ever a real asteroid name, so it would correctly fall through to a genuine `"unknown"` classification instead of `"asteroid"`).
2. Fix `Lilith_BML` (add it to `_LUMINARIES` or a small `_CALCULATED_POINTS` set alongside it — it's neither a luminary nor a planet nor an asteroid; a dedicated bucket, or simply excluding it via the standard-planets check, both work).
3. Be robust against any future body name this hasn't anticipated (a new proprietary point, a lot name once Phase 6 lands, etc.) — those would correctly fall through to `"unknown"` rather than silently inflating asteroid metrics.

This does **not** require touching `engine/transit_engine.py`'s `scan_eclipses()` — that function's `eclipse_type` labeling is correct and used by existing production content-pack routing; changing it risks the exact kind of pipeline regression this whole hygiene effort has been careful to avoid. The fix belongs entirely in the Phase 2 adapter, which is the file that introduced the assumption in the first place.

## Owner

Codex, per `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md` Phase 2 file ownership (`engine/predictive_sidecar.py` is explicitly Codex's territory, not Claude's — Claude's Phase 2 ownership is limited to `phase0/01_predictive_object_schemas.md`, `phase0/06_sidecar_and_export_contract.md`, and schema conformance notes like this one).

## Verification method

Not just read from source — independently reproduced live: generated a real Year Ahead report (`generate.py year_ahead ...`), inspected the resulting `.eo_predictive.json` sidecar directly, and traced every flagged `raw_events` entry back to its root cause in `engine/transit_engine.py`. Test artifacts were generated under `tmp/` (gitignored) and deleted after verification; no repo files were added by this review.
