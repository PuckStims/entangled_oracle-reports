import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import _build_turning_point_timeline


def _months():
    return [
        {"name": "June 2026", "short_name": "Jun"},
        {"name": "July 2026", "short_name": "Jul"},
        {"name": "August 2026", "short_name": "Aug"},
    ]


def _landmarks():
    return [
        {
            "title": "Saturn Sextile natal Saturn",
            "peak_date": "June 10, 2026",
            "peak_datetime": datetime(2026, 6, 10, tzinfo=timezone.utc),
            "active_period": "Active from June 01, 2026 through August 14, 2026 · 74-day active window",
            "intensity_bar": "◆",
            "intensity_label": "Significant",
            "natal_target_display": "Saturn in Virgo",
            "related_month": "June 2026",
            "why_it_matters": "This marks a durable restructuring period around work, health, and long-range maintenance. A second sentence should not carry into the compact timeline.",
            "tone": "challenging",
        },
        {
            "title": "Jupiter Trine natal Sun",
            "peak_date": "July 15, 2026",
            "peak_datetime": datetime(2026, 7, 15, tzinfo=timezone.utc),
            "active_period": "Active from July 02, 2026 through August 01, 2026 · 30-day active window",
            "intensity_bar": "✦",
            "intensity_label": "Key Window",
            "natal_target_display": "Sun in Cancer",
            "related_month": "July 2026",
            "why_it_matters": "This widens the year’s available range for momentum and visible movement.",
            "tone": "flowing",
        },
    ]


def test_turning_point_timeline_groups_landmarks_by_forecast_month():
    timeline = _build_turning_point_timeline(_months(), _landmarks())

    assert [month["name"] for month in timeline] == ["June 2026", "July 2026"]
    assert timeline[0]["entries"][0]["title"] == "Saturn Sextile natal Saturn"
    assert timeline[1]["entries"][0]["intensity_label"] == "✦ Key Window"


def test_turning_point_timeline_reason_line_stays_compact():
    timeline = _build_turning_point_timeline(_months(), _landmarks())
    reason = timeline[0]["entries"][0]["reason_line"]

    assert "durable restructuring period" in reason
    assert "A second sentence" not in reason
    assert timeline[0]["entries"][0]["natal_target"] == "Saturn in Virgo"


if __name__ == "__main__":
    test_turning_point_timeline_groups_landmarks_by_forecast_month()
    test_turning_point_timeline_reason_line_stays_compact()
