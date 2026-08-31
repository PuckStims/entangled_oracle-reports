import pytest

from products.shared.document_output import OutputOptions, docx_output_path


def test_output_options_are_separate_generation_configuration():
    assert OutputOptions.from_formats(None).formats == ("html",)
    assert OutputOptions(("html", "docx")).formats == ("html", "docx")
    assert str(docx_output_path("output/report.html")).endswith("report.docx")


def test_output_options_reject_unknown_formats():
    with pytest.raises(ValueError, match="Unsupported"):
        OutputOptions(("pdf",))
