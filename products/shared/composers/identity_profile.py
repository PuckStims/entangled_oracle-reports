"""Identity Profile context -> shared document model."""
from __future__ import annotations

from typing import Any

from ..document_model import CoverSection, NatalSummaryCard, ParityEntry, PillRow, ReportDocument, ReportFooter, ReportHeader, Section, SupportCard
from ._helpers import cards, footer, metadata, paragraphs, text


def compose_identity_profile(context: dict[str, Any]) -> ReportDocument:
    subject = text(context.get("querent_name"))
    nodes: list[Any] = [CoverSection(ReportHeader("Entangled Identity Profile", subject or None, metadata(("Generated", context.get("generation_date")), ("Location", context.get("generation_location")))), marker="cover")]
    overview_nodes: list[Any] = paragraphs(context.get("portrait_overview_block"))
    glance = context.get("identity_at_a_glance") or []
    if glance:
        overview_nodes.append(NatalSummaryCard("Identity at a Glance", metadata(*tuple((text(item.get("label")), item.get("value")) for item in glance if isinstance(item, dict)))))
    nodes.append(Section("Your Living Archetypal Map", tuple(overview_nodes), marker="overview"))
    systems: list[Any] = []
    for item in context.get("active_index_sections", []) or []:
        if not isinstance(item, dict):
            continue
        body = "\n\n".join(
            filter(None, (text(item.get("expression")), text(item.get("archetype")), text(item.get("tagline")), text(item.get("block"))))
        )
        systems.append(
            SupportCard(text(item.get("name")), body, metadata(("Activation", item.get("activation"))), text(item.get("activation")) or None)
        )
        if item.get("details"):
            systems.append(PillRow(tuple(text(value) for value in item["details"] if text(value))))
    nodes.append(Section("Archetypes Currently Shaping the Story", tuple(systems), marker="systems"))
    tensions = [SupportCard(text(item.get("label")), text(item.get("block")), metadata(("Tension", f"{text(item.get('left'))} ↔ {text(item.get('right'))}")), "pressure") for item in context.get("tension_sections", []) or [] if isinstance(item, dict)]
    if tensions:
        nodes.append(Section("Where Your Archetypes Complicate One Another", tuple(tensions), marker="tensions"))
    quiet = [SupportCard(text(item.get("name")), text(item.get("note")), metadata(("Archetype", item.get("archetype")))) for item in context.get("quiet_signal_sections", []) or [] if isinstance(item, dict)]
    if quiet:
        nodes.append(Section("Archetypes Present at the Edge of the Story", tuple(quiet), marker="quiet"))
    cast = [SupportCard(text(item.get("name")), text(item.get("block")), metadata(("Domain", item.get("domain")), ("Role", item.get("role")), ("Position", item.get("position")), ("House", item.get("house")))) for item in context.get("mythic_cast", []) or [] if isinstance(item, dict)]
    if cast:
        nodes.append(Section("The Entities Behind the Portrait", tuple(cast), marker="cast"))
    if context.get("has_portrait_synthesis") and text(context.get("portrait_synthesis_block")):
        nodes.append(Section("The Story These Forces Make Together", tuple(paragraphs(context.get("portrait_synthesis_block"))), marker="synthesis"))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument("Entangled Identity Profile", tuple(nodes), subject or None, text(context.get("generation_date")) or None, text(context.get("methodology_id")) or None, "identity_profile", text(context.get("palette_name")) or "vibrant", parity_manifest=(ParityEntry("overview", "portrait_overview_block"), ParityEntry("systems", "active_index_sections"), ParityEntry("tensions", "tension_sections"), ParityEntry("cast", "mythic_cast"), ParityEntry("synthesis", "portrait_synthesis_block", False)))
