import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import _build_forecast_shape_details, _derive_forecast_shape


def test_derive_forecast_shape_uses_existing_arc_scores():
    months = [
        {"arc_score": 0.10},
        {"arc_score": 0.12},
        {"arc_score": 0.15},
        {"arc_score": 0.16},
        {"arc_score": 0.18},
        {"arc_score": 0.22},
        {"arc_score": 0.28},
        {"arc_score": 0.34},
        {"arc_score": 0.40},
        {"arc_score": 0.48},
        {"arc_score": 0.56},
        {"arc_score": 0.72},
    ]

    assert _derive_forecast_shape(months) == "Late-Year Expansion"


def test_derive_forecast_shape_falls_back_without_enough_months():
    assert _derive_forecast_shape([]) == "A Developing Annual Story"
    assert _derive_forecast_shape([{"arc_score": 0.2}] * 3) == "A Developing Annual Story"


def test_build_forecast_shape_details_handles_empty_and_short_sets():
    empty = _build_forecast_shape_details([])
    short = _build_forecast_shape_details(
        [{"name": "Jan", "short_name": "Jan", "arc_score": 0.2, "arc_label": "Active"}] * 3
    )

    assert empty["label"] == "A Developing Annual Story"
    assert empty["months"] == []
    assert short["label"] == "A Developing Annual Story"
    assert len(short["months"]) == 3


def test_build_forecast_shape_details_handles_flat_curve():
    months = [
        {"name": f"Month {index+1}", "short_name": f"M{index+1}", "arc_score": 0.4, "arc_label": "Active"}
        for index in range(12)
    ]
    details = _build_forecast_shape_details(months)

    assert details["label"] == "A Developing Annual Story"
    assert details["curve_note"] == "Month-level concentration is relatively even across the forecast window."
    assert all(month["normalized_value"] == 100 for month in details["months"])


def test_build_forecast_shape_details_handles_mixed_curve():
    months = [
        {"name": "June 2026", "short_name": "Jun", "arc_score": 0.10, "arc_label": "Supportive"},
        {"name": "July 2026", "short_name": "Jul", "arc_score": 0.12, "arc_label": "Supportive"},
        {"name": "August 2026", "short_name": "Aug", "arc_score": 0.15, "arc_label": "Active"},
        {"name": "September 2026", "short_name": "Sep", "arc_score": 0.16, "arc_label": "Active"},
        {"name": "October 2026", "short_name": "Oct", "arc_score": 0.18, "arc_label": "Active"},
        {"name": "November 2026", "short_name": "Nov", "arc_score": 0.22, "arc_label": "Significant"},
        {"name": "December 2026", "short_name": "Dec", "arc_score": 0.28, "arc_label": "Significant"},
        {"name": "January 2027", "short_name": "Jan", "arc_score": 0.34, "arc_label": "Significant"},
        {"name": "February 2027", "short_name": "Feb", "arc_score": 0.40, "arc_label": "Key Window"},
        {"name": "March 2027", "short_name": "Mar", "arc_score": 0.48, "arc_label": "Key Window"},
        {"name": "April 2027", "short_name": "Apr", "arc_score": 0.56, "arc_label": "Key Window"},
        {"name": "May 2027", "short_name": "May", "arc_score": 0.72, "arc_label": "Key Window"},
    ]
    details = _build_forecast_shape_details(months)

    assert details["label"] == "Late-Year Expansion"
    assert details["peak_month"] == "May 2027 - Key Window"
    assert details["quiet_month"] == "June 2026 - Supportive"
    assert details["peak_season"] == "Integration Season"
    assert details["months"][-1]["normalized_value"] == 100
