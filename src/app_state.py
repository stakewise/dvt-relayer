from eth_typing import HexStr
from sw_utils import ProtocolConfig

from src.common.typings import OraclesCache, Singleton
from src.validators.typings import Validator


class AppState(metaclass=Singleton):
    oracles_cache: OraclesCache | None = None
    protocol_config: ProtocolConfig
    validators: dict[HexStr, Validator]
