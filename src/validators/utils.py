import json
import os
from pathlib import Path

from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_utils import add_0x_prefix

from src.config import settings
from src.validators.typings import Validator


def load_deposit_data(deposit_data_file: Path) -> list[Validator]:
    with open(deposit_data_file, 'r', encoding='utf-8') as f:
        deposit_data = json.load(f)

    validators = []
    for item in deposit_data:
        validators.append(
            Validator(
                deposit_data_root=add_0x_prefix(item['deposit_data_root']),
                public_key=add_0x_prefix(item['pubkey']),
                deposit_signature=add_0x_prefix(item['signature']),
                amount_gwei=int(item['amount']),
            )
        )
    return validators


def load_validators_manager_account() -> LocalAccount:
    keystore_file = settings.validators_manager_key_file
    keystore_password_file = settings.validators_manager_password_file
    if not os.path.isfile(keystore_file):
        raise ValueError(f"Can't open key file. Path: {keystore_file}")
    if not os.path.isfile(keystore_password_file):
        raise ValueError(f"Can't open password file. Path: {keystore_password_file}")

    with open(keystore_file, 'r', encoding='utf-8') as f:
        keyfile_json = json.load(f)
    with open(keystore_password_file, 'r', encoding='utf-8') as f:
        password = f.read().strip()
    key = Account.decrypt(keyfile_json, password)
    return Account().from_key(key)
