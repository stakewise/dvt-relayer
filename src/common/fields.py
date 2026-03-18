from typing import Annotated

from eth_typing import ChecksumAddress
from pydantic import BeforeValidator
from web3 import Web3

ChecksumAddressField = Annotated[ChecksumAddress, BeforeValidator(Web3.to_checksum_address)]
