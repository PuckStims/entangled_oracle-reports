"""
Standalone proof-of-concept: generate a Temporal River SVG from real birth data.

Usage:
    cd C:\\entangled_oracle
    python scripts/test_temporal_river_from_birth.py

Output:
    output/test_temporal_river.svg
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# ---------------------------------------------------------------------------
# Path setup — run from C:\entangled_oracle or any directory
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.natal_engine import generate_payload
from engine.transit_engine import compute_year_ahead_events
from engine.temporal_river import build_temporal_river_data, render_temporal_river_svg

# ---------------------------------------------------------------------------
# Hard-coded test birth data
# ---------------------------------------------------------------------------
BIRTH_DATA = {
    "date": "1992-03-21",
    "time": "08:11",
    "location": "Peoria, IL",
}

# Report window: 12 months starting today
REPORT_START = datetime(2026, 6, 30)
REPORT_END   = REPORT_START + timedelta(days=365)

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

OUTPUT_PATH = os.path.join(ROOT, "output", "test_temporal_river.svg")

# ---------------------------------------------------------------------------
# Theme assignment (mirrors generate._assign_theme logic)
# ---------------------------------------------------------------------------
_NATAL_TARGET_THEMES = {
    "Sun":     "career_visibility",
    "Moon":    "home_foundation",
    "Mercury": "work_health_capacity",
    "Venus":   "relationship_focus",
    "Mars":    "work_health_capacity",
    "Jupiter": "career_visibility",
    "Saturn":  "structural_growth",
    "Uranus":  "identity_direction",
    "Neptune": "inner_life_rest",
    "Pluto":   "transformation",
    "Chiron":  "inner_life_rest",
    "ASC":     "identity_direction",
    "MC":      "career_visibility",
    "Vertex":  "relationship_focus",
    "North_Node": "identity_direction",
    "South_Node": "inner_life_rest",
}

_HOUSE_THEMES = {
    1:  "identity_direction",
    2:  "money_resources",
    4:  "home_foundation",
    5:  "creativity_pleasure",
    6:  "work_health_capacity",
    7:  "relationship_focus",
    8:  "transformation",
    9:  "career_visibility",
    10: "career_visibility",
    11: "identity_direction",
    12: "inner_life_rest",
}

_PLANET_THEMES = {
    "Saturn":  "structural_growth",
    "Uranus":  "transformation",
    "Neptune": "inner_life_rest",
    "Pluto":   "transformation",
    "Jupiter": "career_visibility",
    "Mars":    "work_health_capacity",
}


def _assign_theme(event: dict) -> str:
    target = event.get("natal_target", "")
    if target in _NATAL_TARGET_THEMES:
        return _NATAL_TARGET_THEMES[target]
    house = event.get("natal_house")
    if house in _HOUSE_THEMES:
        return _HOUSE_THEMES[house]
    planet = event.get("transit_planet", "")
    return _PLANET_THEMES.get(planet, "default")


# ---------------------------------------------------------------------------
# Aggregate events → 12 monthly records
# ---------------------------------------------------------------------------
def events_to_months(all_events: list, start: datetime) -> list:
    """
    Group events by calendar month within the 12-month window.
    Each month record gets:
      - label:  3-letter abbreviation
      - score:  highest combined_intensity_score in that month (0.0–1.0)
      - theme:  theme of the strongest event, or "default"
    """
    buckets: dict[int, list] = defaultdict(list)

    for ev in all_events:
        raw_date = ev.get("peak_date") or ev.get("peak_datetime")
        if raw_date is None:
            continue
        if isinstance(raw_date, str):
            # Try ISO first ("2026-06-30"), then long form ("June 30, 2026")
            for fmt in ("%Y-%m-%d", "%B %d, %Y"):
                try:
                    ev_date = datetime.strptime(raw_date[:10] if fmt == "%Y-%m-%d" else raw_date, fmt)
                    break
                except ValueError:
                    continue
            else:
                continue
        else:
            # strip timezone so arithmetic stays naive
            ev_date = raw_date.replace(tzinfo=None) if hasattr(raw_date, "tzinfo") else raw_date

        # Slot into month index 0–11 relative to report start
        delta_months = (ev_date.year - start.year) * 12 + (ev_date.month - start.month)
        if 0 <= delta_months < 12:
            buckets[delta_months].append(ev)

    months = []
    for i in range(12):
        month_label = MONTH_LABELS[(start.month - 1 + i) % 12]
        evs = buckets.get(i, [])
        if evs:
            best = max(evs, key=lambda e: e.get("combined_intensity_score", 0.0))
            score = best.get("combined_intensity_score", 0.0)
            theme = _assign_theme(best)
        else:
            score = 0.0
            theme = "default"
        months.append({"label": month_label, "score": round(score, 4), "theme": theme})

    return months


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  Temporal River — Proof-of-Concept Runner")
    print("=" * 60)

    # 1. Natal payload
    print(f"\n[1/4] Generating natal chart for {BIRTH_DATA['date']} "
          f"{BIRTH_DATA['time']} — {BIRTH_DATA['location']} ...")
    natal = generate_payload(BIRTH_DATA)
    print(f"      OK Ascendant: {natal['angles']['Ascendant']['formatted']}  "
          f"Sun: {natal['standard_planets']['Sun']['sign']}")

    # 2. Year-ahead transit events
    print(f"\n[2/4] Computing year-ahead events "
          f"({REPORT_START.date()} to {REPORT_END.date()}) ...")
    timeline = compute_year_ahead_events(
        natal,
        start_date=REPORT_START,
        end_date=REPORT_END,
    )
    all_events = timeline.get("all_events", [])
    print(f"      OK {len(all_events)} events  "
          f"({len(timeline.get('transits', []))} transits, "
          f"{len(timeline.get('ingresses', []))} ingresses, "
          f"{len(timeline.get('stations', []))} stations, "
          f"{len(timeline.get('eclipses', []))} eclipses)")

    # 3. Monthly aggregation
    print("\n[3/4] Aggregating events into 12 monthly records ...")
    months = events_to_months(all_events, REPORT_START)
    for m in months:
        bar = "#" * int(m["score"] * 20)
        print(f"      {m['label']:>3}  {m['score']:.3f}  {bar:<20}  {m['theme']}")

    # 4. Build river data + render SVG
    print("\n[4/4] Building Temporal River SVG ...")
    river_data = build_temporal_river_data(months, palette_name="vibrant")
    svg = render_temporal_river_svg(river_data, variant="medium", show_labels=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"\n      OK Saved -> {OUTPUT_PATH}")
    print("\n" + "=" * 60)
    print("  Done!  Open the SVG in a browser to view.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
