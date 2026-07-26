"""Content-pack loading for EIA register copy."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


def default_content_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "content" / "eia"


@lru_cache(maxsize=4)
def load_modes_catalog(content_dir: str | None = None) -> dict[str, list[str]]:
    return _load_json(_resolve(content_dir) / "modes_seed_catalog.json")


@lru_cache(maxsize=4)
def load_register_copy(content_dir: str | None = None) -> dict[str, dict[str, dict[str, str]]]:
    return _load_json(_resolve(content_dir) / "register_copy_v0_1.json")


@lru_cache(maxsize=4)
def load_distortion_patterns(content_dir: str | None = None) -> dict[str, dict[str, str]]:
    return _load_json(_resolve(content_dir) / "distortion_patterns_v0_1.json")


def content_for(register: str, mode: str, content_dir: str | None = None) -> dict[str, str]:
    authored = load_register_copy(content_dir).get(register, {}).get(mode)
    if not authored:
        raise ValueError(f"Missing authored EIA consumer copy for {register}: {mode}")
    required = (
        "consumer_description",
        "mechanism",
        "distortion",
        "restoration",
        "experiment",
        "when_supported",
        "when_pressured",
    )
    missing = [key for key in required if not authored.get(key)]
    if missing:
        raise ValueError(f"Incomplete EIA consumer copy for {register}: {mode}; missing {', '.join(missing)}")
    return authored


def _resolve(content_dir: str | None) -> Path:
    return Path(content_dir) if content_dir else default_content_dir()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
