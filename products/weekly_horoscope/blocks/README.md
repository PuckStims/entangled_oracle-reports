# Weekly Horoscope Blocks

These files supply the prose layer for `weekly_horoscope`.

The weekly product stays smaller than Year Ahead or Personal Forecast: it uses
selected exact contacts from the existing weekly scan, then turns those contacts
into a subscriber-style theme, guidance note, watch-list, and localized timing
notes. Blocks may use Python `str.format_map` placeholders such as
`{strongest_planet}`, `{strongest_house}`, `{contact_phrase}`, and `{count}`.

The timing section is grouped by day. Each day receives a movement label and
short guidance block before its selected contacts. Contact guidance uses
variant keys (`v1`, `v2`, `v3`) so the weekly selector can avoid reusing the
same prose block path while alternatives exist.

## Contact-level selector wiring (exact aspect + target group)

`aspect_character` (`flowing` / `challenging` / `neutral`) is the broad
grouping used by the theme/day/legacy moment blocks above (`aspect_movements`,
`moment_focus`, `moment_guidance`). It stays in place. Alongside it, a
contact-level layer routes on the *exact* aspect and on what natal target is
being contacted, grouped by function rather than raw label:

```
transit_planet -> exact_aspect -> natal_target_group
```

- `exact_aspect` is one of `Conjunction`, `Sextile`, `Trine`, `Square`,
  `Opposition`, `Semisquare`, `Sesquiquadrate`, `Quincunx` (see
  `engine/transit_engine.py`'s `ASPECT_CHARACTERS` / `TIMELINE_ASPECT_CHARACTERS`
  for where these come from).
- `natal_target_group` is a short function-group key, not the raw natal
  target label -- see `_WEEKLY_TARGET_GROUPS` in `generate.py`:
  `identity`=Sun, `mood`=Moon, `language`=Mercury, `values`=Venus,
  `action`=Mars, `growth`=Jupiter, `structure`=Saturn, `disruption`=Uranus,
  `longing`=Neptune, `power`=Pluto, `presence`=ASC, `public_role`=MC,
  `partnership`=DSC, `home`=IC, `threshold`=Vertex.
- House is deliberately **not** a fourth leg of that key path (a
  planet x aspect x target x house matrix explodes too fast). It is an
  independent secondary layer, available as the `{house_context}`
  interpolation value from `house_contexts.json`.

Files in this layer:

- `contact_meanings.json` -- the key path above. Feeds `meaning_primary`
  (primary, reader-facing translated prose).
- `contact_guidance.json` -- `exact_aspect -> guidance_mode`. Feeds
  `guidance_line` (the actionable follow-up sentence).
- `aspect_movements_exact.json` -- `exact_aspect` only. Exposed as the
  `{aspect_movement_exact}` interpolation value, not a rendered field on its
  own.
- `target_functions.json` -- `natal_target_group` only. Glossary of what
  each function-group means; exposed as `{target_function}`.
- `house_contexts.json` -- house number only. Secondary-layer modifier;
  exposed as `{house_context}`.

All five are currently **skeletons**: every leaf is the literal string
`"TODO"`. `generate.py`'s `_weekly_resolve_or_placeholder()` treats a literal
`"TODO"` as unauthored and transparently falls back to the existing
`moment_focus.json` / `moment_guidance.json` output for `meaning_primary` /
`guidance_line`, so shipping with TODO leaves is always safe -- output does
not change until a leaf is actually authored.

The weekly moment context also exposes separated rendered fields so the
template does not have to assemble the card's main meaning from raw
technical fields: `meaning_primary` (primary), `technical_label` (secondary,
e.g. `Mars square Saturn`), `technical_meta` (tertiary, e.g. `House 5 ·
challenging · strong support signal`), `guidance_line`, and `selector_trace`
(internal structured audit data -- requested dimensions, resolved block paths,
fallback depth, whether a TODO placeholder fell back to legacy prose, and which
legacy source supplied the temporary rendered line). The weekly prose ledger
also collects these selector traces under `contact_selector_traces` so coverage
audits can distinguish authored contact-matrix coverage from safe legacy
fallback rendering.

Editorial standards:

- Use `docs/prose_guides/Entangled_Oracle_Master_Plainspeak_Guide_v5.md` for
  plainspeak translation.
- Use `docs/prose_guides/Entangled_Oracle_Anti-Monotony_Redundancy_Protocol_v2.md`
  for variation, adjacent-block value, practical guidance rotation, and
  deterministic-claim boundaries.
- Keep targeted weekly subject phrases to no more than three reader-facing
  subjects. House domains and planet motifs should feel localized, not like a
  keyword thesaurus.
- Do not promote the weekly surface into a full Year Ahead. The blocks should
  add specificity, pacing, and option depth around retained weekly evidence.
