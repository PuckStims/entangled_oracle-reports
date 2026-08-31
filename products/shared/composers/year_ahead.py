"""Year Ahead context -> shared semantic document composition.

The functions in this module only rearrange already-computed context.  They do
not select prose, calculate astrology, or apply DOCX presentation rules.
"""
from __future__ import annotations

from typing import Any, Iterable

from ..document_model import (
    CalloutBlock,
    CoverSection,
    DataTable,
    EventCard,
    Figure,
    KeyValueRow,
    MethodologyNote,
    MonthSection,
    NatalSummaryCard,
    Paragraph,
    ParityEntry,
    PillRow,
    ProseSection,
    ReportDocument,
    ReportFooter,
    ReportHeader,
    Section,
    SupportCard,
    as_nodes,
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _rows(items: Iterable[dict[str, Any]] | None, *, label: str = "label", value: str = "value") -> tuple[KeyValueRow, ...]:
    return tuple(
        KeyValueRow(_text(item.get(label)), _text(item.get(value)))
        for item in (items or [])
        if isinstance(item, dict) and _text(item.get(label)) and _text(item.get(value))
    )


def _paragraphs(text: Any, tone: str | None = None) -> list[Paragraph]:
    return [Paragraph(part, tone=tone) for part in _text(text).split("\n\n") if part.strip()]


def _metadata(*pairs: tuple[str, Any]) -> tuple[KeyValueRow, ...]:
    return tuple(KeyValueRow(label, _text(value)) for label, value in pairs if _text(value))


def _event_card(event: dict[str, Any]) -> EventCard:
    body = _text(event.get("reader_synthesis") or event.get("block"))
    lens = _text(event.get("constellation_lens"))
    if lens:
        body = "\n\n".join(filter(None, [body, f"Through Your Constellation: {lens}"]))
    metadata = list(_metadata(
        ("Date", event.get("date_label") or event.get("date_window")),
        ("Type", event.get("event_label") or event.get("event_type_label")),
        ("Details", event.get("subtitle")),
        ("Why it matters", event.get("why_this_matters")),
        ("Duration", event.get("duration_descriptor")),
        ("Shared emphasis", event.get("shared_emphasis")),
        ("Conditions", event.get("participating_condition_line")),
    ))
    metadata.extend(_rows(event.get("technical_fields")))
    exact_contacts = event.get("exact_contacts") or []
    if exact_contacts:
        metadata.append(
            KeyValueRow(
                "Exact contacts",
                "; ".join(
                    " - ".join(filter(None, (_text(contact.get("sequence_label")), _text(contact.get("date_label")), _text(contact.get("motion_label")))))
                    for contact in exact_contacts if isinstance(contact, dict)
                ),
            )
        )
    return EventCard(
        title=_text(event.get("title") or event.get("event_label") or "Timing event"),
        body=body,
        metadata=tuple(metadata),
        tone=_text(event.get("tone")) or None,
    )


def _cards_from_items(items: Any, *, title_key: str = "title", body_keys: tuple[str, ...] = ("body", "summary", "description")) -> list[SupportCard]:
    cards: list[SupportCard] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        body = next((_text(item.get(key)) for key in body_keys if _text(item.get(key))), "")
        cards.append(
            SupportCard(
                title=_text(item.get(title_key) or item.get("label") or item.get("name") or "Report detail"),
                body=body,
                metadata=_metadata(
                    ("Period", item.get("months_label")),
                    ("Note", item.get("kicker")),
                    ("Source", item.get("source_label")),
                ),
                tone=_text(item.get("tone")) or None,
            )
        )
    return cards


def _technical_table(section: dict[str, Any]) -> DataTable | None:
    columns = tuple(_text(value) for value in section.get("columns", []) if _text(value))
    raw_rows = section.get("rows", [])
    rows = tuple(tuple(_text(cell) for cell in row) for row in raw_rows if isinstance(row, (list, tuple)))
    return DataTable(columns, rows, caption=_text(section.get("title")) or None) if columns and rows else None


def _monthly_section(month: dict[str, Any]) -> MonthSection:
    nodes: list[Any] = []
    nodes.extend(_paragraphs(month.get("month_overview")))
    nodes.extend(_paragraphs(month.get("snapshot_block")))
    metadata = _metadata(
        ("Forecast range", month.get("range")),
        ("Activity", month.get("arc_label")),
        ("Dominant planet", month.get("dominant_planet")),
        ("Aspect character", month.get("dominant_aspect_character")),
        ("Chapter pace", month.get("chapter_density")),
        ("Chapter focus", month.get("chapter_focus")),
        ("Primary motion", month.get("chapter_driver")),
        ("Earliest major window", month.get("chapter_signal")),
        ("Activated areas", month.get("activated_areas_summary")),
        ("Continuing thread", month.get("continuity_from_previous")),
        ("Looking ahead", month.get("looking_ahead")),
        ("Carries forward", month.get("continuity_into_next")),
    )
    if metadata:
        nodes.append(NatalSummaryCard("Month map", metadata))
    activated_domains = month.get("activated_domains") or []
    if activated_domains:
        nodes.append(PillRow(tuple(_text(domain.get("domain")) for domain in activated_domains if isinstance(domain, dict) and _text(domain.get("domain")))))
    nodes.extend(_cards_from_items(month.get("major_timing_windows")))
    nodes.extend(_cards_from_items(month.get("convergence_windows")))
    events = [_event_card(event) for event in month.get("events", []) if isinstance(event, dict)]
    if events:
        nodes.append(Section("Chronological forecast", tuple(events), marker=f"month-events-{month.get('number', '')}"))
    else:
        nodes.append(Paragraph("No qualifying dated entries peak in this forecast period."))
    return MonthSection(
        title=_text(month.get("name") or "Forecast month"),
        number=month.get("number"),
        nodes=tuple(nodes),
        marker=f"month-{month.get('number', '')}",
    )


def _methodology_text(context: dict[str, Any]) -> str:
    methodology = _text(context.get("methodology_label")) or "Tropical zodiac + Whole Sign houses"
    return (
        f"This forecast is calculated with the Swiss Ephemeris using the {methodology} methodology. "
        "The report draws on natal transits, Whole Sign house ingresses, planetary stations, and eclipses that contact selected natal targets. "
        "It does not claim to predict one fixed future; it maps changing symbolic conditions, timing concentrations, and recurring developmental patterns. "
        "The proprietary EO material functions as an additional interpretive lens layered onto that astrological base, not a replacement for it."
    )


def compose_year_ahead(context: dict[str, Any]) -> ReportDocument:
    """Compose the completed Year Ahead context without recomputing it."""
    title = "Year-Ahead Predictive Almanac"
    querent = _text(context.get("querent_name"))
    generation_date = _text(context.get("generation_date"))
    report_span = _text(context.get("report_span_display"))
    footer = _text(context.get("report_footer_text")) or f"Entangled Oracle - Ksisti-Puck LLC - Generated {generation_date}"
    nodes: list[Any] = [
        CoverSection(
            ReportHeader(
                title=title,
                subtitle=querent or None,
                metadata=_metadata(("Forecast span", report_span), ("Generated", generation_date)),
            ),
            marker="cover",
        )
    ]

    if _text(context.get("chart_wheel_svg")):
        nodes.append(
            Section(
                "Natal Wheel",
                (
                    Figure(
                        media_type="image/svg+xml",
                        source=context.get("chart_wheel_svg"),
                        alt_text="Natal chart wheel",
                        semantic_role="natal_chart_wheel",
                        fallback_text="Natal chart wheel source is preserved for a future DOCX visual renderer. "
                        "This DOCX edition retains the chart reference data and forecast content below.",
                    ),
                    PillRow(tuple(_text(v) for v in context.get("wheel_transit_retrograde_planets", []) if _text(v))),
                ),
                kicker="I. Natal wheel",
                marker="natal-wheel",
            )
        )

    chart_rows = _rows(context.get("calculation_record"))
    natal_positions = tuple(
        (_text(row.get("name")), _text(row.get("position")), _text(row.get("house")))
        for row in context.get("natal_positions", [])
        if isinstance(row, dict)
    )
    chart_nodes: list[Any] = [
        NatalSummaryCard(
            "This Forecast, At a Glance",
            _metadata(
                ("Forecast span", report_span),
                ("Birth data", " - ".join(filter(None, [_text(context.get("birth_date_display")), _text(context.get("birth_time_display"))]))),
                ("Birth location", context.get("birth_location")),
                ("Birth-time confidence", context.get("birth_time_confidence")),
                ("Version", context.get("report_version")),
            ),
        ),
        Paragraph("Year Ahead is the annual predictive almanac of the Entangled Oracle suite, tracing the wider movement of the year through natal foundation, timing layers, and EO synthesis."),
    ]
    if chart_rows:
        chart_nodes.append(NatalSummaryCard("Calculation record", chart_rows))
    if natal_positions:
        chart_nodes.append(DataTable(("Point", "Position", "House"), natal_positions, caption="Natal positions"))
    nodes.append(Section("This Forecast, At a Glance", tuple(chart_nodes), kicker="II. Chart reference", marker="chart-reference"))

    guide_nodes: list[Any] = [
        Paragraph("This almanac is not meant to be consumed all at once; it is designed as an annual companion."),
        ProseSection("Quick read", "Start with the high-level yearly pattern, then move to the seasonal highlights, the strongest windows worth returning to, and closing guidance."),
        ProseSection("Monthly use", "Read the relevant season and month as the year unfolds. The report is designed to be revisited in pieces."),
        ProseSection("Deep dive", "Use the chart foundation, long arcs, methodology, and technical trace material to understand how the forecast was constructed."),
    ]
    if _text(context.get("report_boundary_note")):
        guide_nodes.insert(1, CalloutBlock("Forecast span note", _text(context.get("report_boundary_note")), "structure"))
    nodes.append(Section("How to Use This Almanac", tuple(guide_nodes), kicker="Start here", marker="reading-guide"))

    natal_nodes: list[Any] = []
    if context.get("retrograde_cluster_active") and _text(context.get("retrograde_cluster_block")):
        natal_nodes.append(CalloutBlock("Current Retrograde Climate", _text(context.get("retrograde_cluster_block")), "threshold"))
    if context.get("voc_next_active") and _text(context.get("voc_next_block")):
        natal_nodes.append(CalloutBlock("Next Void-of-Course Moon", _text(context.get("voc_next_block")), "threshold"))
    characteristics = context.get("chart_characteristics") or {}
    if _text(characteristics.get("method_note")):
        natal_nodes.append(MethodologyNote(_text(characteristics["method_note"])))
    natal_nodes.extend(_cards_from_items(characteristics.get("cards"), title_key="label", body_keys=("explanation", "availability_note")))
    foundation = context.get("standard_natal_foundation") or {}
    natal_nodes.extend(_paragraphs(foundation.get("intro")))
    natal_nodes.extend(_cards_from_items(foundation.get("sections")))
    natal_nodes.extend(_paragraphs(foundation.get("methodology_note")))
    natal_nodes.extend(_paragraphs(foundation.get("closing")))
    nodes.append(Section("Reading the Chart Foundation", tuple(natal_nodes), kicker="Natal reference", marker="natal-foundation"))

    orientation_nodes: list[Any] = _paragraphs(context.get("year_overview_block"))
    shape = context.get("forecast_shape_details") or {}
    orientation_nodes.append(
        NatalSummaryCard(
            _text(context.get("forecast_shape")) or "Annual pattern",
            _metadata(
                ("Explanation", shape.get("short_explanation")),
                ("Distribution", shape.get("distribution_note")),
                ("Peak month", shape.get("peak_month")),
                ("Quiet month", shape.get("quiet_month")),
                ("Peak season", shape.get("peak_season")),
                ("Confidence", shape.get("confidence_note")),
            ),
        )
    )
    orientation = context.get("orientation_summary") or {}
    orientation_nodes.append(NatalSummaryCard("Orientation notes", _metadata(
        ("Dominant long cycle", orientation.get("long_cycle_emphasis")),
        ("Highest concentration", orientation.get("highest_concentration_period")),
        ("Quietest period", orientation.get("quietest_period")),
    )))
    if orientation.get("strongest_annual_themes"):
        orientation_nodes.append(PillRow(tuple(_text(v) for v in orientation["strongest_annual_themes"] if _text(v)), "highlight"))
    curated = context.get("year_ahead_curated_summaries") or {}
    orientation_nodes.extend(_cards_from_items(curated.get("seasonal_highlights")))
    orientation_nodes.extend(_cards_from_items(curated.get("climate_highlights")))
    nodes.append(Section("The Year in Context", tuple(orientation_nodes), kicker="III. Year orientation", marker="year-orientation"))

    archetypal = context.get("archetypal_opening_section") or {}
    archetypal_nodes = _paragraphs(archetypal.get("body")) or [Paragraph("No archetypal synthesis is available for this forecast.")]
    nodes.append(Section(_text(archetypal.get("title")) or "Your Archetypal Year", tuple(archetypal_nodes), kicker="IV. Archetypal frame", marker="archetypal-frame"))

    arcs: list[Any] = [_event_card(event) for event in context.get("landmarks", []) if isinstance(event, dict)]
    arcs.extend(_event_card(event) for event in context.get("year_texture_progressions", []) if isinstance(event, dict))
    arcs.extend(_event_card(event) for event in context.get("year_texture_solar_arc", []) if isinstance(event, dict))
    tier5 = context.get("tier5_predictive_surfaces") or {}
    arcs.extend(_cards_from_items(tier5.get("annual_profections")))
    arcs.extend(_cards_from_items(tier5.get("zodiacal_releasing")))
    arcs.extend(_cards_from_items(tier5.get("exact_returns")))
    terrain = tier5.get("forecast_terrain") or {}
    arcs.extend(_cards_from_items([terrain.get("annual")] if isinstance(terrain.get("annual"), dict) else []))
    arcs.extend(_cards_from_items(terrain.get("months")))
    arcs.extend(_cards_from_items(terrain.get("chapters")))
    arcs.extend(_cards_from_items(terrain.get("contradictions")))
    predictive_surface = context.get("predictive_report_surface") or {}
    arcs.extend(_cards_from_items(predictive_surface.get("chapters")))
    nodes.append(Section("Long Stories in Motion", tuple(arcs) or (Paragraph("No sustained transit cycles met the current threshold."),), kicker="V. Year arcs", marker="year-arcs"))

    months = [month for month in context.get("months", []) if isinstance(month, dict)]
    rhythm_rows = tuple((_text(month.get("name")), _text(month.get("arc_label")), _text(month.get("activated_areas_summary"))) for month in months)
    rhythm_nodes: list[Any] = [DataTable(("Month", "Activity", "Activated areas"), rhythm_rows, caption="Annual rhythm")] if rhythm_rows else []
    rhythm_nodes.extend(_cards_from_items(context.get("annual_rhythm_quarters"), title_key="season_name", body_keys=("summary", "title")))
    nodes.append(Section("The Year at a Glance", tuple(rhythm_nodes), kicker="VI. Annual rhythm", marker="annual-rhythm"))
    nodes.append(Section("The Year as It Arrives", tuple(_monthly_section(month) for month in months), kicker="VII. Monthly chapters", marker="monthly-chapters"))

    turning_nodes: list[Any] = []
    for month in context.get("turning_point_timeline", []) or []:
        if isinstance(month, dict):
            turning_nodes.extend(_event_card(entry) for entry in month.get("entries", []) if isinstance(entry, dict))
    nodes.append(Section("Windows Worth Returning To", tuple(turning_nodes) or (Paragraph("No sustained landmark cycles met the turning point threshold."),), kicker="VIII. Turning point guide", marker="turning-points"))

    ledger = context.get("raw_cycle_ledger") or {}
    ledger_nodes: list[Any] = [Paragraph("This registry keeps event types distinct and lists them in chronological order without hidden score or theme-strength ranking.")]
    ledger_nodes.extend(_cards_from_items(ledger.get("field_notes"), title_key="event_type"))
    ledger_nodes.extend(_paragraphs(ledger.get("status_method_note")))
    for month in ledger.get("months", context.get("ledger_months", [])) or []:
        if not isinstance(month, dict):
            continue
        entries = [entry for entry in month.get("entries", []) if isinstance(entry, dict)]
        ledger_nodes.append(Section(_text(month.get("name")), tuple(_event_card(entry) for entry in entries)))
    for structure in ledger.get("structure_notes", []) or []:
        if isinstance(structure, dict):
            table = _technical_table(structure)
            if table:
                ledger_nodes.append(table)
    convergence_index = ledger.get("convergence_index") or []
    if convergence_index:
        ledger_nodes.append(
            DataTable(
                ("Window", "Shared emphasis", "Participating conditions", "Activated territories"),
                tuple(
                    (
                        _text(row.get("window")) + (f" - {_text(row.get('title'))}" if _text(row.get("title")) else ""),
                        _text(row.get("shared_emphasis")),
                        _text(row.get("participating_conditions")),
                        _text(row.get("activated_territories")),
                    )
                    for row in convergence_index if isinstance(row, dict)
                ),
                caption="Convergence Index",
            )
        )
    nodes.append(Section(_text(ledger.get("title")) or "Cycle Ledger - Forecast Event Registry", tuple(ledger_nodes), kicker="IX. Cycle ledger", marker="cycle-ledger"))

    appendix_nodes: list[Any] = [
        ProseSection("Transit", "A moving planet's relationship to a natal placement or chart angle."),
        ProseSection("Exact contact", "The closest point of an aspect inside a larger timing window."),
        ProseSection("Orb", "The allowable distance from exactness used to define an aspect's timing range."),
        ProseSection("Station", "The point at which a planet appears to pause before turning retrograde or direct."),
        ProseSection("Retrograde", "An apparent backward motion from Earth's perspective that often marks review, revision, or reworking."),
        ProseSection("House ingress", "A planet entering a new Whole Sign house, shifting the life territory through which it is expressed."),
        ProseSection("Eclipse", "A solar or lunar event that may concentrate attention around a natal point or area of life."),
        MethodologyNote(_methodology_text(context)),
    ]
    if _text(ledger.get("status_method_note")):
        appendix_nodes.append(MethodologyNote(_text(ledger["status_method_note"])))
    nodes.append(Section("Terms, Methods & Definitions", tuple(appendix_nodes), kicker="X. Technical appendix", marker="technical-appendix"))

    integration = _paragraphs(context.get("year_integration_block")) or [Paragraph("No end-of-year integration synthesis is available for this forecast.")]
    integration.append(Paragraph("Use these closing pages to register what the year clarified, what changed shape over time, and what still feels alive as the next cycle begins."))
    nodes.append(Section("What You Carry Forward", tuple(integration), kicker="XI. Year integration", marker="year-integration"))
    nodes.append(ReportFooter(footer))

    return ReportDocument(
        title=title,
        nodes=as_nodes(nodes),
        subject_name=querent or None,
        generation_date=generation_date or None,
        methodology_id=_text(context.get("methodology_id")) or None,
        report_subtype="year_ahead",
        theme_id=_text(context.get("palette_name")) or "vibrant",
        metadata={"report_family": "forecast"},
        parity_manifest=(
            ParityEntry("natal-wheel", "chart_wheel_svg"),
            ParityEntry("chart-reference", "natal_positions"),
            ParityEntry("natal-foundation", "standard_natal_foundation"),
            ParityEntry("year-orientation", "year_overview_block"),
            ParityEntry("archetypal-frame", "archetypal_opening_section"),
            ParityEntry("year-arcs", "landmarks"),
            ParityEntry("annual-rhythm", "annual_rhythm_quarters"),
            ParityEntry("monthly-chapters", "months"),
            ParityEntry("turning-points", "turning_point_timeline"),
            ParityEntry("cycle-ledger", "raw_cycle_ledger"),
            ParityEntry("year-integration", "year_integration_block"),
        ),
    )
