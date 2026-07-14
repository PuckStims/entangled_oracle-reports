import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _generate(args: list[str]) -> Path:
    cmd = [sys.executable, str(PROJECT_ROOT / "generate.py"), "year_ahead", *args, "--no-browser"]
    env = os.environ.copy()
    env["EO_STDOUT_REPORT_PATHS"] = "1"
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), env=env)
    assert result.returncode == 0, (
        f"generate.py failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    for line in result.stdout.splitlines():
        if line.startswith("[Done] Report path:"):
            return Path(line.split(":", 1)[1].strip())
    raise AssertionError(f"Could not find output path in stdout:\n{result.stdout}")


def _html(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def test_turning_point_timeline_renders_dense_report():
    html = _html(_generate(
        [
            "--name", "Puck",
            "--date", "1992-03-21",
            "--time", "08:11",
            "--location", "Peoria, IL",
            "--report-date", "2026-06-28",
            "--output-filename", "test_turning_timeline_puck.html",
        ]
    ))
    assert "turning-guide-timeline" in html
    assert "turning-guide-month-badge" in html
    assert "Natal target" in html
    assert "Related month" in html
    assert "Intensity" in html


def test_turning_point_timeline_renders_second_exact_report():
    html = _html(_generate(
        [
            "--name", "Mira",
            "--date", "1988-11-04",
            "--time", "14:35",
            "--location", "Peoria, IL",
            "--report-date", "2026-06-28",
            "--output-filename", "test_turning_timeline_mira.html",
        ]
    ))
    assert "turning-guide-timeline" in html
    assert "turning-guide-month-badge" in html
    assert "Natal target" in html


if __name__ == "__main__":
    test_turning_point_timeline_renders_dense_report()
    test_turning_point_timeline_renders_second_exact_report()
