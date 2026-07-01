# Entangled Oracle - Report Generator

**MVP Build · Ksisti-Puck LLC**

Offline-capable astrology report generator.
Python computes -> JSON feeds blocks -> localhost HTML renders beautifully.

---

## Setup

```bash
# Install dependencies
pip install jinja2 geopy

# Optional: install pyswisseph for live chart generation
pip install pyswisseph
```

---

## Quick Start

```bash
# Asteroid Portrait (Full birth data)
python generate.py asteroid_portrait \
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

# Daily Horoscope (Simple - DOB only)
python generate.py horoscope \
  --name "Visitor" \
  --date 1990-06-15 \
  --simple
```

Reports open automatically in your browser.
Files saved to `output/`.

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
|   |-- asteroid_portrait/
|   |   |-- blocks/
|   |   `-- templates/
|   |-- predictive_sandbox/
|   |   `-- templates/
|   `-- identity_profile/
|       |-- blocks/
|       |-- runtime/
|       |-- templates/
|       `-- tooling/
|-- tests/                       Regression and rendering-contract coverage
`-- output/                      Generated HTML/PDF reports and manifests
```

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

Every `[TODO: ...]` placeholder in the `products/**/blocks/` JSON files is a paragraph
you need to write. Start with the highest-priority blocks:

**Tier 1 - Write these first:**
1. `products/daily_horoscope/blocks/todays_sky.json` - 32 blocks (~50 words each)
2. `products/asteroid_portrait/blocks/portrait_overview.json` - 7 blocks (~95 words)
3. `products/asteroid_portrait/blocks/foresight_pattern.json` - 5 blocks
4. `products/soul_ecosystem/blocks/souls_promise.json` - 16 blocks (~130 words each)

The block selector falls back gracefully - a `[TODO]` placeholder will
appear in the report rather than crashing. Write blocks iteratively.

---

## Festival Mode

For use at events: connect your existing natal engine, open a terminal,
run the generator, and display or print the HTML output.

No internet required. No cloud dependency.
Target generation time: under 30 seconds per report.

---

*Entangled Oracle · Ksisti-Puck LLC*
