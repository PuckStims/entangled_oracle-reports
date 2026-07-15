"""
Compose one all-signs social tile per date from existing Sun-Sign output.

This is a visual packaging pass only: it reads the generated per-sign HTML cards
and reuses their activation headings and exact activation prose excerpts. It does
not rewrite horoscope copy.

Usage (from C:\\entangled_oracle):
    python products/sun_sign_horoscope/tooling/generate_sun_sign_grid.py output/manual_tests/sun_sign
    python products/sun_sign_horoscope/tooling/generate_sun_sign_grid.py output/manual_tests/sun_sign --date 2026-07-15

Then render the generated grid HTML files with:
    python products/sun_sign_horoscope/tooling/render_cards.py output/manual_tests/sun_sign/grids --size 1080
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from products.sun_sign_horoscope.tooling.sun_sign_engine import (  # noqa: E402
    CARD_INK,
    FRAMES,
    SIGN_GLYPHS,
    ZODIAC_SIGNS,
    _resolve_palette,
)

_TEMPLATE_PATH = os.path.join(
    _PROJECT_ROOT,
    "products",
    "sun_sign_horoscope",
    "templates",
    "sun_sign_grid_card.html",
)

_SENTENCE_RE = re.compile(r".*?(?:[.!?](?=\s|$)|$)", re.S)


class _SunSignCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._class_stack: list[set[str]] = []
        self._current_classes: set[str] = set()
        self._parts: dict[str, list[str]] = defaultdict(list)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = set()
        for name, value in attrs:
            if name == "class" and value:
                classes.update(value.split())
        self._class_stack.append(classes)
        self._current_classes = set().union(*self._class_stack) if self._class_stack else set()

    def handle_endtag(self, tag: str) -> None:
        if self._class_stack:
            self._class_stack.pop()
        self._current_classes = set().union(*self._class_stack) if self._class_stack else set()

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        for key in (
            "sign-name",
            "date-line",
            "moon-line",
            "activation-head",
            "ruler-name",
        ):
            if key in self._current_classes:
                self._parts[key].append(text)
        if "body" in self._current_classes:
            self._parts["body"].append(text)

    def parsed(self) -> dict[str, str]:
        bodies = self._parts.get("body", [])
        return {
            "sign": _joined(self._parts.get("sign-name", [])),
            "display_date": _joined(self._parts.get("date-line", [])),
            "moon_line": _joined(self._parts.get("moon-line", [])),
            "activation_head": _joined(self._parts.get("activation-head", [])),
            "activation_block": bodies[1] if len(bodies) > 1 else "",
            "day_ruler": _joined(self._parts.get("ruler-name", [])),
        }


def _joined(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part.strip())


def _load_template():
    try:
        from jinja2 import Template
    except ImportError as exc:  # pragma: no cover - environment guard
        raise SystemExit("jinja2 is required.\n  pip install jinja2") from exc
    with open(_TEMPLATE_PATH, "r", encoding="utf-8") as handle:
        return Template(handle.read(), autoescape=True)


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate all-signs grid cards from Sun-Sign output.")
    parser.add_argument("directory", help="Folder containing generated sun-sign *.html files.")
    parser.add_argument("--date", default=None, help="Limit to one date, YYYY-MM-DD.")
    parser.add_argument("--out", default=None, help="Output directory. Default: <directory>/grids")
    parser.add_argument("--palette", default=None, choices=["vibrant", "muted", "twilight"],
                        help="Override palette. Defaults to manifest palette, then muted.")
    parser.add_argument("--frame", default=None, choices=["sun", "moon"],
                        help="Override frame. Defaults to manifest frame, then sun.")
    parser.add_argument("--excerpt-sentences", type=int, default=1,
                        help="Exact activation sentences to include per sign (default 1).")
    parser.add_argument("--width", type=int, default=1080, help="Card width in px (default 1080).")
    parser.add_argument("--height", type=int, default=1350, help="Card height in px (default 1350).")
    parser.add_argument("--force", action="store_true", help="Overwrite existing grid HTML files.")
    return parser.parse_args(argv)


def _read_manifest(directory: str) -> dict:
    path = os.path.join(directory, "manifest.json")
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _exact_sentence_excerpt(text: str, sentence_count: int) -> str:
    text = " ".join(text.split())
    if sentence_count <= 0:
        return text
    matches = [match.group(0).strip() for match in _SENTENCE_RE.finditer(text) if match.group(0).strip()]
    excerpt = " ".join(matches[:sentence_count]).strip()
    return excerpt or text


def _read_card(path: str) -> dict[str, str]:
    parser = _SunSignCardParser()
    with open(path, "r", encoding="utf-8") as handle:
        parser.feed(handle.read())
    return parser.parsed()


def _posts_by_date(manifest: dict, directory: str) -> dict[str, list[dict]]:
    posts = manifest.get("posts")
    if posts:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for post in posts:
            grouped[post["date"]].append(post)
        return grouped

    grouped = defaultdict(list)
    for filename in os.listdir(directory):
        if not filename.endswith(".html") or "_" not in filename:
            continue
        stem = filename[:-5]
        date_part, sign_part = stem.rsplit("_", 1)
        grouped[date_part].append({
            "date": date_part,
            "sign": sign_part.capitalize(),
            "html": filename,
        })
    return grouped


def _render_date(template, directory: str, out_dir: str, date: str, posts: list[dict],
                 manifest: dict, args: argparse.Namespace) -> str | None:
    by_sign = {post["sign"]: post for post in posts}
    missing = [sign for sign in ZODIAC_SIGNS if sign not in by_sign]
    if missing:
        print(f"  ! {date}: missing {', '.join(missing)}, skipping")
        return None

    palette_name = args.palette or manifest.get("palette") or "muted"
    frame = args.frame or manifest.get("frame") or "sun"
    frame_info = FRAMES.get(frame, FRAMES["sun"])
    signs = []
    first_card = None

    for sign in ZODIAC_SIGNS:
        html_path = os.path.join(directory, by_sign[sign]["html"])
        parsed = _read_card(html_path)
        if first_card is None:
            first_card = parsed
        signs.append({
            "sign": sign,
            "glyph": SIGN_GLYPHS[sign] + "\ufe0e",
            "activation_head": parsed["activation_head"],
            "excerpt": _exact_sentence_excerpt(parsed["activation_block"], args.excerpt_sentences),
        })

    html_name = f"{date}_all_signs.html"
    out_path = os.path.join(out_dir, html_name)
    if os.path.exists(out_path) and not args.force:
        print(f"  - {html_name} exists, skipping (use --force)")
        return out_path

    page = template.render(
        width=args.width,
        height=args.height,
        iso_date=date,
        display_date=(first_card or {}).get("display_date", date),
        moon_phase=(first_card or {}).get("moon_line", "").split(" in ")[0],
        moon_sign=(first_card or {}).get("moon_line", "").split(" in ")[-1],
        day_ruler=(first_card or {}).get("day_ruler", ""),
        frame_label=frame_info["label"],
        frame_anchor=frame_info["anchor_word"],
        palette=_resolve_palette(palette_name),
        ink=CARD_INK.get(palette_name, CARD_INK["muted"]),
        signs=signs,
    )
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(page)
    print(f"  {html_name}")
    return out_path


def main(argv=None) -> int:
    args = _parse_args(argv)
    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        raise SystemExit(f"Not a directory: {directory}")

    manifest = _read_manifest(directory)
    grouped = _posts_by_date(manifest, directory)
    dates = [args.date] if args.date else sorted(grouped)
    missing_date = [date for date in dates if date not in grouped]
    if missing_date:
        raise SystemExit(f"No sun-sign cards found for: {', '.join(missing_date)}")

    out_dir = os.path.abspath(args.out or os.path.join(directory, "grids"))
    os.makedirs(out_dir, exist_ok=True)
    template = _load_template()

    rendered = 0
    for date in dates:
        if _render_date(template, directory, out_dir, date, grouped[date], manifest, args):
            rendered += 1

    print(f"Generated {rendered} grid HTML file(s) -> {out_dir}")
    print("Next: render PNGs with")
    print(f'  python products/sun_sign_horoscope/tooling/render_cards.py "{out_dir}" --size {args.width}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
