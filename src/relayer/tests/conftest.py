import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture()
def sidecar_shares_1val() -> list[dict]:
    """
    Fixture with shares for 1 validator on Hoodi.
    Note. Exit signature shares are generated for outdated validator index
    and could not be used for real exit messages.
    """
    return json.loads((FIXTURES_DIR / 'sidecar_shares_1_validator.json').read_text())


@pytest.fixture()
def sidecar_shares_2val() -> list[dict]:
    """
    Fixture with shares for 2 validators on Hoodi.
    Note. Exit signature shares are generated for outdated validator index
    and could not be used for real exit messages.
    """
    return json.loads((FIXTURES_DIR / 'sidecar_shares_2_validators.json').read_text())
