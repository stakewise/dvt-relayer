from unittest.mock import patch

from eth_account import Account
from httpx import AsyncClient

from src.app_state import AppState


class TestInfoEndpoint:
    async def test_get_info(self, test_client: AsyncClient) -> None:
        app_state = AppState()
        app_state.validators_manager_account = Account.create()

        with patch('src.common.endpoints.settings') as mock_settings:
            mock_settings.network = 'hoodi'
            resp = await test_client.get('/info')

        assert resp.status_code == 200
        data = resp.json()
        assert data['network'] == 'hoodi'
        assert data['validators_manager_address'] == app_state.validators_manager_account.address
