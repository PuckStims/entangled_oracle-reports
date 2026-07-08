"""
engine/validation_harness.py - Phase 9 retrospective validation tools.

This module reads sidecar evidence and reviewer-authored outcome ledgers. It
does not inspect report HTML, does not code real outcomes, and does not create
fixtures that look like historical validation results.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from product_versions import write_json


OUTCOME_LEDGER_VERSION = "phase0.1.0"
VALIDATION_HARNESS_VERSION = "phase9_validation_v1"

LOCKED_OUTCOME_CATEGORIES = frozenset(
    {
        "supported_hit",
        "supported_non_hit",
        "unresolved",
        "research_incomplete",
        "excluded_by_protocol",
    }
)
MATCH_PRECISION_VALUES = frozenset(
    {
        "",
        "exact_day",
        "within_window",
        "edge_of_window",
        "outside_window_close_call",
    }
)
RESEARCH_COMPLETENESS_VALUES = frozenset({"full", "partial", "minimal"})
BLIND_REVIEW_VALUES = frozenset({"blind", "partially_blind", "open"})


def load_json(path: str | Path) -> dict:
    """Load a JSON object from disk."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def sidecar_run_package(sidecar: dict, *, sidecar_reference: str = "") -> dict:
    """Return a reproducible immutable run-package descriptor for a sidecar."""
    report_run = sidecar.get("report_run") if isinstance(sidecar.get("report_run"), dict) else {}
    natal_snapshot = sidecar.get("natal_snapshot") if isinstance(sidecar.get("natal_snapshot"), dict) else {}
    candidates = sidecar.get("candidates") if isinstance(sidecar.get("candidates"), list) else []
    candidate_ids = sorted(str(candidate.get("candidate_id")) for candidate in candidates if isinstance(candidate, dict))
    basis = {
        "sidecar_version": sidecar.get("sidecar_version") or sidecar.get("sidecar_schema_version"),
        "report_run_id": report_run.get("report_run_id"),
        "report_type": report_run.get("report_type"),
        "report_start": report_run.get("report_start"),
        "report_end": report_run.get("report_end"),
        "natal_snapshot_id": natal_snapshot.get("natal_snapshot_id"),
        "policy_versions": sidecar.get("policy_versions") or {},
        "candidate_ids": candidate_ids,
        "candidate_count": len(candidate_ids),
        "sidecar_reference": Path(sidecar_reference).name if sidecar_reference else "",
    }
    return {
        "run_package_id": _hash_id("runpkg", basis),
        "harness_version": VALIDATION_HARNESS_VERSION,
        "sidecar_reference": sidecar_reference,
        "sidecar_sha256": _json_hash(sidecar),
        "sidecar_report_run_id": report_run.get("report_run_id", ""),
        "sidecar_natal_snapshot_id": natal_snapshot.get("natal_snapshot_id", ""),
        "candidate_count": len(candidate_ids),
        "quiet_period": len(candidate_ids) == 0,
        "basis": basis,
    }


def initialize_outcome_ledger(sidecar: dict, *, sidecar_reference: str = "") -> dict:
    """Create an empty outcome ledger shell for a sidecar."""
    report_run = sidecar.get("report_run") if isinstance(sidecar.get("report_run"), dict) else {}
    natal_snapshot = sidecar.get("natal_snapshot") if isinstance(sidecar.get("natal_snapshot"), dict) else {}
    return {
        "outcome_ledger_version": OUTCOME_LEDGER_VERSION,
        "sidecar_reference": sidecar_reference,
        "sidecar_natal_snapshot_id": natal_snapshot.get("natal_snapshot_id", ""),
        "sidecar_report_run_id": report_run.get("report_run_id", ""),
        "run_package": sidecar_run_package(sidecar, sidecar_reference=sidecar_reference),
        "outcomes": [],
        "matched_random_baseline": build_matched_random_baseline(sidecar),
        "aggregation_notes": "",
    }


def read_outcome_ledger(path: str | Path) -> dict:
    """Read and validate an existing outcome ledger."""
    ledger = load_json(path)
    _validate_ledger_shape(ledger)
    return ledger


def write_outcome_ledger(path: str | Path, ledger: dict) -> None:
    """Atomically write an outcome ledger."""
    _validate_ledger_shape(ledger)
    write_json(str(path), ledger)


