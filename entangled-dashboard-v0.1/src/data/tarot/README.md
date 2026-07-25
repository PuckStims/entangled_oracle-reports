# Tarot Data

This repo intentionally does not generate tarot meanings.

Wire your existing 78-card JSON into the tarot adapter at:

```text
src/features/tarot/tarotEngine.ts
```

Recommended local/public options:

- `src/data/tarot/tarot-78.json` for a repo-safe committed dataset.
- `src/data/tarot/tarot-78.local.json` for a private local file.

The placeholder file is an empty array so the app can run before real data is connected.
