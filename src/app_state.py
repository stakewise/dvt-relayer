from eth_account.signers.local import LocalAccount
from eth_typing import HexStr
from sw_utils import ProtocolConfig

from src.common.typings import OraclesCache, Singleton
from src.relayer.typings import Validator


class AppState(metaclass=Singleton):
    oracles_cache: OraclesCache | None = None
    protocol_config: ProtocolConfig
    validators: dict[HexStr, Validator]
    validators_manager_account: LocalAccount