def append_outcome_entry(
    ledger: dict,
    sidecar: dict,
    *,
    candidate_id: str,
    research_subject: str,
    chronology_source: str,
    chronology_source_timestamp: str,
    outcome_category: str,
    reviewer_id: str,
    reviewed_at: str,
    match_precision: str = "",
    research_completeness: str = "minimal",
    event_date: str = "",
    domain_mismatch: bool = False,
    non_hit_rationale: str = "",
    unresolved_rationale: str = "",
    blind_review_status: str = "partially_blind",
) -> dict:
    """Append one reviewer-coded outcome entry and return it."""
    if outcome_category not in LOCKED_OUTCOME_CATEGORIES:
        raise ValueError(f"Invalid outcome_category: {outcome_category}")
    if match_precision not in MATCH_PRECISION_VALUES:
        raise ValueError(f"Invalid match_precision: {match_precision}")
    if research_completeness not in RESEARCH_COMPLETENESS_VALUES:
        raise ValueError(f"Invalid research_completeness: {research_completeness}")
    if blind_review_status not in BLIND_REVIEW_VALUES:
        raise ValueError(f"Invalid blind_review_status: {blind_review_status}")

    candidate = _candidate_by_id(sidecar, candidate_id)
    pre_registered_at = _parse_datetime(candidate.get("pre_registered_at"))
    reviewed_at_dt = _parse_datetime(reviewed_at)
    if pre_registered_at and reviewed_at_dt and reviewed_at_dt < pre_registered_at:
        raise ValueError("reviewed_at must not precede candidate pre_registered_at")
    if outcome_category == "supported_hit" and not event_date:
        raise ValueError("supported_hit requires event_date")
    if outcome_category != "supported_hit" and event_date:
        raise ValueError("event_date is only allowed for supported_hit")

    report_run = sidecar.get("report_run") if isinstance(sidecar.get("report_run"), dict) else {}
    natal_snapshot = sidecar.get("natal_snapshot") if isinstance(sidecar.get("natal_snapshot"), dict) else {}
    entry_basis = {
        "candidate_id": candidate_id,
        "reviewed_at": reviewed_at,
        "reviewer_id": reviewer_id,
        "category": outcome_category,
        "existing_outcome_count": len(ledger.get("outcomes", [])),
    }
    entry = {
        "outcome_id": _hash_id("out", entry_basis),
        "candidate_id": candidate_id,
        "report_run_id": report_run.get("report_run_id", candidate.get("report_run_id", "")),
        "chart_id": natal_snapshot.get("natal_snapshot_id", ""),
        "research_subject": research_subject,
        "candidate_window": [candidate.get("start_at", ""), candidate.get("end_at", "")],
        "candidate_domain": candidate.get("candidate_domain", []),
        "pre_registered_evidence": candidate,
        "chronology_source": chronology_source,
        "chronology_source_timestamp": chronology_source_timestamp,
        "outcome_category": outcome_category,
        "event_date": event_date,
        "match_precision": match_precision,
        "research_completeness": research_completeness,
        "domain_mismatch": bool(domain_mismatch),
        "non_hit_rationale": non_hit_rationale,
        "unresolved_rationale": unresolved_rationale,
        "reviewer_id": reviewer_id,
        "reviewed_at": reviewed_at,
        "blind_review_status": blind_review_status,
    }
    ledger.setdefault("outcomes", []).append(entry)
    _validate_ledger_shape(ledger)
    return entry


