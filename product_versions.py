"""
Central production version registry and file-fingerprint helpers.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Iterable

from config import BASE_DIR, CONTENT_PACKS, PRODUCTS_DIR


PRODUCTION_BASELINE_VERSION = "2026.06.30"
REPORT_MANIFEST_SCHEMA_VERSION = "1.0.0"
FINAL_BASELINE_PACKAGE_VERSION = "1.0.0"

PACKAGE_VERSIONS = {
    "formula_modules": "2026.06.30",
    "standard_engine_package": "2026.06.30",
    "established_niche_registry": "2026.06.30",
    "eo_proprietary_formula_package": "2026.06.30",
    "content_libraries": "2026.06.30",
    "block_files": "2026.06.30",
    "templates": "2026.06.30",
    "visual_system_css": "2026.06.30",
    "report_generation_code": "2026.06.30",
    "output_package": "2026.06.30",
}

REPORT_TYPE_VERSIONS = {
    "horoscope": "Horoscope v1.0",
    "weekly_horoscope": "Weekly Horoscope v0.1",
    "year_ahead": "Year Ahead v2.0",
    "personal_forecast": "Personal Forecast v1.0",
    "soul_ecosystem": "Soul Ecosystem v1.0",
    "internal_architecture": "Internal Architecture v0.1",
}

TEMPLATE_MAP = {
    "horoscope": os.path.join(PRODUCTS_DIR, "daily_horoscope", "templates", "daily_horoscope.html"),
    "weekly_horoscope": os.path.join(PRODUCTS_DIR, "weekly_horoscope", "templates", "weekly_horoscope.html"),
    "year_ahead": os.path.join(PRODUCTS_DIR, "year_ahead", "templates", "active", "year_ahead.html"),
    "personal_forecast": os.path.join(PRODUCTS_DIR, "personal_forecast", "templates", "personal_forecast.html"),
    "soul_ecosystem": os.path.join(PRODUCTS_DIR, "soul_ecosystem", "templates", "soul_ecosystem.html"),
    "internal_architecture": os.path.join(PRODUCTS_DIR, "internal_architecture", "templates", "internal_architecture.html"),
}

VISUAL_SYSTEM_FILES = [
    os.path.join(PRODUCTS_DIR, "shared", "report_visual_system.css"),
    os.path.join(PRODUCTS_DIR, "shared", "REPORT_PDF_WORKFLOW.md"),
]


def _normalize_path(path: str) -> str:
    return os.path.normpath(path)


def _existing_files(paths: Iterable[str]) -> list[str]:
    existing = []
    for path in paths:
        normalized = _normalize_path(path)
        if os.path.isfile(normalized):
            existing.append(normalized)
    return sorted(set(existing))


def _walk_files(root: str, suffixes: tuple[str, ...]) -> list[str]:
    collected: list[str] = []
    for current_root, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(suffixes):
                collected.append(os.path.join(current_root, name))
    return _existing_files(collected)


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint_files(paths: Iterable[str], *, package_version: str) -> dict:
    files = _existing_files(paths)
    digest = hashlib.sha256()
    file_records = []
    for path in files:
        relative = os.path.relpath(path, BASE_DIR)
        file_hash = _sha256_file(path)
        digest.update(relative.encode("utf-8"))
        digest.update(file_hash.encode("utf-8"))
        file_records.append(
            {
                "path": relative.replace("\\", "/"),
                "sha256": file_hash,
            }
        )
    return {
        "package_version": package_version,
        "file_count": len(file_records),
        "fingerprint": digest.hexdigest(),
        "files": file_records,
    }


def report_version(report_type: str) -> str:
    return REPORT_TYPE_VERSIONS.get(report_type, "Unknown Report Version")


def template_path(report_type: str) -> str:
    return TEMPLATE_MAP.get(report_type, TEMPLATE_MAP["horoscope"])


def _report_block_paths(report_type: str, content_pack: str) -> list[str]:
    if report_type == "year_ahead":
        pack = CONTENT_PACKS.get(content_pack) or CONTENT_PACKS["plainspeak"]
        return [value for value in pack.values() if isinstance(value, str) and os.path.isfile(value)]
    if report_type == "personal_forecast":
        pack = CONTENT_PACKS.get(content_pack) or CONTENT_PACKS["plainspeak"]
        paths = []
        if isinstance(pack.get("personal_forecast"), str):
            paths.append(pack["personal_forecast"])
        if isinstance(pack.get("standard_natal_foundation"), str):
            paths.append(pack["standard_natal_foundation"])
        return _existing_files(paths)
    block_dirs = {
        "horoscope": os.path.join(PRODUCTS_DIR, "daily_horoscope", "blocks"),
        "weekly_horoscope": os.path.join(PRODUCTS_DIR, "weekly_horoscope", "blocks"),
        "soul_ecosystem": os.path.join(PRODUCTS_DIR, "soul_ecosystem", "blocks"),
        "internal_architecture": os.path.join(BASE_DIR, "content", "eia"),
    }
    block_root = block_dirs.get(report_type)
    if not block_root or not os.path.isdir(block_root):
        return []
    return _walk_files(block_root, (".json", ".md", ".html"))


def build_version_registry(report_type: str, content_pack: str) -> dict:
    formula_paths = _walk_files(os.path.join(BASE_DIR, "formulas"), (".py",))
    standard_paths = _walk_files(os.path.join(BASE_DIR, "formulas", "standard"), (".py",))
    established_niche_paths = _existing_files(
        [
            os.path.join(BASE_DIR, "formulas", "established_niche.py"),
            os.path.join(BASE_DIR, "formulas", "governance_registry.py"),
        ]
    )
    eo_paths = _existing_files(
        [
            os.path.join(BASE_DIR, "formulas", "proprietary_indexes.py"),
            os.path.join(BASE_DIR, "products", "year_ahead", "blocks", "shared", "Standard_Natal_Foundation_Blocks.json"),
        ]
    )
    content_library_paths = _walk_files(os.path.join(BASE_DIR, "products"), (".json", ".html", ".css", ".md"))
    report_generation_paths = _existing_files(
        [os.path.join(BASE_DIR, "generate.py")]
        + _walk_files(os.path.join(BASE_DIR, "selectors"), (".py",))
        + _walk_files(os.path.join(BASE_DIR, "engine"), (".py",))
        + _walk_files(os.path.join(BASE_DIR, "eia_engine"), (".py",))
    )
    block_paths = _report_block_paths(report_type, content_pack)
    template_paths = _existing_files([template_path(report_type)])

    return {
        "production_baseline_version": PRODUCTION_BASELINE_VERSION,
        "report_manifest_schema_version": REPORT_MANIFEST_SCHEMA_VERSION,
        "report_version": report_version(report_type),
        "formula_modules": fingerprint_files(
            formula_paths,
            package_version=PACKAGE_VERSIONS["formula_modules"],
        ),
        "standard_engine_package": fingerprint_files(
            standard_paths,
            package_version=PACKAGE_VERSIONS["standard_engine_package"],
        ),
        "established_niche_registry": fingerprint_files(
            established_niche_paths,
            package_version=PACKAGE_VERSIONS["established_niche_registry"],
        ),
        "eo_proprietary_formula_package": fingerprint_files(
            eo_paths,
            package_version=PACKAGE_VERSIONS["eo_proprietary_formula_package"],
        ),
        "content_libraries": fingerprint_files(
            content_library_paths,
            package_version=PACKAGE_VERSIONS["content_libraries"],
        ),
        "block_files": fingerprint_files(
            block_paths,
            package_version=PACKAGE_VERSIONS["block_files"],
        ),
        "templates": fingerprint_files(
            template_paths,
            package_version=PACKAGE_VERSIONS["templates"],
        ),
        "visual_system_css": fingerprint_files(
            VISUAL_SYSTEM_FILES,
            package_version=PACKAGE_VERSIONS["visual_system_css"],
        ),
        "report_generation_code": fingerprint_files(
            report_generation_paths,
            package_version=PACKAGE_VERSIONS["report_generation_code"],
        ),
        "output_package": {
            "package_version": PACKAGE_VERSIONS["output_package"],
            "schema_version": REPORT_MANIFEST_SCHEMA_VERSION,
            "final_baseline_package_version": FINAL_BASELINE_PACKAGE_VERSION,
        },
        "content_pack": {
            "name": content_pack,
            "version": PACKAGE_VERSIONS["content_libraries"],
            "declared_inputs": [
                os.path.relpath(path, BASE_DIR).replace("\\", "/")
                for path in block_paths
            ],
        },
    }


def write_json(path: str, payload: dict) -> None:
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    directory = os.path.dirname(path) or "."
    temp_name = f".{os.path.basename(path)}.{uuid.uuid4().hex}.tmp"
    temp_path = os.path.join(directory, temp_name)
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
