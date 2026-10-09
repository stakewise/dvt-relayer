from time import time
from unittest.mock import AsyncMock, patch

import pytest
from eth_typing import BLSSignature, ChecksumAddress, HexStr
from httpx import AsyncClient
from sw_utils.tests import faker
from web3 import Web3
from web3.types import Gwei

from src.app_state import AppState
from src.config.networks import NETWORKS
from src.relayer.tests.utils import patch_vault_contract, setup_app_state
from src.relayer.typings import Validator, ValidatorType

# A dummy 96-byte BLS signature
DUMMY_SIGNATURE = BLSSignature(b'\x01' * 96)


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

    async def test_register_creates_new_validators(
        self,
        test_client: AsyncClient,
        vault_address: ChecksumAddress,
        pubkey_1: HexStr,
        pubkey_2: HexStr,
    ) -> None:
        """Test that /register creates validators for unregistered public keys."""
        setup_app_state(unregistered_keys=[pubkey_1, pubkey_2])

        resp = await test_client.post(
            '/register',
            json={
                'vault': vault_address,
                'validators_start_index': 100,
                'amounts': [32000000000, 32000000000],
                'validator_type': '0x01',
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 2
        assert data['validators'][0]['public_key'] == pubkey_1
        assert data['validators'][1]['public_key'] == pubkey_2
        assert data['validators'][0]['amount'] == 32000000000
        assert data['validators_manager_signature'] is None

    async def test_register_returns_existing_validators(
        self, test_client: AsyncClient, vault_address: ChecksumAddress, pubkey_1: HexStr
    ) -> None:
        """Test that /register returns existing validators if they match."""
        existing_validator = Validator(
            public_key=pubkey_1,
            vault=vault_address,
            validator_index=100,
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
        )
        setup_app_state(
            unregistered_keys=[pubkey_1],
            validators={pubkey_1: existing_validator},
        )

        resp = await test_client.post(
            '/register',
            json={
                'vault': vault_address,
                'validators_start_index': 100,
                'amounts': [32000000000],
                'validator_type': '0x01',
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 1
        assert data['validators'][0]['public_key'] == pubkey_1

    async def test_register_with_signatures_ready(
        self, test_client: AsyncClient, vault_address: ChecksumAddress, pubkey_1: HexStr
    ) -> None:
        """Test that /register returns validators_manager_signature when all sigs ready."""
        validator = Validator(
            public_key=pubkey_1,
            vault=vault_address,
            validator_index=100,
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
            deposit_signature=DUMMY_SIGNATURE,
            exit_signature=DUMMY_SIGNATURE,
        )
        setup_app_state(
            unregistered_keys=[pubkey_1],
            validators={pubkey_1: validator},
        )

        mock_root = b'\x00' * 32
        with patch('src.relayer.endpoints.validators_registry_contract') as mock_contract:
            mock_contract.get_registry_root = AsyncMock(return_value=mock_root)
            resp = await test_client.post(
                '/register',
                json={
                    'vault': vault_address,
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
        self, test_client: AsyncClient, vault_address: ChecksumAddress, pubkey_1: HexStr
    ) -> None:
        """Test that a new validator is created if the index doesn't match."""
        existing_validator = Validator(
            public_key=pubkey_1,
            vault=vault_address,
            validator_index=50,  # different index
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V1,
        )
        setup_app_state(
            unregistered_keys=[pubkey_1],
            validators={pubkey_1: existing_validator},
        )

        resp = await test_client.post(
            '/register',
            json={
                'vault': vault_address,
                'validators_start_index': 100,
                'amounts': [32000000000],
                'validator_type': '0x01',
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data['validators']) == 1
        app_state = AppState()
        assert app_state.validators[pubkey_1].validator_index == 100


class TestRegisterEmptyAmounts:
    async def test_register_empty_amounts_rejected(
        self, test_client: AsyncClient, vault_address: ChecksumAddress
    ) -> None:
        """Test that /register rejects empty amounts list."""
        resp = await test_client.post(
            '/register',
            json={
                'vault': vault_address,
                'validators_start_index': 100,
                'amounts': [],
                'validator_type': '0x01',
            },
        )
        assert resp.status_code == 422


class TestFundEndpoint:
    async def test_fund_empty_amounts_rejected(
        self, test_client: AsyncClient, vault_address: ChecksumAddress, pubkey_1: HexStr
    ) -> None:
        """Test that /fund rejects empty amounts list."""
        resp = await test_client.post(
            '/fund',
            json={
                'vault': vault_address,
                'public_keys': [pubkey_1],
                'amounts': [],
            },
        )
        assert resp.status_code == 422

    async def test_fund_validators(
        self,
        test_client: AsyncClient,
        vault_address: ChecksumAddress,
        pubkey_1: HexStr,
        pubkey_2: HexStr,
    ) -> None:
        """Test that /fund returns a validators_manager_signature."""
        setup_app_state()

        with patch_vault_contract(validators_manager_nonce=1):
            resp = await test_client.post(
                '/fund',
                json={
                    'vault': vault_address,
                    'public_keys': [pubkey_1, pubkey_2],
                    'amounts': [32000000000, 32000000000],
                },
            )

        assert resp.status_code == 200
        assert resp.json()['validators_manager_signature'] is not None


class TestWithdrawEndpoint:
    async def test_withdraw_empty_amounts_rejected(
        self, test_client: AsyncClient, vault_address: ChecksumAddress, pubkey_1: HexStr
    ) -> None:
        """Test that /withdraw rejects empty amounts list."""
        resp = await test_client.post(
            '/withdraw',
            json={
                'vault': vault_address,
                'public_keys': [pubkey_1],
                'amounts': [],
            },
        )
        assert resp.status_code == 422

    async def test_withdraw_validators(
        self, test_client: AsyncClient, vault_address: ChecksumAddress, pubkey_1: HexStr
    ) -> None:
        """Test that /withdraw returns a validators_manager_signature."""
        setup_app_state()

        with patch_vault_contract(validators_manager_nonce=1):
            resp = await test_client.post(
                '/withdraw',
                json={
                    'vault': vault_address,
                    'public_keys': [pubkey_1],
                    'amounts': [32000000000],
                },
            )

        assert resp.status_code == 200
        assert resp.json()['validators_manager_signature'] is not None


class TestConsolidateEndpoint:
    async def test_consolidate_validators(
        self,
        test_client: AsyncClient,
        vault_address: ChecksumAddress,
        pubkey_1: HexStr,
        pubkey_2: HexStr,
    ) -> None:
        """Test that /consolidate returns a validators_manager_signature."""
        setup_app_state()

        with patch_vault_contract(validators_manager_nonce=1):
            resp = await test_client.post(
                '/consolidate',
                json={
                    'vault': vault_address,
                    'source_public_keys': [pubkey_1],
                    'target_public_keys': [pubkey_2],
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
        setup_app_state(unregistered_keys=[public_key])

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
        setup_app_state(unregistered_keys=public_keys)

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

    def _make_validator(self, public_key: HexStr) -> Validator:
        return Validator(
            public_key=public_key,
            vault=Web3.to_checksum_address(DVT_VAULT),
            validator_index=10,
            created_at=int(time()),
            amount=Gwei(32000000000),
            validator_type=ValidatorType.V2,
        )

    async def test_rejects_public_key_shares_that_do_not_reconstruct(
        self, test_client: AsyncClient, pubkey_1: HexStr
    ) -> None:
        """Public key shares that don't reconstruct to the validator pubkey are rejected."""
        validator = self._make_validator(pubkey_1)
        setup_app_state(validators={pubkey_1: validator})

        request = {
            'share_index': 1,
            'shares': [
                {
                    'public_key': pubkey_1,
                    # Random shares — won't reconstruct to pubkey_1
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

    async def test_rejects_missing_public_key_shares_field(
        self, test_client: AsyncClient, pubkey_1: HexStr
    ) -> None:
        """The public_key_shares field is required by the schema."""
        setup_app_state(validators={pubkey_1: self._make_validator(pubkey_1)})

        request = {
            'share_index': 1,
            'shares': [
                {
                    'public_key': pubkey_1,
                    'exit_signature': faker.validator_signature(),
                    'deposit_signature': faker.validator_signature(),
                }
            ],
        }

        resp = await test_client.post('/signatures', json=request)

        assert resp.status_code == 422
