from typing import TYPE_CHECKING, Annotated, Union

from annotated_types import Ge
from eth_typing import HexStr
from pydantic import BaseModel, field_validator

from src.validators.fields import BLSPubkeyField, BLSSignatureField

if TYPE_CHECKING:
    from src.validators.typings import (
        OraclesExitSignatureShares as OraclesSharesDataclass,
    )
    from src.validators.typings import Validator


class ExitSignatureShareRequestItem(BaseModel):
    public_key: BLSPubkeyField
    exit_signature: BLSSignatureField


class ExitSignatureShareRequest(BaseModel):
    share_index: Annotated[int, Ge(0)]
    shares: list[ExitSignatureShareRequestItem]

    @field_validator('shares')
    @classmethod
    def shares_nonempty(cls, v: list) -> list:
        if not v:
            raise ValueError('list must be non-empty')
        return v


class ExitSignatureShareResponse(BaseModel):
    ...


class ValidatorsRequest(BaseModel):
    public_keys: list[BLSPubkeyField]

    @field_validator('public_keys')
    @classmethod
    def public_keys_nonempty(cls, v: list) -> list:
        if not v:
            raise ValueError('list must be non-empty')
        return v


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
    is_exit_signature_ready: bool

    @staticmethod
    def from_validator(v: 'Validator') -> 'ExitsResponseItem':
        return ExitsResponseItem(
            public_key=v.public_key,
            validator_index=v.validator_index,
            is_exit_signature_ready=bool(v.exit_signature),
        )


class ExitsResponse(BaseModel):
    exits: list[ExitsResponseItem]
