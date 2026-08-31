from datetime import datetime, timezone

from engine import report_io


def test_report_window_weekly_starts_on_report_day():
    report_start = datetime(2026, 7, 15, 14, 30, tzinfo=timezone.utc)

    start, end = report_io.report_window("weekly_horoscope", report_start)

    assert start == datetime(2026, 7, 15, tzinfo=timezone.utc)
    assert end == datetime(2026, 7, 22, tzinfo=timezone.utc)


def test_add_one_year_handles_leap_day():
    assert report_io.add_one_year(datetime(2024, 2, 29)) == datetime(2025, 2, 28)


def test_default_output_filename_contains_safe_identity_and_report_type():
    filename = report_io.default_output_filename(
        "year_ahead",
        {"name": "Test Client"},
        datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    )

    assert filename.startswith("test_client_year_ahead_20260102_030405_")
    assert filename.endswith(".html")
