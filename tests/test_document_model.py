from products.shared.document_model import DataTable, Heading, ReportDocument, Section


def test_document_model_supports_nested_semantic_nodes():
    document = ReportDocument(
        title="Test report",
        nodes=(Section("Overview", (Heading("A heading", level=2),), marker="overview"),),
        theme_id="vibrant",
    )

    assert document.nodes[0].marker == "overview"
    assert document.nodes[0].nodes[0].level == 2


def test_data_table_rejects_misaligned_rows():
    try:
        DataTable(("A", "B"), (("only one",),))
    except ValueError as exc:
        assert "header width" in str(exc)
    else:
        raise AssertionError("Expected row-width validation to fail.")
