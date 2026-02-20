from eth_account.signers.local import LocalAccount
from eth_typing import BlockNumber, HexStr
from sw_utils import ProtocolConfig

from src.common.typings import OraclesCache, Singleton
from src.relayer.typings import Validator


class AppState(metaclass=Singleton):
    oracles_cache: OraclesCache | None = None
    protocol_config: ProtocolConfig

    # Last block number processed by NetworkValidatorsTask
    network_validators_block: BlockNumber

    validators: dict[HexStr, Validator]
    validators_manager_account: LocalAccount
