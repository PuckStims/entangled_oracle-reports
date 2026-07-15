"""
Render one combined Cosmic Weather + all Sun signs social frame as a PNG.

This is a visual packaging pass only. It reads already-generated Cosmic Weather
and Sun-Sign HTML cards, then draws a single 1080x1920 PNG from their existing
prose. The sign grid uses exact sentence excerpts from the generated activation
blocks; it does not rewrite horoscope copy.

Usage (from C:\\entangled_oracle):
    python products/sun_sign_horoscope/tooling/generate_daily_briefing_frame.py ^
      --date 2026-07-15 ^
      --sun-dir output/manual_tests/sun_sign ^
      --weather-dir output/manual_tests/cosmic_weather
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from html.parser import HTMLParser

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from products.sun_sign_horoscope.tooling.sun_sign_engine import ZODIAC_SIGNS  # noqa: E402

_SENTENCE_RE = re.compile(r".*?(?:[.!?](?=\s|$)|$)", re.S)


class _ClassTextParser(HTMLParser):
    def __init__(self, wanted_classes: set[str]) -> None:
        super().__init__(convert_charrefs=True)
        self._wanted_classes = wanted_classes
        self._class_stack: list[set[str]] = []
        self.parts: dict[str, list[str]] = defaultdict(list)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = set()
        for name, value in attrs:
            if name == "class" and value:
                classes.update(value.split())
        self._class_stack.append(classes)

    def handle_endtag(self, tag: str) -> None:
        if self._class_stack:
            self._class_stack.pop()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        active = set().union(*self._class_stack) if self._class_stack else set()
        for class_name in self._wanted_classes:
            if class_name in active:
                self.parts[class_name].append(text)


def _parse_html(path: str, classes: set[str]) -> dict[str, list[str]]:
    parser = _ClassTextParser(classes)
    with open(path, "r", encoding="utf-8") as handle:
        parser.feed(handle.read())
    return parser.parts


def _first_sentence(text: str) -> str:
    clean = " ".join(text.split())
    match = next((m.group(0).strip() for m in _SENTENCE_RE.finditer(clean) if m.group(0).strip()), "")
    return match or clean


def _one(parts: dict[str, list[str]], key: str, index: int = 0) -> str:
    values = parts.get(key, [])
    return values[index] if len(values) > index else ""


def _load_weather(weather_dir: str, date: str) -> dict[str, str]:
    path = os.path.join(weather_dir, f"{date}.html")
    if not os.path.isfile(path):
        raise SystemExit(f"Cosmic Weather card not found: {path}")
    parts = _parse_html(path, {"weekday", "date-line", "headline", "body", "theme"})
    return {
        "weekday": _one(parts, "weekday"),
        "date_line": _one(parts, "date-line"),
        "sky_headline": _one(parts, "headline", 0),
        "sky_body": _one(parts, "body", 0),
        "ruler": _one(parts, "headline", 1),
        "ruler_body": _one(parts, "body", 1),
        "theme": _one(parts, "theme"),
    }


def _load_signs(sun_dir: str, date: str) -> list[dict[str, str]]:
    signs = []
    for sign in ZODIAC_SIGNS:
        path = os.path.join(sun_dir, f"{date}_{sign.lower()}.html")
        if not os.path.isfile(path):
            raise SystemExit(f"Sun-sign card not found: {path}")
        parts = _parse_html(path, {"sign-name", "activation-head", "body"})
        activation_block = _one(parts, "body", 1)
        signs.append({
            "sign": _one(parts, "sign-name") or sign,
            "activation": _one(parts, "activation-head"),
            "excerpt": _first_sentence(activation_block),
        })
    return signs


def _load_sun_manifest(sun_dir: str) -> dict:
    path = os.path.join(sun_dir, "manifest.json")
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _post_index(manifest: dict) -> dict[tuple[str, str], dict]:
    return {
        (post["date"], post["sign"]): post
        for post in manifest.get("posts", [])
    }


def _activation_window(index: dict[tuple[str, str], dict], date: str, sign: str) -> tuple[int, int, str]:
    post = index.get((date, sign))
    if not post:
        return 1, 1, ""

    combo = (post.get("activation_planet"), post.get("activation_house"))
    sign_posts = sorted(
        (item for (item_date, item_sign), item in index.items() if item_sign == sign),
        key=lambda item: item["date"],
    )
    dates = [item["date"] for item in sign_posts]
    try:
        center = dates.index(date)
    except ValueError:
        return 1, 1, ""

    start = center
    while start > 0 and (
        sign_posts[start - 1].get("activation_planet"),
        sign_posts[start - 1].get("activation_house"),
    ) == combo:
        start -= 1

    end = center
    while end + 1 < len(sign_posts) and (
        sign_posts[end + 1].get("activation_planet"),
        sign_posts[end + 1].get("activation_house"),
    ) == combo:
        end += 1

    day = center - start + 1
    total = end - start + 1
    if total == 1:
        label = "Single-day signal"
    elif day == 1:
        label = "Opening signal"
    elif day == total:
        label = "Closing pass"
    elif day <= max(2, total // 3):
        label = "Building pattern"
    elif day >= total - max(1, total // 3) + 1:
        label = "Integrating pattern"
    else:
        label = "Holding pattern"
    return day, total, label


def _add_inflections(signs: list[dict[str, str]], date: str, manifest: dict) -> list[dict[str, str]]:
    index = _post_index(manifest)
    if not index:
        return signs
    for sign in signs:
        day, total, label = _activation_window(index, date, sign["sign"])
        sign["inflection"] = f"{label} · day {day} of {total}" if total > 1 else label
    return signs


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a combined daily astro briefing PNG.")
    parser.add_argument("--date", default=None,
                        help="Date to render, YYYY-MM-DD. Defaults to all dates present in both input folders.")
    parser.add_argument("--start", default=None,
                        help="First date YYYY-MM-DD for a multi-day render window.")
    parser.add_argument("--days", type=int, default=None,
                        help="Number of consecutive days to render when --start is used.")
    parser.add_argument("--sun-dir", required=True, help="Folder containing generated sun-sign HTML cards.")
    parser.add_argument("--weather-dir", required=True, help="Folder containing generated cosmic-weather HTML cards.")
    parser.add_argument("--out", default=None,
                        help="Output PNG path for one date, or output folder for multiple dates.")
    parser.add_argument("--width", type=int, default=1080, help="Image width in px (default 1080).")
    parser.add_argument("--height", type=int, default=1920, help="Image height in px (default 1920).")
    return parser.parse_args(argv)


def _dates_from_window(start: str, days: int | None) -> list[str]:
    if days is None:
        days = 7
    if days < 1:
        raise SystemExit("--days must be at least 1.")
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid --start date {start!r}; expected YYYY-MM-DD.") from exc
    return [
        (start_date + timedelta(days=offset)).strftime("%Y-%m-%d")
        for offset in range(days)
    ]


def _resolve_dates(args: argparse.Namespace, sun_dir: str, weather_dir: str) -> list[str]:
    if args.date and args.start:
        raise SystemExit("Use either --date or --start/--days, not both.")
    if args.date:
        return [args.date]
    if args.start:
        return _dates_from_window(args.start, args.days)
    if args.days is not None:
        raise SystemExit("--days requires --start.")
    return _discover_dates(sun_dir, weather_dir)


def _discover_dates(sun_dir: str, weather_dir: str) -> list[str]:
    weather_dates = {
        name[:-5]
        for name in os.listdir(weather_dir)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", name)
    }
    sun_counts: dict[str, int] = defaultdict(int)
    for name in os.listdir(sun_dir):
        match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})_([a-z]+)\.html", name)
        if match:
            sun_counts[match.group(1)] += 1
    sun_dates = {date for date, count in sun_counts.items() if count >= len(ZODIAC_SIGNS)}
    dates = sorted(weather_dates & sun_dates)
    if not dates:
        raise SystemExit("No dates found with both Cosmic Weather and all 12 Sun-sign cards.")
    return dates


def _resolve_out_path(args: argparse.Namespace, sun_dir: str, date: str, multi_date: bool) -> str:
    if args.out and not multi_date and args.out.lower().endswith(".png"):
        return os.path.abspath(args.out)
    out_dir = os.path.abspath(args.out) if args.out else os.path.abspath(os.path.join(
        sun_dir,
        "..",
        "daily_briefing_frames",
    ))
    return os.path.join(out_dir, f"{date}_daily_briefing.png")


def _font(size: int, bold: bool = False, italic: bool = False):
    from PIL import ImageFont

    if bold and italic:
        filename = "georgiaz.ttf"
    elif bold:
        filename = "georgiab.ttf"
    elif italic:
        filename = "georgiai.ttf"
    else:
        filename = "georgia.ttf"
    path = os.path.join("C:\\Windows\\Fonts", filename)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _measure(draw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if _measure(draw, trial, font)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _text(draw, xy: tuple[int, int], text: str, font, fill: str, max_width: int | None = None,
          line_gap: int = 6) -> int:
    x, y = xy
    lines = _wrap(draw, text, font, max_width) if max_width else text.splitlines()
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += _measure(draw, line or "Ag", font)[1] + line_gap
    return y


def _center(draw, y: int, text: str, font, fill: str, width: int) -> int:
    text_width, text_height = _measure(draw, text, font)
    draw.text(((width - text_width) / 2, y), text, font=font, fill=fill)
    return y + text_height


def _draw_panel(draw, box: tuple[int, int, int, int], outline: str, fill: str, radius: int = 14) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)


def _draw_frame(path: str, weather: dict[str, str], signs: list[dict[str, str]],
                width: int, height: int) -> None:
    from PIL import Image, ImageDraw

    bg = "#F8F4EE"
    surface = "#F0EBE3"
    border = "#D4CBC0"
    text = "#2A2420"
    muted = "#7A6E66"
    head = "#8A7499"
    gold = "#A57C3A"
    accent = "#5F8C7E"

    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)

    margin = 56
    y = 52
    y = _center(draw, y, "ENTANGLED ORACLE · DAILY ASTRO BRIEFING",
                _font(18), muted, width) + 22
    y = _center(draw, y, weather["date_line"].upper(), _font(56, bold=True), text, width) + 12
    y = _center(draw, y, weather["weekday"], _font(24), gold, width) + 30

    panel_top = y
    panel_bottom = 620
    _draw_panel(draw, (margin, panel_top, width - margin, panel_bottom), border, surface, 18)
    inner_x = margin + 30
    inner_width = width - (margin * 2) - 60
    y = panel_top + 28
    draw.text((inner_x, y), "COSMIC WEATHER", font=_font(18), fill=head)
    y += 34
    draw.text((inner_x, y), weather["sky_headline"], font=_font(34, bold=True), fill=text)
    y += 48
    y = _text(draw, (inner_x, y), weather["sky_body"], _font(22), text, inner_width, 8)
    y += 8
    divider_y = y + 6
    draw.line((inner_x, divider_y, inner_x + inner_width, divider_y), fill=border, width=1)
    y = divider_y + 20
    left_width = int(inner_width * 0.60)
    right_x = inner_x + left_width + 32
    draw.text((inner_x, y), f"The Day's Ruler: {weather['ruler']}", font=_font(22, bold=True), fill=gold)
    _text(draw, (inner_x, y + 34), weather["ruler_body"], _font(18), text, left_width, 6)
    draw.text((right_x, y), "BEST USED FOR", font=_font(16), fill=head)
    _text(draw, (right_x, y + 32), weather["theme"], _font(20, italic=True), text,
          inner_width - left_width - 32, 7)

    y = panel_bottom + 28
    draw.text((margin, y), "SUN SIGN ACTIVATIONS", font=_font(24, bold=True), fill=text)
    draw.text((width - margin - 380, y + 4), "read by your Sun sign", font=_font(20, italic=True), fill=muted)
    y += 44

    cols = 3
    rows = 4
    gap = 14
    grid_w = width - (margin * 2)
    card_w = (grid_w - gap * (cols - 1)) // cols
    card_h = (height - y - 70 - gap * (rows - 1)) // rows
    sign_font = _font(27, bold=True)
    label_font = _font(18)
    inflection_font = _font(16, italic=True)
    body_font = _font(18)

    for index, sign in enumerate(signs):
        row = index // cols
        col = index % cols
        x = margin + col * (card_w + gap)
        cy = y + row * (card_h + gap)
        _draw_panel(draw, (x, cy, x + card_w, cy + card_h), border, "#F4EFE8", 12)
        sx = x + 18
        sy = cy + 18
        draw.text((sx, sy), sign["sign"].upper(), font=sign_font, fill=text)
        sy += 38
        sy = _text(draw, (sx, sy), sign["activation"], label_font, gold, card_w - 36, 4)
        if sign.get("inflection"):
            sy += 4
            sy = _text(draw, (sx, sy), sign["inflection"], inflection_font, head, card_w - 36, 4)
        sy += 6
        _text(draw, (sx, sy), sign["excerpt"], body_font, text, card_w - 36, 6)

    footer_y = height - 42
    draw.text((margin, footer_y), "SAVE · SHARE · READ YOUR SIGN", font=_font(17), fill=muted)
    right = "KSISTI-PUCK LLC · ENTANGLED-ORACLE"
    right_w, _ = _measure(draw, right, _font(17))
    draw.text((width - margin - right_w, footer_y), right, font=_font(17), fill=muted)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)


def main(argv=None) -> int:
    args = _parse_args(argv)
    sun_dir = os.path.abspath(args.sun_dir)
    weather_dir = os.path.abspath(args.weather_dir)
    if not os.path.isdir(sun_dir):
        raise SystemExit(f"Not a directory: {sun_dir}")
    if not os.path.isdir(weather_dir):
        raise SystemExit(f"Not a directory: {weather_dir}")

    dates = _resolve_dates(args, sun_dir, weather_dir)
    sun_manifest = _load_sun_manifest(sun_dir)
    rendered = 0
    for date in dates:
        weather = _load_weather(weather_dir, date)
        signs = _add_inflections(_load_signs(sun_dir, date), date, sun_manifest)
        out = _resolve_out_path(args, sun_dir, date, len(dates) > 1)
        _draw_frame(out, weather, signs, args.width, args.height)
        rendered += 1
        print(f"Rendered combined briefing frame -> {out}")
    print(f"Rendered {rendered} combined briefing frame(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
