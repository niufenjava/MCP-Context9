import sqlite3
import sqlite_vec
import os
import json
import threading
from typing import Optional, Set
from indexer.chunker import chunk_markdown
from indexer.embedder import Embedder

class IndexService:
    def __init__(self, index_dir: str = None):
        self.index_dir = index_dir or os.path.expanduser("~/.index/doc-index")
        os.makedirs(self.index_dir, exist_ok=True)

        self.db_path = os.path.join(self.index_dir, "doc-index.db")
        self._conn: Optional[sqlite3.Connection] = None
        self._embedder: Optional[Embedder] = None
        self._embedder_lock = threading.Lock()
        self._tables_initialized = False

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA secure_delete = ON")
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
        return self._conn

    def _init_tables(self):
        if self._tables_initialized:
            return
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS doc_chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                vec_rowid INTEGER NOT NULL
            )
        """)
        dim = self.embedder.dimension
        conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
                embedding float[{dim}]
            )
        """)
        conn.commit()
        self._tables_initialized = True

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            with self._embedder_lock:
                if self._embedder is None:
                    self._embedder = Embedder()
        return self._embedder

    def add_document(self, doc: dict):
        """添加文档到索引"""
        self._init_tables()
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT COUNT(*) FROM doc_chunks WHERE doc_id = ?", (doc["doc_id"],)
        ).fetchone()[0]
        if existing > 0:
            return
        chunks = chunk_markdown(doc["content"])
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['doc_id']}-{i}"
            embedding = self.embedder.encode(chunk["content"])[0]
            vec_blob = sqlite_vec.serialize_float32(embedding)
            cursor = conn.execute(
                "INSERT INTO vec_chunks(embedding) VALUES (?)",
                (vec_blob,)
            )
            vec_rowid = cursor.lastrowid
            conn.execute(
                "INSERT INTO doc_chunks (chunk_id, doc_id, title, source, url, content, chunk_index, vec_rowid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (chunk_id, doc["doc_id"], doc["title"], doc["source"], doc["url"], chunk["content"], i, vec_rowid)
            )
        conn.commit()

    def search(self, query: str, source: Optional[str] = None, limit: int = 5) -> list[dict]:
        """搜索文档"""
        self._init_tables()
        embedding = self.embedder.encode(query)[0]
        import sqlite_vec
        vec_blob = sqlite_vec.serialize_float32(embedding)
        conn = self._get_conn()
        fetch_limit = limit * 20 if source else limit
        results = conn.execute(f"""
            SELECT
                dc.chunk_id, dc.doc_id, dc.title, dc.source, dc.url, dc.content, dc.chunk_index,
                vc.distance
            FROM doc_chunks dc
            JOIN (
                SELECT rowid, distance
                FROM vec_chunks
                WHERE embedding match ?
                ORDER BY distance
                LIMIT {fetch_limit}
            ) vc ON dc.vec_rowid = vc.rowid
        """, (vec_blob,)).fetchall()
        docs = []
        for row in results:
            if source and row[3] != source:
                continue
            docs.append({
                "doc_id": row[1],
                "title": row[2],
                "source": row[3],
                "url": row[4],
                "content": row[5],
                "score": row[7]
            })
            if len(docs) >= limit:
                break
        return docs

    def get_document(self, doc_id: str) -> Optional[dict]:
        """获取文档所有 chunks"""
        self._init_tables()
        conn = self._get_conn()
        results = conn.execute("""
            SELECT doc_id, title, source, url, content, chunk_index
            FROM doc_chunks
            WHERE doc_id = ?
            ORDER BY chunk_index
        """, (doc_id,)).fetchall()
        if not results:
            return None
        first = results[0]
        return {
            "doc_id": first[0],
            "title": first[1],
            "source": first[2],
            "url": first[3],
            "content": "\n\n".join(r[4] for r in results)
        }

    def delete_document(self, doc_id: str):
        """删除文档"""
        self._init_tables()
        conn = self._get_conn()
        rowids = [r[0] for r in conn.execute(
            "SELECT vec_rowid FROM doc_chunks WHERE doc_id = ?", (doc_id,)
        ).fetchall()]
        for rowid in rowids:
            conn.execute("DELETE FROM vec_chunks WHERE rowid = ?", (rowid,))
        conn.execute("DELETE FROM doc_chunks WHERE doc_id = ?", (doc_id,))
        conn.commit()

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
