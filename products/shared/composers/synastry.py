"""Synastry context -> shared semantic document composition."""
from __future__ import annotations

from typing import Any

from ..document_model import (
    CoverSection,
    DataTable,
    KeyValueRow,
    MethodologyNote,
    ParityEntry,
    ReportDocument,
    ReportFooter,
    ReportHeader,
    Section,
    SupportCard,
    as_nodes,
)
from ._helpers import footer, metadata, text


def _card(item: dict[str, Any]) -> SupportCard:
    values = item.get("metadata") or {}
    rows = tuple(
        KeyValueRow(str(key).replace("_", " ").title(), ", ".join(map(str, value)) if isinstance(value, list) else text(value))
        for key, value in values.items()
        if text(value)
    )
    return SupportCard(
        title=text(item.get("title") or item.get("id") or "Evidence item"),
        body=text(item.get("body")),
        metadata=rows,
        tone=text(values.get("polarity")) or None,
    )


def compose_synastry(context: dict) -> ReportDocument:
    """Arrange the dedicated synastry context without recalculating evidence."""
    person_a = text(context.get("person_a_name")) or "Person A"
    person_b = text(context.get("person_b_name")) or "Person B"
    relationship_meta = context.get("relationship_meta") or {}
    sections = [section for section in context.get("sections", []) if isinstance(section, dict)]
    nodes: list[Any] = [
        CoverSection(
            ReportHeader(
                title=text(context.get("product_name")) or "Synastry Narrative Preview",
                subtitle=f"{person_a} and {person_b}",
                metadata=metadata(
                    ("Relationship type", relationship_meta.get("relationship_type")),
                    (f"{person_a} birth-time state", context.get("person_a_birth_time_state")),
                    (f"{person_b} birth-time state", context.get("person_b_birth_time_state")),
                ),
            )
        )
    ]
    for section in sections:
        section_nodes: list[Any] = []
        for key in ("blocks", "items", "body_items", "aspect_items", "ambiguity_items", "boundary_items"):
            section_nodes.extend(_card(item) for item in section.get(key, []) if isinstance(item, dict))
        method_note = (section.get("method_note") or {}).get("body")
        if text(method_note):
            section_nodes.append(MethodologyNote(text(method_note)))
        withheld = (section.get("withheld_summary") or {}).get("by_reason") or {}
        if withheld:
            section_nodes.append(DataTable(("Withheld reason", "Count"), tuple((text(reason), text(count)) for reason, count in withheld.items())))
        nodes.append(Section(text(section.get("title")) or "Report section", tuple(section_nodes), marker=text(section.get("id")) or None))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument(
        title=text(context.get("product_name")) or "Synastry Narrative Preview",
        nodes=as_nodes(nodes),
        subject_name=f"{person_a} and {person_b}",
        methodology_id=text(context.get("pair_schema_version")) or None,
        report_subtype="synastry",
        theme_id=text(relationship_meta.get("palette")) or "vibrant",
        metadata={"report_family": "synastry"},
        parity_manifest=tuple(ParityEntry(text(section.get("id")), "sections") for section in sections if text(section.get("id"))),
    )
