import chromadb
from chromadb.config import Settings
import os
import json
import time
from typing import Optional, Set
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

    def get_indexed_paths(self) -> Set[str]:
        """获取已索引的文件路径集合"""
        paths_file = os.path.join(self.index_dir, "indexed_paths.json")
        if os.path.exists(paths_file):
            with open(paths_file, "r") as f:
                return set(json.load(f))
        return set()

    def save_indexed_paths(self, paths: Set[str]):
        """保存已索引的文件路径集合"""
        paths_file = os.path.join(self.index_dir, "indexed_paths.json")
        with open(paths_file, "w") as f:
            json.dump(list(paths), f)

    def is_file_indexed(self, path: str, mtime: float) -> bool:
        """检查文件是否已索引且未修改"""
        index_meta_file = os.path.join(self.index_dir, "file_mtimes.json")
        if os.path.exists(index_meta_file):
            with open(index_meta_file, "r") as f:
                mtimes = json.load(f)
            return path in mtimes and mtimes[path] >= mtime
        return False

    def save_file_mtime(self, path: str, mtime: float):
        """保存文件修改时间"""
        mtime_file = os.path.join(self.index_dir, "file_mtimes.json")
        mtimes = {}
        if os.path.exists(mtime_file):
            with open(mtime_file, "r") as f:
                mtimes = json.load(f)
        mtimes[path] = mtime
        with open(mtime_file, "w") as f:
            json.dump(mtimes, f)

    def remove_file_mtime(self, path: str):
        """删除文件修改时间记录"""
        mtime_file = os.path.join(self.index_dir, "file_mtimes.json")
        if os.path.exists(mtime_file):
            with open(mtime_file, "r") as f:
                mtimes = json.load(f)
            if path in mtimes:
                del mtimes[path]
            with open(mtime_file, "w") as f:
                json.dump(mtimes, f)