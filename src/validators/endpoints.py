from fastapi import APIRouter

from src.validators.typings import ValidatorsRequest

router = APIRouter()


@router.get('/validators')
async def get_pending_validators() -> list:
    return []


@router.post('/validators')
async def create_validators(request: ValidatorsRequest) -> list:
    return []
