from unittest.mock import patch

from eth_account import Account

from src.app_state import AppState
from src.common.endpoints import get_info


class TestInfoEndpoint:
    async def test_get_info(self) -> None:
        app_state = AppState()
        app_state.validators_manager_account = Account.create()

        with patch('src.common.endpoints.settings') as mock_settings:
            mock_settings.network = 'hoodi'
            response = await get_info()

        assert response.network == 'hoodi'
        assert response.validators_manager_address == app_state.validators_manager_account.address
