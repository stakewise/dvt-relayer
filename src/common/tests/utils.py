from time import time

import jwt


def create_jwt_token(secret: bytes, iat: float | None = None) -> str:
    claims = {'iat': int(time() if iat is None else iat)}
    return jwt.encode(claims, secret, algorithm='HS256')
