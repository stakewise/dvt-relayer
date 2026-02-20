import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from eth_typing import BlockNumber
from sw_utils.tests import faker

from src.app_state import AppState
from src.common.typings import Singleton
from src.relayer.public_keys import PublicKeysManager

PUBKEY_1 = faker.validator_public_key()
PUBKEY_2 = faker.validator_public_key()
PUBKEY_3 = faker.validator_public_key()


@pytest.fixture(autouse=True)
def _clean_app_state() -> None:  # type: ignore[misc]
    """Clean AppState singleton between tests."""
    Singleton._instances.pop(AppState, None)
    yield  # type: ignore[misc]
    Singleton._instances.pop(AppState, None)


class TestPublicKeysManagerLoad:
    def test_load_valid_csv(self) -> None:
        """Test loading public keys from a valid CSV file."""
        manager = PublicKeysManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write(f'{PUBKEY_1}\n')
            f.write(f'{PUBKEY_2}\n')
            csv_path = f.name

        try:
            with patch('src.relayer.public_keys.settings') as mock_settings:
                mock_settings.public_keys_file = csv_path
                manager.load_from_file()

            assert manager.public_keys == [PUBKEY_1, PUBKEY_2]
        finally:
            os.unlink(csv_path)

    def test_load_missing_file_raises(self) -> None:
        """Test that loading from a missing file raises ValueError."""
        manager = PublicKeysManager()

        with patch('src.relayer.public_keys.settings') as mock_settings:
            mock_settings.public_keys_file = '/nonexistent/path/keys.csv'
            with pytest.raises(ValueError, match="Can't open public keys file"):
                manager.load_from_file()

    def test_load_empty_file_raises(self) -> None:
        """Test that loading from a file with no valid keys raises ValueError."""
        manager = PublicKeysManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write('\n\n')
            csv_path = f.name

        try:
            with patch('src.relayer.public_keys.settings') as mock_settings:
                mock_settings.public_keys_file = csv_path
                with pytest.raises(ValueError, match='No public keys found'):
                    manager.load_from_file()
        finally:
            os.unlink(csv_path)

    def test_load_skips_empty_rows(self) -> None:
        """Test that empty rows in the CSV are skipped."""
        manager = PublicKeysManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write(f'{PUBKEY_1}\n')
            f.write('\n')
            f.write(f'{PUBKEY_2}\n')
            csv_path = f.name

        try:
            with patch('src.relayer.public_keys.settings') as mock_settings:
                mock_settings.public_keys_file = csv_path
                manager.load_from_file()

            assert manager.public_keys == [PUBKEY_1, PUBKEY_2]
        finally:
            os.unlink(csv_path)

    def test_load_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from public keys."""
        manager = PublicKeysManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write(f'  {PUBKEY_1}  \n')
            csv_path = f.name

        try:
            with patch('src.relayer.public_keys.settings') as mock_settings:
                mock_settings.public_keys_file = csv_path
                manager.load_from_file()

            assert manager.public_keys == [PUBKEY_1]
        finally:
            os.unlink(csv_path)


class TestPublicKeysManagerFetchRegistered:
    async def test_fetch_registered_empty_public_keys(self) -> None:
        """Test that fetch_registered is a no-op when no public keys are loaded."""
        manager = PublicKeysManager()
        assert manager.public_keys == []

        # Should return early without making any calls
        with patch('src.relayer.public_keys.consensus_client') as mock_client:
            await manager.fetch_registered()
            mock_client.get_validators_by_ids.assert_not_called()

        assert manager.registered_public_keys == set()

    async def test_fetch_registered_with_results(self) -> None:
        """Test fetching registered validators from the consensus client."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1, PUBKEY_2, PUBKEY_3]

        # PUBKEY_1 and PUBKEY_3 are registered on the consensus layer
        mock_response = {
            'data': [
                {'validator': {'pubkey': PUBKEY_1.replace('0x', '')}},
                {'validator': {'pubkey': PUBKEY_3.replace('0x', '')}},
            ]
        }

        with patch('src.relayer.public_keys.consensus_client') as mock_client:
            mock_client.get_validators_by_ids = AsyncMock(return_value=mock_response)
            await manager.fetch_registered()

        assert manager.registered_public_keys == {PUBKEY_1, PUBKEY_3}

    async def test_fetch_registered_no_validators_found(self) -> None:
        """Test fetch_registered when no validators are found on the consensus layer."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1, PUBKEY_2]

        mock_response: dict = {'data': []}

        with patch('src.relayer.public_keys.consensus_client') as mock_client:
            mock_client.get_validators_by_ids = AsyncMock(return_value=mock_response)
            await manager.fetch_registered()

        assert manager.registered_public_keys == set()

    async def test_fetch_registered_calls_with_correct_params(self) -> None:
        """Test that fetch_registered calls consensus_client with correct parameters."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1, PUBKEY_2]

        mock_response: dict = {'data': []}

        with patch('src.relayer.public_keys.consensus_client') as mock_client:
            mock_client.get_validators_by_ids = AsyncMock(return_value=mock_response)
            await manager.fetch_registered()
            mock_client.get_validators_by_ids.assert_called_once_with(
                validator_ids=[PUBKEY_1, PUBKEY_2],
                state_id='head',
            )


