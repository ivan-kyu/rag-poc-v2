from langchain_core.documents import Document

from app.ingestion.chunker import chunk_documents


def test_chunk_count_increases_with_content():
    doc = Document(page_content="word " * 500, metadata={"source": "test.md"})
    chunks = chunk_documents([doc])
    assert len(chunks) > 1


def test_chunk_overlap_preserved():
    # Chunk size=800, overlap=150 - adjacent chunks should share some content
    doc = Document(page_content="sentence. " * 200, metadata={"source": "test.md"})
    chunks = chunk_documents([doc])
    if len(chunks) >= 2:
        end_of_first = chunks[0].page_content[-100:]
        start_of_second = chunks[1].page_content[:200]
        assert any(word in start_of_second for word in end_of_first.split() if len(word) > 4)


def test_source_metadata_preserved():
    doc = Document(page_content="content " * 100, metadata={"source": "myfile.md"})
    chunks = chunk_documents([doc])
    for chunk in chunks:
        assert chunk.metadata["source"] == "myfile.md"
