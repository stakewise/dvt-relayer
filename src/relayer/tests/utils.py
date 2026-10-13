from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from eth_account import Account
from eth_typing import HexStr

from src.app_state import AppState
from src.relayer.public_keys import PublicKeysManager
from src.relayer.tests.factories import create_protocol_config
from src.relayer.typings import Validator


@contextmanager
def patch_vault_contract(validators_manager_nonce: int) -> Iterator[None]:
    with patch('src.relayer.endpoints.VaultContract') as mock_vault_class:
        mock_vault_instance = MagicMock()
        mock_vault_instance.validators_manager_nonce = AsyncMock(
            return_value=validators_manager_nonce
        )
        mock_vault_class.return_value = mock_vault_instance
        yield


def setup_app_state(
    unregistered_keys: list[HexStr] | None = None,
    validators: dict[HexStr, Validator] | None = None,
) -> AppState:
    """Helper to set up AppState and public_keys_manager state."""
    app_state = AppState()

    public_keys_manager = PublicKeysManager()
    if unregistered_keys is not None:
        public_keys_manager.public_keys = list(unregistered_keys)
        # registered_public_keys stays empty, so get_unregistered returns all
    app_state.public_keys_manager = public_keys_manager

    # Set up validators manager account
    test_account = Account.create()
    app_state.validators_manager_account = test_account

    # Set up protocol config with valid oracle keys
    app_state.protocol_config = create_protocol_config()

    # Set up validators dict
    app_state.validators = validators or {}

    return app_state
