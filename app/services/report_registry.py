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
    needs_destination: bool = False
    destination_label: str = "Destination"
    destination_help: str = ""


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
    "identity_profile": ReportDefinition(
        key="identity_profile",
        label="Identity Profile",
        promise="A natal identity report built from the existing Entangled Oracle identity-profile surface.",
        best_for="A core portrait when you want the personal architecture rather than timing.",
        depth="Deep",
        birth_time_rule="Exact birth time required",
        status="Local generator",
        available=True,
        content_packs=("plainspeak", "entangled_oracle"),
        default_content_pack="plainspeak",
    ),
    "internal_architecture": ReportDefinition(
        key="internal_architecture",
        label="Internal Architecture",
        promise="A symbolic operating map for signal, decision tempo, energy economy, boundaries, pressure patterns, and restoration keys.",
        best_for="Turning the natal chart and EO pattern logic into a practical self-mapping report.",
        depth="Deep",
        birth_time_rule="Exact birth time required",
        status="EIA v0.1",
        available=True,
    ),
    "horoscope": ReportDefinition(
        key="horoscope",
        label="Daily Horoscope",
        promise="A compact daily orientation tuned to the active sky and chart context.",
        best_for="A small daily check-in without building a full report.",
        depth="Short",
        birth_time_rule="Birth time optional; DOB-only uses simple mode",
        status="Local generator",
        available=True,
        allow_unknown_time=True,
        report_date_label="Forecast date",
    ),
    "weekly_horoscope": ReportDefinition(
        key="weekly_horoscope",
        label="Weekly Horoscope",
        promise="A focused seven-day reading for immediate timing and guidance.",
        best_for="A lighter timing report when you want the week rather than the year.",
        depth="Short-medium",
        birth_time_rule="Birth time optional; exact time improves house and angle context",
        status="Local generator",
        available=True,
        allow_unknown_time=True,
        report_date_label="Week begins",
    ),
    "place_resonance": ReportDefinition(
        key="place_resonance",
        label="Place Resonance",
        promise="A single-destination relocated-chart report for how one place emphasizes the natal pattern.",
        best_for="Testing one city, move, trip, or possible home base.",
        depth="Medium-deep",
        birth_time_rule="Exact birth time required",
        status="Location Services",
        available=True,
        needs_destination=True,
        destination_label="Destination",
        destination_help="City, state/country to test as the relocated place.",
    ),
    "place_resonance_search": ReportDefinition(
        key="place_resonance_search",
        label="Place Resonance Search",
        promise="A curated location search across the packaged candidate catalog.",
        best_for="Finding a shortlist before choosing individual places to inspect.",
        depth="Medium-deep",
        birth_time_rule="Exact birth time required",
        status="Location Services",
        available=True,
    ),
    "world_lines": ReportDefinition(
        key="world_lines",
        label="World Lines Companion",
        promise="A location-services report for computed angular line proximity around a destination.",
        best_for="Understanding which planetary lines are closest to a place.",
        depth="Medium",
        birth_time_rule="Exact birth time required",
        status="Location Services",
        available=True,
        needs_destination=True,
        destination_label="Destination",
        destination_help="City, state/country where line proximity should be checked.",
    ),
    "local_compass": ReportDefinition(
        key="local_compass",
        label="Local Compass",
        promise="A directional local-space report for one destination or anchor relationship.",
        best_for="A practical directional layer without hand-writing route arguments.",
        depth="Medium",
        birth_time_rule="Exact birth time required",
        status="Location Services",
        available=True,
        needs_destination=True,
        destination_label="Destination",
        destination_help="City, state/country used as the destination bearing.",
    ),
    "living_map": ReportDefinition(
        key="living_map",
        label="Living Map",
        promise="A dynamic location-timing overlay for a destination.",
        best_for="Seeing temporary timing weather over a place baseline.",
        depth="Medium",
        birth_time_rule="Exact birth time required",
        status="Location Services",
        available=True,
        needs_destination=True,
        destination_label="Destination",
        destination_help="City, state/country for the timing overlay.",
    ),
}

BLOCKED_REPORTS = {"predictive_sandbox"}


def get_report_definition(report_type: str) -> ReportDefinition | None:
    return CONSUMER_REPORTS.get(report_type)


def available_reports() -> list[ReportDefinition]:
    return [report for report in CONSUMER_REPORTS.values() if report.available]


def deferred_reports() -> list[ReportDefinition]:
    return [report for report in CONSUMER_REPORTS.values() if not report.available]
