from ecies.utils import generate_key
from sw_utils.tests.factories import get_mocked_protocol_config
from sw_utils.typings import Oracle, ProtocolConfig
from web3 import Web3


def _generate_oracle(index: int) -> Oracle:
    key = generate_key()
    public_key = Web3.to_hex(key.public_key.format(compressed=False)[1:])
    return Oracle(public_key=public_key, endpoints=[f'http://example.com/{index}/'])


def create_protocol_config(
    oracles_count: int = 3,
    exit_signature_recover_threshold: int = 1,
    exit_signature_epoch: int = 0,
) -> ProtocolConfig:
    oracles = [_generate_oracle(i) for i in range(oracles_count)]
    return get_mocked_protocol_config(
        oracles=oracles,
        exit_signature_recover_threshold=exit_signature_recover_threshold,
        exit_signature_epoch=exit_signature_epoch,
    )
