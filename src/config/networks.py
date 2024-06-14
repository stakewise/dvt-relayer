from dataclasses import dataclass

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.constants import ADDRESS_ZERO

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
    VALIDATORS_CHECKER_CONTRACT_ADDRESS: ChecksumAddress


NETWORKS = {
    MAINNET: NetworkConfig(
        CHAIN_ID=1,
        VALIDATORS_CHECKER_CONTRACT_ADDRESS=Web3.to_checksum_address(ADDRESS_ZERO),
    ),
    HOLESKY: NetworkConfig(
        CHAIN_ID=17000,
        VALIDATORS_CHECKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x23FCd08f2e85f765d329027AB6D4323a0BC057A7'
        ),
    ),
    GNOSIS: NetworkConfig(
        CHAIN_ID=100,
        VALIDATORS_CHECKER_CONTRACT_ADDRESS=Web3.to_checksum_address(ADDRESS_ZERO),
    ),
    CHIADO: NetworkConfig(
        CHAIN_ID=10200,
        VALIDATORS_CHECKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x5Fa9600FF682FA65Fff6085df06CCBB7dC01DF08'
        ),
    ),
}
