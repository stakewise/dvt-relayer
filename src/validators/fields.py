from typing import Annotated

from eth_typing import HexStr
from pydantic import AfterValidator

from src.validators.validators import validate_bls_pubkey, validate_bls_signature

BLSPubkeyField = Annotated[HexStr, AfterValidator(validate_bls_pubkey)]
BLSSignatureField = Annotated[HexStr, AfterValidator(validate_bls_signature)]
