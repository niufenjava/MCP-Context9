# doc-index-mcp

索引 OpenClaw/OpenCode/Claude 官方文档及本地 Markdown，提供语义检索。

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python -m src.server
```

## 环境变量

- `INDEX_DIR`: ChromaDB 索引目录 (默认: ~/.index/doc-index)
- `LOCAL_DOCS_PATH`: 本地文档路径 (默认: ~/my-claw)
