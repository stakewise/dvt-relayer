from dataclasses import dataclass, field
from enum import Enum

from eth_typing import BLSSignature, HexStr
from web3.types import Gwei

from src.validators.typings import OraclesExitSignatureShares


class ValidatorType(Enum):
    V1 = '0x01'
    V2 = '0x02'


@dataclass
class Validator:  # pylint: disable=too-many-instance-attributes
    public_key: HexStr

    # Relayer fields
    deposit_data_root: HexStr = HexStr('')
    deposit_signature: HexStr = HexStr('')
    amount: Gwei = Gwei(0)
    validator_type: ValidatorType = ValidatorType.V2

    # DVT exit signature fields
    validator_index: int = 0
    created_at: int = 0
    exit_signature: BLSSignature | None = None
    exit_signature_shares: dict[int, BLSSignature] = field(default_factory=dict)
    oracles_exit_signature_shares: OraclesExitSignatureShares | None = None
