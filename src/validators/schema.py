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
    # Fields used for building deposit and exit messages
    vault: HexStr
    public_key: HexStr
    amount: int
    validator_index: int
    validator_type: str

    # The `is_signatures_ready` flag indicates whether both deposit and exit signatures
    # are ready for the validator without exposing the signatures themselves.
    is_signatures_ready: bool

    # Timestamps for observability
    created_at_timestamp: int
    created_at_string: str

    # List of share indexes for which both deposit and exit signature shares have been submitted.
    # This can be used by the Sidecars to determine which shares are still missing.
    share_indexes_ready: list[int]

    @staticmethod
    def from_validator(v: 'Validator') -> 'ValidatorsResponseItem':
        return ValidatorsResponseItem(
            vault=v.vault,
            public_key=v.public_key,
            amount=v.amount,
            validator_index=v.validator_index,
            validator_type=v.validator_type.value,
            is_signatures_ready=bool(v.exit_signature) and bool(v.deposit_signature),
            created_at_timestamp=v.created_at,
            created_at_string=datetime.fromtimestamp(v.created_at, timezone.utc).strftime(
                '%Y-%m-%d %H:%M:%S%z'
            ),
            share_indexes_ready=sorted(
                v.exit_signature_shares.keys() & v.deposit_signature_shares.keys()
            ),
        )


class ValidatorsResponse(BaseModel):
    validators: list[ValidatorsResponseItem]


# End of validators data
