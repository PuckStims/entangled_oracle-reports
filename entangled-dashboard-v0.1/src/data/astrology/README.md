# Astrology Data

This repo intentionally does not create astrological meanings, natal data, or computed sky context.

Wire the existing astrology engine into:

```text
src/features/astrology/liveAstroEngine.ts
src/features/astrology/natalLens.ts
```

Recommended privacy pattern:

- Commit examples and schemas only.
- Keep exact natal/profile data in `*.local.json` files.
- `.local.json` astrology files are gitignored.
