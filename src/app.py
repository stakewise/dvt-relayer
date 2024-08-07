import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.app_state import AppState
from src.common.setup_logging import setup_logging, setup_sentry
from src.config import settings
from src.protocol_config.tasks import ProtocolConfigTask, update_protocol_config
from src.validators.database import NetworkValidatorCrud
from src.validators.endpoints import router
from src.validators.tasks import NetworkValidatorsTask, load_genesis_validators

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator:  # pylint:disable=unused-argument
    app_state = AppState()

    app_state.validators = {}

    NetworkValidatorCrud().setup()
    await load_genesis_validators()

    logger.info('Fetching protocol config...')
    await update_protocol_config()
    logger.info('Protocol config is ready')

    # Note: we create a strong references to the tasks. Helps to avoid garbage collecting.
    protocol_config_task = asyncio.create_task(ProtocolConfigTask().run())
    network_validators_task = asyncio.create_task(NetworkValidatorsTask().run())

    yield

    network_validators_task.cancel()
    protocol_config_task.cancel()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)


setup_sentry()


if __name__ == '__main__':
    uvicorn.run(app, host=settings.relayer_host, port=settings.relayer_port)
