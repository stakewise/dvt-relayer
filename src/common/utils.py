import functools
from pathlib import Path

import tomli


@functools.cache
def get_project_meta() -> dict:
    toml_path = Path() / 'pyproject.toml'

    with toml_path.open(mode='rb') as pyproject:
        return tomli.load(pyproject)


def get_project_version() -> str:
    return get_project_meta()['tool']['poetry']['version']
