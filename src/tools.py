from typing import Optional
from functools import lru_cache
import json
from src.index_service import IndexService

_index_service: Optional[IndexService] = None

def get_index_service() -> IndexService:
    global _index_service
    if _index_service is None:
        _index_service = IndexService()
    return _index_service

@lru_cache(maxsize=100)
def _search_cached(query: str, source: str, limit: int) -> str:
    """内部缓存搜索结果，返回 JSON 字符串"""
    service = get_index_service()
    results = service.search(query, source=source or None, limit=limit)
    return json.dumps(results, ensure_ascii=False)

def search_docs(query: str, source: Optional[str] = None, limit: int = 5) -> list[dict]:
    """
    检索相关文档（结果会被缓存）

    Args:
        query: 搜索 query
        source: 可选过滤来源 (openclaw/opencode/local)
        limit: 返回数量，默认 5

    Returns:
        [{doc_id, title, source, url, content, score}, ...]
    """
    cached = _search_cached(query, source or "", limit)
    return json.loads(cached)

def get_doc(doc_id: str) -> dict:
    """
    根据 doc_id 获取完整文档内容

    Args:
        doc_id: 文档唯一标识

    Returns:
        {doc_id, title, source, url, content}
    """
    service = get_index_service()
    doc = service.get_document(doc_id)
    if doc is None:
        return {"error": f"Document not found: {doc_id}"}
    return doc