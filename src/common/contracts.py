import json
import os
from functools import cached_property

from eth_typing import BlockNumber
from sw_utils.typings import Bytes32
from web3.contract import AsyncContract
from web3.contract.async_contract import (
    AsyncContractEvent,
    AsyncContractEvents,
    AsyncContractFunctions,
)
from web3.types import ChecksumAddress, EventData

from src.common.clients import execution_client
from src.config import settings


class ContractWrapper:
    abi_path: str = ''

    def __init__(self, address: ChecksumAddress):
        self.address = address

    @cached_property
    def contract(self) -> AsyncContract:
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, self.abi_path), encoding='utf-8') as f:
            abi = json.load(f)
        return execution_client.eth.contract(abi=abi, address=self.address)

    @property
    def functions(self) -> AsyncContractFunctions:
        return self.contract.functions

    @property
    def events(self) -> AsyncContractEvents:
        return self.contract.events

    @property
    def events_blocks_range_interval(self) -> int:
        return 43200 // settings.network_config.SECONDS_PER_BLOCK  # 12 hrs

    async def _get_last_event(
        self,
        event: type[AsyncContractEvent],
        from_block: BlockNumber,
        to_block: BlockNumber,
        argument_filters: dict | None = None,
    ) -> EventData | None:
        blocks_range = self.events_blocks_range_interval

        while to_block >= from_block:
            events = await event.get_logs(
                from_block=BlockNumber(max(to_block - blocks_range, from_block)),
                to_block=to_block,
                argument_filters=argument_filters,
            )
            if events:
                return events[-1]
            to_block = BlockNumber(to_block - blocks_range - 1)
        return None


class ValidatorsRegistryContract(ContractWrapper):
    abi_path = 'abi/IValidatorsRegistry.json'

    async def get_registry_root(self) -> Bytes32:
        """Fetches the latest validators registry root."""
        return await self.contract.functions.get_deposit_root().call()


class KeeperContract(ContractWrapper):
    abi_path = 'abi/IKeeper.json'

    async def get_config_updated_event(
        self, from_block: BlockNumber | None = None, to_block: BlockNumber | None = None
    ) -> EventData | None:
        """Fetches the last oracles config updated event."""
        return await self._get_last_event(
            self.events.ConfigUpdated,  # type: ignore
            from_block=from_block or settings.network_config.KEEPER_GENESIS_BLOCK,
            to_block=to_block or await execution_client.eth.get_block_number(),
        )


class VaultContract(ContractWrapper):
    abi_path = 'abi/IEthVault.json'

    async def validators_manager_nonce(self) -> int:
        return await self.contract.functions.validatorsManagerNonce().call()


validators_registry_contract = ValidatorsRegistryContract(
    settings.network_config.VALIDATORS_REGISTRY_CONTRACT_ADDRESS
)
keeper_contract = KeeperContract(settings.network_config.KEEPER_CONTRACT_ADDRESS)
