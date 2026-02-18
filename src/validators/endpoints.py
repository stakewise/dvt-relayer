from eth_typing import BLSSignature, HexStr
from fastapi import APIRouter
from web3 import Web3

from src.app_state import AppState
from src.config import settings
from src.validators.exit_signature import (
    get_oracles_exit_signature_shares,
    validate_exit_signature,
)
from src.validators.key_shares import reconstruct_shared_bls_signature
from src.validators.schema import (
    ExitSignatureShareRequest,
    ExitSignatureShareResponse,
    ExitsResponse,
    ExitsResponseItem,
)

router = APIRouter()


@router.get('/exits')
async def get_exits() -> ExitsResponse:
    app_state = AppState()
    response = ExitsResponse(exits=[])

    for validator in app_state.validators.values():
        response.exits.append(ExitsResponseItem.from_validator(validator))
    return response


@router.post('/exit-signature')
async def create_exit_signature_shares(
    request: ExitSignatureShareRequest,
) -> ExitSignatureShareResponse:
    app_state = AppState()

    for share in request.shares:
        validator = app_state.validators.get(share.public_key)
        if validator is None:
            continue

        current_share = validator.exit_signature_shares.get(request.share_index)
        if current_share:
            continue

        validator.exit_signature_shares[request.share_index] = BLSSignature(
            Web3.to_bytes(hexstr=HexStr(share.exit_signature))
        )

        if len(validator.exit_signature_shares) < settings.signature_threshold:
            continue

        exit_signature = reconstruct_shared_bls_signature(validator.exit_signature_shares)
        if not validate_exit_signature(
            validator.public_key, validator.validator_index, exit_signature
        ):
            raise RuntimeError('invalid exit signature')

        validator.exit_signature = exit_signature

        oracles_shares = await get_oracles_exit_signature_shares(
            public_key=validator.public_key,
            validator_index=validator.validator_index,
            exit_signature=validator.exit_signature,
        )
        validator.oracles_exit_signature_shares = oracles_shares

    return ExitSignatureShareResponse()
