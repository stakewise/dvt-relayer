import logging
from typing import cast

from eth_typing import BlockNumber
from sw_utils import build_protocol_config

from src.app_state import AppState
from src.common.checks import wait_execution_catch_up_consensus
from src.common.clients import execution_client, ipfs_fetch_client
from src.common.consensus import get_chain_finalized_head
from src.common.contracts import keeper_contract
from src.common.tasks import BaseTask
from src.common.typings import OraclesCache
from src.config import settings

logger = logging.getLogger(__name__)


class ProtocolConfigTask(BaseTask):
    async def process_block(self) -> None:
        chain_state = await get_chain_finalized_head()
        await wait_execution_catch_up_consensus(chain_state=chain_state)
        await update_protocol_config()


async def update_protocol_config() -> None:
    """
    Fetches latest oracle config from IPFS. Uses cache if possible.
    """
    app_state = AppState()
    oracles_cache = app_state.oracles_cache

    # Find the latest block for which oracle config is cached
    if oracles_cache:
        from_block = BlockNumber(oracles_cache.checkpoint_block + 1)
    else:
        from_block = settings.network_config.KEEPER_GENESIS_BLOCK

    to_block = await execution_client.eth.get_block_number()

    if from_block > to_block:
        return

    logger.debug('update_oracles_cache: get logs from block %s to block %s', from_block, to_block)
    event = await keeper_contract.get_config_updated_event(from_block=from_block, to_block=to_block)
    if event:
        ipfs_hash = event['args']['configIpfsHash']
        config = cast(dict, await ipfs_fetch_client.fetch_json(ipfs_hash))
    else:
        config = oracles_cache.config  # type: ignore

    app_state.oracles_cache = OraclesCache(
        config=config,
        checkpoint_block=to_block,
    )

    app_state.protocol_config = build_protocol_config(config_data=app_state.oracles_cache.config)
