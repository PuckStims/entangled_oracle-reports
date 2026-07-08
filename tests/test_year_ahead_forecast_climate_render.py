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


def test_forecast_climate_renders_in_three_report_outputs():
    samples = [
        {
            "args": [
                "--name", "Noah",
                "--date", "2004-07-09",
                "--time", "22:11",
                "--location", "Watertown, WI",
                "--report-date", "2026-06-28",
                "--output-filename", "test_noah_forecast_climate.html",
            ],
            "must_include": ["Primary pattern:", "Most activated territory:"],
        },
        {
            "args": [
                "--name", "Visitor",
                "--date", "1990-06-15",
                "--location", "Peoria, IL",
                "--simple",
                "--report-date", "2026-06-28",
                "--output-filename", "test_visitor_forecast_climate.html",
            ],
            "must_include": ["House- and angle-based routing is withheld without exact birth time."],
        },
        {
            "args": [
                "--name", "Puck",
                "--date", "1992-03-21",
                "--time", "08:11",
                "--location", "Peoria, IL",
                "--report-date", "2026-06-28",
                "--output-filename", "test_puck_forecast_climate.html",
            ],
            "must_include": ["These field qualities organize the recurring conditions already visible across the report"],
        },
    ]

    for sample in samples:
        html_path = _generate(sample["args"])
        html = _html(html_path)
        assert "Forecast climate" in html
        assert "forecast-climate-list" in html
        assert "Primary pattern:" in html
        assert "Primary cycles:" in html
        assert "Field qualities" in html
        assert "No separate convergence window was isolated for this month." not in html
        # Section numbering shifted after "Annual rhythm" (VIII) and "Turning
        # point guide" (X) were inserted ahead of these sections.
        assert "IX. Monthly chapters" in html
        assert "XI. Cycle ledger" in html
        assert "XII. Technical appendix" in html
        assert "XIII. Year integration" in html
        for text in sample["must_include"]:
            assert text in html


if __name__ == "__main__":
    test_forecast_climate_renders_in_three_report_outputs()
