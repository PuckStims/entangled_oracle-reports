# Entangled Identity Profile — v0.2 Ready-to-Drop Integration

## What to replace

Copy the files in this package over the matching files in your project:

```text
products/identity_profile/runtime/identity_profile_context.py
products/identity_profile/templates/entangled_identity_profile.html
```

Then add the four JSON files to the block location your existing `select_block()` resolver uses for the `identity_profile` report type:

```text
products/identity_profile/blocks/entity_cast.json
products/identity_profile/blocks/identity_synthesis.json
products/identity_profile/blocks/nge_narrative_gravity.json
products/identity_profile/blocks/archetypal_tensions.json
```

These are canonical runtime names. Do not keep the `_filled` suffix when installing them.

## No change is required in `generate.py`

Your current generator already sends `variables`, `index_results`, and `payload` into `build_identity_profile_context()`. This package changes the content builder and template only.

## What this version specifically fixes

- Uses NGE as the current narrative identity layer, not legacy MAGNETIC/MCQ/SIREN.
- Keeps the current EAS ordering intact and allows NGE to be the actual strongest current when it ranks first.
- Shows the NGE Narrative Gravity paragraph only when `NGE.display_full` is true.
- Shows Identity Synthesis only when both NGE and the focal primary EAS result have qualified for full display.
- Keeps AHL ancillary; it cannot become the focal primary identity current.
- Uses `lilith_source` for DFIS so `Lilith_BML` correctly falls back to asteroid `Lilith` when needed.
- Limits Archetypal Tensions to one real, auditable square or opposition between active driver bodies.
- Preserves authored paragraph spacing in the HTML output.

## Required selector behavior

The builder calls your existing selector with these exact paths:

```text
select_block("identity_profile", "entity_cast", normalized_driver_body)
select_block("identity_profile", "identity_synthesis", genre_key, primary_index_key, activation_key)
select_block("identity_profile", "narrative_gravity", genre_key, nge_activation_key)
select_block("identity_profile", "archetypal_tensions", sorted_index_pair_key, aspect_key)
```

The new builder supports both selector signatures below:

```python
select_block(report_type, block_file, *keys, fallback="")
select_block(report_type, block_file, *keys)
```

If your block selector dynamically resolves `blocks/<report_type>/<block_file>.json`, no additional selector edit is needed. If it uses an explicit filename registry, register the four names above using the same pattern as your other `identity_profile` blocks.

## Smoke test

Generate an Identity Profile exactly as you already do:

```text
python generate.py identity_profile --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
```

Check these output conditions:

1. NGE appears as the first system card only when it is display-qualified.
2. A profile with suppressed NGE has no final “The story these forces make together” panel.
3. DFIS uses “Black Moon Lilith” or “Lilith” cleanly rather than exposing `Lilith_BML`.
4. At most one Archetypal Tension card appears.
5. Entity Cast cards use authored copy, not generic fallback language, for active drivers.

## Validation included

`validation/identity_profile_integration_test_reference.py` is the reference smoke test used for this package. It verifies the NGE suppression guard, ranked focal selection, DFIS Lilith fallback, authored cast resolution, and one-tension cap.
