from dataclasses import dataclass

from eth_typing import HexStr
from pydantic import BaseModel

from src.common.typings import Singleton


@dataclass
class Validator:
    public_key: HexStr
    signature: HexStr
    amount_gwei: int
    deposit_data_index: int


class ValidatorsRequest(BaseModel):
    start_index: int
    validators_count: int


class AppState(metaclass=Singleton):
    validators: list[Validator]
