from typing import Sequence

from multiproof import MultiProof, StandardMerkleTree
from sw_utils import compute_deposit_data
from web3 import Web3

from src.validators.typings import Validator


def generate_validators_tree(validators: list[Validator]) -> StandardMerkleTree:
    leaves: list[tuple[bytes, int]] = []
    for validator in validators:
        leaves.append((encode_tx_validator(validator), validator.deposit_data_index))

    return StandardMerkleTree.of(leaves, ['bytes', 'uint256'])


def get_validators_proof(
    tree: StandardMerkleTree,
    validators: Sequence[Validator],
) -> MultiProof:
    leaves: list[tuple[bytes, int]] = []
    for validator in validators:
        tx_validator = encode_tx_validator(validator)
        leaves.append((tx_validator, validator.deposit_data_index))

    return tree.get_multi_proof(leaves)


def encode_tx_validator(validator: Validator) -> bytes:
    public_key = Web3.to_bytes(hexstr=validator.public_key)
    signature = Web3.to_bytes(hexstr=validator.deposit_signature)
    deposit_root = compute_deposit_data(
        public_key=public_key,
        withdrawal_credentials=Web3.to_bytes(hexstr=validator.withdrawal_credentials),
        amount_gwei=validator.amount_gwei,
        signature=signature,
    ).hash_tree_root
    return public_key + signature + deposit_root


def _calc_leaf_indexes(deposit_data_indexes: list[int]) -> list[int]:
    if not deposit_data_indexes:
        return []

    sorted_indexes = sorted(deposit_data_indexes)
    return [deposit_data_indexes.index(index) for index in sorted_indexes]
