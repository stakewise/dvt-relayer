from contextlib import contextmanager
from time import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from eth_account import Account
from eth_typing import BLSSignature, HexStr
from httpx import AsyncClient
from sw_utils.tests import faker
from web3 import Web3
from web3.types import Gwei

from src.app_state import AppState
from src.config.networks import NETWORKS
from src.relayer.public_keys import PublicKeysManager
from src.relayer.tests.factories import create_protocol_config
from src.relayer.typings import Validator, ValidatorType

PUBKEY_1 = faker.validator_public_key()
PUBKEY_2 = faker.validator_public_key()
PUBKEY_3 = faker.validator_public_key()

VAULT_ADDRESS = '0x1234567890abcdef1234567890abcdef12345678'


@contextmanager
def patch_vault_contract(validators_manager_nonce: int):
    with patch('src.relayer.endpoints.VaultContract') as mock_vault_class:
        mock_vault_instance = MagicMock()
        mock_vault_instance.validators_manager_nonce = AsyncMock(
            return_value=validators_manager_nonce
        )
        mock_vault_class.return_value = mock_vault_instance
        yield


# A dummy 96-byte BLS signature
DUMMY_SIGNATURE = BLSSignature(b'\x01' * 96)


def _setup_app_state(
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


class TestRegisterEndpoint:
    @pytest.fixture(autouse=True)
    def _mock_pending_deposits(self) -> None:  # type: ignore[misc]
        """Patch get_unregistered dependencies so no pending deposits are found."""
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            yield  # type: ignore[misc]

    async def test_register_creates_new_validators(self, test_client: AsyncClient) -> None:
        """Test that /register creates validators for unregistered public keys."""
        _setup_app_state(unregistered_keys=[PUBKEY_1, PUBKEY_2])

        resp = await test_client.post(
            '/register',
            json={
                'vault': VAULT_ADDRESS,
                'validators_start_index': 100,
                'amounts': [32000000000, 32000000000],
                'validator_type': '0x01',
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 2
        assert data['validators'][0]['public_key'] == PUBKEY_1
        assert data['validators'][1]['public_key'] == PUBKEY_2
        assert data['validators'][0]['amount'] == 32000000000
        assert data['validators_manager_signature'] is None

    async def test_register_returns_existing_validators(self, test_client: AsyncClient) -> None:
        """Test that /register returns existing validators if they match."""
        existing_validator = Validator(
            public_key=PUBKEY_1,
            vault=Web3.to_checksum_address(VAULT_ADDRESS),
            validator_index=100,
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
        )
        _setup_app_state(
            unregistered_keys=[PUBKEY_1],
            validators={PUBKEY_1: existing_validator},
        )

        resp = await test_client.post(
            '/register',
            json={
                'vault': VAULT_ADDRESS,
                'validators_start_index': 100,
                'amounts': [32000000000],
                'validator_type': '0x01',
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 1
        assert data['validators'][0]['public_key'] == PUBKEY_1

    async def test_register_with_signatures_ready(self, test_client: AsyncClient) -> None:
        """Test that /register returns validators_manager_signature when all sigs ready."""
        validator = Validator(
            public_key=PUBKEY_1,
            vault=Web3.to_checksum_address(VAULT_ADDRESS),
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

        mock_root = b'\x00' * 32
        with patch('src.relayer.endpoints.validators_registry_contract') as mock_contract:
            mock_contract.get_registry_root = AsyncMock(return_value=mock_root)
            resp = await test_client.post(
                '/register',
                json={
                    'vault': VAULT_ADDRESS,
                    'validators_start_index': 100,
                    'amounts': [32000000000],
                    'validator_type': '0x01',
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data['validators_manager_signature'] is not None
        assert len(data['validators']) == 1

    async def test_register_replaces_validator_on_index_mismatch(
        self, test_client: AsyncClient
    ) -> None:
        """Test that a new validator is created if the index doesn't match."""
        existing_validator = Validator(
            public_key=PUBKEY_1,
            vault=Web3.to_checksum_address(VAULT_ADDRESS),
            validator_index=50,  # different index
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
        )
        _setup_app_state(
            unregistered_keys=[PUBKEY_1],
            validators={PUBKEY_1: existing_validator},
        )

        resp = await test_client.post(
            '/register',
            json={
                'vault': VAULT_ADDRESS,
                'validators_start_index': 100,
                'amounts': [32000000000],
                'validator_type': '0x01',
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 1
        app_state = AppState()
        assert app_state.validators[PUBKEY_1].validator_index == 100


class TestRegisterEmptyAmounts:
    async def test_register_empty_amounts_rejected(self, test_client: AsyncClient) -> None:
        """Test that /register rejects empty amounts list."""
        resp = await test_client.post(
            '/register',
            json={
                'vault': VAULT_ADDRESS,
                'validators_start_index': 100,
                'amounts': [],
                'validator_type': '0x01',
            },
        )
        assert resp.status_code == 422


class TestFundEndpoint:
    async def test_fund_empty_amounts_rejected(self, test_client: AsyncClient) -> None:
        """Test that /fund rejects empty amounts list."""
        resp = await test_client.post(
            '/fund',
            json={
                'vault': VAULT_ADDRESS,
                'public_keys': [PUBKEY_1],
                'amounts': [],
            },
        )
        assert resp.status_code == 422

    async def test_fund_validators(self, test_client: AsyncClient) -> None:
        """Test that /fund returns a validators_manager_signature."""
        _setup_app_state()

        with patch_vault_contract(validators_manager_nonce=1):
            resp = await test_client.post(
                '/fund',
                json={
                    'vault': VAULT_ADDRESS,
                    'public_keys': [PUBKEY_1, PUBKEY_2],
                    'amounts': [32000000000, 32000000000],
                },
            )

        assert resp.status_code == 200
        assert resp.json()['validators_manager_signature'] is not None


class TestWithdrawEndpoint:
    async def test_withdraw_empty_amounts_rejected(self, test_client: AsyncClient) -> None:
        """Test that /withdraw rejects empty amounts list."""
        resp = await test_client.post(
            '/withdraw',
            json={
                'vault': VAULT_ADDRESS,
                'public_keys': [PUBKEY_1],
                'amounts': [],
            },
        )
        assert resp.status_code == 422

    async def test_withdraw_validators(self, test_client: AsyncClient) -> None:
        """Test that /withdraw returns a validators_manager_signature."""
        _setup_app_state()

        with patch_vault_contract(validators_manager_nonce=1):
            resp = await test_client.post(
                '/withdraw',
                json={
                    'vault': VAULT_ADDRESS,
                    'public_keys': [PUBKEY_1],
                    'amounts': [32000000000],
                },
            )

        assert resp.status_code == 200
        assert resp.json()['validators_manager_signature'] is not None


class TestConsolidateEndpoint:
    async def test_consolidate_validators(self, test_client: AsyncClient) -> None:
        """Test that /consolidate returns a validators_manager_signature."""
        _setup_app_state()

        with patch_vault_contract(validators_manager_nonce=1):
            resp = await test_client.post(
                '/consolidate',
                json={
                    'vault': VAULT_ADDRESS,
                    'source_public_keys': [PUBKEY_1],
                    'target_public_keys': [PUBKEY_2],
                },
            )

        assert resp.status_code == 200
        assert resp.json()['validators_manager_signature'] is not None


DVT_VAULT = '0x8ae5c1046158526cf236f74d8fb88fabe2e94aca'


class TestRegisterSignatureAggregation:
    """Test full flow: /register → sidecar /signatures submissions → /register with all ready."""

    @pytest.fixture(autouse=True)
    def _mock_pending_deposits(self) -> None:  # type: ignore[misc]
        hoodi_config = NETWORKS['hoodi']
        with (
            patch('src.relayer.public_keys.execution_client') as mock_exec,
            patch('src.relayer.public_keys.validators_registry_contract') as mock_registry,
            patch('src.config.settings.network_config', hoodi_config),
        ):
            mock_exec.eth.get_block_number = AsyncMock(return_value=110)
            mock_registry.events.DepositEvent.get_logs = AsyncMock(return_value=[])
            yield  # type: ignore[misc]

    @pytest.mark.parametrize(
        'skip_share_index',
        [None, 263, 280, 281, 282],
    )
    async def test_register_with_signature_aggregation(
        self,
        skip_share_index: int,
        sidecar_shares_1val: list[dict],
        test_client: AsyncClient,
    ) -> None:
        """Submit sidecar shares, verify threshold aggregation works.

        When skip_share_index is None, all 4 shares are submitted (redundant shares case).
        Otherwise, 3 of 4 shares are submitted (skipping one).
        """
        public_key = HexStr(sidecar_shares_1val[0]['shares'][0]['public_key'])
        _setup_app_state(unregistered_keys=[public_key])

        register_request = {
            'vault': DVT_VAULT,
            'validators_start_index': 10,
            'amounts': [32000000000],
            'validator_type': '0x02',
        }

        # Step 1: initial /register creates the validator with no signatures
        resp = await test_client.post('/register', json=register_request)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 1
        assert data['validators'][0]['deposit_signature'] is None
        assert data['validators_manager_signature'] is None

        # Step 2: submit signature shares from 3 sidecars (skip one)
        shares_to_submit = [s for s in sidecar_shares_1val if s['share_index'] != skip_share_index]
        with patch('src.config.settings.signature_threshold', 3):
            for sidecar_data in shares_to_submit:
                resp = await test_client.post('/signatures', json=sidecar_data)
                assert resp.status_code == 200

        # Step 3: /register again — all signatures should be ready
        mock_root = b'\x00' * 32
        with patch('src.relayer.endpoints.validators_registry_contract') as mock_contract:
            mock_contract.get_registry_root = AsyncMock(return_value=mock_root)
            resp = await test_client.post('/register', json=register_request)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 1
        assert data['validators'][0]['deposit_signature'] is not None
        assert data['validators'][0]['oracles_exit_signature_shares'] is not None
        assert data['validators_manager_signature'] is not None

    @pytest.mark.parametrize(
        'skip_share_index',
        [None, 263, 280, 281, 282],
    )
    async def test_register_2_validators_with_signature_aggregation(
        self,
        skip_share_index: int,
        sidecar_shares_2val: list[dict],
        test_client: AsyncClient,
    ) -> None:
        """Submit sidecar shares for 2 validators, verify threshold aggregation.

        When skip_share_index is None, all 4 shares are submitted (redundant shares case).
        Otherwise, 3 of 4 shares are submitted (skipping one).
        """
        public_keys = [HexStr(s['public_key']) for s in sidecar_shares_2val[0]['shares']]
        _setup_app_state(unregistered_keys=public_keys)

        register_request = {
            'vault': DVT_VAULT,
            'validators_start_index': 10,
            'amounts': [32000000000, 34000000000],
            'validator_type': '0x02',
        }

        # Step 1: initial /register creates validators with no signatures
        resp = await test_client.post('/register', json=register_request)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 2
        assert data['validators'][0]['deposit_signature'] is None
        assert data['validators'][1]['deposit_signature'] is None
        assert data['validators_manager_signature'] is None

        # Step 2: submit signature shares from 3 sidecars (skip one)
        shares_to_submit = [s for s in sidecar_shares_2val if s['share_index'] != skip_share_index]
        with patch('src.config.settings.signature_threshold', 3):
            for sidecar_data in shares_to_submit:
                resp = await test_client.post('/signatures', json=sidecar_data)
                assert resp.status_code == 200

        # Step 3: /register again — all signatures should be ready for both validators
        mock_root = b'\x00' * 32
        with patch('src.relayer.endpoints.validators_registry_contract') as mock_contract:
            mock_contract.get_registry_root = AsyncMock(return_value=mock_root)
            resp = await test_client.post('/register', json=register_request)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 2
        for validator in data['validators']:
            assert validator['deposit_signature'] is not None
            assert validator['oracles_exit_signature_shares'] is not None
        assert data['validators_manager_signature'] is not None


class TestSubmitSignatureSharesValidation:
    """Validation of incoming signature shares on POST /signatures."""

    def _make_validator(self) -> Validator:
        return Validator(
            public_key=PUBKEY_1,
            vault=Web3.to_checksum_address(DVT_VAULT),
            validator_index=10,
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V2,
        )

    async def test_rejects_public_key_shares_that_do_not_reconstruct(
        self, test_client: AsyncClient
    ) -> None:
        """Public key shares that don't reconstruct to the validator pubkey are rejected."""
        validator = self._make_validator()
        _setup_app_state(validators={PUBKEY_1: validator})

        request = {
            'share_index': 1,
            'shares': [
                {
                    'public_key': PUBKEY_1,
                    # Random shares — won't reconstruct to PUBKEY_1
                    'public_key_shares': [
                        {'share_index': 1, 'public_key_share': faker.validator_public_key()},
                        {'share_index': 2, 'public_key_share': faker.validator_public_key()},
                        {'share_index': 3, 'public_key_share': faker.validator_public_key()},
                    ],
                    'exit_signature': faker.validator_signature(),
                    'deposit_signature': faker.validator_signature(),
                }
            ],
        }

        resp = await test_client.post('/signatures', json=request)

        # Validation happens in the SignatureShareRequest schema -> 422
        assert resp.status_code == 422
        assert 'invalid public key shares' in str(resp.json()['detail'])
        # Nothing stored
        assert validator.exit_signature_shares == {}
        assert validator.deposit_signature_shares == {}

    async def test_rejects_missing_public_key_shares_field(self, test_client: AsyncClient) -> None:
        """The public_key_shares field is required by the schema."""
        _setup_app_state(validators={PUBKEY_1: self._make_validator()})

        request = {
            'share_index': 1,
            'shares': [
                {
                    'public_key': PUBKEY_1,
                    'exit_signature': faker.validator_signature(),
                    'deposit_signature': faker.validator_signature(),
                }
            ],
        }

        resp = await test_client.post('/signatures', json=request)

        assert resp.status_code == 422
