import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _generate(args: list[str]) -> Path:
    cmd = [sys.executable, str(PROJECT_ROOT / "generate.py"), "year_ahead", *args, "--no-browser"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), env=os.environ.copy())
    assert result.returncode == 0, (
        f"generate.py failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    for line in result.stdout.splitlines():
        if line.startswith("[Done] Report saved:"):
            return Path(line.split(":", 1)[1].strip())
    raise AssertionError(f"Could not find output path in stdout:\n{result.stdout}")


def _html(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def test_raw_cycle_ledger_renders_contacts_and_field_notes():
    html_path = _generate(
        [
            "--name", "Noah",
            "--date", "2004-07-09",
            "--time", "22:11",
            "--location", "Watertown, WI",
            "--report-date", "2026-06-28",
            "--output-filename", "test_noah_raw_cycle_ledger.html",
        ]
    )
    html = _html(html_path)
    assert "Cycle Ledger" in html
    assert "Related Convergence" in html
    assert "Convergence Index" in html
    assert "Transit Contact Notes" in html


if __name__ == "__main__":
    test_raw_cycle_ledger_renders_contacts_and_field_notes()
