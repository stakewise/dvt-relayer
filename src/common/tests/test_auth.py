import os
from pathlib import Path
from time import time
from unittest.mock import patch

import jwt
import pytest
from httpx import AsyncClient

from src.common.auth import load_jwt_secret
from src.common.tests.utils import create_jwt_token
from src.conftest import TEST_JWT_SECRET
from src.relayer.tests.test_endpoints import (
    PUBKEY_1,
    VAULT_ADDRESS,
    _setup_app_state,
    patch_vault_contract,
)

WITHDRAW_REQUEST = {
    'vault': VAULT_ADDRESS,
    'public_keys': [PUBKEY_1],
    'amounts': [32000000000],
}


async def _post_withdraw(client: AsyncClient, token: str | None = None) -> int:
    headers = {'Authorization': f'Bearer {token}'} if token is not None else None
    with patch_vault_contract(validators_manager_nonce=1):
        resp = await client.post('/withdraw', json=WITHDRAW_REQUEST, headers=headers)
    return resp.status_code


class TestVerifyJwt:
    async def test_valid_token(self, anonymous_client: AsyncClient) -> None:
        _setup_app_state()

        token = create_jwt_token(TEST_JWT_SECRET)
        assert await _post_withdraw(anonymous_client, token) == 200

    async def test_missing_token(self, anonymous_client: AsyncClient) -> None:
        _setup_app_state()

        assert await _post_withdraw(anonymous_client) == 401

    async def test_wrong_scheme(self, anonymous_client: AsyncClient) -> None:
        _setup_app_state()

        headers = {'Authorization': f'Basic {create_jwt_token(TEST_JWT_SECRET)}'}
        with patch_vault_contract(validators_manager_nonce=1):
            resp = await anonymous_client.post('/withdraw', json=WITHDRAW_REQUEST, headers=headers)
        assert resp.status_code == 401

    async def test_wrong_secret(self, anonymous_client: AsyncClient) -> None:
        _setup_app_state()

        token = create_jwt_token(os.urandom(32))
        assert await _post_withdraw(anonymous_client, token) == 401

    async def test_unsigned_token(self, anonymous_client: AsyncClient) -> None:
        _setup_app_state()

        token = jwt.encode({'iat': int(time())}, None, algorithm='none')
        assert await _post_withdraw(anonymous_client, token) == 401

    async def test_missing_iat(self, anonymous_client: AsyncClient) -> None:
        _setup_app_state()

        token = jwt.encode({}, TEST_JWT_SECRET, algorithm='HS256')
        assert await _post_withdraw(anonymous_client, token) == 401

    @pytest.mark.parametrize('iat_shift', [-61, 61])
    async def test_stale_token(self, anonymous_client: AsyncClient, iat_shift: int) -> None:
        _setup_app_state()

        token = create_jwt_token(TEST_JWT_SECRET, iat=time() + iat_shift)
        assert await _post_withdraw(anonymous_client, token) == 401

    @pytest.mark.parametrize('path', ['/register', '/fund', '/withdraw', '/consolidate'])
    async def test_manager_endpoints_protected(
        self, anonymous_client: AsyncClient, path: str
    ) -> None:
        _setup_app_state()

        resp = await anonymous_client.post(path, json={})
        assert resp.status_code == 401

    async def test_info_not_protected(self, anonymous_client: AsyncClient) -> None:
        _setup_app_state()

        resp = await anonymous_client.get('/info')
        assert resp.status_code == 200


class TestLoadJwtSecret:
    @pytest.mark.parametrize('prefix', ['', '0x'])
    def test_load(self, tmp_path: Path, prefix: str) -> None:
        secret_file = tmp_path / 'jwt.hex'
        secret_file.write_text(f'{prefix}{TEST_JWT_SECRET.hex()}\n')

        with patch('src.config.settings.jwt_secret_file', str(secret_file)):
            assert load_jwt_secret() == TEST_JWT_SECRET

    def test_missing_file(self, tmp_path: Path) -> None:
        with patch('src.config.settings.jwt_secret_file', str(tmp_path / 'missing.hex')):
            with pytest.raises(ValueError, match="Can't open JWT secret file"):
                load_jwt_secret()

    def test_not_hex(self, tmp_path: Path) -> None:
        secret_file = tmp_path / 'jwt.hex'
        secret_file.write_text('not-a-hex-string')

        with patch('src.config.settings.jwt_secret_file', str(secret_file)):
            with pytest.raises(ValueError, match='must be a hex string'):
                load_jwt_secret()

    def test_too_short(self, tmp_path: Path) -> None:
        secret_file = tmp_path / 'jwt.hex'
        secret_file.write_text(os.urandom(16).hex())

        with patch('src.config.settings.jwt_secret_file', str(secret_file)):
            with pytest.raises(ValueError, match='at least 32 bytes'):
                load_jwt_secret()
