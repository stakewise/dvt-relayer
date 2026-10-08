import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.app_state import AppState
from src.common.tests.utils import create_jwt_token
from src.common.typings import Singleton

TEST_JWT_SECRET = os.urandom(32)


@pytest.fixture(autouse=True)
def _clean_singleton() -> None:  # type: ignore[misc]
    """Clean AppState singleton between tests."""
    Singleton._instances.pop(AppState, None)
    AppState().jwt_secret = TEST_JWT_SECRET
    yield
    Singleton._instances.pop(AppState, None)


@pytest.fixture()
async def test_client() -> AsyncIterator[AsyncClient]:
    """Client authenticated with JWT token."""
    headers = {'Authorization': f'Bearer {create_jwt_token(TEST_JWT_SECRET)}'}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test', headers=headers) as client:
        yield client


@pytest.fixture()
async def anonymous_client() -> AsyncIterator[AsyncClient]:
    """Client without JWT token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client
