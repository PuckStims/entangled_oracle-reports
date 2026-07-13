"""
Batch generator for newspaper-style Sun-Sign Horoscopes.

Pre-generates a run of daily posts (12 signs x N days) for Facebook scheduling.
Each sign/day produces a self-contained HTML card; the run also writes a
captions.csv (the text half of every post) and a manifest.json.

Usage (from C:\\entangled_oracle):
    python products/sun_sign_horoscope/tooling/generate_sun_sign_batch.py --start 2026-07-06 --days 30
    python products/sun_sign_horoscope/tooling/generate_sun_sign_batch.py --days 7 --sign Leo
    python products/sun_sign_horoscope/tooling/generate_sun_sign_batch.py --days 7 --palette muted

Output lands in output/sun_sign_horoscope/<start>_<days>d/ by default:
    <date>_<sign>.html      one card per sign per day
    captions.csv            date, sign, image_filename, caption
    manifest.json           run metadata + per-post index

Render the HTML cards to 1080x1080 PNGs with render_cards.py.
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
from products.sun_sign_horoscope.tooling.sun_sign_engine import (  # noqa: E402
    ZODIAC_SIGNS,
    build_caption,
    build_sign_reading,
    compute_day_sky,
)

_TEMPLATE_PATH = os.path.join(
    _PROJECT_ROOT, "products", "sun_sign_horoscope", "templates", "sun_sign_card.html"
)


def _load_template():
    try:
        from jinja2 import Template
    except ImportError as exc:  # pragma: no cover - environment guard
        raise SystemExit(
            "jinja2 is required for the sun-sign card template.\n"
            "Install it with:  pip install jinja2"
        ) from exc
    with open(_TEMPLATE_PATH, "r", encoding="utf-8") as handle:
        return Template(handle.read(), autoescape=True)


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch-generate sun-sign horoscope cards.")
    parser.add_argument("--start", default=None,
                        help="First date YYYY-MM-DD (UTC). Defaults to today.")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of consecutive days to generate (default 7).")
    parser.add_argument("--sign", default=None,
                        help="Limit to a single sign (e.g. Leo). Default: all 12.")
    parser.add_argument("--frame", default="sun", choices=["sun", "moon"],
                        help="sun = Sun-sign/external (default); moon = Moon-sign/internal.")
    parser.add_argument("--palette", default=None, choices=["vibrant", "muted", "twilight"],
                        help="Color palette. Default: muted for sun, twilight for moon.")
    parser.add_argument("--out", default=None,
                        help="Output directory. Default: output/sun_sign_horoscope/<start>_<days>d_<frame>")
    return parser.parse_args(argv)


def _resolve_start(value: str | None) -> datetime:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _resolve_signs(value: str | None) -> list[str]:
    if not value:
        return list(ZODIAC_SIGNS)
    match = next((s for s in ZODIAC_SIGNS if s.lower() == value.lower()), None)
    if not match:
        raise SystemExit(f"Unknown sign: {value!r}. Choose one of {', '.join(ZODIAC_SIGNS)}.")
    return [match]


def main(argv=None) -> int:
    args = _parse_args(argv)
    start = _resolve_start(args.start)
    signs = _resolve_signs(args.sign)
    palette = args.palette or ("twilight" if args.frame == "moon" else "muted")
    template = _load_template()

    out_dir = args.out or os.path.join(
        OUTPUT_DIR, "sun_sign_horoscope",
        f"{start.strftime('%Y-%m-%d')}_{args.days}d_{args.frame}",
    )
    os.makedirs(out_dir, exist_ok=True)

    posts: list[dict] = []
    captions_rows: list[dict] = []

    for day_offset in range(args.days):
        date = start + timedelta(days=day_offset)
        sky = compute_day_sky(date)  # computed once per day, shared across signs
        for sign in signs:
            reading = build_sign_reading(sky, sign, palette_name=palette, frame=args.frame)
            html = template.render(**reading)
            stem = f"{reading['iso_date']}_{sign.lower()}"
            html_name = f"{stem}.html"
            image_name = f"{stem}.png"
            with open(os.path.join(out_dir, html_name), "w", encoding="utf-8") as handle:
                handle.write(html)

            caption = build_caption(reading)
            captions_rows.append({
                "date": reading["iso_date"],
                "sign": sign,
                "image_filename": image_name,
                "caption": caption,
            })
            posts.append({
                "date": reading["iso_date"],
                "sign": sign,
                "html": html_name,
                "image": image_name,
                "activation_planet": reading["activation_planet"],
                "activation_house": reading["activation_house"],
                "moon_phase": reading["moon_phase"],
                "moon_sign": reading["moon_sign"],
                "day_ruler": reading["day_ruler_name"],
            })

    captions_path = os.path.join(out_dir, "captions.csv")
    with open(captions_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "sign", "image_filename", "caption"])
        writer.writeheader()
        writer.writerows(captions_rows)

    anchor = "Moon sign" if args.frame == "moon" else "Sun sign"
    manifest = {
        "product": "sun_sign_horoscope",
        "frame": args.frame,
        "methodology": f"Tropical zodiac · whole-sign houses from the reader's {anchor}",
        "complexity_capacity": [
            "Swiss Ephemeris sky positions are computed once per calendar day.",
            "Moon phase, Moon sign, day ruler, and featured fast-planet aspect are calculated from the real sky.",
            "Each sign receives a solar-house activation by treating that sign as the first house.",
        ],
        "simplified_output_contract": (
            "One square social card per sign per day; natal birth data, exact houses, and personal transits are intentionally excluded."
        ),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "start_date": start.strftime("%Y-%m-%d"),
        "days": args.days,
        "signs": signs,
        "palette": palette,
        "post_count": len(posts),
        "posts": posts,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    print(f"Generated {len(posts)} cards -> {out_dir}")
    print(f"  captions.csv  ({len(captions_rows)} rows)")
    print(f"  manifest.json ({len(posts)} posts)")
    print("Next: render PNGs with")
    print(f'  python products/sun_sign_horoscope/tooling/render_cards.py "{out_dir}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
