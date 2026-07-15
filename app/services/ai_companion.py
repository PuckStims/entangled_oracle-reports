"""Static, no-API companion prompts for report reading."""

from __future__ import annotations


PROMPT_GROUPS = {
    "before": [
        "Choose one question you want the report to help organize, not answer for you.",
        "Skim the section titles first. Notice where your attention lands before reading every detail.",
        "Mark language that feels clarifying, and leave anything that feels too loud for later.",
    ],
    "during": [
        "Pause when a sentence names something familiar. Ask what evidence in your life already supports or complicates it.",
        "Separate description from instruction. A symbolic pattern can be useful without becoming a command.",
        "Choose one theme to observe for a week before trying to act on the whole report.",
    ],
    "after": [
        "Write three takeaways: one confirming, one challenging, and one you are not ready to decide about.",
        "Name one grounded next observation. Keep it small enough to actually notice.",
        "If the report stirred up urgency, step away before making any major decision from it.",
    ],
}

COPY_TO_AI_PROMPT = (
    "I am reading an Entangled Oracle astrology report. Please help me reflect on it without "
    "treating it as fate, diagnosis, or instruction. Ask grounding questions, help me identify "
    "themes, and remind me to keep agency and proportion. Do not create new astrology claims."
)


def prompt_groups() -> dict[str, list[str]]:
    return PROMPT_GROUPS


def copy_to_ai_prompt() -> str:
    return COPY_TO_AI_PROMPT

