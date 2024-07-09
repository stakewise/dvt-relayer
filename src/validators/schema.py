from eth_typing import ChecksumAddress, HexStr
from pydantic import BaseModel


class ExitSignatureShareRequest(BaseModel):
    public_key: HexStr
    share_index: int
    signature: HexStr


class ExitSignatureShareResponse(BaseModel):
    ...


class ValidatorsRequest(BaseModel):
    vault: ChecksumAddress
    validator_index: int
    validators_count: int


class ValidatorsResponseItem(BaseModel):
    public_key: HexStr
    deposit_signature: HexStr
    amount_gwei: int
    exit_signature: HexStr


class ValidatorsResponse(BaseModel):
    validators: list[ValidatorsResponseItem]
    proof: list[HexStr]
    proof_flags: list[bool]
    proof_indexes: list[int]


class PendingValidatorResponseItem(BaseModel):
    public_key: HexStr
    validator_index: int


class PendingValidatorResponse(BaseModel):
    pending_validators: list[PendingValidatorResponseItem]