def build_matched_random_baseline(sidecar: dict, *, seed: int | None = None) -> dict:
    """Generate deterministic uncoded matched-random baseline candidates."""
    report_run = sidecar.get("report_run") if isinstance(sidecar.get("report_run"), dict) else {}
    report_start = _parse_datetime(report_run.get("report_start"))
    report_end = _parse_datetime(report_run.get("report_end"))
    candidates = [c for c in sidecar.get("candidates", []) if isinstance(c, dict)]
    baseline_seed = seed if seed is not None else _seed_for_sidecar(sidecar)
    rng = random.Random(baseline_seed)
    baseline_candidates = []

    if report_start and report_end and report_end >= report_start:
        total_seconds = max(0, int((report_end - report_start).total_seconds()))
        for index, candidate in enumerate(candidates):
            start_at = _parse_datetime(candidate.get("start_at"))
            end_at = _parse_datetime(candidate.get("end_at"))
            width_seconds = _candidate_width_seconds(candidate, start_at, end_at)
            max_offset = max(0, total_seconds - width_seconds)
            offset = rng.randint(0, max_offset) if max_offset else 0
            random_start = report_start + timedelta(seconds=offset)
            random_end = random_start + timedelta(seconds=width_seconds)
            baseline_id = _hash_id(
                "basecand",
                {
                    "report_run_id": report_run.get("report_run_id"),
                    "candidate_id": candidate.get("candidate_id"),
                    "index": index,
                    "seed": baseline_seed,
                    "width_seconds": width_seconds,
                },
            )
            baseline_candidates.append(
                {
                    "baseline_candidate_id": baseline_id,
                    "matched_to_candidate_id": candidate.get("candidate_id", ""),
                    "start_at": _iso_datetime(random_start),
                    "end_at": _iso_datetime(random_end),
                    "window_days": round(width_seconds / 86400.0, 4),
                    "candidate_domain": candidate.get("candidate_domain", []),
                    "candidate_topic_keys": candidate.get("candidate_topic_keys", []),
                }
            )

    return {
        "baseline_id": _hash_id("base", {"seed": baseline_seed, "report_run_id": report_run.get("report_run_id", "")}),
        "generation_procedure": "deterministic matched-random baseline preserving report period, candidate count, and each candidate window width; outcomes remain uncoded until reviewer review",
        "random_seed": baseline_seed,
        "candidate_count": len(candidates),
        "baseline_candidates": baseline_candidates,
        "baseline_outcomes": [
            _uncoded_baseline_outcome(item, sidecar)
            for item in baseline_candidates
        ],
    }


def summarize_outcomes(ledger: dict) -> dict:
    """Summarize reviewer-coded outcomes without coercing unresolved statuses."""
    counts = {category: 0 for category in sorted(LOCKED_OUTCOME_CATEGORIES)}
    for entry in ledger.get("outcomes", []):
        category = entry.get("outcome_category")
        if category in counts:
            counts[category] += 1
    denominator = counts["supported_hit"] + counts["supported_non_hit"]
    precision = round(counts["supported_hit"] / denominator, 4) if denominator else None
    return {
        "counts": counts,
        "precision": precision,
        "precision_denominator": denominator,
        "excluded_from_precision": counts["unresolved"] + counts["research_incomplete"] + counts["excluded_by_protocol"],
    }


def build_ablation_report(sidecar: dict, disabled_method_families: list[str]) -> dict:
    """
    Sidecar-native ablation summary.

    A full production ablation reruns generation with method families disabled;
    this helper provides the comparable sidecar accounting layer by reporting
    which pre-registered candidates rely on the disabled families.
    """
    disabled = {str(item) for item in disabled_method_families}
    candidates = [c for c in sidecar.get("candidates", []) if isinstance(c, dict)]
    retained = []
    removed = []
    for candidate in candidates:
        families = {str(item) for item in candidate.get("independent_method_families", [])}
        target = removed if families & disabled else retained
        target.append(candidate.get("candidate_id", ""))
    return {
        "ablation_id": _hash_id("abl", {"run": _report_run_id(sidecar), "disabled": sorted(disabled)}),
        "harness_version": VALIDATION_HARNESS_VERSION,
        "disabled_method_families": sorted(disabled),
        "full_candidate_count": len(candidates),
        "retained_candidate_count": len([item for item in retained if item]),
        "removed_candidate_count": len([item for item in removed if item]),
        "retained_candidate_ids": sorted(item for item in retained if item),
        "removed_candidate_ids": sorted(item for item in removed if item),
        "comparison_basis": "candidate independent_method_families in sidecar; use paired regenerated sidecars for publication metrics",
    }


def asteroid_contribution_report(sidecar: dict) -> dict:
    """Summarize candidate participation by asteroid name."""
    candidates = [c for c in sidecar.get("candidates", []) if isinstance(c, dict)]
    by_asteroid: dict[str, dict] = {}
    with_asteroid = []
    without_asteroid = []
    for candidate in candidates:
        asteroids = [str(item) for item in candidate.get("asteroid_participants", []) if str(item)]
        candidate_id = candidate.get("candidate_id", "")
        if asteroids:
            with_asteroid.append(candidate_id)
        else:
            without_asteroid.append(candidate_id)
        for asteroid in asteroids:
            bucket = by_asteroid.setdefault(asteroid, {"candidate_count": 0, "candidate_ids": []})
            bucket["candidate_count"] += 1
            bucket["candidate_ids"].append(candidate_id)
    for bucket in by_asteroid.values():
        bucket["candidate_ids"] = sorted(item for item in bucket["candidate_ids"] if item)
        bucket["publication_ready"] = bucket["candidate_count"] >= 10
    return {
        "harness_version": VALIDATION_HARNESS_VERSION,
        "candidate_count": len(candidates),
        "with_asteroid_candidate_count": len([item for item in with_asteroid if item]),
        "without_asteroid_candidate_count": len([item for item in without_asteroid if item]),
        "with_asteroid_candidate_ids": sorted(item for item in with_asteroid if item),
        "without_asteroid_candidate_ids": sorted(item for item in without_asteroid if item),
        "per_asteroid": dict(sorted(by_asteroid.items())),
        "publication_rule": "per-asteroid precision claims require at least 10 candidate outcomes involving that asteroid",
    }


