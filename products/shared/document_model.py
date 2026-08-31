"""Format-neutral report document primitives.

Composers translate a completed report context into these semantic nodes.  No
node imports, exposes, or depends on a renderer implementation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


Tone = str


@dataclass(frozen=True)
class KeyValueRow:
    label: str
    value: str


@dataclass(frozen=True)
class Heading:
    text: str
    level: int = 1
    kicker: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.level <= 3:
            raise ValueError("Heading level must be between 1 and 3.")


@dataclass(frozen=True)
class Paragraph:
    text: str
    tone: Tone | None = None


@dataclass(frozen=True)
class CalloutBlock:
    title: str | None
    body: str
    tone: Tone = "highlight"


@dataclass(frozen=True)
class EventCard:
    title: str
    body: str = ""
    metadata: tuple[KeyValueRow, ...] = ()
    tone: Tone | None = None


@dataclass(frozen=True)
class DataTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    caption: str | None = None

    def __post_init__(self) -> None:
        if not self.headers:
            raise ValueError("DataTable requires at least one header.")
        expected_columns = len(self.headers)
        if any(len(row) != expected_columns for row in self.rows):
            raise ValueError("Every DataTable row must match the header width.")


@dataclass(frozen=True)
class Figure:
    """A renderer-neutral visual source with an accessible textual fallback."""

    media_type: str
    source: str | bytes | None
    alt_text: str
    caption: str | None = None
    semantic_role: str | None = None
    width_inches: float | None = None
    height_inches: float | None = None
    fallback_text: str | None = None


@dataclass(frozen=True)
class PillRow:
    items: tuple[str, ...]
    tone: Tone | None = None


@dataclass(frozen=True)
class MethodologyNote:
    text: str


@dataclass(frozen=True)
class PageBreak:
    pass


@dataclass(frozen=True)
class ReportFooter:
    text: str


@dataclass(frozen=True)
class ReportHeader:
    title: str
    subtitle: str | None = None
    metadata: tuple[KeyValueRow, ...] = ()


@dataclass(frozen=True)
class NatalSummaryCard:
    title: str
    rows: tuple[KeyValueRow, ...]
    tone: Tone | None = None


@dataclass(frozen=True)
class SupportCard:
    title: str
    body: str
    metadata: tuple[KeyValueRow, ...] = ()
    tone: Tone | None = None


@dataclass(frozen=True)
class ProseSection:
    title: str
    body: str
    subtitle: str | None = None
    tone: Tone | None = None


@dataclass(frozen=True)
class Section:
    """Reusable structural container; ``marker`` is for parity/audit tooling."""

    title: str | None = None
    nodes: tuple[Any, ...] = ()
    kicker: str | None = None
    tone: Tone | None = None
    marker: str | None = None


@dataclass(frozen=True)
class CoverSection:
    header: ReportHeader
    nodes: tuple[Any, ...] = ()
    marker: str | None = "cover"


@dataclass(frozen=True)
class MonthSection:
    title: str
    number: int | None = None
    nodes: tuple[Any, ...] = ()
    marker: str | None = None


DocumentNode = (
    Heading
    | Paragraph
    | CalloutBlock
    | EventCard
    | DataTable
    | Figure
    | PillRow
    | MethodologyNote
    | PageBreak
    | ReportFooter
    | ReportHeader
    | NatalSummaryCard
    | SupportCard
    | ProseSection
    | Section
)


@dataclass(frozen=True)
class ParityEntry:
    """Declarative map between a context path and a composed document marker."""

    marker: str
    context_path: str
    required_when_present: bool = True


@dataclass(frozen=True)
class ReportDocument:
    title: str
    nodes: tuple[DocumentNode | CoverSection | MonthSection, ...]
    subject_name: str | None = None
    generation_date: str | None = None
    methodology_id: str | None = None
    report_subtype: str | None = None
    theme_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    parity_manifest: tuple[ParityEntry, ...] = ()


def as_nodes(nodes: Sequence[DocumentNode | CoverSection | MonthSection]) -> tuple[DocumentNode | CoverSection | MonthSection, ...]:
    """A small convenience for composers that build node lists incrementally."""
    return tuple(nodes)
