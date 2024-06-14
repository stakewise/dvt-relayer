from dataclasses import dataclass

from eth_account.signers.local import LocalAccount
from eth_typing import BLSSignature, HexStr

from src.common.typings import Singleton


@dataclass
class Validator:
    public_key: HexStr
    deposit_data_root: HexStr
    deposit_signature: HexStr
    amount_gwei: int


@dataclass
class PendingValidator:
    public_key: HexStr
    validator_index: int


@dataclass
class ExitSignatureShareRow:
    public_key: HexStr
    share_index: int
    signature: BLSSignature


@dataclass
class ExitSignatureRow:
    public_key: HexStr
    signature: BLSSignature


class AppState(metaclass=Singleton):
    validators: list[Validator]
    validators_manager_account: LocalAccount
    pending_validators: list[PendingValidator]
    exit_signature_shares: list[ExitSignatureShareRow]
    exit_signatures: list[ExitSignatureRow]

    def get_validator(self, public_key: str) -> Validator | None:
        for validator in self.validators:
            if validator.public_key == public_key:
                return validator
        return None

    def get_exit_signature_share(
        self, public_key: HexStr, share_index: int
    ) -> ExitSignatureShareRow | None:
        for share in self.exit_signature_shares:
            if share.public_key == public_key and share.share_index == share_index:
                return share
        return None

    def get_exit_signature_shares(self, public_key: HexStr) -> list[ExitSignatureShareRow]:
        return [s for s in self.exit_signature_shares if s.public_key == public_key]

    def get_exit_signature(self, public_key: HexStr) -> BLSSignature | None:
        for row in self.exit_signatures:
            if row.public_key == public_key:
                return row.signature
        return None

    def remove_pending_validator(self, public_key: HexStr) -> None:
        for index, pv in enumerate(self.pending_validators):
            if pv.public_key == public_key:
                self.pending_validators.pop(index)
                break

    def get_available_validators(self, validators_count: int) -> list[Validator]:
        return self.validators[:validators_count]
