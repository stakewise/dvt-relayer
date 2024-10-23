import asyncio
import logging
from contextlib import asynccontextmanager
from time import time
from typing import AsyncIterator, Callable

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from src.app_state import AppState
from src.common.endpoints import router as common_router
from src.common.setup_logging import setup_logging, setup_sentry
from src.common.utils import get_project_version
from src.config import settings
from src.protocol_config.tasks import ProtocolConfigTask, update_protocol_config
from src.validators.database import NetworkValidatorCrud
from src.validators.endpoints import router as validators_router
from src.validators.tasks import (
    CleanupValidatorsTask,
    NetworkValidatorsTask,
    load_genesis_validators,
)

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator:
    del app_instance  # mute linters, unused argument error

    version = get_project_version()
    logger.info('Starting DVT Relayer service %s', version)

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
    cleanup_validators_task = asyncio.create_task(CleanupValidatorsTask().run())

    yield

    protocol_config_task.cancel()
    network_validators_task.cancel()
    cleanup_validators_task.cancel()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.middleware('http')
async def log_request_processing_time(request: Request, call_next: Callable) -> None:
    start = time()
    try:
        return await call_next(request)
    finally:
        elapsed = time() - start
        logger.info('Request processing time for path %s is %.1f', request.url.path, elapsed)


app.include_router(validators_router)
app.include_router(common_router)


setup_sentry()


if __name__ == '__main__':
    uvicorn.run(app, host=settings.relayer_host, port=settings.relayer_port)
