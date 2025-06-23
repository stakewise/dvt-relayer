import logging
from time import time

from eth_typing import BlockNumber
from sw_utils import EventScanner, IpfsFetchClient
from web3 import Web3

from src.app_state import AppState
from src.common.checks import wait_execution_catch_up_consensus
from src.common.consensus import get_chain_finalized_head
from src.common.tasks import BaseTask
from src.config import settings
from src.validators.database import NetworkValidatorCrud
from src.validators.execution import NetworkValidatorsProcessor
from src.validators.typings import NetworkValidator

logger = logging.getLogger(__name__)


class NetworkValidatorsTask(BaseTask):
    def __init__(self) -> None:
        network_validators_processor = NetworkValidatorsProcessor()
        self.network_validators_scanner = EventScanner(network_validators_processor)

    async def process_block(self) -> None:
        chain_state = await get_chain_finalized_head()
        await wait_execution_catch_up_consensus(chain_state=chain_state)

        # process new network validators
        await self.network_validators_scanner.process_new_events(chain_state.block_number)


async def load_genesis_validators() -> None:
    """
    Load consensus network validators from the ipfs dump.
    Used to speed up service startup
    """
    ipfs_hash = settings.network_config.GENESIS_VALIDATORS_IPFS_HASH
    if not (NetworkValidatorCrud().get_last_network_validator() is None and ipfs_hash):
        return

    ipfs_fetch_client = IpfsFetchClient(
        ipfs_endpoints=settings.ipfs_fetch_endpoints,
        timeout=settings.genesis_validators_ipfs_timeout,
        retry_timeout=settings.genesis_validators_ipfs_retry_timeout,
    )
    logger.info('Fetching genesis validators...')
    data = await ipfs_fetch_client.fetch_bytes(ipfs_hash)
    genesis_validators: list[NetworkValidator] = []
    logger.info('Loading genesis validators...')
    for i in range(0, len(data), 52):
        genesis_validators.append(
            NetworkValidator(
                public_key=Web3.to_hex(data[i + 4 : i + 52]),
                block_number=BlockNumber(int.from_bytes(data[i : i + 4], 'big')),
            )
        )

    NetworkValidatorCrud().save_network_validators(genesis_validators)
    logger.info('Loaded %d genesis validators', len(genesis_validators))


class CleanupValidatorsTask(BaseTask):
    async def process_block(self) -> None:
        app_state = AppState()
        public_keys = []
        now = int(time())
        for public_key, validator in app_state.validators.items():
            if now - validator.created_at > settings.VALIDATOR_LIFETIME:
                public_keys.append(public_key)

        for public_key in public_keys:
            logger.info('Cleanup validator %s', public_key)
            del app_state.validators[public_key]
