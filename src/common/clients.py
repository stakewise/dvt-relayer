from sw_utils import get_execution_client

from src.config import settings

execution_client = get_execution_client(
    [settings.execution_endpoint],
    timeout=settings.execution_timeout,
    retry_timeout=settings.execution_retry_timeout,
)
