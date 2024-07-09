import asyncio

from eth_typing import BLSSignature, HexStr
from fastapi import APIRouter, HTTPException
from web3 import Web3

from src.config import settings
from src.validators.database import NetworkValidatorCrud
from src.validators.key_shares import reconstruct_shared_bls_signature
from src.validators.proof import _calc_leaf_indexes, get_validators_proof
from src.validators.schema import (
    ExitSignatureShareRequest,
    ExitSignatureShareResponse,
    PendingValidatorResponse,
    PendingValidatorResponseItem,
    ValidatorsRequest,
    ValidatorsResponse,
    ValidatorsResponseItem,
)
from src.validators.typings import (
    AppState,
    ExitSignatureRow,
    ExitSignatureShareRow,
    PendingValidator,
    Validator,
)

router = APIRouter()


@router.post('/validators')
async def create_validators_and_wait_for_signatures(
    request: ValidatorsRequest,
) -> ValidatorsResponse:
    app_state = AppState()
    validator_items = []

    validators = _get_available_validators(request.validators_count)
    if not validators:
        raise HTTPException(status_code=400, detail='no available validators')

    app_state.pending_validators = []
    for validator_index, validator in enumerate(validators, request.validator_index):
        app_state.pending_validators.append(
            PendingValidator(public_key=validator.public_key, validator_index=validator_index)
        )

    for validator in validators:
        while (exit_signature := app_state.get_exit_signature(validator.public_key)) is None:
            await asyncio.sleep(1)

        validator_items.append(
            ValidatorsResponseItem(
                public_key=validator.public_key,
                deposit_signature=validator.deposit_signature,
                amount_gwei=validator.amount_gwei,
                exit_signature=Web3.to_hex(exit_signature),
            )
        )

    app_state.pending_validators = []

    multi_proof = get_validators_proof(app_state.deposit_data.tree, validators)
    deposit_data_indexes = [leaf[1] for leaf in multi_proof.leaves]
    leaf_indexes = _calc_leaf_indexes(deposit_data_indexes)

    return ValidatorsResponse(
        validators=validator_items,
        proof=multi_proof.proof,
        proof_flags=multi_proof.proof_flags,
        proof_indexes=leaf_indexes,
    )


def _get_available_validators(validators_count: int) -> list[Validator]:
    res = []
    app_state = AppState()
    for validator in app_state.deposit_data.validators:
        if NetworkValidatorCrud().is_validator_registered(validator.public_key):
            continue
        res.append(validator)
        if len(res) == validators_count:
            break
    return res


@router.get('/validators')
async def get_pending_validators() -> PendingValidatorResponse:
    app_state = AppState()
    response = PendingValidatorResponse(pending_validators=[])

    for pv in app_state.pending_validators:
        response.pending_validators.append(
            PendingValidatorResponseItem(
                public_key=pv.public_key, validator_index=pv.validator_index
            )
        )
    return response


@router.post('/exit-signature')
async def create_exit_signature_share(
    request: ExitSignatureShareRequest,
) -> ExitSignatureShareResponse:
    app_state = AppState()
    validator = app_state.get_validator(request.public_key)
    if validator is None:
        raise HTTPException(status_code=400)

    current_share = app_state.get_exit_signature_share(request.public_key, request.share_index)
    if current_share:
        return ExitSignatureShareResponse()

    app_state.exit_signature_shares.append(
        ExitSignatureShareRow(
            public_key=request.public_key,
            share_index=request.share_index,
            signature=BLSSignature(Web3.to_bytes(hexstr=HexStr(request.signature))),
        )
    )

    signature_shares = app_state.get_exit_signature_shares(request.public_key)
    if len(signature_shares) < settings.signature_threshold:
        return ExitSignatureShareResponse()

    signature = reconstruct_shared_bls_signature(
        {s.share_index: s.signature for s in signature_shares}
    )

    if signature is not None:
        app_state.exit_signatures.append(
            ExitSignatureRow(public_key=request.public_key, signature=signature)
        )
        app_state.remove_pending_validator(request.public_key)

    return ExitSignatureShareResponse()
