from unittest.mock import patch

from generate import generate_report


def test_location_report_supports_docx_without_rendering_html(tmp_path):
    routing = {
        "is_location_report_type": lambda report_type: report_type == "location_services.world_lines",
        "build_location_report_artifacts": lambda *_args: {
            "html": "<html>location</html>",
            "context": {"product_name": "World Lines", "sections": []},
            "public_report_type": "location_services.world_lines",
        },
        "location_report_window": lambda *_args: (None, None),
    }
    birth_data = {"name": "Puck", "location": "Peoria, IL", "date": "1992-03-21", "time": "08:11"}

    with patch("generate._location_services_routing", return_value=routing), \
         patch("generate.get_payload", return_value={"payload": True}), \
         patch("generate._write_report_manifest", return_value=str(tmp_path / "manifest.json")), \
         patch("generate._atomic_write_text") as write_html, \
         patch("products.shared.document_output.render_docx_report") as render_docx:
        output_path = generate_report(
            "location_services.world_lines",
            birth_data,
            output_filename="world_lines.docx",
            output_dir=str(tmp_path),
            formats=("docx",),
        )

    expected = tmp_path / "world_lines.docx"
    assert output_path == str(expected)
    write_html.assert_not_called()
    render_docx.assert_called_once_with("location_services.world_lines", {"product_name": "World Lines", "sections": []}, expected)
