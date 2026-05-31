# doc-index-mcp

索引 OpenClaw/OpenCode 官方文档及本地 Markdown，提供语义检索。

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python -m src.server
```

## MCP 工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `search_docs` | query, source?, limit? | 语义检索文档 |
| `get_doc` | doc_id | 获取完整文档 |

## 手动索引官方文档

```python
from src.crawler import OfficialDocCrawler
from src.index_service import IndexService

crawler = OfficialDocCrawler()
index_service = IndexService()

# 爬取 OpenClaw 文档（最多 100 篇）
docs = crawler.crawl_source("openclaw", limit=100)
for doc in docs:
    index_service.add_document(doc)

# 爬取 OpenCode 文档
docs = crawler.crawl_source("opencode", limit=100)
for doc in docs:
    index_service.add_document(doc)
```

## 数据源

| 来源 | 说明 |
|------|------|
| OpenClaw | docs.openclaw.ai（通过 sitemap 爬取） |
| OpenCode | opencode.ai/docs（通过 sitemap 爬取） |
| 本地 | ~/my-claw/*.md（实时监听） |

## 环境变量

- `INDEX_DIR`: ChromaDB 索引目录（默认: ~/.index/doc-index）
- `LOCAL_DOCS_PATH`: 本地文档路径（默认: ~/my-claw）
