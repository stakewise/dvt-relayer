from collections.abc import Iterator
from contextlib import contextmanager
from time import time
from typing import Any
from unittest.mock import patch

import jwt

from src.common.auth import JWT_ALGORITHM
from src.config import settings


def create_jwt_token(secret: bytes, iat: float | None = None) -> str:
    claims = {'iat': int(time() if iat is None else iat)}
    return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


@contextmanager
def patch_settings(key: str, value: Any) -> Iterator[None]:
    """
    Temporarily overrides a settings attribute.
    Settings is a global singleton, so direct assignment leaks into other tests.
    """
    with patch.object(settings, key, value):
        yield
