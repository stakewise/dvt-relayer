from datetime import datetime, timezone
from typing import TYPE_CHECKING, Annotated

from annotated_types import Ge
from eth_typing import HexStr
from pydantic import BaseModel, field_validator

from src.validators.fields import BLSPubkeyField, BLSSignatureField

if TYPE_CHECKING:
    from src.relayer.typings import Validator


# Signature shares request submitted by DVT Sidecars


class SignatureShareRequestItem(BaseModel):
    public_key: BLSPubkeyField
    exit_signature: BLSSignatureField
    deposit_signature: BLSSignatureField


class SignatureShareRequest(BaseModel):
    share_index: Annotated[int, Ge(0)]
    shares: list[SignatureShareRequestItem]

    @field_validator('shares')
    @classmethod
    def shares_nonempty(cls, v: list) -> list:
        if not v:
            raise ValueError('list must be non-empty')
        return v


# End of signature shares request


class SignatureShareResponse(BaseModel):
    ...


# Validators data consumed by the DVT Sidecars to sign deposit messages and exit messages


class ValidatorsResponseItem(BaseModel):
    vault: HexStr
    public_key: HexStr
    amount: int
    validator_index: int
    validator_type: str
    is_exit_signature_ready: bool
    created_at_timestamp: int
    created_at_string: str
    share_indexes_ready: list[int]

    @staticmethod
    def from_validator(v: 'Validator') -> 'ValidatorsResponseItem':
        return ValidatorsResponseItem(
            vault=v.vault,
            public_key=v.public_key,
            amount=v.amount,
            validator_index=v.validator_index,
            validator_type=v.validator_type.value,
            is_exit_signature_ready=bool(v.exit_signature),
            created_at_timestamp=v.created_at,
            created_at_string=datetime.fromtimestamp(v.created_at, timezone.utc).strftime(
                '%Y-%m-%d %H:%M:%S%z'
            ),
            share_indexes_ready=sorted(list(v.exit_signature_shares.keys())),
        )


class ValidatorsResponse(BaseModel):
    validators: list[ValidatorsResponseItem]


# End of validators data
