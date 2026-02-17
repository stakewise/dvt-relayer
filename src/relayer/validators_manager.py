import json
import os
from typing import Sequence

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress, HexStr
from web3 import Web3
from web3.types import Gwei

from src.app_state import AppState
from src.config import settings
from src.relayer.typings import Validator, ValidatorType


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


def get_validators_manager_signature_register(
    vault: ChecksumAddress, validators_registry_root: HexStr, validators: Sequence[Validator]
) -> HexStr:
    encoded_validators = [_encode_validator(v) for v in validators]
    return _create_and_sign_message(
        vault=vault,
        validators=b''.join(encoded_validators),
        validators_registry_root=Web3.to_bytes(hexstr=validators_registry_root),
    )


def get_validators_manager_signature_funding(
    vault: ChecksumAddress, validators_manager_nonce: int, validators: Sequence[Validator]
) -> HexStr:
    encoded_validators = [_encode_validator(v) for v in validators]
    return _create_and_sign_message(
        vault=vault,
        validators=b''.join(encoded_validators),
        validators_registry_root=validators_manager_nonce.to_bytes(32, byteorder='big'),
    )


def get_validators_manager_signature_withdrawal(
    vault: ChecksumAddress,
    validators_manager_nonce: int,
    public_keys: list[HexStr],
    amounts: list[Gwei],
) -> HexStr:
    encoded_withdrawals = _encode_withdrawals(public_keys, amounts)
    return _create_and_sign_message(
        vault=vault,
        validators=encoded_withdrawals,
        validators_registry_root=validators_manager_nonce.to_bytes(32, byteorder='big'),
    )


def get_validators_manager_signature_consolidation(
    vault: ChecksumAddress,
    validators_manager_nonce: int,
    source_public_keys: list[HexStr],
    target_public_keys: list[HexStr],
) -> HexStr:
    encoded_consolidations = _encode_consolidations(source_public_keys, target_public_keys)
    return _create_and_sign_message(
        vault=vault,
        validators=encoded_consolidations,
        validators_registry_root=validators_manager_nonce.to_bytes(32, byteorder='big'),
    )


def _encode_validator(v: Validator) -> bytes:
    encoded_validator = [
        Web3.to_bytes(hexstr=v.public_key),
        Web3.to_bytes(hexstr=v.deposit_signature),
        Web3.to_bytes(hexstr=v.deposit_data_root),
    ]
    if v.validator_type == ValidatorType.V2:
        encoded_validator.append(v.amount.to_bytes(8, byteorder='big'))
    return b''.join(encoded_validator)


def _encode_withdrawals(public_keys: list[HexStr], amounts: list[Gwei]) -> bytes:
    data = b''
    for public_key, amount in zip(public_keys, amounts):
        data += Web3.to_bytes(hexstr=public_key)
        data += amount.to_bytes(8, byteorder='big')

    return data


def _encode_consolidations(
    source_public_keys: list[HexStr], target_public_keys: list[HexStr]
) -> bytes:
    validators_data = b''
    for source_key, target_key in zip(source_public_keys, target_public_keys):
        validators_data += Web3.to_bytes(hexstr=source_key)
        validators_data += Web3.to_bytes(hexstr=target_key)
    return validators_data


def _create_and_sign_message(
    vault: ChecksumAddress, validators: bytes, validators_registry_root: bytes
) -> HexStr:
    full_message = {
        'primaryType': 'VaultValidators',
        'types': {
            'VaultValidators': [
                {'name': 'validatorsRegistryRoot', 'type': 'bytes32'},
                {'name': 'validators', 'type': 'bytes'},
            ],
        },
        'domain': {
            'name': 'VaultValidators',
            'version': '1',
            'chainId': settings.network_config.CHAIN_ID,
            'verifyingContract': vault,
        },
        'message': {
            'validatorsRegistryRoot': validators_registry_root,
            'validators': validators,
        },
    }

    app_state = AppState()
    encoded_message = encode_typed_data(full_message=full_message)
    signed_msg = app_state.validators_manager_account.sign_message(encoded_message)

    return HexStr(signed_msg.signature.hex())
