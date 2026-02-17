import logging
from time import time

from src.app_state import AppState
from src.common.tasks import BaseTask
from src.config import settings

logger = logging.getLogger(__name__)


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
