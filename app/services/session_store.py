"""Filesystem-backed session storage for locally generated reports."""

from __future__ import annotations

import json
import gc
import re
import shutil
import secrets
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{24,80}$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_ROOT = PROJECT_ROOT / "runtime" / "studio_sessions"


class SessionNotFoundError(FileNotFoundError):
    """Raised when a requested report session does not exist."""


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def create_session_dir() -> tuple[str, Path]:
    SESSION_ROOT.mkdir(parents=True, exist_ok=True)
    for _attempt in range(10):
        session_id = secrets.token_urlsafe(24)
        session_path = SESSION_ROOT / session_id
        try:
            session_path.mkdir(mode=0o700)
        except FileExistsError:
            continue
        return session_id, session_path
    raise RuntimeError("Could not allocate a unique report session.")


def session_path(session_id: str) -> Path:
    if not SESSION_ID_RE.match(session_id):
        raise SessionNotFoundError("Unknown report session.")
    path = SESSION_ROOT / session_id
    if not path.exists() or not path.is_dir():
        raise SessionNotFoundError("Unknown report session.")
    return path


def report_html_path(session_id: str) -> Path:
    path = session_path(session_id) / "report.html"
    if not path.exists():
        raise SessionNotFoundError("Report has not been generated.")
    return path


def manifest_path(session_id: str) -> Path | None:
    path = session_path(session_id) / "report.manifest.json"
    return path if path.exists() else None


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def delete_session(session_id: str) -> None:
    path = session_path(session_id)
    last_error: PermissionError | None = None
    for _attempt in range(5):
        try:
            shutil.rmtree(path)
            return
        except PermissionError as exc:
            last_error = exc
            gc.collect()
            time.sleep(0.15)
    if last_error:
        raise last_error


def cleanup_expired_sessions(max_age_hours: int = 48) -> int:
    if not SESSION_ROOT.exists():
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    removed = 0
    for child in SESSION_ROOT.iterdir():
        if not child.is_dir():
            continue
        try:
            created = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if created < cutoff:
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
    return removed
