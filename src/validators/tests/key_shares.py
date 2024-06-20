from eth_typing import BLSPubkey
from py_ecc.bls.g2_primitives import G1_to_pubkey, pubkey_to_G1
from py_ecc.optimized_bls12_381 import Z1, add, curve_order, multiply
from py_ecc.utils import prime_field_inv


def reconstruct_shared_bls_public_key(public_keys: dict[int, BLSPubkey]) -> BLSPubkey:
    """
    Reconstructs shared BLS public key.
    Inspired by https://github.com/dankrad/python-ibft/blob/master/bls_threshold.py

    public_keys: dict[int, BLSPubkey] - indexes must be 1-based (1,2,3...)
    """
    r = Z1
    for i, key in public_keys.items():
        key_point = pubkey_to_G1(key)
        coef = 1
        for j in public_keys:
            if j != i:
                coef = -coef * j * prime_field_inv(i - j, curve_order) % curve_order
        r = add(r, multiply(key_point, coef))
    return G1_to_pubkey(r)
