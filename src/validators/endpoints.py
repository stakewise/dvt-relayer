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

        # Save exit signature share if not already saved
        if not validator.exit_signature_shares.get(request.share_index):
            validator.exit_signature_shares[request.share_index] = BLSSignature(
                Web3.to_bytes(hexstr=share.exit_signature)
            )
        # Save deposit signature share if not already saved
        if not validator.deposit_signature_shares.get(request.share_index):
            validator.deposit_signature_shares[request.share_index] = BLSSignature(
                Web3.to_bytes(hexstr=share.deposit_signature)
            )

        # Handle exit signature shares
        if (
            validator.exit_signature is None
            and len(validator.exit_signature_shares) >= settings.signature_threshold
        ):
            # Reconstruct and validate exit signature
            exit_signature = reconstruct_shared_bls_signature(validator.exit_signature_shares)
            if not validate_exit_signature(
                validator.public_key, validator.validator_index, exit_signature
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f'invalid exit signature for public_key={share.public_key},'
                        f' share_index={request.share_index}'
                    ),
                )

            validator.exit_signature = exit_signature

            # Split exit signature into shares for oracles
            oracles_shares = await get_oracles_exit_signature_shares(
                public_key=validator.public_key,
                validator_index=validator.validator_index,
                exit_signature=validator.exit_signature,
            )
            validator.oracles_exit_signature_shares = oracles_shares

        # Handle deposit signature shares
        if (
            validator.deposit_signature is None
            and len(validator.deposit_signature_shares) >= settings.signature_threshold
        ):
            # Reconstruct and validate deposit signature
            deposit_signature = reconstruct_shared_bls_signature(validator.deposit_signature_shares)
            if not validate_deposit_signature(
                validator.public_key,
                Web3.to_bytes(hexstr=validator.withdrawal_credentials),
                validator.amount,
                deposit_signature,
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f'invalid deposit signature for public_key={share.public_key},'
                        f' share_index={request.share_index}'
                    ),
                )

            validator.deposit_signature = deposit_signature

    return SignatureShareResponse()
