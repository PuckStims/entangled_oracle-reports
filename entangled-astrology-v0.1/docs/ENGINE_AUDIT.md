# Engine Audit

Date: 2026-07-18

## Scope

This audit covers the first mobile API bridge pass for `C:\entangled_oracle\entangled-astrology-v0.1`. It inspects the existing Entangled Oracle engine in `C:\entangled_oracle` and identifies which v1 API endpoints can be exposed without creating a simplified replacement astrology engine.

## Confirmed Engine Entry Points

- CLI: `python generate.py <report_type> --name ... --date ... --time ... --location ...`
- Programmatic natal payload: `generate.get_payload(birth_data)`, which calls `engine.natal_engine.generate_payload`.
- Programmatic report generation: `app.services.report_service.create_report`, which validates beta report requests and calls `generate.generate_report`.
- Local studio web app: `app.web.create_app`, a Flask surface over the same report service.

## Data Flow Observed

Birth data enters as a dictionary with `name`, `date`, `time`, `location`, `current_location`, `simple_mode`, optional `destination`, `report_date`, and `palette`.

`generate.get_payload()` resolves the birth location, timezone, UTC datetime, Swiss Ephemeris state, tropical zodiac, Whole Sign houses, standard planets, custom asteroids, angles, houses, and natal aspects. A smoke call returned structured keys including `user_profile`, `standard_planets`, `custom_asteroids`, `angles`, `houses`, and `aspects`.

`generate.generate_report()` then computes proprietary indexes, builds the standard report bundle, resolves template variables, selects content blocks, renders HTML, and writes an adjacent `report.manifest.json` for non-location-service report types.

## Supported Immediately

- `GET /v1/health`
- `GET /v1/engine/identity`
- `GET /v1/capabilities`
- `POST /v1/profiles/validate`
- `POST /v1/charts/natal`
- `POST /v1/fields/current`
- `POST /v1/timelines/calculate`
- `POST /v1/reports/generate`
- `GET /v1/jobs/{jobId}`
- `GET /v1/reports/{reportId}`

These are backed by actual engine functions or existing report sessions.

## Not Exposed As Structured Data Yet

- Place Resonance structured response
- Between Places
- Relationships

The engine contains location-service machinery, but this pass did not prove a stable mapping from those rendered/report-specific objects into the v1 structured Place Resonance response. The adapter returns explicit unsupported-capability errors instead of fabricating transport objects.

## Current Field And Timeline Mapping

`POST /v1/fields/current` uses `engine.transit_engine.compute_current_transits()` plus `engine.transit_engine.compute_daily_timeline()`. Field patterns are adapter summaries over returned event IDs; they do not add astrological interpretation beyond what the event scanners calculated.

`POST /v1/timelines/calculate` uses `engine.transit_engine.compute_year_ahead_events()` over the requested date range. Returned events are normalized through the existing canonical forecast-event adapter where needed and mapped into the Android `CalculatedEvent` contract.

## Environment And Runtime Notes

- Swiss Ephemeris path is reset by `generate._reset_swiss_ephemeris_path()` to the repository `ephemeris` folder.
- The engine repository contains a local package named `selectors`, which can shadow Python's standard library `selectors` module. The FastAPI bridge imports FastAPI first, then installs the engine path and EO selector package before engine calls.
- Existing report sessions are stored in `C:\entangled_oracle\runtime\studio_sessions`.
- No calculation-code changes were made in this pass.

## Release Integrity Notes

The adapter advertises `natal_chart`, `current_field`, `timeline`, and `report_generation` as supported techniques. It advertises report keys from the existing report registry. Location-service reports can be generated as HTML reports through `/v1/reports/generate`, but the structured `/v1/places/resonance` endpoint remains gated until source-to-output parity is documented.
