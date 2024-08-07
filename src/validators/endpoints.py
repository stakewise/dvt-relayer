from time import time

from eth_typing import BLSSignature, HexStr
from fastapi import APIRouter
from web3 import Web3

from src.app_state import AppState
from src.config import settings
from src.validators.execution import get_start_validator_index
from src.validators.key_shares import reconstruct_shared_bls_signature
from src.validators.oracle_shares import get_oracles_exit_signature_shares
from src.validators.schema import (
    CreateValidatorsResponse,
    CreateValidatorsResponseItem,
    ExitSignatureShareRequest,
    ExitSignatureShareResponse,
    ValidatorResponse,
    ValidatorsRequest,
    ValidatorsResponseItem,
)
from src.validators.typings import Validator

router = APIRouter()


@router.post('/validators')
async def create_validators(
    request: ValidatorsRequest,
) -> CreateValidatorsResponse:
    app_state = AppState()
    validator_items = []

    validator_index = None
    exit_signatures_ready = True
    now = int(time())

    for public_key in request.public_keys:
        validator = app_state.validators.get(public_key)
        if validator is None:
            if validator_index is None:
                validator_index = await get_start_validator_index()

            validator = Validator(
                public_key=public_key,
                validator_index=validator_index,
                created_at=now,
            )
            app_state.validators[public_key] = validator
            validator_index += 1

        if validator.exit_signature is None:
            exit_signatures_ready = False

        validator_items.append(CreateValidatorsResponseItem.from_validator(validator))

    return CreateValidatorsResponse(
        ready=exit_signatures_ready,
        validators=validator_items,
    )


@router.get('/validators')
async def get_validators() -> ValidatorResponse:
    app_state = AppState()
    response = ValidatorResponse(validators=[])

    for pv in app_state.validators.values():
        response.validators.append(
            ValidatorsResponseItem(public_key=pv.public_key, validator_index=pv.validator_index)
        )
    return response


@router.post('/exit-signature')
async def create_exit_signature_share(
    request: ExitSignatureShareRequest,
) -> ExitSignatureShareResponse:
    app_state = AppState()
    validator = app_state.validators.get(request.public_key)
    if validator is None:
        return ExitSignatureShareResponse()

    current_share = validator.exit_signature_shares.get(request.share_index)
    if current_share:
        return ExitSignatureShareResponse()

    validator.exit_signature_shares[request.share_index] = BLSSignature(
        Web3.to_bytes(hexstr=HexStr(request.signature))
    )

    if len(validator.exit_signature_shares) < settings.signature_threshold:
        return ExitSignatureShareResponse()

    validator.exit_signature = reconstruct_shared_bls_signature(validator.exit_signature_shares)
    oracles_shares = await get_oracles_exit_signature_shares(
        public_key=validator.public_key,
        validator_index=validator.validator_index,
        exit_signature=validator.exit_signature,
    )
    validator.oracles_exit_signature_shares = oracles_shares

    return ExitSignatureShareResponse()
