from typing import TYPE_CHECKING, Union

from eth_typing import HexStr
from pydantic import BaseModel

if TYPE_CHECKING:
    from src.validators.typings import (
        OraclesExitSignatureShares as OraclesSharesDataclass,
    )
    from src.validators.typings import Validator


class ExitSignatureShareRequestItem(BaseModel):
    public_key: HexStr
    exit_signature: HexStr


class ExitSignatureShareRequest(BaseModel):
    share_index: int
    shares: list[ExitSignatureShareRequestItem]


class ExitSignatureShareResponse(BaseModel):
    ...


class ValidatorsRequest(BaseModel):
    public_keys: list[HexStr]


class CreateValidatorsResponseItem(BaseModel):
    public_key: HexStr
    oracles_exit_signature_shares: Union['OraclesExitSignatureShares', None]

    @staticmethod
    def from_validator(v: 'Validator') -> 'CreateValidatorsResponseItem':
        oracles_exit_signature_shares = None
        if shares := v.oracles_exit_signature_shares:
            oracles_exit_signature_shares = OraclesExitSignatureShares.from_dataclass(shares)

        return CreateValidatorsResponseItem(
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


class CreateValidatorsResponse(BaseModel):
    ready: bool
    validators: list[CreateValidatorsResponseItem]


class ExitsResponseItem(BaseModel):
    public_key: HexStr
    validator_index: int

    @staticmethod
    def from_validator(v: 'Validator') -> 'ExitsResponseItem':
        return ExitsResponseItem(public_key=v.public_key, validator_index=v.validator_index)


class ExitsResponse(BaseModel):
    exits: list[ExitsResponseItem]
