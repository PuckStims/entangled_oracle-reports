"""Mode selection rules for EIA register scoring."""

from __future__ import annotations

CONTRADICTION_PAIRS = {
    frozenset(("Direct Spark", "Quiet Accumulation")),
    frozenset(("Open Field", "Selective Gate")),
    frozenset(("Immediate Knowing", "Tidal Knowing")),
    frozenset(("Membrane", "Wall")),
    frozenset(("Catalyst", "Stabilizer")),
}


def select_dominant_mode(mode_scores: dict[str, float], mode_order: list[str] | tuple[str, ...] | None = None) -> str:
    order = list(mode_order or mode_scores.keys())
    return max(order, key=lambda mode: (mode_scores.get(mode, 0.0), -order.index(mode)))


def select_secondary_mode(
    mode_scores: dict[str, float],
    dominant: str,
    mode_order: list[str] | tuple[str, ...] | None = None,
) -> str | None:
    order = [mode for mode in list(mode_order or mode_scores.keys()) if mode != dominant]
    if not order:
        return None
    secondary = max(order, key=lambda mode: (mode_scores.get(mode, 0.0), -order.index(mode)))
    secondary_score = mode_scores.get(secondary, 0.0)
    dominant_score = mode_scores.get(dominant, 0.0)
    if secondary_score < 0.50:
        return None
    if dominant_score - secondary_score <= 0.18:
        return secondary
    if frozenset((dominant, secondary)) in CONTRADICTION_PAIRS:
        return secondary
    return None
