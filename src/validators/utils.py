import json
import logging
from pathlib import Path

from eth_utils import add_0x_prefix

from src.validators.proof import generate_validators_tree
from src.validators.typings import DepositData, Validator

logger = logging.getLogger(__name__)


def load_deposit_data(deposit_data_file: Path) -> DepositData:
    logger.info('loading deposit data from %s', deposit_data_file)

    with open(deposit_data_file, 'r', encoding='utf-8') as f:
        deposit_data = json.load(f)

    validators = []
    for deposit_data_index, item in enumerate(deposit_data):
        validators.append(
            Validator(
                public_key=add_0x_prefix(item['pubkey']),
                withdrawal_credentials=add_0x_prefix(item['withdrawal_credentials']),
                deposit_signature=add_0x_prefix(item['signature']),
                amount_gwei=int(item['amount']),
                deposit_data_root=add_0x_prefix(item['deposit_data_root']),
                deposit_data_index=deposit_data_index,
            )
        )
    tree = generate_validators_tree(validators)
    return DepositData(validators=validators, tree=tree)
