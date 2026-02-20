import csv
import logging
import os

from eth_typing import BlockNumber, HexStr
from eth_utils import add_0x_prefix
from web3 import Web3

from src.app_state import AppState
from src.common.clients import consensus_client, execution_client
from src.common.contracts import validators_registry_contract
from src.config import settings
from src.validators.validators import validate_bls_pubkey

logger = logging.getLogger(__name__)


class PublicKeysManager:
    def __init__(self) -> None:
        self.public_keys: list[HexStr] = []
        self.registered_public_keys: set[HexStr] = set()

    def load_from_file(self) -> None:
        """Loads public keys from the configured CSV file."""
        public_keys_file = settings.public_keys_file
        if not os.path.isfile(public_keys_file):
            raise ValueError(f"Can't open public keys file. Path: {public_keys_file}")

        public_keys: list[HexStr] = []
        with open(public_keys_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                public_key = validate_bls_pubkey(HexStr(row[0].strip()))
                public_keys.append(public_key)

        if not public_keys:
            raise ValueError(f'No public keys found in file. Path: {public_keys_file}')

        self.public_keys = public_keys
        logger.info('Loaded %d public keys', len(public_keys))

    async def fetch_registered(self) -> None:
        """
        Fetches validators from the consensus client and updates registered public keys.
        This includes validators that have been submitted to deposit contract up to the
        finalized block.
        """
        if not self.public_keys:
            return

        response = await consensus_client.get_validators_by_ids(
            validator_ids=self.public_keys,
            state_id='head',
        )
        registered_keys: set[HexStr] = set()
        for validator in response.get('data', []):
            pubkey = add_0x_prefix(validator['validator']['pubkey'])
            registered_keys.add(HexStr(pubkey))

        self.registered_public_keys = registered_keys
        logger.info(
            'Found %d registered validators out of %d',
            len(registered_keys),
            len(self.public_keys),
        )

    async def get_unregistered(self) -> list[HexStr]:
        """
        Returns public keys that are not yet registered on the consensus layer.
        Also excludes keys with pending deposits between the finalized and head blocks.
        """
        if not self.public_keys:
            return []

        network_validators_block = AppState().network_validators_block
        head_block = await execution_client.eth.get_block_number()

        pending_keys: set[HexStr] = set()

        if head_block > network_validators_block:
            events = await validators_registry_contract.events.DepositEvent.get_logs(
                from_block=BlockNumber(network_validators_block + 1),
                to_block=head_block,
            )
            for event in events:
                pending_keys.add(HexStr(Web3.to_hex(event['args']['pubkey'])))

        return [
            pk
            for pk in self.public_keys
            if pk not in self.registered_public_keys and pk not in pending_keys
        ]


public_keys_manager = PublicKeysManager()
