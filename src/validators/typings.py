from dataclasses import dataclass, field

from eth_typing import BLSSignature, HexStr


@dataclass
class OraclesExitSignatureShares:
    public_keys: list[HexStr]
    encrypted_exit_signatures: list[HexStr]


@dataclass
class Validator:
    public_key: HexStr
    validator_index: int
    created_at: int
    exit_signature: BLSSignature | None = None

    # DVT operators' shares
    exit_signature_shares: dict[int, BLSSignature] = field(default_factory=dict)

    # Oracles' shares
    oracles_exit_signature_shares: OraclesExitSignatureShares | None = None
