"""Consumer-facing report availability for the private beta studio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportDefinition:
    key: str
    label: str
    promise: str
    best_for: str
    depth: str
    birth_time_rule: str
    status: str
    available: bool
    content_packs: tuple[str, ...] = ("plainspeak",)
    default_content_pack: str = "plainspeak"
    allow_unknown_time: bool = False
    report_date_label: str = "Report start date"


CONSUMER_REPORTS: dict[str, ReportDefinition] = {
    "year_ahead": ReportDefinition(
        key="year_ahead",
        label="Year Ahead",
        promise="A flagship annual timing report with major themes, monthly movement, and meaningful windows.",
        best_for="A structured map of the year without pretending the map is fate.",
        depth="Deep",
        birth_time_rule="Exact birth time required",
        status="Private beta studio",
        available=True,
        content_packs=("plainspeak", "entangled_oracle"),
        default_content_pack="plainspeak",
        report_date_label="Year begins",
    ),
    "personal_forecast": ReportDefinition(
        key="personal_forecast",
        label="Personal Forecast",
        promise="A focused reading for current activations, active pressures, and near-term windows.",
        best_for="Present-tense life weather and practical timing awareness.",
        depth="Medium-deep",
        birth_time_rule="Exact birth time required",
        status="Private beta studio",
        available=True,
        content_packs=("plainspeak", "entangled_oracle"),
        default_content_pack="plainspeak",
    ),
    "soul_ecosystem": ReportDefinition(
        key="soul_ecosystem",
        label="Soul Ecosystem",
        promise="A deep natal-architecture portrait of internal patterns, archetypes, and living structures.",
        best_for="The strongest demonstration that this is not generic sign-by-sign copy.",
        depth="Deep",
        birth_time_rule="Exact birth time required",
        status="Private beta studio",
        available=True,
    ),
    "horoscope": ReportDefinition(
        key="horoscope",
        label="Daily Horoscope",
        promise="A compact daily orientation tuned to the active sky and chart context.",
        best_for="A smaller check-in once exact and DOB-only behavior is revalidated.",
        depth="Short",
        birth_time_rule="Conditional: DOB-only path requires revalidation",
        status="Deferred validation",
        available=False,
        allow_unknown_time=True,
    ),
    "weekly_horoscope": ReportDefinition(
        key="weekly_horoscope",
        label="Weekly Horoscope",
        promise="A focused seven-day reading for immediate timing and guidance.",
        best_for="A later/internal surface, not the current public beta promise.",
        depth="Short-medium",
        birth_time_rule="Exact birth time recommended",
        status="Runtime-supported, commercially deferred",
        available=False,
    ),
}

BLOCKED_REPORTS = {"predictive_sandbox", "identity_profile"}


def get_report_definition(report_type: str) -> ReportDefinition | None:
    return CONSUMER_REPORTS.get(report_type)


def available_reports() -> list[ReportDefinition]:
    return [report for report in CONSUMER_REPORTS.values() if report.available]


def deferred_reports() -> list[ReportDefinition]:
    return [report for report in CONSUMER_REPORTS.values() if not report.available]

