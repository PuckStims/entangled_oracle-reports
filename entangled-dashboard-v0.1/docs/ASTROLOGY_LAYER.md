# Astrology Layer

The v0.1 astrology layer is an adapter scaffold. It intentionally does not create astrological data, approximate sky context, natal meanings, or profile routing.

## Live Sky Context

The future wired engine should provide:

- Sun sign.
- Approximate Moon sign.
- Approximate Moon phase.
- Selected planet signs.
- Retrograde notes.
- Major current aspects.
- Dominant element and modality.

## Profile Lens

`src/data/astrology/profile.placeholder.json` marks the private profile slot. Personal profiles can be added as `.local.json` files, which are gitignored.

The profile lens changes emphasis. It does not override the symbol.
