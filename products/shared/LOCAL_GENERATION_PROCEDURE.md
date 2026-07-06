# Local Generation Procedure

## Scope

This is the active local production procedure for Tropical zodiac + Whole Sign house reports generated from `C:\entangled_oracle`.

## Required Project Location

- Active workspace root: `C:\entangled_oracle`
- Run all commands from that directory.

## Required Environment

- Windows PowerShell
- Python 3.14 or a compatible local Python on the system path
- Local filesystem write access to `C:\entangled_oracle\output`

## Required Dependencies

- Required for HTML template rendering:
  - `pip install jinja2`
- Required for live natal and transit calculations:
  - `pip install pyswisseph`

If `jinja2` is missing, the generator falls back to a simple HTML renderer.
If `pyswisseph` is missing, live transit-dependent reports cannot use the full local transit engine.

## Birth-Data Intake Format

Use one record per client with these fields:

- `name`: client-facing name
- `date`: `YYYY-MM-DD`
- `time`: `HH:MM` in 24-hour local birth time when available
- `location`: free-text city/state/country string
- `report_date`: `YYYY-MM-DD` start date for forecast reports when needed
- `simple_mode`: use only when birth time is unknown and the report supports DOB-only operation

Minimum CLI intake examples:

```powershell
python .\generate.py horoscope --name "Visitor" --date 1990-06-15 --simple --location "Peoria, IL" --no-browser
python .\generate.py year_ahead --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL" --report-date 2026-01-01 --content-pack entangled_oracle --no-browser
```

## Report-Type Selection

Active report types:

- `horoscope`
- `year_ahead`
- `personal_forecast`
- `soul_ecosystem`

Use `--simple` only for DOB-only horoscope generation.

## Methodology Statement

Active production methodology:

- Tropical zodiac
- Whole Sign houses

No active production procedure should route to Sidereal, Placidus, ayanamsa-specific, or synthesis-profile outputs.

## Content-Pack Selection

Use `--content-pack` for forecast-style report voices:

- `plainspeak`
- `entangled_oracle`

Current operational rule:

- `year_ahead` and `personal_forecast` may use either content pack.
- `horoscope` and `soul_ecosystem` use their report-local content libraries and should keep the default unless a controlled test specifically requires otherwise.

## Generation Command

Canonical command pattern:

```powershell
python .\generate.py <report_type> `
  --name "<Client Name>" `
  --date YYYY-MM-DD `
  --time HH:MM `
  --location "<City, State>" `
  --report-date YYYY-MM-DD `
  --content-pack <plainspeak|entangled_oracle> `
  --output-filename <client_report.html> `
  --no-browser
```

DOB-only horoscope pattern:

```powershell
python .\generate.py horoscope `
  --name "<Client Name>" `
  --date YYYY-MM-DD `
  --location "<City, State>" `
  --simple `
  --output-filename <client_horoscope_simple.html> `
  --no-browser
```

## Output Location

Generated HTML and manifest sidecar files land in:

- `C:\entangled_oracle\output\`

Each report now produces:

- `<report>.html`
- `<report>.manifest.json`

## HTML Review

Before delivery:

1. Open the HTML file.
2. Confirm client name, birth data, report type, date range, and methodology labels.
3. Confirm no placeholder text, missing block markers, debug traces, or broken layout sections are visible.
4. Confirm the adjacent manifest exists and references Tropical zodiac + Whole Sign houses.

## PDF Generation

Use the approved browser-print workflow only:

- `products/shared/REPORT_PDF_WORKFLOW.md`

The HTML file is the source of truth. Do not use ad hoc PDF export routes that bypass the approved browser-print workflow.

## Quality-Control Review

Run the local QA workflow before controlled delivery:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_phase8_qa.ps1
```

Then review:

- `products/shared/PRE_DELIVERY_QC_CHECKLIST.md`
- `output/phase8_review_pack/review_checklist.md`

## Delivery Preparation

Deliver only after:

1. HTML review is complete.
2. PDF review is complete when PDF delivery is requested.
3. The manifest sidecar is present.
4. File naming matches the client and report type.
5. The pre-delivery checklist is complete.
