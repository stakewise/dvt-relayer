from eth_typing import ChecksumAddress, HexStr
from pydantic import BaseModel
from web3.types import Gwei

from src.relayer.typings import ValidatorType
from src.validators.typings import (
    OraclesExitSignatureShares as OraclesExitSignatureSharesDataclass,
)


class ValidatorsRegisterRequest(BaseModel):
    vault: ChecksumAddress
    validators_start_index: int
    amounts: list[Gwei]
    validator_type: ValidatorType


class OraclesExitSignatureShares(BaseModel):
    public_keys: list[HexStr]
    encrypted_exit_signatures: list[HexStr]

    @staticmethod
    def from_dataclass(
        d: OraclesExitSignatureSharesDataclass,
    ) -> 'OraclesExitSignatureShares':
        return OraclesExitSignatureShares(
            public_keys=d.public_keys,
            encrypted_exit_signatures=d.encrypted_exit_signatures,
        )


class ValidatorsRegisterResponseItem(BaseModel):
    public_key: HexStr
    amount: Gwei
    deposit_signature: HexStr | None = None
    exit_signature: HexStr | None = None
    oracles_exit_signature_shares: OraclesExitSignatureShares | None = None


class ValidatorsRegisterResponse(BaseModel):
    validators: list[ValidatorsRegisterResponseItem]
    validators_manager_signature: HexStr | None = None


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
