from fastapi import APIRouter

from src.app_state import AppState
from src.common.schema import InfoResponse
from src.config import settings

router = APIRouter()


@router.get('/info')
async def get_info() -> InfoResponse:
    app_state = AppState()
    return InfoResponse(
        network=settings.network,
        validators_manager_address=app_state.validators_manager_account.address,
    )
