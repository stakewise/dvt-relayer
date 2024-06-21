from dataclasses import dataclass

from eth_typing import ChecksumAddress
from web3 import Web3

MAINNET = 'mainnet'
GNOSIS = 'gnosis'
HOLESKY = 'holesky'
CHIADO = 'chiado'

GNO_NETWORKS = [GNOSIS, CHIADO]
RATED_NETWORKS = [MAINNET, HOLESKY]


@dataclass
# pylint: disable=invalid-name
class NetworkConfig:
    CHAIN_ID: int
    VALIDATORS_REGISTRY_CONTRACT_ADDRESS: ChecksumAddress


NETWORKS = {
    MAINNET: NetworkConfig(
        CHAIN_ID=1,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x00000000219ab540356cBB839Cbe05303d7705Fa'
        ),
    ),
    HOLESKY: NetworkConfig(
        CHAIN_ID=17000,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x4242424242424242424242424242424242424242'
        ),
    ),
    GNOSIS: NetworkConfig(
        CHAIN_ID=100,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x0B98057eA310F4d31F2a452B414647007d1645d9'
        ),
    ),
    CHIADO: NetworkConfig(
        CHAIN_ID=10200,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xb97036A26259B7147018913bD58a774cf91acf25'
        ),
    ),
}
