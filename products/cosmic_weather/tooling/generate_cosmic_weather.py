"""
Cosmic Weather Snapshot — collective daily sky, ONE card per day (no signs).

The "macro" print framework: strip the 12 sign-specific house activations and
publish just the shared modules — Today's Sky (moon phase x element) and The
Day's Ruler (weekday ruler + a practical "best used for" theme). Great for local
business ads that want astro content without running twelve horoscopes, and a
fraction of the render load (1 card/day instead of 12).

Reuses the real engine: sky positions come from products.sun_sign_horoscope's
compute_day_sky (Swiss Ephemeris), and the copy comes from the existing
daily_horoscope blocks plus this product's day_theme.json.

Usage (from C:\\entangled_oracle):
    python products/cosmic_weather/tooling/generate_cosmic_weather.py --start 2026-07-06 --days 30
    python products/cosmic_weather/tooling/generate_cosmic_weather.py --days 7 --palette twilight

Output -> output/cosmic_weather/<start>_<days>d/ :
    <date>.html      one collective card per day
    captions.csv     date, weekday, ruler, image_filename, caption
    manifest.json

Render to 1080x1080 PNGs with the shared renderer:
    python products/sun_sign_horoscope/tooling/render_cards.py output/cosmic_weather/<start>_<days>d
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config import OUTPUT_DIR  # noqa: E402
from selectors.block_selector import select_block  # noqa: E402
from products.sun_sign_horoscope.tooling.sun_sign_engine import (  # noqa: E402
    compute_day_sky,
    _resolve_palette,
    CARD_INK,
)

_TEMPLATE_PATH = os.path.join(
    _PROJECT_ROOT, "products", "cosmic_weather", "templates", "cosmic_weather_card.html"
)
_DAY_THEME_PATH = os.path.join(
    _PROJECT_ROOT, "products", "cosmic_weather", "blocks", "day_theme.json"
)


def _load_template():
    try:
        from jinja2 import Template
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("jinja2 is required.\n  pip install jinja2") from exc
    with open(_TEMPLATE_PATH, "r", encoding="utf-8") as handle:
        return Template(handle.read(), autoescape=True)


def _load_day_themes() -> dict:
    with open(_DAY_THEME_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_weather_reading(sky: dict, day_themes: dict, palette_name: str) -> dict:
    """Assemble one collective Cosmic Weather card from a precomputed day sky."""
    todays_sky_block = select_block(
        "daily_horoscope", "todays_sky",
        sky["moon_phase_key"], sky["moon_sign_element"],
    )
    day_ruler_block = select_block("daily_horoscope", "day_ruler", sky["day_ruler"])
    day_theme = day_themes.get(sky["day_ruler"], "")

    return {
        "date": sky["date"],
        "display_date": sky["date"].strftime("%B %d, %Y"),
        "iso_date": sky["date"].strftime("%Y-%m-%d"),
        "weekday": sky["date"].strftime("%A"),
        "moon_phase": sky["moon_phase"],
        "moon_sign": sky["moon_sign"],
        "todays_sky_block": todays_sky_block,
        "day_ruler_name": sky["day_ruler"],
        "day_ruler_block": day_ruler_block,
        "day_theme": day_theme,
        "palette_name": palette_name,
        "palette": _resolve_palette(palette_name),
        "ink": CARD_INK.get(palette_name, CARD_INK["muted"]),
    }


def build_caption(reading: dict) -> str:
    return (
        f"✧ COSMIC WEATHER · {reading['display_date']} ✧\n\n"
        f"{reading['moon_phase']} in {reading['moon_sign']}. "
        f"{reading['todays_sky_block']}\n\n"
        f"{reading['weekday']} is ruled by {reading['day_ruler_name']}. "
        f"{reading['day_ruler_block']}\n\n"
        f"Best used for: {reading['day_theme']}\n\n"
        f"— Entangled Oracle"
    )


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate collective Cosmic Weather cards.")
    parser.add_argument("--start", default=None, help="First date YYYY-MM-DD (UTC). Default: today.")
    parser.add_argument("--days", type=int, default=7, help="Days to generate (default 7).")
    parser.add_argument("--palette", default="muted", choices=["vibrant", "muted", "twilight"],
                        help="Color palette (default muted).")
    parser.add_argument("--out", default=None, help="Output directory override.")
    return parser.parse_args(argv)


def _resolve_start(value: str | None) -> datetime:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def main(argv=None) -> int:
    args = _parse_args(argv)
    start = _resolve_start(args.start)
    template = _load_template()
    day_themes = _load_day_themes()

    out_dir = args.out or os.path.join(
        OUTPUT_DIR, "cosmic_weather", f"{start.strftime('%Y-%m-%d')}_{args.days}d"
    )
    os.makedirs(out_dir, exist_ok=True)

    posts: list[dict] = []
    captions_rows: list[dict] = []

    for day_offset in range(args.days):
        date = start + timedelta(days=day_offset)
        sky = compute_day_sky(date)
        reading = build_weather_reading(sky, day_themes, args.palette)
        html = template.render(**reading)
        html_name = f"{reading['iso_date']}.html"
        image_name = f"{reading['iso_date']}.png"
        with open(os.path.join(out_dir, html_name), "w", encoding="utf-8") as handle:
            handle.write(html)

        captions_rows.append({
            "date": reading["iso_date"],
            "weekday": reading["weekday"],
            "ruler": reading["day_ruler_name"],
            "image_filename": image_name,
            "caption": build_caption(reading),
        })
        posts.append({
            "date": reading["iso_date"],
            "weekday": reading["weekday"],
            "html": html_name,
            "image": image_name,
            "moon_phase": reading["moon_phase"],
            "moon_sign": reading["moon_sign"],
            "day_ruler": reading["day_ruler_name"],
        })

    with open(os.path.join(out_dir, "captions.csv"), "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "weekday", "ruler", "image_filename", "caption"])
        writer.writeheader()
        writer.writerows(captions_rows)

    manifest = {
        "product": "cosmic_weather",
        "methodology": "Tropical zodiac · collective daily sky (no natal / no signs)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "start_date": start.strftime("%Y-%m-%d"),
        "days": args.days,
        "palette": args.palette,
        "post_count": len(posts),
        "posts": posts,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    print(f"Generated {len(posts)} cards -> {out_dir}")
    print(f"  captions.csv  ({len(captions_rows)} rows)")
    print("Next: render PNGs with")
    print(f'  python products/sun_sign_horoscope/tooling/render_cards.py "{out_dir}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
