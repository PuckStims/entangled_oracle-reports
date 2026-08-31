"""Small, explicit parity checks for context-to-document compositions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .document_model import CoverSection, MonthSection, ReportDocument, Section


@dataclass(frozen=True)
class ParityIssue:
    marker: str
    context_path: str
    message: str


def context_value(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def _markers(nodes: Iterable[Any]) -> set[str]:
    found: set[str] = set()
    for node in nodes:
        marker = getattr(node, "marker", None)
        if marker:
            found.add(marker)
        if isinstance(node, (Section, MonthSection, CoverSection)):
            found.update(_markers(node.nodes))
    return found


def validate_document_parity(document: ReportDocument, context: dict[str, Any]) -> list[ParityIssue]:
    """Return omissions where source context is present but its marker is absent.

    This intentionally avoids comparing HTML and DOCX bytes.  The manifest is
    reviewed with the composer and makes structural omissions testable.
    """
    markers = _markers(document.nodes)
    issues: list[ParityIssue] = []
    for entry in document.parity_manifest:
        source = context_value(context, entry.context_path)
        if entry.required_when_present and source and entry.marker not in markers:
            issues.append(
                ParityIssue(
                    marker=entry.marker,
                    context_path=entry.context_path,
                    message=f"Context '{entry.context_path}' is present but marker '{entry.marker}' is missing.",
                )
            )
    return issues
