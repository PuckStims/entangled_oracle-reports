# Consumer Report Studio + Beta Website Implementation Status

Date: 2026-07-15

This document records the current implementation state for the larger Consumer Report Studio + Beta Website build plan. It is intentionally not a completion claim for the full build plan.

## Full Build Destination

The larger destination remains:

- a local/private browser-based Report Studio around the existing Python report engine;
- a public static beta website that explains the product, evidence, method, limits, samples, and beta access;
- free-only public hosting and intake options;
- optional AI-feeling engagement that is not load-bearing;
- clear privacy handling for birth data and generated reports;
- explicit separation between current beta exposure, deferred surfaces, and future public self-serve generation.

## Implemented In This Slice

- Added a Flask-based Report Studio app shell.
- Added guarded report registry for beta exposure.
- Exposed `year_ahead`, `personal_forecast`, and `soul_ecosystem` in the Studio.
- Kept `horoscope` and `weekly_horoscope` visible as deferred rather than silently removed.
- Blocked non-consumer/internal surfaces from Studio exposure.
- Added report intake, validation, review, generation, viewer, raw HTML, and delete routes.
- Added local session storage under `runtime/studio_sessions/`.
- Ensured generated Studio output uses `report.html` inside a random session folder, avoiding client names in filenames or routes.
- Added static no-API companion prompts.
- Added print/save and local delete controls in the viewer.
- Updated the existing static `marketing-site/index.html` with private beta Studio framing, method explanation, current/deferred report positioning, deterministic report finder, reflection prompt tool, and beta request CTA.
- Added deployment-safe marketing image asset under `marketing-site/assets/img/`.
- Added `flask` to project dependencies.
- Made setuptools package discovery explicit so editable install works with the new `app/` package.
- Added ignore rules for `runtime/` and `*.egg-info/`.

## Verified

- `python -m py_compile` passed for the new app modules.
- `python -m unittest tests.test_phase9_operational_readiness -v` passed: 4 tests.
- `git diff --check` passed.
- Flask test client loaded:
  - `/`
  - `/reports`
  - `/create/year_ahead`
  - `/companion`
  - `/health`
- Blocked report URL `/create/predictive_sandbox` returned 404.
- Valid Year Ahead intake reached review.
- Missing exact birth time for Year Ahead returned a friendly validation error.
- Deferred Daily Horoscope route returned a friendly "not exposed" error.
- Real `year_ahead` generated through the service into a random local session with `report.html` and `report.manifest.json`.
- Real `personal_forecast` generated through the Flask `/generate` route and redirected to the viewer.
- Viewer and raw report routes loaded a generated report.
- Delete route removed the generated session after the report response was closed.
- Browser QA used Playwright with system Chrome because the bundled Playwright browser was not installed.
- Browser screenshots were inspected for:
  - Studio reports desktop
  - Studio reports mobile
  - Studio viewer desktop with generated report iframe
  - marketing site desktop
  - marketing site mobile
- Static marketing interactions were verified:
  - Report Finder changes recommendation.
  - Reflection Prompt changes prompt tone.

## Explicit Deferrals

These are not dropped from the larger build plan:

- A real Tally or Google Forms beta intake form is not yet created or embedded; current beta request uses email because form creation requires account-side setup.
- Public self-serve generation is not implemented.
- Hosted Flask deployment is not attempted.
- Payment handling is not implemented.
- Accounts, authentication, rate limiting, queues, and public deletion workflows are not implemented.
- Sample report gallery and fictionalized public samples are not yet built.
- Full multi-page static site expansion is not yet built; this slice updates the existing single-page `marketing-site/index.html`.
- `horoscope` remains deferred pending revalidation of exact and DOB-only paths.
- `weekly_horoscope` remains commercially deferred and is not part of the current Studio exposure.
- AI is static/no-API only; no Ollama, Gemini, OpenAI, or bring-your-own-key integration is implemented.
- Manifest PII redesign is not implemented; the Studio avoids exposing full manifest details in the UI but the underlying generated manifest still follows the current engine schema.

## Local Run Command

```powershell
.\.venv\Scripts\python.exe run_app.py
```

Then open:

```text
http://127.0.0.1:5055/
```
