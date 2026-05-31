# MCP-Context9

索引 OpenClaw/OpenCode 官方文档及本地 Markdown，提供语义检索。

## 功能

- 语义检索官方文档（OpenClaw、OpenCode）
- 本地 Markdown 文档实时监听索引
- MCP 协议集成，OpenClaw/OpenCode 可直接调用

## 安装

```bash
cd /Users/niufen/my-projects/MCP-Context9
pip install -r requirements.txt
```

## 索引官方文档

首次使用需要手动索引官方文档：

```bash
cd /Users/niufen/my-projects/MCP-Context9
source .venv/bin/activate
python -c "
from src.crawler import OfficialDocCrawler
from src.index_service import IndexService

crawler = OfficialDocCrawler()
index_service = IndexService()

# 索引 OpenClaw 文档
print('Indexing OpenClaw docs...')
docs = crawler.crawl_source('openclaw', limit=200)
for doc in docs:
    index_service.add_document(doc)
print(f'Indexed {len(docs)} OpenClaw docs')

# 索引 OpenCode 文档
print('Indexing OpenCode docs...')
docs = crawler.crawl_source('opencode', limit=200)
for doc in docs:
    index_service.add_document(doc)
print(f'Indexed {len(docs)} OpenCode docs')
"
```

## OpenClaw 配置

在 OpenClaw 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "context9": {
      "command": "/Users/niufen/my-projects/MCP-Context9/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/niufen/my-projects/MCP-Context9"
    }
  }
}
```

OpenClaw 启动时会自动启动 MCP Server。

## OpenCode 配置

在 OpenCode 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "context9": {
      "command": "/Users/niufen/my-projects/MCP-Context9/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/niufen/my-projects/MCP-Context9"
    }
  }
}
```

OpenCode 启动时会自动启动 MCP Server。

## MCP 工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `search_docs` | query, source?, limit? | 语义检索文档 |
| `get_doc` | doc_id | 获取完整文档 |

### search_docs 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索 query |
| source | string | 否 | 过滤来源：`openclaw` / `opencode` / `local` |
| limit | integer | 否 | 返回数量，默认 5 |

### get_doc 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doc_id | string | 是 | 文档唯一标识 |

## 数据源

| 来源 | 说明 |
|------|------|
| OpenClaw | docs.openclaw.ai（手动索引） |
| OpenCode | opencode.ai/docs（手动索引） |
| 本地 | ~/my-claw/*.md（自动监听） |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `INDEX_DIR` | `~/.index/doc-index` | ChromaDB 索引目录 |
| `LOCAL_DOCS_PATH` | `~/my-claw` | 本地文档路径 |

## 项目结构

```
MCP-Context9/
├── src/
│   ├── server.py         # MCP Server
│   ├── tools.py          # search_docs, get_doc
│   ├── index_service.py  # ChromaDB 索引
│   ├── crawler.py        # 官方文档爬虫
│   └── file_watcher.py  # 本地文件监听
├── indexer/
│   ├── embedder.py       # fastembed embedding
│   └── chunker.py        # 文档分块
├── tests/
├── .venv/               # Python 虚拟环境
├── requirements.txt
└── README.md
```
