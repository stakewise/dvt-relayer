from eth_typing import HexStr
from sw_utils import ProtocolConfig

from src.common.typings import OraclesCache, Singleton
from src.validators.typings import ExitSignatureShareRow, PendingValidator


class AppState(metaclass=Singleton):
    oracles_cache: OraclesCache | None = None
    protocol_config: ProtocolConfig
    pending_validators: dict[HexStr, PendingValidator]
    exit_signature_shares: list[ExitSignatureShareRow]

    def get_exit_signature_shares(self, public_key: HexStr) -> list[ExitSignatureShareRow]:
        return [s for s in self.exit_signature_shares if s.public_key == public_key]
