import httpx
from bs4 import BeautifulSoup
from typing import Optional
import time
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

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
            "opencode": "https://opencode.ai/docs/sitemap-index.xml"
        }
        self.client = httpx.Client(timeout=30.0)
        self.lang_prefixes = {
            "ar", "bs", "da", "de", "es", "fa", "fr", "id", "it", "ja",
            "ko", "nb", "nl", "pl", "pt-br", "ru", "th", "tr", "uk",
            "vi", "zh-cn", "zh-tw"
        }

    def _is_english_url(self, url: str, base_path: str = "") -> bool:
        """Check if URL is English version (no language prefix in path)"""
        parsed = urlparse(url)
        path = parsed.path
        if base_path and path.startswith(base_path):
            path = path[len(base_path):]
        parts = [p for p in path.split("/") if p]
        if not parts:
            return True
        first_part = parts[0].lower()
        if first_part in self.lang_prefixes:
            return False
        lang_base = first_part.split("-")[0]
        if lang_base in self.lang_prefixes:
            return False
        return True

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

    def crawl_source(self, source: str, limit: int = 100, delay: float = 0.5, english_only: bool = True) -> list[dict]:
        """爬取指定来源的所有文档"""
        if source not in self.sources:
            raise ValueError(f"Unknown source: {source}")

        sitemap_url = self.sources[source]
        docs = []

        try:
            if sitemap_url.endswith(".xml"):
                sitemap = SitemapParser(sitemap_url)
                all_urls = sitemap.urls
                if english_only:
                    if source == "openclaw":
                        all_urls = [u for u in all_urls if self._is_english_url(u, "/")]
                    elif source == "opencode":
                        all_urls = [u for u in all_urls if self._is_english_url(u, "/docs/")]
                urls = all_urls[:limit] if limit else all_urls
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
