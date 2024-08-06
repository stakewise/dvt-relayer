from dataclasses import dataclass

from eth_typing import BlockNumber, ChecksumAddress, HexStr
from sw_utils import ConsensusFork
from sw_utils.typings import Bytes32
from web3 import Web3

MAINNET = 'mainnet'
GNOSIS = 'gnosis'
HOLESKY = 'holesky'
CHIADO = 'chiado'

GNO_NETWORKS = [GNOSIS, CHIADO]


# pylint: disable=too-many-instance-attributes
@dataclass
class NetworkConfig:
    CHAIN_ID: int
    VALIDATORS_REGISTRY_CONTRACT_ADDRESS: ChecksumAddress
    SECONDS_PER_BLOCK: int
    GENESIS_VALIDATORS_IPFS_HASH: str
    GENESIS_FORK_VERSION: bytes
    SLOTS_PER_EPOCH: int
    SHAPELLA_FORK_VERSION: bytes
    SHAPELLA_EPOCH: int
    GENESIS_VALIDATORS_ROOT: Bytes32
    KEEPER_CONTRACT_ADDRESS: ChecksumAddress
    KEEPER_GENESIS_BLOCK: BlockNumber

    @property
    def SHAPELLA_FORK(self) -> ConsensusFork:
        return ConsensusFork(
            version=self.SHAPELLA_FORK_VERSION,
            epoch=self.SHAPELLA_EPOCH,
        )


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
        SHAPELLA_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x03000000')),
        SHAPELLA_EPOCH=194048,
        GENESIS_VALIDATORS_ROOT=Bytes32(
            Web3.to_bytes(
                hexstr=HexStr('0x4b363db94e286120d76eb905340fdd4e54bfe9f06bf33ff6cf5ad27f511bfe95')
            )
        ),
        KEEPER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x6B5815467da09DaA7DC83Db21c9239d98Bb487b5'
        ),
        KEEPER_GENESIS_BLOCK=BlockNumber(18470089),
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
        SHAPELLA_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x04017000')),
        SHAPELLA_EPOCH=256,
        GENESIS_VALIDATORS_ROOT=Bytes32(
            Web3.to_bytes(
                hexstr=HexStr('0x9143aa7c615a7f7115e2b6aac319c03529df8242ae705fba9df39b79c59fa8b1')
            )
        ),
        KEEPER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xB580799Bf7d62721D1a523f0FDF2f5Ed7BA4e259'
        ),
        KEEPER_GENESIS_BLOCK=BlockNumber(215379),
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
        SHAPELLA_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x03000064')),
        SHAPELLA_EPOCH=648704,
        GENESIS_VALIDATORS_ROOT=Bytes32(
            Web3.to_bytes(
                hexstr=HexStr('0xf5dcb5564e829aab27264b9becd5dfaa017085611224cb3036f573368dbb9d47')
            )
        ),
        KEEPER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xcAC0e3E35d3BA271cd2aaBE688ac9DB1898C26aa'
        ),
        KEEPER_GENESIS_BLOCK=BlockNumber(34778552),
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
        SHAPELLA_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x0300006f')),
        SHAPELLA_EPOCH=244224,
        GENESIS_VALIDATORS_ROOT=Bytes32(
            Web3.to_bytes(
                hexstr=HexStr('0x9d642dac73058fbf39c0ae41ab1e34e4d889043cb199851ded7095bc99eb4c1e')
            )
        ),
        KEEPER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x5f31eD13eBF81B67a9f9498F3d1D2Da553058988'
        ),
        KEEPER_GENESIS_BLOCK=BlockNumber(10627588),
    ),
}
