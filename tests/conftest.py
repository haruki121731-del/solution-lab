"""
Pytest configuration and fixtures.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings between tests if needed."""
    # Settings are cached, but tests should be independent
    yield


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
