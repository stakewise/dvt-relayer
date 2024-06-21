import asyncio
import logging
from pathlib import Path

import aiohttp
from aiohttp import ClientTimeout
from eth_typing import BLSPubkey, BLSSignature, HexStr
from sw_utils import ConsensusFork
from sw_utils.typings import Bytes32
from web3 import Web3

from src.common.setup_logging import setup_logging
from src.config import settings
from src.validators.tests.key_shares import reconstruct_shared_bls_public_key
from src.validators.tests.keystores.local import LocalKeystore
from src.validators.typings import Validator
from src.validators.utils import load_deposit_data

setup_logging()

logger = logging.getLogger(__name__)
relayer_base_url = f'http://{settings.relayer_host}:{settings.relayer_port}'


async def run_dvt_nodes():
    first_public_key_shares = {}
    keystores = {}
    deposit_data = load_deposit_data(Path(settings.deposit_data_path))

    for node_index in range(4):
        logger.info('load_keystore %s', node_index)
        keystore = await load_keystore(node_index)
        keystores[node_index] = keystore
        logger.info('loaded keystore %s', node_index)

        logger.info('node_index %s, public_keys %s', node_index, keystore.public_keys)
        first_public_key_shares[node_index] = keystore.public_keys[0]

    check_reconstruct_public_key(deposit_data, first_public_key_shares)

    for node_index, keystore in keystores.items():
        asyncio.create_task(poll_validators_and_push_signatures(deposit_data, keystore, node_index))

    # Keep tasks running
    while True:
        await asyncio.sleep(0.1)


def check_reconstruct_public_key(
    deposit_data: list[Validator], public_key_shares: dict[int, HexStr]
) -> None:
    """
    Check share indexes assigned properly
    """
    share_index_to_pubkey_share = {}
    for node_index, pubkey in public_key_shares.items():
        share_index = node_index + 1
        share_index_to_pubkey_share[share_index] = BLSPubkey(Web3.to_bytes(hexstr=pubkey))

    pubkey = reconstruct_shared_bls_public_key(share_index_to_pubkey_share)
    assert deposit_data[0].public_key == Web3.to_hex(pubkey)


async def load_keystore(node_index: int) -> LocalKeystore:
    dir_path = f'obol-cluster-{settings.network.lower()}/node{node_index}/validator_keys'
    return await LocalKeystore.load(Path(dir_path))


async def poll_validators_and_push_signatures(
    deposit_data: list[Validator], keystore: LocalKeystore, node_index: int
):
    pushed_public_keys = set()
    pub_key_to_share = {
        validator.public_key: pub_key_share
        for pub_key_share, validator in zip(keystore.public_keys, deposit_data)
    }

    async with aiohttp.ClientSession(timeout=ClientTimeout(5)) as session:
        while True:
            try:
                pending_validators = await poll_pending_validators(session)
                for pv in pending_validators:
                    if pv['public_key'] in pushed_public_keys:
                        continue
                    pub_key_share = pub_key_to_share[pv['public_key']]
                    exit_signature = await get_exit_signature(
                        keystore, pv['validator_index'], pub_key_share
                    )
                    await push_signature(session, pv['public_key'], exit_signature, node_index)
                    pushed_public_keys.add(pv['public_key'])
            except Exception as e:
                logger.exception('')
                logger.error(repr(e))
            await asyncio.sleep(1)


async def poll_pending_validators(session):
    while True:
        res = await session.get(f'{relayer_base_url}/validators')
        res.raise_for_status()
        jsn = await res.json()
        if pending_validators := jsn['pending_validators']:
            return pending_validators
        await asyncio.sleep(1)


async def get_exit_signature(
    keystore: LocalKeystore, validator_index: int, public_key: HexStr
) -> BLSSignature:
    # holesky
    SHAPELLA_FORK_VERSION = Web3.to_bytes(hexstr=HexStr('0x04017000'))
    SHAPELLA_EPOCH = 256
    genesis_validators_root = Bytes32(
        Web3.to_bytes(
            hexstr=HexStr('0x9143aa7c615a7f7115e2b6aac319c03529df8242ae705fba9df39b79c59fa8b1')
        )
    )

    fork = ConsensusFork(
        version=SHAPELLA_FORK_VERSION,
        epoch=SHAPELLA_EPOCH,
    )

    return await keystore.get_exit_signature(
        validator_index, public_key, fork, genesis_validators_root
    )


async def push_signature(
    session: aiohttp.ClientSession,
    public_key: HexStr,
    exit_signature: BLSSignature,
    node_index: int,
):
    share_index = node_index + 1
    jsn = {
        'public_key': public_key,
        'share_index': share_index,
        'signature': Web3.to_hex(exit_signature),
    }
    logger.info('push exit signature for share_index %s', share_index)
    res = await session.post(f'{relayer_base_url}/exit-signature', json=jsn)
    res.raise_for_status()


if __name__ == '__main__':
    logger.info('network %s', settings.network)
    asyncio.run(run_dvt_nodes())
