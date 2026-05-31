import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re

class OfficialDocCrawler:
    def __init__(self):
        self.sources = {
            "openclaw": "https://docs.openclaw.ai",
            "opencode": "https://docs.opencode.ai",
            "claude": "https://docs.anthropic.com"
        }
        self.client = httpx.Client(timeout=30.0)

    def crawl_page(self, url: str) -> Optional[str]:
        """爬取单个页面内容"""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            for tag in soup(["script", "style"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            lines = [line for line in text.split("\n") if line.strip()]
            return "\n".join(lines)
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

    def get_doc_title(self, url: str) -> str:
        """从 URL 提取文档标题"""
        path = url.split("/")[-1]
        title = path.replace("-", " ").replace(".md", "")
        return title.title()

    def crawl_source(self, source: str, limit: int = 100):
        """爬取指定来源的所有文档"""
        if source not in self.sources:
            raise ValueError(f"Unknown source: {source}")

        base_url = self.sources[source]
        docs = []

        return docs
