import pytest

from products.shared.composers import COMPOSERS, compose_report
from products.shared.document_parity import validate_document_parity


@pytest.mark.parametrize(
    ("report_type", "context"),
    [
        ("horoscope", {"querent_name": "Puck", "todays_sky_block": "Sky prose.", "activation_block": "Activation prose.", "day_ruler_block": "Ruler prose.", "closing_block": "Closing prose."}),
        ("weekly_horoscope", {"querent_name": "Puck", "weekly_theme_overview": "Week prose.", "weekly_work_with": "Work with this.", "weekly_days": [{"day_label": "Monday", "guidance": "Day prose.", "moments": [{"technical_label": "Moon transit", "meaning_primary": "Moment prose."}]}]}),
        ("personal_forecast", {"querent_name": "Puck", "opening_snapshot": "Opening prose.", "themes": [{"theme_label": "Work", "title": "Work theme", "body": "Theme prose."}], "timing_windows": [{"date_label": "Jan 1", "theme": "Work", "best_use": "Plan", "intensity": "high"}], "featured_event": {"title": "Feature", "body_1": "Feature prose."}, "closing_integration": "Closing prose."}),
        ("soul_ecosystem", {"querent_name": "Puck", "souls_story_block": "Story prose.", "core_support_cards": [{"name": "Sun", "body": "Core prose."}], "growth_support_cards": [{"name": "Saturn", "body": "Growth prose."}], "world_support_cards": [{"name": "MC", "body": "World prose."}], "soul_ecosystem_eas_depth": {"dominant": {"available": True, "title": "Depth", "expression": "Depth prose."}}, "primary_archetype_block": "Archetype prose."}),
        ("identity_profile", {"querent_name": "Puck", "portrait_overview_block": "Portrait prose.", "active_index_sections": [{"name": "NGE", "expression": "Expression", "block": "System prose."}], "tension_sections": [{"label": "Tension", "left": "A", "right": "B", "block": "Tension prose."}], "mythic_cast": [{"name": "Mercury", "block": "Cast prose."}]}),
        ("internal_architecture", {"querent_name": "Puck", "opening_synthesis": ["Opening prose."], "architecture_at_a_glance": [{"label": "Mode", "value": "Signal", "summary": "Glance prose."}], "internal_architecture_registers": [{"title": "Register", "consumer_description": "Register prose."}], "internal_architecture_pressure_patterns": [{"name": "Pressure", "activated": "Pattern prose."}], "signal_path_paragraphs": ["Signal prose."], "internal_architecture_practitioner_rows": [{"register": "A", "primary_mode": "B", "secondary_mode": "C", "signal_strength": "D", "source_basis": "E"}]}),
    ],
)
def test_core_composers_register_and_satisfy_their_parity_manifest(report_type, context):
    assert report_type in COMPOSERS
    document = compose_report(report_type, context)

    assert document.report_subtype == report_type
    assert not validate_document_parity(document, context)
