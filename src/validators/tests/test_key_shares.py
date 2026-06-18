import secrets

from eth_typing import BLSPubkey
from py_ecc.bls import G2ProofOfPossession as bls_pop
from py_ecc.optimized_bls12_381.optimized_curve import G1 as P1
from py_ecc.optimized_bls12_381.optimized_curve import curve_order, multiply

from src.validators.key_shares import (
    bls_public_key_to_shares,
    reconstruct_shared_bls_public_key,
)


def _make_shares(threshold: int, total: int) -> tuple[BLSPubkey, dict[int, BLSPubkey]]:
    secret_key = bls_pop.KeyGen(secrets.token_bytes(32))
    public_key = BLSPubkey(bls_pop.SkToPk(secret_key))

    coefficients_int = [secrets.randbelow(curve_order) for _ in range(threshold - 1)]
    coefficients_g1 = [multiply(P1, coef) for coef in coefficients_int]

    # bls_public_key_to_shares evaluates the polynomial at x = 1..total
    shares = bls_public_key_to_shares(public_key, coefficients_g1, total)
    shares_by_index = {index + 1: share for index, share in enumerate(shares)}
    return public_key, shares_by_index


def test_reconstruct_with_all_shares():
    public_key, shares_by_index = _make_shares(threshold=3, total=4)
    assert reconstruct_shared_bls_public_key(shares_by_index) == public_key


def test_reconstruct_with_threshold_subset():
    threshold = 3
    public_key, shares_by_index = _make_shares(threshold=threshold, total=4)
    subset = dict(list(shares_by_index.items())[:threshold])
    assert reconstruct_shared_bls_public_key(subset) == public_key


def test_reconstruct_with_wrong_shares_does_not_match():
    public_key, _ = _make_shares(threshold=3, total=4)
    _, other_shares = _make_shares(threshold=3, total=4)
    assert reconstruct_shared_bls_public_key(other_shares) != public_key
