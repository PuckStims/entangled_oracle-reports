"""
Sun-Sign Horoscope engine — newspaper-column style.

Unlike the personalized Daily Horoscope (which needs a real birth chart to know
which natal house a transit falls in), this produces ONE reading per zodiac sign
using SOLAR HOUSES: each sign is treated as its own 1st house, and the day's real
transiting planets are mapped into houses *relative to that sign*. No birth time,
no birth date — just the sign.

This lets us reuse the existing Daily Horoscope block libraries verbatim:
  - products/daily_horoscope/blocks/your_activation.json  (transit_planet x house)
  - products/daily_horoscope/blocks/todays_sky.json        (moon_phase x element)
  - products/daily_horoscope/blocks/day_ruler.json         (weekday ruler)

The sky (moon phase, moon sign, day ruler, featured transit) is computed ONCE per
day; only the solar house of the featured transit differs from sign to sign.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

# Make the project root importable when run from anywhere.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import swisseph as swe  # noqa: E402

from config import HOUSE_DOMAINS, PALETTES  # noqa: E402

# The card colors its glyph and section headers with accent "ink". The base
# palettes' accent colors are tuned as fills, not as text — on the muted (cream)
# palette they'd be nearly invisible — so the card uses its own readable accents:
# bright on the dark vibrant palette, soft earthy tones on the light muted one.
CARD_INK = {
    "vibrant": {"accent": "#00FFB2", "head": "#BF7FFF", "gold": "#FFD000"},
    "muted":   {"accent": "#5F8C7E", "head": "#8A7499", "gold": "#A57C3A"},
    # Cool twilight ink for the Moon-sign frame (internal landscape).
    "twilight": {"accent": "#5F7A99", "head": "#74749A", "gold": "#93826B"},
}

# Card-local palettes not in config. "twilight" is a soft, cool light scheme so
# the Moon-sign line reads distinctly from the warm cream Sun-sign line in-feed.
CARD_PALETTES = {
    "twilight": {
        "bg": "#EDEFF5", "surface": "#E4E8F1", "surface_2": "#DBE0EC",
        "border": "#CBD2E0", "text": "#262B36", "muted": "#6E7688",
        "subtle": "#9AA2B2",
        # legacy aliases used by the template
        "accent": "#5F7A99", "purple": "#74749A", "gold": "#93826B",
    },
}


def _resolve_palette(palette_name: str) -> dict:
    if palette_name in CARD_PALETTES:
        return CARD_PALETTES[palette_name]
    return PALETTES.get(palette_name, PALETTES["vibrant"])
from selectors.utils import get_sign_element  # noqa: E402
from selectors.block_selector import select_block  # noqa: E402
from formulas.standard_indexes import get_day_ruler  # noqa: E402
from engine.transit_engine import _whole_sign_house, _planet_state  # noqa: E402


ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_GLYPHS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}

SIGN_DATE_RANGES = {
    "Aries": "Mar 21 – Apr 19", "Taurus": "Apr 20 – May 20",
    "Gemini": "May 21 – Jun 20", "Cancer": "Jun 21 – Jul 22",
    "Leo": "Jul 23 – Aug 22", "Virgo": "Aug 23 – Sep 22",
    "Libra": "Sep 23 – Oct 22", "Scorpio": "Oct 23 – Nov 21",
    "Sagittarius": "Nov 22 – Dec 21", "Capricorn": "Dec 22 – Jan 19",
    "Aquarius": "Jan 20 – Feb 18", "Pisces": "Feb 19 – Mar 20",
}

_BODY_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
}

# Sun-Moon separation -> 8 named phases (same thresholds the resolver uses).
_PHASE_NAMES = [
    (45, "New Moon"), (90, "Waxing Crescent"), (135, "First Quarter"),
    (180, "Waxing Gibbous"), (225, "Full Moon"), (270, "Waning Gibbous"),
    (315, "Last Quarter"), (360, "Balsamic"),
]

_PHASE_KEYS = {
    "New Moon": "new_moon", "Waxing Crescent": "waxing_crescent",
    "First Quarter": "first_quarter", "Waxing Gibbous": "waxing_gibbous",
    "Full Moon": "full_moon", "Waning Gibbous": "waning_gibbous",
    "Last Quarter": "last_quarter", "Balsamic": "balsamic",
}

# Which planet "activates" the day is a sky-only decision here (there is no natal
# chart to aspect). We feature the tightest aspect the day forms between a fast
# mover and any other planet, so the featured planet rotates day to day. The fast
# mover is reported because its solar house shifts most across signs and dates.
_FEATURE_PLANETS = ["Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
_FAST_MOVERS = {"Sun", "Mercury", "Venus", "Mars"}
_FEATURE_ORB = 6.0  # generous — this is a flavor pick, not a dated precision event
_ASPECT_ANGLES = [("Conjunction", 0), ("Opposition", 180), ("Square", 90),
                  ("Trine", 120), ("Sextile", 60)]

# Ranks which partner is thematically "louder" when two planets aspect.
_SIGNIFICANCE = {
    "Sun": 0.65, "Mercury": 0.45, "Venus": 0.50, "Mars": 0.55, "Jupiter": 0.75,
    "Saturn": 0.85, "Uranus": 0.90, "Neptune": 0.95, "Pluto": 1.00,
}


def _noon_utc(date: datetime) -> datetime:
    """Anchor every reading to 12:00 UTC so a calendar day has one stable sky."""
    return date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def _aspect_orb(sep: float) -> tuple[str, float] | None:
    """Nearest major aspect within _FEATURE_ORB, or None."""
    best = None
    for name, angle in _ASPECT_ANGLES:
        orb = abs(sep - angle)
        if orb <= _FEATURE_ORB and (best is None or orb < best[1]):
            best = (name, orb)
    return best


def _pick_feature(longitudes: dict[str, float]) -> dict:
    """
    Choose the day's featured transit from real sky positions only.

    Returns {"planet", "longitude", "partner", "aspect"} — planet is a fast mover
    whose solar house we look up per sign. Falls back to the Sun when no aspect is
    within orb (the Sun is always meaningful and always present).
    """
    best = None  # (score, planet, partner, aspect)
    # Only consider the feature planets (Sun..Pluto). The Moon is intentionally
    # excluded here — it already headlines the Today's Sky section.
    names = [p for p in _FEATURE_PLANETS if p in longitudes]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a not in _FAST_MOVERS and b not in _FAST_MOVERS:
                continue  # keep the feature rotating quickly
            sep = abs(longitudes[a] - longitudes[b]) % 360
            if sep > 180:
                sep = 360 - sep
            hit = _aspect_orb(sep)
            if not hit:
                continue
            aspect, orb = hit
            score = max(_SIGNIFICANCE[a], _SIGNIFICANCE[b]) * (1.0 - orb / _FEATURE_ORB)
            # Report the fast mover (its house moves most); if both fast, the louder one.
            fast_candidates = [p for p in (a, b) if p in _FAST_MOVERS]
            planet = max(fast_candidates, key=_SIGNIFICANCE.get)
            partner = b if planet == a else a
            if best is None or score > best[0]:
                best = (score, planet, partner, aspect)

    if best is None:
        return {"planet": "Sun", "longitude": longitudes["Sun"],
                "partner": None, "aspect": None}
    _score, planet, partner, aspect = best
    return {"planet": planet, "longitude": longitudes[planet],
            "partner": partner, "aspect": aspect}


def compute_day_sky(date: datetime) -> dict:
    """
    Compute the shared, sign-independent sky for one calendar day.

    Everything here is identical for all twelve signs; only the featured planet's
    solar house (computed later, per sign) changes.
    """
    moment = _noon_utc(date)
    longitudes = {name: _planet_state(bid, moment)["longitude"]
                  for name, bid in _BODY_IDS.items()}

    phase_angle = (longitudes["Moon"] - longitudes["Sun"]) % 360
    phase = next(name for threshold, name in _PHASE_NAMES if phase_angle < threshold)

    moon_sign = ZODIAC_SIGNS[int(longitudes["Moon"] // 30)]

    feature = _pick_feature(longitudes)

    return {
        "date": moment,
        "longitudes": longitudes,
        "moon_phase": phase,
        "moon_phase_key": _PHASE_KEYS[phase],
        "moon_sign": moon_sign,
        "moon_sign_element": get_sign_element(moon_sign),
        "day_ruler": get_day_ruler(moment),
        "feature_planet": feature["planet"],
        "feature_longitude": feature["longitude"],
        "feature_partner": feature["partner"],
        "feature_aspect": feature["aspect"],
    }


# Per-frame framing: which sign the reader anchors on, and the editorial voice.
#   sun  — Sun sign as 1st house; features the day's fast-planet aspect (external
#          events, how the day meets you).
#   moon — Moon sign as 1st house; features the transiting Moon's own house
#          (internal weather, how you meet the day inside).
FRAMES = {
    "sun":  {"label": "Sun Sign", "tagline": "External Identity",
             "anchor_word": "Sun sign"},
    "moon": {"label": "Moon Sign", "tagline": "Internal Landscape",
             "anchor_word": "Moon sign"},
}


def build_sign_reading(sky: dict, sign: str, palette_name: str = "vibrant",
                       frame: str = "sun") -> dict:
    """
    Assemble the medium-length reading for one sign from a precomputed day sky.

    Sections: Today's Sky (shared) - Your Activation (whole-sign house) - Day's Ruler.

    frame="sun"  anchors on the reader's Sun sign and features the day's fast
                 planet. frame="moon" anchors on the reader's Moon sign and
                 features the transiting Moon (its house shifts every ~2.5 days).
    """
    frame_info = FRAMES.get(frame, FRAMES["sun"])
    sign_index = ZODIAC_SIGNS.index(sign)

    if frame == "moon":
        feature_planet = "Moon"
        feature_longitude = sky["longitudes"]["Moon"]
    else:
        feature_planet = sky["feature_planet"]
        feature_longitude = sky["feature_longitude"]

    # Whole-sign houses from the anchor: the sign's 0th degree is its 1st-house cusp.
    house = _whole_sign_house(feature_longitude, sign_index * 30)
    house_name = HOUSE_DOMAINS.get(house, "chart")

    todays_sky_block = select_block(
        "daily_horoscope", "todays_sky",
        sky["moon_phase_key"], sky["moon_sign_element"],
    )
    activation_block = select_block(
        "daily_horoscope", "your_activation",
        feature_planet, str(house),
    )
    day_ruler_block = select_block(
        "daily_horoscope", "day_ruler", sky["day_ruler"],
    )

    return {
        "sign": sign,
        # Trailing U+FE0E (text variation selector) forces monochrome text
        # rendering, so the glyph takes the accent color instead of the OS
        # color-emoji presentation (a bright purple box on Windows).
        "sign_glyph": SIGN_GLYPHS[sign] + "︎",
        "sign_dates": SIGN_DATE_RANGES[sign],
        "date": sky["date"],
        "display_date": sky["date"].strftime("%A, %B %d, %Y"),
        "iso_date": sky["date"].strftime("%Y-%m-%d"),
        "moon_phase": sky["moon_phase"],
        "moon_sign": sky["moon_sign"],
        "todays_sky_block": todays_sky_block,
        "activation_planet": feature_planet,
        "activation_house": house,
        "activation_house_name": house_name,
        "activation_block": activation_block,
        "day_ruler_name": sky["day_ruler"],
        "day_ruler_block": day_ruler_block,
        "frame": frame,
        "frame_label": frame_info["label"],
        "frame_tagline": frame_info["tagline"],
        "palette_name": palette_name,
        "palette": _resolve_palette(palette_name),
        "ink": CARD_INK.get(palette_name, CARD_INK["vibrant"]),
    }


def build_caption(reading: dict) -> str:
    """Facebook caption (the text half of each post)."""
    read_by = "read by your Moon sign" if reading["frame"] == "moon" else "read by your Sun sign"
    return (
        f"{reading['sign_glyph']} {reading['sign'].upper()} "
        f"({reading['frame_label']} · {read_by}) · {reading['display_date']}\n\n"
        f"{reading['activation_planet']} moves through your "
        f"{reading['activation_house_name']}. {reading['activation_block']}\n\n"
        f"Today's sky: {reading['moon_phase']} in {reading['moon_sign']}. "
        f"The day's ruler is {reading['day_ruler_name']}.\n\n"
        f"— Entangled Oracle"
    )
