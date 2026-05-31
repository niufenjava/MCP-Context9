import pytest
from indexer.embedder import Embedder

def test_embedder_initialization():
    embedder = Embedder()
    assert embedder.model_name == "BAAI/bge-small-en-v1.5"

def test_embedder_encode_single():
    embedder = Embedder()
    embedding = embedder.encode("hello world")
    assert isinstance(embedding, list)
    assert len(embedding) == 1  # list of one embedding
    assert len(embedding[0]) == 384  # bge-small dimension

def test_embedder_encode_batch():
    embedder = Embedder()
    embeddings = embedder.encode(["hello", "world"])
    assert len(embeddings) == 2
    assert all(len(e) == 384 for e in embeddings)