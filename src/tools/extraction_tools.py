"""BeautifulSoup-based extraction tools for structured data."""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests
from pydantic import BaseModel, Field


class ExtractedData(BaseModel):
    """Extracted structured data from a webpage."""

    url: str = Field(description="Source URL")
    data: List[Dict[str, Any]] = Field(description="Extracted data items")
    success: bool = Field(default=True)
    error: Optional[str] = Field(default=None)


class BeautifulSoupTool:
    """Tool for extracting data using BeautifulSoup."""

    @staticmethod
    def fetch_html(url: str, timeout: int = 10) -> Optional[str]:
        """Fetch HTML content from a URL.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            HTML content or None if failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    @staticmethod
    def extract_by_selectors(
        html: str,
        selectors: Dict[str, str],
        container_selector: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Extract data using CSS selectors.

        Args:
            html: HTML content
            selectors: Dict mapping field names to CSS selectors
            container_selector: Optional selector for container elements

        Returns:
            List of extracted data dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        results = []

        if container_selector:
            # Extract from multiple containers
            containers = soup.select(container_selector)
            for container in containers:
                item = {}
                for field, selector in selectors.items():
                    elements = container.select(selector)
                    if elements:
                        item[field] = elements[0].get_text(strip=True)
                    else:
                        item[field] = None
                if any(item.values()):  # Only add if we extracted something
                    results.append(item)
        else:
            # Extract single items
            item = {}
            for field, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    item[field] = elements[0].get_text(strip=True)
                else:
                    item[field] = None
            if any(item.values()):
                results.append(item)

        return results

    @staticmethod
    def extract_table(html: str, table_selector: str = "table") -> List[Dict[str, str]]:
        """Extract data from HTML tables.

        Args:
            html: HTML content
            table_selector: CSS selector for the table

        Returns:
            List of row dictionaries with column headers as keys
        """
        soup = BeautifulSoup(html, 'lxml')
        table = soup.select_one(table_selector)

        if not table:
            return []

        # Get headers
        headers = []
        header_row = table.select_one('thead tr') or table.select_one('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.select('th, td')]

        # Get rows
        rows = []
        body = table.select_one('tbody') or table
        for row in body.select('tr')[1:]:  # Skip header row
            cells = [td.get_text(strip=True) for td in row.select('td')]
            if cells and len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))

        return rows

    @staticmethod
    def extract_links(
        html: str,
        link_selector: str = "a",
        base_url: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Extract links from HTML.

        Args:
            html: HTML content
            link_selector: CSS selector for links
            base_url: Base URL for resolving relative links

        Returns:
            List of dicts with 'text' and 'url' keys
        """
        soup = BeautifulSoup(html, 'lxml')
        links = []

        for link in soup.select(link_selector):
            href = link.get('href')
            text = link.get_text(strip=True)

            if href:
                # Resolve relative URLs
                if base_url and not href.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)

                links.append({
                    'text': text,
                    'url': href
                })

        return links

    def extract_from_url(
        self,
        url: str,
        selectors: Dict[str, str],
        container_selector: Optional[str] = None,
    ) -> ExtractedData:
        """Fetch a URL and extract data.

        Args:
            url: URL to fetch
            selectors: CSS selectors for extraction
            container_selector: Optional container selector

        Returns:
            ExtractedData with results
        """
        html = self.fetch_html(url)
        if not html:
            return ExtractedData(url=url, data=[], success=False, error="Failed to fetch URL")

        try:
            data = self.extract_by_selectors(html, selectors, container_selector)
            return ExtractedData(url=url, data=data, success=True)
        except Exception as e:
            return ExtractedData(url=url, data=[], success=False, error=str(e))
