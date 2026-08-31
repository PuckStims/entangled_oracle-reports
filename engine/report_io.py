"""Report generation I/O and timing helpers."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def reset_swiss_ephemeris_path(base_dir: str) -> None:
    """Keep long-lived web sessions pinned to the repo ephemeris directory."""
    try:
        import swisseph as swe
    except ImportError:
        return
    swe.set_ephe_path(os.path.join(base_dir, "ephemeris"))


def add_one_year(start: datetime) -> datetime:
    """Returns the same calendar date one year later, with leap-day safety."""
    try:
        return start.replace(year=start.year + 1)
    except ValueError:
        return start.replace(year=start.year + 1, month=2, day=28)


def align_to_day_start(moment: datetime) -> datetime:
    """Returns UTC midnight for the calendar day containing moment."""
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def align_to_week_start(moment: datetime) -> datetime:
    """Returns UTC midnight of the Monday in the same calendar week as moment."""
    day_start = align_to_day_start(moment)
    return day_start - timedelta(days=day_start.weekday())


def report_window(report_type: str, report_start: datetime) -> tuple[datetime, datetime]:
    """
    Returns (report_start, report_end) for a report type's forecast window.

    weekly_horoscope starts on the report/generation date and covers seven
    full calendar days. That keeps the product from forcing a Monday-Friday
    work-week layout when it is created on a different day.
    """
    if report_type == "weekly_horoscope":
        day_start = align_to_day_start(report_start)
        return day_start, day_start + timedelta(days=7)
    return report_start, add_one_year(report_start)


def stdout_report_paths_enabled() -> bool:
    return env_flag("EO_STDOUT_REPORT_PATHS")


def stdout_verbose_enabled() -> bool:
    return env_flag("EO_VERBOSE_STDOUT")


def log_verbose(message: str) -> None:
    if stdout_verbose_enabled():
        print(message)


def atomic_write_text(path: str, content: str) -> None:
    directory = os.path.dirname(path) or "."
    Path(directory).mkdir(parents=True, exist_ok=True)
    temp_name = f".{os.path.basename(path)}.{uuid.uuid4().hex}.tmp"
    temp_path = os.path.join(directory, temp_name)
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def default_output_filename(report_type: str, birth_data: dict, report_start: datetime) -> str:
    safe_name = birth_data["name"].replace(" ", "_").lower()
    timestamp = report_start.strftime("%Y%m%d_%H%M%S")
    request_id = uuid.uuid4().hex[:8]
    return f"{safe_name}_{report_type}_{timestamp}_{request_id}.html"


def default_synastry_output_filename(person_a: dict, person_b: dict) -> str:
    safe_a = str(person_a.get("name", "person_a")).replace(" ", "_").lower()
    safe_b = str(person_b.get("name", "person_b")).replace(" ", "_").lower()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    request_id = uuid.uuid4().hex[:8]
    return f"{safe_a}_{safe_b}_synastry_{timestamp}_{request_id}.html"
