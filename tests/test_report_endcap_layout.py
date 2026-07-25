from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


REPORT_TEMPLATES = [
    PROJECT_ROOT / "products" / "daily_horoscope" / "templates" / "daily_horoscope.html",
    PROJECT_ROOT / "products" / "weekly_horoscope" / "templates" / "weekly_horoscope.html",
    PROJECT_ROOT / "products" / "personal_forecast" / "templates" / "personal_forecast.html",
    PROJECT_ROOT / "products" / "soul_ecosystem" / "templates" / "soul_ecosystem.html",
    PROJECT_ROOT / "products" / "year_ahead" / "templates" / "active" / "year_ahead.html",
    PROJECT_ROOT / "products" / "identity_profile" / "templates" / "entangled_identity_profile.html",
]


def _body(template_path: Path) -> str:
    text = template_path.read_text(encoding="utf-8")
    return text[text.index("<body"):]


def test_report_endcap_wraps_final_copy_and_footer_across_reports():
    shared_css = (PROJECT_ROOT / "products" / "shared" / "report_visual_system.css").read_text(
        encoding="utf-8"
    )
    assert ".report-endcap" in shared_css
    assert "break-inside: avoid" in shared_css

    for template_path in REPORT_TEMPLATES:
        body = _body(template_path)
        assert "report-endcap" in body, template_path.name
        assert body.index("report-endcap") < body.rindex("<footer"), template_path.name
