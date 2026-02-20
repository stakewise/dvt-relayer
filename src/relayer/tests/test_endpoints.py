from time import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from eth_account import Account
from eth_typing import BLSSignature, HexStr
from sw_utils.tests import faker
from web3 import Web3
from web3.types import Gwei

from src.app_state import AppState
from src.common.typings import Singleton
from src.relayer.endpoints import (
    consolidate_validators,
    fund_validators,
    register_validators,
    withdraw_validators,
)
from src.relayer.public_keys import public_keys_manager
from src.relayer.schema import (
    ValidatorsConsolidationRequest,
    ValidatorsFundRequest,
    ValidatorsRegisterRequest,
    ValidatorsWithdrawalRequest,
)
from src.relayer.typings import Validator, ValidatorType

PUBKEY_1 = faker.validator_public_key()
PUBKEY_2 = faker.validator_public_key()
PUBKEY_3 = faker.validator_public_key()

VAULT_ADDRESS = Web3.to_checksum_address('0x1234567890abcdef1234567890abcdef12345678')

# A dummy 96-byte BLS signature
DUMMY_SIGNATURE = BLSSignature(b'\x01' * 96)


@pytest.fixture(autouse=True)
def _clean_singleton() -> None:  # type: ignore[misc]
    """Clean AppState singleton and public_keys_manager state between tests."""
    Singleton._instances.pop(AppState, None)
    public_keys_manager.public_keys = []
    public_keys_manager.registered_public_keys = set()
    yield  # type: ignore[misc]
    Singleton._instances.pop(AppState, None)
    public_keys_manager.public_keys = []
    public_keys_manager.registered_public_keys = set()


def _setup_app_state(
    unregistered_keys: list[HexStr] | None = None,
    validators: dict[HexStr, Validator] | None = None,
) -> AppState:
    """Helper to set up AppState and public_keys_manager state."""
    app_state = AppState()

    if unregistered_keys is not None:
        public_keys_manager.public_keys = list(unregistered_keys)
        # registered_public_keys stays empty, so get_unregistered returns all

    # Set up validators manager account
    test_account = Account.create()
    app_state.validators_manager_account = test_account

    # Set up validators dict
    app_state.validators = validators or {}

    return app_state


class TestRegisterEndpoint:
    @pytest.fixture(autouse=True)
    def _mock_pending_deposits(self) -> None:  # type: ignore[misc]
        """Patch get_unregistered dependencies so no pending deposits are found."""
        AppState().network_validators_block = 100
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            yield  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_register_creates_new_validators(self) -> None:
        """Test that /register creates validators for unregistered public keys."""
        _setup_app_state(unregistered_keys=[PUBKEY_1, PUBKEY_2])

        request = ValidatorsRegisterRequest(
            vault=VAULT_ADDRESS,
            validators_start_index=100,
            amounts=[Gwei(32000000000), Gwei(32000000000)],
            validator_type=ValidatorType.V1,
        )

        response = await register_validators(request)

        assert len(response.validators) == 2
        assert response.validators[0].public_key == PUBKEY_1
        assert response.validators[1].public_key == PUBKEY_2
        assert response.validators[0].amount == Gwei(32000000000)
        assert response.validators_manager_signature is None  # no signatures ready

    @pytest.mark.asyncio
    async def test_register_returns_existing_validators(self) -> None:
        """Test that /register returns existing validators if they match."""
        existing_validator = Validator(
            public_key=PUBKEY_1,
            vault=VAULT_ADDRESS,
            validator_index=100,
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
        )
        _setup_app_state(
            unregistered_keys=[PUBKEY_1],
            validators={PUBKEY_1: existing_validator},
        )

        request = ValidatorsRegisterRequest(
            vault=VAULT_ADDRESS,
            validators_start_index=100,
            amounts=[Gwei(32000000000)],
            validator_type=ValidatorType.V1,
        )

        response = await register_validators(request)

        assert len(response.validators) == 1
        assert response.validators[0].public_key == PUBKEY_1

    @pytest.mark.asyncio
    async def test_register_with_signatures_ready(self) -> None:
        """Test that /register returns validators_manager_signature when all sigs ready."""
        validator = Validator(
            public_key=PUBKEY_1,
            vault=VAULT_ADDRESS,
            validator_index=100,
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
            deposit_signature=DUMMY_SIGNATURE,
            exit_signature=DUMMY_SIGNATURE,
        )
        _setup_app_state(
            unregistered_keys=[PUBKEY_1],
            validators={PUBKEY_1: validator},
        )

        request = ValidatorsRegisterRequest(
            vault=VAULT_ADDRESS,
            validators_start_index=100,
            amounts=[Gwei(32000000000)],
            validator_type=ValidatorType.V1,
        )

        # Mock the validators_registry_contract.get_registry_root() call
        mock_root = b'\x00' * 32
        with patch('src.relayer.endpoints.validators_registry_contract') as mock_contract:
            mock_contract.get_registry_root = AsyncMock(return_value=mock_root)
            response = await register_validators(request)

        assert response.validators_manager_signature is not None
        assert len(response.validators) == 1

    @pytest.mark.asyncio
    async def test_register_replaces_validator_on_index_mismatch(self) -> None:
        """Test that a new validator is created if the index doesn't match."""
        existing_validator = Validator(
            public_key=PUBKEY_1,
            vault=VAULT_ADDRESS,
            validator_index=50,  # different index
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
        )
        _setup_app_state(
            unregistered_keys=[PUBKEY_1],
            validators={PUBKEY_1: existing_validator},
        )

        request = ValidatorsRegisterRequest(
            vault=VAULT_ADDRESS,
            validators_start_index=100,  # new index
            amounts=[Gwei(32000000000)],
            validator_type=ValidatorType.V1,
        )

        response = await register_validators(request)

        assert len(response.validators) == 1
        # Validator should have been replaced
        app_state = AppState()
        assert app_state.validators[PUBKEY_1].validator_index == 100


