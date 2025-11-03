"""Search tools for Google Custom Search and Brave Search APIs."""

import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from googleapiclient.discovery import build


class SearchResult(BaseModel):
    """A single search result."""

    title: str = Field(description="Result title")
    url: str = Field(description="Result URL")
    snippet: str = Field(description="Result snippet/description")
    source: str = Field(description="Search engine used (google, brave)")


class GoogleSearchTool:
    """Tool for Google Custom Search API."""

    def __init__(self, api_key: str, cse_id: str):
        """Initialize Google Search tool.

        Args:
            api_key: Google API key
            cse_id: Custom Search Engine ID
        """
        self.api_key = api_key
        self.cse_id = cse_id
        self.service = build("customsearch", "v1", developerKey=api_key)

    def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> List[SearchResult]:
        """Search using Google Custom Search API.

        Args:
            query: Search query
            num_results: Number of results to return (max 10 per request)
            **kwargs: Additional parameters for the API

        Returns:
            List of SearchResult objects
        """
        results = []
        num_results = min(num_results, 10)  # Google CSE limit per request

        try:
            response = self.service.cse().list(
                q=query,
                cx=self.cse_id,
                num=num_results,
                **kwargs
            ).execute()

            if 'items' in response:
                for item in response['items']:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', ''),
                        source='google'
                    ))

        except Exception as e:
            print(f"Google Search error: {e}")

        return results


class BraveSearchTool:
    """Tool for Brave Search API."""

    def __init__(self, api_key: str):
        """Initialize Brave Search tool.

        Args:
            api_key: Brave Search API key
        """
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def search(
        self,
        query: str,
        num_results: int = 10,
        country: str = "US",
        search_lang: str = "en",
        **kwargs
    ) -> List[SearchResult]:
        """Search using Brave Search API.

        Args:
            query: Search query
            num_results: Number of results to return
            country: Country code for search
            search_lang: Search language
            **kwargs: Additional parameters

        Returns:
            List of SearchResult objects
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        params = {
            "q": query,
            "count": num_results,
            "country": country,
            "search_lang": search_lang,
            **kwargs
        }

        results = []

        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if 'web' in data and 'results' in data['web']:
                for item in data['web']['results']:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('description', ''),
                        source='brave'
                    ))

        except Exception as e:
            print(f"Brave Search error: {e}")

        return results


class UnifiedSearchTool:
    """Unified search tool that can use multiple search engines."""

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        brave_api_key: Optional[str] = None,
    ):
        """Initialize unified search tool.

        Args:
            google_api_key: Google API key
            google_cse_id: Google Custom Search Engine ID
            brave_api_key: Brave Search API key
        """
        self.google = None
        self.brave = None

        if google_api_key and google_cse_id:
            self.google = GoogleSearchTool(google_api_key, google_cse_id)

        if brave_api_key:
            self.brave = BraveSearchTool(brave_api_key)

    def search(
        self,
        query: str,
        num_results: int = 10,
        engine: str = "auto",
    ) -> List[SearchResult]:
        """Search using available search engines.

        Args:
            query: Search query
            num_results: Number of results to return
            engine: Which engine to use ('google', 'brave', 'auto')

        Returns:
            List of SearchResult objects
        """
        if engine == "google" and self.google:
            return self.google.search(query, num_results)
        elif engine == "brave" and self.brave:
            return self.brave.search(query, num_results)
        elif engine == "auto":
            # Try Brave first (cheaper), fall back to Google
            if self.brave:
                results = self.brave.search(query, num_results)
                if results:
                    return results
            if self.google:
                return self.google.search(query, num_results)

        return []

    def multi_engine_search(
        self,
        query: str,
        num_results_per_engine: int = 5,
    ) -> List[SearchResult]:
        """Search using all available engines and combine results.

        Args:
            query: Search query
            num_results_per_engine: Results per engine

        Returns:
            Combined list of SearchResult objects
        """
        all_results = []

        if self.google:
            all_results.extend(self.google.search(query, num_results_per_engine))

        if self.brave:
            all_results.extend(self.brave.search(query, num_results_per_engine))

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results
