from fastapi import APIRouter

from src.common.schema import InfoResponse
from src.config import settings

router = APIRouter()


@router.get('/info')
async def get_info() -> InfoResponse:
    return InfoResponse(network=settings.network)
