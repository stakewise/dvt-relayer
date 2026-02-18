from fastapi import APIRouter
from sw_utils import DepositData, get_v2_withdrawal_credentials
from web3 import Web3

from src.common.contracts import VaultContract, validators_registry_contract
from src.relayer import schema
from src.relayer.typings import Validator
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
    validator_items = []
    validators: list[Validator] = []

    for validator in validators:
        validator_items.append(
            schema.ValidatorsRegisterResponseItem(
                public_key=validator.public_key,
                deposit_signature=validator.deposit_signature,
                amount=validator.amount,
                exit_signature=Web3.to_hex(validator.exit_signature),
            )
        )

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
        deposit_data = DepositData(
            pubkey=Web3.to_bytes(hexstr=public_key),
            withdrawal_credentials=get_v2_withdrawal_credentials(request.vault),
            amount=amount,
            signature=empty_signature,
        )
        validator = Validator(
            public_key=public_key,
            amount=amount,
            deposit_signature=Web3.to_hex(empty_signature),
            deposit_data_root=Web3.to_hex(deposit_data.hash_tree_root),
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
