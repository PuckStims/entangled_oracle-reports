import os
import sys
from argparse import Namespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generate import (
    InputValidationError,
    _parse_synastry_party_data,
    generate_synastry_report,
)


def test_parse_synastry_party_data_accepts_exact_birth_data():
    args = Namespace(
        name1="Rowan",
        date1="1992-03-21",
        time1="08:11",
        location1="Peoria, IL",
        simple1=False,
        palette="vibrant",
    )

    birth_data = _parse_synastry_party_data(args, "1")

    assert birth_data["name"] == "Rowan"
    assert birth_data["date"] == "1992-03-21"
    assert birth_data["time"] == "08:11"
    assert birth_data["location"] == "Peoria, IL"
    assert birth_data["simple_mode"] is False


def test_parse_synastry_party_data_defaults_to_simple_mode_without_time():
    args = Namespace(
        name2="Mira",
        date2="1995-02-15",
        time2=None,
        location2="Seattle, WA",
        simple2=False,
        palette="vibrant",
    )

    birth_data = _parse_synastry_party_data(args, "2")

    assert birth_data["time"] is None
    assert birth_data["simple_mode"] is True


def test_parse_synastry_party_data_uses_time_even_when_simple_flag_is_set():
    args = Namespace(
        name1="Cher",
        date1="1946-05-20",
        time1="08:11",
        location1="El Centro, CA",
        simple1=True,
        palette="muted",
    )

    birth_data = _parse_synastry_party_data(args, "1")

    assert birth_data["time"] == "08:11"
    assert birth_data["simple_mode"] is False


def test_parse_synastry_party_data_rejects_missing_location():
    args = Namespace(
        name1="Rowan",
        date1="1992-03-21",
        time1="08:11",
        location1="",
        simple1=False,
        palette="vibrant",
    )

    try:
        _parse_synastry_party_data(args, "1")
    except InputValidationError as exc:
        assert "--location1 is required" in str(exc)
    else:
        raise AssertionError("Expected InputValidationError for missing synastry location.")


def test_generate_synastry_report_writes_html(tmp_path):
    person_a = {"name": "Rowan", "date": "1992-03-21", "time": "08:11", "location": "Peoria, IL", "simple_mode": False}
    person_b = {"name": "Mira", "date": "1995-02-15", "time": "18:42", "location": "Seattle, WA", "simple_mode": False}

    with patch("engine.natal_engine.generate_payload", side_effect=[{"payload": "A"}, {"payload": "B"}]), \
         patch("products.synastry.assembler.build_synastry_context", return_value={"context": True}), \
         patch("products.synastry.renderer.render_synastry_html", return_value="<html>synastry</html>"):
        output_path = generate_synastry_report(
            person_a,
            person_b,
            output_filename="synastry_test.html",
            output_dir=str(tmp_path),
        )

    assert output_path == str(tmp_path / "synastry_test.html")
    assert (tmp_path / "synastry_test.html").read_text(encoding="utf-8") == "<html>synastry</html>"
