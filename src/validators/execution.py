import logging
import struct
from typing import Set, cast

from eth_typing import BlockNumber, HexStr
from sw_utils import EventProcessor, is_valid_deposit_data_signature
from web3 import Web3
from web3.contract.async_contract import AsyncContractEvent
from web3.types import EventData

from src.common.contracts import validators_registry_contract
from src.config import settings
from src.validators.database import NetworkValidatorCrud
from src.validators.typings import NetworkValidator

logger = logging.getLogger(__name__)


class NetworkValidatorsProcessor(EventProcessor):
    contract_event = 'DepositEvent'

    @property
    def contract(self):
        return validators_registry_contract

    @staticmethod
    async def get_from_block() -> BlockNumber:
        last_validator = NetworkValidatorCrud().get_last_network_validator()
        if not last_validator:
            raise RuntimeError('network validators are missing')

        return BlockNumber(last_validator.block_number + 1)

    @staticmethod
    # pylint: disable-next=unused-argument
    async def process_events(events: list[EventData], to_block: BlockNumber) -> None:
        validators = process_network_validator_events(events)
        NetworkValidatorCrud().save_network_validators(validators)


def process_network_validator_events(events: list[EventData]) -> list[NetworkValidator]:
    """
    Processes `ValidatorsRegistry` registration events
    and returns the list of valid validators.
    """
    result: list[NetworkValidator] = []
    for event in events:
        public_key = process_network_validator_event(event)
        if not public_key:
            continue

        result.append(
            NetworkValidator(public_key=public_key, block_number=BlockNumber(event['blockNumber']))
        )

    return result


def process_network_validator_event(event: EventData) -> HexStr | None:
    """
    Processes validator deposit event
    and returns its public key if the deposit is valid.
    """
    public_key = event['args']['pubkey']
    withdrawal_creds = event['args']['withdrawal_credentials']
    amount_gwei = struct.unpack('<Q', event['args']['amount'])[0]
    signature = event['args']['signature']
    fork_version = settings.network_config.GENESIS_FORK_VERSION
    if is_valid_deposit_data_signature(
        public_key, withdrawal_creds, signature, amount_gwei, fork_version
    ):
        return Web3.to_hex(public_key)

    return None


async def get_latest_network_validator_public_keys() -> Set[HexStr]:
    """Fetches the latest network validator public keys."""
    last_validator = NetworkValidatorCrud().get_last_network_validator()
    if last_validator:
        from_block = BlockNumber(last_validator.block_number + 1)
    else:
        raise RuntimeError('network validators are missing')

    event_cls = cast(type[AsyncContractEvent], validators_registry_contract.events.DepositEvent)
    new_events = await event_cls.get_logs(fromBlock=from_block)
    new_public_keys: Set[HexStr] = set()
    for event in new_events:
        public_key = process_network_validator_event(event)
        if public_key:
            new_public_keys.add(public_key)

    return new_public_keys
