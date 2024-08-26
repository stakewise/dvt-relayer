from eth_typing import HexStr
from web3 import Web3

BLS_PUBLIC_KEY_BYTES_LENGTH = 48
BLS_SIGNATURE_LENGTH = 96


def validate_bls_pubkey(v: HexStr) -> HexStr:
    try:
        if len(Web3.to_bytes(hexstr=v)) == BLS_PUBLIC_KEY_BYTES_LENGTH:
            return v
    except Exception:  # nosec
        pass

    raise ValueError('invalid BLS public key')


def validate_bls_signature(v: HexStr) -> HexStr:
    try:
        if len(Web3.to_bytes(hexstr=v)) == BLS_SIGNATURE_LENGTH:
            return v
    except Exception:  # nosec
        pass

    raise ValueError('invalid BLS signature')
