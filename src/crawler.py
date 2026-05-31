import httpx
from bs4 import BeautifulSoup
from typing import Optional
import os
import time
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import threading
import schedule

class SitemapParser:
    def __init__(self, url: str):
        self.urls = []
        try:
            response = httpx.Client(timeout=30.0).get(url)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            if root.tag.endswith("sitemapindex"):
                for sitemap in root.findall("sm:sitemap", ns):
                    loc = sitemap.find("sm:loc", ns)
                    if loc is not None and loc.text:
                        sub_sitemap = SitemapParser(loc.text)
                        self.urls.extend(sub_sitemap.urls)
            else:
                for url_elem in root.findall("sm:url", ns):
                    loc = url_elem.find("sm:loc", ns)
                    if loc is not None and loc.text:
                        self.urls.append(loc.text)
        except Exception as e:
            print(f"Error parsing sitemap {url}: {e}")

class OfficialDocCrawler:
    def __init__(self):
        self.sources = {
            "openclaw": "https://docs.openclaw.ai/sitemap.xml",
            "opencode": "https://opencode.ai/docs/sitemap-index.xml",
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

    def get_doc_title(self, url: str, content: str = "") -> str:
        """从 URL 或内容提取文档标题"""
        if content:
            soup = BeautifulSoup(content, "lxml")
            h1 = soup.find("h1")
            if h1:
                return h1.get_text(strip=True)
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        if parts:
            return parts[-1].replace("-", " ").replace(".md", "").title()
        return "Untitled"

    def crawl_source(self, source: str, limit: int = 100, delay: float = 0.5) -> list[dict]:
        """爬取指定来源的所有文档"""
        if source not in self.sources:
            raise ValueError(f"Unknown source: {source}")

        sitemap_url = self.sources[source]
        docs = []

        try:
            if sitemap_url.endswith(".xml"):
                sitemap = SitemapParser(sitemap_url)
                urls = sitemap.urls[:limit] if limit else sitemap.urls
            else:
                urls = []

            for i, url in enumerate(urls):
                print(f"[{source}] Crawling {i+1}/{len(urls)}: {url}")
                content = self.crawl_page(url)
                if content:
                    title = self.get_doc_title(url, content)
                    doc_id = f"{source}-{i:04d}"
                    docs.append({
                        "doc_id": doc_id,
                        "title": title,
                        "source": source,
                        "url": url,
                        "content": content
                    })
                time.sleep(delay)

        except Exception as e:
            print(f"Error parsing sitemap {sitemap_url}: {e}")

        return docs

    def crawl_all(self, limit_per_source: int = 100) -> list[dict]:
        """爬取所有来源的文档"""
        all_docs = []
        for source in self.sources:
            docs = self.crawl_source(source, limit=limit_per_source)
            all_docs.extend(docs)
        return all_docs


class CrawlScheduler:
    def __init__(self, crawler: OfficialDocCrawler, index_service, interval_hours: int = 1):
        self.crawler = crawler
        self.index_service = index_service
        self.interval_hours = interval_hours
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _job(self):
        """Run incremental crawl and update index"""
        print(f"[Scheduler] Starting incremental crawl...")
        for source in self.crawler.sources:
            docs = self.crawler.crawl_source(source, limit=50, delay=0.3)
            for doc in docs:
                self.index_service.add_document(doc)
        print(f"[Scheduler] Incremental crawl complete")

    def start(self):
        """Start the scheduler in a background thread"""
        self._stop_event.clear()
        schedule.every(self.interval_hours).hours.do(self._job)

        def run_scheduler():
            while not self._stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)

        self._thread = threading.Thread(target=run_scheduler, daemon=True)
        self._thread.start()
        print(f"[Scheduler] Started with {self.interval_hours}h interval")

    def stop(self):
        """Stop the scheduler"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("[Scheduler] Stopped")
