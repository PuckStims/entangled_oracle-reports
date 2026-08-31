"""Output configuration and format-independent composition entry points."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .composers import compose_report
from .document_model import ReportDocument
from .document_parity import validate_document_parity


@dataclass(frozen=True)
class OutputOptions:
    formats: tuple[str, ...] = ("html",)

    def __post_init__(self) -> None:
        unsupported = set(self.formats) - {"html", "docx"}
        if unsupported:
            raise ValueError(f"Unsupported output formats: {', '.join(sorted(unsupported))}")
        if not self.formats:
            raise ValueError("At least one output format is required.")

    @classmethod
    def from_formats(cls, formats: Iterable[str] | None) -> "OutputOptions":
        return cls(tuple(formats or ("html",)))


def compose_document(report_type: str, context: dict) -> ReportDocument:
    return compose_report(report_type, context)


def docx_output_path(html_output_path: str | Path) -> Path:
    return Path(html_output_path).with_suffix(".docx")


def render_docx_report(report_type: str, context: dict, output_path: str | Path) -> Path:
    """Compose then render; neither layer knows caller/domain runtime details."""
    from .docx_renderer import DocxRenderer

    document = compose_document(report_type, context)
    parity_issues = validate_document_parity(document, context)
    if parity_issues:
        details = "; ".join(issue.message for issue in parity_issues)
        raise ValueError(f"Document parity validation failed: {details}")
    return DocxRenderer(theme_id=document.theme_id).render_to_path(document, output_path)