def _validate_ledger_shape(ledger: dict) -> None:
    if ledger.get("outcome_ledger_version") != OUTCOME_LEDGER_VERSION:
        raise ValueError("Unsupported outcome_ledger_version")
    if not isinstance(ledger.get("outcomes"), list):
        raise ValueError("Outcome ledger requires an outcomes list")
    baseline = ledger.get("matched_random_baseline")
    if not isinstance(baseline, dict):
        raise ValueError("Outcome ledger requires matched_random_baseline")
    for entry in ledger.get("outcomes", []):
        if not isinstance(entry, dict):
            raise ValueError("Outcome entries must be objects")
        category = entry.get("outcome_category")
        if category not in LOCKED_OUTCOME_CATEGORIES:
            raise ValueError(f"Invalid outcome_category: {category}")
        if entry.get("match_precision", "") not in MATCH_PRECISION_VALUES:
            raise ValueError(f"Invalid match_precision: {entry.get('match_precision')}")
        if entry.get("research_completeness") not in RESEARCH_COMPLETENESS_VALUES:
            raise ValueError(f"Invalid research_completeness: {entry.get('research_completeness')}")
        if entry.get("blind_review_status") not in BLIND_REVIEW_VALUES:
            raise ValueError(f"Invalid blind_review_status: {entry.get('blind_review_status')}")


def _candidate_by_id(sidecar: dict, candidate_id: str) -> dict:
    for candidate in sidecar.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
            return candidate
    raise ValueError(f"Candidate not found in sidecar: {candidate_id}")


def _uncoded_baseline_outcome(baseline_candidate: dict, sidecar: dict) -> dict:
    report_run = sidecar.get("report_run") if isinstance(sidecar.get("report_run"), dict) else {}
    natal_snapshot = sidecar.get("natal_snapshot") if isinstance(sidecar.get("natal_snapshot"), dict) else {}
    return {
        "outcome_id": _hash_id("baseout", baseline_candidate),
        "candidate_id": baseline_candidate.get("baseline_candidate_id", ""),
        "report_run_id": report_run.get("report_run_id", ""),
        "chart_id": natal_snapshot.get("natal_snapshot_id", ""),
        "research_subject": "synthetic matched-random baseline placeholder; not a real reviewed outcome",
        "candidate_window": [baseline_candidate.get("start_at", ""), baseline_candidate.get("end_at", "")],
        "candidate_domain": baseline_candidate.get("candidate_domain", []),
        "pre_registered_evidence": baseline_candidate,
        "chronology_source": "",
        "chronology_source_timestamp": "",
        "outcome_category": "research_incomplete",
        "event_date": "",
        "match_precision": "",
        "research_completeness": "minimal",
        "domain_mismatch": False,
        "non_hit_rationale": "",
        "unresolved_rationale": "Synthetic matched-random baseline has not been reviewer coded.",
        "reviewer_id": "",
        "reviewed_at": "",
        "blind_review_status": "blind",
    }


def _candidate_width_seconds(candidate: dict, start_at: datetime | None, end_at: datetime | None) -> int:
    if start_at and end_at and end_at >= start_at:
        return max(1, int((end_at - start_at).total_seconds()))
    try:
        return max(1, int(float(candidate.get("window_days") or 1.0) * 86400))
    except (TypeError, ValueError):
        return 86400


def _seed_for_sidecar(sidecar: dict) -> int:
    digest = hashlib.sha256(_canonical_json(sidecar).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _report_run_id(sidecar: dict) -> str:
    report_run = sidecar.get("report_run") if isinstance(sidecar.get("report_run"), dict) else {}
    return str(report_run.get("report_run_id") or "")


def _json_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _hash_id(prefix: str, value: Any) -> str:
    return f"{prefix}_{_json_hash(value)[:8]}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if not value:
        return None
    try:
        return _ensure_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except ValueError:
        try:
            parsed = date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
        return datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso_datetime(value: datetime) -> str:
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")
