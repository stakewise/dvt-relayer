from dataclasses import dataclass, field
from typing import Union

from eth_typing import BlockNumber, BLSSignature, HexStr


@dataclass
class NetworkValidator:
    public_key: HexStr
    block_number: BlockNumber


@dataclass
class Validator:
    public_key: HexStr
    validator_index: int
    created_at: int
    exit_signature: BLSSignature | None = None

    # DVT operators' shares
    exit_signature_shares: dict[int, BLSSignature] = field(default_factory=dict)

    # Oracles' shares
    oracles_exit_signature_shares: Union['OraclesExitSignatureShares', None] = None


@dataclass
class OraclesExitSignatureShares:
    public_keys: list[HexStr]
    encrypted_exit_signatures: list[HexStr]
