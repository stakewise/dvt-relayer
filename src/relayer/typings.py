from dataclasses import dataclass
from enum import Enum

from eth_typing import BLSSignature, HexStr
from web3.types import Gwei


class ValidatorType(Enum):
    V1 = '0x01'
    V2 = '0x02'


@dataclass
class Validator:
    public_key: HexStr
    deposit_data_root: HexStr
    deposit_signature: HexStr
    amount: Gwei
    validator_type: ValidatorType = ValidatorType.V2
    exit_signature: BLSSignature | None = None
