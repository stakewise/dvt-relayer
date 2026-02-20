import logging
from time import time

from eth_typing import BlockNumber
from sw_utils import EventScanner

from src.app_state import AppState
from src.common.checks import wait_execution_catch_up_consensus
from src.common.consensus import get_chain_finalized_head
from src.common.tasks import BaseTask
from src.config import settings
from src.validators.execution import NetworkValidatorsProcessor

logger = logging.getLogger(__name__)


class NetworkValidatorsTask(BaseTask):
    def __init__(self, from_block: BlockNumber) -> None:
        network_validators_processor = NetworkValidatorsProcessor(from_block)
        self.network_validators_scanner = EventScanner(network_validators_processor)

    async def process_block(self) -> None:
        chain_state = await get_chain_finalized_head()
        await wait_execution_catch_up_consensus(chain_state=chain_state)

        # process new network validators
        await self.network_validators_scanner.process_new_events(chain_state.block_number)


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
