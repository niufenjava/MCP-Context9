from typing import Optional
from src.index_service import IndexService

_index_service: Optional[IndexService] = None

def get_index_service() -> IndexService:
    global _index_service
    if _index_service is None:
        _index_service = IndexService()
    return _index_service

def search_docs(query: str, source: Optional[str] = None, limit: int = 5) -> list[dict]:
    """
    检索相关文档

    Args:
        query: 搜索 query
        source: 可选过滤来源 (openclaw/opencode/claude/local)
        limit: 返回数量，默认 5

    Returns:
        [{doc_id, title, source, url, content, score}, ...]
    """
    service = get_index_service()
    return service.search(query, source=source, limit=limit)

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