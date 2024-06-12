import json
from pathlib import Path

from eth_utils import add_0x_prefix

from src.validators.typings import Validator


def load_deposit_data(deposit_data_file: Path) -> list[Validator]:
    with open(deposit_data_file, 'r', encoding='utf-8') as f:
        deposit_data = json.load(f)

    validators = []
    for deposit_data_index, item in enumerate(deposit_data):
        validators.append(
            Validator(
                deposit_data_index=deposit_data_index,
                public_key=add_0x_prefix(item['pubkey']),
                signature=add_0x_prefix(item['signature']),
                amount_gwei=int(item['amount']),
            )
        )
    return validators
