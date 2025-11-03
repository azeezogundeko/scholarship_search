"""Crawl4AI integration for web crawling and extraction."""

import asyncio
from typing import Optional, List, Dict, Any
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field


class CrawlResult(BaseModel):
    """Result from crawling a web page."""

    url: str = Field(description="The URL that was crawled")
    title: Optional[str] = Field(default=None, description="Page title")
    markdown: str = Field(description="Page content as Markdown")
    links: List[str] = Field(default_factory=list, description="Links found on the page")
    success: bool = Field(default=True, description="Whether crawl was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class Crawl4AITool:
    """Tool for crawling web pages with Crawl4AI."""

    def __init__(self, headless: bool = True, browser: str = "chromium"):
        """Initialize Crawl4AI tool.

        Args:
            headless: Run browser in headless mode
            browser: Browser to use (chromium, firefox, webkit)
        """
        self.headless = headless
        self.browser = browser

    async def crawl_url(
        self,
        url: str,
        extract_links: bool = True,
        wait_for: Optional[str] = None,
    ) -> CrawlResult:
        """Crawl a single URL and extract content.

        Args:
            url: URL to crawl
            extract_links: Whether to extract links from the page
            wait_for: CSS selector to wait for before extracting

        Returns:
            CrawlResult with page content and metadata
        """
        try:
            async with AsyncWebCrawler(
                headless=self.headless,
                browser_type=self.browser
            ) as crawler:
                result = await crawler.arun(
                    url=url,
                    bypass_cache=True,
                    word_count_threshold=10,
                )

                links = []
                if extract_links and result.links:
                    # Extract internal and external links
                    links = [link.get('href', '') for link in result.links.get('internal', [])]
                    links.extend([link.get('href', '') for link in result.links.get('external', [])])

                return CrawlResult(
                    url=url,
                    title=result.metadata.get('title') if result.metadata else None,
                    markdown=result.markdown or "",
                    links=links,
                    success=result.success,
                )
        except Exception as e:
            return CrawlResult(
                url=url,
                markdown="",
                success=False,
                error=str(e),
            )

    async def crawl_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 5,
    ) -> List[CrawlResult]:
        """Crawl multiple URLs concurrently.

        Args:
            urls: List of URLs to crawl
            max_concurrent: Maximum number of concurrent crawls

        Returns:
            List of CrawlResult objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_semaphore(url: str) -> CrawlResult:
            async with semaphore:
                return await self.crawl_url(url)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        crawl_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                crawl_results.append(CrawlResult(
                    url=urls[i],
                    markdown="",
                    success=False,
                    error=str(result),
                ))
            else:
                crawl_results.append(result)

        return crawl_results

    async def deep_crawl(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 10,
        url_filter: Optional[callable] = None,
    ) -> List[CrawlResult]:
        """Perform deep crawling starting from a URL.

        Args:
            start_url: Starting URL
            max_depth: Maximum depth to crawl
            max_pages: Maximum number of pages to crawl
            url_filter: Optional function to filter URLs (return True to include)

        Returns:
            List of CrawlResult objects
        """
        visited = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        results = []

        while to_visit and len(results) < max_pages:
            url, depth = to_visit.pop(0)

            if url in visited or depth > max_depth:
                continue

            visited.add(url)

            # Crawl the URL
            result = await self.crawl_url(url)
            results.append(result)

            # Add links to visit queue if we haven't reached max depth
            if depth < max_depth and result.success:
                for link in result.links:
                    if link not in visited:
                        # Apply URL filter if provided
                        if url_filter is None or url_filter(link):
                            to_visit.append((link, depth + 1))

        return results


# Synchronous wrapper for use in non-async contexts
def crawl_url_sync(url: str, headless: bool = True) -> CrawlResult:
    """Synchronous wrapper for crawling a single URL.

    Args:
        url: URL to crawl
        headless: Run browser in headless mode

    Returns:
        CrawlResult with page content
    """
    tool = Crawl4AITool(headless=headless)
    return asyncio.run(tool.crawl_url(url))
