from eth_typing import BLSSignature, HexStr
from fastapi import APIRouter
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


@router.get('/exits')
async def get_exits() -> ValidatorsResponse:
    app_state = AppState()
    response = ValidatorsResponse(validators=[])

    for validator in app_state.validators.values():
        response.validators.append(ValidatorsResponseItem.from_validator(validator))
    return response


@router.post('/exit-signature')
async def create_exit_signature_shares(
    request: SignatureShareRequest,
) -> SignatureShareResponse:
    app_state = AppState()

    for share in request.shares:
        validator = app_state.validators.get(share.public_key)
        if validator is None:
            continue

        # Handle exit signature shares
        if not validator.exit_signature_shares.get(request.share_index):
            validator.exit_signature_shares[request.share_index] = BLSSignature(
                Web3.to_bytes(hexstr=HexStr(share.exit_signature))
            )

            if len(validator.exit_signature_shares) >= settings.signature_threshold:
                # Reconstruct and validate exit signature
                exit_signature = reconstruct_shared_bls_signature(validator.exit_signature_shares)
                if not validate_exit_signature(
                    validator.public_key, validator.validator_index, exit_signature
                ):
                    raise RuntimeError('invalid exit signature')

                validator.exit_signature = exit_signature

                # Split exit signature into shares for oracles
                oracles_shares = await get_oracles_exit_signature_shares(
                    public_key=validator.public_key,
                    validator_index=validator.validator_index,
                    exit_signature=validator.exit_signature,
                )
                validator.oracles_exit_signature_shares = oracles_shares

        # Handle deposit signature shares
        if not validator.deposit_signature_shares.get(request.share_index):
            validator.deposit_signature_shares[request.share_index] = HexStr(
                share.deposit_signature
            )

            if len(validator.deposit_signature_shares) >= settings.signature_threshold:
                # Reconstruct and validate deposit signature
                deposit_sig_shares = {
                    idx: BLSSignature(Web3.to_bytes(hexstr=sig))
                    for idx, sig in validator.deposit_signature_shares.items()
                }
                deposit_signature = reconstruct_shared_bls_signature(deposit_sig_shares)
                if not validate_deposit_signature(
                    validator.public_key,
                    Web3.to_bytes(hexstr=validator.withdrawal_credentials),
                    validator.amount,
                    deposit_signature,
                ):
                    raise RuntimeError('invalid deposit signature')

                validator.deposit_signature = Web3.to_hex(deposit_signature)

    return SignatureShareResponse()
