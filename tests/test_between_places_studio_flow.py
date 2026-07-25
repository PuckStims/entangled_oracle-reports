import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import generate


def test_generate_report_between_places_writes_manifest(monkeypatch, tmp_path: Path):
    manifest_calls = []

    monkeypatch.setattr(generate, "get_payload", lambda birth_data: {"payload": True})

    def fake_artifacts(report_type, payload, birth_data):
        assert report_type == "between_places"
        assert birth_data["destination_a"] == "Lisbon, Portugal"
        assert birth_data["destination_b"] == "Kyoto, Japan"
        return {
            "public_report_type": "between_places",
            "full_report_type": "location_services.between_places",
            "context": {"report_type": "location_services.between_places"},
            "html": "<html><body>between places</body></html>",
        }

    def fake_manifest(**kwargs):
        manifest_calls.append(kwargs)
        manifest_path = tmp_path / "report.manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")
        return str(manifest_path)

    monkeypatch.setattr(generate, "build_location_report_artifacts", fake_artifacts)
    monkeypatch.setattr(generate, "_write_report_manifest", fake_manifest)

    output_path = generate.generate_report(
        "between_places",
        {
            "name": "Aster",
            "date": "1990-01-01",
            "time": "12:00",
            "location": "Chicago, IL",
            "current_location": "Chicago, IL",
            "destination_a": "Lisbon, Portugal",
            "destination_b": "Kyoto, Japan",
            "purpose_lens": "belonging",
        },
        output_filename="report.html",
        output_dir=str(tmp_path),
    )

    assert Path(output_path).exists()
    assert manifest_calls
    assert manifest_calls[0]["report_type"] == "between_places"
