from eth_typing import ChecksumAddress, HexStr
from pydantic import BaseModel
from web3.types import Gwei

from src.relayer.typings import ValidatorType


class ValidatorsRegisterRequest(BaseModel):
    vault: ChecksumAddress
    validators_start_index: int
    amounts: list[Gwei]
    validator_type: ValidatorType


class ValidatorsRegisterResponseItem(BaseModel):
    public_key: HexStr
    deposit_signature: HexStr
    amount: Gwei
    exit_signature: HexStr


class ValidatorsRegisterResponse(BaseModel):
    validators: list[ValidatorsRegisterResponseItem]
    validators_manager_signature: HexStr


class ValidatorsFundRequest(BaseModel):
    vault: ChecksumAddress
    public_keys: list[HexStr]
    amounts: list[Gwei]


class ValidatorsWithdrawalRequest(BaseModel):
    vault: ChecksumAddress
    public_keys: list[HexStr]
    amounts: list[Gwei]


class ValidatorsConsolidationRequest(BaseModel):
    vault: ChecksumAddress
    source_public_keys: list[HexStr]
    target_public_keys: list[HexStr]


class ValidatorsSignatureResponse(BaseModel):
    validators_manager_signature: HexStr
