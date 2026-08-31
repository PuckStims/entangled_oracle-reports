from products.shared.composers import compose_report
from products.shared.document_parity import validate_document_parity
from products.shared.document_model import MonthSection, Section


def _context():
    return {
        "querent_name": "Puck",
        "generation_date": "January 01, 2026",
        "report_span_display": "January 2026 - December 2026",
        "methodology_id": "tropical_whole_sign",
        "methodology_label": "Tropical zodiac + Whole Sign houses",
        "palette_name": "vibrant",
        "birth_date_display": "March 21, 1992",
        "birth_time_display": "08:11",
        "birth_location": "Peoria, IL",
        "birth_time_confidence": "Exact",
        "report_version": "Year Ahead v2.0",
        "calculation_record": [{"label": "Zodiac", "value": "Tropical"}],
        "natal_positions": [{"name": "Sun", "position": "0 Aries", "house": "1"}],
        "chart_wheel_svg": "<svg></svg>",
        "wheel_transit_retrograde_planets": ["Saturn"],
        "standard_natal_foundation": {"intro": "Natal baseline.", "sections": [{"title": "Sun", "body": "Foundation prose."}]},
        "year_overview_block": "Year overview.",
        "forecast_shape": "Late-Year Expansion",
        "forecast_shape_details": {"peak_month": "December", "quiet_month": "January"},
        "orientation_summary": {"long_cycle_emphasis": "Saturn", "strongest_annual_themes": ["Structure"]},
        "archetypal_opening_section": {"title": "Your Archetypal Year", "body": "Archetypal prose."},
        "landmarks": [{"title": "Saturn cycle", "block": "Long-cycle prose.", "tone": "structure"}],
        "annual_rhythm_quarters": [{"season_name": "Opening", "summary": "Season prose."}],
        "months": [{"number": 1, "name": "January 2026", "range": "Jan 1 - Jan 31", "arc_label": "Active", "events": [{"title": "Event", "block": "Event prose.", "date_label": "Jan 4", "event_label": "Transit", "tone": "threshold"}]}],
        "turning_point_timeline": [{"entries": [{"title": "Turning point", "date_label": "Jan 4", "intensity_text": "Active"}]}],
        "raw_cycle_ledger": {"title": "Cycle Ledger", "months": [{"name": "January 2026", "entries": [{"title": "Ledger event", "date_label": "Jan 4"}]}]},
        "year_integration_block": "Closing prose.",
    }


def _all_nodes(nodes):
    for node in nodes:
        yield node
        if isinstance(node, (Section, MonthSection)):
            yield from _all_nodes(node.nodes)


def test_year_ahead_composer_uses_context_collections_without_recomputation():
    context = _context()
    document = compose_report("year_ahead", context)
    months = [node for node in _all_nodes(document.nodes) if isinstance(node, MonthSection)]

    assert document.report_subtype == "year_ahead"
    assert document.theme_id == "vibrant"
    assert len(months) == len(context["months"])
    assert months[0].title == context["months"][0]["name"]
    assert not validate_document_parity(document, context)


def test_year_ahead_parity_manifest_exposes_missing_structural_sections():
    context = _context()
    document = compose_report("year_ahead", context)
    broken = document.__class__(
        **{**document.__dict__, "nodes": tuple(node for node in document.nodes if getattr(node, "marker", "") != "cycle-ledger")}
    )

    issues = validate_document_parity(broken, context)

    assert any(issue.marker == "cycle-ledger" for issue in issues)
