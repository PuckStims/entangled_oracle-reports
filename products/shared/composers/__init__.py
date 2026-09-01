"""Explicit registry of report-context composers.

Renderers are deliberately absent from this module: a composer only returns a
format-neutral :class:`ReportDocument`.
"""
from __future__ import annotations

from collections.abc import Callable

from ..document_model import ReportDocument

Composer = Callable[[dict], ReportDocument]


def _year_ahead() -> Composer:
    from .year_ahead import compose_year_ahead
    return compose_year_ahead


COMPOSERS: dict[str, Composer] = {
    "year_ahead": _year_ahead(),
}


def _register_core_composers() -> None:
    from .horoscope import compose_horoscope
    from .identity_profile import compose_identity_profile
    from .internal_architecture import compose_internal_architecture
    from .personal_forecast import compose_personal_forecast
    from .soul_ecosystem import compose_soul_ecosystem
    from .weekly_horoscope import compose_weekly_horoscope
    from .location import compose_location_report
    from .synastry import compose_synastry

    COMPOSERS.update(
        {
            "horoscope": compose_horoscope,
            "weekly_horoscope": compose_weekly_horoscope,
            "personal_forecast": compose_personal_forecast,
            "soul_ecosystem": compose_soul_ecosystem,
            "identity_profile": compose_identity_profile,
            "internal_architecture": compose_internal_architecture,
            "synastry": compose_synastry,
            "location_services.place_resonance": compose_location_report,
            "location_services.place_resonance_search": compose_location_report,
            "location_services.between_places": compose_location_report,
            "location_services.world_lines": compose_location_report,
            "location_services.local_compass": compose_location_report,
            "location_services.living_map": compose_location_report,
        }
    )


_register_core_composers()


def compose_report(report_type: str, context: dict) -> ReportDocument:
    try:
        composer = COMPOSERS[report_type]
    except KeyError as exc:
        raise ValueError(f"No document composer registered for '{report_type}'.") from exc
    return composer(context)
