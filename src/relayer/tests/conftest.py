import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture()
async def test_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client


@pytest.fixture()
def sidecar_shares_1val() -> list[dict]:
    return json.loads((FIXTURES_DIR / 'sidecar_shares_1_validator.json').read_text())
