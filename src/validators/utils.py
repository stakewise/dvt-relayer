from eth_typing import HexStr
from web3 import Web3


def to_hex_or_none(v: bytes | None) -> HexStr | None:
    if v is None:
        return None
    return Web3.to_hex(v)
