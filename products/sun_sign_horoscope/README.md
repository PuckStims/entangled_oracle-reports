# Sun-Sign Horoscope (newspaper-style)

Pre-generates classic "newspaper column" daily horoscopes — **one reading per
zodiac sign**, no birth time or birth date required — as Facebook-ready image
cards plus matching text captions, in bulk for scheduling.

## How it works

The personalized [Daily Horoscope](../daily_horoscope) needs a real birth chart
to know which natal house a transit falls in. This product uses **solar houses**
instead: each sign is treated as its own 1st house, and the day's real
transiting planets are mapped into houses *relative to that sign*. That is how
professional sun-sign columns are actually built, and it lets us reuse the Daily
Horoscope block libraries verbatim:

- `daily_horoscope/blocks/todays_sky.json` — moon phase × element (shared by all signs)
- `daily_horoscope/blocks/your_activation.json` — transit planet × house (differs per sign)
- `daily_horoscope/blocks/day_ruler.json` — weekday ruler (shared by all signs)

The sky (moon phase, moon sign, day ruler, and the featured transit) is computed
**once per day** at 12:00 UTC; only the solar house of the featured planet — and
therefore the "Your Activation" paragraph — changes from sign to sign.

Methodology: Tropical zodiac · solar (whole-sign-from-Sun) houses.

## Files

- `tooling/sun_sign_engine.py` — sky computation + solar-house mapping + block assembly
- `templates/sun_sign_card.html` — 1080×1080 Facebook card (Today's Sky · Your Activation · Day's Ruler)
- `tooling/generate_sun_sign_batch.py` — batch loop → HTML cards + `captions.csv` + `manifest.json`
- `tooling/render_cards.py` — Playwright HTML → 1080×1080 PNG
- `tooling/generate_daily_briefing_frame.py` - combines generated Cosmic Weather + all 12 Sun-sign cards into one 1080x1920 PNG per date

## Usage

From `C:\entangled_oracle`:

```powershell
# 1. Generate a month of cards (12 signs × 30 days = 360 posts)
python products/sun_sign_horoscope/tooling/generate_sun_sign_batch.py --start 2026-08-01 --days 30

# 2. Render them all to PNGs (needs Playwright — see setup below)
python products/sun_sign_horoscope/tooling/render_cards.py output/sun_sign_horoscope/2026-08-01_30d
```

Output lands in `output/sun_sign_horoscope/<start>_<days>d/`:

- `<date>_<sign>.html` / `<date>_<sign>.png` — one card per sign per day
- `captions.csv` — columns `date, sign, image_filename, caption` (the text half of each post)
- `manifest.json` — run metadata + a per-post index

Then upload/schedule to Facebook by walking `captions.csv`: for each row, post
`image_filename` with `caption`, scheduled for `date`.

## Combined daily briefing frame

When 12 separate sign cards are too much friction for social sharing, generate
one portrait frame per date that combines the collective Cosmic Weather with all
12 Sun-sign activations:

```powershell
python products/sun_sign_horoscope/tooling/generate_daily_briefing_frame.py `
  --start 2026-01-01 `
  --days 7 `
  --sun-dir output/manual_tests/sun_sign `
  --weather-dir output/manual_tests/cosmic_weather
```

The frame renderer reads the already-generated HTML cards as source material and
draws PNGs directly. It keeps the Cosmic Weather prose intact and uses exact
first-sentence excerpts from each sign activation rather than rewriting the
horoscope copy. Each sign tile also gets a small daily inflection leaf (for
example, `Opening signal - day 1 of 6` or `Closing pass - day 6 of 6`) computed
from the contiguous manifest run where the same activation planet and solar
house remain active.

### Options

| Flag | Default | Notes |
|------|---------|-------|
| `--start YYYY-MM-DD` | today (UTC) | first day of the run |
| `--days N` | 7 | consecutive days to generate |
| `--sign Leo` | all 12 | limit to one sign |
| `--palette vibrant\|muted` | vibrant | card color scheme |
| `--out DIR` | `output/sun_sign_horoscope/<start>_<days>d` | override output folder |

`render_cards.py` takes the output directory and supports `--only <file.html>`,
`--force` (re-render existing PNGs), and `--size` (square edge, default 1080).

## Playwright setup (one time)

```powershell
pip install playwright
python -m playwright install chromium
```

## Tuning the featured transit

Which planet "activates" a given day is a sky-only choice (there is no natal
chart to aspect). `sun_sign_engine.py` features the tightest aspect the day forms
between a fast mover (Sun/Mercury/Venus/Mars) and any other planet, reporting the
fast mover because its solar house shifts most across signs and dates. If no
aspect is within `_FEATURE_ORB` (6°), it falls back to the Sun. A slow outer-planet
aspect can linger for days, so the featured planet may repeat across a short run —
adjust `_FEATURE_ORB`, `_FEATURE_PLANETS`, or `_FAST_MOVERS` in the engine to
change how quickly the feature rotates.
