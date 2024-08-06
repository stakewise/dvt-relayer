from dataclasses import dataclass, field
from typing import Union

from eth_typing import BlockNumber, BLSSignature, HexStr


@dataclass
class NetworkValidator:
    public_key: HexStr
    block_number: BlockNumber


@dataclass
class ExitSignatureShareRow:
    public_key: HexStr
    share_index: int
    signature: BLSSignature


@dataclass
class PendingValidator:
    public_key: HexStr
    validator_index: int
    exit_signature: BLSSignature | None = None

    # DVT operators' shares
    exit_signature_shares: list[ExitSignatureShareRow] = field(default_factory=list)

    # Oracles' shares
    oracles_exit_signature_shares: Union['OraclesExitSignatureShares', None] = None

    def get_exit_signature_share(
        self, public_key: HexStr, share_index: int
    ) -> ExitSignatureShareRow | None:
        for share in self.exit_signature_shares:
            if share.public_key == public_key and share.share_index == share_index:
                return share
        return None


@dataclass
class OraclesExitSignatureShares:
    public_keys: list[HexStr]
    encrypted_exit_signatures: list[HexStr]
