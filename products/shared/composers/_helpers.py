"""Small format-neutral construction helpers shared by report composers."""
from __future__ import annotations

from typing import Any, Iterable

from ..document_model import KeyValueRow, Paragraph, SupportCard


def text(value: Any) -> str:
    return str(value or "").strip()


def paragraphs(value: Any, tone: str | None = None) -> list[Paragraph]:
    return [Paragraph(part, tone=tone) for part in text(value).split("\n\n") if part.strip()]


def metadata(*pairs: tuple[str, Any]) -> tuple[KeyValueRow, ...]:
    return tuple(KeyValueRow(label, text(value)) for label, value in pairs if text(value))


def rows(items: Iterable[dict[str, Any]] | None, label: str = "label", value: str = "value") -> tuple[KeyValueRow, ...]:
    return tuple(
        KeyValueRow(text(item.get(label)), text(item.get(value)))
        for item in (items or [])
        if isinstance(item, dict) and text(item.get(label)) and text(item.get(value))
    )


def cards(items: Iterable[dict[str, Any]] | None, *, title_key: str = "title", body_keys: tuple[str, ...] = ("body", "summary", "block", "note")) -> list[SupportCard]:
    result: list[SupportCard] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        body = next((text(item.get(key)) for key in body_keys if text(item.get(key))), "")
        result.append(
            SupportCard(
                title=text(item.get(title_key) or item.get("name") or item.get("label") or "Report detail"),
                body=body,
                metadata=metadata(
                    ("Date", item.get("date_label") or item.get("peak_date")),
                    ("Type", item.get("type")),
                    ("Status", item.get("activation")),
                    ("Meta", item.get("meta")),
                ),
                tone=text(item.get("tone") or item.get("character")) or None,
            )
        )
    return result


def footer(context: dict[str, Any]) -> str:
    return text(context.get("report_footer_text")) or f"Entangled Oracle - Ksisti-Puck LLC - Generated {text(context.get('generation_date'))}"
