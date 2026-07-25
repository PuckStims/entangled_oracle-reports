# Rune Data

This repo intentionally does not generate Elder Futhark meanings.

Wire your existing rune JSON and freehand cast logic into:

```text
src/features/runes/runeEngine.ts
```

Recommended local/public options:

- `src/data/runes/elder-futhark.json` for a repo-safe committed dataset.
- `src/data/runes/elder-futhark.local.json` for a private local file.

The placeholder file is an empty array so the app can run before real data is connected.
