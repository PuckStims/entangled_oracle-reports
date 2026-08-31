"""Personal Forecast context -> shared document model."""
from __future__ import annotations

from typing import Any

from ..document_model import CalloutBlock, CoverSection, DataTable, Figure, NatalSummaryCard, ParityEntry, PillRow, ReportDocument, ReportFooter, ReportHeader, Section, SupportCard
from ._helpers import cards, footer, metadata, paragraphs, text


def compose_personal_forecast(context: dict[str, Any]) -> ReportDocument:
    subject = text(context.get("querent_name"))
    span = " - ".join(filter(None, (text(context.get("report_start_display")), text(context.get("report_end_display")))))
    nodes: list[Any] = [
        CoverSection(ReportHeader("Personal Forecast", subject or None, metadata(("Forecast span", span), ("Generated", context.get("generation_date")))), marker="cover"),
    ]
    if text(context.get("chart_wheel_svg")):
        nodes.append(Section("Natal Wheel", (Figure("image/svg+xml", context.get("chart_wheel_svg"), "Natal chart wheel", semantic_role="natal_chart_wheel", fallback_text="Natal wheel retained as a visual source; chart positions are listed below."), PillRow(tuple(text(item) for item in context.get("wheel_transit_retrograde_planets", []) if text(item)))), marker="natal-wheel"))
    wheel = context.get("chart_wheel_data") or {}
    bodies = wheel.get("bodies") or []
    reference_nodes: list[Any] = [NatalSummaryCard("Report record", metadata(("Subject", subject), ("Forecast span", span), ("Birth date", context.get("birth_date_display")), ("Birth location", context.get("birth_location")), ("Birth-time confidence", context.get("birth_time_confidence")), ("Version", context.get("report_version"))))]
    if bodies:
        reference_nodes.append(DataTable(("Point", "Position", "House"), tuple((text(body.get("name")).replace("_", " "), text(body.get("position")), text(body.get("house")) or "-") for body in bodies if isinstance(body, dict)), caption="Natal positions"))
    nodes.append(Section("This Forecast, At a Glance", tuple(reference_nodes), marker="record"))
    opening: list[Any] = paragraphs(context.get("opening_snapshot"))
    if context.get("retrograde_cluster_active") and text(context.get("retrograde_cluster_block")):
        opening.append(CalloutBlock("Current Retrograde Climate", text(context.get("retrograde_cluster_block")), "threshold"))
    if context.get("voc_next_active") and text(context.get("voc_next_block")):
        opening.append(CalloutBlock("Next Void-of-Course Moon", text(context.get("voc_next_block")), "threshold"))
    nodes.append(Section("Your Next 90 Days", tuple(opening), marker="opening"))
    theme_nodes: list[Any] = []
    for theme in context.get("themes", []) or []:
        if not isinstance(theme, dict):
            continue
        body = "\n\n".join(filter(None, (text(theme.get("body")), f"Practical application: {text(theme.get('action'))}" if text(theme.get("action")) else "")))
        support = theme.get("supporting_events") or []
        theme_nodes.append(SupportCard(text(theme.get("title")) or text(theme.get("theme_label")), body, metadata(("Anchor", (theme.get("anchor_event") or {}).get("peak_date")), ("Theme", theme.get("theme_label"))), text(theme.get("character")) or None))
        theme_nodes.extend(cards(support, title_key="label", body_keys=()))
    nodes.append(Section("Themes in Motion", tuple(theme_nodes), marker="themes"))
    timing = context.get("timing_windows") or []
    if timing:
        nodes.append(Section("Timing Windows", (DataTable(("Date", "Theme", "Best use", "Intensity"), tuple((text(item.get("date_label")), text(item.get("theme")), text(item.get("best_use")), text(item.get("intensity"))) for item in timing if isinstance(item, dict))),), marker="timing"))
    featured = context.get("featured_event") or {}
    if featured:
        feature_body = "\n\n".join(text(featured.get(key)) for key in ("body_1", "body_2", "body_3", "action") if text(featured.get(key)))
        nodes.append(Section("Featured Event", (SupportCard(text(featured.get("title")), feature_body, metadata(("Date", featured.get("peak_date"))), "highlight"),), marker="featured"))
    guidance = [SupportCard("Professional", text(context.get("guidance_professional"))), SupportCard("Relationships", text(context.get("guidance_relationships"))), SupportCard("Capacity", text(context.get("guidance_capacity")))]
    nodes.append(Section("Working With the Forecast", tuple(card for card in guidance if card.body), marker="guidance"))
    predictive = context.get("predictive_report_surface") or {}
    predictive_cards = cards(predictive.get("chapters")) + cards(predictive.get("candidates"))
    if predictive_cards:
        nodes.append(Section("Forecast Evidence Notes", tuple(predictive_cards), marker="predictive"))
    nodes.append(Section("Closing Integration", tuple(paragraphs(context.get("closing_integration"))), marker="closing"))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument("Personal Forecast", tuple(nodes), subject or None, text(context.get("generation_date")) or None, text(context.get("methodology_id")) or None, "personal_forecast", text(context.get("palette_name")) or "vibrant", parity_manifest=(ParityEntry("natal-wheel", "chart_wheel_svg"), ParityEntry("opening", "opening_snapshot"), ParityEntry("themes", "themes"), ParityEntry("timing", "timing_windows"), ParityEntry("featured", "featured_event"), ParityEntry("closing", "closing_integration")))
