from src.devtools_ingest import Document, chunk_document


def test_chunking_preserves_release_diagnostic_context() -> None:
    document = Document(path="build.md", text="build event release diagnostic", release="1.2", build_id="b7")
    assert chunk_document(document, size=2) == ["build event", "release diagnostic"]

