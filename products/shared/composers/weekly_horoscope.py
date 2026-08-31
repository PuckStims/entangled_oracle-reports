"""Weekly Horoscope context -> shared document model."""
from __future__ import annotations

from typing import Any

from ..document_model import CoverSection, MethodologyNote, ParityEntry, ReportDocument, ReportFooter, ReportHeader, Section, SupportCard
from ._helpers import footer, metadata, paragraphs, text


def compose_weekly_horoscope(context: dict[str, Any]) -> ReportDocument:
    subject = text(context.get("querent_name"))
    span = " - ".join(filter(None, (text(context.get("week_start_display")), text(context.get("week_end_display")))))
    nodes: list[Any] = [CoverSection(ReportHeader("Weekly Horoscope", subject or None, metadata(("Week", span), ("Generated", context.get("generation_date")))), marker="cover")]
    nodes.append(Section("Weekly Theme", tuple(paragraphs(context.get("weekly_theme_headline"))) + tuple(paragraphs(context.get("weekly_theme_overview"))), marker="theme"))
    work_with = text(context.get("weekly_work_with"))
    watch_for = tuple(text(item) for item in context.get("weekly_watch_for", []) if text(item))
    if work_with or watch_for:
        nodes.append(Section("How to Work With This Week", tuple(paragraphs(work_with)) + ((SupportCard("Watch for", " | ".join(watch_for), tone="threshold"),) if watch_for else ()), marker="guidance"))
    day_nodes: list[Any] = []
    for day in context.get("weekly_days", []) or []:
        if not isinstance(day, dict):
            continue
        moments: list[Any] = []
        for moment in day.get("moments", []) or []:
            if not isinstance(moment, dict):
                continue
            body = " ".join(filter(None, (text(moment.get("meaning_primary")), text(moment.get("guidance_line")), text(moment.get("technical_meta")))))
            moments.append(SupportCard(text(moment.get("technical_label")) or text(moment.get("day_label")) or "Timing moment", body, metadata(("When", " ".join(filter(None, (text(moment.get("day_label")), text(moment.get("time_label"))))))), text(moment.get("tone")) or None))
        day_nodes.append(Section(text(day.get("day_label")) or "Forecast day", tuple(paragraphs(day.get("guidance"))) + tuple(moments), kicker=text(day.get("movement_label")) or None))
    nodes.append(Section("The Week as It Arrives", tuple(day_nodes) or tuple(paragraphs(context.get("weekly_scope_note"))), marker="days"))
    basis = text(context.get("weekly_simplified_output_contract"))
    if basis:
        nodes.append(Section("Calculation Basis", (MethodologyNote(basis), MethodologyNote(text(context.get("weekly_narrative_basis"))), MethodologyNote(" ".join(text(value) for value in context.get("weekly_complexity_capacity", []) if text(value)))), marker="methodology"))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument("Weekly Horoscope", tuple(nodes), subject or None, text(context.get("generation_date")) or None, text(context.get("methodology_id")) or None, "weekly_horoscope", text(context.get("palette_name")) or "vibrant", parity_manifest=(ParityEntry("theme", "weekly_theme_overview"), ParityEntry("guidance", "weekly_work_with"), ParityEntry("days", "weekly_days")))
