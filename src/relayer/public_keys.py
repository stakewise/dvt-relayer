import csv
import logging
import os

from eth_typing import BlockNumber, HexStr
from eth_utils import add_0x_prefix
from sw_utils.typings import ChainHead
from web3 import Web3

from src.common.clients import consensus_client, execution_client
from src.common.contracts import validators_registry_contract
from src.config import settings
from src.validators.validators import validate_bls_pubkey

logger = logging.getLogger(__name__)


class PublicKeysManager:
    def __init__(
        self,
        public_keys: list[HexStr] | None = None,
        registered_public_keys: set[HexStr] | None = None,
        block_number: BlockNumber = BlockNumber(0),
    ) -> None:
        self.public_keys: list[HexStr] = public_keys or []
        self.registered_public_keys: set[HexStr] = registered_public_keys or set()
        self.block_number: BlockNumber = block_number

    @classmethod
    async def build(cls, chain_head: ChainHead) -> 'PublicKeysManager':
        """Creates and initializes a PublicKeysManager from config and chain state."""
        public_keys = cls.load_from_file()
        registered = await cls.fetch_registered(public_keys=public_keys, state_id=chain_head.slot)
        return cls(
            public_keys=public_keys,
            registered_public_keys=registered,
            block_number=chain_head.block_number,
        )

    @classmethod
    def load_from_file(cls) -> list[HexStr]:
        """Loads public keys from the configured CSV file and returns them."""
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

        logger.info('Loaded %d public keys', len(public_keys))
        return public_keys

    @classmethod
    async def fetch_registered(
        cls, public_keys: list[HexStr], state_id: int | str = 'head'
    ) -> set[HexStr]:
        """
        Fetches validators from the consensus client and returns registered public keys.
        This includes validators that are present in the
        finalized state, as well as pending deposits awaiting activation.
        """
        if not public_keys:
            return set()

        public_keys_set = set(public_keys)

        logger.info('Fetching validators by ids, state_id=%s', state_id)
        response = await consensus_client.get_validators_by_ids(
            validator_ids=public_keys,
            state_id=str(state_id),
        )
        logger.info('Fetched %d validators', len(response.get('data', [])))
        registered_keys: set[HexStr] = set()
        for validator in response.get('data', []):
            pubkey = add_0x_prefix(validator['validator']['pubkey'])
            registered_keys.add(HexStr(pubkey))

        logger.info('Fetching pending deposits, state_id=%s', state_id)
        pending_deposits = await consensus_client.get_pending_deposits(state_id=state_id)
        logger.info('Fetched %d pending deposits', len(pending_deposits))
        for deposit in pending_deposits:
            pubkey = HexStr(add_0x_prefix(deposit['pubkey']))
            if pubkey in public_keys_set:
                registered_keys.add(pubkey)

        logger.info(
            'Found %d registered validators out of %d',
            len(registered_keys),
            len(public_keys),
        )
        return registered_keys

    def update_registered_public_keys(
        self, new_keys: set[HexStr], block_number: BlockNumber
    ) -> None:
        """Adds newly registered public keys and advances the tracked block number."""
        if new_keys:
            self.registered_public_keys.update(new_keys)
            logger.info('Found %d newly registered validators', len(new_keys))
        self.block_number = block_number

    async def get_unregistered(self) -> list[HexStr]:
        """
        Returns public keys that are not yet registered on the consensus layer.
        Also excludes keys with pending deposits between the finalized and head blocks.
        """
        if not self.public_keys:
            return []

        head_block = await execution_client.eth.get_block_number()

        pending_keys: set[HexStr] = set()

        if head_block > self.block_number:
            events = await validators_registry_contract.events.DepositEvent.get_logs(
                from_block=BlockNumber(self.block_number + 1),
                to_block=head_block,
            )
            for event in events:
                pending_keys.add(HexStr(Web3.to_hex(event['args']['pubkey'])))

        return [
            pk
            for pk in self.public_keys
            if pk not in self.registered_public_keys and pk not in pending_keys
        ]
