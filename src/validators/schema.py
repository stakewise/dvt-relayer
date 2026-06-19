from datetime import datetime, timezone
from typing import TYPE_CHECKING, Annotated

from annotated_types import Ge
from eth_typing import BLSPubkey, BLSSignature, HexStr
from pydantic import BaseModel, field_validator, model_validator
from web3 import Web3

from src.app_state import AppState
from src.validators.exit_signature import (
    validate_deposit_signature_share,
    validate_exit_signature_share,
    validate_public_key_shares,
)
from src.validators.fields import BLSPubkeyField, BLSSignatureField

if TYPE_CHECKING:
    from src.relayer.typings import Validator


# Signature shares request submitted by DVT Sidecars


class PublicKeyShare(BaseModel):
    share_index: Annotated[int, Ge(0)]
    public_key_share: BLSPubkeyField


class SignatureShareRequestItem(BaseModel):
    public_key: BLSPubkeyField
    # All operators' public key shares. Lets the relayer reconstruct the full validator
    # public key and verify each submitted signature share against its public key share.
    public_key_shares: list[PublicKeyShare]
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

    @model_validator(mode='after')
    def validate_signature_shares(self) -> 'SignatureShareRequest':
        """
        Validates submitted shares against the registered validators in AppState:
        * the public key shares must reconstruct to the full validator public key;
        * the exit and deposit signature shares must verify against the operator's
          public key share at this `share_index`.
        Shares for unknown validators are ignored (the endpoint skips them too).
        """
        validators = AppState().validators

        for share in self.shares:
            validator = validators.get(share.public_key)
            if validator is None:
                continue

            shares_by_index = {
                pks.share_index: BLSPubkey(Web3.to_bytes(hexstr=pks.public_key_share))
                for pks in share.public_key_shares
            }
            if not validate_public_key_shares(share.public_key, shares_by_index):
                raise ValueError(f'invalid public key shares for public_key={share.public_key}')

            public_key_share = shares_by_index.get(self.share_index)
            if public_key_share is None:
                raise ValueError(
                    f'missing public key share for public_key={share.public_key},'
                    f' share_index={self.share_index}'
                )

            if not validate_exit_signature_share(
                validator.validator_index,
                public_key_share,
                BLSSignature(Web3.to_bytes(hexstr=share.exit_signature)),
            ):
                raise ValueError(
                    f'invalid exit signature share for public_key={share.public_key},'
                    f' share_index={self.share_index}'
                )

            if not validate_deposit_signature_share(
                public_key_share,
                validator.public_key,
                Web3.to_bytes(hexstr=validator.withdrawal_credentials),
                validator.amount,
                BLSSignature(Web3.to_bytes(hexstr=share.deposit_signature)),
            ):
                raise ValueError(
                    f'invalid deposit signature share for public_key={share.public_key},'
                    f' share_index={self.share_index}'
                )

        return self


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
