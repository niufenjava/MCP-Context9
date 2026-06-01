# MCP-Context9

索引 OpenCode、OpenClaw 官方文档及本地 Markdown，提供语义检索。

## 功能

- 语义检索 OpenCode、OpenClaw 官方文档
- 本地 Markdown 文档实时监听索引（~/my-claw）
- MCP 协议集成，OpenClaw/OpenCode 可直接调用
- 搜索结果缓存，重复查询零 CPU
- 增量索引，官方文档用 content hash 检测变化
- 向量存储使用 sqlite-vec（轻量、无 SIGSEGV 问题）

## 安装

```bash
cd /Users/niufen/my-projects/MCP-Context9
pip install -r requirements.txt
```

## 本地启动与停止

```bash
# 启动（后台运行）
./run_server.sh start

# 停止
./run_server.sh stop

# 重启
./run_server.sh restart

# 查看状态
./run_server.sh status
```

或手动：

```bash
# 启动
PYTHONUNBUFFERED=1 .venv/bin/python -m src.server > /tmp/server_out.txt 2>&1 &

# 停止
ps aux | grep "src.server" | grep -v grep | awk '{print $2}' | xargs kill
```

## OpenClaw 配置

在 `~/.openclaw/openclaw.json` 的 `mcp.servers` 中添加：

```json
"context9": {
  "command": "/usr/local/bin/python3",
  "args": ["-m", "src.server"],
  "cwd": "/Users/niufen/my-projects/MCP-Context9",
  "env": {
    "PATH": "/Users/niufen/my-projects/MCP-Context9/.venv/bin:/usr/local/bin:/usr/bin"
  }
}
```

## OpenCode 配置

在 `~/.config/opencode/opencode.jsonc` 中添加：

```json
{
  "mcpServers": {
    "context9": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "src.server"],
      "cwd": "/Users/niufen/my-projects/MCP-Context9",
      "env": {
        "PATH": "/Users/niufen/my-projects/MCP-Context9/.venv/bin:/usr/local/bin:/usr/bin"
      }
    }
  }
}
```

## MCP 工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `search_docs` | query, source?, limit? | 语义检索文档 |
| `get_doc` | doc_id | 获取完整文档 |

### search_docs 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索 query |
| source | string | 否 | 过滤来源：`opencode` / `openclaw` / `local` |
| limit | integer | 否 | 返回数量，默认 5 |

### get_doc 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doc_id | string | 是 | 文档唯一标识 |

## 数据源

| 来源 | 说明 | 更新方式 |
|------|------|----------|
| OpenCode | opencode.ai/docs（35 英文页） | 启动时增量检查 |
| OpenClaw | docs.openclaw.ai（683 英文页） | 启动时增量检查 |
| 本地 | ~/my-claw/*.md | FileWatcher 实时监听 |

## 性能优化

- **延迟加载**：模型首次搜索时才加载
- **搜索缓存**：相同 query 直接返回，CPU ≈ 0
- **增量索引**：跳过未修改的文件
- **sqlite-vec**：轻量 SQLite 扩展，无 Rust 绑定问题

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `INDEX_DIR` | `~/.index/doc-index` | 索引目录（含 sqlite 数据库和 JSON 元数据） |

## 项目结构

```
MCP-Context9/
├── src/
│   ├── server.py         # MCP Server
│   ├── tools.py          # search_docs, get_doc
│   ├── index_service.py  # sqlite-vec 索引
│   ├── crawler.py        # OpenCode 文档爬虫
│   └── file_watcher.py  # 本地文件监听
├── indexer/
│   ├── embedder.py       # fastembed embedding
│   └── chunker.py        # 文档分块
├── tests/
├── .venv/
├── requirements.txt
└── README.md
```

## 技术选型

- **向量数据库**：sqlite-vec（纯 C SQLite 扩展，稳定轻量）
- **Embedding 模型**：BAAI/bge-small-en（384 维，13MB）
- **MCP 协议**：stdio 模式
