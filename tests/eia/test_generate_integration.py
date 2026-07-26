from datetime import datetime, timezone
import sys

if "selectors" in sys.modules and not hasattr(sys.modules["selectors"], "__path__"):
    del sys.modules["selectors"]
from generate import build_report_context, render_template

from .test_report_builder import sample_natal_chart


def test_internal_architecture_context_uses_existing_report_builder_path():
    context = build_report_context(
        "internal_architecture",
        {
            "querent_name": "EIA Fixture",
            "birth_date_display": "March 21, 1992",
            "birth_time_display": "08:11",
            "birth_location": "Peoria, IL",
        },
        {"CATALYST": {"activation_score": 2.4, "expression": "Activation field", "activation": "Embodied"}},
        sample_natal_chart(),
        report_start=datetime(2026, 7, 25, tzinfo=timezone.utc),
        report_end=datetime(2026, 7, 25, tzinfo=timezone.utc),
    )

    assert context["internal_architecture"]["report_type"] == "internal_architecture"
    assert len(context["internal_architecture_registers"]) == 7
    assert context["internal_architecture"]["mythic_overlay_optional"]["eas_current"] == "Impact Radius"


def test_internal_architecture_template_renders():
    context = build_report_context(
        "internal_architecture",
        {
            "querent_name": "EIA Fixture",
            "birth_date_display": "March 21, 1992",
            "birth_time_display": "08:11",
            "birth_location": "Peoria, IL",
        },
        {},
        sample_natal_chart(),
    )

    html = render_template("internal_architecture", context)

    assert "Internal Architecture" in html
    assert "Architecture At A Glance" in html
    assert "Your Signal Path" in html
    assert "Calculation Basis" in html
    assert "Blend Grammar" not in html
    assert "When The System Comes Under Pressure" not in html
    assert "Contextual Operating Environments" not in html
    assert context["report_depth"] == "core"
    assert "Technical JSON" not in html
    assert "Developer JSON" not in html
    assert "Score " not in html
    assert "Exact_Birth_Time" not in html


def test_internal_architecture_debug_json_is_opt_in():
    context = build_report_context(
        "internal_architecture",
        {
            "querent_name": "EIA Fixture",
            "birth_date_display": "March 21, 1992",
            "birth_time_display": "08:11",
            "birth_location": "Peoria, IL",
            "include_debug_json": True,
        },
        {},
        sample_natal_chart(),
    )

    html = render_template("internal_architecture", context)

    assert "Developer JSON" in html


def test_internal_architecture_anonymized_sample_identity():
    context = build_report_context(
        "internal_architecture",
        {
            "querent_name": "Puck",
            "birth_date_display": "March 21, 1992",
            "birth_time_display": "08:11",
            "birth_location": "Peoria, IL",
            "sample_identity_mode": "anonymized",
            "sample_display_name": "Sample Client",
        },
        {},
        sample_natal_chart(),
    )

    html = render_template("internal_architecture", context)

    assert context["client_name"] == "Sample Client"
    assert context["internal_architecture"]["client"]["name"] == "Sample Client"
    assert "Founder demo, shared with consent." not in html
    assert "<strong>Puck</strong>" not in html
    assert "Ksisti-Puck LLC" not in html
    assert "Public sample; client name anonymized." in html
    assert "Entangled Oracle - Public sample" in html


def test_internal_architecture_founder_demo_identity_note():
    context = build_report_context(
        "internal_architecture",
        {
            "querent_name": "Puck",
            "birth_date_display": "March 21, 1992",
            "birth_time_display": "08:11",
            "birth_location": "Peoria, IL",
            "sample_identity_mode": "founder_demo",
        },
        {},
        sample_natal_chart(),
    )

    html = render_template("internal_architecture", context)

    assert context["client_name"] == "Puck"
    assert "Founder demo, shared with consent." in html


def test_internal_architecture_expanded_tier_renders_system_layers():
    context = build_report_context(
        "internal_architecture",
        {
            "querent_name": "EIA Fixture",
            "birth_date_display": "March 21, 1992",
            "birth_time_display": "08:11",
            "birth_location": "Peoria, IL",
            "report_depth": "expanded",
        },
        {},
        sample_natal_chart(),
    )

    html = render_template("internal_architecture", context)

    assert context["report_depth"] == "expanded"
    assert "Blend Grammar" in html
    assert "How This Architecture Moves" in html
    assert "When The System Comes Under Pressure" in html
    assert "Restoration Matrix" in html
    assert "Contextual Operating Environments" not in html
    assert "Why This Architecture Was Selected" not in html


def test_internal_architecture_advanced_tier_renders_appendix_layers():
    context = build_report_context(
        "internal_architecture",
        {
            "querent_name": "EIA Fixture",
            "birth_date_display": "March 21, 1992",
            "birth_time_display": "08:11",
            "birth_location": "Peoria, IL",
            "report_depth": "advanced",
        },
        {},
        sample_natal_chart(),
    )

    html = render_template("internal_architecture", context)

    assert "Contextual Operating Environments" in html
    assert "Misread Lenses" in html
    assert "Why This Architecture Was Selected" in html
    assert "activation_state" not in html
    assert "Catalyst Index" not in html
