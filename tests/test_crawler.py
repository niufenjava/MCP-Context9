import pytest
from unittest.mock import patch, MagicMock
from src.crawler import OfficialDocCrawler

def test_crawler_initialization():
    crawler = OfficialDocCrawler()
    assert "openclaw" in crawler.sources
    assert "opencode" in crawler.sources
    assert "claude" in crawler.sources

@patch("src.crawler.httpx.Client")
def test_crawl_page(mock_client):
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "<html><body><h1>Test</h1><p>Content</p></body></html>"
    mock_instance.get.return_value = mock_response
    mock_instance.__enter__.return_value = mock_instance
    mock_client.return_value = mock_instance

    crawler = OfficialDocCrawler()
    content = crawler.crawl_page("https://docs.openclaw.ai/test")
    assert "Test" in content
    assert "Content" in content
