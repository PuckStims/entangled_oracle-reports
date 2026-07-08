import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import HOUSE_DOMAINS
from generate import _build_raw_cycle_ledger


def _months():
    return [
        {"name": "June 2026", "short_name": "Jun"},
        {"name": "July 2026", "short_name": "Jul"},
    ]


def _source_events():
    transit = {
        "event_type": "transit",
        "peak_datetime": datetime(2026, 6, 10, tzinfo=timezone.utc),
        "display_anchor_date": "June 10, 2026",
        "entry_date": "June 01, 2026",
        "peak_date": "June 10, 2026",
        "leave_date": "August 14, 2026",
        "duration_days": 74.0,
        "transit_planet": "Saturn",
        "aspect": "Sextile",
        "natal_target": "Saturn",
        "natal_target_display": "Saturn in Virgo",
        "natal_house": 6,
        "orb": 0.1234,
        "cycle_id": "saturn_sextile_saturn_202606",
        "contact_count": 3,
        "contacts": [
            {
                "sequence_index": 1,
                "contact_date": "June 10, 2026",
                "motion_direction": "direct",
                "contact_orb": 0.1234,
                "is_exact": False,
            },
            {
                "sequence_index": 2,
                "contact_date": "July 02, 2026",
                "motion_direction": "retrograde",
                "contact_orb": 0.0003,
                "is_exact": True,
            },
        ],
        "intensity_bar": "◆",
        "intensity_label": "Significant",
        "combined_intensity_score": 0.8,
    }
    station = {
        "event_type": "station",
        "peak_datetime": datetime(2026, 6, 18, tzinfo=timezone.utc),
        "peak_date": "June 18, 2026",
        "entry_date": "June 18, 2026",
        "transit_planet": "Mercury",
        "station_type": "Retrograde",
        "natal_target": "Moon",
        "natal_target_display": "Moon in Libra",
        "natal_house": 7,
        "distance_to_natal_target": 1.234,
        "intensity_bar": "●",
        "intensity_label": "Active",
        "combined_intensity_score": 0.55,
    }
    ingress = {
        "event_type": "ingress",
        "peak_datetime": datetime(2026, 7, 3, tzinfo=timezone.utc),
        "peak_date": "July 03, 2026",
        "entry_date": "July 03, 2026",
        "transit_planet": "Jupiter",
        "house_number": 10,
        "previous_house_number": 9,
        "intensity_bar": "●",
        "intensity_label": "Active",
        "combined_intensity_score": 0.4,
    }
    eclipse = {
        "event_type": "eclipse",
        "peak_datetime": datetime(2026, 7, 12, tzinfo=timezone.utc),
        "peak_date": "July 12, 2026",
        "entry_date": "July 12, 2026",
        "transit_planet": "Solar",
        "eclipse_type": "Solar",
        "eclipse_degree": 20.04,
        "eclipse_sign": "Leo",
        "natal_target": "Sun",
        "natal_target_display": "Sun in Leo",
        "natal_house": 10,
        "distance_to_natal_target": 0.456,
        "intensity_bar": "✦",
        "intensity_label": "Key Window",
        "combined_intensity_score": 0.95,
    }
    convergence = {
        "event_type": "convergence",
        "peak_datetime": datetime(2026, 7, 20, tzinfo=timezone.utc),
        "peak_date": "July 20, 2026",
        "entry_date": "July 14, 2026",
        "leave_date": "July 24, 2026",
        "title": "Public Emergence Convergence",
        "subtitle": "July 14 – July 24, 2026",
        "convergence_pattern": "public_emergence_convergence",
        "constituent_events": [transit, ingress, eclipse],
        "intensity_bar": "▲▲▲",
        "intensity_label": "Convergence",
        "combined_intensity_score": 0.0,
    }
    return [transit, station, ingress, eclipse, convergence]


def _structure_row(ledger: dict, section_key: str, first_column_value: str) -> list:
    for section in ledger["structure_notes"]:
        if section["key"] != section_key:
            continue
        for row in section["rows"]:
            if row[0] == first_column_value:
                return row
    raise AssertionError(f"Missing row for {first_column_value!r} in section {section_key}")


def test_raw_cycle_ledger_preserves_source_record_fields():
    # _build_raw_cycle_ledger deliberately excludes debug-only internals like
    # raw_record/technical_fields; per-event-type detail now lives in the
    # separate `structure_notes` sections instead of on the entry itself.
    ledger = _build_raw_cycle_ledger(_months(), _source_events(), HOUSE_DOMAINS)

    assert ledger["uses_raw_records"] is True
    assert len(ledger["months"]) == 2
    june_entries = ledger["months"][0]["entries"]
    transit_entry = june_entries[0]

    assert transit_entry["event_type_key"] == "natal_transit"
    assert transit_entry["title"] == "Saturn Sextile natal Saturn"
    assert "3-pass cycle" in transit_entry["cycle_structure"]

    transit_row = _structure_row(ledger, "transit_contact_notes", "Saturn")
    assert transit_row[3] == "0.123°"  # Closest Orb
    assert transit_row[6] == "3"  # Pass Count


def test_raw_cycle_ledger_respects_event_family_specific_fields():
    ledger = _build_raw_cycle_ledger(_months(), _source_events(), HOUSE_DOMAINS)
    july_entries = ledger["months"][1]["entries"]

    ingress_entry = next(entry for entry in july_entries if entry["event_type_key"] == "house_ingress")
    eclipse_entry = next(entry for entry in july_entries if entry["event_type_key"] == "eclipse")

    assert ingress_entry["target_house"] == "Career / Public Life"
    eclipse_row = _structure_row(ledger, "eclipse_lunation_notes", "Eclipse")
    assert eclipse_row[5] == "0.456°"  # Closest Orb

    # Convergence windows are routed to their own top-level index, not into
    # the per-month entry list.
    assert not any(entry["event_type_key"] == "convergence" for entry in july_entries)
    assert any(row["title"] == "Public Emergence Convergence" for row in ledger["convergence_index"])


def test_raw_cycle_ledger_empty_state_stays_fallback_safe():
    ledger = _build_raw_cycle_ledger([], _source_events(), HOUSE_DOMAINS)
    assert ledger["months"] == []
    assert ledger["uses_raw_records"] is False
    assert ledger["migration_fallback_ready"] is True


if __name__ == "__main__":
    test_raw_cycle_ledger_preserves_source_record_fields()
    test_raw_cycle_ledger_respects_event_family_specific_fields()
    test_raw_cycle_ledger_empty_state_stays_fallback_safe()