class TestPublicKeysManagerGetUnregistered:
    async def test_get_unregistered_all_unregistered(self) -> None:
        """Test get_unregistered when no keys are registered."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1, PUBKEY_2, PUBKEY_3]
        manager.registered_public_keys = set()

        AppState().network_validators_block = BlockNumber(100)
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            result = await manager.get_unregistered()

        assert result == [PUBKEY_1, PUBKEY_2, PUBKEY_3]

    async def test_get_unregistered_some_registered(self) -> None:
        """Test get_unregistered when some keys are registered."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1, PUBKEY_2, PUBKEY_3]
        manager.registered_public_keys = {PUBKEY_1, PUBKEY_3}

        AppState().network_validators_block = BlockNumber(100)
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            result = await manager.get_unregistered()

        assert result == [PUBKEY_2]

    async def test_get_unregistered_all_registered(self) -> None:
        """Test get_unregistered when all keys are registered."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1, PUBKEY_2]
        manager.registered_public_keys = {PUBKEY_1, PUBKEY_2}

        AppState().network_validators_block = BlockNumber(100)
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            result = await manager.get_unregistered()

        assert result == []

    async def test_get_unregistered_empty_public_keys(self) -> None:
        """Test get_unregistered when no public keys are loaded."""
        manager = PublicKeysManager()
        result = await manager.get_unregistered()
        assert result == []

    async def test_get_unregistered_preserves_order(self) -> None:
        """Test that get_unregistered preserves the order of public keys."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_3, PUBKEY_1, PUBKEY_2]
        manager.registered_public_keys = {PUBKEY_1}

        AppState().network_validators_block = BlockNumber(100)
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            result = await manager.get_unregistered()

        assert result == [PUBKEY_3, PUBKEY_2]

    async def test_get_unregistered_excludes_pending_deposits(self) -> None:
        """Test that get_unregistered excludes keys with pending deposits."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1, PUBKEY_2, PUBKEY_3]
        manager.registered_public_keys = set()

        # PUBKEY_2 has a pending deposit event
        pending_event = {'args': {'pubkey': bytes.fromhex(PUBKEY_2[2:])}}

        AppState().network_validators_block = BlockNumber(100)
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[pending_event])
            result = await manager.get_unregistered()

        assert result == [PUBKEY_1, PUBKEY_3]

    async def test_get_unregistered_no_fetch_when_finalized_equals_head(self) -> None:
        """Test that deposit events are not fetched when head == network_validators_block."""
        manager = PublicKeysManager()
        manager.public_keys = [PUBKEY_1]
        manager.registered_public_keys = set()

        AppState().network_validators_block = BlockNumber(100)
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=100)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            result = await manager.get_unregistered()

        mock_registry.events.DepositEvent.get_logs.assert_not_called()
        assert result == [PUBKEY_1]
