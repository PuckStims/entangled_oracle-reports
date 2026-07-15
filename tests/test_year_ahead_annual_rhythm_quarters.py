import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import _build_annual_rhythm_quarters


def _month(name: str, short_name: str, arc_score: float, domains: list[dict]) -> dict:
    return {
        "name": name,
        "short_name": short_name,
        "arc_score": arc_score,
        "activated_domains": domains,
    }


def _event(
    transit_planet: str,
    aspect: str,
    natal_target: str,
    natal_target_display: str,
    start: datetime,
    end: datetime,
    score: float = 0.8,
    event_type: str = "transit",
) -> dict:
    return {
        "event_type": event_type,
        "transit_planet": transit_planet,
        "aspect": aspect,
        "natal_target": natal_target,
        "natal_target_display": natal_target_display,
        "entry_datetime": start,
        "leave_datetime": end,
        "combined_intensity_score": score,
    }


def test_annual_rhythm_quarters_restore_summary_and_contour_fields():
    months = [
        _month("July 2026", "Jul", 0.31, [{"domain": "Work / Health / Routine", "score": 0.6}]),
        _month("August 2026", "Aug", 0.28, [{"domain": "Work / Health / Routine", "score": 0.5}]),
        _month("September 2026", "Sep", 0.29, [{"domain": "Relationships / Partnership", "score": 0.4}]),
        _month("October 2026", "Oct", 0.81, [{"domain": "Career / Public Life", "score": 0.8}]),
        _month("November 2026", "Nov", 0.67, [{"domain": "Career / Public Life", "score": 0.7}]),
        _month("December 2026", "Dec", 0.58, [{"domain": "Spirituality / Inner Life / Rest", "score": 0.5}]),
        _month("January 2027", "Jan", 0.48, [{"domain": "Beliefs / Travel / Expansion", "score": 0.5}]),
        _month("February 2027", "Feb", 0.42, [{"domain": "Beliefs / Travel / Expansion", "score": 0.4}]),
        _month("March 2027", "Mar", 0.62, [{"domain": "Career / Public Life", "score": 0.6}]),
        _month("April 2027", "Apr", 0.54, [{"domain": "Relationships / Partnership", "score": 0.5}]),
        _month("May 2027", "May", 0.57, [{"domain": "Relationships / Partnership", "score": 0.5}]),
        _month("June 2027", "Jun", 0.59, [{"domain": "Work / Health / Routine", "score": 0.7}]),
    ]
    all_events = [
        _event(
            "Saturn",
            "Conjunction",
            "Mercury",
            "your Mercury in the 12th house",
            datetime(2026, 9, 12, tzinfo=timezone.utc),
            datetime(2027, 2, 28, tzinfo=timezone.utc),
            0.82,
        ),
        _event(
            "Neptune",
            "Conjunction",
            "Sun",
            "your Sun in the 12th house",
            datetime(2026, 8, 4, tzinfo=timezone.utc),
            datetime(2026, 12, 31, tzinfo=timezone.utc),
            0.76,
        ),
    ]
    house_domains = {
        5: "Creativity / Pleasure",
        6: "Work / Health / Routine",
        7: "Relationships / Partnership",
        9: "Beliefs / Travel / Expansion",
        10: "Career / Public Life",
        12: "Spirituality / Inner Life / Rest",
    }

    quarters = _build_annual_rhythm_quarters(months, all_events, house_domains)

    assert len(quarters) == 4
    assert quarters[0]["season_name"] == "Jul to Sep: Shared Rhythm"
    assert "shared movement" in quarters[0]["summary"]
    assert quarters[0]["peak_month"] == "July 2026"
    assert quarters[0]["quiet_month"] == "August 2026"
    assert quarters[1]["season_name"] == "October 2026 Carries the Emphasis"
    assert "strongest concentration gathers in October 2026" in quarters[1]["summary"]
    assert quarters[1]["quiet_month"] == "December 2026"
