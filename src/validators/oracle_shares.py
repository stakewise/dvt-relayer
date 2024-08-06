import ecies
from eth_typing import BLSPubkey, BLSSignature, HexStr
from sw_utils import ConsensusFork, get_exit_message_signing_root
from web3 import Web3

from src.app_state import AppState
from src.config import settings
from src.validators.key_shares import bls_signature_and_public_key_to_shares
from src.validators.typings import OraclesExitSignatureShares


async def get_oracles_exit_signature_shares(
    public_key: HexStr,
    validator_index: int,
    exit_signature: BLSSignature,
    fork: ConsensusFork | None = None,
) -> OraclesExitSignatureShares:
    """
    * generates exit signature shards,
    * generates public key shards
    * encrypts exit signature shards with oracles' public keys.
    """
    fork = fork or settings.network_config.SHAPELLA_FORK
    app_state = AppState()
    protocol_config = app_state.protocol_config
    oracle_public_keys = [oracle.public_key for oracle in protocol_config.oracles]
    message = get_exit_message_signing_root(
        validator_index=validator_index,
        genesis_validators_root=settings.network_config.GENESIS_VALIDATORS_ROOT,
        fork=fork,
    )

    public_key_bytes = BLSPubkey(Web3.to_bytes(hexstr=public_key))
    threshold = protocol_config.exit_signature_recover_threshold
    total = len(protocol_config.oracles)

    exit_signature_shares, public_key_shares = bls_signature_and_public_key_to_shares(
        message, exit_signature, public_key_bytes, threshold, total
    )

    encrypted_exit_signature_shares = encrypt_signatures_list(
        oracle_public_keys, exit_signature_shares
    )
    return OraclesExitSignatureShares(
        public_keys=[Web3.to_hex(p) for p in public_key_shares],
        encrypted_exit_signatures=encrypted_exit_signature_shares,
    )


def encrypt_signatures_list(
    oracle_pubkeys: list[HexStr], signatures: list[BLSSignature]
) -> list[HexStr]:
    res: list[HexStr] = []
    for signature, oracle_pubkey in zip(signatures, oracle_pubkeys):
        res.append(encrypt_signature(oracle_pubkey, signature))
    return res


def encrypt_signature(oracle_pubkey: HexStr, signature: BLSSignature) -> HexStr:
    return Web3.to_hex(ecies.encrypt(oracle_pubkey, signature))
