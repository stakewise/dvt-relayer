import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture()
def sidecar_shares_1val() -> list[dict]:
    return json.loads((FIXTURES_DIR / 'sidecar_shares_1_validator.json').read_text())
