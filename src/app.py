import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.common.setup_logging import setup_logging, setup_sentry
from src.config import settings
from src.validators.database import NetworkValidatorCrud
from src.validators.endpoints import router
from src.validators.tasks import NetworkValidatorsTask, load_genesis_validators
from src.validators.typings import AppState
from src.validators.utils import load_deposit_data

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator:  # pylint:disable=unused-argument
    deposit_data = load_deposit_data(Path(settings.deposit_data_path))
    app_state = AppState()
    app_state.deposit_data = deposit_data

    app_state.pending_validators = []
    app_state.exit_signature_shares = []
    app_state.exit_signatures = []

    NetworkValidatorCrud().setup()
    await load_genesis_validators()

    # Creates a strong reference to the task. Helps to avoid garbage collecting.
    network_validators_task = asyncio.create_task(NetworkValidatorsTask().run())

    yield

    network_validators_task.cancel()


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
