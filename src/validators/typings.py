from dataclasses import dataclass, field

from eth_account.signers.local import LocalAccount
from eth_typing import BlockNumber, BLSSignature, HexStr

from src.common.typings import Singleton


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
    exit_signature_shares: list[ExitSignatureShareRow] = field(default_factory=list)
    exit_signature: BLSSignature | None = None

    def get_exit_signature_share(
        self, public_key: HexStr, share_index: int
    ) -> ExitSignatureShareRow | None:
        for share in self.exit_signature_shares:
            if share.public_key == public_key and share.share_index == share_index:
                return share
        return None


class AppState(metaclass=Singleton):
    validators_manager_account: LocalAccount
    pending_validators: dict[HexStr, PendingValidator]
    exit_signature_shares: list[ExitSignatureShareRow]

    def get_exit_signature_shares(self, public_key: HexStr) -> list[ExitSignatureShareRow]:
        return [s for s in self.exit_signature_shares if s.public_key == public_key]
