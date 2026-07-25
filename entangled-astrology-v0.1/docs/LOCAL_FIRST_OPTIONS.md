# Local-First Options

## Route A — FastAPI adapter first

Preserves the current Python engine and gives the Kotlin app a verifiable bridge. This is the recommended Codex target.

## Route B — embedded Python feasibility pass

Investigate only after Route A works. Confirm Android support for every native dependency, especially Swiss Ephemeris bindings and ephemeris file access. Do not assume a desktop wheel can run on Android.

## Route C — native/JNI engine

Potential long-term standalone route. Requires parity tests against the Python engine to prevent semantic drift.

Because the app depends only on `AstrologyEngine`, these routes can coexist during migration.
