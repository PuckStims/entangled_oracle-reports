# Codex Backend Build Prompt

You are integrating the existing Entangled Oracle Python astrology/report engine with the supplied Entangled Astrology Kotlin frontend.

Do not create a simplified replacement astrology engine. Do not infer chart positions, transits, report prose, activation scores, or life-area weighting from generic astrology knowledge. The supplied engine and known-good outputs are authoritative.

## Phase 1 — audit before implementation

1. Inspect the entire supplied engine repository.
2. Identify the working CLI command and programmatic entry points.
3. Trace the full path from birth inputs to calculations, raw events, normalization, canonical IDs, deduplication, selectors, content packs, fallback tiers, report context, section assembly, and rendering.
4. Identify Swiss Ephemeris bindings, ephemeris paths, timezone/location dependencies, environment variables, global state, caches, and concurrency hazards.
5. Run or inspect the supplied known-good raw output and report.
6. Produce `ENGINE_AUDIT.md` before changing calculation code.

## Phase 2 — build the thin bridge

Implement a FastAPI adapter conforming exactly to `openapi/entangled-oracle-v1.yaml`.

Prefer importing and calling existing functions used by the CLI. Adapter code may normalize transport shapes but must not change calculation semantics.

Implement:

- `GET /v1/health`
- `GET /v1/engine/identity`
- `GET /v1/capabilities`
- `POST /v1/profiles/validate`
- `POST /v1/charts/natal`
- `POST /v1/fields/current`
- `POST /v1/timelines/calculate`
- `POST /v1/places/resonance`
- `POST /v1/places/compare`
- `POST /v1/relationships/calculate`
- `POST /v1/reports/generate`
- `GET /v1/jobs/{jobId}`
- `GET /v1/reports/{reportId}`

Only advertise capabilities that the inspected engine actually supports.

## Phase 3 — provenance and validation

Every response must include the engine version, schema version, invoked calculation modules, normalization status, content-pack IDs, fallback tier, and warnings.

Every synthesized current-field or relationship pattern must list supporting event IDs that appear in the response.

Return explicit unsupported-capability responses instead of fabricated content.

## Phase 4 — parity tests

Create fixtures from supplied real engine outputs and prove that API results reconcile with the CLI for identical inputs. Test timezone behavior, exact aspect/orb values, applying/exact/separating state, duplicate-event handling, natal angle aliases, continuation/page behavior where relevant, and fallback reporting.

## Phase 5 — connect Android

Run the backend and use the Android engine settings screen to test health, identity, capabilities, natal chart, Current Field, timeline, and supported reports. Do not patch the frontend to accept weaker data; fix the adapter or document a deliberate schema revision.

## Deliverables

- backend source,
- dependency lock file,
- `.env.example` without secrets,
- startup scripts for Windows and Unix,
- tests,
- `ENGINE_AUDIT.md`,
- `PARITY_REPORT.md`,
- updated OpenAPI only when necessary and with a migration note,
- instructions for emulator and physical-device connection.
