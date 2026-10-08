import os
from binascii import unhexlify
from time import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app_state import AppState
from src.config import settings

JWT_ALGORITHM = 'HS256'
JWT_SECRET_MIN_LENGTH = 32

bearer_scheme = HTTPBearer(auto_error=False)


def load_jwt_secret() -> bytes:
    """
    Loads hex-encoded JWT secret from file, the same format as Engine API `jwt.hex`.
    Generate with `openssl rand -hex 32`.
    """
    jwt_secret_file = settings.jwt_secret_file
    if not os.path.isfile(jwt_secret_file):
        raise ValueError(f"Can't open JWT secret file. Path: {jwt_secret_file}")

    with open(jwt_secret_file, 'r', encoding='utf-8') as f:
        secret_hex = f.read().strip().removeprefix('0x')
    try:
        secret = unhexlify(secret_hex)
    except ValueError as e:
        raise ValueError('JWT secret must be a hex string') from e

    if len(secret) < JWT_SECRET_MIN_LENGTH:
        raise ValueError(f'JWT secret must be at least {JWT_SECRET_MIN_LENGTH} bytes')
    return secret


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """
    Checks `Authorization: Bearer <token>` header.
    Token must be signed with HS256 and contain fresh `iat` claim.
    """
    if credentials is None:
        raise _unauthorized('Missing bearer token')

    try:
        claims = jwt.decode(
            credentials.credentials,
            AppState().jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={'require': ['iat']},
        )
    except jwt.PyJWTError as e:
        raise _unauthorized('Invalid token') from e

    if abs(time() - claims['iat']) > settings.jwt_iat_tolerance:
        raise _unauthorized('Stale token')


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={'WWW-Authenticate': 'Bearer'},
    )
