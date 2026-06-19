from typing import TYPE_CHECKING

from eth_typing import BLSSignature
from fastapi import APIRouter, HTTPException
from web3 import Web3

from src.app_state import AppState
from src.config import settings
from src.validators.exit_signature import (
    get_oracles_exit_signature_shares,
    validate_deposit_signature,
    validate_exit_signature,
)
from src.validators.key_shares import reconstruct_shared_bls_signature
from src.validators.schema import (
    SignatureShareRequest,
    SignatureShareResponse,
    ValidatorsResponse,
    ValidatorsResponseItem,
)

if TYPE_CHECKING:
    from src.relayer.typings import Validator

router = APIRouter()


@router.get('/validators')
async def get_validators() -> ValidatorsResponse:
    app_state = AppState()
    response = ValidatorsResponse(validators=[])

    for validator in app_state.validators.values():
        response.validators.append(ValidatorsResponseItem.from_validator(validator))
    return response


@router.post('/signatures')
async def submit_signature_shares(
    request: SignatureShareRequest,
) -> SignatureShareResponse:
    app_state = AppState()

    for share in request.shares:
        validator = app_state.validators.get(share.public_key)
        if validator is None:
            continue

        # Save shares if not already saved (shares are validated, so first-write-wins is safe)
        validator.exit_signature_shares.setdefault(
            request.share_index, BLSSignature(Web3.to_bytes(hexstr=share.exit_signature))
        )
        validator.deposit_signature_shares.setdefault(
            request.share_index, BLSSignature(Web3.to_bytes(hexstr=share.deposit_signature))
        )

        await _reconstruct_exit_signature(validator)
        _reconstruct_deposit_signature(validator)

    return SignatureShareResponse()


async def _reconstruct_exit_signature(validator: 'Validator') -> None:
    """Reconstructs the full exit signature once the share threshold is reached."""
    if (
        validator.exit_signature is not None
        or len(validator.exit_signature_shares) < settings.signature_threshold
    ):
        return

    try:
        exit_signature = reconstruct_shared_bls_signature(validator.exit_signature_shares)
        is_valid = validate_exit_signature(
            validator.public_key, validator.validator_index, exit_signature
        )
    except Exception as e:
        validator.exit_signature_shares.clear()
        raise HTTPException(
            status_code=400,
            detail=f'failed to reconstruct exit signature for public_key={validator.public_key}',
        ) from e
    if not is_valid:
        validator.exit_signature_shares.clear()
        raise HTTPException(
            status_code=400,
            detail=f'invalid exit signature for public_key={validator.public_key}',
        )

    validator.exit_signature = exit_signature

    # Split exit signature into shares for oracles
    validator.oracles_exit_signature_shares = await get_oracles_exit_signature_shares(
        public_key=validator.public_key,
        validator_index=validator.validator_index,
        exit_signature=validator.exit_signature,
    )


def _reconstruct_deposit_signature(validator: 'Validator') -> None:
    """Reconstructs the full deposit signature once the share threshold is reached."""
    if (
        validator.deposit_signature is not None
        or len(validator.deposit_signature_shares) < settings.signature_threshold
    ):
        return

    try:
        deposit_signature = reconstruct_shared_bls_signature(validator.deposit_signature_shares)
        is_valid = validate_deposit_signature(
            validator.public_key,
            Web3.to_bytes(hexstr=validator.withdrawal_credentials),
            validator.amount,
            deposit_signature,
        )
    except Exception as e:
        validator.deposit_signature_shares.clear()
        raise HTTPException(
            status_code=400,
            detail=f'failed to reconstruct deposit signature for public_key={validator.public_key}',
        ) from e
    if not is_valid:
        validator.deposit_signature_shares.clear()
        raise HTTPException(
            status_code=400,
            detail=f'invalid deposit signature for public_key={validator.public_key}',
        )

    validator.deposit_signature = deposit_signature
