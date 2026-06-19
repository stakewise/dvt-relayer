import functools
import tomllib
from pathlib import Path


@functools.cache
def get_project_meta() -> dict:
    toml_path = Path() / 'pyproject.toml'

    with toml_path.open(mode='rb') as pyproject:
        return tomllib.load(pyproject)


def get_project_version() -> str:
    return get_project_meta()['tool']['poetry']['version']
