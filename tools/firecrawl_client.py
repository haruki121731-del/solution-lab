"""
Firecrawl Client - Thin adapter for web research.

This is a stub implementation for the MVP.
TODO: Replace with actual Firecrawl API integration.
"""

from typing import Any

from config import settings


class FirecrawlSearchResult:
    """Represents a single search result."""

    def __init__(
        self,
        url: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None
    ):
        self.url = url
        self.title = title
        self.content = content
        self.metadata = metadata or {}


class FirecrawlClient:
    """
    Thin adapter for Firecrawl API.

    Responsibilities:
    - Abstract Firecrawl-specific details
    - Provide structured search results
    - Handle rate limiting and errors
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        """
        Initialize the client.

        Args:
            api_key: Firecrawl API key (defaults to settings)
            base_url: Firecrawl base URL (defaults to settings)
        """
        self.api_key = api_key or settings.firecrawl_api_key
        self.base_url = base_url or settings.firecrawl_base_url
        self._client: Any | None = None

    async def search(self, query: str, limit: int = 5) -> list[FirecrawlSearchResult]:
        """
        Search the web using Firecrawl.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of search results

        Raises:
            NotImplementedError: In MVP - real implementation pending
        """
        # TODO: Implement actual Firecrawl integration
        # Example integration:
        # if not self._client:
        #     from firecrawl import FirecrawlApp
        #     self._client = FirecrawlApp(api_key=self.api_key)
        #
        # results = self._client.search(query, limit=limit)
        # return [self._convert_result(r) for r in results]

        raise NotImplementedError(
            "Firecrawl integration not yet implemented. "
            "Use placeholder findings from Researcher agent."
        )

    async def scrape(self, url: str) -> FirecrawlSearchResult:
        """
        Scrape a specific URL.

        Args:
            url: URL to scrape

        Returns:
            Scraped content as search result

        Raises:
            NotImplementedError: In MVP - real implementation pending
        """
        # TODO: Implement actual Firecrawl integration
        raise NotImplementedError(
            "Firecrawl integration not yet implemented."
        )

    def _convert_result(self, raw_result: dict[str, Any]) -> FirecrawlSearchResult:
        """Convert raw API response to structured result."""
        return FirecrawlSearchResult(
            url=raw_result.get("url", ""),
            title=raw_result.get("title", ""),
            content=raw_result.get("content", ""),
            metadata=raw_result.get("metadata", {})
        )

    @property
    def is_configured(self) -> bool:
        """Check if client has necessary configuration."""
        return bool(self.api_key)
