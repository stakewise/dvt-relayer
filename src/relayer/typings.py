from dataclasses import dataclass, field
from enum import Enum

from eth_typing import BLSSignature, ChecksumAddress, HexStr
from sw_utils import (
    DepositData,
    get_v1_withdrawal_credentials,
    get_v2_withdrawal_credentials,
)
from web3 import Web3
from web3.types import Gwei

from src.validators.typings import OraclesExitSignatureShares


class ValidatorType(Enum):
    V1 = '0x01'
    V2 = '0x02'


@dataclass
class Validator:  # pylint: disable=too-many-instance-attributes
    public_key: HexStr

    # Deposit message signing fields
    vault: ChecksumAddress
    amount: Gwei
    validator_type: ValidatorType

    # Exit message signing fields
    validator_index: int

    # Metadata
    created_at: int

    # Exit signature
    exit_signature: BLSSignature | None = None
    exit_signature_shares: dict[int, BLSSignature] = field(default_factory=dict)
    oracles_exit_signature_shares: OraclesExitSignatureShares | None = None

    # Deposit signature
    deposit_signature: BLSSignature | None = None
    deposit_signature_shares: dict[int, BLSSignature] = field(default_factory=dict)

    @property
    def deposit_data(self) -> DepositData:
        if not self.deposit_signature:
            raise ValueError('Deposit signature is not set')

        return DepositData(
            pubkey=Web3.to_bytes(hexstr=self.public_key),
            withdrawal_credentials=Web3.to_bytes(hexstr=self.withdrawal_credentials),
            amount=self.amount,
            signature=self.deposit_signature,
        )

    @property
    def withdrawal_credentials(self) -> HexStr:
        if self.validator_type == ValidatorType.V1:
            return Web3.to_hex(get_v1_withdrawal_credentials(self.vault))

        if self.validator_type == ValidatorType.V2:
            return Web3.to_hex(get_v2_withdrawal_credentials(self.vault))

        raise ValueError(f'Unknown validator type: {self.validator_type}')

    @property
    def deposit_data_root(self) -> HexStr:
        return Web3.to_hex(self.deposit_data.hash_tree_root)
