import pytest
import tempfile
import os
from src.index_service import IndexService

def test_index_service_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = IndexService(index_dir=tmpdir)
        assert os.path.exists(tmpdir)

def test_index_service_add_document():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = IndexService(index_dir=tmpdir)
        doc = {
            "doc_id": "test-001",
            "title": "Test",
            "source": "local",
            "url": "/tmp/test.md",
            "content": "This is test content"
        }
        service.add_document(doc)
        results = service.search("test")
        assert len(results) >= 1

def test_index_service_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = IndexService(index_dir=tmpdir)
        service.add_document({
            "doc_id": "test-002",
            "title": "Memory Wiki",
            "source": "openclaw",
            "url": "https://docs.openclaw.ai/test",
            "content": "memory-wiki is a plugin"
        })
        results = service.search("memory-wiki", source="openclaw")
        assert any("memory-wiki" in r["title"].lower() or "memory-wiki" in r["content"].lower() for r in results)