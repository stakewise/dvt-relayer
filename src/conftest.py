import os
from collections.abc import AsyncIterator

import pytest
from eth_typing import ChecksumAddress, HexStr
from httpx import ASGITransport, AsyncClient
from sw_utils.tests import faker

from src.app import app
from src.app_state import AppState
from src.common.tests.utils import create_jwt_token
from src.common.typings import Singleton


@pytest.fixture(autouse=True)
def _clean_singleton() -> None:  # type: ignore[misc]
    """Clean AppState singleton between tests."""
    Singleton._instances.pop(AppState, None)
    yield
    Singleton._instances.pop(AppState, None)


@pytest.fixture()
def jwt_secret() -> bytes:
    """Random JWT secret set in AppState."""
    secret = os.urandom(32)
    AppState().jwt_secret = secret
    return secret


@pytest.fixture()
async def test_client(jwt_secret: bytes) -> AsyncIterator[AsyncClient]:
    """Client authenticated with JWT token."""
    headers = {'Authorization': f'Bearer {create_jwt_token(jwt_secret)}'}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test', headers=headers) as client:
        yield client


@pytest.fixture()
async def anonymous_client(jwt_secret: bytes) -> AsyncIterator[AsyncClient]:
    """Client without JWT token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client


@pytest.fixture()
def vault_address() -> ChecksumAddress:
    return faker.eth_address()


@pytest.fixture()
def pubkey_1() -> HexStr:
    return faker.validator_public_key()


@pytest.fixture()
def pubkey_2() -> HexStr:
    return faker.validator_public_key()
