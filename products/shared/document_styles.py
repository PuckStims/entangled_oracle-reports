"""Centralized DOCX theme tokens; composers only provide semantic tones."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocxTheme:
    body_font: str = "Aptos"
    heading_font: str = "Aptos Display"
    body_color: str = "25223A"
    muted_color: str = "655F78"
    accent_color: str = "6C4AB6"
    background_color: str = "F8F6FC"
    tone_accents: dict[str, str] | None = None

    def accent_for(self, tone: str | None) -> str:
        return (self.tone_accents or {}).get(tone or "", self.accent_color)


def theme_for(theme_id: str | None) -> DocxTheme:
    # Theme identifiers remain semantic/document metadata.  This is the one
    # renderer-owned mapping point for future visual systems.
    if theme_id == "muted":
        return DocxTheme(
            accent_color="7A5B3E",
            background_color="F7F2EA",
            tone_accents={
                "flowing": "53735A",
                "pressure": "9A4D4D",
                "threshold": "8C6438",
                "structure": "4D5F80",
                "highlight": "7A5B3E",
            },
        )
    return DocxTheme(
        tone_accents={
            "flowing": "3B7C71",
            "pressure": "A34A5D",
            "threshold": "A76B29",
            "structure": "5269A6",
            "highlight": "6C4AB6",
            "challenging": "A34A5D",
        }
    )
