"""Optional state overlay normalization."""

from __future__ import annotations

from typing import Any

from eia_engine.models import EIAStateSnapshot
from eia_engine.schema import REGISTERS


def normalize_state_overlay(state_overlay: dict[str, Any] | None) -> dict[str, Any] | None:
    if not state_overlay:
        return None
    active_register = state_overlay.get("active_register") or state_overlay.get("register")
    if active_register not in REGISTERS:
        raise ValueError("State overlay requires a valid active_register")
    return {
        "method": state_overlay.get("method"),
        "seed_id": str(state_overlay.get("seed_id", "")),
        "active_register": active_register,
        "symbol": str(state_overlay.get("symbol", "")),
        "state_message": str(state_overlay.get("state_message", "")),
        "experiment": str(state_overlay.get("experiment", "")),
        "mode_hints": list(state_overlay.get("mode_hints", [])),
    }


def build_state_snapshot(state_overlay: dict[str, Any] | None) -> EIAStateSnapshot | None:
    state = normalize_state_overlay(state_overlay)
    if not state:
        return None
    return EIAStateSnapshot(
        method=state["method"],
        seed_id=state["seed_id"],
        active_register=state["active_register"],
        symbol=state["symbol"],
        state_message=state["state_message"],
        experiment=state["experiment"],
    )
