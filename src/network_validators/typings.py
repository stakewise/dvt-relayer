from dataclasses import dataclass

from eth_typing import BlockNumber, HexStr


@dataclass
class NetworkValidator:
    public_key: HexStr
    block_number: BlockNumber
