"""Internal Architecture context -> shared document model."""
from __future__ import annotations

import json
from typing import Any

from ..document_model import CoverSection, DataTable, MethodologyNote, NatalSummaryCard, ParityEntry, ReportDocument, ReportFooter, ReportHeader, Section, SupportCard
from ._helpers import footer, metadata, paragraphs, text


def compose_internal_architecture(context: dict[str, Any]) -> ReportDocument:
    subject = text(context.get("client_name") or context.get("querent_name"))
    nodes: list[Any] = [CoverSection(ReportHeader("Internal Architecture", subject or None, metadata(("Birth date", context.get("birth_date_display")), ("Birth time", context.get("birth_time_display")), ("Birth location", context.get("birth_location")), ("Version", context.get("report_version")))), marker="cover")]
    if text(context.get("sample_identity_note")):
        nodes.append(Section("Sample Identity Note", tuple(paragraphs(context.get("sample_identity_note"))), marker="identity-note"))
    nodes.append(Section("Your Internal Architecture", tuple(paragraphs("\n\n".join(text(value) for value in context.get("opening_synthesis", []) if text(value)))), marker="synthesis"))
    glance = [SupportCard(text(item.get("label")), text(item.get("summary")), metadata(("Mode", item.get("value")), ("Signal", item.get("signal")))) for item in context.get("architecture_at_a_glance", []) or [] if isinstance(item, dict)]
    nodes.append(Section("Architecture at a Glance", tuple(glance), marker="glance"))
    registers: list[Any] = []
    for item in context.get("internal_architecture_registers", []) or []:
        if not isinstance(item, dict):
            continue
        body = "\n\n".join(filter(None, (text(item.get("consumer_description")), text(item.get("mechanism")), text(item.get("when_supported")), text(item.get("when_pressured")), text(item.get("experiment")))))
        registers.append(SupportCard(text(item.get("title")) or "Register", body, metadata(("Mode", item.get("mode_line")), ("Question", item.get("question")), ("Signal", item.get("signal_language")))))
    nodes.append(Section("Register Detail", tuple(registers), marker="registers"))
    patterns = [
        SupportCard(
            text(item.get("name")),
            "\n\n".join(filter(None, (text(item.get("activated")), text(item.get("feels")), text(item.get("distorts")), text(item.get("correction"))))),
            tone="pressure",
        )
        for item in context.get("internal_architecture_pressure_patterns", []) or []
        if isinstance(item, dict)
    ]
    if patterns:
        nodes.append(Section("Pressure Patterns", tuple(patterns), marker="pressure"))
    nodes.append(Section("Your Signal Path", tuple(paragraphs("\n\n".join(text(value) for value in context.get("signal_path_paragraphs", []) if text(value)))), marker="signal-path"))
    practitioner_rows = context.get("internal_architecture_practitioner_rows") or []
    if practitioner_rows:
        nodes.append(Section("Architecture Index", (DataTable(("Register", "Primary mode", "Secondary mode", "Signal strength", "Source basis"), tuple((text(row.get("register")), text(row.get("primary_mode")), text(row.get("secondary_mode")), text(row.get("signal_strength")), text(row.get("source_basis"))) for row in practitioner_rows if isinstance(row, dict))),), marker="index"))
    basis = context.get("calculation_basis") or {}
    if basis:
        nodes.append(Section("Calculation Basis", tuple(MethodologyNote(text(basis.get(key))) for key in ("calculation_basis", "method_note", "birth_time_confidence", "proprietary_layer") if text(basis.get(key))), marker="calculation"))
    if context.get("include_practitioner_appendix") and practitioner_rows:
        nodes.append(Section("Practitioner Appendix", (DataTable(("Register", "Primary mode", "Secondary mode", "Signal strength", "Confidence", "Source basis"), tuple((text(row.get("register")), text(row.get("primary_mode")), text(row.get("secondary_mode")), text(row.get("signal_strength")), text(row.get("confidence")), text(row.get("source_basis"))) for row in practitioner_rows if isinstance(row, dict))),), marker="practitioner"))
    if context.get("include_debug_json") and context.get("internal_architecture_json"):
        nodes.append(Section("Developer JSON", tuple(paragraphs(json.dumps(context["internal_architecture_json"], indent=2, default=str))), marker="debug"))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument("Internal Architecture", tuple(nodes), subject or None, text(context.get("generation_date")) or None, text(context.get("methodology_id")) or None, "internal_architecture", text(context.get("palette_name")) or "vibrant", parity_manifest=(ParityEntry("synthesis", "opening_synthesis"), ParityEntry("glance", "architecture_at_a_glance"), ParityEntry("registers", "internal_architecture_registers"), ParityEntry("pressure", "internal_architecture_pressure_patterns"), ParityEntry("signal-path", "signal_path_paragraphs"), ParityEntry("index", "internal_architecture_practitioner_rows")))
