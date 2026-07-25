"""
Reusable prose-unit builders for synastry narrative compilation.
"""
from __future__ import annotations

from typing import Any


def sentence_join(parts: list[str]) -> str:
    clean = [str(part).strip() for part in parts if isinstance(part, str) and part.strip()]
    return " ".join(clean)


def serial_join(parts: list[str]) -> str:
    clean = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def topic_intro(topic_key: str) -> str:
    mapping = {
        "attachment_emotional_rhythm": "Emotional rhythm is the clearest organizing theme in this relationship.",
        "communication": "Communication is not peripheral here; it is one of the main ways the relationship becomes real.",
        "growth_meaning": "Growth and meaning are active enough here that the relationship keeps widening the frame around itself.",
        "commitment_constraint_time": "Care, routine, and responsibility matter because this bond does not stay purely atmospheric.",
        "intensity_merging_shared_resources": "Depth and shared stakes are part of the structure, not just occasional mood.",
    }
    return mapping.get(topic_key, "This relationship theme is strong enough to shape how the connection is actually lived.")


def evidence_bridge(families: list[str], *, qualifier: str | None = None) -> str:
    if not families:
        return ""
    sentence = f"The evidence repeats through {serial_join(families[:4])}, so the theme does not stay abstract for long."
    if qualifier:
        sentence += f" {qualifier.strip()}"
    return sentence


def directional_overlay_interpretation(
    source_name: str,
    source_body: str,
    target_name: str,
    target_house_label: str,
    *,
    sign_tone: str | None = None,
    implication: str | None = None,
) -> str:
    body = (
        f"{source_name}'s {source_body} lands in {target_name}'s {target_house_label}, "
        f"so {source_name} is being felt there in a direct, lived way."
    )
    if sign_tone:
        body += f" The sign tone makes that field read as {sign_tone}."
    if implication:
        body += f" {implication.strip()}"
    return body


def mutual_contact_interpretation(
    left_name: str,
    left_body: str,
    aspect: str,
    right_name: str,
    right_body: str,
    *,
    implication: str | None = None,
) -> str:
    body = (
        f"{left_name}'s {left_body} {aspect.lower()}s {right_name}'s {right_body}"
        if aspect == "Opposition"
        else f"{left_name}'s {left_body} {aspect.lower()} {right_name}'s {right_body}"
    )
    sentence = f"{body}, creating a contact the relationship is unlikely to experience as neutral."
    if implication:
        sentence += f" {implication.strip()}"
    return sentence


def cluster_synthesis(sentence: str) -> str:
    return sentence.strip()


def friction_modifier(sentence: str) -> str:
    return sentence.strip()


def constructive_use(sentence: str) -> str:
    return sentence.strip()


def appendix_card(
    title: str,
    body: str,
    *,
    metadata: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
) -> dict:
    return {
        "title": title,
        "body": body,
        "metadata": metadata or {},
        "source": source or {},
    }
