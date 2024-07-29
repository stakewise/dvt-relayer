from eth_typing import HexStr
from pydantic import BaseModel


class ExitSignatureShareRequest(BaseModel):
    public_key: HexStr
    share_index: int
    signature: HexStr


class ExitSignatureShareResponse(BaseModel):
    ...


class ValidatorsRequest(BaseModel):
    public_keys: list[HexStr]


class ValidatorsResponseItem(BaseModel):
    public_key: HexStr
    exit_signature: HexStr | None


class ValidatorsResponse(BaseModel):
    ready: bool
    validators: list[ValidatorsResponseItem]


class PendingValidatorResponseItem(BaseModel):
    public_key: HexStr
    validator_index: int


class PendingValidatorResponse(BaseModel):
    pending_validators: list[PendingValidatorResponseItem]
