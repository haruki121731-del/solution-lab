from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


@dataclass(frozen=True)
class APIKeyAuth:
    """Simple API key authentication."""

    valid_keys: frozenset[str]
    header_name: str = 'X-API-Key'

    def __post_init__(self) -> None:
        object.__setattr__(
            self, '_security', APIKeyHeader(name=self.header_name, auto_error=False)
        )

    @property
    def security(self) -> APIKeyHeader:
        return object.__getattribute__(self, '_security')

    async def __call__(self, api_key: str | None = Security(lambda: None)) -> str:
        """Validate API key."""
        if not self.valid_keys:
            # No auth required if no keys configured (development mode)
            return 'anonymous'

        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='API key required',
                headers={'WWW-Authenticate': f'Header {self.header_name}'},
            )

        if api_key not in self.valid_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Invalid API key',
            )

        return api_key


def get_api_key_auth() -> APIKeyAuth:
    """Factory to create auth from environment."""
    # Read API keys from environment variable (comma-separated)
    keys_str = os.environ.get('API_KEYS', '')
    valid_keys = frozenset(k.strip() for k in keys_str.split(',') if k.strip())

    # In production, require at least one key
    # In development, empty set means no auth required
    return APIKeyAuth(valid_keys=valid_keys)


def generate_api_key() -> str:
    """Generate a new random API key."""
    return f'skl_{secrets.token_urlsafe(32)}'
