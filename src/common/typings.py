from dataclasses import dataclass

from eth_typing import BlockNumber


class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class OraclesCache:
    checkpoint_block: BlockNumber
    config: dict
