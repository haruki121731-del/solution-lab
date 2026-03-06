from __future__ import annotations

import os
from typing import Any

import httpx

from schemas.models import Evidence, EvidenceType
from tools.research import ResearchClient


class FirecrawlClient(ResearchClient):
    """Real Firecrawl API client for web research."""

    def __init__(self, api_key: str | None = None, base_url: str = 'https://api.firecrawl.dev') -> None:
        self.api_key = api_key or os.environ.get('FIRECRAWL_API_KEY')
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(self, query: str, *, problem_context: str) -> list[Evidence]:
        """Search using Firecrawl API."""
        if not self.api_key:
            raise RuntimeError('Firecrawl API key not configured')

        try:
            response = await self.client.post(
                f'{self.base_url}/v1/search',
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={'query': query, 'limit': 5},
            )
            response.raise_for_status()
            data = response.json()

            evidence_list: list[Evidence] = []
            for item in data.get('data', []):
                evidence_list.append(
                    Evidence(
                        title=item.get('title', 'Untitled'),
                        summary=item.get('description', item.get('content', ''))[:200],
                        source=item.get('url', 'firecrawl'),
                        evidence_type=EvidenceType.external,
                        confidence=0.75,
                        url=item.get('url'),
                    )
                )

            # Always include problem context as evidence
            evidence_list.insert(
                0,
                Evidence(
                    title='Problem context',
                    summary=problem_context,
                    source='session-input',
                    evidence_type=EvidenceType.user_input,
                    confidence=0.95,
                ),
            )

            return evidence_list

        except httpx.HTTPError as e:
            raise RuntimeError(f'Firecrawl API error: {e}') from e

    async def close(self) -> None:
        await self.client.aclose()


class HybridResearchClient(ResearchClient):
    """Uses Firecrawl if available, falls back to heuristics."""

    def __init__(self, api_key: str | None = None) -> None:
        self.firecrawl = FirecrawlClient(api_key) if (api_key or os.environ.get('FIRECRAWL_API_KEY')) else None
        from tools.research import HeuristicResearchClient

        self.heuristic = HeuristicResearchClient()

    async def search(self, query: str, *, problem_context: str) -> list[Evidence]:
        if self.firecrawl:
            try:
                return await self.firecrawl.search(query, problem_context=problem_context)
            except Exception:
                pass  # Fall through to heuristic
        return await self.heuristic.search(query, problem_context=problem_context)
