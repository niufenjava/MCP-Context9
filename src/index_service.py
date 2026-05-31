import chromadb
from chromadb.config import Settings
import os
from typing import Optional
from indexer.chunker import chunk_markdown
from indexer.embedder import Embedder

class IndexService:
    def __init__(self, index_dir: str = None):
        self.index_dir = index_dir or os.path.expanduser("~/.index/doc-index")
        os.makedirs(self.index_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.index_dir)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = Embedder()

    def add_document(self, doc: dict):
        """添加文档到索引"""
        chunks = chunk_markdown(doc["content"])
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['doc_id']}-{i}"
            embedding = self.embedder.encode(chunk["content"])
            self.collection.add(
                ids=[chunk_id],
                embeddings=embedding,
                documents=[chunk["content"]],
                metadatas=[{
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "source": doc["source"],
                    "url": doc["url"],
                    "chunk_index": i
                }]
            )

    def search(self, query: str, source: Optional[str] = None, limit: int = 5) -> list[dict]:
        """搜索文档"""
        embedding = self.embedder.encode(query)
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=limit,
            where={"source": source} if source else None
        )
        return [
            {
                "doc_id": meta["doc_id"],
                "title": meta["title"],
                "source": meta["source"],
                "url": meta["url"],
                "content": doc,
                "score": score
            }
            for doc, meta, score in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]

    def get_document(self, doc_id: str) -> Optional[dict]:
        """获取文档所有 chunks"""
        results = self.collection.get(
            where={"doc_id": doc_id}
        )
        if not results["ids"]:
            return None
        chunks = sorted(
            zip(results["metadatas"], results["documents"]),
            key=lambda x: x[0].get("chunk_index", 0)
        )
        return {
            "doc_id": doc_id,
            "title": chunks[0][0]["title"],
            "source": chunks[0][0]["source"],
            "url": chunks[0][0]["url"],
            "content": "\n\n".join(c for _, c in chunks)
        }

    def delete_document(self, doc_id: str):
        """删除文档"""
        self.collection.delete(where={"doc_id": doc_id})