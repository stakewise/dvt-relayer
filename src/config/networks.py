from dataclasses import dataclass

from eth_typing import ChecksumAddress, HexStr
from web3 import Web3

MAINNET = 'mainnet'
GNOSIS = 'gnosis'
HOLESKY = 'holesky'
CHIADO = 'chiado'

GNO_NETWORKS = [GNOSIS, CHIADO]


@dataclass
class NetworkConfig:
    CHAIN_ID: int
    VALIDATORS_REGISTRY_CONTRACT_ADDRESS: ChecksumAddress
    SECONDS_PER_BLOCK: int
    GENESIS_VALIDATORS_IPFS_HASH: str
    GENESIS_FORK_VERSION: bytes
    SLOTS_PER_EPOCH: int


NETWORKS = {
    MAINNET: NetworkConfig(
        CHAIN_ID=1,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x00000000219ab540356cBB839Cbe05303d7705Fa'
        ),
        SECONDS_PER_BLOCK=12,
        GENESIS_VALIDATORS_IPFS_HASH='bafybeigzq2ntq5zw4tdym5vckbf66mla5q3ge2fzdgqslhckdytlmm7k7y',
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00000000')),
        SLOTS_PER_EPOCH=32,
    ),
    HOLESKY: NetworkConfig(
        CHAIN_ID=17000,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x4242424242424242424242424242424242424242'
        ),
        SECONDS_PER_BLOCK=12,
        GENESIS_VALIDATORS_IPFS_HASH='bafybeihhaxvlkbvwda6jy3ucawb4cdmgbaumbvoi337gdyp6hdtlrfnb64',
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x01017000')),
        SLOTS_PER_EPOCH=32,
    ),
    GNOSIS: NetworkConfig(
        CHAIN_ID=100,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x0B98057eA310F4d31F2a452B414647007d1645d9'
        ),
        SECONDS_PER_BLOCK=5,
        GENESIS_VALIDATORS_IPFS_HASH='bafybeid4xnpjblh4izjb32qygdubyugotivm5rscx6b3jpsez4vxlyig44',
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00000064')),
        SLOTS_PER_EPOCH=16,
    ),
    CHIADO: NetworkConfig(
        CHAIN_ID=10200,
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xb97036A26259B7147018913bD58a774cf91acf25'
        ),
        SECONDS_PER_BLOCK=5,
        GENESIS_VALIDATORS_IPFS_HASH='bafybeih2he7opyg4e7ontq4cvh42tou4ekizpbn4emg6u5lhfziyxcm3zq',
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x0000006f')),
        SLOTS_PER_EPOCH=16,
    ),
}
