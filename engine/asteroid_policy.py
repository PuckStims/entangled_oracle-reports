"""
engine/asteroid_policy.py - Phase 3 all-34 asteroid predictive policy.

Loads and validates the Phase 0 asteroid registry, then exposes a small
policy API for source/target/clock eligibility without changing scanner
calibration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


REQUIRED_ASTEROID_COUNT = 34
USER_ACTIVATED_DEFERRED_TARGET_CLOCKS = frozenset({"progression", "solar_arc"})
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "phase0" / "02_asteroid_predictive_registry.json"

_REQUIRED_ASTEROID_FIELDS = frozenset({
    "asteroid_name",
    "ephemeris_id",
    "tier",
    "natal_roles",
    "topic_keys",
    "domain_keys",
    "proprietary_index_links",
})


class AsteroidRegistryError(ValueError):
    """Raised when the machine-readable asteroid registry is not usable."""


@dataclass(frozen=True)
class AsteroidPolicy:
    raw: dict[str, Any]

    @property
    def policy_version(self) -> str:
        return str(self.raw.get("registry_metadata", {}).get("policy_version") or "")

    @property
    def asteroid_names(self) -> tuple[str, ...]:
        return tuple(record["asteroid_name"] for record in self.raw["asteroids"])

    @property
    def asteroid_count(self) -> int:
        return len(self.raw["asteroids"])

    def record_for(self, asteroid_name: str) -> dict[str, Any] | None:
        return _records_by_name(self.raw).get(asteroid_name)

    def require_record(self, asteroid_name: str) -> dict[str, Any]:
        record = self.record_for(asteroid_name)
        if record is None:
            raise KeyError(f"Unknown asteroid in predictive registry: {asteroid_name}")
        return record

    def tier_defaults_for(self, asteroid_name: str) -> dict[str, Any]:
        record = self.require_record(asteroid_name)
        tier = str(record.get("tier") or "")
        return self.raw["tier_defaults"][tier]

    def topic_keys(self, asteroid_name: str) -> list[str]:
        return _string_list(self.require_record(asteroid_name).get("topic_keys"))

    def domain_keys(self, asteroid_name: str) -> list[str]:
        return _string_list(self.require_record(asteroid_name).get("domain_keys"))

    def report_surface_permissions(self, asteroid_name: str) -> list[str]:
        defaults = self.tier_defaults_for(asteroid_name)
        return _string_list(defaults.get("report_surface_permissions"))

    def validation_category(self, asteroid_name: str) -> str:
        defaults = self.tier_defaults_for(asteroid_name)
        return str(defaults.get("validation_category") or "")

    def target_weight(self, asteroid_name: str) -> float:
        record = self.require_record(asteroid_name)
        defaults = self.tier_defaults_for(asteroid_name)
        value = record.get("weight_policy_override", defaults.get("weight_policy_default", 0.0))
        return _safe_float(value, 0.0)

    def allowed_aspects(self, asteroid_name: str, clock: str) -> list[str]:
        override = self._source_override(asteroid_name, clock)
        if override and override.get("allowed_aspects") is not None:
            return _string_list(override.get("allowed_aspects"))
        defaults = self.tier_defaults_for(asteroid_name)
        aspects = defaults.get("allowed_aspects_by_clock", {}).get(clock, [])
        return _string_list(aspects)

    def orb(self, asteroid_name: str, clock: str) -> float | None:
        defaults = self.tier_defaults_for(asteroid_name)
        value = defaults.get("orb_policy_by_clock", {}).get(clock)
        if value is None:
            return None
        return _safe_float(value, 0.0)

    def target_eligible(self, asteroid_name: str, clock: str) -> bool:
        override = self._target_override(asteroid_name, clock)
        if override is not None:
            value = str(override).lower()
            return value in {"yes", "conditional_within_1_degree_and_index_participation"}
        defaults = self.tier_defaults_for(asteroid_name)
        value = str(defaults.get("target_eligibility", {}).get(clock) or "").lower()
        if value == "deferred" and clock in USER_ACTIVATED_DEFERRED_TARGET_CLOCKS:
            return str(self.require_record(asteroid_name).get("tier") or "").lower() == "elevated"
        return value in {"yes", "conditional_within_1_degree_and_index_participation"}

    def source_eligible(
        self,
        asteroid_name: str,
        clock: str,
        *,
        aspect: str | None = None,
        target_body: str | None = None,
    ) -> bool:
        override = self._source_override(asteroid_name, clock)
        if override is not None:
            allowed_aspects = set(_string_list(override.get("allowed_aspects")))
            restricted_targets = set(_string_list(override.get("restricted_targets")))
            if aspect and allowed_aspects and aspect not in allowed_aspects:
                return False
            if target_body and restricted_targets and target_body not in restricted_targets:
                return False
            return True

        defaults = self.tier_defaults_for(asteroid_name)
        value = str(defaults.get("source_eligibility", {}).get(clock) or "").lower()
        if value == "yes":
            return True
        if value == "conditional_on_index_driver_role":
            record = self.require_record(asteroid_name)
            return bool(record.get("proprietary_index_links"))
        return False

    def clock_eligible(self, asteroid_name: str, clock: str) -> bool:
        return self.target_eligible(asteroid_name, clock) or self.source_eligible(asteroid_name, clock)

    def metadata(self) -> dict[str, Any]:
        meta = dict(self.raw.get("registry_metadata") or {})
        meta["loaded_asteroid_count"] = self.asteroid_count
        return meta

    def _source_override(self, asteroid_name: str, clock: str) -> dict[str, Any] | None:
        record = self.require_record(asteroid_name)
        overrides = record.get("source_eligibility_override")
        if not isinstance(overrides, dict):
            return None
        value = overrides.get(clock)
        return value if isinstance(value, dict) else None

    def _target_override(self, asteroid_name: str, clock: str) -> Any | None:
        record = self.require_record(asteroid_name)
        overrides = record.get("target_eligibility_override")
        if not isinstance(overrides, dict):
            return None
        return overrides.get(clock)


@lru_cache(maxsize=1)
def load_asteroid_policy(registry_path: str | Path | None = None) -> AsteroidPolicy:
    path = Path(registry_path) if registry_path else REGISTRY_PATH
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    validate_asteroid_registry(raw)
    return AsteroidPolicy(raw=raw)


def validate_asteroid_registry(raw: dict[str, Any]) -> None:
    if not isinstance(raw, dict):
        raise AsteroidRegistryError("Asteroid registry must be a JSON object.")

    asteroids = raw.get("asteroids")
    if not isinstance(asteroids, list):
        raise AsteroidRegistryError("Asteroid registry requires an asteroids array.")
    if len(asteroids) != REQUIRED_ASTEROID_COUNT:
        raise AsteroidRegistryError(f"Asteroid registry must contain exactly {REQUIRED_ASTEROID_COUNT} records.")

    metadata_count = raw.get("registry_metadata", {}).get("asteroid_count")
    if metadata_count != REQUIRED_ASTEROID_COUNT:
        raise AsteroidRegistryError("registry_metadata.asteroid_count must be exactly 34.")

    tier_defaults = raw.get("tier_defaults")
    if not isinstance(tier_defaults, dict):
        raise AsteroidRegistryError("Asteroid registry requires tier_defaults.")

    seen: set[str] = set()
    for index, record in enumerate(asteroids):
        if not isinstance(record, dict):
            raise AsteroidRegistryError(f"Asteroid record {index} must be an object.")
        missing = _REQUIRED_ASTEROID_FIELDS - set(record.keys())
        if missing:
            name = record.get("asteroid_name", f"record {index}")
            raise AsteroidRegistryError(f"{name} missing required fields: {sorted(missing)}")
        name = str(record["asteroid_name"])
        if name in seen:
            raise AsteroidRegistryError(f"Duplicate asteroid registry record: {name}")
        seen.add(name)
        tier = str(record.get("tier") or "")
        if tier not in tier_defaults:
            raise AsteroidRegistryError(f"{name} references unknown tier: {tier}")
        defaults = tier_defaults[tier]
        for field in (
            "target_eligibility",
            "source_eligibility",
            "allowed_aspects_by_clock",
            "orb_policy_by_clock",
            "weight_policy_default",
            "report_surface_permissions",
            "validation_category",
        ):
            if field not in defaults:
                raise AsteroidRegistryError(f"Tier {tier} missing required default field: {field}")


def asteroid_registry_summary() -> dict[str, Any]:
    policy = load_asteroid_policy()
    return {
        "policy_version": policy.policy_version,
        "asteroid_count": policy.asteroid_count,
        "asteroid_names": list(policy.asteroid_names),
        "validation_categories": {
            name: policy.validation_category(name)
            for name in policy.asteroid_names
        },
    }


def _records_by_name(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(record.get("asteroid_name")): record
        for record in raw.get("asteroids", [])
        if isinstance(record, dict)
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
