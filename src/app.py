from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.common.setup_logging import setup_logging, setup_sentry
from src.config import settings
from src.validators.endpoints import router
from src.validators.typings import AppState
from src.validators.utils import load_deposit_data, load_validators_manager_account
import logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator:  # pylint:disable=unused-argument
    validators = load_deposit_data(Path(settings.deposit_data_path))
    app_state = AppState()
    app_state.validators = validators

    validators_manager = load_validators_manager_account()
    app_state.validators_manager_account = validators_manager
    logger.info('validators manager address: %s', validators_manager.address)

    app_state.pending_validators = []
    app_state.exit_signature_shares = []
    app_state.exit_signatures = []
    yield


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
