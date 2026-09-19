from devtools_ingest import Document, InfraiClient, ingest_documents


def main() -> None:
    document = Document(
        path="docs/release-notes.md",
        release="2026.09",
        build_id="build-2026-09-02",
        text="The CLI now reports dependency diagnostics during build events. Release operators can inspect the failing package and rerun the verified step.",
    )
    count = ingest_documents(InfraiClient(), "developer-tools-docs", [document])
    print(f"ingested {count} document chunks for release {document.release}")


if __name__ == "__main__":
    main()

