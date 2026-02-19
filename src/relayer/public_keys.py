import csv
import os

from eth_typing import HexStr

from src.config import settings
from src.validators.validators import validate_bls_pubkey


def load_public_keys() -> list[HexStr]:
    public_keys_file = settings.public_keys_file
    if not os.path.isfile(public_keys_file):
        raise ValueError(f"Can't open public keys file. Path: {public_keys_file}")

    public_keys: list[HexStr] = []
    with open(public_keys_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            public_key = validate_bls_pubkey(HexStr(row[0].strip()))
            public_keys.append(public_key)

    if not public_keys:
        raise ValueError(f'No public keys found in file. Path: {public_keys_file}')

    return public_keys
