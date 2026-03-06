import os

import pytest
from fastapi import HTTPException

from auth.api_key import APIKeyAuth, generate_api_key, get_api_key_auth


def test_generate_api_key() -> None:
    key = generate_api_key()
    assert key.startswith('skl_')
    assert len(key) > 10


def test_auth_no_keys_allows_anonymous() -> None:
    auth = APIKeyAuth(valid_keys=frozenset())
    # Valid keys should be empty frozenset
    assert auth.valid_keys == frozenset()


@pytest.mark.asyncio
async def test_auth_rejects_invalid_key() -> None:
    auth = APIKeyAuth(valid_keys=frozenset({'valid-key-123'}))

    with pytest.raises(HTTPException) as exc_info:
        await auth('invalid-key')

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_auth_accepts_valid_key() -> None:
    auth = APIKeyAuth(valid_keys=frozenset({'valid-key-123'}))

    result = await auth('valid-key-123')
    assert result == 'valid-key-123'


def test_auth_with_api_keys_env() -> None:
    # Save original
    original = os.environ.get('API_KEYS')

    try:
        os.environ['API_KEYS'] = 'key1,key2,key3'
        auth = get_api_key_auth()
        assert auth.valid_keys == frozenset({'key1', 'key2', 'key3'})
    finally:
        # Restore
        if original is None:
            del os.environ['API_KEYS']
        else:
            os.environ['API_KEYS'] = original


@pytest.mark.asyncio
async def test_auth_no_key_provided() -> None:
    auth = APIKeyAuth(valid_keys=frozenset({'valid-key'}))

    with pytest.raises(HTTPException) as exc_info:
        await auth(None)

    assert exc_info.value.status_code == 401
