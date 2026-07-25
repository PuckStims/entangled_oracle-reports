from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def _body(template_path: Path) -> str:
    text = template_path.read_text(encoding="utf-8")
    return text[text.index("<body"):]


def test_star_wheel_renders_as_cover_before_reader_guidance():
    personal_body = _body(
        PROJECT_ROOT / "products" / "personal_forecast" / "templates" / "personal_forecast.html"
    )
    assert personal_body.index("</header>") < personal_body.index('class="chart-snapshot"')
    assert personal_body.index('class="chart-snapshot"') < personal_body.index('class="report-record-grid"')
    assert personal_body.index('class="chart-snapshot"') < personal_body.index("How to Use This Forecast")

    soul_body = _body(PROJECT_ROOT / "products" / "soul_ecosystem" / "templates" / "soul_ecosystem.html")
    assert soul_body.index("</header>") < soul_body.index('class="chart-wheel-container"')
    assert soul_body.index('class="chart-wheel-container"') < soul_body.index('class="report-record-grid"')
    assert soul_body.index('class="chart-wheel-container"') < soul_body.index("How to Use This Report")

    year_body = _body(
        PROJECT_ROOT / "products" / "year_ahead" / "templates" / "active" / "year_ahead.html"
    )
    assert year_body.index("</header>") < year_body.index('id="natal-wheel"')
    assert year_body.index('id="natal-wheel"') < year_body.index('id="chart-reference"')
    assert year_body.index('id="natal-wheel"') < year_body.index("How to Use This Almanac")
