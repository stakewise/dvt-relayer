import os
from pathlib import Path
from time import time

import jwt
import pytest
from eth_typing import ChecksumAddress, HexStr
from httpx import AsyncClient, Response

from src.common.auth import JWT_ALGORITHM, load_jwt_secret
from src.common.tests.utils import create_jwt_token, patch_settings
from src.relayer.tests.utils import patch_vault_contract, setup_app_state


@pytest.fixture()
def withdraw_request(vault_address: ChecksumAddress, pubkey_1: HexStr) -> dict:
    return {
        'vault': vault_address,
        'public_keys': [pubkey_1],
        'amounts': [32000000000],
    }


async def _post_withdraw(client: AsyncClient, request: dict, token: str | None = None) -> Response:
    headers = {'Authorization': f'Bearer {token}'} if token is not None else None
    with patch_vault_contract(validators_manager_nonce=1):
        return await client.post('/withdraw', json=request, headers=headers)


class TestVerifyJwt:
    async def test_valid_token(
        self, anonymous_client: AsyncClient, jwt_secret: bytes, withdraw_request: dict
    ) -> None:
        setup_app_state()

        token = create_jwt_token(jwt_secret)
        assert (await _post_withdraw(anonymous_client, withdraw_request, token)).status_code == 200

    async def test_missing_token(
        self, anonymous_client: AsyncClient, withdraw_request: dict
    ) -> None:
        setup_app_state()

        assert (await _post_withdraw(anonymous_client, withdraw_request)).status_code == 401

    async def test_wrong_scheme(
        self, anonymous_client: AsyncClient, jwt_secret: bytes, withdraw_request: dict
    ) -> None:
        setup_app_state()

        headers = {'Authorization': f'Basic {create_jwt_token(jwt_secret)}'}
        with patch_vault_contract(validators_manager_nonce=1):
            resp = await anonymous_client.post('/withdraw', json=withdraw_request, headers=headers)
        assert resp.status_code == 401

    async def test_wrong_secret(
        self, anonymous_client: AsyncClient, withdraw_request: dict
    ) -> None:
        setup_app_state()

        token = create_jwt_token(os.urandom(32))
        assert (await _post_withdraw(anonymous_client, withdraw_request, token)).status_code == 401

    async def test_unsigned_token(
        self, anonymous_client: AsyncClient, withdraw_request: dict
    ) -> None:
        setup_app_state()

        token = jwt.encode({'iat': int(time())}, None, algorithm='none')
        assert (await _post_withdraw(anonymous_client, withdraw_request, token)).status_code == 401

    async def test_missing_iat(
        self, anonymous_client: AsyncClient, jwt_secret: bytes, withdraw_request: dict
    ) -> None:
        setup_app_state()

        token = jwt.encode({}, jwt_secret, algorithm=JWT_ALGORITHM)
        assert (await _post_withdraw(anonymous_client, withdraw_request, token)).status_code == 401

    @pytest.mark.parametrize('iat_shift', [-30, 30])
    async def test_iat_within_tolerance(
        self,
        anonymous_client: AsyncClient,
        jwt_secret: bytes,
        iat_shift: int,
        withdraw_request: dict,
    ) -> None:
        setup_app_state()

        token = create_jwt_token(jwt_secret, iat=time() + iat_shift)
        assert (await _post_withdraw(anonymous_client, withdraw_request, token)).status_code == 200

    @pytest.mark.parametrize('iat_shift', [-61, 61])
    async def test_stale_token(
        self,
        anonymous_client: AsyncClient,
        jwt_secret: bytes,
        iat_shift: int,
        withdraw_request: dict,
    ) -> None:
        setup_app_state()

        token = create_jwt_token(jwt_secret, iat=time() + iat_shift)
        resp = await _post_withdraw(anonymous_client, withdraw_request, token)
        assert resp.status_code == 401

    async def test_string_iat(
        self, anonymous_client: AsyncClient, jwt_secret: bytes, withdraw_request: dict
    ) -> None:
        setup_app_state()

        token = jwt.encode({'iat': str(int(time()))}, jwt_secret, algorithm=JWT_ALGORITHM)
        assert (await _post_withdraw(anonymous_client, withdraw_request, token)).status_code == 200

        token = jwt.encode({'iat': str(int(time()) - 61)}, jwt_secret, algorithm=JWT_ALGORITHM)
        assert (await _post_withdraw(anonymous_client, withdraw_request, token)).status_code == 401

    @pytest.mark.parametrize('path', ['/register', '/fund', '/withdraw', '/consolidate'])
    async def test_manager_endpoints_protected(
        self, anonymous_client: AsyncClient, path: str
    ) -> None:
        setup_app_state()

        resp = await anonymous_client.post(path, json={})
        assert resp.status_code == 401

    async def test_info_not_protected(self, anonymous_client: AsyncClient) -> None:
        setup_app_state()

        resp = await anonymous_client.get('/info')
        assert resp.status_code == 200


class TestLoadJwtSecret:
    @pytest.mark.parametrize('prefix', ['', '0x'])
    def test_load(self, tmp_path: Path, jwt_secret: bytes, prefix: str) -> None:
        secret_file = tmp_path / 'jwt.hex'
        secret_file.write_text(f'{prefix}{jwt_secret.hex()}\n')

        with patch_settings('jwt_secret_file', str(secret_file)):
            assert load_jwt_secret() == jwt_secret

    def test_missing_file(self, tmp_path: Path) -> None:
        with patch_settings('jwt_secret_file', str(tmp_path / 'missing.hex')):
            with pytest.raises(ValueError, match="Can't open JWT secret file"):
                load_jwt_secret()

    def test_not_hex(self, tmp_path: Path) -> None:
        secret_file = tmp_path / 'jwt.hex'
        secret_file.write_text('not-a-hex-string')

        with patch_settings('jwt_secret_file', str(secret_file)):
            with pytest.raises(ValueError, match='must be a hex string'):
                load_jwt_secret()

    def test_too_short(self, tmp_path: Path) -> None:
        secret_file = tmp_path / 'jwt.hex'
        secret_file.write_text(os.urandom(16).hex())

        with patch_settings('jwt_secret_file', str(secret_file)):
            with pytest.raises(ValueError, match='at least 32 bytes'):
                load_jwt_secret()
