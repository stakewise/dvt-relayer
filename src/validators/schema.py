from typing import TYPE_CHECKING, Union

from eth_typing import HexStr
from pydantic import BaseModel

if TYPE_CHECKING:
    from src.validators.typings import (
        OraclesExitSignatureShares as OraclesSharesDataclass,
    )
    from src.validators.typings import PendingValidator


class ExitSignatureShareRequest(BaseModel):
    public_key: HexStr
    share_index: int
    signature: HexStr


class ExitSignatureShareResponse(BaseModel):
    ...


class ValidatorsRequest(BaseModel):
    public_keys: list[HexStr]


class ValidatorsResponseItem(BaseModel):
    public_key: HexStr
    oracles_exit_signature_shares: Union['OraclesExitSignatureShares', None]

    @staticmethod
    def from_validator(v: 'PendingValidator') -> 'ValidatorsResponseItem':
        oracles_exit_signature_shares = None
        if shares := v.oracles_exit_signature_shares:
            oracles_exit_signature_shares = OraclesExitSignatureShares.from_dataclass(shares)

        return ValidatorsResponseItem(
            public_key=v.public_key, oracles_exit_signature_shares=oracles_exit_signature_shares
        )


class OraclesExitSignatureShares(BaseModel):
    public_keys: list[HexStr]
    encrypted_exit_signatures: list[HexStr]

    @staticmethod
    def from_dataclass(d: 'OraclesSharesDataclass') -> 'OraclesExitSignatureShares':
        return OraclesExitSignatureShares(
            public_keys=d.public_keys,
            encrypted_exit_signatures=d.encrypted_exit_signatures,
        )


class ValidatorsResponse(BaseModel):
    ready: bool
    validators: list[ValidatorsResponseItem]


class PendingValidatorResponseItem(BaseModel):
    public_key: HexStr
    validator_index: int


class PendingValidatorResponse(BaseModel):
    pending_validators: list[PendingValidatorResponseItem]
