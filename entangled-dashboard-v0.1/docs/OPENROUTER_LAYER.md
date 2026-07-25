# OpenRouter Layer

OpenRouter is optional and non-loadbearing.

## States

- `disabled`: no key or user disabled LLM.
- `available`: proxy/key available.
- `quota_reached`: API returned quota or rate-limit state.
- `error`: network, proxy, or model error.

## Prompt Contract

The LLM receives structured data and must:

- Use only the supplied tarot/rune meanings, layout, astrology context, profile lens, and user question.
- Not invent cards, runes, placements, transits, or chart data.
- Distinguish static symbol meaning, live astrology, profile routing, and interpretive synthesis.
- Avoid certainty, fate claims, diagnosis, medical guidance, or external authority.

When LLM synthesis fails, the app displays local synthesis.
