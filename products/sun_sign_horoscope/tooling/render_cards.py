"""
Render sun-sign horoscope HTML cards to 1080x1080 PNGs for Facebook.

Uses headless Chromium via Playwright so a full month (360 cards) renders
unattended. It screenshots the #card element, so the PNG is exactly the
1080x1080 canvas defined in the template.

Setup (one time):
    pip install playwright
    python -m playwright install chromium

Usage (from C:\\entangled_oracle):
    python products/sun_sign_horoscope/tooling/render_cards.py output/sun_sign_horoscope/2026-07-06_30d
    python products/sun_sign_horoscope/tooling/render_cards.py <dir> --only 2026-07-06_leo.html

Renders every *.html in <dir> (skipping any already-rendered PNG unless --force)
next to its source file.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render sun-sign HTML cards to PNGs.")
    parser.add_argument("directory", help="Folder of generated *.html cards.")
    parser.add_argument("--only", default=None,
                        help="Render just this one HTML filename (within the directory).")
    parser.add_argument("--force", action="store_true",
                        help="Re-render even if the PNG already exists.")
    parser.add_argument("--size", type=int, default=1080,
                        help="Square edge in px (default 1080).")
    return parser.parse_args(argv)


def _targets(directory: str, only: str | None) -> list[str]:
    if only:
        path = os.path.join(directory, only)
        if not os.path.isfile(path):
            raise SystemExit(f"File not found: {path}")
        return [path]
    files = sorted(glob.glob(os.path.join(directory, "*.html")))
    if not files:
        raise SystemExit(f"No .html cards found in {directory}")
    return files


def main(argv=None) -> int:
    args = _parse_args(argv)
    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        raise SystemExit(f"Not a directory: {directory}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is required to render PNGs.\n"
            "Install it with:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        ) from exc

    targets = _targets(directory, args.only)
    rendered = 0
    skipped = 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": args.size, "height": args.size},
            device_scale_factor=1,
        )
        for html_path in targets:
            png_path = os.path.splitext(html_path)[0] + ".png"
            if os.path.exists(png_path) and not args.force:
                skipped += 1
                continue
            page.goto("file:///" + html_path.replace("\\", "/"))
            card = page.query_selector("#card")
            if card is None:
                print(f"  ! no #card element in {os.path.basename(html_path)}, skipping")
                continue
            card.screenshot(path=png_path)
            rendered += 1
            print(f"  {os.path.basename(png_path)}")
        browser.close()

    print(f"Rendered {rendered} PNG(s), skipped {skipped} existing "
          f"(use --force to re-render) in {directory}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
