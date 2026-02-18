from dataclasses import dataclass

from eth_typing import HexStr


@dataclass
class OraclesExitSignatureShares:
    public_keys: list[HexStr]
    encrypted_exit_signatures: list[HexStr]