class TestFundEndpoint:
    @pytest.mark.asyncio
    async def test_fund_validators(self) -> None:
        """Test that /fund returns a validators_manager_signature."""
        _setup_app_state()

        request = ValidatorsFundRequest(
            vault=VAULT_ADDRESS,
            public_keys=[PUBKEY_1, PUBKEY_2],
            amounts=[Gwei(32000000000), Gwei(32000000000)],
        )

        with patch('src.relayer.endpoints.VaultContract') as mock_vault_class:
            mock_vault_instance = MagicMock()
            mock_vault_instance.validators_manager_nonce = AsyncMock(return_value=1)
            mock_vault_class.return_value = mock_vault_instance

            response = await fund_validators(request)

        assert response.validators_manager_signature is not None


class TestWithdrawEndpoint:
    @pytest.mark.asyncio
    async def test_withdraw_validators(self) -> None:
        """Test that /withdraw returns a validators_manager_signature."""
        _setup_app_state()

        request = ValidatorsWithdrawalRequest(
            vault=VAULT_ADDRESS,
            public_keys=[PUBKEY_1],
            amounts=[Gwei(32000000000)],
        )

        with patch('src.relayer.endpoints.VaultContract') as mock_vault_class:
            mock_vault_instance = MagicMock()
            mock_vault_instance.validators_manager_nonce = AsyncMock(return_value=1)
            mock_vault_class.return_value = mock_vault_instance

            response = await withdraw_validators(request)

        assert response.validators_manager_signature is not None


class TestConsolidateEndpoint:
    @pytest.mark.asyncio
    async def test_consolidate_validators(self) -> None:
        """Test that /consolidate returns a validators_manager_signature."""
        _setup_app_state()

        request = ValidatorsConsolidationRequest(
            vault=VAULT_ADDRESS,
            source_public_keys=[PUBKEY_1],
            target_public_keys=[PUBKEY_2],
        )

        with patch('src.relayer.endpoints.VaultContract') as mock_vault_class:
            mock_vault_instance = MagicMock()
            mock_vault_instance.validators_manager_nonce = AsyncMock(return_value=1)
            mock_vault_class.return_value = mock_vault_instance

            response = await consolidate_validators(request)

        assert response.validators_manager_signature is not None
