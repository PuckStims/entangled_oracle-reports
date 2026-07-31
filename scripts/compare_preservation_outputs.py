#!/usr/bin/env python3
"""Generate and compare preservation-smoke report outputs.

This helper is intentionally small and conservative. It runs representative
CLI report paths into two directories and compares normalized HTML/manifest
artifacts. Normalization only removes run metadata such as generation
timestamps and absolute output paths; report prose and rendered content remain
diff-sensitive.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLES = {
    "horoscope": [
        "horoscope",
        "--name",
        "Preservation Sample",
        "--date",
        "1990-06-15",
        "--time",
        "14:30",
        "--location",
        "Chicago, IL",
        "--report-date",
        "2026-01-15",
    ],
    "year_ahead": [
        "year_ahead",
        "--name",
        "Preservation Sample",
        "--date",
        "1990-06-15",
        "--time",
        "14:30",
        "--location",
        "Chicago, IL",
        "--report-date",
        "2026-01-15",
    ],
    "soul_ecosystem": [
        "soul_ecosystem",
        "--name",
        "Preservation Sample",
        "--date",
        "1990-06-15",
        "--time",
        "14:30",
        "--location",
        "Chicago, IL",
        "--report-date",
        "2026-01-15",
    ],
    "internal_architecture": [
        "internal_architecture",
        "--name",
        "Preservation Sample",
        "--date",
        "1990-06-15",
        "--time",
        "14:30",
        "--location",
        "Chicago, IL",
        "--report-date",
        "2026-01-15",
        "--report-depth",
        "core",
    ],
}

VOLATILE_KEYS = {
    "generation_date",
    "report_path",
    "trace_file_reference",
}


def _run_reports(output_dir: Path, reports: list[str], *, clean: bool) -> None:
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONHASHSEED", "0")
    for report in reports:
        command = [
            sys.executable,
            "generate.py",
            *SAMPLES[report],
            "--no-browser",
            "--output-dir",
            str(output_dir),
            "--output-filename",
            f"{report}.html",
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, env=env, check=True)


def _normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            if key in VOLATILE_KEYS:
                normalized[key] = f"<{key}>"
            else:
                normalized[key] = _normalize_json(item)
        return normalized
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    if isinstance(value, str):
        return value.replace(str(PROJECT_ROOT), "<PROJECT_ROOT>")
    return value


def _normalize_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = text.replace(str(PROJECT_ROOT), "<PROJECT_ROOT>")
    text = re.sub(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+00:00|Z)",
        "<ISO_TIMESTAMP>",
        text,
    )
    return text


def _normalize_file(path: Path) -> str:
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(_normalize_json(payload), indent=2, sort_keys=True)
    return _normalize_text(path)


def _expected_files(directory: Path, report: str) -> list[Path]:
    return [
        directory / f"{report}.html",
        directory / f"{report}.manifest.json",
    ]


def _compare_dirs(baseline_dir: Path, after_dir: Path, reports: list[str]) -> list[str]:
    failures: list[str] = []
    for report in reports:
        for baseline_path in _expected_files(baseline_dir, report):
            after_path = after_dir / baseline_path.name
            if not baseline_path.exists() or not after_path.exists():
                failures.append(f"Missing artifact for {report}: {baseline_path.name}")
                continue
            before = _normalize_file(baseline_path).splitlines(keepends=True)
            after = _normalize_file(after_path).splitlines(keepends=True)
            if before != after:
                diff = "".join(
                    difflib.unified_diff(
                        before,
                        after,
                        fromfile=str(baseline_path),
                        tofile=str(after_path),
                        n=3,
                    )
                )
                failures.append(diff)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", default="tmp/preservation_baseline")
    parser.add_argument("--after-dir", default="tmp/preservation_after")
    parser.add_argument(
        "--reports",
        nargs="+",
        choices=sorted(SAMPLES),
        default=list(SAMPLES),
    )
    parser.add_argument("--skip-generate-baseline", action="store_true")
    parser.add_argument("--skip-generate-after", action="store_true")
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()

    baseline_dir = (PROJECT_ROOT / args.baseline_dir).resolve()
    after_dir = (PROJECT_ROOT / args.after_dir).resolve()

    if not args.skip_generate_baseline:
        _run_reports(baseline_dir, args.reports, clean=not args.no_clean)
    if not args.skip_generate_after:
        _run_reports(after_dir, args.reports, clean=not args.no_clean)

    failures = _compare_dirs(baseline_dir, after_dir, args.reports)
    if failures:
        print("\n\n".join(failures))
        return 1
    print(f"Preservation outputs match for: {', '.join(args.reports)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
