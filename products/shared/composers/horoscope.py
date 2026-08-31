"""Daily Horoscope context -> shared document model."""
from __future__ import annotations

from typing import Any

from ..document_model import CoverSection, MethodologyNote, NatalSummaryCard, ParityEntry, ReportDocument, ReportFooter, ReportHeader, Section, SupportCard
from ._helpers import footer, metadata, paragraphs, text


def compose_horoscope(context: dict[str, Any]) -> ReportDocument:
    subject = text(context.get("querent_name"))
    nodes: list[Any] = [CoverSection(ReportHeader("Daily Horoscope", subject or None, metadata(("Date", context.get("display_date")), ("Location", context.get("generation_location")))), marker="cover")]
    nodes.append(Section("Today’s Sky", tuple(paragraphs(context.get("todays_sky_block"))) + (NatalSummaryCard("Moon", metadata(("Phase", context.get("moon_phase_descriptor")), ("Sign", context.get("sky_moon_sign") or context.get("moon_sign")))),), marker="today-sky"))
    if not context.get("simple_mode"):
        activation_nodes: list[Any] = [SupportCard("Your Activation", text(context.get("activation_block")), metadata(("Planet", context.get("activation_planet")), ("House", context.get("natal_house_name")), ("Basis", context.get("activation_basis_line"))), "highlight")]
        activation_nodes.extend(paragraphs(context.get("secondary_activation_line")))
        nodes.append(Section("Your Activation", tuple(activation_nodes), marker="activation"))
        nodes.append(Section(text(context.get("day_ruler_name")) or "Day Ruler", tuple(paragraphs(context.get("day_ruler_block"))), marker="day-ruler"))
        if text(context.get("activated_index_name")) or text(context.get("proprietary_block")):
            nodes.append(Section(text(context.get("activated_index_name")) or "EO Reference", tuple(paragraphs(context.get("proprietary_block"))), marker="proprietary"))
    nodes.append(Section("Closing", tuple(paragraphs(context.get("closing_block"))), marker="closing"))
    method = text(context.get("horoscope_simplified_output_contract"))
    if method:
        nodes.append(Section("Calculation Basis", (MethodologyNote(method), MethodologyNote(f"Daily sky positions are calculated using {text(context.get('methodology_label')) or 'Tropical zodiac + Whole Sign houses'} and Swiss Ephemeris positions where available.")), marker="methodology"))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument("Daily Horoscope", tuple(nodes), subject or None, text(context.get("generation_date")) or None, text(context.get("methodology_id")) or None, "horoscope", text(context.get("palette_name")) or "vibrant", parity_manifest=(ParityEntry("today-sky", "todays_sky_block"), ParityEntry("activation", "activation_block", False), ParityEntry("day-ruler", "day_ruler_block", False), ParityEntry("closing", "closing_block")))
