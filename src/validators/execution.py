import logging
import struct

from eth_typing import BlockNumber, HexStr
from sw_utils import EventProcessor, is_valid_deposit_data_signature
from web3 import Web3
from web3.types import EventData

from src.app_state import AppState
from src.common.contracts import validators_registry_contract
from src.config import settings
from src.relayer.public_keys import public_keys_manager

logger = logging.getLogger(__name__)


class NetworkValidatorsProcessor(EventProcessor):
    """
    Processor for network validators events. It listens to the DepositEvent of the
    ValidatorsRegistry contract and updates registered public keys in the app state.
    """

    contract_event = 'DepositEvent'

    def __init__(self, from_block: BlockNumber) -> None:
        self._from_block = from_block

    @property
    def contract(self):  # type: ignore
        return validators_registry_contract

    async def get_from_block(self) -> BlockNumber:
        # Returns first unprocessed block number
        # Used by EventScanner
        return self._from_block

    async def process_events(self, events: list[EventData], to_block: BlockNumber) -> None:
        new_keys: set[HexStr] = set()
        for event in events:
            public_key = process_network_validator_event(event)
            if public_key and public_key in public_keys_manager.public_keys:
                new_keys.add(public_key)

        if new_keys:
            public_keys_manager.registered_public_keys.update(new_keys)
            logger.info('Found %d newly registered validators', len(new_keys))

        AppState().network_validators_block = to_block
        self._from_block = BlockNumber(to_block + 1)


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
