# Parity Report

Date: 2026-07-18

## Completed

- Android unit build passed with `gradlew.bat test`.
- FastAPI adapter calls `generate.get_payload()` for natal chart data rather than recalculating placements.
- FastAPI adapter calls `app.services.report_service.create_report()` for generated HTML reports.
- Profile validation uses the engine payload to normalize resolved location, timezone, and coordinates.
- Current Field uses existing current-transit and daily-timeline scanners.
- Timeline uses the existing year-ahead event scanner over the requested API range.
- Remaining unsupported structured endpoints return explicit `UNSUPPORTED_CAPABILITY` responses.

## Smoke Parity Basis

A local natal smoke profile for `1990-06-15 08:30, Peoria, IL` returned the same engine-owned payload shape used by the CLI/report generator:

- `user_profile.timezone`: `America/Chicago`
- `user_profile.zodiac`: `Tropical`
- `user_profile.house_system`: `Whole Sign`
- `standard_planets`: present
- `angles`: present
- `aspects`: present

The API maps these fields into the Android v1 `NatalChart` contract without changing the underlying calculation semantics.

Current Field and Timeline smoke tests assert that returned field patterns reference event IDs present in the same response, and that timeline event IDs remain unique.

## Remaining Parity Work

- Build fixtures from known-good CLI outputs and compare API natal placement/aspect responses field by field.
- Compare API current-field/timeline events against known-good raw scanner outputs for multiple birth profiles and date ranges.
- Reconcile structured Place Resonance objects with existing location-service renderers before enabling `/v1/places/resonance`.
- Add report-generation parity tests that compare generated API report sessions with CLI output for the same birth profile, report date, content pack, and destination.
