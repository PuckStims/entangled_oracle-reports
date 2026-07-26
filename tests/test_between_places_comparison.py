"""
Tests for Between Places comparison logic.
"""
from products.location_services.between_places.plugin import BetweenPlacesProduct
from products.location_services.between_places.comparison import build_comparison_record
from test_location_services_relocated_payload import _build_natal_payload

def test_comparison_record_generates_valid_tradeoffs():
    record_a = {
        "destination_context": {"location_id": "us-tx-austin", "display_name": "Austin, TX"},
        "theme_clusters": {"clusters": [{"theme_keys": ["career_visibility"]}]},
        "evidence_record": {
            "relocated_angle_contacts": [{"body": "Venus", "angle": "Midheaven", "contact_strength": "tight"}],
            "planet_house_changes": [{"body": "Moon", "movement_type": "leaves_angular"}],
        },
        "goal_profile": {"goals": [{"goal_key": "career_visibility", "opportunity": 0.8}]},
    }
    record_b = {
        "destination_context": {"location_id": "us-ny-new_york", "display_name": "New York, NY"},
        "theme_clusters": {"clusters": [{"theme_keys": ["career_visibility", "money_resources"]}]},
        "evidence_record": {
            "relocated_angle_contacts": [],
            "planet_house_changes": [],
        },
        "goal_profile": {"goals": [{"goal_key": "career_visibility", "opportunity": 0.3}]},
    }
    
    comp = build_comparison_record([record_a, record_b])
    
    assert "career_visibility" in comp["shared_themes"]
    assert "money_resources" in comp["divergent_themes"]
    assert any(t["stronger_location_id"] == "us-tx-austin" and t["goal_key"] == "career_visibility" for t in comp["tradeoffs"])
    assert any(diff["description"] == "Moon leaves angular is uniquely foregrounded here." for diff in comp["strongest_differences"])
    assert "career visibility" in comp["comparison_summary"].lower()

def test_plugin_between_places_integration():
    plugin = BetweenPlacesProduct()
    context = plugin.build_context(
        _build_natal_payload(),
        {"latitude": 30.2672, "longitude": -97.7431, "timezone": "America/Chicago", "display_name": "Austin, TX", "location_id": "us-tx-austin"},
        {"latitude": 40.7128, "longitude": -74.0060, "timezone": "America/New_York", "display_name": "New York, NY", "location_id": "us-ny-new_york"},
        purpose_lens="career",
    )
    
    assert context["context_version"] == "between_places_context_v0.3.0"
    assert "comparison_record" in context
    assert "record_a" in context
    assert "record_b" in context
    assert context["purpose_lens_label"] == "Career"
    assert context["comparison_record"]["comparison_summary"]
    assert context["decision_notes"]
    assert len(context["compact_profile_a"]["goal_highlights"]) <= 3
    
    html = plugin.render_html(context)
    assert "Austin, TX" in html
    assert "New York, NY" in html
    assert "Comparison Summary" in html
    assert "Decision Notes" in html
