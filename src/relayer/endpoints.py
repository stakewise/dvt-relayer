from time import time

from eth_typing import BLSSignature, HexStr
from fastapi import APIRouter
from web3 import Web3

from src.app_state import AppState
from src.common.contracts import VaultContract, validators_registry_contract
from src.relayer import schema
from src.relayer.public_keys import public_keys_manager
from src.relayer.typings import Validator, ValidatorType
from src.relayer.validators_manager import (
    get_validators_manager_signature_consolidation,
    get_validators_manager_signature_funding,
    get_validators_manager_signature_register,
    get_validators_manager_signature_withdrawal,
)

router = APIRouter()


@router.post('/register')
async def register_validators(
    request: schema.ValidatorsRegisterRequest,
) -> schema.ValidatorsRegisterResponse:
    app_state = AppState()
    validators: list[Validator] = []

    # Flag is True when all validators have deposit and exit signatures, False otherwise.
    is_signatures_ready_for_all_validators = True

    now = int(time())

    # Build validators list and check if signatures are ready for all validators
    for i, (public_key, amount) in enumerate(
        zip(await public_keys_manager.get_unregistered(), request.amounts)
    ):
        validator_index = request.validators_start_index + i
        validator = app_state.validators.get(public_key)

        if validator is None or validator.validator_index != validator_index:
            validator = Validator(
                public_key=public_key,
                vault=request.vault,
                validator_index=validator_index,
                created_at=now,
                amount=amount,
                validator_type=request.validator_type,
            )
            app_state.validators[public_key] = validator

        if validator.deposit_signature is None or validator.exit_signature is None:
            is_signatures_ready_for_all_validators = False

        validators.append(validator)

    # Build response
    validator_items: list[schema.ValidatorsRegisterResponseItem] = []

    for validator in validators:
        oracles_shares = validator.oracles_exit_signature_shares
        validator_items.append(
            schema.ValidatorsRegisterResponseItem(
                public_key=validator.public_key,
                amount=validator.amount,
                deposit_signature=(
                    Web3.to_hex(validator.deposit_signature)
                    if validator.deposit_signature is not None
                    else None
                ),
                exit_signature=(
                    Web3.to_hex(validator.exit_signature)
                    if validator.exit_signature is not None
                    else None
                ),
                oracles_exit_signature_shares=(
                    schema.OraclesExitSignatureShares.from_dataclass(oracles_shares)
                    if oracles_shares
                    else None
                ),
            )
        )

    # Compute validators manager signature
    validators_manager_signature: HexStr | None = None

    if is_signatures_ready_for_all_validators:
        validators_registry_root = await validators_registry_contract.get_registry_root()
        validators_manager_signature = get_validators_manager_signature_register(
            Web3.to_checksum_address(request.vault),
            Web3.to_hex(validators_registry_root),
            validators,
        )

    return schema.ValidatorsRegisterResponse(
        validators=validator_items,
        validators_manager_signature=validators_manager_signature,
    )


@router.post('/fund')
async def fund_validators(
    request: schema.ValidatorsFundRequest,
) -> schema.ValidatorsSignatureResponse:
    validators = []

    # use empty signature for funding
    empty_signature = bytes(96)
    for public_key, amount in zip(request.public_keys, request.amounts):
        validator = Validator(
            public_key=public_key,
            vault=Web3.to_checksum_address(request.vault),
            amount=amount,
            validator_type=ValidatorType.V2,
            validator_index=0,
            created_at=0,
            deposit_signature=BLSSignature(empty_signature),
        )
        validators.append(validator)

    vault_contact = VaultContract(request.vault)
    validators_manager_nonce = await vault_contact.validators_manager_nonce()
    validators_manager_signature = get_validators_manager_signature_funding(
        Web3.to_checksum_address(request.vault),
        validators_manager_nonce,
        validators,
    )

    return schema.ValidatorsSignatureResponse(
        validators_manager_signature=validators_manager_signature,
    )


@router.post('/withdraw')
async def withdraw_validators(
    request: schema.ValidatorsWithdrawalRequest,
) -> schema.ValidatorsSignatureResponse:
    vault_contact = VaultContract(request.vault)
    validators_manager_nonce = await vault_contact.validators_manager_nonce()
    validators_manager_signature = get_validators_manager_signature_withdrawal(
        Web3.to_checksum_address(request.vault),
        validators_manager_nonce,
        request.public_keys,
        request.amounts,
    )

    return schema.ValidatorsSignatureResponse(
        validators_manager_signature=validators_manager_signature,
    )


@router.post('/consolidate')
async def consolidate_validators(
    request: schema.ValidatorsConsolidationRequest,
) -> schema.ValidatorsSignatureResponse:
    vault_contact = VaultContract(request.vault)
    validators_manager_nonce = await vault_contact.validators_manager_nonce()
    validators_manager_signature = get_validators_manager_signature_consolidation(
        Web3.to_checksum_address(request.vault),
        validators_manager_nonce,
        request.source_public_keys,
        request.target_public_keys,
    )

    return schema.ValidatorsSignatureResponse(
        validators_manager_signature=validators_manager_signature,
    )
