import pytest

from src.app_state import AppState
from src.common.typings import Singleton


@pytest.fixture(autouse=True)
def _clean_singleton() -> None:  # type: ignore[misc]
    """Clean AppState singleton between tests."""
    Singleton._instances.pop(AppState, None)
    yield
    Singleton._instances.pop(AppState, None)
