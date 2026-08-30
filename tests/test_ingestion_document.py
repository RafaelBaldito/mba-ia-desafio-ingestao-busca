from pathlib import Path

import pytest
from langchain_core.documents import Document

from src.ingestion_config import APPROVED_EMBEDDING_MODEL, IngestionSettings
from src.ingestion_document import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    IngestionChunkError,
    IngestionSourceError,
    load_and_chunk,
)


def settings(pdf_path: Path) -> IngestionSettings:
    return IngestionSettings(
        openai_api_key="test-key",
        openai_embedding_model=APPROVED_EMBEDDING_MODEL,
        database_url="postgresql://user:password@localhost/app",
        collection_name="chunks",
        pdf_path=pdf_path,
    )


class ControlledLoader:
    def __init__(self, pages=None, error=None):
        self.pages = pages
        self.error = error

    def load(self):
        if self.error:
            raise self.error
        return self.pages


def loader_for(pages=None, error=None):
    calls = []

    def factory(path):
        calls.append(path)
        return ControlledLoader(pages, error)

    factory.calls = calls
    return factory


def test_loads_pages_in_order_and_creates_exact_chunks_without_trimming(tmp_path):
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"controlled")
    text = "A" * 900 + "  " + "B" * 1000 + "\n " + "C" * 300
    pages = [Document(page_content=text[:1200]), Document(page_content=text[1200:])]
    chunks = load_and_chunk(settings(pdf), loader_factory=loader_for(pages))

    assert "".join(chunk.page_content for chunk in chunks).startswith("A" * 900 + "  ")
    assert len(chunks) == 3
    assert [len(chunk.page_content) for chunk in chunks] == [1000, 1000, 505]
    assert chunks[0].page_content[-CHUNK_OVERLAP:] == chunks[1].page_content[:CHUNK_OVERLAP]
    assert chunks[1].page_content[-CHUNK_OVERLAP:] == chunks[2].page_content[:CHUNK_OVERLAP]
    assert [chunk.metadata for chunk in chunks] == [
        {
            "source": "document.pdf",
            "chunk_index": index,
            "embedding_model": APPROVED_EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        }
        for index in range(3)
    ]


def test_page_boundary_is_one_newline_and_whitespace_is_preserved(tmp_path):
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"pdf")
    factory = loader_for([Document(page_content=" first "), Document(page_content=" second ")])
    chunks = load_and_chunk(settings(pdf), loader_factory=factory)
    assert chunks[0].page_content == " first \n second "
    assert factory.calls == [str(pdf)]


@pytest.mark.parametrize(
    "path, contents",
    [("missing.pdf", None), ("wrong.txt", b"text")],
)
def test_invalid_source_fails_before_loader(tmp_path, path, contents):
    source = tmp_path / path
    if contents is not None:
        source.write_bytes(contents)
    factory = loader_for([Document(page_content="text")])
    with pytest.raises(IngestionSourceError):
        load_and_chunk(settings(source), loader_factory=factory)
    assert factory.calls == []


def test_directory_and_unreadable_source_are_rejected(tmp_path, monkeypatch):
    directory = tmp_path / "document.pdf"
    directory.mkdir()
    with pytest.raises(IngestionSourceError):
        load_and_chunk(settings(directory), loader_factory=loader_for())

    source = tmp_path / "unreadable.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr("src.ingestion_document.os.access", lambda *_: False)
    with pytest.raises(IngestionSourceError):
        load_and_chunk(settings(source), loader_factory=loader_for())


def test_loader_failure_and_textless_pdf_are_typed_errors(tmp_path):
    source = tmp_path / "document.pdf"
    source.write_bytes(b"pdf")
    with pytest.raises(IngestionSourceError):
        load_and_chunk(settings(source), loader_factory=loader_for(error=ValueError("malformed")))
    with pytest.raises(IngestionSourceError, match="no text"):
        load_and_chunk(settings(source), loader_factory=loader_for([Document(page_content=" \n")]))


def test_page_without_text_content_is_a_source_error(tmp_path):
    source = tmp_path / "document.pdf"
    source.write_bytes(b"pdf")
    with pytest.raises(IngestionSourceError):
        load_and_chunk(settings(source), loader_factory=loader_for([object()]))


def test_chunk_invariant_failure_is_typed(monkeypatch, tmp_path):
    source = tmp_path / "document.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr(
        "src.ingestion_document.RecursiveCharacterTextSplitter.split_documents",
        lambda self, documents: [Document(page_content="bad"), Document(page_content="also bad")],
    )
    with pytest.raises(IngestionChunkError):
        load_and_chunk(settings(source), loader_factory=loader_for([Document(page_content="valid")]))


@pytest.mark.parametrize(
    "chunks",
    [
        [],
        [Document(page_content="bad"), Document(page_content="bad")],
        [Document(page_content="x" * 1001)],
        [Document(page_content="x" * 1000), Document(page_content="y" * 151)],
    ],
)
def test_all_chunk_contract_boundaries_raise_typed_error(monkeypatch, tmp_path, chunks):
    source = tmp_path / "document.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr(
        "src.ingestion_document.RecursiveCharacterTextSplitter.split_documents",
        lambda self, documents: chunks,
    )
    with pytest.raises(IngestionChunkError):
        load_and_chunk(settings(source), loader_factory=loader_for([Document(page_content="valid")]))
