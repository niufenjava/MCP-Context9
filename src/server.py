import os
import threading
import mcp
from mcp.server import Server
from mcp.types import Tool, TextContent
from src.tools import search_docs, get_doc
from src.file_watcher import FileWatcher
import json

server = Server("doc-index-mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_docs",
            description="检索相关文档",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索 query"},
                    "source": {"type": "string", "description": "可选过滤来源 (openclaw/opencode/claude/local)"},
                    "limit": {"type": "integer", "description": "返回数量，默认 5", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_doc",
            description="根据 doc_id 获取完整文档内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "文档唯一标识"}
                },
                "required": ["doc_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "search_docs":
        results = search_docs(
            query=arguments["query"],
            source=arguments.get("source"),
            limit=arguments.get("limit", 5)
        )
        return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
    elif name == "get_doc":
        result = get_doc(doc_id=arguments["doc_id"])
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    else:
        raise ValueError(f"Unknown tool: {name}")

local_docs_path = os.path.expanduser("~/my-claw")
watcher = FileWatcher(root_dir=local_docs_path)
watcher_thread = threading.Thread(target=watcher.start, daemon=True)
watcher_thread.start()

watcher.index_existing()

if __name__ == "__main__":
    mcp.server.run_server(server)