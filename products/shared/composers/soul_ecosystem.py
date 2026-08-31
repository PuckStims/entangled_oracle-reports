"""Soul Ecosystem context -> shared document model."""
from __future__ import annotations

from typing import Any

from ..document_model import CalloutBlock, CoverSection, Figure, NatalSummaryCard, ParityEntry, PillRow, ReportDocument, ReportFooter, ReportHeader, Section, SupportCard
from ._helpers import cards, footer, metadata, paragraphs, text


def _block_cards(context: dict[str, Any], definitions: tuple[tuple[str, str], ...]) -> list[Any]:
    nodes: list[Any] = []
    for title, key in definitions:
        value = text(context.get(key))
        if value:
            nodes.append(SupportCard(title, value))
    return nodes


def compose_soul_ecosystem(context: dict[str, Any]) -> ReportDocument:
    subject = text(context.get("querent_name"))
    nodes: list[Any] = [CoverSection(ReportHeader("Soul Ecosystem", subject or None, metadata(("Birth date", context.get("birth_date_display")), ("Birth location", context.get("birth_location")), ("Generated", context.get("generation_date")))), marker="cover")]
    if text(context.get("chart_wheel_svg")):
        nodes.append(Section("Natal Wheel", (Figure("image/svg+xml", context.get("chart_wheel_svg"), "Natal chart wheel", semantic_role="natal_chart_wheel", fallback_text="Natal wheel retained as source content; the ecosystem interpretation follows."), PillRow(tuple(text(item) for item in context.get("wheel_transit_retrograde_planets", []) if text(item)))), marker="natal-wheel"))
    overview = _block_cards(context, (("Soul’s Story", "ecosystem_overview_block"), ("Soul’s Story", "souls_story_block"), ("Soul’s Promise", "souls_promise_block"), ("Sun and Moon Integration", "sun_moon_integration_block")))
    nodes.append(Section("Your Soul Ecosystem", tuple(overview), marker="overview"))
    regions = (
        ("Core Pattern", "core_support_cards", (("Core", "core_block"), ("Core Identity", "core_identity_block"))),
        ("Hidden Resources", "hidden_support_cards", (("South Node Sign", "south_node_sign_block"), ("South Node House", "south_node_house_block"), ("Twelfth House", "twelfth_house_blocks"))),
        ("Growth Pattern", "growth_support_cards", (("North Node Sign", "north_node_sign_block"), ("North Node House", "north_node_house_block"), ("Saturn", "saturn_block"), ("Chiron", "chiron_block"))),
        ("Inherited Pattern", "inherited_support_cards", (("Ancestral Layer", "ancestral_block"), ("Pluto Generation", "pluto_generation_block"))),
        ("World Pattern", "world_support_cards", (("Midheaven", "midheaven_block"), ("Jupiter", "jupiter_block"))),
        ("World Interface", "world_interface_support_cards", (("World Interface", "world_interface_block"),)),
        ("Living Integration", "living_integration_support_cards", (("Living Integration", "living_integration_block"),)),
    )
    for title, cards_key, blocks in regions:
        content: list[Any] = cards(context.get(cards_key))
        for block_title, key in blocks:
            value = context.get(key)
            if isinstance(value, list):
                content.extend(SupportCard(text(item.get("planet")) or block_title, text(item.get("block"))) for item in value if isinstance(item, dict) and text(item.get("block")))
            elif text(value):
                content.append(SupportCard(block_title, text(value)))
        if content:
            nodes.append(Section(title, tuple(content), marker=title.lower().replace(" ", "-")))
    eas = context.get("soul_ecosystem_eas_depth") or {}
    depth_nodes: list[Any] = _block_cards(context, ((text(context.get("proprietary_section_title")) or "EO Pattern Depth", "proprietary_section_block"),))
    for rank in ("dominant", "secondary", "tertiary"):
        detail = eas.get(rank) or {}
        if isinstance(detail, dict) and detail.get("available"):
            depth_nodes.append(
                SupportCard(
                    text(detail.get("title")) or rank.title(),
                    "\n\n".join(filter(None, (text(detail.get("archetype")), text(detail.get("expression")), text(detail.get("activation")), text((detail.get("driver") or {}).get("body"))))),
                )
            )
    if depth_nodes:
        nodes.append(Section("EO Pattern Depth", tuple(depth_nodes), marker="eas-depth"))
    archetype_nodes = _block_cards(
        context,
        (
            (text(context.get("primary_archetype_name")) or "Primary Archetype", "primary_archetype_block"),
            (text(context.get("secondary_archetype_name")) or "Secondary Archetype", "secondary_archetype_block"),
        ),
    )
    nodes.append(Section("Archetypal Support", tuple(archetype_nodes), marker="archetypes"))
    nodes.append(Section("Calculation Basis", (NatalSummaryCard("Report record", metadata(("Birth-time confidence", context.get("birth_time_confidence")), ("Methodology", context.get("methodology_label")), ("Version", context.get("report_version")))),), marker="basis"))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument("Soul Ecosystem", tuple(nodes), subject or None, text(context.get("generation_date")) or None, text(context.get("methodology_id")) or None, "soul_ecosystem", text(context.get("palette_name")) or "vibrant", parity_manifest=(ParityEntry("natal-wheel", "chart_wheel_svg"), ParityEntry("overview", "souls_story_block"), ParityEntry("core-pattern", "core_support_cards"), ParityEntry("growth-pattern", "growth_support_cards"), ParityEntry("world-pattern", "world_support_cards"), ParityEntry("eas-depth", "soul_ecosystem_eas_depth"), ParityEntry("archetypes", "primary_archetype_block")))
