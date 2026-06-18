import ecies
import milagro_bls_binding as bls
from eth_typing import BLSPubkey, BLSSignature, HexStr
from sw_utils import (
    ConsensusFork,
    DepositMessage,
    compute_deposit_domain,
    compute_signing_root,
    get_exit_message_signing_root,
    is_valid_deposit_data_signature,
    is_valid_exit_signature,
)
from sw_utils.typings import Bytes32
from web3 import Web3
from web3.types import Gwei

from src.app_state import AppState
from src.config import settings
from src.validators.key_shares import (
    bls_signature_and_public_key_to_shares,
    reconstruct_shared_bls_public_key,
)
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


def validate_exit_signature(
    public_key: HexStr,
    validator_index: int,
    exit_signature: BLSSignature,
) -> bool:
    genesis_validators_root = settings.network_config.GENESIS_VALIDATORS_ROOT
    fork = settings.network_config.SHAPELLA_FORK

    message = get_exit_message_signing_root(
        validator_index=validator_index,
        genesis_validators_root=genesis_validators_root,
        fork=fork,
    )

    return bls.Verify(Web3.to_bytes(hexstr=public_key), message, exit_signature)


def validate_deposit_signature(
    public_key: HexStr,
    withdrawal_credentials: bytes,
    amount: Gwei,
    deposit_signature: BLSSignature,
) -> bool:
    return is_valid_deposit_data_signature(
        public_key=BLSPubkey(Web3.to_bytes(hexstr=public_key)),
        withdrawal_credentials=Bytes32(withdrawal_credentials),
        signature=deposit_signature,
        amount=amount,
        fork_version=settings.network_config.GENESIS_FORK_VERSION,
    )


def validate_public_key_shares(
    public_key: HexStr,
    shares_by_index: dict[int, BLSPubkey],
) -> bool:
    """Reconstructs the full validator public key from shares and compares it."""
    try:
        reconstructed = reconstruct_shared_bls_public_key(shares_by_index)
    except Exception:  # nosec
        return False
    return reconstructed == BLSPubkey(Web3.to_bytes(hexstr=public_key))


def validate_exit_signature_share(
    validator_index: int,
    public_key_share: BLSPubkey,
    exit_signature_share: BLSSignature,
) -> bool:
    """Verifies an exit signature share against the operator's public key share."""
    try:
        return is_valid_exit_signature(
            validator_index=validator_index,
            public_key=public_key_share,
            signature=exit_signature_share,
            genesis_validators_root=settings.network_config.GENESIS_VALIDATORS_ROOT,
            fork=settings.network_config.SHAPELLA_FORK,
        )
    except Exception:  # nosec
        return False


def validate_deposit_signature_share(
    public_key_share: BLSPubkey,
    public_key: HexStr,
    withdrawal_credentials: bytes,
    amount: Gwei,
    deposit_signature_share: BLSSignature,
) -> bool:
    """
    Verifies a deposit signature share against the operator's public key share.

    The deposit message embeds the full validator public key, so the message is built
    from `public_key` while verification uses the `public_key_share`.
    """
    try:
        domain = compute_deposit_domain(fork_version=settings.network_config.GENESIS_FORK_VERSION)
        deposit_message = DepositMessage(
            pubkey=Web3.to_bytes(hexstr=public_key),
            withdrawal_credentials=Bytes32(withdrawal_credentials),
            amount=amount,
        )
        message = compute_signing_root(deposit_message, domain)
        return bls.Verify(public_key_share, message, deposit_signature_share)
    except Exception:  # nosec
        return False
