import pytest
from indexer.chunker import chunk_text, chunk_markdown

def test_chunk_text_by_size():
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 600 for c in chunks)

def test_chunk_markdown_preserves_headers():
    md = "# Title\n\nContent 1\n\n## Section\n\nContent 2"
    chunks = chunk_markdown(md)
    assert any(c["title"] == "Title" for c in chunks)
    assert any(c["title"] == "Section" for c in chunks)

def test_chunk_overlap():
    text = " ".join(["word"] * 1000)
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    if len(chunks) >= 2:
        assert chunks[0][-20:] == chunks[1][:20]