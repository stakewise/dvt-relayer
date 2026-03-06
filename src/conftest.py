from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.app_state import AppState
from src.common.typings import Singleton


@pytest.fixture(autouse=True)
def _clean_singleton() -> None:  # type: ignore[misc]
    """Clean AppState singleton between tests."""
    Singleton._instances.pop(AppState, None)
    yield
    Singleton._instances.pop(AppState, None)


@pytest.fixture()
async def test_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client
