# Entangled Oracle - Report Generator

**MVP Build · Ksisti-Puck LLC**

Offline-capable astrology report generator.
Python computes -> JSON feeds blocks -> localhost HTML renders beautifully.

---

## Setup

```bash
# Install runtime dependencies
pip install -e .

# Optional: install dev/test extras
pip install -e .[dev]
```

---

## Quick Start

`--name`, `--date`, and `--location` are required for every report type,
including `--simple` mode — a real location is always resolved to
coordinates and a timezone, even when birth time is skipped.

```bash
# Year Ahead
python generate.py year_ahead \
  --name "Puck" \
  --date 1992-03-21 \
  --time 08:11 \
  --location "Peoria, IL"

# Personal Forecast
python generate.py personal_forecast \
  --name "Puck" \
  --date 1992-03-21 \
  --time 08:11 \
  --location "Peoria, IL"

# Soul Ecosystem
python generate.py soul_ecosystem \
  --name "Puck" \
  --date 1992-03-21 \
  --time 08:11 \
  --location "Peoria, IL"

# Daily Horoscope (Full mode)
python generate.py horoscope \
  --name "Visitor" \
  --date 1990-06-15 \
  --time 14:30 \
  --location "Chicago, IL"

# Daily Horoscope (Simple - DOB only, birth time skipped but location is still required)
python generate.py horoscope \
  --name "Visitor" \
  --date 1990-06-15 \
  --location "Chicago, IL" \
  --simple
```

Reports open automatically in your browser.
Files saved to `output/`.

Malformed `--date`/`--time`, an empty `--name`, or a missing `--location`
fail immediately with a clear one-line message rather than a raw
traceback or a silently wrong chart.

**Retired:** Asteroid Portrait was removed 2026-07-02. Every archetype
and dimension it covered has a Soul Ecosystem equivalent (same
taxonomy, better-tuned plainspeak voice) — see `agents/REVISIONS.md`
for the full migration audit before assuming anything needs rebuilding.

---

## Supporting Docs

- [ARCHITECTURE.md](C:/entangled_oracle/ARCHITECTURE.md)
- [METHODS.md](C:/entangled_oracle/METHODS.md)
- [products/shared/CLIENT_METHOD_AND_LIMITS.md](C:/entangled_oracle/products/shared/CLIENT_METHOD_AND_LIMITS.md)

---

## Project Structure

```text
entangled_oracle/
|-- generate.py                  Main CLI entry point and report orchestrator
|-- config.py                    Thresholds, mappings, and path configuration
|-- engine/
|   |-- natal_engine.py          Swiss Ephemeris natal payload generation
|   |-- transit_engine.py        Year Ahead / predictive transit timeline engine
|   `-- chart_wheel.py           SVG natal chart wheel rendering
|-- formulas/
|   |-- standard_indexes.py      Standard astrological computations
|   |-- proprietary_indexes.py   EO proprietary index calculations
|   `-- standard/                Auditable standard-method submodules
|-- selectors/
|   |-- utils.py                 Core geometry and payload helpers
|   |-- block_selector.py        JSON block selection and fallback routing
|   `-- variable_resolver.py     Template-variable derivation from payload/indexes
|-- products/
|   |-- daily_horoscope/
|   |   |-- blocks/
|   |   `-- templates/
|   |-- personal_forecast/
|   |   |-- blocks/
|   |   `-- templates/
|   |-- soul_ecosystem/
|   |   |-- blocks/
|   |   `-- templates/
|   |-- year_ahead/
|   |   |-- blocks/
|   |   |-- templates/
|   |   |-- drafts/
|   |   `-- tooling/
|   |-- predictive_sandbox/
|   |   `-- templates/
|   `-- identity_profile/
|       |-- blocks/
|       |-- runtime/
|       |-- templates/
|       `-- tooling/
|-- tests/                       Regression and rendering-contract coverage
|-- agents/                      Cross-session notes: revisions log, planned
|                                 updates, and a running musings file (see
|                                 agents/README.md)
`-- output/                      Generated HTML/PDF reports and manifests
```

---

## Transit Climate Notes (Personal Forecast, Year Ahead)

Two purely transit-based, natal-independent features run alongside the
main report content:

- **Retrograde cluster climate** — flags a stretch where 2+ of the eight
  outer/inner planets (Mercury through Pluto) are simultaneously
  retrograde, and surfaces a plainspeak framing paragraph for whichever
  cluster is active at the report's start date.
- **Void-of-Course Moon** — finds the next Moon VOC window (the Moon's
  last classical aspect to Sun through Saturn before it changes sign) from
  the report's start date, tiered `brief_void` vs. `extended_void`.

Both are computed in `engine/transit_engine.py`
(`detect_retrograde_clusters`, `detect_void_of_course_windows`), authored
in `products/personal_forecast/blocks/shared/` (shared by both report
types — see `config.py`'s `CONTENT_PACKS`), and fail non-fatally: if
either detector errors, the section is simply omitted rather than
breaking the report.

The natal chart wheel (Personal Forecast, Soul Ecosystem, Year Ahead)
additionally rings any placement whose planet is *currently* retrograde
by transit — distinct from, and shown alongside, the existing orange
natal-retrograde label.

---

## Connecting Your Engine

Open `generate.py` and find the `get_payload()` function.
Replace the stub with your engine call:

```python
def get_payload(birth_data: dict) -> dict:
    from engine.natal_engine import generate_payload
    return generate_payload(birth_data)
```

Your engine must return a v2 payload dict with these keys:
- `standard_planets` - Sun through Chiron with sign, house, longitude, retrograde
- `custom_asteroids` - your asteroid catalog
- `angles` - Ascendant, Midheaven, Descendant, Imum_Coeli, Vertex
- `houses` - 12 house cusps
- `aspects` - pre-computed body-to-body and body-to-angle aspects
- `user_profile` - birth datetime, location, Julian day

---

## Writing Paragraph Blocks

The block library is fully written — there are no outstanding `[TODO: ...]`
placeholders as of this writing. If you add a new report type, placement,
or key path, drop the new paragraph(s) into the relevant
`products/<report>/blocks/**/*.json` file using the existing key
structure in that file as a model.

The block selector falls back gracefully through the key hierarchy (see
`selectors/block_selector.py`), and `_usable_block()` in `generate.py`
scrubs any `[TODO]`, `[BLOCK NOT FOUND: ...]`, or `[MISSING BLOCK FILE: ...]`
marker before it reaches a template — a missing or misspelled key path
degrades to blank prose instead of visible debug text. That filter
currently runs for Year Ahead, Personal Forecast, and Soul Ecosystem; it
has not yet been extended to Daily Horoscope.

---

## Festival Mode

For use at events: connect your existing natal engine, open a terminal,
run the generator, and display or print the HTML output.

No internet required. No cloud dependency.
Target generation time: under 30 seconds per report.

---

*Entangled Oracle · Ksisti-Puck LLC*
