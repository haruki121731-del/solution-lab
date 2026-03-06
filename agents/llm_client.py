from __future__ import annotations

import os
from typing import Any, Protocol

import httpx


class LLMClient(Protocol):
    """Protocol for LLM completions."""

    async def complete(self, prompt: str, *, temperature: float = 0.3, max_tokens: int = 1000) -> str: ...


class OpenAIClient:
    """OpenAI API client."""

    def __init__(self, api_key: str | None = None, model: str = 'gpt-4o-mini') -> None:
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def complete(self, prompt: str, *, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        if not self.api_key:
            raise RuntimeError('OpenAI API key not configured')

        response = await self.client.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': self.model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': temperature,
                'max_tokens': max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']

    async def close(self) -> None:
        await self.client.aclose()


class AnthropicClient:
    """Anthropic Claude API client."""

    def __init__(self, api_key: str | None = None, model: str = 'claude-3-haiku-20240307') -> None:
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def complete(self, prompt: str, *, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        if not self.api_key:
            raise RuntimeError('Anthropic API key not configured')

        response = await self.client.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01',
            },
            json={
                'model': self.model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': max_tokens,
                'temperature': temperature,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data['content'][0]['text']

    async def close(self) -> None:
        await self.client.aclose()
