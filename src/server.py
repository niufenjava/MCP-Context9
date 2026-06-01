import os
import asyncio
import threading
import hashlib
import time
import mcp
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from src.tools import search_docs, get_doc, get_index_service
from src.file_watcher import FileWatcher
from src.crawler import OfficialDocCrawler, SitemapParser
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

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def url_to_doc_id(source: str, url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"{source}-{h}"


def update_official_docs(source: str, crawler: OfficialDocCrawler, index_service, limit: int = 3000, delay: float = 0.3):
    """增量更新官方文档，对比 sitemap，只爬取有变化的页面"""
    sitemap_url = crawler.sources.get(source)
    if not sitemap_url:
        print(f"[{source}] No sitemap configured")
        return

    print(f"[{source}] Fetching sitemap...")
    sitemap = SitemapParser(sitemap_url)
    all_urls = sitemap.urls

    if source == "openclaw":
        current_urls = [u for u in all_urls if crawler._is_english_url(u, "/")]
    elif source == "opencode":
        current_urls = [u for u in all_urls if crawler._is_english_url(u, "/docs/")]
    else:
        current_urls = all_urls

    current_urls = current_urls[:limit] if limit else current_urls
    current_set = set(current_urls)

    indexed_urls = index_service.get_indexed_urls(source)
    indexed_set = set(indexed_urls)

    new_urls = current_set - indexed_set
    existing_urls = current_set & indexed_set
    deleted_urls = indexed_set - current_set

    print(f"[{source}] Total: {len(current_urls)}, New: {len(new_urls)}, Existing: {len(existing_urls)}, Deleted: {len(deleted_urls)}")

    updated = 0
    skipped = 0
    for i, url in enumerate(existing_urls):
        stored_hash = index_service.get_url_content_hash(url)
        content, new_hash = crawler.crawl_page(url, stored_hash)
        if content is None:
            skipped += 1
        elif new_hash and new_hash == stored_hash:
            skipped += 1
        else:
            title = crawler.get_doc_title(url, content)
            doc_id = url_to_doc_id(source, url)
            index_service.upsert_document({
                "doc_id": doc_id,
                "title": title,
                "source": source,
                "url": url,
                "content": content
            }, new_hash)
            updated += 1
        if (i + 1) % 50 == 0:
            print(f"[{source}] Checked {i+1}/{len(existing_urls)} existing pages, {updated} updated, {skipped} unchanged")
        time.sleep(delay)

    for i, url in enumerate(new_urls):
        content, new_hash = crawler.crawl_page(url)
        if content:
            title = crawler.get_doc_title(url, content)
            doc_id = url_to_doc_id(source, url)
            index_service.upsert_document({
                "doc_id": doc_id,
                "title": title,
                "source": source,
                "url": url,
                "content": content
            }, new_hash)
            updated += 1
        if (i + 1) % 50 == 0:
            print(f"[{source}] Indexed {i+1}/{len(new_urls)} new pages")
        time.sleep(delay)

    for url in deleted_urls:
        index_service.delete_document_by_url(url)
        index_service.remove_url_content_hash(url)

    print(f"[{source}] Done. Updated: {updated}, Skipped (unchanged): {skipped}, Deleted: {len(deleted_urls)}")


if __name__ == "__main__":
    local_docs_path = os.path.expanduser("~/my-claw")
    watcher = FileWatcher(root_dir=local_docs_path)
    watcher_thread = threading.Thread(target=watcher.start, daemon=True)
    watcher_thread.start()
    watcher.index_existing()

    index_service = get_index_service()
    crawler = OfficialDocCrawler()

    print("[Server] Updating OpenCode docs...")
    update_official_docs("opencode", crawler, index_service, limit=150, delay=0.3)

    print("[Server] Updating OpenClaw docs...")
    update_official_docs("openclaw", crawler, index_service, limit=3000, delay=0.3)

    asyncio.run(main())