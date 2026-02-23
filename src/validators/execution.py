import struct

from eth_typing import BlockNumber, HexStr
from sw_utils import EventProcessor, is_valid_deposit_data_signature
from web3 import Web3
from web3.types import EventData

from src.app_state import AppState
from src.common.contracts import validators_registry_contract
from src.config import settings


class NetworkValidatorsProcessor(EventProcessor):
    """
    Processor for network validators events. It listens to the DepositEvent of the
    ValidatorsRegistry contract and updates registered public keys in the app state.
    """

    contract_event = 'DepositEvent'

    @property
    def contract(self):  # type: ignore
        return validators_registry_contract

    async def get_from_block(self) -> BlockNumber:
        # Returns first unprocessed block number
        # Used by EventScanner
        return BlockNumber(AppState().public_keys_manager.block_number + 1)

    async def process_events(self, events: list[EventData], to_block: BlockNumber) -> None:
        public_keys_manager = AppState().public_keys_manager
        new_keys: set[HexStr] = set()
        for event in events:
            public_key = process_network_validator_event(event)
            if public_key and public_key in public_keys_manager.public_keys:
                new_keys.add(public_key)

        public_keys_manager.update_registered_public_keys(new_keys, to_block)


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
