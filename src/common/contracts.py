import json
import os
from functools import cached_property

from eth_typing import HexStr
from sw_utils.typings import Bytes32
from web3.contract import AsyncContract
from web3.contract.async_contract import AsyncContractEvents, AsyncContractFunctions
from web3.types import ChecksumAddress

from src.common.clients import execution_client
from src.config import settings


class ContractWrapper:
    abi_path: str = ''
    settings_key: str = ''

    @property
    def contract_address(self) -> ChecksumAddress:
        return getattr(settings.network_config, self.settings_key)

    @cached_property
    def contract(self) -> AsyncContract:
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, self.abi_path), encoding='utf-8') as f:
            abi = json.load(f)
        return execution_client.eth.contract(abi=abi, address=self.contract_address)

    @property
    def address(self) -> ChecksumAddress:
        return self.contract.address

    @property
    def functions(self) -> AsyncContractFunctions:
        return self.contract.functions

    @property
    def events(self) -> AsyncContractEvents:
        return self.contract.events

    def encode_abi(self, fn_name: str, args: list | None = None) -> HexStr:
        return self.contract.encodeABI(fn_name=fn_name, args=args)


class ValidatorsRegistryContract(ContractWrapper):
    abi_path = 'abi/IValidatorsRegistry.json'
    settings_key = 'VALIDATORS_REGISTRY_CONTRACT_ADDRESS'

    async def get_registry_root(self) -> Bytes32:
        """Fetches the latest validators registry root."""
        return await self.contract.functions.get_deposit_root().call()


validators_registry_contract = ValidatorsRegistryContract()
